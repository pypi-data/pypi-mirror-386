#!/usr/bin/env python3
# @CODE:HOOK-BASH-001 | SPEC: TBD | TEST: tests/hooks/test_bash_validation.py
# Bash command validator (from Context7 official docs)
import json
import re
import sys

BLOCKED = [
    (r"rm\s+-rf\s+/", "Blocking rm -rf /"),
    (r"sudo\s+rm", "Blocking sudo rm"),
    (r">\s*/etc/\w+", "Blocking writes to /etc"),
    (r"curl.*\|\s*bash", "Blocking curl | bash"),
]

try:
    data = json.load(sys.stdin)
    cmd = data.get("tool_input", {}).get("command", "")
    for pattern, msg in BLOCKED:
        if re.search(pattern, cmd):
            print(f"🔴 {msg}", file=sys.stderr)
            sys.exit(2)
    sys.exit(0)
except Exception:
    sys.exit(0)
