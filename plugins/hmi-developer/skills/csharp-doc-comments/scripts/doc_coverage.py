#!/usr/bin/env python3
"""XML-doc coverage triage for C# sources.

Lists public/protected type and member declarations that lack an immediately
preceding /// documentation comment. Output is a CANDIDATE list for an agent
to verify against source, not ground truth.

Usage:
    python doc_coverage.py <file-or-directory> [--stats] [--exclude SUBSTR ...]

Output lines:  <path>:<line>: <kind> <name>
Exit codes:    0 = no candidates, 1 = candidates found, 2 = usage/IO error.

Known limitations (by design, keep the tool dependency-free and fast):
- Interface members declared without an access modifier are not scanned
  (implicitly public); scan the interface type itself instead.
- Enum members are not scanned (the enum type is).
- Text inside strings or #if-disabled blocks can rarely produce false
  positives; the consuming agent must verify every candidate in source.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Directories never containing hand-written public API surface.
SKIP_DIRS = {"bin", "obj", ".git", ".vs", "packages", "TestResults", "node_modules"}

# Generated / infrastructure files: documenting them is noise.
SKIP_FILE_SUFFIXES = (".g.cs", ".g.i.cs", ".Designer.cs", ".generated.cs")
SKIP_FILE_NAMES = {"GlobalUsings.cs", "AssemblyInfo.cs"}

# Only these access levels are part of the documented contract (SA1600 scope
# used by the skill: public + protected; private/internal are judgment calls).
ACCESS_RE = re.compile(r"^\s*(?:public|protected(?:\s+internal)?)\s")
PRIVATE_RE = re.compile(r"^\s*private\s")  # excludes 'private protected'

MODIFIERS = {
    "static", "virtual", "override", "sealed", "abstract", "async",
    "readonly", "partial", "new", "unsafe", "extern", "required",
    "volatile", "ref",
}
TYPE_KEYWORDS = {"class", "interface", "struct", "enum", "delegate"}

IDENT = r"[A-Za-z_@][A-Za-z0-9_]*"
METHOD_NAME_RE = re.compile(rf"({IDENT})\s*(?:<[^()=]*?>)?\s*\(")
GENERIC_STRIP_RE = re.compile(r"<[^<>]*>")


def leading_doc_present(lines: list[str], decl_index: int) -> bool:
    """True when a /// run directly precedes the declaration.

    Attributes ([...]), blank lines, and preprocessor lines (#region etc.)
    may legally sit between the doc comment and the declaration.
    """
    i = decl_index - 1
    while i >= 0:
        text = lines[i].strip()
        if text.startswith("///"):
            return True
        if text == "" or text.startswith("[") or text.startswith("#"):
            i -= 1
            continue
        # Continuation of a multi-line attribute argument list.
        if text.endswith("]") and "[" not in text:
            i -= 1
            continue
        return False
    return False


def classify(rest_tokens: list[str], line: str, current_type: str | None):
    """Return (kind, name) for the declaration or None when unclassifiable."""
    tokens = [t for t in rest_tokens if t not in MODIFIERS]
    if not tokens:
        return None

    head = tokens[0]
    if head == "record":
        # record / record class / record struct
        idx = 2 if len(tokens) > 1 and tokens[1] in ("class", "struct") else 1
        if len(tokens) > idx - 0 and len(tokens) > idx:
            return "record", GENERIC_STRIP_RE.sub("", tokens[idx]).strip(":({")
        return None
    if head in TYPE_KEYWORDS:
        if len(tokens) > 1:
            return head, GENERIC_STRIP_RE.sub("", tokens[1]).strip(":({;")
        return None
    if head == "event":
        # event EventHandler<T> Name;   -> last identifier before ; or =
        tail = line.split("event", 1)[1]
        tail = tail.split("=")[0].split(";")[0].strip()
        name = tail.split()[-1] if tail.split() else "?"
        return "event", GENERIC_STRIP_RE.sub("", name)
    if " operator " in line or line.rstrip().endswith("operator"):
        after = line.split("operator", 1)[1].strip()
        symbol = after.split("(")[0].strip()
        return "operator", f"operator {symbol}"

    if "(" in line:
        matches = METHOD_NAME_RE.findall(line.split("=>")[0])
        if matches:
            name = matches[-1] if matches[-1] not in ("if", "switch", "while", "nameof") else matches[0]
            kind = "constructor" if current_type and name == current_type else "method"
            return kind, name
        return None

    # No parentheses: property (has body/expression) or field.
    code = line.split("//")[0].rstrip()
    if "{" in code or "=>" in code:
        before = code.split("{")[0].split("=>")[0].rstrip()
        parts = before.split()
        return ("property", GENERIC_STRIP_RE.sub("", parts[-1])) if parts else None
    if code.endswith(";") or "=" in code:
        before = code.split("=")[0].rstrip().rstrip(";")
        parts = before.split()
        return ("field", GENERIC_STRIP_RE.sub("", parts[-1])) if parts else None
    # Bare declaration line (no body token, no terminator): the accessor block
    # opens on a following line -> property or indexer.
    parts = code.split()
    if len(parts) >= 2:
        name = parts[-1]
        if name.startswith("this["):
            return "indexer", "this[]"
        return "property", GENERIC_STRIP_RE.sub("", name)
    return None


def scan_file(path: Path):
    """Yield (line_number, kind, name, documented) per declaration found."""
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return

    current_type: str | None = None
    in_block_comment = False
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            in_block_comment = "*/" not in stripped
            continue
        if stripped.startswith("//"):
            continue
        if PRIVATE_RE.match(raw) or not ACCESS_RE.match(raw):
            continue

        rest = ACCESS_RE.sub("", raw, count=1).strip()
        result = classify(rest.split(), raw, current_type)
        if result is None:
            continue
        kind, name = result
        if kind in TYPE_KEYWORDS or kind == "record":
            current_type = name
        yield index + 1, kind, name, leading_doc_present(lines, index)


def collect_files(root: Path, excludes: list[str]):
    if root.is_file():
        return [root] if root.suffix == ".cs" else []
    files = []
    for path in sorted(root.rglob("*.cs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILE_NAMES or path.name.endswith(SKIP_FILE_SUFFIXES):
            continue
        posix = path.as_posix()
        if any(substring in posix for substring in excludes):
            continue
        files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", help=".cs file or directory to scan")
    parser.add_argument("--stats", action="store_true", help="print coverage summary")
    parser.add_argument("--exclude", action="append", default=[], metavar="SUBSTR",
                        help="skip paths containing SUBSTR (repeatable), e.g. --exclude Tests")
    args = parser.parse_args()

    root = Path(args.target)
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    files = collect_files(root, args.exclude)
    if not files:
        print(f"error: no .cs files under {root}", file=sys.stderr)
        return 2

    total = documented = 0
    candidates = []
    for path in files:
        rel = path.relative_to(root) if root.is_dir() else path.name
        for line_no, kind, name, has_doc in scan_file(path):
            total += 1
            if has_doc:
                documented += 1
            else:
                candidates.append(f"{rel}:{line_no}: {kind} {name}")

    for entry in candidates:
        print(entry)
    if args.stats:
        pct = (documented / total * 100) if total else 100.0
        print(f"\nfiles: {len(files)}  declarations: {total}  "
              f"documented: {documented}  undocumented: {len(candidates)}  "
              f"coverage: {pct:.1f}%")
    return 1 if candidates else 0


if __name__ == "__main__":
    sys.exit(main())
