"""PyPI registry client."""

import httpx

from ..models import Ecosystem, PackageVersion, VersionStatus
from .base import BaseRegistry


class PyPIRegistry(BaseRegistry):
    """Client for PyPI package registry."""

    def __init__(self, base_url: str = "https://pypi.org/pypi"):
        """Initialize PyPI registry client."""
        super().__init__(Ecosystem.PYTHON, base_url)

    async def get_latest_version(self, package_name: str) -> PackageVersion:
        """
        Get the latest version from PyPI.

        Args:
            package_name: Name of the Python package

        Returns:
            PackageVersion with latest version info

        """
        url = f"{self.base_url}/{package_name}/json"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)

                if response.status_code == 404:
                    return self._create_not_found_response(package_name)

                response.raise_for_status()

                data = response.json()
                version = data.get("info", {}).get("version")

                if not version:
                    return self._create_error_response(
                        package_name, "Version information not found in response",
                    )

                return PackageVersion(
                    package_name=package_name,
                    ecosystem=self.ecosystem,
                    latest_version=version,
                    registry_url=f"https://pypi.org/project/{package_name}/",
                    status=VersionStatus.SUCCESS,
                )

        except httpx.HTTPStatusError as e:
            return self._create_error_response(
                package_name, f"HTTP error: {e.response.status_code}",
            )
        except httpx.RequestError as e:
            return self._create_error_response(
                package_name, f"Request failed: {e!s}",
            )
        except Exception as e:
            return self._create_error_response(
                package_name, f"Unexpected error: {e!s}",
            )
