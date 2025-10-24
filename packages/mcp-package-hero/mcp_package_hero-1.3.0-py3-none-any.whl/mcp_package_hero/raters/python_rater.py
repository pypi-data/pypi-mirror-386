"""Python package rating implementation."""

from datetime import datetime, timezone

import httpx

from mcp_package_hero.github_client import GitHubClient
from mcp_package_hero.llms_txt_client import LLMsTxtClient
from mcp_package_hero.models import Ecosystem, PackageRating, VersionStatus
from mcp_package_hero.rating_calculator import RatingCalculator


class PythonPackageRater:
    """Rates Python packages from PyPI."""

    def __init__(self, github_token: str | None = None) -> None:
        """Initialize Python package rater.

        Args:
            github_token: Optional GitHub token for higher rate limits
        """
        self.pypi_base_url = "https://pypi.org/pypi"
        self.pypistats_base_url = "https://pypistats.org/api"
        self.github_client = GitHubClient(github_token)
        self.llms_txt_client = LLMsTxtClient()

    async def rate_package(self, package_name: str) -> PackageRating:
        """Rate a Python package.

        Args:
            package_name: Name of the package on PyPI

        Returns:
            PackageRating object with comprehensive rating
        """
        try:
            # Get PyPI metadata
            pypi_data = await self._get_pypi_data(package_name)
            if not pypi_data:
                return self._create_not_found_response(package_name)

            # Extract basic info
            info = pypi_data.get("info", {})
            description = info.get("summary") or info.get("description", "")[:200]
            license_name = info.get("license")
            project_urls = info.get("project_urls", {})

            # Find GitHub repository
            repo_url = self._find_github_repo(info, project_urls)
            github_metrics = None
            issue_stats = {"open_issues": 0, "closed_issues_30d": 0}
            pr_stats = {"open_prs": 0, "merged_prs_30d": 0}

            if repo_url:
                repo_info = GitHubClient.extract_repo_from_url(repo_url)
                if repo_info:
                    owner, repo = repo_info
                    github_metrics = await self.github_client.get_repo_metrics(owner, repo)
                    issue_stats = await self.github_client.get_issue_stats(owner, repo)
                    pr_stats = await self.github_client.get_pr_stats(owner, repo)

            # Get download stats
            downloads = await self._get_download_stats(package_name)

            # Calculate last release date
            releases = pypi_data.get("releases", {})
            last_release_days = self._calculate_last_release_days(releases)

            # Calculate scores
            maintenance = RatingCalculator.calculate_maintenance_score(
                last_release_days=last_release_days,
                open_issues=issue_stats["open_issues"],
                closed_issues_30d=issue_stats["closed_issues_30d"],
                open_prs=pr_stats["open_prs"],
                merged_prs_30d=pr_stats["merged_prs_30d"],
            )

            popularity = RatingCalculator.calculate_popularity_score(
                downloads=downloads,
                stars=github_metrics.stars if github_metrics else None,
                dependents=None,  # PyPI doesn't provide this easily
            )

            # Determine quality metrics
            has_documentation = bool(info.get("description") or info.get("summary"))
            readme_length = len(info.get("description", ""))
            has_license = bool(license_name)
            has_tests = None  # Cannot determine easily from PyPI API

            # Check for llms.txt
            has_llms_txt = None
            has_llms_full_txt = None
            try:
                llms_txt_result = await self.llms_txt_client.fetch_for_package(
                    package_name=package_name,
                    ecosystem="python",
                    registry_data=pypi_data,
                    include_full=True,
                )
                if llms_txt_result.status == "success":
                    has_llms_txt = llms_txt_result.llms_txt_content is not None
                    has_llms_full_txt = llms_txt_result.llms_full_txt_content is not None
                else:
                    has_llms_txt = False
                    has_llms_full_txt = False
            except Exception:
                # If llms.txt check fails, treat as not having it
                has_llms_txt = False
                has_llms_full_txt = False

            quality = RatingCalculator.calculate_quality_score(
                has_documentation=has_documentation,
                has_license=has_license,
                has_tests=has_tests,
                readme_length=readme_length,
                has_llms_txt=has_llms_txt,
                has_llms_full_txt=has_llms_full_txt,
            )

            # Calculate overall score and grade
            overall_score = RatingCalculator.calculate_overall_score(
                maintenance=maintenance,
                popularity=popularity,
                quality=quality,
            )
            letter_grade = RatingCalculator.score_to_letter_grade(overall_score)

            # Generate insights and red flags
            insights = RatingCalculator.generate_insights(maintenance, popularity, quality)
            red_flags = RatingCalculator.generate_red_flags(maintenance, popularity, quality)

            return PackageRating(
                package_name=package_name,
                ecosystem=Ecosystem.PYTHON,
                overall_score=overall_score,
                letter_grade=letter_grade,
                maintenance=maintenance,
                popularity=popularity,
                quality=quality,
                repository_url=repo_url,
                license=license_name,
                description=description,
                insights=insights,
                red_flags=red_flags,
                rated_at=datetime.now(timezone.utc),
                status=VersionStatus.SUCCESS,
            )

        except Exception as e:
            return PackageRating(
                package_name=package_name,
                ecosystem=Ecosystem.PYTHON,
                overall_score=0.0,
                letter_grade=RatingCalculator.score_to_letter_grade(0.0),
                maintenance=RatingCalculator.calculate_maintenance_score(None),
                popularity=RatingCalculator.calculate_popularity_score(),
                quality=RatingCalculator.calculate_quality_score(False, False),
                status=VersionStatus.ERROR,
                error_message=str(e),
            )

    async def _get_pypi_data(self, package_name: str) -> dict | None:
        """Get package data from PyPI.

        Args:
            package_name: Package name

        Returns:
            PyPI JSON data or None if not found
        """
        url = f"{self.pypi_base_url}/{package_name}/json"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPError:
                return None

    async def _get_download_stats(self, package_name: str) -> int | None:
        """Get download statistics from pypistats.org.

        Args:
            package_name: Package name

        Returns:
            Monthly download count or None if unavailable
        """
        url = f"{self.pypistats_base_url}/packages/{package_name}/recent"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                # Get last month downloads
                return data.get("data", {}).get("last_month")  # type: ignore[no-any-return]
            except httpx.HTTPError:
                return None

    @staticmethod
    def _find_github_repo(info: dict, project_urls: dict) -> str | None:
        """Find GitHub repository URL from package metadata.

        Args:
            info: PyPI info dict
            project_urls: Project URLs dict

        Returns:
            GitHub repository URL or None
        """
        # Check common URL fields
        common_keys = ["Source", "Repository", "Code", "GitHub", "Homepage"]

        for key in common_keys:
            url = project_urls.get(key)
            if url and "github.com" in url:
                return url  # type: ignore[no-any-return]

        # Check homepage
        homepage = info.get("home_page")
        if homepage and "github.com" in homepage:
            return homepage  # type: ignore[no-any-return]

        return None

    @staticmethod
    def _calculate_last_release_days(releases: dict) -> int | None:
        """Calculate days since last release.

        Args:
            releases: PyPI releases dict

        Returns:
            Days since last release or None if no releases
        """
        if not releases:
            return None

        latest_date = None
        for version_files in releases.values():
            if not version_files:
                continue
            for file_info in version_files:
                upload_time = file_info.get("upload_time_iso_8601")
                if upload_time:
                    upload_dt = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                    if latest_date is None or upload_dt > latest_date:
                        latest_date = upload_dt

        if latest_date:
            days = (datetime.now(timezone.utc) - latest_date).days
            return days

        return None

    def _create_not_found_response(self, package_name: str) -> PackageRating:
        """Create a not found response.

        Args:
            package_name: Package name

        Returns:
            PackageRating with not found status
        """
        return PackageRating(
            package_name=package_name,
            ecosystem=Ecosystem.PYTHON,
            overall_score=0.0,
            letter_grade=RatingCalculator.score_to_letter_grade(0.0),
            maintenance=RatingCalculator.calculate_maintenance_score(None),
            popularity=RatingCalculator.calculate_popularity_score(),
            quality=RatingCalculator.calculate_quality_score(False, False),
            status=VersionStatus.NOT_FOUND,
            error_message=f"Package '{package_name}' not found on PyPI",
        )
