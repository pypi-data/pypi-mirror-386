#!/usr/bin/env python3
"""
Generate DOCUMENTATION_MAP.md from frontmatter in documentation files.

Parses all .md files in user-docs/, project-docs/, dev-docs/ and creates
a comprehensive index organized by:
- Directory (user-docs, project-docs, dev-docs)
- Document type (tutorial, how-to, reference, explanation, etc.)
- Audience, tags, status

Output: DOCUMENTATION_MAP.md in project root
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install PyYAML")
    sys.exit(1)


class DocumentationMapGenerator:
    """Generate DOCUMENTATION_MAP.md from frontmatter."""

    # Directories to scan
    DOC_DIRS = ["user-docs", "project-docs", "dev-docs"]

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.docs: Dict[Path, Dict] = {}  # path -> frontmatter

    def run(self) -> None:
        """Generate DOCUMENTATION_MAP.md."""
        print("Generating DOCUMENTATION_MAP.md for {}...".format(self.root_dir))

        # Step 1: Find and parse all markdown files
        self._parse_all_docs()

        if not self.docs:
            print("No markdown files found. Skipping DOCUMENTATION_MAP.md generation.")
            return

        print("Found {} markdown files".format(len(self.docs)))

        # Step 2: Generate markdown content
        content = self._generate_markdown()

        # Step 3: Write to DOCUMENTATION_MAP.md
        output_path = self.root_dir / "DOCUMENTATION_MAP.md"
        output_path.write_text(content, encoding="utf-8")

        print("✅ Generated {}".format(output_path))

    def _parse_all_docs(self) -> None:
        """Parse frontmatter from all markdown files in doc directories."""
        for doc_dir in self.DOC_DIRS:
            dir_path = self.root_dir / doc_dir
            if not dir_path.exists():
                continue

            for md_file in dir_path.rglob("*.md"):
                self._parse_frontmatter(md_file)

    def _parse_frontmatter(self, md_file: Path) -> None:
        """Parse YAML frontmatter from markdown file."""
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            return  # Skip unreadable files

        # Check for frontmatter (--- ... ---)
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return  # Skip files without frontmatter

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                return
        except yaml.YAMLError:
            return  # Skip invalid YAML

        self.docs[md_file] = frontmatter

    def _generate_markdown(self) -> str:
        """Generate markdown content for DOCUMENTATION_MAP.md."""
        lines = []

        # Header
        lines.append("# Documentation Map")
        lines.append("")
        lines.append("**Generated:** {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append("**Total Documents:** {}".format(len(self.docs)))
        lines.append("")
        lines.append("This file is auto-generated from frontmatter in documentation files.")
        lines.append("Do not edit manually - run `python scripts/generate_docs_map.py` to regenerate.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        lines.append("- [By Directory](#by-directory)")
        lines.append("  - [User Documentation](#user-documentation)")
        lines.append("  - [Project Documentation](#project-documentation)")
        lines.append("  - [Developer Documentation](#developer-documentation)")
        lines.append("- [By Document Type](#by-document-type)")
        lines.append("- [By Status](#by-status)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Section 1: By Directory
        lines.append("## By Directory")
        lines.append("")

        for doc_dir in self.DOC_DIRS:
            dir_docs = [
                (path, fm)
                for path, fm in self.docs.items()
                if str(path).startswith(doc_dir)
            ]

            if not dir_docs:
                continue

            # Section title
            dir_title = {
                "user-docs": "User Documentation",
                "project-docs": "Project Documentation",
                "dev-docs": "Developer Documentation",
            }.get(doc_dir, doc_dir)

            lines.append("### {}".format(dir_title))
            lines.append("")
            lines.append("**Location:** `{}/`".format(doc_dir))
            lines.append("**Count:** {} documents".format(len(dir_docs)))
            lines.append("")

            # Table
            lines.append("| Document | Type | Status | Last Updated |")
            lines.append("|----------|------|--------|--------------|")

            for path, fm in sorted(dir_docs, key=lambda x: str(x[0])):
                rel_path = path.relative_to(self.root_dir)
                title = fm.get("title", path.name)
                doc_type = fm.get("type", "unknown")
                status = fm.get("status", "unknown")
                last_updated = fm.get("last_updated", "unknown")

                lines.append("| [{}]({}) | {} | {} | {} |".format(title, rel_path, doc_type, status, last_updated))

            lines.append("")

        # Section 2: By Document Type
        lines.append("## By Document Type")
        lines.append("")

        # Group by type
        by_type: Dict[str, List] = {}
        for path, fm in self.docs.items():
            doc_type = fm.get("type", "unknown")
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append((path, fm))

        for doc_type in sorted(by_type.keys()):
            docs_of_type = by_type[doc_type]
            lines.append("### {}".format(doc_type.title()))
            lines.append("")
            lines.append("**Count:** {} documents".format(len(docs_of_type)))
            lines.append("")

            # Table
            lines.append("| Document | Location | Status | Last Updated |")
            lines.append("|----------|----------|--------|--------------|")

            for path, fm in sorted(docs_of_type, key=lambda x: str(x[0])):
                rel_path = path.relative_to(self.root_dir)
                title = fm.get("title", path.name)
                location = str(rel_path.parent)
                status = fm.get("status", "unknown")
                last_updated = fm.get("last_updated", "unknown")

                lines.append("| [{}]({}) | {} | {} | {} |".format(title, rel_path, location, status, last_updated))

            lines.append("")

        # Section 3: By Status
        lines.append("## By Status")
        lines.append("")

        # Group by status
        by_status: Dict[str, List] = {}
        for path, fm in self.docs.items():
            status = fm.get("status", "unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append((path, fm))

        for status in sorted(by_status.keys()):
            docs_with_status = by_status[status]
            status_emoji = {"current": "✅", "draft": "🚧", "deprecated": "⚠️"}.get(
                status, "❓"
            )
            lines.append("### {} {}".format(status_emoji, status.title()))
            lines.append("")
            lines.append("**Count:** {} documents".format(len(docs_with_status)))
            lines.append("")

            # Table
            lines.append("| Document | Type | Location | Last Updated |")
            lines.append("|----------|------|----------|--------------|")

            for path, fm in sorted(docs_with_status, key=lambda x: str(x[0])):
                rel_path = path.relative_to(self.root_dir)
                title = fm.get("title", path.name)
                doc_type = fm.get("type", "unknown")
                location = str(rel_path.parent)
                last_updated = fm.get("last_updated", "unknown")

                lines.append("| [{}]({}) | {} | {} | {} |".format(title, rel_path, doc_type, location, last_updated))

            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("**Note:** This file is automatically generated. ")
        lines.append("To update, run: `python scripts/generate_docs_map.py`")
        lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point."""
    # Assume script is in scripts/ directory, project root is parent
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    generator = DocumentationMapGenerator(root_dir)
    generator.run()


if __name__ == "__main__":
    main()
