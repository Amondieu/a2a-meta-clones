"""scripts/check_no_legacy_slug.py — token-aware legacy-slug static check.

The catalog write boundary and the v1 PATCH identity split
require that the bare string `agent-fabric` (without suffix)
MUST NOT appear in customer-facing positions:
  - catalog dict key
  - MCP server ID
  - URL path segment /agent-fabric/
  - Stripe metadata public_slug
  - exact scalar value (in JSON / YAML / Python literal)

The check is token-aware, NOT substring-grep:
  - canonical slugs `agent-fabric-oversight` and
    `agent-fabric-threat-model` are ALLOWED everywhere
  - the bare form `agent-fabric` is REJECTED in the
    customer-facing positions above
  - the same string is ALLOWED in:
    - source filenames (clone_specs/agent-fabric.json)
    - legacy_source_spec_name fields
    - documentation
    - log output

The 4 backlog slugs (agent-catalog, agent-vault,
audit-workbench, policy-hub) follow the same rule.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The 5 legacy identifiers to check
LEGACY_SLUGS = [
    "agent-fabric",       # the bare form
    "agent-catalog",
    "agent-vault",
    "audit-workbench",
    "policy-hub",
]

# Files / paths where the legacy slug is allowed (raw substring)
ALLOWED_PATH_PATTERNS = [
    re.compile(r"clone_specs/.*\.json$"),
    re.compile(r"server_manifests/.*"),
    re.compile(r"docs/.*"),
    re.compile(r"README\.md$"),
    re.compile(r".*\.md$"),  # any markdown doc
    re.compile(r".*LICENSE.*"),
]

# File extensions that are text and should be checked for content
TEXT_EXTENSIONS = {".py", ".json", ".yml", ".yaml", ".md", ".txt", ".toml", ".cfg", ".ini", ".sh", ".ps1", ".tsv", ".csv", ".html", ".css", ".js"}

# Path prefixes to skip entirely
SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    ".cursor",
    ".claude",
    ".minimax",
    "tests/fixtures",
}

# Files that DEFINITIONALLY contain the legacy slugs:
#   - the check file itself (lists the slugs to check)
#   - the vendored catalog snapshot (read-only A2A-Meta source)
#   - the vendored clone specs (read-only PromptGenerator source)
#   - the vendored server manifests (read-only PromptGenerator source)
#   - the pipeline.py metadata dict (overrides dict for legacy name lookup)
#   - test files that assert against the legacy names
# These are NOT customer-facing; the check excludes them.
EXEMPT_FILES = {
    "scripts/check_no_legacy_slug.py",
    "services/shared/catalog_client/catalog_snapshot.py",
    "scripts/pipeline.py",
}


def is_allowed_path(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    for pat in ALLOWED_PATH_PATTERNS:
        if pat.search(rel):
            return True
    return False


def find_legacy_slug(text: str, slug: str) -> List[Tuple[int, str]]:
    """Find all positions in `text` where the exact bare `slug`
    appears (not as a prefix of `slug-oversight` etc.)."""
    violations = []
    # Use word boundary. For hyphenated slugs, the boundary
    # is the hyphen or a non-word char.
    pattern = re.compile(r"(?<![-a-zA-Z])" + re.escape(slug) + r"(?![-a-zA-Z])")
    for m in pattern.finditer(text):
        # Get the line text
        start = text.rfind("\n", 0, m.start()) + 1
        end = text.find("\n", m.end())
        if end == -1:
            end = len(text)
        line = text[start:end].strip()
        line_no = text[: m.start()].count("\n") + 1
        violations.append((line_no, line))
    return violations


def check_file(path: Path) -> List[Tuple[str, int, str]]:
    """Check one file. Return list of (slug, line_no, line_text)."""
    if not path.is_file():
        return []
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return []
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in EXEMPT_FILES:
        return []
    if is_allowed_path(path):
        return []
    # Also skip test files (they assert against the legacy names)
    if rel.startswith("tests/"):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    violations = []
    for slug in LEGACY_SLUGS:
        for line_no, line in find_legacy_slug(text, slug):
            violations.append((slug, line_no, line))
    return violations


def main() -> int:
    violations: List[Tuple[Path, str, int, str]] = []
    files_checked = 0
    for path in REPO_ROOT.rglob("*"):
        rel_parts = path.relative_to(REPO_ROOT).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        files_checked += 1
        for slug, line_no, line in check_file(path):
            violations.append((path, slug, line_no, line))

    if violations:
        print(f"FAIL: {len(violations)} legacy-slug violation(s) in {files_checked} files:")
        for path, slug, line_no, line in violations:
            rel = path.relative_to(REPO_ROOT)
            print(f"  {rel}:{line_no}  slug={slug!r}  line={line!r}")
        return 1
    print(f"OK: 0 violations in {files_checked} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
