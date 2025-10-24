"""MCP Package Hero - FastMCP server for package version lookups."""

from typing import Any, Literal

import httpx
from fastmcp import FastMCP

from .llms_txt_client import LLMsTxtClient
from .llms_txt_generator import LLMsTxtGenerator
from .models import (
    BatchPackageResponse,
    Ecosystem,
    PackageVersion,
)
from .raters import DartPackageRater, JavaScriptPackageRater, PythonPackageRater, RustPackageRater
from .registries import CratesRegistry, NpmRegistry, PubDevRegistry, PyPIRegistry

# Initialize FastMCP server
mcp = FastMCP(
    name="Package Hero",
    instructions="Get the latest package versions, comprehensive quality ratings, and llms.txt documentation from PyPI, npm, pub.dev, and crates.io",
    version="1.3.0",
)

# Initialize registry clients
pypi = PyPIRegistry()
npm = NpmRegistry()
pubdev = PubDevRegistry()
crates = CratesRegistry()

# Initialize rater clients
python_rater = PythonPackageRater()
javascript_rater = JavaScriptPackageRater()
dart_rater = DartPackageRater()
rust_rater = RustPackageRater()

# Initialize llms.txt clients
llms_txt_client = LLMsTxtClient()
llms_txt_generator = LLMsTxtGenerator()


def get_registry(ecosystem: str):
    """Get the appropriate registry client for an ecosystem."""
    if ecosystem == Ecosystem.PYTHON.value:
        return pypi
    if ecosystem == Ecosystem.JAVASCRIPT.value:
        return npm
    if ecosystem == Ecosystem.DART.value:
        return pubdev
    if ecosystem == Ecosystem.RUST.value:
        return crates
    raise ValueError(f"Unsupported ecosystem: {ecosystem}")


def get_rater(ecosystem: str):
    """Get the appropriate rater client for an ecosystem."""
    if ecosystem == Ecosystem.PYTHON.value:
        return python_rater
    if ecosystem == Ecosystem.JAVASCRIPT.value:
        return javascript_rater
    if ecosystem == Ecosystem.DART.value:
        return dart_rater
    if ecosystem == Ecosystem.RUST.value:
        return rust_rater
    raise ValueError(f"Unsupported ecosystem: {ecosystem}")


@mcp.tool()
async def get_latest_version(
    package_name: str,
    ecosystem: Literal["python", "javascript", "dart", "rust"],
) -> dict[str, Any]:
    """
    Get the latest stable version of a package.

    Args:
        package_name: The name of the package (e.g., "requests", "react", "http", "serde")
        ecosystem: The package ecosystem - one of: "python", "javascript", "dart", or "rust"

    Returns:
        Dictionary with package information including:
        - package_name: Name of the package
        - ecosystem: The ecosystem (python/javascript/dart)
        - latest_version: Latest stable version number (or None if not found)
        - registry_url: Link to the package on its registry
        - status: "success", "not_found", or "error"
        - error_message: Error details if status is not "success"

    Examples:
        get_latest_version("requests", "python")
        get_latest_version("react", "javascript")
        get_latest_version("http", "dart")
        get_latest_version("serde", "rust")

    """
    registry = get_registry(ecosystem)
    result = await registry.get_latest_version(package_name)
    return result.model_dump(mode="json")  # type: ignore[no-any-return]


@mcp.tool()
async def get_latest_versions_batch(
    packages: list[dict[str, str]],
    max_packages: int = 10,
) -> dict[str, Any]:
    """
    Get latest versions for multiple packages at once.

    Args:
        packages: List of dictionaries, each with 'package_name' and 'ecosystem' keys
        max_packages: Maximum number of packages to check (default: 10, hard limit)

    Returns:
        Dictionary with:
        - results: Array of version information for each package
        - checked_at: Timestamp when the batch check was performed

    Examples:
        get_latest_versions_batch([
            {"package_name": "requests", "ecosystem": "python"},
            {"package_name": "react", "ecosystem": "javascript"},
            {"package_name": "http", "ecosystem": "dart"},
            {"package_name": "serde", "ecosystem": "rust"}
        ])

    """
    # Validate and limit number of packages
    if len(packages) > max_packages:
        raise ValueError(
            f"Too many packages requested. Maximum is {max_packages}, got {len(packages)}",
        )

    results = []
    for package in packages:
        package_name = package.get("package_name")
        ecosystem = package.get("ecosystem")

        if not package_name or not ecosystem:
            # Create error response for invalid input
            results.append(
                PackageVersion(
                    package_name=package_name or "unknown",
                    ecosystem=ecosystem or Ecosystem.PYTHON,
                    latest_version=None,
                    status="error",
                    error_message="Missing package_name or ecosystem",
                ).model_dump(mode="json"),
            )
            continue

        try:
            registry = get_registry(ecosystem)
            result = await registry.get_latest_version(package_name)
            results.append(result.model_dump(mode="json"))
        except Exception as e:
            results.append(
                PackageVersion(
                    package_name=package_name,
                    ecosystem=ecosystem,
                    latest_version=None,
                    status="error",
                    error_message=str(e),
                ).model_dump(mode="json"),
            )

    return BatchPackageResponse(results=results).model_dump(mode="json")


@mcp.tool()
async def rate_package(
    package_name: str,
    ecosystem: Literal["python", "javascript", "dart", "rust"],
) -> dict[str, Any]:
    """
    Get a comprehensive quality rating for a package.

    This tool analyzes multiple dimensions of package quality including:
    - Maintenance health (release frequency, issue resolution, PR activity)
    - Popularity and adoption (downloads, stars, dependents)
    - Quality metrics (documentation, license, tests)

    Args:
        package_name: The name of the package (e.g., "requests", "react", "http", "serde")
        ecosystem: The package ecosystem - one of: "python", "javascript", "dart", or "rust"

    Returns:
        Dictionary with comprehensive package rating including:
        - overall_score: Overall rating score (0-100)
        - letter_grade: Letter grade (A+ to F)
        - maintenance: Maintenance health score and components
        - popularity: Popularity score and metrics
        - quality: Quality score and indicators
        - repository_url: GitHub repository URL if available
        - license: License type
        - description: Package description
        - insights: Key positive insights about the package
        - red_flags: Warning signs or concerns
        - status: "success", "not_found", or "error"

    Examples:
        rate_package("requests", "python")
        rate_package("react", "javascript")
        rate_package("http", "dart")
        rate_package("serde", "rust")

    """
    rater = get_rater(ecosystem)
    result = await rater.rate_package(package_name)
    return result.model_dump(mode="json")  # type: ignore[no-any-return]


async def _fetch_registry_data(package_name: str, ecosystem: str) -> dict[str, Any] | None:
    """
    Fetch raw package data from registry.

    Args:
        package_name: Name of the package
        ecosystem: Package ecosystem

    Returns:
        Raw registry data or None if not found
    """
    registry_urls = {
        "python": f"https://pypi.org/pypi/{package_name}/json",
        "javascript": f"https://registry.npmjs.org/{package_name}",
        "dart": f"https://pub.dev/api/packages/{package_name}",
        "rust": f"https://crates.io/api/v1/crates/{package_name}",
    }

    url = registry_urls.get(ecosystem)
    if not url:
        return None

    try:
        async with httpx.AsyncClient() as client:
            # crates.io requires a User-Agent header
            headers = {}
            if ecosystem == "rust":
                headers["User-Agent"] = "mcp-package-hero (https://github.com/moinsen-dev/mcp-package-hero)"

            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
    except httpx.HTTPError:
        return None


@mcp.tool()
async def get_llms_txt(
    package_name: str,
    ecosystem: Literal["python", "javascript", "dart", "rust"],
    include_full: bool = False,
) -> dict[str, Any]:
    """
    Get llms.txt documentation file for a package.

    llms.txt is an emerging standard for providing LLM-friendly documentation.
    This tool fetches llms.txt files from package repositories, homepages, or documentation sites.

    Args:
        package_name: The name of the package (e.g., "requests", "react", "http", "serde")
        ecosystem: The package ecosystem - one of: "python", "javascript", "dart", or "rust"
        include_full: Whether to also fetch llms-full.txt (optional, default: False)

    Returns:
        Dictionary with llms.txt information including:
        - package_name: Name of the package
        - ecosystem: Package ecosystem
        - llms_txt_content: Parsed llms.txt content with project name, summary, and sections
        - llms_full_txt_content: Full documentation text (if requested and available)
        - source_url: URL where llms.txt was found
        - source_type: Type of source (github_main, homepage, etc.)
        - repository_url: Package repository URL
        - homepage_url: Package homepage URL
        - status: "success", "not_found", or "error"

    Examples:
        get_llms_txt("fasthtml", "python")
        get_llms_txt("react", "javascript", include_full=True)
        get_llms_txt("flutter_bloc", "dart")
        get_llms_txt("tokio", "rust")

    """
    # Fetch registry data
    registry_data = await _fetch_registry_data(package_name, ecosystem)

    if not registry_data:
        return {
            "package_name": package_name,
            "ecosystem": ecosystem,
            "status": "not_found",
            "error_message": f"Package '{package_name}' not found in {ecosystem} registry",
        }

    # Fetch llms.txt
    result = await llms_txt_client.fetch_for_package(
        package_name=package_name,
        ecosystem=ecosystem,
        registry_data=registry_data,
        include_full=include_full,
    )

    return result.model_dump(mode="json")  # type: ignore[no-any-return]


@mcp.tool()
async def create_llms_txt(
    project_name: str,
    description: str,
    scan_directory: str = ".",
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generate an llms.txt file for your project.

    Creates a standardized llms.txt file by scanning your project directory
    for documentation files and generating structured markdown.

    Args:
        project_name: Name of your project
        description: Brief project description (will appear in blockquote)
        scan_directory: Directory to scan for documentation (default: current directory)
        sections: Specific sections to include (optional, e.g., ["documentation", "examples", "api"])
                 Available sections: documentation, examples, api, guides, configuration

    Returns:
        Dictionary with generated llms.txt:
        - content: Generated llms.txt markdown content
        - discovered_files: Files found by category
        - suggested_path: Suggested file path to save
        - status: "success" or "error"

    Examples:
        create_llms_txt("My Project", "A great Python library")
        create_llms_txt("React App", "Modern web application", sections=["documentation", "examples"])
        create_llms_txt("API Server", "REST API service", scan_directory="./docs")

    """
    result = await llms_txt_generator.generate(
        project_name=project_name,
        description=description,
        scan_directory=scan_directory,
        sections=sections,
        include_file_tree=True,
    )

    return result.model_dump(mode="json")  # type: ignore[no-any-return]


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
