#!/usr/bin/env bash

# update CHANGELOG.md use GITHUB_REPO ENV as github token
git-cliff -o -v --github-repo "atticuszeller/sing-box-service"
# bump version and commit with tags
bump-my-version bump patch
# push remote
git push origin main --tags
