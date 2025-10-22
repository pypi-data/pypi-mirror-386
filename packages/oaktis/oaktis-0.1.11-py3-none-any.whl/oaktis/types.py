"""
Oaktis SDK Type Definitions
"""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class VideoGenerateParams(BaseModel):
    """Parameters for video generation"""

    prompt: str = Field(..., description="Text prompt describing the video to generate")
    duration: Optional[int] = Field(None, description="Video duration in seconds")
    resolution: Optional[Literal["720p", "1080p", "4k"]] = Field(
        None, description="Video resolution"
    )

    class Config:
        extra = "allow"  # Allow additional fields


class ImageGenerateParams(BaseModel):
    """Parameters for image generation"""

    prompt: str = Field(..., description="Text prompt describing the image to generate")
    size: Optional[Literal["512x512", "1024x1024", "1024x1792", "1792x1024"]] = Field(
        None, description="Image size"
    )
    n: Optional[int] = Field(None, description="Number of images to generate")

    class Config:
        extra = "allow"  # Allow additional fields


class Job(BaseModel):
    """Base job information"""

    id: str = Field(..., description="Unique job identifier")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ..., description="Job status"
    )
    created_at: str = Field(..., alias="createdAt", description="Creation timestamp")
    updated_at: str = Field(..., alias="updatedAt", description="Last update timestamp")
    error: Optional[str] = Field(None, description="Error message if job failed")

    class Config:
        populate_by_name = True


class VideoJob(Job):
    """Video generation job"""

    params: Dict[str, Any] = Field(..., description="Video generation parameters")
    video_url: Optional[str] = Field(
        None, alias="videoUrl", description="Generated video URL (when completed)"
    )
    thumbnail_url: Optional[str] = Field(
        None, alias="thumbnailUrl", description="Thumbnail URL (when completed)"
    )


class ImageJob(Job):
    """Image generation job"""

    params: Dict[str, Any] = Field(..., description="Image generation parameters")
    image_urls: Optional[list[str]] = Field(
        None, alias="imageUrls", description="Generated image URLs (when completed)"
    )


class JobStatus(BaseModel):
    """Job status information"""

    id: str = Field(..., description="Job identifier")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ..., description="Current status"
    )
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    estimated_time: Optional[int] = Field(
        None, alias="estimatedTime", description="Estimated time remaining in seconds"
    )
    error: Optional[str] = Field(None, description="Error details if failed")

    class Config:
        populate_by_name = True


class APIError(Exception):
    """API Error exception"""

    def __init__(
        self, code: str, message: str, status: int, details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status = status
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message} (HTTP {self.status})"

    def __repr__(self) -> str:
        return f"APIError(code='{self.code}', message='{self.message}', status={self.status})"
