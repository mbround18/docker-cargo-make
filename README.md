# docker-cargo-make

[![Docker Pulls](https://img.shields.io/docker/pulls/mbround18/cargo-make)](https://hub.docker.com/r/mbround18/cargo-make)
[![GitHub Release](https://img.shields.io/github/v/release/sagiegurari/cargo-make)](https://github.com/sagiegurari/cargo-make/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight Docker image containing [cargo-make], a powerful build tool and task runner for Rust projects. This container provides an easy way to use cargo-make in CI/CD pipelines and development environments without local installation.

[cargo-make]: https://github.com/sagiegurari/cargo-make

## Features

- 🚀 Pre-built cargo-make binary ready to use
- 🐳 Minimal Docker image for efficient CI/CD
- 🔄 Automated synchronization with cargo-make releases
- 📦 Multi-architecture support

## Quick Start

### Using in Dockerfile

```Dockerfile
FROM rust:1.88 as builder
WORKDIR /app
COPY . .
COPY --from=mbround18/cargo-make /usr/local/bin/cargo-make /usr/local/cargo/bin/
RUN cargo make build
```

### Running Directly

```bash
# Pull and run a specific version
docker run --rm mbround18/cargo-make:0.37.20 cargo make --version

# Run cargo-make commands directly
docker run --rm -v $(pwd):/workspace -w /workspace mbround18/cargo-make cargo make build

# Interactive shell with cargo-make available
docker run --rm -it -v $(pwd):/workspace -w /workspace mbround18/cargo-make sh
```

## Examples

### Basic Build Task

```dockerfile
FROM mbround18/cargo-make:latest as make
FROM rust:1.88 as builder

WORKDIR /app
COPY . .
COPY --from=make /usr/local/bin/cargo-make /usr/local/cargo/bin/

RUN cargo make ci-flow
```

### Multi-stage Build with Tests

```dockerfile
FROM mbround18/cargo-make:latest as make
FROM rust:1.88 as builder

WORKDIR /app
COPY . .
COPY --from=make /usr/local/bin/cargo-make /usr/local/cargo/bin/

# Run tests and build
RUN cargo make test
RUN cargo make build --release

FROM debian:bookworm-slim
COPY --from=builder /app/target/release/myapp /usr/local/bin/
CMD ["myapp"]
```

## Contributing

Contributions are welcome! This repository includes automation tools for maintaining Docker images and syncing with cargo-make releases.

For development setup, available commands, and contribution guidelines, please see [Code of Conduct](docs/CODE_OF_CONDUCT.md)

For issues related to cargo-make functionality, please report them to the [cargo-make repository](https://github.com/sagiegurari/cargo-make/issues).

For issues specific to this Docker container, please use this repository's issue tracker.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- [cargo-make Documentation](https://github.com/sagiegurari/cargo-make)
- [Example Implementation](https://github.com/mbround18/valheim-docker/blob/ab63fe348eb1b7425508b461e4835ca43676db2e/Dockerfile.odin#L32)
