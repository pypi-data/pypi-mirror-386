"""crates.io registry client."""

import httpx

from ..models import Ecosystem, PackageVersion, VersionStatus
from .base import BaseRegistry


class CratesRegistry(BaseRegistry):
    """Client for crates.io package registry."""

    def __init__(self, base_url: str = "https://crates.io/api/v1"):
        """Initialize crates.io registry client."""
        super().__init__(Ecosystem.RUST, base_url)

    async def get_latest_version(self, package_name: str) -> PackageVersion:
        """
        Get the latest version from crates.io.

        Args:
            package_name: Name of the Rust crate

        Returns:
            PackageVersion with latest version info

        """
        url = f"{self.base_url}/crates/{package_name}"

        try:
            async with httpx.AsyncClient() as client:
                # crates.io requires a User-Agent header
                headers = {"User-Agent": "mcp-package-hero (https://github.com/moinsen-dev/mcp-package-hero)"}
                response = await client.get(url, headers=headers, timeout=10.0)

                if response.status_code == 404:
                    return self._create_not_found_response(package_name)

                response.raise_for_status()

                data = response.json()
                crate = data.get("crate", {})
                version = crate.get("max_version")

                if not version:
                    return self._create_error_response(
                        package_name, "Version information not found in response",
                    )

                return PackageVersion(
                    package_name=package_name,
                    ecosystem=self.ecosystem,
                    latest_version=version,
                    registry_url=f"https://crates.io/crates/{package_name}",
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
