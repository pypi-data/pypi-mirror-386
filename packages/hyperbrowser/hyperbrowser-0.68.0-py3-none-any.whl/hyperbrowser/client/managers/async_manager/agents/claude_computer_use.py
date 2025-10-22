import asyncio

from hyperbrowser.exceptions import HyperbrowserError

from .....models import (
    POLLING_ATTEMPTS,
    BasicResponse,
    ClaudeComputerUseTaskResponse,
    ClaudeComputerUseTaskStatusResponse,
    StartClaudeComputerUseTaskParams,
    StartClaudeComputerUseTaskResponse,
)


class ClaudeComputerUseManager:
    def __init__(self, client):
        self._client = client

    async def start(
        self, params: StartClaudeComputerUseTaskParams
    ) -> StartClaudeComputerUseTaskResponse:
        response = await self._client.transport.post(
            self._client._build_url("/task/claude-computer-use"),
            data=params.model_dump(exclude_none=True, by_alias=True),
        )
        return StartClaudeComputerUseTaskResponse(**response.data)

    async def get(self, job_id: str) -> ClaudeComputerUseTaskResponse:
        response = await self._client.transport.get(
            self._client._build_url(f"/task/claude-computer-use/{job_id}")
        )
        return ClaudeComputerUseTaskResponse(**response.data)

    async def get_status(self, job_id: str) -> ClaudeComputerUseTaskStatusResponse:
        response = await self._client.transport.get(
            self._client._build_url(f"/task/claude-computer-use/{job_id}/status")
        )
        return ClaudeComputerUseTaskStatusResponse(**response.data)

    async def stop(self, job_id: str) -> BasicResponse:
        response = await self._client.transport.put(
            self._client._build_url(f"/task/claude-computer-use/{job_id}/stop")
        )
        return BasicResponse(**response.data)

    async def start_and_wait(
        self, params: StartClaudeComputerUseTaskParams
    ) -> ClaudeComputerUseTaskResponse:
        job_start_resp = await self.start(params)
        job_id = job_start_resp.job_id
        if not job_id:
            raise HyperbrowserError("Failed to start Claude Computer Use task job")

        failures = 0
        while True:
            try:
                job_response = await self.get_status(job_id)
                if (
                    job_response.status == "completed"
                    or job_response.status == "failed"
                    or job_response.status == "stopped"
                ):
                    return await self.get(job_id)
                failures = 0
            except Exception as e:
                failures += 1
                if failures >= POLLING_ATTEMPTS:
                    raise HyperbrowserError(
                        f"Failed to poll Claude Computer Use task job {job_id} after {POLLING_ATTEMPTS} attempts: {e}"
                    )
            await asyncio.sleep(2)
