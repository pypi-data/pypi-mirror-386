"""Rating calculation utilities."""

import math

from mcp_package_hero.models import LetterGrade, MaintenanceScore, PopularityScore, QualityScore


class RatingCalculator:
    """Utility class for calculating package ratings."""

    # Weights for overall score
    MAINTENANCE_WEIGHT = 0.35
    POPULARITY_WEIGHT = 0.25
    QUALITY_WEIGHT = 0.40

    @staticmethod
    def calculate_maintenance_score(
        last_release_days: int | None,
        open_issues: int = 0,
        closed_issues_30d: int = 0,
        open_prs: int = 0,
        merged_prs_30d: int = 0,
    ) -> MaintenanceScore:
        """Calculate maintenance health score.

        Args:
            last_release_days: Days since last release
            open_issues: Number of open issues
            closed_issues_30d: Number of closed issues in last 30 days
            open_prs: Number of open pull requests
            merged_prs_30d: Number of merged PRs in last 30 days

        Returns:
            MaintenanceScore object
        """
        # Release frequency score (based on days since last release)
        if last_release_days is None:
            release_score = 50.0  # Neutral if unknown
        elif last_release_days <= 30:
            release_score = 100.0
        elif last_release_days <= 90:
            release_score = 80.0
        elif last_release_days <= 180:
            release_score = 60.0
        elif last_release_days <= 365:
            release_score = 40.0
        else:
            release_score = 20.0

        # Issue resolution score
        total_issues = open_issues + closed_issues_30d
        if total_issues == 0:
            issue_score = 100.0  # No issues is good
        else:
            resolution_rate = closed_issues_30d / total_issues
            issue_score = min(100.0, resolution_rate * 100 + 20)  # Minimum 20 for any activity

        # PR merge score
        total_prs = open_prs + merged_prs_30d
        if total_prs == 0:
            pr_score = 80.0  # Neutral - no PR activity
        else:
            merge_rate = merged_prs_30d / total_prs
            pr_score = min(100.0, merge_rate * 100 + 10)

        # Overall maintenance score
        overall = (release_score * 0.5) + (issue_score * 0.3) + (pr_score * 0.2)

        return MaintenanceScore(
            score=round(overall, 1),
            last_release_days=last_release_days,
            release_frequency_score=round(release_score, 1),
            issue_resolution_score=round(issue_score, 1),
            pr_merge_score=round(pr_score, 1),
        )

    @staticmethod
    def calculate_popularity_score(
        downloads: int | None = None,
        stars: int | None = None,
        dependents: int | None = None,
    ) -> PopularityScore:
        """Calculate popularity and adoption score.

        Args:
            downloads: Monthly download count
            stars: GitHub stars
            dependents: Number of dependent packages

        Returns:
            PopularityScore object
        """
        # Downloads score (logarithmic scale)
        if downloads is None or downloads == 0:
            downloads_score = 0.0
        else:
            # Log scale: 1K downloads = 40, 10K = 60, 100K = 80, 1M+ = 100
            downloads_score = min(100.0, 20 + math.log10(downloads) * 20)

        # Stars score (logarithmic scale)
        if stars is None or stars == 0:
            stars_score = 0.0
        else:
            # Log scale: 10 stars = 40, 100 = 60, 1000 = 80, 10000+ = 100
            stars_score = min(100.0, 20 + math.log10(stars) * 30)

        # Dependents score (not used in overall but tracked)
        dependents_score = 0.0
        if dependents:
            dependents_score = min(100.0, math.log10(max(1, dependents)) * 30)

        # Overall popularity (downloads and stars weighted equally)
        if downloads is None and stars is None:
            overall = 0.0
        elif downloads is None:
            overall = stars_score
        elif stars is None:
            overall = downloads_score
        else:
            overall = (downloads_score * 0.6) + (stars_score * 0.4)

        return PopularityScore(
            score=round(overall, 1),
            downloads=downloads,
            stars=stars,
            dependents=dependents,
            downloads_score=round(downloads_score, 1),
            stars_score=round(stars_score, 1),
        )

    @staticmethod
    def calculate_quality_score(
        has_documentation: bool,
        has_license: bool,
        has_tests: bool | None = None,
        readme_length: int | None = None,
        has_llms_txt: bool | None = None,
        has_llms_full_txt: bool | None = None,
    ) -> QualityScore:
        """Calculate quality metrics score.

        Args:
            has_documentation: Has README or documentation
            has_license: Has license file
            has_tests: Has test indicators
            readme_length: Length of README (for quality assessment)
            has_llms_txt: Has llms.txt file
            has_llms_full_txt: Has llms-full.txt file

        Returns:
            QualityScore object
        """
        # Documentation score
        if not has_documentation:
            doc_score = 0.0
        elif readme_length is None:
            doc_score = 50.0  # Has docs but unknown quality
        elif readme_length < 100:
            doc_score = 30.0
        elif readme_length < 500:
            doc_score = 60.0
        elif readme_length < 2000:
            doc_score = 80.0
        else:
            doc_score = 100.0

        # License score
        license_score = 100.0 if has_license else 0.0

        # Test score
        if has_tests is None:
            test_score = 50.0  # Unknown
        elif has_tests:
            test_score = 100.0
        else:
            test_score = 0.0

        # llms.txt score (bonus for LLM-friendly documentation)
        if has_llms_txt is None:
            llms_txt_score = 0.0  # Not checked
        elif has_llms_txt and has_llms_full_txt:
            llms_txt_score = 100.0  # Has both files - excellent
        elif has_llms_txt:
            llms_txt_score = 70.0  # Has llms.txt only - good
        else:
            llms_txt_score = 0.0  # No llms.txt

        # Overall quality (weighted)
        # Adjusted weights to include llms.txt: doc(35%), license(25%), tests(25%), llms.txt(15%)
        overall = (
            (doc_score * 0.35)
            + (license_score * 0.25)
            + (test_score * 0.25)
            + (llms_txt_score * 0.15)
        )

        return QualityScore(
            score=round(overall, 1),
            has_documentation=has_documentation,
            has_license=has_license,
            has_tests=has_tests,
            has_llms_txt=has_llms_txt,
            has_llms_full_txt=has_llms_full_txt,
            documentation_score=round(doc_score, 1),
            license_score=round(license_score, 1),
            test_score=round(test_score, 1),
            llms_txt_score=round(llms_txt_score, 1),
        )

    @classmethod
    def calculate_overall_score(
        cls,
        maintenance: MaintenanceScore,
        popularity: PopularityScore,
        quality: QualityScore,
    ) -> float:
        """Calculate overall package rating score.

        Args:
            maintenance: Maintenance score
            popularity: Popularity score
            quality: Quality score

        Returns:
            Overall score (0-100)
        """
        overall = (
            maintenance.score * cls.MAINTENANCE_WEIGHT
            + popularity.score * cls.POPULARITY_WEIGHT
            + quality.score * cls.QUALITY_WEIGHT
        )
        return round(overall, 1)

    @staticmethod
    def score_to_letter_grade(score: float) -> LetterGrade:
        """Convert numeric score to letter grade.

        Args:
            score: Numeric score (0-100)

        Returns:
            Letter grade
        """
        if score >= 95:
            return LetterGrade.A_PLUS
        elif score >= 90:
            return LetterGrade.A
        elif score >= 85:
            return LetterGrade.A_MINUS
        elif score >= 80:
            return LetterGrade.B_PLUS
        elif score >= 75:
            return LetterGrade.B
        elif score >= 70:
            return LetterGrade.B_MINUS
        elif score >= 65:
            return LetterGrade.C_PLUS
        elif score >= 60:
            return LetterGrade.C
        elif score >= 55:
            return LetterGrade.C_MINUS
        elif score >= 50:
            return LetterGrade.D
        else:
            return LetterGrade.F

    @staticmethod
    def generate_insights(
        maintenance: MaintenanceScore,
        popularity: PopularityScore,
        quality: QualityScore,
    ) -> list[str]:
        """Generate insights from scores.

        Args:
            maintenance: Maintenance score
            popularity: Popularity score
            quality: Quality score

        Returns:
            List of insight strings
        """
        insights = []

        # Maintenance insights
        if maintenance.last_release_days and maintenance.last_release_days <= 30:
            insights.append("Recently updated (within last 30 days)")
        if maintenance.issue_resolution_score >= 80:
            insights.append("Strong issue resolution track record")
        if maintenance.pr_merge_score >= 80:
            insights.append("Active PR merge activity")

        # Popularity insights
        if popularity.downloads and popularity.downloads >= 100000:
            insights.append("Highly popular with 100K+ monthly downloads")
        elif popularity.downloads and popularity.downloads >= 10000:
            insights.append("Popular package with 10K+ monthly downloads")
        if popularity.stars and popularity.stars >= 1000:
            insights.append("Well-starred project (1000+ stars)")

        # Quality insights
        if quality.score >= 80:
            insights.append("High quality package with good documentation and license")
        if quality.has_tests:
            insights.append("Includes test suite")
        if quality.has_llms_txt and quality.has_llms_full_txt:
            insights.append("Excellent LLM-friendly documentation (llms.txt + llms-full.txt)")
        elif quality.has_llms_txt:
            insights.append("Has LLM-friendly documentation (llms.txt)")

        return insights

    @staticmethod
    def generate_red_flags(
        maintenance: MaintenanceScore,
        popularity: PopularityScore,
        quality: QualityScore,
    ) -> list[str]:
        """Generate warning signs from scores.

        Args:
            maintenance: Maintenance score
            popularity: Popularity score
            quality: Quality score

        Returns:
            List of red flag strings
        """
        red_flags = []

        # Maintenance red flags
        if maintenance.last_release_days and maintenance.last_release_days > 365:
            red_flags.append(f"Not updated in over a year ({maintenance.last_release_days} days)")
        elif maintenance.last_release_days and maintenance.last_release_days > 180:
            red_flags.append(f"Not updated in over 6 months ({maintenance.last_release_days} days)")

        if maintenance.issue_resolution_score < 40:
            red_flags.append("Low issue resolution rate")
        if maintenance.pr_merge_score < 40:
            red_flags.append("Low PR merge rate")

        # Popularity red flags
        if popularity.downloads is not None and popularity.downloads < 100:
            red_flags.append("Very low download count")
        if popularity.stars is not None and popularity.stars < 10:
            red_flags.append("Few GitHub stars")

        # Quality red flags
        if not quality.has_license:
            red_flags.append("No license found")
        if not quality.has_documentation:
            red_flags.append("Missing documentation")
        if quality.has_tests is False:
            red_flags.append("No test suite detected")
        # Note: Not having llms.txt is not a red flag since it's still an emerging standard

        return red_flags
