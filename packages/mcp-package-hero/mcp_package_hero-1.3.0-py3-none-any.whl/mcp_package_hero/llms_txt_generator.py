"""Generator for creating llms.txt files from project directories."""

import os
from pathlib import Path

from .llms_txt_models import LLMsTxtGenerateResponse, LLMsTxtStatus


class LLMsTxtGenerator:
    """Generator for creating llms.txt files."""

    # Common patterns to ignore
    IGNORE_PATTERNS = {
        ".git",
        ".github",
        ".vscode",
        ".idea",
        "__pycache__",
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "coverage",
        ".coverage",
        "htmlcov",
        "*.pyc",
        "*.egg-info",
    }

    # File categories to discover
    FILE_CATEGORIES = {
        "documentation": [
            "README.md",
            "README.rst",
            "README.txt",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "HISTORY.md",
            "docs/",
        ],
        "examples": ["examples/", "samples/", "demo/"],
        "api": ["API.md", "api/", "reference/"],
        "guides": ["docs/guides/", "tutorials/", "docs/tutorials/"],
        "configuration": ["CONFIG.md", ".env.example", "config.example.json"],
    }

    def __init__(self) -> None:
        """Initialize the generator."""
        pass

    async def generate(
        self,
        project_name: str,
        description: str,
        scan_directory: str = ".",
        sections: list[str] | None = None,
        include_file_tree: bool = True,
    ) -> LLMsTxtGenerateResponse:
        """
        Generate llms.txt content for a project.

        Args:
            project_name: Name of the project
            description: Brief project description
            scan_directory: Directory to scan for files
            sections: Specific sections to include (or None for all)
            include_file_tree: Whether to include discovered files

        Returns:
            LLMsTxtGenerateResponse with generated content
        """
        try:
            # Scan directory for files
            discovered_files = {}
            if include_file_tree:
                discovered_files = self._scan_directory(scan_directory, sections)

            # Generate markdown content
            content = self._generate_markdown(
                project_name=project_name,
                description=description,
                discovered_files=discovered_files,
            )

            return LLMsTxtGenerateResponse(
                content=content,
                discovered_files=discovered_files,
                suggested_path=os.path.join(scan_directory, "llms.txt"),
                status=LLMsTxtStatus.SUCCESS,
            )

        except Exception as e:
            return LLMsTxtGenerateResponse(
                content="",
                discovered_files={},
                status=LLMsTxtStatus.ERROR,
                error_message=f"Failed to generate llms.txt: {e!s}",
            )

    def _scan_directory(
        self, directory: str, sections: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """
        Scan directory for documentation files.

        Args:
            directory: Directory to scan
            sections: Specific sections to scan for (or None for all)

        Returns:
            Dictionary mapping category to list of discovered file paths
        """
        discovered: dict[str, list[str]] = {}
        base_path = Path(directory).resolve()

        # Determine which categories to scan
        categories_to_scan = sections if sections else list(self.FILE_CATEGORIES.keys())

        for category in categories_to_scan:
            if category not in self.FILE_CATEGORIES:
                continue

            patterns = self.FILE_CATEGORIES[category]
            discovered[category] = []

            for pattern in patterns:
                # Handle directory patterns
                if pattern.endswith("/"):
                    dir_name = pattern.rstrip("/")
                    dir_path = base_path / dir_name

                    if dir_path.exists() and dir_path.is_dir():
                        # Find markdown and text files in directory
                        files = self._find_docs_in_dir(dir_path, base_path)
                        discovered[category].extend(files)

                # Handle file patterns
                else:
                    file_path = base_path / pattern
                    if file_path.exists() and file_path.is_file():
                        rel_path = file_path.relative_to(base_path)
                        discovered[category].append(str(rel_path))

        # Remove empty categories
        discovered = {k: v for k, v in discovered.items() if v}

        return discovered

    def _find_docs_in_dir(
        self, directory: Path, base_path: Path, max_depth: int = 3,
    ) -> list[str]:
        """
        Find documentation files in a directory.

        Args:
            directory: Directory to search
            base_path: Base path for relative paths
            max_depth: Maximum depth to recurse

        Returns:
            List of relative file paths
        """
        docs: list[str] = []
        doc_extensions = {".md", ".rst", ".txt", ".html"}

        try:
            depth = len(directory.relative_to(base_path).parts)
            if depth > max_depth:
                return docs

            for item in directory.iterdir():
                # Skip ignored patterns
                if any(ignore in str(item) for ignore in self.IGNORE_PATTERNS):
                    continue

                if item.is_file() and item.suffix in doc_extensions:
                    rel_path = item.relative_to(base_path)
                    docs.append(str(rel_path))

                elif item.is_dir():
                    # Recurse into subdirectories
                    docs.extend(self._find_docs_in_dir(item, base_path, max_depth))

        except (PermissionError, OSError):
            pass

        return sorted(docs)

    def _generate_markdown(
        self,
        project_name: str,
        description: str,
        discovered_files: dict[str, list[str]],
    ) -> str:
        """
        Generate llms.txt markdown content.

        Args:
            project_name: Name of the project
            description: Project description
            discovered_files: Discovered files by category

        Returns:
            Markdown content following llms.txt spec
        """
        lines: list[str] = []

        # H1 - Project name (required)
        lines.append(f"# {project_name}")
        lines.append("")

        # Blockquote - Summary
        lines.append(f"> {description}")
        lines.append("")

        # Sections with file links
        section_titles = {
            "documentation": "Documentation",
            "examples": "Examples",
            "api": "API Reference",
            "guides": "Guides & Tutorials",
            "configuration": "Configuration",
        }

        for category, files in discovered_files.items():
            if not files:
                continue

            section_title = section_titles.get(category, category.title())
            lines.append(f"## {section_title}")
            lines.append("")

            for file_path in files:
                # Generate a readable title from filename
                title = self._generate_file_title(file_path)

                # Create relative URL (for local use, this would need to be adjusted)
                # For now, we'll use the file path as the URL
                url = file_path.replace("\\", "/")

                # Add description hint based on filename
                description_hint = self._generate_file_description(file_path)

                if description_hint:
                    lines.append(f"- [{title}]({url}): {description_hint}")
                else:
                    lines.append(f"- [{title}]({url})")

            lines.append("")

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return "\n".join(lines)

    def _generate_file_title(self, file_path: str) -> str:
        """
        Generate a readable title from a file path.

        Args:
            file_path: File path

        Returns:
            Readable title
        """
        # Get filename without extension
        filename = Path(file_path).stem

        # Handle common names
        if filename.upper() == "README":
            return "README"
        if filename.upper() == "CONTRIBUTING":
            return "Contributing Guide"
        if filename.upper() == "CHANGELOG":
            return "Changelog"
        if filename.upper() == "API":
            return "API Reference"

        # Convert snake_case or kebab-case to Title Case
        title = filename.replace("_", " ").replace("-", " ")
        title = " ".join(word.capitalize() for word in title.split())

        return title

    def _generate_file_description(self, file_path: str) -> str:
        """
        Generate a brief description hint based on filename.

        Args:
            file_path: File path

        Returns:
            Description hint or empty string
        """
        filename_lower = Path(file_path).name.lower()
        path_lower = file_path.lower()

        # Common file descriptions
        if "readme" in filename_lower:
            return "Project overview and getting started"
        if "contributing" in filename_lower:
            return "Guidelines for contributing"
        if "changelog" in filename_lower or "history" in filename_lower:
            return "Version history and changes"
        if "api" in path_lower or "reference" in path_lower:
            return "API reference documentation"
        if "tutorial" in path_lower or "guide" in path_lower:
            return "Tutorial or guide"
        if "example" in path_lower or "demo" in path_lower:
            return "Example code"
        if "config" in filename_lower:
            return "Configuration reference"
        if "quickstart" in filename_lower or "getting-started" in filename_lower:
            return "Quick start guide"

        return ""
