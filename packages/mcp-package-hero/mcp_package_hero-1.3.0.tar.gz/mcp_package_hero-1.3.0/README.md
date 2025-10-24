# 🦸 MCP Package Hero

[![PyPI](https://img.shields.io/pypi/v/mcp-package-hero.svg)](https://pypi.org/project/mcp-package-hero/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/moinsen-dev/mcp-package-hero)
[![Coverage](https://img.shields.io/badge/coverage-81%25-yellowgreen.svg)](https://github.com/moinsen-dev/mcp-package-hero)
[![Type Check](https://img.shields.io/badge/mypy-passing-blue.svg)](https://github.com/moinsen-dev/mcp-package-hero)

> A comprehensive Model Context Protocol (MCP) server for checking package versions and rating package quality across Python (PyPI), JavaScript/TypeScript (npm), Dart (pub.dev), and Rust (crates.io).

## 🎯 Purpose

MCP Package Hero helps you make informed decisions about packages by providing:
- **Version Information**: Get the latest stable version of any package
- **Quality Ratings**: Comprehensive quality analysis across multiple dimensions
- **llms.txt Documentation**: Fetch and generate LLM-friendly documentation files

Package Hero focuses on four major ecosystems:
- ✅ Python packages on PyPI
- ✅ JavaScript/TypeScript packages on npm
- ✅ Dart/Flutter packages on pub.dev
- ✅ Rust packages on crates.io

## 🚀 Features

### Version Checking
- **Simple API**: Get latest version for one or multiple packages
- **Fast**: Sub-second response times with async operations
- **Batch Support**: Check up to 10 packages at once

### Quality Rating (v1.1.0+)
- **Comprehensive Analysis**: Multi-dimensional package quality scoring
  - 🔧 **Maintenance Health** (35%): Release frequency, issue resolution, PR activity
  - 📊 **Popularity** (25%): Downloads, GitHub stars, community adoption
  - ✨ **Quality Metrics** (40%): Documentation (35%), license (25%), tests (25%), llms.txt (15%)
- **Letter Grades**: A+ to F rating system for quick assessment
- **Actionable Insights**: Key strengths and red flags for each package
- **Ecosystem Integration**: Leverages native scores (pub.dev pub points, npms.io scores)
- **llms.txt Bonus** (v1.2.0+): Packages with llms.txt get bonus points (70 for llms.txt, 100 for both llms.txt + llms-full.txt)

### llms.txt Support (v1.2.0+)
- **Fetch llms.txt**: Get LLM-friendly documentation from package repositories
- **Generate llms.txt**: Create standardized documentation for your projects
- **Multi-Source**: Searches GitHub, homepages, and documentation sites
- **Validation**: Parses and validates llms.txt format compliance
- **Smart Scanning**: Automatically discovers documentation files in projects

### Technical Excellence
- **LLM-Friendly**: Designed specifically for AI assistants and agents
- **Type-Safe**: Full type hints, Pydantic validation, and mypy compliance
- **Well-Tested**: Comprehensive coverage for all features
- **Production-Ready**: Modern Python best practices, timezone-aware, Pydantic V2

## 📦 Installation

### From PyPI (Recommended)

The fastest and easiest way to use MCP Package Hero is directly from PyPI:

```bash
# No installation needed! Just use uvx to run it directly
uvx mcp-package-hero

# Or install it as a tool for repeated use
uv tool install mcp-package-hero
```

### From Source (Development)

For development or contributing:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/moinsen-dev/mcp-package-hero.git
cd mcp-package-hero

# Install dependencies
uv sync

# Install the package in editable mode
uv pip install -e .
```

## 🔧 Configuration

Add to your MCP client configuration (e.g., Claude Desktop, Cline, etc.):

### Claude Desktop

#### Option 1: From PyPI (Recommended - Fast!)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "package-hero": {
      "command": "uvx",
      "args": ["mcp-package-hero"]
    }
  }
}
```

**Startup time**: ~1-2 seconds (first run), ~0.5 seconds (cached) ⚡

#### Option 2: From GitHub (Slower)

```json
{
  "mcpServers": {
    "package-hero": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/moinsen-dev/mcp-package-hero.git",
        "mcp-package-hero"
      ]
    }
  }
}
```

#### Option 3: From local directory (Development)

```json
{
  "mcpServers": {
    "package-hero": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/mcp-package-hero",
        "mcp-package-hero"
      ]
    }
  }
}
```

### Cline VSCode Extension

Edit `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`:

#### Option 1: From PyPI (Recommended - Fast!)

```json
{
  "mcpServers": {
    "package-hero": {
      "command": "uvx",
      "args": ["mcp-package-hero"]
    }
  }
}
```

#### Option 2: From GitHub (Slower)

```json
{
  "mcpServers": {
    "package-hero": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/moinsen-dev/mcp-package-hero.git",
        "mcp-package-hero"
      ]
    }
  }
}
```

#### Option 3: From local directory (Development)

```json
{
  "mcpServers": {
    "package-hero": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/mcp-package-hero",
        "mcp-package-hero"
      ]
    }
  }
}
```

### Claude Code

Add the server globally to Claude Code using the CLI:

#### Option 1: From PyPI (Recommended - Fast!)

```bash
claude mcp add-json package-hero '{"type":"stdio","command":"uvx","args":["mcp-package-hero"]}'
```

#### Option 2: From GitHub (Slower)

```bash
claude mcp add-json package-hero '{"type":"stdio","command":"uvx","args":["--from","git+https://github.com/moinsen-dev/mcp-package-hero.git","mcp-package-hero"]}'
```

#### Option 3: From local directory (Development)

```bash
claude mcp add-json package-hero '{"type":"stdio","command":"uv","args":["run","--directory","/path/to/mcp-package-hero","mcp-package-hero"]}'
```

## 📖 Usage

### Tool 1: Get Latest Version

Check the latest version of a single package:

```python
# Example queries for your LLM:
"What's the latest version of requests in Python?"
"Check the current version of react"
"Show me the latest version of the http package for Dart"
"What's the latest version of serde in Rust?"
```

**Tool Name**: `get_latest_version`

**Parameters**:
- `package_name` (string): Name of the package
- `ecosystem` (string): One of "python", "javascript", "dart", or "rust"

**Example Response**:
```json
{
  "package_name": "requests",
  "ecosystem": "python",
  "latest_version": "2.31.0",
  "registry_url": "https://pypi.org/project/requests/",
  "checked_at": "2025-10-06T10:30:00Z",
  "status": "success"
}
```

### Tool 2: Batch Version Check

Check multiple packages at once (max 10):

```python
# Example query:
"Check the latest versions of requests (python), react (javascript), http (dart), and serde (rust)"
```

**Tool Name**: `get_latest_versions_batch`

**Parameters**:
- `packages` (array): List of objects with `package_name` and `ecosystem`
- `max_packages` (integer, optional): Limit (default: 10)

**Example Response**:
```json
{
  "results": [
    {
      "package_name": "requests",
      "ecosystem": "python",
      "latest_version": "2.31.0",
      "status": "success"
    },
    {
      "package_name": "nonexistent-pkg",
      "ecosystem": "python",
      "latest_version": null,
      "status": "not_found"
    }
  ],
  "checked_at": "2025-10-06T10:30:00Z"
}
```

### Tool 3: Rate Package Quality (v1.1.0+)

Get comprehensive quality rating for a package:

```python
# Example queries:
"Rate the quality of the requests package"
"How good is the react package?"
"Give me a quality assessment of flutter_bloc"
"How does the serde crate rate?"
```

**Tool Name**: `rate_package`

**Parameters**:
- `package_name` (string): Name of the package
- `ecosystem` (string): One of "python", "javascript", "dart", or "rust"

**Example Response**:
```json
{
  "package_name": "requests",
  "ecosystem": "python",
  "overall_score": 86.6,
  "letter_grade": "A-",
  "maintenance": {
    "score": 78.8,
    "last_release_days": 48,
    "release_frequency_score": 80.0,
    "issue_resolution_score": 100.0,
    "pr_merge_score": 44.2
  },
  "popularity": {
    "score": 100.0,
    "downloads": 855587647,
    "stars": 53340,
    "downloads_score": 100.0,
    "stars_score": 100.0
  },
  "quality": {
    "score": 85.0,
    "has_documentation": true,
    "has_license": true,
    "has_tests": null,
    "documentation_score": 100.0,
    "license_score": 100.0,
    "test_score": 50.0
  },
  "repository_url": "https://github.com/psf/requests",
  "license": "Apache-2.0",
  "description": "Python HTTP for Humans.",
  "insights": [
    "Strong issue resolution track record",
    "Highly popular with 100K+ monthly downloads",
    "Well-starred project (1000+ stars)",
    "High quality package with good documentation and license"
  ],
  "red_flags": [],
  "status": "success"
}
```

### Tool 4: Get llms.txt (v1.2.0+)

Fetch llms.txt documentation file for a package:

```python
# Example queries:
"Get the llms.txt file for fasthtml"
"Show me the documentation structure for react"
"Fetch llms.txt and llms-full.txt for flutter_bloc"
"Get the llms.txt for tokio"
```

**Tool Name**: `get_llms_txt`

**Parameters**:
- `package_name` (string): Name of the package
- `ecosystem` (string): One of "python", "javascript", "dart", or "rust"
- `include_full` (boolean, optional): Also fetch llms-full.txt (default: false)

**Example Response**:
```json
{
  "package_name": "fasthtml",
  "ecosystem": "python",
  "llms_txt_content": {
    "project_name": "FastHTML",
    "summary": "FastHTML is a python library which brings together Starlette, Uvicorn, HTMX, and fastcore's FT FastTags",
    "sections": [
      {
        "title": "Docs",
        "links": [
          {
            "title": "FastHTML quick start",
            "url": "https://fastht.ml/docs/tutorials/quickstart_for_web_devs.html.md",
            "description": "Overview of features"
          }
        ]
      }
    ],
    "raw_content": "# FastHTML\n\n> FastHTML is a python library...",
    "is_valid": true,
    "validation_warnings": []
  },
  "source_url": "https://raw.githubusercontent.com/AnswerDotAI/fasthtml/main/llms.txt",
  "source_type": "github_main",
  "repository_url": "https://github.com/AnswerDotAI/fasthtml",
  "status": "success"
}
```

### Tool 5: Create llms.txt (v1.2.0+)

Generate an llms.txt file for your project:

```python
# Example queries:
"Create an llms.txt file for my project called 'My Library'"
"Generate llms.txt documentation for this codebase"
"Create llms.txt with only documentation and examples sections"
```

**Tool Name**: `create_llms_txt`

**Parameters**:
- `project_name` (string): Name of your project
- `description` (string): Brief project description
- `scan_directory` (string, optional): Directory to scan (default: ".")
- `sections` (list, optional): Specific sections to include (e.g., ["documentation", "examples"])

**Available Sections**: documentation, examples, api, guides, configuration

**Example Response**:
```json
{
  "content": "# My Project\n\n> A comprehensive Python library\n\n## Documentation\n\n- [README](README.md): Project overview and getting started\n- [Contributing Guide](CONTRIBUTING.md): Guidelines for contributing\n\n## Examples\n\n- [Basic Example](examples/basic.py): Example code\n",
  "discovered_files": {
    "documentation": ["README.md", "CONTRIBUTING.md"],
    "examples": ["examples/basic.py"]
  },
  "suggested_path": "./llms.txt",
  "status": "success"
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_package_hero --cov-report=html

# Run with coverage summary
uv run pytest --cov=src/mcp_package_hero --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_registries/test_pypi.py
```

### Test Results
- ✅ 68/68 tests passing
- ✅ Comprehensive coverage for version checking, rating, and llms.txt features
- ✅ All four ecosystems validated with live API calls

## 🏗️ Development

### Project Structure

```
mcp-package-hero/
├── src/mcp_package_hero/
│   ├── __init__.py
│   ├── server.py              # Main FastMCP server
│   ├── models.py              # Pydantic models
│   ├── github_client.py       # GitHub API client
│   ├── rating_calculator.py   # Rating algorithms
│   ├── registries/            # Version checking
│   │   ├── base.py
│   │   ├── pypi.py
│   │   ├── npm.py
│   │   └── pubdev.py
│   └── raters/                # Quality rating
│       ├── python_rater.py
│       ├── javascript_rater.py
│       └── dart_rater.py
├── tests/
├── README.md
└── pyproject.toml
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix safe linting issues
uv run ruff check --fix .

# Type check
uv run mypy src/
```

### Quality Standards
- ✅ **Type Safety**: Full mypy compliance with Pydantic plugin
- ✅ **Code Style**: Ruff linting and formatting
- ✅ **Modern Python**: Python 3.10+ type hints (PEP 604)
- ✅ **Timezone-Aware**: All timestamps use UTC timezone
- ✅ **Pydantic V2**: Using latest ConfigDict patterns

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) by Prefect
- Inspired by [mcp-package-version](https://github.com/sammcj/mcp-package-version) by Sam McLeod
- Part of the [Model Context Protocol](https://modelcontextprotocol.io) ecosystem

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/moinsen-dev/mcp-package-hero/issues)
- **Discussions**: [GitHub Discussions](https://github.com/moinsen-dev/mcp-package-hero/discussions)

## 🗺️ Roadmap

### v1.2.0 ✅ (Current)
- [x] llms.txt support - fetch documentation from packages
- [x] llms.txt generation - create documentation for projects
- [x] Multi-source fetching (GitHub, homepages)
- [x] Documentation validation and parsing

### v1.1.0 ✅
- [x] Package quality rating system
- [x] Multi-dimensional scoring (maintenance, popularity, quality)
- [x] GitHub integration for repository metrics
- [x] Integration with ecosystem-native scores (pub.dev, npms.io)

### v1.3.0 ✅
- [x] Rust ecosystem support (crates.io)
- [x] Full integration with existing tools (version checking, quality rating, llms.txt)
- [x] Comprehensive test coverage for Rust packages

### v1.4.0 (Planned)
- [ ] Additional ecosystems (Go, Swift)
- [ ] Cache layer for improved performance
- [ ] Support for specific version queries

### v2.0 (Future)
- [ ] Dependency tree analysis
- [ ] Version compatibility checking
- [ ] Security vulnerability detection

---

Made with ☕️ by [moinsen-dev](https://github.com/moinsen-dev)
