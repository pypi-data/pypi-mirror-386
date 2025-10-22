"""
Oaktis SDK for Python
Official client library for the Oaktis API

Example:
    >>> import asyncio
    >>> from oaktis import OaktisClient, VideoGenerateParams
    >>>
    >>> async def main():
    ...     client = OaktisClient(api_key="your-api-key")
    ...     job = await client.video.generate(
    ...         VideoGenerateParams(prompt="a cat surfing")
    ...     )
    ...     print(f"Job ID: {job.id}")
    >>>
    >>> asyncio.run(main())
"""

__version__ = "0.1.0"

from .client import OaktisClient, VideoAPI, ImageAPI
from .types import (
    VideoGenerateParams,
    ImageGenerateParams,
    VideoJob,
    ImageJob,
    JobStatus,
    APIError,
)

__all__ = [
    # Client
    "OaktisClient",
    "VideoAPI",
    "ImageAPI",
    # Types
    "VideoGenerateParams",
    "ImageGenerateParams",
    "VideoJob",
    "ImageJob",
    "JobStatus",
    "APIError",
    # Version
    "__version__",
]
