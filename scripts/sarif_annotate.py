#!/usr/bin/env python3
"""Emit ::error / ::warning GitHub Actions annotations from a sisakulint SARIF file."""
import json
import sys


def main(path: str) -> int:
    with open(path) as fh:
        sarif = json.load(fh)
    for run in sarif.get("runs", []):
        for r in run.get("results", []):
            rid = r.get("ruleId", "")
            msg = (r.get("message") or {}).get("text", "").replace("\n", " ")
            loc = (r.get("locations") or [{}])[0].get("physicalLocation", {})
            f = (loc.get("artifactLocation") or {}).get("uri", "")
            reg = loc.get("region") or {}
            line = reg.get("startLine", 1)
            col = reg.get("startColumn", 1)
            lvl = "error" if any(rid.endswith(s) for s in ("-critical", "-high")) else "warning"
            print(f"::{lvl} file={f},line={line},col={col},title=sisakulint[{rid}]::{msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
