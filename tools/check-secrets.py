#!/usr/bin/env python3
"""Focused secret check. Never emit matched lines or credential values."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

RULES = {
    "private-key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "common credential token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})"),
    "sensitive assignment": re.compile(r"(?i)(?:access[_-]?key|secret[_-]?key|api[_-]?key|password|client[_-]?secret|(?:auth|access|refresh)[_-]?token)[\x22\x27]?\s*[=:]\s*[\x22\x27]?([A-Za-z0-9_+./=-]{16,})(?![A-Za-z0-9_+./=-])"),
}


def findings(data):
    # Decode only for scanning; undecodable bytes must not hide an ASCII secret.
    for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
        for rule, pattern in RULES.items():
            if pattern.search(line):
                yield number, rule


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true", help="check the full Git index")
    args = parser.parse_args()
    root = Path(git("rev-parse", "--show-toplevel").decode().strip())
    import os
    os.chdir(root)
    names = git("ls-files", "-z", "--cached", *([] if args.staged else ["--others", "--exclude-standard"]))
    failed = False
    for name in sorted(set(names.decode("utf-8", errors="surrogateescape").split("\0"))):
        if not name:
            continue
        path = root / name
        if args.staged:
            # Submodule entries have no file blob to scan in this repository.
            entry = git("ls-files", "--stage", "--", name).split(b" ", 1)[0]
            if entry == b"160000":
                continue
            data = git("show", ":" + name)
        else:
            if not path.is_file() or path.is_symlink():
                continue
            data = path.read_bytes()
        for line, rule in findings(data):
            print(f"{name}:{line}: {rule} [REDACTED]")
            failed = True
    if failed:
        print("Secret check failed. Remove credentials before committing.", file=sys.stderr)
        return 1
    print("Focused secret check passed. Git history was not scanned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
