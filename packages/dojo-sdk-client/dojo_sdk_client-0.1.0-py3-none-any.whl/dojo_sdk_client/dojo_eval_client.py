import asyncio
import logging
import traceback
from dataclasses import dataclass
from typing import List, Optional

from dojo_sdk_core import Action, ActionType, FailAction, RemoteTaskLoader, TaskDefinition
from dojo_sdk_core.ws_types import HistoryStep
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from .agents.base_agent import BaseAgent
from .base_dojo_client import BaseDojoClient
from .types import ResponseStatus, TaskResponse

logger = logging.getLogger(__name__)


@dataclass
class StepReward:
    step: int
    reward: float
    reason: str


@dataclass
class TaskMetadata:
    task_id: str
    exec_id: str
    task_definition: TaskDefinition
    current_step: int = 0
    step_rewards: list = None

    def __post_init__(self):
        if self.step_rewards is None:
            self.step_rewards = []


@dataclass
class EvaluationResult:
    task_id: str
    task_name: str
    score: float
    reason: str
    step_rewards: List[StepReward]
    status: ResponseStatus
    total_steps: int
    error: Optional[str] = None


class DojoEvalClient:
    """High-level client for running evaluations"""

    def __init__(self, agent: BaseAgent, api_key: str):
        self.agent = agent
        self.client = BaseDojoClient(api_key)
        self.task_loader = RemoteTaskLoader(dataset_name="chakra-labs/dojo-bench-mini")

        self.task_metadata: dict[str, TaskMetadata] = {}  # exec_id -> metadata
        self.active_tasks: set[str] = set()

    def _reset_stats(self):
        self.success_tasks = 0
        self.failed_tasks = 0
        self.error_tasks = 0

    async def evaluate(self, tasks: list[str], num_runners: int = 1) -> List[EvaluationResult]:
        """
        Evaluate a list of tasks, respecting runner_limit.
        Tasks are queued and started as previous tasks complete.
        Returns list of evaluation results with task_id, task_name, score, and reason.
        """
        self._reset_stats()

        self.pbar = tqdm(total=len(tasks), desc="Evaluating tasks", unit="task", leave=True, position=0)

        # Reddrect logging so we can always see the progress bar
        with logging_redirect_tqdm():
            # Create all tasks
            exec_ids = []
            for task_id in tasks:
                exec_id = await self._create_task(task_id, "test_job_id")
                exec_ids.append(exec_id)
                logger.info(f"Created task {task_id} -> {exec_id}")

            # Queue for pending tasks
            pending_queue = asyncio.Queue()
            for exec_id in exec_ids:
                await pending_queue.put(exec_id)

            # Store completed tasks
            completed_tasks = []

            # Start initial batch of workers up to runner_limit
            workers = [
                asyncio.create_task(self._worker(pending_queue, completed_tasks))
                for _ in range(min(num_runners, len(exec_ids)))
            ]

            # Wait for all workers to complete
            await asyncio.gather(*workers)
            await pending_queue.join()

            # At the end, transform completed_tasks to EvaluationResults
            results = []
            for exec_id, task_response, error in completed_tasks:
                metadata = self.task_metadata[exec_id]
                task_def = metadata.task_definition

                if error:
                    # Task errored
                    results.append(
                        EvaluationResult(
                            task_id=metadata.task_id,
                            task_name=task_def.name,
                            score=0.0,
                            reason="",
                            step_rewards=metadata.step_rewards,
                            status=ResponseStatus.FAILED,
                            total_steps=len(metadata.step_rewards),
                            error=error,
                        )
                    )
                else:
                    # Calculate final score
                    reward_function = task_def.load_reward_function()

                    tqdm.write(f"task_response.state: {task_response.state}")
                    tqdm.write(f"task_def.initial_state: {task_def.initial_state}")

                    final_score, reason = reward_function(task_def.initial_state, task_response.state)

                    results.append(
                        EvaluationResult(
                            task_id=metadata.task_id,
                            task_name=task_def.name,
                            score=final_score,
                            reason=reason,
                            step_rewards=metadata.step_rewards,
                            status=task_response.status,
                            total_steps=len(metadata.step_rewards),
                        )
                    )

        self.pbar = None
        self._print_results(results)
        return results

    def _print_results(self, results: List[EvaluationResult]) -> str:
        """Format the results as a string"""
        failures = [r for r in results if r.score == 0.0 and not r.error]
        errors = [r for r in results if r.error]
        successes = [r for r in results if r.score > 0.0]

        results_str = "\n"

        if failures:
            results_str += "Failure details:\n"
            for result in failures:
                results_str += f"\t\t- {result.task_name} -> Status: {result.status.value} score: {result.score} reason: {result.reason} steps:{result.total_steps}\n"

        if errors:
            results_str += "Errors:\n"
            for result in errors:
                results_str += f"\t\t- {result.task_name} -> Error: {result.error}\n"

        # Summary line
        if results_str:
            results_str += "\n"

        percentage = int((len(successes) / len(results)) * 100) if len(results) > 0 else 0
        results_str += f"Score {percentage}% ({len(successes)}/{len(results)})"
        errors_count = len(errors)
        if errors_count > 0:
            results_str += f" | {errors_count} task{'s' if errors_count != 1 else ''} errored"

        print(results_str)

    async def _create_task(self, task_id: str, job_id: str) -> str:
        """Create a task and store its metadata"""
        task_def = self.task_loader.load_task(task_id)

        exec_id = await self.client.create_task(
            task_id=task_id,
            state=task_def.initial_state,
            timeout=60,
            metadata={"job_id": job_id},
        )

        # Store metadata for tracking
        self.task_metadata[exec_id] = TaskMetadata(task_id=task_id, exec_id=exec_id, task_definition=task_def, current_step=0)

        return exec_id

    async def _worker(self, pending_queue: asyncio.Queue, completed_tasks: list):
        """Worker that processes tasks from the queue"""
        while True:
            try:
                exec_id = pending_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            self.active_tasks.add(exec_id)
            try:
                result = await self._run_task(exec_id)
                completed_tasks.append((exec_id, result, None))
            except Exception as e:
                completed_tasks.append((exec_id, None, str(e)))
            finally:
                self.active_tasks.discard(exec_id)
                pending_queue.task_done()

    async def _run_task(self, exec_id: str) -> TaskResponse:
        """Execute a single task from start to completion"""
        metadata = self.task_metadata[exec_id]
        task_def = metadata.task_definition

        try:
            logger.info(f"Starting task {exec_id} ({metadata.task_id})")

            await self.client.start_task(exec_id)
            logger.info(f"Started task {exec_id} ({metadata.task_id})")

            result = await self.client.get_task_status(exec_id)
            success = False

            # wait for task to be ready
            while result.status is ResponseStatus.QUEUED:
                await asyncio.sleep(0.5)
                result = await self.client.get_task_status(exec_id)

            # Poll and execute actions until completion
            while result.status is ResponseStatus.RUNNING:
                if metadata.current_step >= task_def.max_steps:
                    logger.warning(f"Task {exec_id} reached max steps ({task_def.max_steps})")
                    fail_action = FailAction(message="Max steps reached")
                    await self.client.submit_action(exec_id, fail_action.model_dump(), "Max steps reached", "{}")
                    success = False
                    break

                logger.info(f"Getting next action for task {exec_id}")
                action, reasoning, raw_response = await self._get_agent_action(
                    result.history or [], task_def.instructions.user_prompt, result.screenshot
                )

                await self.client.submit_action(exec_id, action.model_dump(), reasoning, raw_response)

                metadata.current_step = result.step

                # Poll until step is applied
                result = await self.client.get_task_status(exec_id)
                while result.status is ResponseStatus.RUNNING and result.step == metadata.current_step:
                    await asyncio.sleep(0.5)
                    result = await self.client.get_task_status(exec_id)

                if result.status is not ResponseStatus.RUNNING:
                    break

                logger.info(f"result.state: {result.state}")

                # Calculate step reward
                reward_function = task_def.load_reward_function()
                reward, reason = reward_function(task_def.initial_state, result.state)

                success = reward > 0

                # Save the step reward
                metadata.step_rewards.append(StepReward(step=metadata.current_step, reward=reward, reason=reason))

                logger.info(
                    f"Task {exec_id} at step {metadata.current_step}/{task_def.max_steps} with reward {reward} and reason {reason}"
                )

                if action.type == ActionType.DONE or action.type == ActionType.FAIL:
                    break

            if success:
                self.success_tasks += 1
            else:
                self.failed_tasks += 1

            await self.client.stop_task(exec_id)

            logger.info(f"Completed task {exec_id} ({metadata.task_id}) with status {result.status}")
            return result

        except Exception as e:
            self.error_tasks += 1  # Is this atomic?
            logger.error(f"Error running task {exec_id}: {e} {traceback.format_exc()}")
            raise
        finally:
            self.pbar.update(1)
            self.pbar.set_postfix({"✓": self.success_tasks, "✗": self.failed_tasks, "!": self.error_tasks})

    async def _get_agent_action(
        self, history: List[HistoryStep], prompt: str, screenshot_path: str
    ) -> tuple[Action, str, Optional[str]]:
        """Get next action from agent"""
        screenshot = await self.client.get_image(screenshot_path)

        action, reasoning, raw_response = self.agent.get_next_action(
            prompt,
            screenshot,
            history,
        )

        return action, reasoning, raw_response
