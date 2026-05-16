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
      - uses: sisaku-security/sisakulint-action@596af4ab15e8c5b232c74aa97525a0302e7b7af4  # v1.0.0
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
| `version` | `0.3.0` | sisakulint release tag to install. Pinned to the version this Action release was tested against. Override to roll forward (e.g. `0.4.0`). |
| `working-directory` | repo root | Directory to `cd` into before running sisakulint. |
| `args` | `""` | Extra raw args appended to the sisakulint invocation (e.g. `-ignore "missing-timeout-minutes"`). |
| `config-file` | `""` | Path to a sisakulint config file. Passed as `-config-file`. |
| `autofix` | `off` | `off` \| `on` \| `dry-run`. `on` rewrites files in place; pair with a commit step. |
| `fail-on` | `high` | `none` \| `low` \| `medium` \| `high` \| `critical`. Minimum severity that fails the job. |
| `upload-sarif` | `false` | Upload the SARIF result to GitHub Code Scanning. Requires `security-events: write`. |
| `sarif-file` | `sisakulint.sarif` | Path the SARIF report is written to. |

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
      - uses: sisaku-security/sisakulint-action@596af4ab15e8c5b232c74aa97525a0302e7b7af4  # v1.0.0
        with:
          fail-on: critical
          upload-sarif: true
```

### Open an autofix PR

```yaml
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683            # v4.2.2
        with:
          persist-credentials: false
      - uses: sisaku-security/sisakulint-action@596af4ab15e8c5b232c74aa97525a0302e7b7af4  # v1.0.0
        with:
          autofix: "on"
          fail-on: none
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
      - uses: sisaku-security/sisakulint-action@596af4ab15e8c5b232c74aa97525a0302e7b7af4  # v1.0.0
        with:
          config-file: .github/sisakulint.yaml
          args: -ignore "some-rule-id"
```

## Org-wide rollout (reusable workflow)

For centralized policy across many repositories, this repo also ships a
[reusable workflow](https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations)
at [`.github/workflows/scan.yml`](./.github/workflows/scan.yml). It wraps the
composite action with the same inputs and outputs, and is meant to be called
from other repos so you only have to upgrade one SHA per release.

### 1. Call it from any repo

```yaml
# .github/workflows/sisakulint.yml
name: sisakulint
on:
  pull_request:
    paths: [".github/workflows/**"]
  push:
    branches: ["main"]
    paths: [".github/workflows/**"]
permissions:
  contents: read
  security-events: write
jobs:
  scan:
    uses: sisaku-security/sisakulint-action/.github/workflows/scan.yml@596af4ab15e8c5b232c74aa97525a0302e7b7af4  # v1.0.0
    with:
      fail-on: critical
      upload-sarif: true
```

A copy-paste ready version lives at [`examples/caller.yml`](./examples/caller.yml).

### 2. Enforce it org-wide via a ruleset

To make sisakulint a [required workflow](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-workflows-to-pass-before-merging)
on every PR across an organization, create a branch ruleset with a `workflows`
rule pointing at this repo:

```bash
ORG=your-org
REPO_ID=$(gh api /repos/sisaku-security/sisakulint-action --jq .id)

jq --argjson rid "$REPO_ID" \
  '.rules[0].parameters.workflows[0].repository_id = $rid' \
  examples/org-required-ruleset.json \
  | gh api -X POST "/orgs/$ORG/rulesets" --input -
```

The ruleset template is at [`examples/org-required-ruleset.json`](./examples/org-required-ruleset.json).
By default it targets `~DEFAULT_BRANCH` on `~ALL` repos with branch protection
eligibility — adjust `conditions.repository_name` (or use `repository_property`
conditions) to scope it to a subset.

### 3. Or distribute via the org `.github` repo as a template

Drop [`examples/caller.yml`](./examples/caller.yml) into
`<org>/.github/workflow-templates/` together with a `sisakulint.properties.json`
to surface it in every repo's "New workflow" picker. Useful when you want
opt-in adoption rather than mandatory enforcement.

## Permissions

This Action needs

- `contents: read` — to read your workflow files.
- `security-events: write` — only when `upload-sarif: true`, to push SARIF into Code Scanning.

If your repo is in an org without GitHub Advanced Security, Code Scanning isn't available; use `upload-sarif: false` (default) and rely on the inline PR annotations.

## License

[Apache-2.0](./LICENSE), matching upstream [sisakulint](https://github.com/sisaku-security/sisakulint).
