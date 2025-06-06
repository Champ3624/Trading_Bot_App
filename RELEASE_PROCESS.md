# Release Process

This document outlines the process for releasing new versions of the trading bot.

## Versioning

We follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):
- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality
- PATCH: Backwards-compatible bug fixes

## Pre-release Checklist

1. Update version number in:
   - `setup.py`
   - `trading_bot/__init__.py`
   - Documentation

2. Ensure all tests pass:
   ```bash
   pytest --cov=src tests/
   ```

3. Update documentation:
   - README.md
   - CONFIGURATION.md
   - DEPLOYMENT.md
   - CHANGELOG.md

4. Review and update dependencies:
   ```bash
   pip freeze > requirements.txt
   ```

5. Create a release branch:
   ```bash
   git checkout -b release/vX.Y.Z
   ```

## Release Process

1. Create a pull request from the release branch to main
2. Get code review and approval
3. Merge the pull request
4. Create a new release on GitHub:
   - Tag version (vX.Y.Z)
   - Release title: "Version X.Y.Z"
   - Release notes from CHANGELOG.md
   - Attach any additional files

5. Build and push Docker image:
   ```bash
   docker build -t trading-bot:vX.Y.Z .
   docker tag trading-bot:vX.Y.Z trading-bot:latest
   docker push trading-bot:vX.Y.Z
   docker push trading-bot:latest
   ```

6. Deploy to production:
   - The CI/CD pipeline will automatically deploy the new version
   - Monitor the deployment in the GitHub Actions tab
   - Verify the deployment in the web interface

## Post-release Tasks

1. Update development version number
2. Create a new development branch
3. Notify users of the new release
4. Monitor for any issues
5. Update documentation if needed

## Emergency Releases

For critical bug fixes:

1. Create a hotfix branch from the latest release tag
2. Make minimal necessary changes
3. Update version number (PATCH version)
4. Follow the normal release process
5. Merge changes back to main

## Release Schedule

- Major releases: Quarterly
- Minor releases: Monthly
- Patch releases: As needed

## Release Communication

1. Release notes in CHANGELOG.md
2. GitHub release notes
3. Email notification to users
4. Update documentation
5. Social media announcement (if applicable)

## Rollback Procedure

If issues are detected after release:

1. Stop the current version:
   ```bash
   docker stop trading-bot
   docker rm trading-bot
   ```

2. Roll back to previous version:
   ```bash
   docker run -d \
     --name trading-bot \
     -p 5000:5000 \
     -v $(pwd)/config.json:/app/config.json \
     -v $(pwd)/logs:/app/logs \
     trading-bot:vX.Y.Z
   ```

3. Notify users of the rollback
4. Document the issue and resolution
5. Plan for a new release with the fix

## Release Metrics

Track the following metrics for each release:

1. Number of issues reported
2. Time to resolution
3. User adoption rate
4. Performance metrics
5. System stability

## Support

For release-related issues:

1. Check the release documentation
2. Review the release notes
3. Contact the development team
4. Check the issue tracker
5. Review the logs 