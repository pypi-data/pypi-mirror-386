"""Client for fetching llms.txt from package repositories and websites."""

import re
from typing import Any

import httpx

from .github_client import GitHubClient
from .llms_txt_models import (
    LLMsTxtContent,
    LLMsTxtResponse,
    LLMsTxtSection,
    LLMsTxtSource,
    LLMsTxtStatus,
)


class LLMsTxtClient:
    """Client for fetching and parsing llms.txt files."""

    def __init__(self) -> None:
        """Initialize the llms.txt client."""
        self.github_client = GitHubClient()
        self.timeout = 10.0

    async def fetch_for_package(
        self,
        package_name: str,
        ecosystem: str,
        registry_data: dict[str, Any],
        include_full: bool = False,
    ) -> LLMsTxtResponse:
        """
        Fetch llms.txt for a package from various sources.

        Args:
            package_name: Name of the package
            ecosystem: Package ecosystem
            registry_data: Package metadata from registry
            include_full: Whether to also fetch llms-full.txt

        Returns:
            LLMsTxtResponse with fetched content or error
        """
        # Extract URLs from registry data
        repository_url = self._extract_repository_url(registry_data)
        homepage_url = self._extract_homepage_url(registry_data)

        # Try fetching from multiple sources
        llms_txt_content = None
        source_url = None
        source_type = None

        # Try GitHub first (most common)
        if repository_url:
            github_result = await self._fetch_from_github(repository_url)
            if github_result:
                llms_txt_content, source_url, source_type = github_result

        # Try homepage if GitHub failed
        if not llms_txt_content and homepage_url:
            homepage_result = await self._fetch_from_url(f"{homepage_url.rstrip('/')}/llms.txt")
            if homepage_result:
                llms_txt_content, source_url = homepage_result
                source_type = LLMsTxtSource.HOMEPAGE

        # Fetch llms-full.txt if requested
        llms_full_txt_content = None
        if include_full and source_url:
            full_url = source_url.replace("/llms.txt", "/llms-full.txt")
            full_result = await self._fetch_from_url(full_url)
            if full_result:
                llms_full_txt_content = full_result[0]

        # Return response
        if llms_txt_content:
            parsed_content = self._parse_llms_txt(llms_txt_content)
            return LLMsTxtResponse(
                package_name=package_name,
                ecosystem=ecosystem,
                llms_txt_content=parsed_content,
                llms_full_txt_content=llms_full_txt_content,
                source_url=source_url,
                source_type=source_type,
                repository_url=repository_url,
                homepage_url=homepage_url,
                status=LLMsTxtStatus.SUCCESS,
            )
        else:
            return LLMsTxtResponse(
                package_name=package_name,
                ecosystem=ecosystem,
                repository_url=repository_url,
                homepage_url=homepage_url,
                status=LLMsTxtStatus.NOT_FOUND,
                error_message=f"llms.txt not found for package '{package_name}'",
            )

    async def _fetch_from_github(
        self, repository_url: str,
    ) -> tuple[str, str, LLMsTxtSource] | None:
        """
        Try fetching llms.txt from GitHub repository.

        Args:
            repository_url: GitHub repository URL

        Returns:
            Tuple of (content, url, source_type) or None if not found
        """
        # Extract owner and repo
        repo_info = GitHubClient.extract_repo_from_url(repository_url)
        if not repo_info:
            return None

        owner, repo = repo_info

        # Try common branch names
        branches = [
            ("main", LLMsTxtSource.GITHUB_MAIN),
            ("master", LLMsTxtSource.GITHUB_MASTER),
            ("develop", LLMsTxtSource.GITHUB_DEVELOP),
        ]

        for branch, source_type in branches:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/llms.txt"
            result = await self._fetch_from_url(url)
            if result:
                content, _ = result
                return (content, url, source_type)

        return None

    async def _fetch_from_url(self, url: str) -> tuple[str, str] | None:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch from

        Returns:
            Tuple of (content, url) or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout, follow_redirects=True)

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                # Check if content looks like markdown
                content = response.text
                if not content.strip():
                    return None

                return (content, url)

        except httpx.HTTPError:
            return None
        except Exception:
            return None

    def _parse_llms_txt(self, content: str) -> LLMsTxtContent:
        """
        Parse llms.txt content into structured format.

        Args:
            content: Raw markdown content

        Returns:
            LLMsTxtContent with parsed structure
        """
        lines = content.split("\n")
        validation_warnings: list[str] = []

        # Extract H1 (project name) - required
        project_name = None
        summary = None
        description_lines: list[str] = []
        sections: list[LLMsTxtSection] = []

        current_section: LLMsTxtSection | None = None
        in_blockquote = False
        blockquote_lines: list[str] = []

        for line in lines:
            line = line.rstrip()

            # H1 - Project name
            if line.startswith("# ") and not project_name:
                project_name = line[2:].strip()
                continue

            # H2 - Section
            if line.startswith("## "):
                if current_section:
                    sections.append(current_section)
                current_section = LLMsTxtSection(title=line[3:].strip(), links=[])
                continue

            # Blockquote - Summary
            if line.startswith("> "):
                in_blockquote = True
                blockquote_lines.append(line[2:])
                continue

            if in_blockquote and line.startswith(">"):
                blockquote_lines.append(line[1:].strip())
                continue

            if in_blockquote and not line.startswith(">"):
                in_blockquote = False
                summary = " ".join(blockquote_lines).strip()

            # Links in sections
            if current_section and line.strip().startswith("- ["):
                link_data = self._parse_link(line.strip())
                if link_data:
                    current_section.links.append(link_data)
                continue

            # Description text
            if not current_section and line.strip() and not in_blockquote:
                description_lines.append(line)

        # Add last section
        if current_section:
            sections.append(current_section)

        # Validation
        is_valid = True
        if not project_name:
            is_valid = False
            validation_warnings.append("Missing required H1 with project name")

        description = "\n".join(description_lines).strip() if description_lines else None

        return LLMsTxtContent(
            project_name=project_name or "Unknown",
            summary=summary,
            description=description,
            sections=sections,
            raw_content=content,
            is_valid=is_valid,
            validation_warnings=validation_warnings,
        )

    def _parse_link(self, line: str) -> dict[str, str] | None:
        """
        Parse a markdown link line.

        Expected format: - [title](url): optional description

        Args:
            line: Markdown link line

        Returns:
            Dictionary with url, title, and optional description
        """
        # Pattern: - [title](url): description
        pattern = r"^-\s*\[(.*?)\]\((.*?)\)(?::\s*(.*))?$"
        match = re.match(pattern, line)

        if match:
            title = match.group(1).strip()
            url = match.group(2).strip()
            description = match.group(3).strip() if match.group(3) else ""

            return {
                "title": title,
                "url": url,
                "description": description,
            }

        return None

    def _extract_repository_url(self, registry_data: dict[str, Any]) -> str | None:
        """Extract repository URL from registry data."""
        # Try common keys
        repo_url = (
            registry_data.get("repository_url")
            or registry_data.get("repository", {}).get("url")
            or registry_data.get("repo_url")
        )

        if repo_url and isinstance(repo_url, str):
            # Clean up git URLs
            cleaned_url: str = repo_url.replace("git+", "").replace(".git", "")
            return cleaned_url

        return None

    def _extract_homepage_url(self, registry_data: dict[str, Any]) -> str | None:
        """Extract homepage URL from registry data."""
        # Try common keys
        homepage = (
            registry_data.get("homepage")
            or registry_data.get("homepage_url")
            or registry_data.get("home_page")
        )

        if homepage and isinstance(homepage, str) and homepage.startswith("http"):
            homepage_str: str = homepage
            return homepage_str

        return None
