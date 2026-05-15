#!/usr/bin/env python3
"""Apply a fail-on severity gate to a sisakulint SARIF file.

Severity is inferred from:
  1. ruleId suffix (-critical, -high, -medium, -low)
  2. Message text markers like [Medium], (critical), "high:"
Unknown findings default to "low".

Outputs `findings`, `failing-findings`, `sarif-file` to $GITHUB_OUTPUT.
Exits 1 if any finding is at or above the threshold, else 0.
`threshold=none` always exits 0.
"""
import json
import os
import sys

ORDER = {"none": -1, "low": 0, "medium": 1, "high": 2, "critical": 3}
LEVELS = ("critical", "high", "medium", "low")


def classify(rule_id: str, message: str) -> str:
    rid = (rule_id or "").lower()
    msg = (message or "").lower()
    for s in LEVELS:
        if rid.endswith(f"-{s}") or f"[{s}]" in msg or f"({s})" in msg or f" {s}:" in msg:
            return s
    return "low"


def main(path: str, threshold: str) -> int:
    if threshold not in ORDER:
        print(f"::error::invalid threshold: {threshold}", file=sys.stderr)
        return 2
    with open(path) as fh:
        sarif = json.load(fh)
    total = 0
    failing = 0
    thr = ORDER[threshold]
    for run in sarif.get("runs", []):
        for r in run.get("results", []):
            total += 1
            sev = classify(r.get("ruleId"), (r.get("message") or {}).get("text"))
            if threshold != "none" and ORDER[sev] >= thr:
                failing += 1
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"findings={total}\n")
            fh.write(f"failing-findings={failing}\n")
            fh.write(f"sarif-file={path}\n")
    print(f"total={total} failing={failing} threshold={threshold}")
    return 1 if failing > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
