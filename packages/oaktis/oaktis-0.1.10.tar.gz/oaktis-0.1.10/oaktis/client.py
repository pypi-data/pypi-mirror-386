"""
Oaktis API Client
"""

import httpx
from typing import Any, Dict, Optional

from .types import (
    VideoGenerateParams,
    ImageGenerateParams,
    VideoJob,
    ImageJob,
    JobStatus,
    APIError,
)


class VideoAPI:
    """Video generation API"""

    def __init__(self, client: "OaktisClient"):
        self._client = client

    async def generate(self, params: VideoGenerateParams) -> VideoJob:
        """Generate a video from a text prompt"""
        response = await self._client._request(
            "POST", "/v1/video/generate", json=params.model_dump(exclude_none=True)
        )
        return VideoJob(**response)

    def generate_sync(self, params: VideoGenerateParams) -> VideoJob:
        """Generate a video from a text prompt (sync version)"""
        response = self._client._request_sync(
            "POST", "/v1/video/generate", json=params.model_dump(exclude_none=True)
        )
        return VideoJob(**response)

    async def get_status(self, job_id: str) -> JobStatus:
        """Get the status of a video generation job"""
        response = await self._client._request("GET", f"/v1/video/jobs/{job_id}")
        return JobStatus(**response)

    def get_status_sync(self, job_id: str) -> JobStatus:
        """Get the status of a video generation job (sync version)"""
        response = self._client._request_sync("GET", f"/v1/video/jobs/{job_id}")
        return JobStatus(**response)

    async def get_job(self, job_id: str) -> VideoJob:
        """Get video job details"""
        response = await self._client._request("GET", f"/v1/video/jobs/{job_id}/details")
        return VideoJob(**response)

    def get_job_sync(self, job_id: str) -> VideoJob:
        """Get video job details (sync version)"""
        response = self._client._request_sync("GET", f"/v1/video/jobs/{job_id}/details")
        return VideoJob(**response)


class ImageAPI:
    """Image generation API"""

    def __init__(self, client: "OaktisClient"):
        self._client = client

    async def generate(self, params: ImageGenerateParams) -> ImageJob:
        """Generate an image from a text prompt"""
        response = await self._client._request(
            "POST", "/v1/image/generate", json=params.model_dump(exclude_none=True)
        )
        return ImageJob(**response)

    def generate_sync(self, params: ImageGenerateParams) -> ImageJob:
        """Generate an image from a text prompt (sync version)"""
        response = self._client._request_sync(
            "POST", "/v1/image/generate", json=params.model_dump(exclude_none=True)
        )
        return ImageJob(**response)

    async def get_status(self, job_id: str) -> JobStatus:
        """Get the status of an image generation job"""
        response = await self._client._request("GET", f"/v1/image/jobs/{job_id}")
        return JobStatus(**response)

    def get_status_sync(self, job_id: str) -> JobStatus:
        """Get the status of an image generation job (sync version)"""
        response = self._client._request_sync("GET", f"/v1/image/jobs/{job_id}")
        return JobStatus(**response)

    async def get_job(self, job_id: str) -> ImageJob:
        """Get image job details"""
        response = await self._client._request("GET", f"/v1/image/jobs/{job_id}/details")
        return ImageJob(**response)

    def get_job_sync(self, job_id: str) -> ImageJob:
        """Get image job details (sync version)"""
        response = self._client._request_sync("GET", f"/v1/image/jobs/{job_id}/details")
        return ImageJob(**response)


class OaktisClient:
    """
    Oaktis API Client

    Example:
        >>> import asyncio
        >>> from oaktis import OaktisClient, VideoGenerateParams
        >>>
        >>> async def main():
        ...     client = OaktisClient(api_key="your-api-key")
        ...     job = await client.video.generate(
        ...         VideoGenerateParams(prompt="a cat surfing")
        ...     )
        ...     print(job.id)
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.oaktis.com",
        timeout: float = 60.0,
    ):
        """
        Initialize Oaktis client

        Args:
            api_key: API key for authentication
            base_url: Base URL for the Oaktis API
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Initialize API namespaces
        self.video = VideoAPI(self)
        self.image = ImageAPI(self)

        # HTTP client (lazy initialization)
        self._async_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Oaktis-Ref": "pypi-sdk",
        }

    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Make an async request to the Oaktis API"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)

        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = await self._async_client.request(
                method, url, headers=headers, **kwargs
            )

            if not response.is_success:
                error_data = response.json() if response.text else {}
                raise APIError(
                    code=error_data.get("code", "API_ERROR"),
                    message=error_data.get(
                        "message", f"HTTP {response.status_code}: {response.reason_phrase}"
                    ),
                    status=response.status_code,
                    details=error_data,
                )

            return response.json()

        except httpx.TimeoutException:
            raise APIError(
                code="TIMEOUT",
                message=f"Request timeout after {self.timeout}s",
                status=0,
            )

    def _request_sync(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Make a sync request to the Oaktis API"""
        if self._sync_client is None:
            self._sync_client = httpx.Client(timeout=self.timeout)

        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = self._sync_client.request(
                method, url, headers=headers, **kwargs
            )

            if not response.is_success:
                error_data = response.json() if response.text else {}
                raise APIError(
                    code=error_data.get("code", "API_ERROR"),
                    message=error_data.get(
                        "message", f"HTTP {response.status_code}: {response.reason_phrase}"
                    ),
                    status=response.status_code,
                    details=error_data,
                )

            return response.json()

        except httpx.TimeoutException:
            raise APIError(
                code="TIMEOUT",
                message=f"Request timeout after {self.timeout}s",
                status=0,
            )

    async def close(self) -> None:
        """Close the async HTTP client"""
        if self._async_client:
            await self._async_client.aclose()

    def close_sync(self) -> None:
        """Close the sync HTTP client"""
        if self._sync_client:
            self._sync_client.close()

    async def __aenter__(self) -> "OaktisClient":
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()

    def __enter__(self) -> "OaktisClient":
        """Sync context manager entry"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Sync context manager exit"""
        self.close_sync()
