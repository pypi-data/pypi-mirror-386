"""Data models for MCP Package Hero."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Ecosystem(str, Enum):
    """Supported package ecosystems."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    DART = "dart"


class VersionStatus(str, Enum):
    """Status of version check."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"


class PackageVersion(BaseModel):
    """Package version information."""

    model_config = ConfigDict(use_enum_values=True)

    package_name: str = Field(..., description="Name of the package")
    ecosystem: Ecosystem = Field(..., description="Package ecosystem")
    latest_version: str | None = Field(None, description="Latest stable version")
    registry_url: str | None = Field(None, description="Link to package registry")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of version check",
    )
    status: VersionStatus = Field(
        default=VersionStatus.SUCCESS, description="Status of the check",
    )
    error_message: str | None = Field(None, description="Error message if failed")


class BatchPackageRequest(BaseModel):
    """Request for batch package version check."""

    package_name: str = Field(..., description="Name of the package")
    ecosystem: Ecosystem = Field(..., description="Package ecosystem")


class BatchPackageResponse(BaseModel):
    """Response for batch package version check."""

    results: list[PackageVersion] = Field(..., description="List of version results")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of batch check",
    )
