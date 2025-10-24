"""MCP Package Hero - FastMCP server for package version lookups."""

from typing import Any, Literal

from fastmcp import FastMCP

from .models import (
    BatchPackageResponse,
    Ecosystem,
    PackageVersion,
)
from .registries import NpmRegistry, PubDevRegistry, PyPIRegistry

# Initialize FastMCP server
mcp = FastMCP(
    name="Package Hero",
    instructions="Get the latest package versions from PyPI, npm, and pub.dev",
    version="1.0.0",
)

# Initialize registry clients
pypi = PyPIRegistry()
npm = NpmRegistry()
pubdev = PubDevRegistry()


def get_registry(ecosystem: str):
    """Get the appropriate registry client for an ecosystem."""
    if ecosystem == Ecosystem.PYTHON.value:
        return pypi
    if ecosystem == Ecosystem.JAVASCRIPT.value:
        return npm
    if ecosystem == Ecosystem.DART.value:
        return pubdev
    raise ValueError(f"Unsupported ecosystem: {ecosystem}")


@mcp.tool()
async def get_latest_version(
    package_name: str,
    ecosystem: Literal["python", "javascript", "dart"],
) -> dict[str, Any]:
    """
    Get the latest stable version of a package.

    Args:
        package_name: The name of the package (e.g., "requests", "react", "http")
        ecosystem: The package ecosystem - one of: "python", "javascript", or "dart"

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
            {"package_name": "http", "ecosystem": "dart"}
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


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
