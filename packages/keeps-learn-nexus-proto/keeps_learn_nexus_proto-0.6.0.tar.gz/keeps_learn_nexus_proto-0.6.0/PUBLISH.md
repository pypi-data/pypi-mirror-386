# Publishing Guide

## 1. Update Version

Update the version in **all** files:

### package.json
```json
{
  "version": "0.6.0"
}
```

### pyproject.toml
```toml
version = "0.6.0"
```

### nexus_proto/__init__.py
```python
__version__ = "0.6.0"
```

## 2. Commit

```bash
git add .
git commit -m "Bump version to 0.6.0"
```

## 3. Tag

```bash
git tag v0.6.0
```

## 4. Push

```bash
git push origin main
git push origin v0.6.0
```

## 5. Done!

GitHub Actions automatically publishes to **both** registries:

- **npm**: https://www.npmjs.com/package/@keeps-learn/nexus-proto
- **PyPI**: https://pypi.org/project/keeps-learn-nexus-proto/

Check the pipeline at: https://github.com/Keeps-Learn/nexus-proto/actions

## Installation

### Node.js
```bash
npm install @keeps-learn/nexus-proto
```

### Python
```bash
pip install keeps-learn-nexus-proto
```

