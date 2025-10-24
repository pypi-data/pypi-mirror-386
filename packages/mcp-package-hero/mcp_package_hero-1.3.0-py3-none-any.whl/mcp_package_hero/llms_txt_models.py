"""Data models for llms.txt functionality."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LLMsTxtStatus(str, Enum):
    """Status of llms.txt operation."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"


class LLMsTxtSource(str, Enum):
    """Source where llms.txt was found."""

    GITHUB_MAIN = "github_main"
    GITHUB_MASTER = "github_master"
    GITHUB_DEVELOP = "github_develop"
    HOMEPAGE = "homepage"
    REGISTRY = "registry"
    GENERATED = "generated"


class LLMsTxtSection(BaseModel):
    """A section in an llms.txt file."""

    model_config = ConfigDict(use_enum_values=True)

    title: str = Field(..., description="Section title (H2)")
    links: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of links with 'url', 'title', and optional 'description'",
    )


class LLMsTxtContent(BaseModel):
    """Parsed llms.txt content."""

    model_config = ConfigDict(use_enum_values=True)

    project_name: str = Field(..., description="Project name from H1")
    summary: str | None = Field(None, description="Summary from blockquote")
    description: str | None = Field(None, description="Additional description paragraphs")
    sections: list[LLMsTxtSection] = Field(
        default_factory=list,
        description="H2 sections with links",
    )
    raw_content: str = Field(..., description="Raw markdown content")
    is_valid: bool = Field(
        default=True,
        description="Whether content follows llms.txt spec",
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings if format is non-standard",
    )


class LLMsTxtResponse(BaseModel):
    """Response for get_llms_txt tool."""

    model_config = ConfigDict(use_enum_values=True)

    package_name: str = Field(..., description="Name of the package")
    ecosystem: str = Field(..., description="Package ecosystem")

    llms_txt_content: LLMsTxtContent | None = Field(
        None,
        description="Parsed llms.txt content",
    )
    llms_full_txt_content: str | None = Field(
        None,
        description="Raw llms-full.txt content if requested",
    )

    source_url: str | None = Field(None, description="URL where llms.txt was found")
    source_type: LLMsTxtSource | None = Field(None, description="Type of source")

    repository_url: str | None = Field(None, description="Package repository URL")
    homepage_url: str | None = Field(None, description="Package homepage URL")

    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when fetched",
    )
    status: LLMsTxtStatus = Field(
        default=LLMsTxtStatus.SUCCESS,
        description="Status of the operation",
    )
    error_message: str | None = Field(None, description="Error message if failed")


class LLMsTxtGenerateRequest(BaseModel):
    """Request for creating llms.txt."""

    model_config = ConfigDict(use_enum_values=True)

    project_name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Brief project description")
    scan_directory: str = Field(default=".", description="Directory to scan")
    sections: list[str] | None = Field(
        None,
        description="Sections to include (e.g., ['documentation', 'examples', 'api'])",
    )
    include_file_tree: bool = Field(
        default=True,
        description="Include discovered files in sections",
    )


class LLMsTxtGenerateResponse(BaseModel):
    """Response for create_llms_txt tool."""

    model_config = ConfigDict(use_enum_values=True)

    content: str = Field(..., description="Generated llms.txt content")
    discovered_files: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Files discovered by category",
    )

    suggested_path: str = Field(
        default="llms.txt",
        description="Suggested file path to save",
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when generated",
    )
    status: LLMsTxtStatus = Field(
        default=LLMsTxtStatus.SUCCESS,
        description="Status of the operation",
    )
    error_message: str | None = Field(None, description="Error message if failed")
