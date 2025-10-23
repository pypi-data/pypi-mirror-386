# Nexus Proto

Shared Protocol Buffer definitions for Nexus microservices.

## Why "Nexus"?

The name **Nexus** was chosen to represent the **central connection** between microservices. In many languages, "nexus" refers to a point of intersection or link, which is exactly what this project provides: an efficient hub for communication between distributed services built in different technologies. The idea is to create a convergence point that makes it easier to integrate systems, ensuring consistent and scalable communication, no matter the language or framework used. **Nexus** is the solution that connects and unites services in a simple and effective way.

## Features

- **Centralized Protocol Definitions**: All communication contracts are defined in a shared repository of `.proto` files.
- **Multi-Language Support**: Easily integrate microservices written in different programming languages (e.g., Python, Node.js, Java, etc.).
- **Scalable Communication**: Easily extend the system as new microservices are added to the architecture.
- **gRPC-powered**: Leveraging gRPC for high-performance communication with built-in support for multiple programming languages.

## Installation

### Node.js / npm

```bash
npm install @keeps-learn/nexus-proto
```

📦 **npm Package**: https://www.npmjs.com/package/@keeps-learn/nexus-proto

### Python / pip

```bash
pip install keeps-learn-nexus-proto
```

📦 **PyPI Package**: https://pypi.org/project/keeps-learn-nexus-proto/

## Publishing

1. Update version in `package.json`, `setup.py`, and `pyproject.toml`
2. Commit: `git commit -m "Bump version to X.Y.Z"`
3. Tag: `git tag vX.Y.Z`
4. Push: `git push origin vX.Y.Z`

GitHub Actions publishes automatically to both **npmjs.com** and **pypi.org**

See [PUBLISH.md](./PUBLISH.md) for detailed publishing instructions.
