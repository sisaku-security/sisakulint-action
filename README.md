# Setup sisakulint

This action sets up sisakulint CLI tool in your GitHub Actions workflow.

## Usage

```yaml
- uses: sisaku-security/setup-sisakulint@v1
  with:
    sisakulint_version: '0.0.9'
```

## Inputs

- `sisakulint_version` - **Required** Version of sisakulint to install

## Example workflow

```yaml
name: Scan with sisakulint
on: [push]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: sisaku-security/setup-sisakulint@v1
        with:
          sisakulint_version: '0.0.9'
      - run: sisakulint scan
```
