# Publishing to PyPI Guide

This guide walks you through publishing the `social-media-posters` CLI package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org
2. **Test PyPI Account** (optional but recommended): Create an account at https://test.pypi.org
3. **GitHub Repository Access**: Admin access to configure repository secrets and environments

## Setup Steps

### 1. Configure PyPI Trusted Publishing (Recommended)

PyPI now supports "Trusted Publishing" which is more secure than API tokens. This is the preferred method.

#### For PyPI (Production):

1. Go to https://pypi.org/manage/account/publishing/
2. Scroll to "Add a new pending publisher"
3. Fill in the form:
   - **PyPI Project Name**: `social-media-posters`
   - **Owner**: `geraldnguyen`
   - **Repository name**: `social-media-posters`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `pypi`
4. Click "Add"

#### For Test PyPI (Optional, for testing):

1. Go to https://test.pypi.org/manage/account/publishing/
2. Repeat the same steps as above, but use environment name: `testpypi`

### 2. Configure GitHub Environments

1. Go to your repository settings: `https://github.com/geraldnguyen/social-media-posters/settings/environments`
2. Create two environments:
   - **pypi** (for production releases)
   - **testpypi** (for testing)
3. For each environment, you can optionally add:
   - **Required reviewers**: Add yourself to approve before publishing
   - **Deployment branches**: Restrict to specific branches/tags

### 3. Alternative: Using API Tokens (Legacy Method)

If you prefer not to use Trusted Publishing, you can use API tokens:

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token with scope: "Entire account" or specific to your project
3. Copy the token (starts with `pypi-`)
4. In GitHub repository settings, go to Secrets and variables → Actions
5. Add a new repository secret:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token

Then modify the workflow file to use the token instead of trusted publishing:
```yaml
- name: Publish distribution to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}
```

## Publishing Process

### Option 1: Automatic Publishing on Release (Recommended)

1. **Update Version**: Update the version in `pyproject.toml` (e.g., `1.12.0` → `1.12.1`)
2. **Update CHANGELOG**: Add release notes to `CHANGELOG.md`
3. **Commit Changes**: 
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 1.12.1"
   git push
   ```
4. **Create GitHub Release**:
   - Go to https://github.com/geraldnguyen/social-media-posters/releases/new
   - Choose a tag: Create new tag (e.g., `v1.12.1`)
   - Release title: `v1.12.1`
   - Description: Copy from CHANGELOG.md
   - Click "Publish release"
5. **Monitor Workflow**: 
   - The GitHub Action will automatically trigger
   - Go to Actions tab to monitor progress
   - Once complete, your package will be on PyPI!

### Option 2: Manual Publishing to Test PyPI

Test your package before publishing to production:

1. Go to Actions tab in your repository
2. Select "Publish to PyPI" workflow
3. Click "Run workflow"
4. Select branch and check "Publish to Test PyPI instead of PyPI"
5. Click "Run workflow"
6. After successful publishing, test installation:
   ```bash
   pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ social-media-posters
   ```

### Option 3: Manual Local Publishing (Not Recommended)

For testing or emergency situations:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the distribution
twine check dist/*

# Upload to Test PyPI (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*
```

## Verification

After publishing, verify your package:

1. **Check PyPI page**: https://pypi.org/project/social-media-posters/
2. **Install and test**:
   ```bash
   pip install social-media-posters
   social --version
   social --help
   ```
3. **Test platform-specific installations**:
   ```bash
   pip install social-media-posters[x]
   pip install social-media-posters[all]
   ```

## Version Numbering

Follow Semantic Versioning (SemVer):
- **Major** (X.0.0): Breaking changes
- **Minor** (1.X.0): New features, backward compatible
- **Patch** (1.12.X): Bug fixes, backward compatible

Examples:
- `1.12.0` → `1.12.1` (bug fix)
- `1.12.0` → `1.13.0` (new feature)
- `1.12.0` → `2.0.0` (breaking change)

## Troubleshooting

### Issue: "File already exists"
- **Cause**: Version already published to PyPI
- **Solution**: Increment version number in `pyproject.toml`

### Issue: "Invalid credentials"
- **Cause**: Trusted Publishing not configured or API token invalid
- **Solution**: Verify PyPI trusted publisher settings or regenerate API token

### Issue: "Distribution not found"
- **Cause**: Build step failed
- **Solution**: Check GitHub Actions logs for build errors

### Issue: "Missing dependencies"
- **Cause**: MANIFEST.in not including necessary files
- **Solution**: Review and update MANIFEST.in

### Issue: "Package name already taken"
- **Cause**: Another package with the same name exists
- **Solution**: Choose a different name or contact PyPI support if you own the name

### Issue: twine check shows "Invalid distribution metadata: unrecognized or malformed field 'license-file'"
- **Cause**: This is a known compatibility issue with older versions of twine not recognizing Metadata 2.4 format
- **Solution**: This is a false positive. The package is valid and will upload successfully to PyPI. You can safely ignore this warning or use `python -m build` output for validation instead. The GitHub Actions workflow will handle this correctly.

## Best Practices

1. **Always test on Test PyPI first** before publishing to production
2. **Use semantic versioning** for version numbers
3. **Update CHANGELOG.md** for every release
4. **Tag releases in Git** for version tracking
5. **Create detailed release notes** on GitHub releases
6. **Monitor downloads and issues** after publishing
7. **Keep dependencies up to date** but test thoroughly
8. **Respond to PyPI security advisories** promptly

## Quick Checklist

Before each release:
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Commit and push changes
- [ ] Run tests locally: `python -m unittest discover`
- [ ] Build locally: `python -m build`
- [ ] Check distribution: `twine check dist/*`
- [ ] Test installation locally: `pip install dist/*.whl`
- [ ] Test CLI: `social --version` and `social --help`
- [ ] Create GitHub release with tag
- [ ] Monitor GitHub Actions workflow
- [ ] Verify on PyPI
- [ ] Test installation from PyPI
- [ ] Announce release (if applicable)

## Additional Resources

- PyPI Documentation: https://packaging.python.org/
- Trusted Publishing Guide: https://docs.pypi.org/trusted-publishers/
- setuptools Documentation: https://setuptools.pypa.io/
- GitHub Actions for PyPI: https://github.com/marketplace/actions/pypi-publish

## Support

If you encounter issues:
1. Check GitHub Actions logs for error messages
2. Review PyPI package page for status
3. Consult PyPI documentation
4. Open an issue in the repository
