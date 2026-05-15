# sisakulint-action

[![GitHub release](https://img.shields.io/github/v/release/sisaku-security/sisakulint-action?display_name=tag&sort=semver)](https://github.com/sisaku-security/sisakulint-action/releases)
[![Marketplace](https://img.shields.io/badge/Marketplace-sisakulint-purple?logo=github)](https://github.com/marketplace/actions/sisakulint)
[![License](https://img.shields.io/github/license/sisaku-security/sisakulint-action)](./LICENSE)

A GitHub Action that runs [**sisakulint**](https://github.com/sisaku-security/sisakulint) — a fast, CI-friendly static linter and SAST for GitHub Actions workflows — and uploads the results to GitHub Code Scanning.

sisakulint covers the [OWASP Top 10 CI/CD Security Risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/): code injection via `${{ }}`, dangerous triggers (`pull_request_target`), unpinned actions, secret exfiltration, broad permissions, and more — with autofix support.

## Quick start

```yaml
name: sisakulint

on:
  pull_request:
    paths: [".github/workflows/**"]
  push:
    branches: ["main"]
    paths: [".github/workflows/**"]
  schedule:
    - cron: "0 3 * * 1"

permissions:
  contents: read
  security-events: write     # required for upload-sarif: true

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: sisaku-security/sisakulint-action@v1
        with:
          version: latest
          upload-sarif: true
          fail-on: critical
          autofix: dry-run
```

That's it. Findings appear under the **Security → Code scanning** tab, and high/critical issues are surfaced as inline PR annotations.

## Three pinning patterns

Pick the level of supply-chain hardening you want.

### 1. Floating major tag (recommended for most teams)

You always get the latest backwards-compatible release. Easiest to upgrade.

```yaml
- uses: sisaku-security/sisakulint-action@v1
  with:
    version: latest
```

### 2. Pinned release tag

You opt into a specific Action *and* sisakulint binary version. Reproducible, but no automatic security fixes for the Action itself.

```yaml
- uses: sisaku-security/sisakulint-action@v1.0.0
  with:
    version: "0.3.0"
```

### 3. Full commit SHA (recommended for security-conscious repos)

This is the [Harden-Runner](https://github.com/step-security/harden-runner) / [scorecard](https://github.com/ossf/scorecard) style. The tag is a comment; the SHA is what GitHub actually resolves. A compromised tag cannot redirect your workflow.

```yaml
- uses: sisaku-security/sisakulint-action@60c04f6a024125eb39ea6da9513407ef0e276125  # v1.0.0
  with:
    version: "0.3.0"   # also pin the binary
```

> [!TIP]
> Combine pattern 3 with [Dependabot](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file#package-ecosystem) (`package-ecosystem: github-actions`) to get automated, reviewable bump PRs that update the SHA together with the trailing version comment.

## Inputs

| Name | Default | Description |
|---|---|---|
| `version` | `latest` | sisakulint version to install. Pass a tag like `0.3.0` / `v0.3.0`, or `latest` to resolve from the GitHub API. |
| `working-directory` | repo root | Directory to `cd` into before running sisakulint. |
| `args` | `""` | Extra raw args appended to the sisakulint invocation (e.g. `-ignore "missing-timeout-minutes"`). |
| `config-file` | `""` | Path to a sisakulint config file. Passed as `-config-file`. |
| `autofix` | `off` | `off` \| `on` \| `dry-run`. `on` rewrites files in place; pair with a commit step. |
| `fail-on` | `high` | `none` \| `low` \| `medium` \| `high` \| `critical`. Minimum severity that fails the job. |
| `upload-sarif` | `true` | Upload the SARIF result to GitHub Code Scanning. Requires `security-events: write`. |
| `sarif-file` | `sisakulint.sarif` | Path the SARIF report is written to. |
| `github-token` | `${{ github.token }}` | Token used only when `version: latest` to resolve the release tag. |

## Outputs

| Name | Description |
|---|---|
| `sarif-file` | Path to the generated SARIF file. |
| `findings` | Total SARIF results produced. |
| `failing-findings` | Count of findings at or above the `fail-on` threshold. |
| `resolved-version` | The concrete sisakulint version that was installed. |

## Recipes

### Block PRs on `critical` only, warn on the rest

```yaml
- uses: sisaku-security/sisakulint-action@v1
  with:
    fail-on: critical
    upload-sarif: true
```

### Open an autofix PR

```yaml
- uses: actions/checkout@v4
- uses: sisaku-security/sisakulint-action@v1
  with:
    autofix: on
    fail-on: none           # let the autofix do its job, then commit
    upload-sarif: false
- uses: peter-evans/create-pull-request@v6
  with:
    branch: sisakulint/autofix
    commit-message: "fix(ci): sisakulint autofix"
    title: "sisakulint autofix"
```

### Local config & ignore rules

```yaml
- uses: sisaku-security/sisakulint-action@v1
  with:
    config-file: .github/sisakulint.yaml
    args: -ignore "missing-timeout-minutes"
```

## Permissions

This Action needs:

- `contents: read` — to read your workflow files.
- `security-events: write` — only when `upload-sarif: true`, to push SARIF into Code Scanning.

If your repo is in an org without GitHub Advanced Security, Code Scanning isn't available; set `upload-sarif: false` and rely on the inline PR annotations.

## How it works

1. Resolves `version` (via `https://api.github.com/repos/sisaku-security/sisakulint/releases/latest` when `latest`).
2. Downloads the matching `linux_amd64` / `linux_arm64` / `darwin_amd64` / `darwin_arm64` archive.
3. **Verifies the SHA-256 checksum** against the official `sisakulint_<ver>_checksums.txt` before extraction.
4. Runs `sisakulint -fix <autofix> -format '{{sarif .}}'` and writes SARIF.
5. Emits `::error` / `::warning` annotations per finding (Critical/High → error, others → warning).
6. Applies the `fail-on` policy by classifying each result via rule-id suffix (`-critical`, `-high`, `-medium`, `-low`) and message markers.
7. Uploads SARIF via [`github/codeql-action/upload-sarif@v3`](https://github.com/github/codeql-action) when `upload-sarif: true`.

## Compatibility

- Runners: `ubuntu-*`, `macos-*` (x64 + arm64). Windows is not supported.
- sisakulint: `v0.3.0` or later (earlier versions do not publish arm64 / checksums).
- GitHub Enterprise Server: works wherever `github/codeql-action/upload-sarif@v3` is available.

## License

[Apache-2.0](./LICENSE), matching upstream [sisakulint](https://github.com/sisaku-security/sisakulint).
