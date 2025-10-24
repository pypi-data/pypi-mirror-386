"""JavaScript package rating implementation."""

from datetime import datetime, timezone

import httpx

from mcp_package_hero.github_client import GitHubClient
from mcp_package_hero.llms_txt_client import LLMsTxtClient
from mcp_package_hero.models import Ecosystem, PackageRating, VersionStatus
from mcp_package_hero.rating_calculator import RatingCalculator


class JavaScriptPackageRater:
    """Rates JavaScript/TypeScript packages from npm."""

    def __init__(self, github_token: str | None = None) -> None:
        """Initialize JavaScript package rater.

        Args:
            github_token: Optional GitHub token for higher rate limits
        """
        self.npm_base_url = "https://registry.npmjs.org"
        self.npms_base_url = "https://api.npms.io/v2"
        self.github_client = GitHubClient(github_token)
        self.llms_txt_client = LLMsTxtClient()

    async def rate_package(self, package_name: str) -> PackageRating:
        """Rate a JavaScript package.

        Args:
            package_name: Name of the package on npm

        Returns:
            PackageRating object with comprehensive rating
        """
        try:
            # Get npm metadata
            npm_data = await self._get_npm_data(package_name)
            if not npm_data:
                return self._create_not_found_response(package_name)

            # Get npms.io scores (quality, popularity, maintenance)
            npms_scores = await self._get_npms_scores(package_name)

            # Extract basic info
            description = npm_data.get("description", "")
            license_name = npm_data.get("license")
            if isinstance(license_name, dict):
                license_name = license_name.get("type")

            # Find GitHub repository
            repo_url = self._find_github_repo(npm_data)
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
            time_data = npm_data.get("time", {})
            last_release_days = self._calculate_last_release_days(time_data)

            # Get download stats from official npm API (primary source)
            downloads = await self._get_npm_downloads(package_name)

            # Fallback to npms.io only if npm API fails AND npms.io has non-zero data
            if downloads is None and npms_scores:
                downloads_raw = npms_scores.get("evaluation", {}).get("popularity", {}).get("downloadsCount")
                if downloads_raw is not None and downloads_raw > 0:
                    downloads = int(downloads_raw)  # Convert to int if float

            # If npms.io has scores, use them as a boost (only if data appears valid)
            npms_maintenance = None
            npms_popularity = None
            npms_quality = None
            npms_is_stale = False

            if npms_scores:
                # Check if npms.io data appears stale (0 downloads when we have real data)
                npms_downloads = npms_scores.get("evaluation", {}).get("popularity", {}).get("downloadsCount", 0)
                if downloads and downloads > 0 and npms_downloads == 0:
                    npms_is_stale = True

                # Only use npms.io scores if data appears valid
                if not npms_is_stale:
                    # Access scores from score.detail (npms.io API v2 structure)
                    score_detail = npms_scores.get("score", {}).get("detail", {})
                    # npms scores are 0-1, convert to 0-100
                    npms_maintenance = score_detail.get("maintenance", 0) * 100
                    npms_popularity = score_detail.get("popularity", 0) * 100
                    npms_quality = score_detail.get("quality", 0) * 100

            # Calculate our scores
            maintenance = RatingCalculator.calculate_maintenance_score(
                last_release_days=last_release_days,
                open_issues=issue_stats["open_issues"],
                closed_issues_30d=issue_stats["closed_issues_30d"],
                open_prs=pr_stats["open_prs"],
                merged_prs_30d=pr_stats["merged_prs_30d"],
            )

            # Blend with npms maintenance score if available
            if npms_maintenance is not None:
                maintenance.score = round((maintenance.score * 0.5) + (npms_maintenance * 0.5), 1)

            popularity = RatingCalculator.calculate_popularity_score(
                downloads=downloads,
                stars=github_metrics.stars if github_metrics else None,
                dependents=npms_scores.get("evaluation", {}).get("popularity", {}).get("dependentsCount") if npms_scores else None,
            )

            # Blend with npms popularity score if available
            if npms_popularity is not None:
                popularity.score = round((popularity.score * 0.5) + (npms_popularity * 0.5), 1)

            # Determine quality metrics
            readme = npm_data.get("readme", "")
            has_documentation = bool(description or readme)
            readme_length = len(readme)
            has_license = bool(license_name)

            # Check for test indicators in package.json
            has_tests = self._has_tests(npm_data)

            # Check for llms.txt
            has_llms_txt = None
            has_llms_full_txt = None
            try:
                llms_txt_result = await self.llms_txt_client.fetch_for_package(
                    package_name=package_name,
                    ecosystem="javascript",
                    registry_data=npm_data,
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

            # Blend with npms quality score if available
            if npms_quality is not None:
                quality.score = round((quality.score * 0.5) + (npms_quality * 0.5), 1)

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

            # Add npm-specific insights
            if npms_scores and not npms_is_stale:
                final_score = npms_scores.get("score", {}).get("final", 0)
                if final_score >= 0.8:
                    insights.insert(0, f"Excellent npms.io score: {final_score:.2f}/1.00")

            return PackageRating(
                package_name=package_name,
                ecosystem=Ecosystem.JAVASCRIPT,
                overall_score=overall_score,
                letter_grade=letter_grade,
                maintenance=maintenance,
                popularity=popularity,
                quality=quality,
                repository_url=repo_url,
                license=license_name,
                description=description[:200] if description else None,
                insights=insights,
                red_flags=red_flags,
                rated_at=datetime.now(timezone.utc),
                status=VersionStatus.SUCCESS,
            )

        except Exception as e:
            return PackageRating(
                package_name=package_name,
                ecosystem=Ecosystem.JAVASCRIPT,
                overall_score=0.0,
                letter_grade=RatingCalculator.score_to_letter_grade(0.0),
                maintenance=RatingCalculator.calculate_maintenance_score(None),
                popularity=RatingCalculator.calculate_popularity_score(),
                quality=RatingCalculator.calculate_quality_score(False, False),
                status=VersionStatus.ERROR,
                error_message=str(e),
            )

    async def _get_npm_data(self, package_name: str) -> dict | None:
        """Get package data from npm registry.

        Args:
            package_name: Package name

        Returns:
            npm JSON data or None if not found
        """
        url = f"{self.npm_base_url}/{package_name}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPError:
                return None

    async def _get_npms_scores(self, package_name: str) -> dict | None:
        """Get package scores from npms.io.

        Args:
            package_name: Package name

        Returns:
            npms.io data or None if unavailable
        """
        url = f"{self.npms_base_url}/package/{package_name}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except httpx.HTTPError:
                return None

    async def _get_npm_downloads(self, package_name: str) -> int | None:
        """Get download statistics from official npm downloads API.

        Args:
            package_name: Package name

        Returns:
            Monthly download count or None if unavailable
        """
        url = f"https://api.npmjs.org/downloads/point/last-month/{package_name}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                return data.get("downloads")  # type: ignore[no-any-return]
            except httpx.HTTPError:
                return None

    @staticmethod
    def _find_github_repo(npm_data: dict) -> str | None:
        """Find GitHub repository URL from npm metadata.

        Args:
            npm_data: npm registry data

        Returns:
            GitHub repository URL or None
        """
        # Check repository field
        repository = npm_data.get("repository")
        if repository:
            if isinstance(repository, dict):
                url = repository.get("url", "")
            else:
                url = str(repository)

            # Clean up git+ prefix and .git suffix
            url = url.replace("git+", "").replace("git://", "https://")
            if url.endswith(".git"):
                url = url[:-4]  # Remove .git suffix properly
            if "github.com" in url:
                return url  # type: ignore[no-any-return]

        # Check homepage
        homepage = npm_data.get("homepage")
        if homepage and "github.com" in homepage:
            return homepage  # type: ignore[no-any-return]

        return None

    @staticmethod
    def _calculate_last_release_days(time_data: dict) -> int | None:
        """Calculate days since last release.

        Args:
            time_data: npm time data

        Returns:
            Days since last release or None if no releases
        """
        if not time_data:
            return None

        # Get the 'modified' field which is the last publish time
        modified = time_data.get("modified")
        if not modified:
            return None

        try:
            modified_dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - modified_dt).days
            return days
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _has_tests(npm_data: dict) -> bool | None:
        """Check if package has test indicators.

        Args:
            npm_data: npm registry data

        Returns:
            True if tests found, False if not found, None if unknown
        """
        # Check scripts for test command
        scripts = npm_data.get("scripts", {})
        if "test" in scripts:
            test_script = scripts["test"]
            # Check if it's not the default "no test specified"
            if "no test specified" not in test_script.lower():
                return True
            return False

        # Check devDependencies for test frameworks
        dev_deps = npm_data.get("devDependencies", {})
        test_frameworks = ["jest", "mocha", "jasmine", "ava", "tape", "vitest", "playwright", "cypress"]

        for framework in test_frameworks:
            if framework in dev_deps:
                return True

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
            ecosystem=Ecosystem.JAVASCRIPT,
            overall_score=0.0,
            letter_grade=RatingCalculator.score_to_letter_grade(0.0),
            maintenance=RatingCalculator.calculate_maintenance_score(None),
            popularity=RatingCalculator.calculate_popularity_score(),
            quality=RatingCalculator.calculate_quality_score(False, False),
            status=VersionStatus.NOT_FOUND,
            error_message=f"Package '{package_name}' not found on npm",
        )
