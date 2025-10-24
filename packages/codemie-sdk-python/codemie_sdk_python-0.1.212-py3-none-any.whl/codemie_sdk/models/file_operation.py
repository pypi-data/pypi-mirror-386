"""File operation models."""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class FileResponse(BaseModel):
    """Individual file response model."""

    model_config = ConfigDict(extra="ignore")

    file_url: str = Field(..., description="URL or identifier for the uploaded file")


class FileBulkCreateResponse(BaseModel):
    """Response model for bulk file creation."""

    model_config = ConfigDict(extra="ignore")

    files: List[FileResponse] = Field(
        ..., description="List of successfully uploaded files with their URLs"
    )
    failed_files: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of files that failed to upload, null if no failures"
    )
