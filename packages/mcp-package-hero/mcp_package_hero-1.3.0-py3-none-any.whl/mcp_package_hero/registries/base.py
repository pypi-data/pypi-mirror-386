"""Base class for package registry clients."""

from abc import ABC, abstractmethod

from ..models import Ecosystem, PackageVersion, VersionStatus


class BaseRegistry(ABC):
    """Abstract base class for package registry integrations."""

    def __init__(self, ecosystem: Ecosystem, base_url: str):
        """
        Initialize the registry client.

        Args:
            ecosystem: The ecosystem this registry serves
            base_url: Base URL for the registry API

        """
        self.ecosystem = ecosystem
        self.base_url = base_url

    @abstractmethod
    async def get_latest_version(self, package_name: str) -> PackageVersion:
        """
        Get the latest version of a package.

        Args:
            package_name: Name of the package to look up

        Returns:
            PackageVersion object with version information

        """

    def _create_not_found_response(
        self, package_name: str, error_msg: str | None = None,
    ) -> PackageVersion:
        """
        Create a not-found response.

        Args:
            package_name: Name of the package
            error_msg: Optional error message

        Returns:
            PackageVersion with not_found status

        """
        return PackageVersion(
            package_name=package_name,
            ecosystem=self.ecosystem,
            latest_version=None,
            registry_url=None,
            status=VersionStatus.NOT_FOUND,
            error_message=error_msg or f"Package '{package_name}' not found",
        )

    def _create_error_response(
        self, package_name: str, error_msg: str,
    ) -> PackageVersion:
        """
        Create an error response.

        Args:
            package_name: Name of the package
            error_msg: Error message

        Returns:
            PackageVersion with error status

        """
        return PackageVersion(
            package_name=package_name,
            ecosystem=self.ecosystem,
            latest_version=None,
            registry_url=None,
            status=VersionStatus.ERROR,
            error_message=error_msg,
        )
