# PyPI Publishing Guide

## Quick Answer

**NO** - Simply pushing code to the repository will **NOT** automatically publish to PyPI.

Publishing to PyPI requires creating a **GitHub Release** with a version tag.

## Workflow Overview

### Current Setup

Your repository has two GitHub Actions workflows:

#### 1. **CI Workflow** (`.github/workflows/ci.yml`)
- **Triggers**: On push to `main` or `develop` branches, or on pull requests
- **Actions**:
  - Runs linting (black, isort, flake8)
  - Runs type checking (mypy)
  - Runs unit tests (pytest)
  - Uploads coverage to Codecov
  - Builds package (uv build)
  - Validates package with twine
- **Result**: ✓ Tests pass, ✗ Does NOT publish to PyPI

#### 2. **Publish Workflow** (`.github/workflows/publish.yml`)
- **Triggers**: Only on GitHub Release creation (when you publish a release)
- **Condition**: `if: startsWith(github.ref, 'refs/tags/')`
- **Actions**:
  - Builds distribution package
  - Publishes to PyPI using trusted publishing
- **Result**: ✓ Package published to PyPI

## Publishing Process

### Step 1: Update Version Number
Update the version in `pyproject.toml`:
```toml
[project]
version = "0.0.4"  # Change from 0.0.3 to 0.0.4
```

### Step 2: Commit Changes
```bash
git add pyproject.toml
git commit -m "Bump version to 0.0.4"
git push origin main
```

### Step 3: Create GitHub Release
```bash
# Create a git tag
git tag v0.0.4

# Push the tag to GitHub
git push origin v0.0.4
```

**OR** use GitHub UI:
1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Enter tag: `v0.0.4`
4. Enter title: `Release v0.0.4`
5. Add release notes
6. Click "Publish release"

### Step 4: Monitor Publishing
1. Go to GitHub Actions
2. Watch the "Publish to PyPI" workflow run
3. Check PyPI: https://pypi.org/project/egnyte-langchain-connector/

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Push Code to GitHub                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │   CI Workflow Runs             │
        │ - Linting                      │
        │ - Type checking                │
        │ - Unit tests                   │
        │ - Build package                │
        │ - Validate package             │
        └────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │   Tests Pass?                  │
        └────────────────────────────────┘
                    YES │ NO
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
    Continue              Workflow Fails (Stop)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              Create GitHub Release (Tag)                    │
│              (Manual step - NOT automatic)                  │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│          Publish Workflow Triggers                          │
│          (Only on tag push: refs/tags/*)                    │
└────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│   Build & Publish to PyPI                                   │
│   - Build distribution                                      │
│   - Upload to PyPI                                          │
│   - Package available at:                                   │
│     https://pypi.org/project/egnyte-langchain-connector/    │
└─────────────────────────────────────────────────────────────┘
```

## Current Version

**Current Version**: 0.0.3
**Last Published**: Already on PyPI
**Status**: Ready for next release

## What Triggers Publishing

### ✓ WILL Publish to PyPI
- Creating a GitHub Release with a tag
- Pushing a git tag that matches `refs/tags/*`
- Example: `git tag v0.0.4 && git push origin v0.0.4`

### ✗ WILL NOT Publish to PyPI
- Pushing to `main` branch
- Pushing to `develop` branch
- Creating a pull request
- Committing code directly
- Running CI workflow

## Security: Trusted Publishing

Your workflow uses **Trusted Publishing** (PyPI's recommended approach):
- No API tokens stored in GitHub secrets
- Uses OIDC (OpenID Connect) for authentication
- More secure than traditional API tokens
- Requires PyPI environment configuration

## Next Steps to Publish

### Option 1: Using Git Commands
```bash
# Update version
nano pyproject.toml  # Change version to 0.0.4

# Commit
git add pyproject.toml
git commit -m "Bump version to 0.0.4"
git push origin main

# Create tag and push
git tag v0.0.4
git push origin v0.0.4

# Monitor at: https://github.com/yourusername/egnyte-langchain-connector/actions
```

### Option 2: Using GitHub UI
1. Go to repository
2. Click "Releases"
3. Click "Create a new release"
4. Tag: `v0.0.4`
5. Title: `Release v0.0.4`
6. Add release notes
7. Click "Publish release"

## Verification

After publishing, verify at:
- **PyPI**: https://pypi.org/project/egnyte-langchain-connector/
- **GitHub Actions**: Check workflow run status
- **Install**: `pip install egnyte-langchain-connector==0.0.4`

## Important Notes

1. **Version Consistency**: Version in `pyproject.toml` should match the git tag
   - Tag: `v0.0.4`
   - Version: `0.0.4`

2. **CI Must Pass**: Publishing only happens if CI tests pass

3. **One Release Per Tag**: Each tag can only be released once

4. **Semantic Versioning**: Follow semver for version numbers
   - Major.Minor.Patch (e.g., 0.0.4)

5. **Release Notes**: Add meaningful release notes describing changes

## Troubleshooting

### Publishing Failed
- Check GitHub Actions logs
- Verify version in `pyproject.toml` matches tag
- Ensure CI tests passed
- Check PyPI environment configuration

### Package Not Appearing on PyPI
- Wait 5-10 minutes for PyPI to index
- Check PyPI project page
- Verify version number in tag

### Need to Republish
- Cannot republish same version
- Must create new version and tag
- Example: 0.0.4 → 0.0.5

## Summary

| Action | Publishes to PyPI? |
|--------|-------------------|
| Push to main | ✗ No |
| Push to develop | ✗ No |
| Create pull request | ✗ No |
| Push code commit | ✗ No |
| Create git tag | ✓ Yes |
| Create GitHub Release | ✓ Yes |

**Bottom Line**: You must explicitly create a GitHub Release or push a git tag to publish to PyPI. Simply pushing code will NOT publish.

---

**Current Status**: Ready to publish v0.0.4 whenever you're ready!

