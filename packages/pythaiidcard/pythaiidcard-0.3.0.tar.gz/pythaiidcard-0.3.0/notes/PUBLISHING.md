# Publishing Guide for pythaiidcard

This guide covers building and publishing pythaiidcard to PyPI using `uv`.

## Prerequisites

1. **PyPI Account**
   - Create account at https://pypi.org/account/register/
   - Verify your email address

2. **API Token**
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with "Entire account" scope
   - Save the token securely (starts with `pypi-`)

3. **Optional: TestPyPI Account**
   - Create account at https://test.pypi.org/account/register/
   - Create API token at https://test.pypi.org/manage/account/token/

## Pre-Release Checklist

Before publishing, ensure:

- [ ] All tests pass
- [ ] Code is formatted with ruff
- [ ] Documentation builds without errors
- [ ] Version number is updated
- [ ] CHANGELOG is updated (create if needed)
- [ ] README is up to date
- [ ] All changes are committed

## Version Update

Update the version in two places:

1. **pyproject.toml**:
```toml
[project]
version = "0.1.0"  # Update this
```

2. **pythaiidcard/__init__.py**:
```python
__version__ = "0.1.0"  # Update this
```

## Building the Package

### Clean Previous Builds

```bash
# Using mise
mise run clean

# Or manually
rm -rf dist/ build/ *.egg-info
```

### Build with uv

```bash
# Using mise (recommended)
mise run build

# Or directly with uv
uv build
```

This creates:
- `dist/pythaiidcard-{version}-py3-none-any.whl` (wheel)
- `dist/pythaiidcard-{version}.tar.gz` (source distribution)

### Verify Build

Check what's included in the package:

```bash
# List wheel contents
python -m zipfile -l dist/pythaiidcard-*.whl

# List tarball contents
tar -tzf dist/pythaiidcard-*.tar.gz
```

Verify metadata:

```bash
# Check package metadata
python -m tarfile -l dist/pythaiidcard-*.tar.gz | grep METADATA
tar -xzf dist/pythaiidcard-*.tar.gz --to-stdout '*/METADATA' | less
```

## Publishing

### Option 1: Test on TestPyPI First (Recommended)

Test your package on TestPyPI before publishing to production PyPI:

```bash
# Using mise (recommended)
UV_PUBLISH_TOKEN=pypi-YOUR_TESTPYPI_TOKEN mise run publish-test

# Or directly with uv
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-YOUR_TESTPYPI_TOKEN
```

Or use environment variable:

```bash
export UV_PUBLISH_TOKEN=pypi-YOUR_TESTPYPI_TOKEN
mise run publish-test
```

Test installation from TestPyPI:

```bash
# Create test environment
uv venv test-env
source test-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pythaiidcard

# Test it works
python -c "from pythaiidcard import ThaiIDCardReader; print('Success!')"

# Clean up
deactivate
rm -rf test-env
```

### Option 2: Publish to Production PyPI

Once verified on TestPyPI, publish to production:

```bash
# Using mise (recommended - includes confirmation prompt)
UV_PUBLISH_TOKEN=pypi-YOUR_PYPI_TOKEN mise run publish

# Or directly with uv
uv publish --token pypi-YOUR_PYPI_TOKEN
```

Or use environment variable:

```bash
export UV_PUBLISH_TOKEN=pypi-YOUR_PYPI_TOKEN
mise run publish  # Will prompt for confirmation
```

### Using Stored Credentials

For convenience, configure credentials in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN
```

Then publish without specifying token:

```bash
# Test
uv publish --publish-url https://test.pypi.org/legacy/

# Production
uv publish
```

## Post-Publication

After successful publication:

### 1. Create Git Tag

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 2. Create GitHub Release

1. Go to https://github.com/ninyawee/pythaiidcard/releases/new
2. Select the tag you just created
3. Add release notes (from CHANGELOG)
4. Attach the distribution files (optional)
5. Publish release

### 3. Verify Installation

Test that users can install the package:

```bash
# Fresh environment
uv venv verify-env
source verify-env/bin/activate

# Install from PyPI
pip install pythaiidcard

# Verify
python -c "import pythaiidcard; print(pythaiidcard.__version__)"

# Clean up
deactivate
rm -rf verify-env
```

### 4. Update Documentation

If using GitHub Pages for documentation:

```bash
uv run mkdocs gh-deploy
```

### 5. Announce

Consider announcing the release:
- GitHub Discussions
- Social media
- Python communities
- Relevant forums

## Troubleshooting

### Authentication Failed

```
HTTP Error 403: Invalid or non-existent authentication information
```

**Solution**: Check your API token:
- Token must start with `pypi-`
- Token must have correct scope
- Token must not be expired
- Use `__token__` as username (not your PyPI username)

### File Already Exists

```
HTTP Error 400: File already exists
```

**Solution**: You cannot re-upload the same version. Options:
1. Delete from PyPI (if just published)
2. Increment version number
3. Use `--skip-existing` flag (not recommended)

### Package Name Taken

```
HTTP Error 403: The name 'pythaiidcard' is too similar to an existing project
```

**Solution**:
1. Choose a different name
2. Contact PyPI support if you believe you have rights to the name

### Large Package Size

If package is unexpectedly large:

```bash
# Check what's included
tar -tzf dist/pythaiidcard-*.tar.gz

# Add patterns to .gitignore or use [tool.hatch.build] in pyproject.toml
```

## Automated Publishing (GitHub Actions)

For automated publishing on release, create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For trusted publishing
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
        run: uv publish
```

Add your PyPI API token to GitHub Secrets:
1. Go to repo Settings → Secrets and variables → Actions
2. Add new secret named `PYPI_API_TOKEN`
3. Paste your PyPI API token

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes (1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (1.0.0 → 1.1.0)
- **PATCH**: Bug fixes, backward compatible (1.0.0 → 1.0.1)

Pre-release versions:
- Alpha: `0.1.0a1`, `0.1.0a2`
- Beta: `0.1.0b1`, `0.1.0b2`
- Release Candidate: `0.1.0rc1`, `0.1.0rc2`

## Quick Reference

```bash
# View all available tasks
mise tasks

# Clean build artifacts
mise run clean

# Build package
mise run build

# Run all verification checks
mise run verify

# Test on TestPyPI
UV_PUBLISH_TOKEN=pypi-TOKEN mise run publish-test

# Publish to PyPI
UV_PUBLISH_TOKEN=pypi-TOKEN mise run publish

# Tag and push
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Deploy docs
mise run docs-deploy
```

### All Available Tasks

```bash
mise run build         # Build distribution packages
mise run clean         # Clean build artifacts and cache
mise run dev           # Install all dependencies
mise run docs-build    # Build documentation
mise run docs-deploy   # Deploy docs to GitHub Pages
mise run docs-serve    # Serve docs locally
mise run format        # Format code with ruff
mise run format-check  # Check code formatting
mise run lint          # Run linting checks
mise run publish       # Publish to PyPI
mise run publish-test  # Publish to TestPyPI
mise run verify        # Run all verification checks
```

## Security Best Practices

1. **Never commit tokens** to git
2. **Use scoped tokens** (project-specific when possible)
3. **Rotate tokens** periodically
4. **Use environment variables** or `~/.pypirc` for credentials
5. **Enable 2FA** on PyPI account
6. **Consider trusted publishing** with GitHub Actions

## Support

For publishing issues:
- PyPI Status: https://status.python.org/
- PyPI Support: https://pypi.org/help/
- GitHub Issues: https://github.com/ninyawee/pythaiidcard/issues

---

**Last Updated**: 2025-10-23
**Package**: pythaiidcard
**Current Version**: 0.1.0
