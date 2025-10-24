#!/usr/bin/env python3
"""
Generate documentation metrics and health report.

Analyzes all documentation files to provide insights on:
- Coverage (% of code modules with corresponding docs)
- Health (staleness ratio, broken links, frontmatter completeness)
- Activity (docs updated in last 30/60/90 days)
- Quality (cross-reference density, test extraction usage)

Output: DOCUMENTATION_METRICS.md
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install PyYAML")
    sys.exit(1)


class DocumentationMetrics:
    """Generate comprehensive documentation metrics."""

    # Directories to analyze
    DOC_DIRS = ["user-docs", "project-docs", "dev-docs"]
    CODE_DIRS = ["src"]

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.docs: Dict[Path, Dict] = {}  # path -> frontmatter
        self.code_files: List[Path] = []
        self.metrics: Dict[str, any] = {}

    def run(self) -> None:
        """Generate metrics and create DOCUMENTATION_METRICS.md."""
        print("Analyzing documentation metrics for {}...".format(self.root_dir))
        print()

        # Step 1: Parse all documentation
        self._parse_all_docs()

        if not self.docs:
            print("No documentation files found.")
            return

        # Step 2: Find all code files
        self._find_code_files()

        # Step 3: Calculate metrics
        self._calculate_coverage()
        self._calculate_health()
        self._calculate_activity()
        self._calculate_quality()

        # Step 4: Generate report
        self._generate_report()

    def _parse_all_docs(self) -> None:
        """Parse all markdown files in documentation directories."""
        for doc_dir in self.DOC_DIRS:
            dir_path = self.root_dir / doc_dir
            if not dir_path.exists():
                continue

            for md_file in dir_path.rglob("*.md"):
                frontmatter = self._parse_frontmatter(md_file)
                if frontmatter:
                    self.docs[md_file] = frontmatter

        print("Found {} documentation files".format(len(self.docs)))

    def _parse_frontmatter(self, md_file: Path) -> Dict | None:
        """Parse YAML frontmatter from markdown file."""
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            return None

        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return {}  # No frontmatter, but still count as doc

        try:
            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                return {}
            return frontmatter
        except yaml.YAMLError:
            return {}

    def _find_code_files(self) -> None:
        """Find all Python code files."""
        for code_dir in self.CODE_DIRS:
            dir_path = self.root_dir / code_dir
            if not dir_path.exists():
                continue

            self.code_files.extend(dir_path.rglob("*.py"))

        # Exclude __init__.py and test files
        self.code_files = [
            f for f in self.code_files
            if f.name != "__init__.py" and not f.name.startswith("test_")
        ]

        print("Found {} code files".format(len(self.code_files)))

    def _calculate_coverage(self) -> None:
        """Calculate documentation coverage metrics."""
        # Count modules with corresponding documentation
        documented_modules = 0

        for code_file in self.code_files:
            # Check if there's a doc mentioning this module
            module_name = code_file.stem
            for doc_path, fm in self.docs.items():
                doc_content = doc_path.read_text(encoding="utf-8")
                if module_name in doc_content:
                    documented_modules += 1
                    break

        total_modules = len(self.code_files)
        coverage_pct = (documented_modules / total_modules * 100) if total_modules > 0 else 0

        # Count API reference docs
        api_docs = sum(
            1 for fm in self.docs.values()
            if fm.get("type") == "reference"
        )

        self.metrics["coverage"] = {
            "total_modules": total_modules,
            "documented_modules": documented_modules,
            "coverage_pct": coverage_pct,
            "api_docs": api_docs,
        }

    def _calculate_health(self) -> None:
        """Calculate documentation health score."""
        # Check for broken links (basic check)
        broken_links = 0
        for doc_path in self.docs.keys():
            content = doc_path.read_text(encoding="utf-8")
            links = re.findall(r"\[([^\}}+)\]\(([^\)]+)\)", content)

            for link_text, link_path in links:
                # Skip external links
                if link_path.startswith(("http://", "https://", "mailto:")):
                    continue

                # Skip anchors
                if link_path.startswith("#"):
                    continue

                # Check if file exists
                clean_path = link_path.split("#")[0]
                if clean_path:
                    target = (doc_path.parent / clean_path).resolve()
                    if not target.exists():
                        broken_links += 1

        # Check staleness (>90 days)
        today = datetime.now().date()
        threshold = today - timedelta(days=90)
        stale_docs = 0

        for fm in self.docs.values():
            if "last_updated" in fm:
                try:
                    last_updated = datetime.strptime(str(fm["last_updated"]), "%Y-%m-%d").date()
                    if last_updated < threshold:
                        stale_docs += 1
                except ValueError:
                    pass

        # Check frontmatter completeness
        required_fields = ["title", "type", "status", "last_updated"]
        complete_frontmatter = sum(
            1 for fm in self.docs.values()
            if all(field in fm for field in required_fields)
        )

        frontmatter_pct = (complete_frontmatter / len(self.docs) * 100) if self.docs else 0

        # Calculate health score (0-100)
        # Factors: no broken links (40 pts), low staleness (30 pts), frontmatter complete (30 pts)
        health_score = 0

        if broken_links == 0:
            health_score += 40
        elif broken_links < 5:
            health_score += 20

        staleness_ratio = (stale_docs / len(self.docs)) if self.docs else 0
        if staleness_ratio < 0.1:
            health_score += 30
        elif staleness_ratio < 0.2:
            health_score += 20
        elif staleness_ratio < 0.3:
            health_score += 10

        if frontmatter_pct > 90:
            health_score += 30
        elif frontmatter_pct > 75:
            health_score += 20
        elif frontmatter_pct > 50:
            health_score += 10

        self.metrics["health"] = {
            "score": health_score,
            "broken_links": broken_links,
            "stale_docs": stale_docs,
            "frontmatter_complete_pct": frontmatter_pct,
        }

    def _calculate_activity(self) -> None:
        """Calculate documentation activity metrics."""
        today = datetime.now().date()

        updated_30d = 0
        updated_60d = 0
        updated_90d = 0

        for fm in self.docs.values():
            if "last_updated" in fm:
                try:
                    last_updated = datetime.strptime(str(fm["last_updated"]), "%Y-%m-%d").date()
                    days_ago = (today - last_updated).days

                    if days_ago <= 30:
                        updated_30d += 1
                    if days_ago <= 60:
                        updated_60d += 1
                    if days_ago <= 90:
                        updated_90d += 1
                except ValueError:
                    pass

        # Count new vs deprecated
        new_docs = sum(1 for fm in self.docs.values() if fm.get("status") == "draft")
        deprecated_docs = sum(1 for fm in self.docs.values() if fm.get("status") == "deprecated")

        self.metrics["activity"] = {
            "updated_30d": updated_30d,
            "updated_60d": updated_60d,
            "updated_90d": updated_90d,
            "new_docs": new_docs,
            "deprecated_docs": deprecated_docs,
        }

    def _calculate_quality(self) -> None:
        """Calculate documentation quality metrics."""
        # Cross-reference density
        docs_with_refs = sum(
            1 for fm in self.docs.values()
            if "related" in fm and fm["related"]
        )

        ref_density_pct = (docs_with_refs / len(self.docs) * 100) if self.docs else 0

        # Test extraction usage
        docs_with_tests = sum(
            1 for fm in self.docs.values()
            if fm.get("test_extraction") is True
        )

        # Count by type
        by_type = {}
        for fm in self.docs.values():
            doc_type = fm.get("type", "unknown")
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

        self.metrics["quality"] = {
            "cross_ref_density_pct": ref_density_pct,
            "docs_with_tests": docs_with_tests,
            "by_type": by_type,
        }

    def _generate_report(self) -> None:
        """Generate DOCUMENTATION_METRICS.md."""
        output_file = self.root_dir / "DOCUMENTATION_METRICS.md"

        lines = []

        # Header
        lines.append("# Documentation Metrics")
        lines.append("")
        lines.append("**Generated:** {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append("**Total Documents:** {}".format(len(self.docs)))
        lines.append("")
        lines.append("---")
        lines.append("")

        # Coverage section
        cov = self.metrics["coverage"]
        lines.append("## Coverage")
        lines.append("")
        lines.append("- **Code Coverage:** {:.1f}% ({}/{} modules documented)".format(cov['coverage_pct'], cov['documented_modules'], cov['total_modules']))
        lines.append("- **API Documentation:** {} reference docs".format(cov['api_docs']))
        lines.append("")

        # Health section
        health = self.metrics["health"]
        health_icon = "🟢" if health["score"] >= 80 else "🟡" if health["score"] >= 60 else "🔴"
        lines.append("## Health Score: {} {}/100".format(health_icon, health["score"]))
        lines.append("")
        lines.append("**Factors:**")
        lines.append("- {} Broken links: {}".format('✅' if health['broken_links'] == 0 else '❌', health['broken_links']))
        lines.append("- {} Stale docs (>90 days): {}".format('✅' if health['stale_docs'] < len(self.docs) * 0.1 else '⚠️ ', health['stale_docs']))
        lines.append("- {} Frontmatter complete: {:.1f}%".format('✅' if health['frontmatter_complete_pct'] > 90 else '⚠️ ', health['frontmatter_complete_pct']))
        lines.append("")

        # Activity section
        activity = self.metrics["activity"]
        lines.append("## Activity (Last 30/60/90 Days)")
        lines.append("")
        lines.append("- **Last 30 days:** {} docs updated".format(activity['updated_30d']))
        lines.append("- **Last 60 days:** {} docs updated".format(activity['updated_60d']))
        lines.append("- **Last 90 days:** {} docs updated".format(activity['updated_90d']))
        lines.append("")
        lines.append("- **New (draft):** {} docs".format(activity['new_docs']))
        lines.append("- **Deprecated:** {} docs".format(activity['deprecated_docs']))
        lines.append("")

        # Quality section
        quality = self.metrics["quality"]
        lines.append("## Quality")
        lines.append("")
        lines.append("- **Cross-reference density:** {:.1f}% (docs with related links)".format(quality['cross_ref_density_pct']))
        lines.append("- **Test extraction enabled:** {} docs".format(quality['docs_with_tests']))
        lines.append("")

        # By type breakdown
        lines.append("### Documents by Type")
        lines.append("")
        lines.append("| Type | Count | Percentage |")
        lines.append("|------|-------|------------|")
        for doc_type in sorted(quality["by_type"].keys()):
            count = quality["by_type"][doc_type]
            pct = (count / len(self.docs) * 100) if self.docs else 0
            lines.append("| {} | {} | {:.1f}% |".format(doc_type, count, pct))
        lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")

        if health["broken_links"] > 0:
            lines.append("- ⚠️  Fix {} broken internal links".format(health['broken_links']))

        if health["stale_docs"] > 0:
            lines.append("- ⚠️  Review {} stale docs (>90 days old)".format(health['stale_docs']))

        if health["frontmatter_complete_pct"] < 90:
            lines.append("- ⚠️  Add missing frontmatter fields ({:.1f}% incomplete)".format(100 - health['frontmatter_complete_pct']))

        if cov["coverage_pct"] < 75:
            lines.append("- 📝 Document {} undocumented modules".format(cov['total_modules'] - cov['documented_modules']))

        if quality["cross_ref_density_pct"] < 50:
            lines.append("- 🔗 Add cross-references to more docs (currently {:.1f}%)".format(quality['cross_ref_density_pct']))

        if not lines[-1].startswith("-"):
            lines.append("- ✅ No critical issues detected")

        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("**Note:** Run `python scripts/docs_metrics.py` to regenerate this report.")
        lines.append("")

        # Write to file
        content = "\n".join(lines)
        output_file.write_text(content, encoding="utf-8")

        print("✅ Generated {}".format(output_file))
        print()
        print("Health Score: {}/100".format(health['score']))
        print("Coverage: {:.1f}%".format(cov['coverage_pct']))
        print("Stale docs: {}".format(health['stale_docs']))
        print()


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    metrics = DocumentationMetrics(root_dir)
    metrics.run()


if __name__ == "__main__":
    main()
