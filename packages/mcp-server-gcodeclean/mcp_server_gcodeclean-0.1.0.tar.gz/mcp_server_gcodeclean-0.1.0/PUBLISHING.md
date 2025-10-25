# Publishing to PyPI

## Prerequisites

1. Create PyPI account at https://pypi.org/account/register/
2. Create API token at https://pypi.org/manage/account/token/
3. Configure credentials:

```bash
# Option 1: Environment variable
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=<your-pypi-token>

# Option 2: ~/.pypirc file
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = <your-pypi-token>
EOF
chmod 600 ~/.pypirc
```

## Publishing Steps

### 1. Verify Package Name Availability

```bash
# Check if name is available on PyPI
pip search mcp-server-gcodeclean
# Or visit: https://pypi.org/project/mcp-server-gcodeclean/
```

### 2. Update Version

Edit `pyproject.toml` and increment version:
```toml
version = "0.1.0"  # Change to "0.1.1", "0.2.0", etc.
```

### 3. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

### 4. Build Package

```bash
uv build
```

This creates:
- `dist/mcp_server_gcodeclean-<version>.tar.gz` (source distribution)
- `dist/mcp_server_gcodeclean-<version>-py3-none-any.whl` (wheel)

### 5. Verify Package Contents

```bash
# Check source distribution
tar -tzf dist/mcp_server_gcodeclean-*.tar.gz | less

# Check wheel
unzip -l dist/mcp_server_gcodeclean-*.whl | less

# Verify resources are included
tar -tzf dist/mcp_server_gcodeclean-*.tar.gz | grep resources
```

### 6. Test Installation Locally

```bash
# Create test venv
python -m venv test-env
source test-env/bin/activate

# Install from wheel
pip install dist/mcp_server_gcodeclean-*.whl

# Test the command
mcp-server-gcodeclean --help

# Verify binary detection
python -c "from mcp_server_gcodeclean.server import get_gcodeclean_path; print(get_gcodeclean_path())"

# Clean up
deactivate
rm -rf test-env
```

### 7. Upload to TestPyPI (Optional)

```bash
# First time setup
pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ mcp-server-gcodeclean
```

### 8. Upload to PyPI

```bash
twine upload dist/*
```

### 9. Verify Upload

Visit https://pypi.org/project/mcp-server-gcodeclean/ to confirm.

### 10. Test Installation from PyPI

```bash
# Using pip
pip install mcp-server-gcodeclean

# Using uvx (recommended for MCP servers)
uvx mcp-server-gcodeclean
```

## Post-Publication

### Update README

Add installation instructions:

```markdown
## Installation from PyPI

Using uvx (recommended):
```bash
uvx mcp-server-gcodeclean
```

Using pip:
```bash
pip install mcp-server-gcodeclean
```
\```

### Update Claude Desktop Config

Users can now reference the package directly:

```json
{
  "mcpServers": {
    "gcodeclean": {
      "command": "uvx",
      "args": ["mcp-server-gcodeclean"]
    }
  }
}
```

### Tag Release in Git

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

## Version Bumping

For subsequent releases:

1. Update version in `pyproject.toml`
2. Update CHANGELOG if you create one
3. Commit changes
4. Build and upload
5. Tag release in git

## Troubleshooting

**Package name already taken:**
- Choose a different name in `pyproject.toml`
- Update `name` field and rebuild

**Upload rejected (file already exists):**
- PyPI doesn't allow re-uploading same version
- Increment version number and rebuild

**Missing files in distribution:**
- Check `MANIFEST.in`
- Verify `pyproject.toml` includes correct patterns
- Rebuild and re-check contents

**Binary files not executable:**
- Should be handled automatically
- If issues, check file permissions in source

## PyPI Package Size Limits

- Maximum file size: 100MB
- Current package: ~29MB (within limit)
- If exceeding: Consider removing unused platform binaries
