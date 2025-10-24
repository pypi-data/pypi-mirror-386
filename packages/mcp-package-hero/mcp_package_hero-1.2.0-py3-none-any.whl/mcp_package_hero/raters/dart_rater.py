"""Dart package rating implementation."""

from datetime import datetime, timezone

import httpx

from mcp_package_hero.github_client import GitHubClient
from mcp_package_hero.llms_txt_client import LLMsTxtClient
from mcp_package_hero.models import Ecosystem, PackageRating, VersionStatus
from mcp_package_hero.rating_calculator import RatingCalculator


class DartPackageRater:
    """Rates Dart/Flutter packages from pub.dev."""

    def __init__(self, github_token: str | None = None) -> None:
        """Initialize Dart package rater.

        Args:
            github_token: Optional GitHub token for higher rate limits
        """
        self.pubdev_base_url = "https://pub.dev/api"
        self.github_client = GitHubClient(github_token)
        self.llms_txt_client = LLMsTxtClient()

    async def rate_package(self, package_name: str) -> PackageRating:
        """Rate a Dart package.

        Args:
            package_name: Name of the package on pub.dev

        Returns:
            PackageRating object with comprehensive rating
        """
        try:
            # Get pub.dev package data
            package_data = await self._get_package_data(package_name)
            if not package_data:
                return self._create_not_found_response(package_name)

            # Get pub.dev native scores (pub points)
            pub_scores = await self._get_pub_scores(package_name)

            # Extract basic info
            latest = package_data.get("latest", {})
            pubspec = latest.get("pubspec", {})
            description = pubspec.get("description", "")
            license_name = latest.get("archive_url")  # pub.dev doesn't expose license directly

            # Find GitHub repository
            repo_url = self._find_github_repo(pubspec)
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

            # Calculate last release date
            published = latest.get("published")
            last_release_days = None
            if published:
                published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                last_release_days = (datetime.now(timezone.utc) - published_dt).days

            # pub.dev provides native scores - use them as a boost
            pub_points = None
            pub_popularity = None
            pub_likes = None

            if pub_scores:
                pub_points = pub_scores.get("grantedPoints", 0)  # Out of 160
                pub_popularity = pub_scores.get("popularityScore", 0) * 100  # 0-1 to 0-100
                pub_likes = pub_scores.get("likeCount", 0)

            # Calculate our scores
            maintenance = RatingCalculator.calculate_maintenance_score(
                last_release_days=last_release_days,
                open_issues=issue_stats["open_issues"],
                closed_issues_30d=issue_stats["closed_issues_30d"],
                open_prs=pr_stats["open_prs"],
                merged_prs_30d=pr_stats["merged_prs_30d"],
            )

            # Boost maintenance with pub points (maintenance-related)
            if pub_points is not None:
                # pub points has maintenance component (20 points)
                # Convert to 0-100 scale and blend
                pub_maintenance_boost = (pub_points / 160) * 100
                maintenance.score = round((maintenance.score * 0.6) + (pub_maintenance_boost * 0.4), 1)

            popularity = RatingCalculator.calculate_popularity_score(
                downloads=None,  # pub.dev doesn't expose download count via API
                stars=github_metrics.stars if github_metrics else None,
                dependents=None,
            )

            # Boost popularity with pub.dev popularity score
            if pub_popularity is not None:
                popularity.score = round((popularity.score * 0.3) + (pub_popularity * 0.7), 1)

            # Determine quality metrics from pub points
            has_documentation = bool(description or pubspec.get("homepage"))
            readme_length = len(description)
            has_license = github_metrics.has_license if github_metrics else False

            # pub.dev checks for tests in their scoring
            has_tests = None
            if pub_points is not None and pub_points >= 90:
                # High pub points usually means tests exist
                has_tests = True

            # Check for llms.txt
            has_llms_txt = None
            has_llms_full_txt = None
            try:
                llms_txt_result = await self.llms_txt_client.fetch_for_package(
                    package_name=package_name,
                    ecosystem="dart",
                    registry_data=package_data,
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

            # Boost quality with pub points (quality-related)
            if pub_points is not None:
                # pub points has quality components (documentation, platform support, etc.)
                pub_quality_boost = (pub_points / 160) * 100
                quality.score = round((quality.score * 0.4) + (pub_quality_boost * 0.6), 1)

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

            # Add pub.dev-specific insights
            if pub_points is not None:
                if pub_points >= 140:
                    insights.insert(0, f"Excellent pub points: {pub_points}/160")
                elif pub_points >= 120:
                    insights.insert(0, f"Good pub points: {pub_points}/160")
                elif pub_points < 90:
                    red_flags.append(f"Low pub points: {pub_points}/160")

            if pub_likes is not None and pub_likes >= 100:
                insights.append(f"Well-liked package ({pub_likes} likes)")

            return PackageRating(
                package_name=package_name,
                ecosystem=Ecosystem.DART,
                overall_score=overall_score,
                letter_grade=letter_grade,
                maintenance=maintenance,
                popularity=popularity,
                quality=quality,
                repository_url=repo_url,
                license=github_metrics.license_name if github_metrics else None,
                description=description[:200] if description else None,
                insights=insights,
                red_flags=red_flags,
                rated_at=datetime.now(timezone.utc),
                status=VersionStatus.SUCCESS,
            )

        except Exception as e:
            return PackageRating(
                package_name=package_name,
                ecosystem=Ecosystem.DART,
                overall_score=0.0,
                letter_grade=RatingCalculator.score_to_letter_grade(0.0),
                maintenance=RatingCalculator.calculate_maintenance_score(None),
                popularity=RatingCalculator.calculate_popularity_score(),
                quality=RatingCalculator.calculate_quality_score(False, False),
                status=VersionStatus.ERROR,
                error_message=str(e),
            )

    async def _get_package_data(self, package_name: str) -> dict | None:
        """Get package data from pub.dev.

        Args:
            package_name: Package name

        Returns:
            pub.dev JSON data or None if not found
        """
        url = f"{self.pubdev_base_url}/packages/{package_name}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPError:
                return None

    async def _get_pub_scores(self, package_name: str) -> dict | None:
        """Get pub points and scores from pub.dev.

        Args:
            package_name: Package name

        Returns:
            pub.dev score data or None if unavailable
        """
        url = f"{self.pubdev_base_url}/packages/{package_name}/score"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPError:
                return None

    @staticmethod
    def _find_github_repo(pubspec: dict) -> str | None:
        """Find GitHub repository URL from pubspec.

        Args:
            pubspec: pubspec.yaml as dict

        Returns:
            GitHub repository URL or None
        """
        # Check repository field
        repository = pubspec.get("repository")
        if repository and "github.com" in repository:
            return repository  # type: ignore[no-any-return]

        # Check homepage
        homepage = pubspec.get("homepage")
        if homepage and "github.com" in homepage:
            return homepage  # type: ignore[no-any-return]

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
            ecosystem=Ecosystem.DART,
            overall_score=0.0,
            letter_grade=RatingCalculator.score_to_letter_grade(0.0),
            maintenance=RatingCalculator.calculate_maintenance_score(None),
            popularity=RatingCalculator.calculate_popularity_score(),
            quality=RatingCalculator.calculate_quality_score(False, False),
            status=VersionStatus.NOT_FOUND,
            error_message=f"Package '{package_name}' not found on pub.dev",
        )
