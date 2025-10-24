from io import BytesIO
from typing import Any, Optional

import aiohttp
import PIL.Image
from dojo_sdk_core.settings import settings
from dojo_sdk_core.ws_types import HistoryStep

from .types import NoRunnersAvailableError, ResponseStatus, TaskResponse

# TODO: add a way to terminate task


class BaseDojoClient:
    """Barebones HTTP client for Dojo"""

    def __init__(self, api_key: str) -> None:
        self.api_key: str = api_key
        self.http_endpoint: str = settings.dojo_http_endpoint

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def create_job(self) -> dict[str, Any]:
        """Create a new job"""
        async with aiohttp.request(
            "POST", f"{self.http_endpoint}/jobs/create", json={}, headers=self._get_headers()
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get job status"""
        async with aiohttp.request(
            "GET", f"{self.http_endpoint}/jobs/{job_id}/status", headers=self._get_headers()
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def create_task(
        self,
        task_id: str,
        state: dict[str, Any],
        timeout: int = 60,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Create a task execution"""
        async with aiohttp.request(
            "POST",
            f"{self.http_endpoint}/tasks",
            json={
                "task_id": task_id,
                "timeout": timeout,
                "metadata": metadata or {},
                "state": state,
            },
            headers=self._get_headers(),
        ) as response:
            response.raise_for_status()
            resp = await response.json()
            return resp["exec_id"]

    async def start_task(self, exec_id: str) -> dict[str, Any]:
        """Start a task execution"""
        async with aiohttp.request(
            "POST", f"{self.http_endpoint}/tasks/start", json={"exec_id": exec_id}, headers=self._get_headers()
        ) as response:
            resp = await response.json()
            if response.status != 200:
                if resp.get("error") == "No runners available":
                    raise NoRunnersAvailableError(resp.get("error"))
                else:
                    raise Exception(resp.get("error"))
            return resp

    async def get_task_status(self, exec_id: str) -> TaskResponse:
        """Get task status at a specific step"""
        async with aiohttp.request(
            "GET", f"{self.http_endpoint}/tasks/{exec_id}/status", headers=self._get_headers()
        ) as response:
            result = await response.json()
            history = result.get("history", [])
            if history is None:
                history = []
            return TaskResponse(
                status=ResponseStatus(result.get("status", "PENDING")),
                screenshot=result.get("screenshot"),
                history=[HistoryStep(**h) for h in history],
                step=result.get("step"),
                state=result.get("state"),
            )

    async def submit_action(
        self, exec_id: str, action: dict[str, Any], agent_response: str, raw_response: str = "Not provided"
    ) -> dict[str, Any]:
        """Submit an action for a task"""
        async with aiohttp.request(
            "POST",
            f"{self.http_endpoint}/tasks/actions",
            json={
                "action": action,
                "agent_response": agent_response,
                "exec_id": exec_id,
                "raw_response": raw_response,
            },
            headers=self._get_headers(),
        ) as response:
            return await response.json()

    async def get_image(self, path: str) -> PIL.Image.Image:
        """Get an image from the server"""
        async with aiohttp.request("GET", f"{self.http_endpoint}/image?path={path}", headers=self._get_headers()) as response:
            return PIL.Image.open(BytesIO(await response.read()))

    async def stop_task(self, exec_id: str) -> dict[str, Any]:
        """Stop a task execution"""
        async with aiohttp.request(
            "POST", f"{self.http_endpoint}/tasks/stop", json={"exec_id": exec_id}, headers=self._get_headers()
        ) as response:
            response.raise_for_status()
            return await response.json()
