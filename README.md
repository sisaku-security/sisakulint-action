# sisakulint-action

[![GitHub release](https://img.shields.io/github/v/release/sisaku-security/sisakulint-action?display_name=tag&sort=semver)](https://github.com/sisaku-security/sisakulint-action/releases)
[![Marketplace](https://img.shields.io/badge/Marketplace-sisakulint-purple?logo=github)](https://github.com/marketplace/actions/sisakulint)
[![License](https://img.shields.io/github/license/sisaku-security/sisakulint-action)](./LICENSE)

A GitHub Action that runs [**sisakulint**](https://github.com/sisaku-security/sisakulint) — a fast, CI-friendly static linter and SAST for GitHub Actions workflows — and uploads the results to GitHub Code Scanning.

sisakulint covers the [OWASP Top 10 CI/CD Security Risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/): code injection via `${{ }}`, dangerous triggers (`pull_request_target`), unpinned actions, secret exfiltration, broad permissions, and more — with autofix support.

## Quick start

```yaml
# .github/workflows/sisakulint.yml
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

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683            # v4.2.2
        with:
          persist-credentials: false
      - uses: sisaku-security/sisakulint-action@f92185efeaff7ac9a6ed72b6e5d68412ea13ab54  # v1.0.0
        with:
          version: "0.3.0"
```

And the matching `.github/dependabot.yaml` so SHA bumps come in as reviewable PRs:

```yaml
# .github/dependabot.yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
```

Findings appear as inline PR annotations. To also push them to **Security → Code scanning**, add `upload-sarif: true` and grant `security-events: write` to the job.

> [!TIP]
> [Dependabot](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file#package-ecosystem) updates the SHA *and* the trailing version comment together.

## Inputs

| Name | Default | Description |
|---|---|---|
| `version` | `latest` | sisakulint version to install. Pass a tag like `0.3.0` / `v0.3.0`, or `latest` to resolve from the GitHub API. |
| `working-directory` | repo root | Directory to `cd` into before running sisakulint. |
| `args` | `""` | Extra raw args appended to the sisakulint invocation (e.g. `-ignore "missing-timeout-minutes"`). |
| `config-file` | `""` | Path to a sisakulint config file. Passed as `-config-file`. |
| `autofix` | `off` | `off` \| `on` \| `dry-run`. `on` rewrites files in place; pair with a commit step. |
| `fail-on` | `high` | `none` \| `low` \| `medium` \| `high` \| `critical`. Minimum severity that fails the job. |
| `upload-sarif` | `false` | Upload the SARIF result to GitHub Code Scanning. Requires `security-events: write`. |
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

### Block PRs on `critical` only

```yaml
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683            # v4.2.2
        with:
          persist-credentials: false
      - uses: sisaku-security/sisakulint-action@f92185efeaff7ac9a6ed72b6e5d68412ea13ab54  # v1.0.0
        with:
          version: "0.3.0"
          fail-on: critical
          upload-sarif: true
```

### Open an autofix PR

```yaml
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683            # v4.2.2
        with:
          persist-credentials: false
      - uses: sisaku-security/sisakulint-action@f92185efeaff7ac9a6ed72b6e5d68412ea13ab54  # v1.0.0
        with:
          version: "0.3.0"
          autofix: "on"
          fail-on: none                # let autofix run, then commit the diff
          upload-sarif: false
      - uses: peter-evans/create-pull-request@d4f3be6ce6f4083b7ac7490ab98b48a62db1ee41  # v7.0.10
        with:
          branch: sisakulint/autofix
          commit-message: "fix(ci): sisakulint autofix"
          title: "sisakulint autofix"
```

### Local config & ignore rules

```yaml
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683            # v4.2.2
        with:
          persist-credentials: false
      - uses: sisaku-security/sisakulint-action@f92185efeaff7ac9a6ed72b6e5d68412ea13ab54  # v1.0.0
        with:
          version: "0.3.0"
          config-file: .github/sisakulint.yaml
          args: -ignore "some-rule-id"
```

## Permissions

This Action needs

- `contents: read` — to read your workflow files.
- `security-events: write` — only when `upload-sarif: true`, to push SARIF into Code Scanning.

If your repo is in an org without GitHub Advanced Security, Code Scanning isn't available; use `upload-sarif: false` (default) and rely on the inline PR annotations.

## License

[Apache-2.0](./LICENSE), matching upstream [sisakulint](https://github.com/sisaku-security/sisakulint).
