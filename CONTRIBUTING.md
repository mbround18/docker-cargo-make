# Contributing to docker-cargo-make

Thank you for your interest in contributing to docker-cargo-make! This guide will help you get started with development and contribution workflows.

## Development Setup

### Prerequisites

- Docker daemon running and configured
- Python 3.8+ with uv package manager
- Docker Hub credentials configured for pushing (if contributing image builds)
- Internet connection for GitHub API and Docker Hub access

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/mbround18/docker-cargo-make.git
   cd docker-cargo-make
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

## Development Tools

This repository includes automation tools for maintaining the Docker images:

### Available Commands

| Command                      | Description                                                       |
| ---------------------------- | ----------------------------------------------------------------- |
| `inv diff`                   | Compare GitHub releases with Docker Hub tags                      |
| `inv sync`                   | Build and push missing Docker images (up to 4 concurrent workers) |
| `inv sync --replace VERSION` | Rebuild and push a specific version                               |
| `inv sync --replace all`     | Rebuild and push all versions                                     |

### Usage Examples

```bash
# Show version differences between GitHub and Docker Hub
inv diff

# Sync missing versions to Docker Hub
inv sync

# Rebuild a specific version
inv sync --replace 0.37.20

# Rebuild all versions
inv sync --replace all
```

### Skip Configuration

Some versions may need to be skipped due to build issues or other problems. You can configure skipped versions in `config/skip.json`:

```json
{
  "0.35.3": "This build doesn't match the other versions and can't be deployed."
}
```

Skipped versions will:

- Show as "Skipped" in the `inv diff` output with the reason
- Be excluded from `inv sync` operations
- Appear in the build summary with skip reasons

## Project Structure

```
docker-cargo-make/
├── tasks.py                 # Main invoke tasks (entry point)
├── utils/                   # Utility modules
│   ├── __init__.py
│   ├── api.py              # GitHub and Docker Hub API interactions
│   ├── auth.py             # Authentication helpers
│   ├── config.py           # Configuration loading (skip.json)
│   ├── docker_ops.py       # Docker build and push operations
│   └── version_compare.py  # Version comparison and filtering
├── config/
│   └── skip.json          # Versions to skip with reasons
├── .github/workflows/
│   └── docker-release.yml # Automated image building
└── README.md              # User documentation
```

### Module Responsibilities

- **`tasks.py`**: Main entry point with invoke tasks (`diff`, `sync`)
- **`utils/api.py`**: GitHub releases and Docker Hub tags fetching
- **`utils/auth.py`**: GitHub token authentication
- **`utils/config.py`**: Loading skip configuration
- **`utils/docker_ops.py`**: Docker daemon interaction, building, and pushing
- **`utils/version_compare.py`**: Version filtering and comparison logic

## Automated Workflows

### GitHub Actions

The repository uses GitHub Actions to automatically sync Docker images:

- **Schedule**: Runs every Sunday at midnight UTC
- **Manual**: Can be triggered via `workflow_dispatch`
- **Permissions**: Configured for repository access and container registry operations

## Contributing Guidelines

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test your changes locally with `inv diff` and `inv sync --replace VERSION`
5. Commit your changes with clear commit messages
6. Push to your fork and submit a pull request

### Code Style

- Follow Python PEP 8 conventions
- Use type hints where appropriate
- Keep functions focused on single responsibilities
- Add docstrings for new functions
- Use Rich console for consistent output formatting

### Testing Changes

Before submitting a PR:

1. Test the diff command: `inv diff`
2. Test syncing a single version: `inv sync --replace VERSION`
3. Ensure Docker operations work correctly
4. Verify skip configuration is respected

### Adding New Features

When adding new functionality:

1. Place utility functions in appropriate modules under `utils/`
2. Update the main `tasks.py` only for new invoke tasks
3. Add any new configuration to `config/` directory
4. Update this contributing guide if needed
5. Add examples in the main README if user-facing

## Issue Reporting

### For cargo-make Issues

If you encounter issues with cargo-make functionality itself, please report them to the [cargo-make repository](https://github.com/sagiegurari/cargo-make/issues).

### For Container Issues

For issues specific to this Docker container or the automation tools:

1. Use the GitHub issue tracker
2. Include relevant logs and error messages
3. Specify Docker version and environment details
4. Provide steps to reproduce the issue

## Release Process

Images are automatically built and pushed when:

1. New cargo-make releases are detected
2. The weekly GitHub Actions workflow runs
3. Manual workflow triggers

The process:

1. Fetches latest cargo-make releases from GitHub
2. Compares with existing Docker Hub tags
3. Builds and pushes missing versions
4. Respects skip configuration for problematic versions

## Getting Help

- Check existing issues and discussions
- Review the main README for usage examples
- Look at the code in `utils/` modules for implementation details
- Feel free to open an issue for questions or clarifications
