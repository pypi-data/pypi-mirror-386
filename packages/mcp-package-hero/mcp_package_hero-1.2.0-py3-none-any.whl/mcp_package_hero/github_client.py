"""GitHub API client for repository metrics."""

from datetime import datetime, timezone
from typing import Any

import httpx


class GitHubMetrics:
    """GitHub repository metrics."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize from GitHub API response."""
        self.stars: int = data.get("stargazers_count", 0)
        self.open_issues: int = data.get("open_issues_count", 0)
        self.forks: int = data.get("forks_count", 0)
        self.watchers: int = data.get("watchers_count", 0)
        self.has_license: bool = data.get("license") is not None
        self.license_name: str | None = data.get("license", {}).get("name") if data.get("license") else None
        self.description: str | None = data.get("description")
        self.homepage: str | None = data.get("homepage")

        # Parse last update
        updated_at = data.get("updated_at") or data.get("pushed_at")
        if updated_at:
            last_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            self.last_updated: datetime | None = last_dt
            self.days_since_update: int | None = (datetime.now(timezone.utc) - last_dt).days
        else:
            self.last_updated = None
            self.days_since_update = None


class GitHubClient:
    """Client for GitHub API v3."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize GitHub client.

        Args:
            token: Optional GitHub personal access token for higher rate limits
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"

    async def get_repo_metrics(self, owner: str, repo: str) -> GitHubMetrics | None:
        """Get repository metrics from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            GitHubMetrics object or None if not found
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()
                return GitHubMetrics(data)

            except httpx.HTTPError:
                return None

    async def get_issue_stats(self, owner: str, repo: str) -> dict[str, int]:
        """Get issue statistics from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with open and closed issue counts
        """
        # Get open issues
        open_url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params: dict[str, str | int] = {"state": "open", "per_page": 1}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(open_url, headers=self.headers, params=params, timeout=10.0)
                response.raise_for_status()

                # GitHub returns total count in Link header
                open_count = 0
                if "Link" in response.headers:
                    # Parse link header to get total pages
                    link_header = response.headers["Link"]
                    if 'rel="last"' in link_header:
                        # Extract page number from last page link
                        import re
                        match = re.search(r'page=(\d+)>; rel="last"', link_header)
                        if match:
                            open_count = int(match.group(1))
                else:
                    # If no pagination, count items
                    open_count = len(response.json())

                # Get closed issues count (last 30 days)
                from datetime import timedelta
                since_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                closed_url = f"{self.base_url}/repos/{owner}/{repo}/issues"
                params_closed: dict[str, str | int] = {"state": "closed", "since": since_date, "per_page": 100}

                response = await client.get(closed_url, headers=self.headers, params=params_closed, timeout=10.0)
                response.raise_for_status()
                closed_count = len(response.json())

                return {
                    "open_issues": open_count,
                    "closed_issues_30d": closed_count,
                }

            except httpx.HTTPError:
                return {"open_issues": 0, "closed_issues_30d": 0}

    async def get_pr_stats(self, owner: str, repo: str) -> dict[str, int]:
        """Get pull request statistics from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with open and merged PR counts
        """
        # Get open PRs
        open_url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params: dict[str, str | int] = {"state": "open", "per_page": 1}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(open_url, headers=self.headers, params=params, timeout=10.0)
                response.raise_for_status()

                open_count = 0
                if "Link" in response.headers:
                    import re
                    link_header = response.headers["Link"]
                    if 'rel="last"' in link_header:
                        match = re.search(r'page=(\d+)>; rel="last"', link_header)
                        if match:
                            open_count = int(match.group(1))
                else:
                    open_count = len(response.json())

                # Get merged PRs (last 30 days)
                from datetime import timedelta
                since_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                closed_url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
                params_closed: dict[str, str | int] = {"state": "closed", "per_page": 100}

                response = await client.get(closed_url, headers=self.headers, params=params_closed, timeout=10.0)
                response.raise_for_status()

                # Count merged PRs
                prs = response.json()
                merged_count = sum(1 for pr in prs if pr.get("merged_at"))

                return {
                    "open_prs": open_count,
                    "merged_prs_30d": merged_count,
                }

            except httpx.HTTPError:
                return {"open_prs": 0, "merged_prs_30d": 0}

    @staticmethod
    def extract_repo_from_url(url: str) -> tuple[str, str] | None:
        """Extract owner and repo from GitHub URL.

        Args:
            url: GitHub repository URL

        Returns:
            Tuple of (owner, repo) or None if invalid
        """
        import re

        # Match github.com URLs
        pattern = r"github\.com/([^/]+)/([^/]+)"
        match = re.search(pattern, url)

        if match:
            owner = match.group(1)
            repo = match.group(2).removesuffix(".git")
            return owner, repo

        return None
