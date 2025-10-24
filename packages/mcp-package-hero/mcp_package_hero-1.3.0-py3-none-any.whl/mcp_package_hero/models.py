"""Data models for MCP Package Hero."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Ecosystem(str, Enum):
    """Supported package ecosystems."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    DART = "dart"
    RUST = "rust"


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


class LetterGrade(str, Enum):
    """Letter grade for package rating."""

    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D = "D"
    F = "F"


class MaintenanceScore(BaseModel):
    """Maintenance health score components."""

    model_config = ConfigDict(use_enum_values=True)

    score: float = Field(..., ge=0, le=100, description="Overall maintenance score (0-100)")
    last_release_days: int | None = Field(None, description="Days since last release")
    release_frequency_score: float = Field(..., ge=0, le=100, description="Release frequency score")
    issue_resolution_score: float = Field(..., ge=0, le=100, description="Issue resolution score")
    pr_merge_score: float = Field(..., ge=0, le=100, description="PR merge score")


class PopularityScore(BaseModel):
    """Popularity and adoption score components."""

    model_config = ConfigDict(use_enum_values=True)

    score: float = Field(..., ge=0, le=100, description="Overall popularity score (0-100)")
    downloads: int | None = Field(None, description="Download count (30 days)")
    stars: int | None = Field(None, description="GitHub stars")
    dependents: int | None = Field(None, description="Number of dependents")
    downloads_score: float = Field(..., ge=0, le=100, description="Downloads score")
    stars_score: float = Field(..., ge=0, le=100, description="Stars score")


class QualityScore(BaseModel):
    """Quality metrics score components."""

    model_config = ConfigDict(use_enum_values=True)

    score: float = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    has_documentation: bool = Field(..., description="Has README/documentation")
    has_license: bool = Field(..., description="Has license")
    has_tests: bool | None = Field(None, description="Has test indicators")
    has_llms_txt: bool | None = Field(None, description="Has llms.txt file")
    has_llms_full_txt: bool | None = Field(None, description="Has llms-full.txt file")
    documentation_score: float = Field(..., ge=0, le=100, description="Documentation score")
    license_score: float = Field(..., ge=0, le=100, description="License score")
    test_score: float = Field(..., ge=0, le=100, description="Test score")
    llms_txt_score: float = Field(..., ge=0, le=100, description="llms.txt documentation score")


class PackageRating(BaseModel):
    """Comprehensive package rating."""

    model_config = ConfigDict(use_enum_values=True)

    package_name: str = Field(..., description="Name of the package")
    ecosystem: Ecosystem = Field(..., description="Package ecosystem")
    overall_score: float = Field(..., ge=0, le=100, description="Overall rating score (0-100)")
    letter_grade: LetterGrade = Field(..., description="Letter grade (A+ to F)")

    maintenance: MaintenanceScore = Field(..., description="Maintenance health score")
    popularity: PopularityScore = Field(..., description="Popularity score")
    quality: QualityScore = Field(..., description="Quality score")

    repository_url: str | None = Field(None, description="GitHub repository URL")
    license: str | None = Field(None, description="License type")
    description: str | None = Field(None, description="Package description")

    insights: list[str] = Field(default_factory=list, description="Key insights and recommendations")
    red_flags: list[str] = Field(default_factory=list, description="Warning signs or concerns")

    rated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of rating",
    )
    status: VersionStatus = Field(
        default=VersionStatus.SUCCESS, description="Status of the rating",
    )
    error_message: str | None = Field(None, description="Error message if failed")
