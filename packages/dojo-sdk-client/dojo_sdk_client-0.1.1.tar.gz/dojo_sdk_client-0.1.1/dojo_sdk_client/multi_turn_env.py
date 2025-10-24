import asyncio
import base64
import json
import logging
import os
import time
from io import BytesIO
from typing import Any, List, Tuple

import verifiers as vf
from datasets import Dataset
from dojo_sdk_core.settings import settings
from dojo_sdk_core.tasks import RemoteTaskLoader
from dojo_sdk_core.types import (
    Action,
    ClickAction,
    WaitAction,
)
from openai import AsyncOpenAI
from verifiers.types import Message, Messages, State

from .agents.anthropic_cua import SYSTEM_PROMPT
from .agents.computer_use_tool import computer_tool
from .base_dojo_client import BaseDojoClient, NoRunnersAvailableError, ResponseStatus
from .utils import load_tasks_from_hf_dataset

logger = logging.getLogger(__name__)


def load_benchmark_tasks(tasks: List[str], system_prompt: str) -> Dataset:
    task_loader = RemoteTaskLoader("chakra-labs/dojo-bench-mini")
    dataset_rows = []
    for task_id in tasks:
        task = task_loader.load_task(task_id)
        dataset_rows.append(
            {
                "prompt": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task.instructions.user_prompt},
                ],
                "answer": "",
                "info": {
                    "task_id": task_id,
                    "task_name": task.name,
                    "initial_state": json.dumps(task.initial_state),
                    "max_steps": task.max_steps,
                },
            }
        )

    return Dataset.from_list(dataset_rows)


class DojoMultiTurnEnv(vf.ToolEnv):
    def __init__(
        self,
        client: BaseDojoClient,
        dataset: Dataset,
        **kwargs,
    ):
        self.client = client
        self._created_time = time.time()
        self._started = False
        self.job_id = None
        super().__init__(dataset=dataset, **kwargs, tools=[computer_tool])

    async def setup_state(self, state: State, **kwargs) -> State:
        if time.time() - self._created_time > 60 and not self._started:
            logger.error("Environment has been running for more than 60 seconds before starting, terminating")
            raise ValueError("Environment has been running for more than 60 seconds before starting, terminating")
        self._started = True

        info = state.get("info")

        state["task_id"] = info.get("task_id")
        state["initial_state"] = info.get("initial_state")
        state["max_steps"] = min(self.max_turns, info.get("max_steps"))
        state["step"] = 0
        state["started"] = False
        state["created"] = False

        return state

    async def _parse_tool_calls(self, messages: Messages) -> Tuple[List[Action], List[Message]]:
        actions = []
        tool_messages = []
        if "tool_calls" in messages[-1]:
            for tool_call in messages[-1]["tool_calls"]:
                tool_name: str = tool_call.function.name
                tool_args: dict = json.loads(tool_call.function.arguments)
                tool_call_id: str = tool_call.id or ""
                tool_message: Message = await self.call_tool(tool_name, tool_args, tool_call_id)
                tool_messages.append(tool_message)
                try:
                    action = computer_tool(**tool_args)
                    actions.append(action)
                except Exception as e:
                    logger.error(f"Error in computer_tool: {e} falling back to click")
                    action = ClickAction(x=100, y=100)
        return actions, tool_messages

    async def env_response(self, messages: Messages, state: State, **kwargs: Any) -> Tuple[Messages, State]:
        step = state.get("step", 0)
        created = state.get("created", False)

        if not created:
            exec_id = await self.client.create_task(
                state["task_id"], json.loads(state["initial_state"]), timeout=500, metadata={"job_id": self.job_id}
            )
            state["exec_id"] = exec_id
            state["created"] = True
            logger.info(f"Created task {state['task_id']}")

        exec_id = state.get("exec_id")
        if not exec_id:
            raise ValueError("Execution ID not found in state")

        started = state.get("started", False)

        while not started:
            # Start the task using DojoClient
            try:
                await self.client.start_task(exec_id=state.get("exec_id"))
                state["started"] = True
                started = True
            except NoRunnersAvailableError:
                logger.error("No runners available, retrying in 30 seconds")
                await asyncio.sleep(30)
                continue
            except Exception as e:
                logger.error(f"Error starting task {state['exec_id']}: {e}")
                raise e
            logger.info(f"Started task {state['exec_id']}")

            result = await self.client.get_task_status(exec_id)
            while result.status is ResponseStatus.QUEUED:
                logger.info(f"Task {exec_id} is queued, retrying in 1 second")
                await asyncio.sleep(1)
                result = await self.client.get_task_status(exec_id)

        logger.info(f"Environment response for task {exec_id}, step {step}")

        assert isinstance(messages[-1], dict)
        last_message = messages[-1]["content"]
        if not last_message or last_message.strip() == "":
            for message in messages[::-1]:
                last_message = message["content"]
                break

        assert isinstance(messages, list)
        actions, tool_messages = await self._parse_tool_calls(messages)
        logger.info(f"Last message: {last_message} actions: {actions}")

        if len(actions) == 0:
            actions = [WaitAction()]

        logger.info(f"Step: {state.get('step', 0)} Max steps: {state.get('max_steps', 15)}")

        # Submit action using DojoClient
        await self.client.submit_action(
            exec_id=exec_id,
            action=actions[0].model_dump(),
            agent_response=str(last_message),
            raw_response=json.dumps(last_message),
        )

        task_response = await self.client.get_task_status(exec_id)

        screenshot_path = task_response.screenshot
        history = task_response.history
        print(f"history: {history}")
        print(f"screenshot_path: {screenshot_path}")

        state["step"] = task_response.step
        state["history"] = history

        # Get the image from the server
        image = await self.client.get_image(screenshot_path)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        screenshot_bytes = buffer.getvalue()
        b64_img = base64.b64encode(screenshot_bytes).decode("utf-8")

        response_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_img}"},
                    }
                ],
            }
        ]

        logger.info(f"Environment response for task {exec_id}, step {state['step']}")

        return tool_messages + response_messages, state

    async def is_completed(self, messages: Messages, state: State, **kwargs: Any) -> bool:
        """Check if the task is completed."""
        created = state.get("created", False)
        if not created:
            return False

        started = state.get("started", False)
        if not started:
            return False

        exec_id = state.get("exec_id", None)
        if not exec_id:
            raise ValueError("Execution ID not found in state")

        if state.get("step", 0) >= state.get("max_steps", 15):
            await self.client.stop_task(exec_id)
            return True

        # Check task status
        task_response = await self.client.get_task_status(exec_id)
        is_finished = task_response.status in (ResponseStatus.COMPLETED, ResponseStatus.FAILED, ResponseStatus.TIMEOUT)
        logger.info(f"Task {exec_id} is finished: {is_finished}")
        if is_finished:
            await self.client.stop_task(exec_id)
        return is_finished


async def load_environment(API_KEY: str, system_prompt: str, tasks: List[str], **kwargs):
    """Load the Dojo environment. The environment must be executed within a minute or it will be terminated."""

    client = BaseDojoClient(API_KEY)

    # Create all tasks
    tasks_dataset = load_benchmark_tasks(tasks, system_prompt)
    env = DojoMultiTurnEnv(
        client=client,
        dataset=tasks_dataset,
        max_turns=15,
        **kwargs,
    )

    return env


async def main():
    tasks = load_tasks_from_hf_dataset("chakra-labs/dojo-bench-mini")

    API_KEY = os.getenv("DOJO_API_KEY")
    env = await load_environment(
        API_KEY=API_KEY,
        system_prompt=SYSTEM_PROMPT
        + "\n\nScreenshots are always provided as input. DO NOT ASK FOR A SCREENSHOT OR TRY TO TAKE A SCREENSHOT. DO NOT ASK FOR ANY INSTRUCTION FROM THE USER. When you are done, you must use the done action. Always perfom an action",
        tasks=tasks,
    )

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    env.evaluate(
        client=client,
        model="gpt-4o-mini",
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
