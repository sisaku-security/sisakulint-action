#!/usr/bin/env python3
"""Fail CI when action.yml, .github/workflows/scan.yml, or README.md drift.

Checks:
  1. action.yml inputs ⇔ scan.yml inputs   (names + default values)
  2. action.yml outputs ⇔ scan.yml outputs (names)
  3. action.yml inputs ⇔ README ## Inputs  (names only — defaults rendered as prose)
  4. action.yml outputs ⇔ README ## Outputs(names)

Intentional divergences (allowlisted):
  - scan.yml may declare `runs-on` (no counterpart in composite action).
  - `upload-sarif` is a boolean in scan.yml and a string in action.yml.
  - Input `description:` strings are NOT compared (action.yml is the source of
    truth for UI hints; scan.yml descriptions are allowed to summarize).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ACTION = ROOT / "action.yml"
REUSABLE = ROOT / ".github/workflows/scan.yml"
README = ROOT / "README.md"

REUSABLE_ONLY_INPUTS = {"runs-on"}


def _norm_default(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v) if v is not None else ""


def composite_inputs(doc: dict) -> dict[str, str]:
    return {k: _norm_default(v.get("default")) for k, v in (doc.get("inputs") or {}).items()}


def composite_outputs(doc: dict) -> set[str]:
    return set((doc.get("outputs") or {}).keys())


def reusable_inputs(doc: dict) -> dict[str, str]:
    wc = (doc.get(True) or doc.get("on") or {}).get("workflow_call") or {}
    inputs = wc.get("inputs") or {}
    return {
        k: _norm_default(v.get("default"))
        for k, v in inputs.items()
        if k not in REUSABLE_ONLY_INPUTS
    }


def reusable_outputs(doc: dict) -> set[str]:
    wc = (doc.get(True) or doc.get("on") or {}).get("workflow_call") or {}
    return set((wc.get("outputs") or {}).keys())


def readme_section(text: str, title: str) -> str:
    m = re.search(
        rf"^## {re.escape(title)}\s*\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not m:
        sys.exit(f"README.md: '## {title}' section not found")
    return m.group(1)


def readme_row_names(section: str) -> set[str]:
    names: set[str] = set()
    for line in section.splitlines():
        m = re.match(r"\|\s*`([^`]+)`\s*\|", line)
        if m:
            names.add(m.group(1))
    return names


def main() -> int:
    action = yaml.safe_load(ACTION.read_text())
    reusable = yaml.safe_load(REUSABLE.read_text())
    readme_text = README.read_text()

    a_in = composite_inputs(action)
    r_in = reusable_inputs(reusable)
    a_out = composite_outputs(action)
    r_out = reusable_outputs(reusable)
    md_in = readme_row_names(readme_section(readme_text, "Inputs"))
    md_out = readme_row_names(readme_section(readme_text, "Outputs"))

    errs: list[str] = []

    only_a = set(a_in) - set(r_in)
    only_r = set(r_in) - set(a_in)
    if only_a:
        errs.append(f"scan.yml missing inputs: {sorted(only_a)}")
    if only_r:
        errs.append(f"scan.yml has unknown inputs: {sorted(only_r)} (allowlist via REUSABLE_ONLY_INPUTS)")

    for k in sorted(set(a_in) & set(r_in)):
        if a_in[k] != r_in[k]:
            errs.append(f"input {k!r} default drift: action.yml={a_in[k]!r} scan.yml={r_in[k]!r}")

    if a_out != r_out:
        errs.append(f"output keys drift: action.yml={sorted(a_out)} scan.yml={sorted(r_out)}")

    if md_in != set(a_in):
        only_md = md_in - set(a_in)
        only_action = set(a_in) - md_in
        if only_md:
            errs.append(f"README ## Inputs has rows not in action.yml: {sorted(only_md)}")
        if only_action:
            errs.append(f"README ## Inputs missing rows for: {sorted(only_action)}")

    if md_out != a_out:
        only_md = md_out - a_out
        only_action = a_out - md_out
        if only_md:
            errs.append(f"README ## Outputs has rows not in action.yml: {sorted(only_md)}")
        if only_action:
            errs.append(f"README ## Outputs missing rows for: {sorted(only_action)}")

    if errs:
        print("Drift detected:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK: {len(a_in)} inputs, {len(a_out)} outputs are consistent across action.yml, scan.yml, README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
