"""Rust package rating implementation."""

from datetime import datetime, timezone

import httpx

from mcp_package_hero.github_client import GitHubClient
from mcp_package_hero.llms_txt_client import LLMsTxtClient
from mcp_package_hero.models import Ecosystem, PackageRating, VersionStatus
from mcp_package_hero.rating_calculator import RatingCalculator


class RustPackageRater:
    """Rates Rust packages from crates.io."""

    def __init__(self, github_token: str | None = None) -> None:
        """Initialize Rust package rater.

        Args:
            github_token: Optional GitHub token for higher rate limits
        """
        self.crates_base_url = "https://crates.io/api/v1"
        self.github_client = GitHubClient(github_token)
        self.llms_txt_client = LLMsTxtClient()

    async def rate_package(self, package_name: str) -> PackageRating:
        """Rate a Rust package.

        Args:
            package_name: Name of the package on crates.io

        Returns:
            PackageRating object with comprehensive rating
        """
        try:
            # Get crates.io metadata
            crate_data = await self._get_crate_data(package_name)
            if not crate_data:
                return self._create_not_found_response(package_name)

            # Extract basic info
            crate = crate_data.get("crate", {})
            description = crate.get("description", "")[:200]
            repo_url = crate.get("repository")
            documentation_url = crate.get("documentation")
            total_downloads = crate.get("downloads", 0)

            # Get version info for license and release date
            versions = crate_data.get("versions", [])
            license_name = None
            last_release_days = None

            if versions:
                latest_version = versions[0]
                license_name = latest_version.get("license")
                created_at = latest_version.get("created_at")

                if created_at:
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    last_release_days = (datetime.now(timezone.utc) - created_dt).days

            # Get GitHub metrics
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

            # Calculate scores
            maintenance = RatingCalculator.calculate_maintenance_score(
                last_release_days=last_release_days,
                open_issues=issue_stats["open_issues"],
                closed_issues_30d=issue_stats["closed_issues_30d"],
                open_prs=pr_stats["open_prs"],
                merged_prs_30d=pr_stats["merged_prs_30d"],
            )

            # For crates.io, we have total downloads, not monthly
            # We'll use it as is, understanding it's a different scale
            popularity = RatingCalculator.calculate_popularity_score(
                downloads=total_downloads,
                stars=github_metrics.stars if github_metrics else None,
                dependents=None,  # crates.io doesn't expose this easily
            )

            # Determine quality metrics
            has_documentation = bool(description or documentation_url)
            readme_length = len(description)
            has_license = bool(license_name)
            has_tests = None  # Cannot determine easily from crates.io API

            # Check for llms.txt
            has_llms_txt = None
            has_llms_full_txt = None
            try:
                llms_txt_result = await self.llms_txt_client.fetch_for_package(
                    package_name=package_name,
                    ecosystem="rust",
                    registry_data=crate_data,
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
                ecosystem=Ecosystem.RUST,
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
                ecosystem=Ecosystem.RUST,
                overall_score=0.0,
                letter_grade=RatingCalculator.score_to_letter_grade(0.0),
                maintenance=RatingCalculator.calculate_maintenance_score(None),
                popularity=RatingCalculator.calculate_popularity_score(),
                quality=RatingCalculator.calculate_quality_score(False, False),
                status=VersionStatus.ERROR,
                error_message=str(e),
            )

    async def _get_crate_data(self, package_name: str) -> dict | None:
        """Get package data from crates.io.

        Args:
            package_name: Package name

        Returns:
            crates.io JSON data or None if not found
        """
        url = f"{self.crates_base_url}/crates/{package_name}"

        async with httpx.AsyncClient() as client:
            try:
                # crates.io requires a User-Agent header
                headers = {"User-Agent": "mcp-package-hero (https://github.com/moinsen-dev/mcp-package-hero)"}
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPError:
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
            ecosystem=Ecosystem.RUST,
            overall_score=0.0,
            letter_grade=RatingCalculator.score_to_letter_grade(0.0),
            maintenance=RatingCalculator.calculate_maintenance_score(None),
            popularity=RatingCalculator.calculate_popularity_score(),
            quality=RatingCalculator.calculate_quality_score(False, False),
            status=VersionStatus.NOT_FOUND,
            error_message=f"Package '{package_name}' not found on crates.io",
        )
