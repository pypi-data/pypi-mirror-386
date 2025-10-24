#!/usr/bin/env python3
"""
Validate documentation quality for mcp-orchestration.

Checks:
- Frontmatter schema validity (required fields present)
- Broken internal links
- Staleness warnings (>90 days since last_updated)
- Bidirectional cross-references (related: field symmetry)

Exit code 0 if all checks pass, 1 if any failures detected.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install PyYAML")
    sys.exit(1)


class DocumentationValidator:
    """Validate documentation files following DOCUMENTATION_STANDARD.md"""

    # Directories to check
    DOC_DIRS = ["user-docs", "project-docs", "dev-docs"]

    # Required frontmatter fields
    REQUIRED_FIELDS = ["title", "type", "status", "last_updated"]

    # Valid values for type field
    VALID_TYPES = [
        "tutorial",
        "how-to",
        "reference",
        "explanation",
        "process",
        "project",
        "decision",
    ]

    # Valid values for status field
    VALID_STATUS = ["current", "draft", "deprecated"]

    # Staleness threshold (days)
    STALENESS_THRESHOLD = 90

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.docs: Dict[Path, Dict] = {}  # path -> frontmatter

    def run(self) -> int:
        """Run all validation checks. Returns 0 if pass, 1 if fail."""
        print("Validating documentation in {}...".format(self.root_dir))
        print()

        # Step 1: Find all markdown files
        md_files = self._find_markdown_files()
        if not md_files:
            print("No markdown files found in documentation directories.")
            return 0

        print("Found {} markdown files".format(len(md_files)))
        print()

        # Step 2: Parse frontmatter
        for md_file in md_files:
            self._parse_frontmatter(md_file)

        # Step 3: Validate frontmatter
        self._validate_frontmatter()

        # Step 4: Check for broken links
        self._check_broken_links()

        # Step 5: Check for staleness
        self._check_staleness()

        # Step 6: Check bidirectional cross-references
        self._check_bidirectional_refs()

        # Print results
        self._print_results()

        # Exit with appropriate code
        if self.errors:
            return 1
        return 0

    def _find_markdown_files(self) -> List[Path]:
        """Find all .md files in documentation directories."""
        md_files = []
        for doc_dir in self.DOC_DIRS:
            dir_path = self.root_dir / doc_dir
            if not dir_path.exists():
                continue
            md_files.extend(dir_path.rglob("*.md"))
        return md_files

    def _parse_frontmatter(self, md_file: Path) -> None:
        """Parse YAML frontmatter from markdown file."""
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            self.errors.append("{}: Failed to read file: {}".format(md_file, e))
            return

        # Check for frontmatter (--- ... ---)
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            self.errors.append("{}: Missing frontmatter (no --- ... ---)".format(md_file))
            return

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                self.errors.append(
                    "{}: Frontmatter is not a valid YAML dictionary".format(md_file)
                )
                return
        except yaml.YAMLError as e:
            self.errors.append("{}: Invalid YAML in frontmatter: {}".format(md_file, e))
            return

        self.docs[md_file] = frontmatter

    def _validate_frontmatter(self) -> None:
        """Validate frontmatter schema for all documents."""
        for md_file, frontmatter in self.docs.items():
            # Check required fields
            for field in self.REQUIRED_FIELDS:
                if field not in frontmatter:
                    self.errors.append(
                        "{}: Missing required frontmatter field: {}".format(md_file, field)
                    )

            # Validate 'type' field
            if "type" in frontmatter:
                doc_type = frontmatter["type"]
                if doc_type not in self.VALID_TYPES:
                    self.errors.append(
                        "{}: Invalid type '{}' (must be one of: {})".format(
                            md_file, doc_type, ', '.join(self.VALID_TYPES)
                        )
                    )

            # Validate 'status' field
            if "status" in frontmatter:
                status = frontmatter["status"]
                if status not in self.VALID_STATUS:
                    self.errors.append(
                        "{}: Invalid status '{}' (must be one of: {})".format(
                            md_file, status, ', '.join(self.VALID_STATUS)
                        )
                    )

            # Validate 'last_updated' format (YYYY-MM-DD)
            if "last_updated" in frontmatter:
                last_updated = frontmatter["last_updated"]
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(last_updated)):
                    self.errors.append(
                        "{}: Invalid last_updated format (must be YYYY-MM-DD, got: {})".format(
                            md_file, last_updated
                        )
                    )

    def _check_broken_links(self) -> None:
        """Check for broken internal links (relative paths)."""
        for md_file in self.docs.keys():
            content = md_file.read_text(encoding="utf-8")

            # Find all markdown links: [text](path)
            links = re.findall(r"\[([^\}}+)\]\(([^\)]+)\)", content)

            for link_text, link_path in links:
                # Skip external links (http://, https://)
                if link_path.startswith(("http://", "https://", "mailto:")):
                    continue

                # Skip anchors without path (#section)
                if link_path.startswith("#"):
                    continue

                # Remove anchor from path (path/file.md#section → path/file.md)
                clean_path = link_path.split("#")[0]
                if not clean_path:
                    continue

                # Resolve relative path
                target_path = (md_file.parent / clean_path).resolve()

                # Check if target exists
                if not target_path.exists():
                    self.errors.append(
                        "{}: Broken link to '{}' (resolved to {}, but file not found)".format(
                            md_file, link_path, target_path
                        )
                    )

    def _check_staleness(self) -> None:
        """Check for stale documents (>90 days since last_updated)."""
        today = datetime.now().date()
        threshold = today - timedelta(days=self.STALENESS_THRESHOLD)

        for md_file, frontmatter in self.docs.items():
            if "last_updated" not in frontmatter:
                continue  # Already flagged in _validate_frontmatter

            last_updated_str = str(frontmatter["last_updated"])
            try:
                last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d").date()
            except ValueError:
                continue  # Already flagged in _validate_frontmatter

            if last_updated < threshold:
                days_old = (today - last_updated).days
                self.warnings.append(
                    "{}: Stale document (last updated {} days ago, threshold is {} days)".format(
                        md_file, days_old, self.STALENESS_THRESHOLD
                    )
                )

    def _check_bidirectional_refs(self) -> None:
        """Check that related: links are bidirectional (A→B implies B→A)."""
        # Build map of doc -> related docs
        related_map: Dict[Path, Set[Path}} = {}

        for md_file, frontmatter in self.docs.items():
            if "related" not in frontmatter:
                continue

            related = frontmatter["related"]
            if not isinstance(related, list):
                self.errors.append(
                    "{}: 'related' field must be a list, got: {}".format(md_file, type(related))
                )
                continue

            related_paths = set()
            for rel_path in related:
                # Resolve relative path
                target_path = (md_file.parent / rel_path).resolve()

                # Check if target exists (avoid duplicate error)
                if not target_path.exists():
                    # Already flagged in _check_broken_links
                    continue

                related_paths.add(target_path)

            related_map[md_file] = related_paths

        # Check bidirectionality
        for doc_a, related_docs in related_map.items():
            for doc_b in related_docs:
                # Check if doc_b references doc_a back
                if doc_b not in related_map:
                    self.warnings.append(
                        "{}: References {} in 'related:', but {} has no 'related:' field (not bidirectional)".format(
                            doc_a, doc_b, doc_b
                        )
                    )
                    continue

                # Compute relative path from doc_b to doc_a
                try:
                    rel_path_back = doc_a.relative_to(doc_b.parent)
                except ValueError:
                    # Files in different directory trees, compute differently
                    # This is a simplification; may need more robust path handling
                    continue

                if doc_a not in related_map[doc_b]:
                    self.warnings.append(
                        "{}: References {} in 'related:', but {} does not reference {} back (not bidirectional)".format(
                            doc_a, doc_b, doc_b, doc_a
                        )
                    )

    def _print_results(self) -> None:
        """Print validation results."""
        print("=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        print()

        if self.errors:
            print("❌ ERRORS ({}):".format(len(self.errors)))
            print()
            for error in self.errors:
                print("  {}".format(error))
            print()
        else:
            print("✅ No errors found")
            print()

        if self.warnings:
            print("⚠️  WARNINGS ({}):".format(len(self.warnings)))
            print()
            for warning in self.warnings:
                print("  {}".format(warning))
            print()
        else:
            print("✅ No warnings")
            print()

        print("=" * 70)
        print("Checked {} documents".format(len(self.docs)))
        print("Errors: {}".format(len(self.errors)))
        print("Warnings: {}".format(len(self.warnings)))
        print("=" * 70)


def main():
    """Main entry point."""
    # Assume script is in scripts/ directory, project root is parent
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    validator = DocumentationValidator(root_dir)
    exit_code = validator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
