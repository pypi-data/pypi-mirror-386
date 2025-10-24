#!/usr/bin/env python3
"""
Query documentation for AI agents and humans.

Provides multiple search methods:
- Full-text search across all docs
- Tag-based filtering
- Type-based filtering
- Graph traversal (find related docs)

Output: JSON format for machine consumption
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install PyYAML")
    sys.exit(1)


class DocumentationQuery:
    """Query documentation files with multiple search methods."""

    # Directories to search
    DOC_DIRS = ["user-docs", "project-docs", "dev-docs"]

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.docs: Dict[Path, Dict] = {}  # path -> {frontmatter, content}

    def run(self, args: argparse.Namespace) -> None:
        """Execute query based on command-line arguments."""
        # Parse all documentation
        self._parse_all_docs()

        if not self.docs:
            self._output({"error": "No documentation files found", "results": []})
            return

        # Execute query
        if args.topic:
            results = self._search_by_topic(args.topic, args.type)
        elif args.tag:
            results = self._search_by_tags(args.tag, args.type)
        elif args.related:
            results = self._find_related(args.related)
        elif args.type:
            results = self._filter_by_type(args.type)
        else:
            # List all docs
            results = self._list_all()

        self._output({"results": results, "total": len(results)})

    def _parse_all_docs(self) -> None:
        """Parse all markdown files in documentation directories."""
        for doc_dir in self.DOC_DIRS:
            dir_path = self.root_dir / doc_dir
            if not dir_path.exists():
                continue

            for md_file in dir_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    frontmatter = self._parse_frontmatter(content)

                    self.docs[md_file] = {
                        "frontmatter": frontmatter if frontmatter else {},
                        "content": content,
                    }
                except Exception:
                    continue

    def _parse_frontmatter(self, content: str) -> Dict | None:
        """Parse YAML frontmatter from markdown content."""
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return None

        try:
            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                return None
            return frontmatter
        except yaml.YAMLError:
            return None

    def _search_by_topic(self, topic: str, doc_type: str | None = None) -> List[Dict]:
        """Full-text search for topic across all docs."""
        results = []
        topic_lower = topic.lower()

        for doc_path, doc_data in self.docs.items():
            fm = doc_data["frontmatter"]
            content = doc_data["content"]

            # Filter by type if specified
            if doc_type and fm.get("type") != doc_type:
                continue

            # Calculate relevance score
            relevance = 0.0

            # Title match (highest weight)
            if "title" in fm and topic_lower in fm["title"].lower():
                relevance += 1.0

            # Tag match (high weight)
            if "tags" in fm and isinstance(fm["tags"], list):
                if any(topic_lower in tag.lower() for tag in fm["tags"]):
                    relevance += 0.8

            # Content match (lower weight, scaled by frequency)
            content_lower = content.lower()
            matches = content_lower.count(topic_lower)
            if matches > 0:
                # Cap at 0.5 to avoid overwhelming from many mentions
                relevance += min(matches * 0.1, 0.5)

            if relevance > 0:
                results.append(self._format_result(doc_path, fm, relevance))

        # Sort by relevance (descending)
        results.sort(key=lambda x: x["relevance"], reverse=True)

        return results

    def _search_by_tags(self, tags: List[str], doc_type: str | None = None) -> List[Dict]:
        """Search for docs with specific tags."""
        results = []
        tags_lower = [tag.lower() for tag in tags]

        for doc_path, doc_data in self.docs.items():
            fm = doc_data["frontmatter"]

            # Filter by type if specified
            if doc_type and fm.get("type") != doc_type:
                continue

            # Check if doc has matching tags
            if "tags" in fm and isinstance(fm["tags"], list):
                doc_tags_lower = [tag.lower() for tag in fm["tags"}}
                matching_tags = [tag for tag in tags_lower if tag in doc_tags_lower]

                if matching_tags:
                    # Relevance based on % of tags matched
                    relevance = len(matching_tags) / len(tags_lower)
                    results.append(self._format_result(doc_path, fm, relevance))

        # Sort by relevance (descending)
        results.sort(key=lambda x: x["relevance"], reverse=True)

        return results

    def _find_related(self, doc_path_str: str) -> List[Dict]:
        """Find docs related to a specific doc via cross-references."""
        # Resolve the document path
        target_path = (self.root_dir / doc_path_str).resolve()

        if target_path not in self.docs:
            return []

        related_paths: Set[Path] = set()

        # Get direct relations from frontmatter
        fm = self.docs[target_path]["frontmatter"]
        if "related" in fm and isinstance(fm["related"], list):
            for rel_path in fm["related"]:
                # Resolve relative path
                abs_path = (target_path.parent / rel_path).resolve()
                if abs_path in self.docs:
                    related_paths.add(abs_path)

        # Find reverse relations (docs that reference this doc)
        for doc_path, doc_data in self.docs.items():
            if doc_path == target_path:
                continue

            fm_other = doc_data["frontmatter"]
            if "related" in fm_other and isinstance(fm_other["related"], list):
                for rel_path in fm_other["related"]:
                    abs_path = (doc_path.parent / rel_path).resolve()
                    if abs_path == target_path:
                        related_paths.add(doc_path)
                        break

        # Convert to results
        results = []
        for rel_path in related_paths:
            fm_rel = self.docs[rel_path]["frontmatter"]
            results.append(self._format_result(rel_path, fm_rel, 1.0))

        return results

    def _filter_by_type(self, doc_type: str) -> List[Dict]:
        """Filter docs by type (tutorial, how-to, reference, explanation)."""
        results = []

        for doc_path, doc_data in self.docs.items():
            fm = doc_data["frontmatter"]

            if fm.get("type") == doc_type:
                results.append(self._format_result(doc_path, fm, 1.0))

        return results

    def _list_all(self) -> List[Dict]:
        """List all documentation files."""
        results = []

        for doc_path, doc_data in self.docs.items():
            fm = doc_data["frontmatter"]
            results.append(self._format_result(doc_path, fm, 1.0))

        return results

    def _format_result(self, doc_path: Path, frontmatter: Dict, relevance: float) -> Dict:
        """Format a search result as JSON-serializable dict."""
        rel_path = doc_path.relative_to(self.root_dir)

        return {
            "path": str(rel_path),
            "title": frontmatter.get("title", doc_path.name),
            "type": frontmatter.get("type", "unknown"),
            "status": frontmatter.get("status", "unknown"),
            "last_updated": frontmatter.get("last_updated", "unknown"),
            "tags": frontmatter.get("tags", []),
            "audience": frontmatter.get("audience", "all"),
            "relevance": round(relevance, 2),
        }

    def _output(self, data: Dict) -> None:
        """Output results as JSON."""
        print(json.dumps(data, indent=2))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query documentation for AI agents and humans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for topic
  python scripts/query_docs.py --topic authentication

  # Search by tags
  python scripts/query_docs.py --tag api --tag python

  # Find related docs
  python scripts/query_docs.py --related user-docs/tutorials/01-getting-started.md

  # Filter by type
  python scripts/query_docs.py --type how-to

  # Combined: search + filter by type
  python scripts/query_docs.py --topic validation --type reference

Output is JSON format for machine consumption.
        """
    )

    parser.add_argument(
        "--topic",
        type=str,
        help="Full-text search for topic across all docs"
    )

    parser.add_argument(
        "--tag",
        action="append",
        help="Filter by tags (can specify multiple times)"
    )

    parser.add_argument(
        "--type",
        type=str,
        choices=["tutorial", "how-to", "reference", "explanation", "process", "project", "decision"],
        help="Filter by document type"
    )

    parser.add_argument(
        "--related",
        type=str,
        help="Find docs related to specified doc path"
    )

    args = parser.parse_args()

    # Validate: at least one search criterion or list all
    if not any([args.topic, args.tag, args.type, args.related]):
        # List all docs
        pass

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    query = DocumentationQuery(root_dir)
    query.run(args)


if __name__ == "__main__":
    main()
