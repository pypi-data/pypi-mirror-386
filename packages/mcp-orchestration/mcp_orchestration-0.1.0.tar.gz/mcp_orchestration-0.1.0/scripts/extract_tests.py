#!/usr/bin/env python3
"""
Extract executable code examples from documentation and generate test file.

Finds all markdown files with `test_extraction: true` in frontmatter,
extracts code blocks with language tags, and generates test file:
tests/integration/test_from_docs.py

Advanced features (Phase 4a):
- Fixture support (# FIXTURE: name)
- Async/await test support
- Parameterized tests (# PARAMETERIZE: ...)
- Basic bash test support

This ensures documentation examples stay executable and synchronized with code.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install PyYAML")
    sys.exit(1)


class TestExtractor:
    """Extract tests from documentation code examples with advanced features."""

    # Directories to check
    DOC_DIRS = ["user-docs", "project-docs", "dev-docs"]

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.docs_with_tests: List[Tuple[Path, Dict}} = []  # (path, frontmatter)
        self.extracted_tests: List[str] = []
        self.extracted_fixtures: List[str] = []
        self.bash_tests: List[str] = []
        self.requires_async: bool = False
        self.requires_pytest_params: bool = False

    def run(self) -> None:
        """Run test extraction and generate test file."""
print("Extracting tests from documentation in {}...".format(self.root_dir))        print()

        # Step 1: Find docs with test_extraction: true
        self._find_docs_with_tests()

        if not self.docs_with_tests:
            print("No documents found with test_extraction: true in frontmatter.")
            print("Skipping test file generation.")
            return

print("Found {} documents with test_extraction: true".format(len(self.docs_with_tests)))        print()

        # Step 2: Extract code blocks
        for md_file, frontmatter in self.docs_with_tests:
            self._extract_tests_from_doc(md_file, frontmatter)

        if not self.extracted_tests and not self.bash_tests:
            print("No testable code blocks found (need language-tagged code blocks)")
            return

        # Step 3: Generate test files
        if self.extracted_tests:
            self._generate_python_test_file()

        if self.bash_tests:
            self._generate_bash_test_file()

    def _find_docs_with_tests(self) -> None:
        """Find all docs with test_extraction: true in frontmatter."""
        for doc_dir in self.DOC_DIRS:
            dir_path = self.root_dir / doc_dir
            if not dir_path.exists():
                continue

            for md_file in dir_path.rglob("*.md"):
                frontmatter = self._parse_frontmatter(md_file)
                if frontmatter and frontmatter.get("test_extraction") is True:
                    self.docs_with_tests.append((md_file, frontmatter))

    def _parse_frontmatter(self, md_file: Path) -> Dict | None:
        """Parse YAML frontmatter from markdown file."""
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            return None

        # Check for frontmatter (--- ... ---)
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return None

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                return None
            return frontmatter
        except yaml.YAMLError:
            return None

    def _extract_tests_from_doc(self, md_file: Path, frontmatter: Dict) -> None:
        """Extract testable code blocks from a markdown file."""
        content = md_file.read_text(encoding="utf-8")

        # Find all code blocks with language tag
        # Pattern: ```language\ncode\n```
        code_blocks = re.findall(
            r"```(python|bash|sh)\n(.*?)```", content, re.DOTALL
        )

        if not code_blocks:
            return

        doc_title = frontmatter.get("title", md_file.name)
        doc_rel_path = md_file.relative_to(self.root_dir)

        for idx, (lang, code) in enumerate(code_blocks, start=1):
            if lang == "python":
                self._extract_python_test(doc_title, doc_rel_path, code, idx)
            elif lang in ("bash", "sh"):
                self._extract_bash_test(doc_title, doc_rel_path, code, idx)

    def _extract_python_test(
        self, doc_title: str, doc_path: Path, code: str, idx: int
    ) -> None:
        """Extract a Python code block as a test with advanced features."""
        code = code.strip()

        # Check for special markers
        is_fixture = "# FIXTURE:" in code
        is_parameterized = "# PARAMETERIZE:" in code
        is_async = "async def" in code or "await " in code
        has_assertions = "assert" in code or "raise" in code

        if is_fixture:
            self._extract_fixture(doc_title, code, idx)
            return

        # Skip code blocks that are just examples without assertions
        if not has_assertions and not is_parameterized:
            return

        # Generate test function name (safe identifier)
        safe_title = re.sub(r"[^a-zA-Z0-9_]", "_", doc_title.lower())
test_name = "test_{}_example_{}".format(safe_title, idx)
        if is_parameterized:
            self._extract_parameterized_test(test_name, doc_title, doc_path, code, idx)
        elif is_async:
            self._extract_async_test(test_name, doc_title, doc_path, code, idx)
        else:
            self._extract_regular_test(test_name, doc_title, doc_path, code, idx)

    def _extract_fixture(self, doc_title: str, code: str, idx: int) -> None:
        """Extract a pytest fixture from documentation."""
        # Parse fixture name from comment
        match = re.search(r"# FIXTURE:\s*(\w+)", code)
        if not match:
            return

        fixture_name = match.group(1)

        # Remove the FIXTURE comment from code
        code_lines = code.split("\n")
        code_lines = [line for line in code_lines if not line.strip().startswith("# FIXTURE:")]
        clean_code = "\n".join(code_lines)

        # Generate fixture
fixture_code = '''
@pytest.fixture
def {}():
    """Fixture extracted from documentation: {}"""
{}
'''.format(fixture_name, doc_title, self._indent(clean_code, 4))
        self.extracted_fixtures.append(fixture_code)

    def _extract_async_test(
        self, test_name: str, doc_title: str, doc_path: Path, code: str, idx: int
    ) -> None:
        """Extract an async test function."""
        self.requires_async = True

        # Generate async test function
test_code = '''
@pytest.mark.asyncio
async def {}():
    """
    Async test extracted from documentation: {}
    Source: {}
    Example {}
    """
{}
'''.format(test_name, doc_title, doc_path, idx, self._indent(code, 4))
        self.extracted_tests.append(test_code)

    def _extract_parameterized_test(
        self, test_name: str, doc_title: str, doc_path: Path, code: str, idx: int
    ) -> None:
        """Extract a parameterized test function."""
        self.requires_pytest_params = True

        # Parse PARAMETERIZE comment
        # Format: # PARAMETERIZE: argnames="x,y", argvalues=[(1,2), (3,4)]
        match = re.search(r'# PARAMETERIZE:\s*(.+)', code)
        if not match:
            # Fall back to regular test if parsing fails
            self._extract_regular_test(test_name, doc_title, doc_path, code, idx)
            return

        param_spec = match.group(1).strip()

        # Remove PARAMETERIZE comment from code
        code_lines = code.split("\n")
        code_lines = [line for line in code_lines if not line.strip().startswith("# PARAMETERIZE:")]
        clean_code = "\n".join(code_lines)

        # Generate parameterized test
test_code = '''
@pytest.mark.parametrize({})
def {}():
    """
    Parameterized test extracted from documentation: {}
    Source: {}
    Example {}
    """
{}
'''.format(param_spec, test_name, doc_title, doc_path, idx, self._indent(clean_code, 4))
        self.extracted_tests.append(test_code)

    def _extract_regular_test(
        self, test_name: str, doc_title: str, doc_path: Path, code: str, idx: int
    ) -> None:
        """Extract a regular (non-async, non-parameterized) test function."""
        # Generate test function
test_code = '''
def {}():
    """
    Test extracted from documentation: {}
    Source: {}
    Example {}
    """
{}
'''.format(test_name, doc_title, doc_path, idx, self._indent(code, 4))
        self.extracted_tests.append(test_code)

    def _extract_bash_test(
        self, doc_title: str, doc_path: Path, code: str, idx: int
    ) -> None:
        """Extract a bash test case."""
        code = code.strip()

        # Look for EXPECT_EXIT and EXPECT_OUTPUT markers
        expected_exit = "0"
        expected_output = None

        # Parse special comments
        if "# EXPECT_EXIT:" in code:
            match = re.search(r"# EXPECT_EXIT:\s*(\d+)", code)
            if match:
                expected_exit = match.group(1)

        if "# EXPECT_OUTPUT:" in code:
            match = re.search(r"# EXPECT_OUTPUT:\s*(.+)", code)
            if match:
                expected_output = match.group(1).strip()

        # Remove special comments from code
        code_lines = code.split("\n")
        code_lines = [
            line for line in code_lines
            if not line.strip().startswith(("# EXPECT_EXIT:", "# EXPECT_OUTPUT:", "# TEST:"))
        ]
        clean_code = "\n".join(code_lines)

        # Generate bash test
        safe_title = re.sub(r"[^a-zA-Z0-9_]", "_", doc_title.lower())
test_name = "test_{}_bash_example_{}".format(safe_title, idx)
bash_test = '''
test_{}_bash_example_{}() {{
    # Test extracted from documentation: {}
    # Source: {}
    # Example {}

{}

    local exit_code=$?
    if [ $exit_code -ne {} ]; then
        echo "FAILED: Expected exit code {}, got $exit_code"
        return 1
    fi
'''.format(safe_title, idx, doc_title, doc_path, idx, self._indent(clean_code, 4), expected_exit, expected_exit)
        if expected_output:
bash_test += '''
    # Check output contains expected string
    if ! echo "$output" | grep -q "{}"; then
        echo "FAILED: Expected output to contain: {}"
        return 1
    fi
'''.format(expected_output, expected_output)
        bash_test += '''
    echo "PASSED"
    return 0
}
'''

        self.bash_tests.append(bash_test)

    def _indent(self, text: str, spaces: int) -> str:
        """Indent text by specified number of spaces."""
        indent = " " * spaces
        return "\n".join(indent + line if line.strip() else line for line in text.split("\n"))

    def _generate_python_test_file(self) -> None:
        """Generate tests/integration/test_from_docs.py."""
        output_dir = self.root_dir / "tests" / "integration"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "test_from_docs.py"

        # Generate file header
        imports = ["import pytest", "from pathlib import Path", "import sys"]

        if self.requires_async:
            imports.insert(1, "import pytest_asyncio")

        # Build features list
        features = []
        if self.requires_async:
            features.append('- Async tests (pytest-asyncio)')
        if self.requires_pytest_params:
            features.append('- Parameterized tests')
        if self.extracted_fixtures:
            features.append('- Fixtures')
        features_text = '\n'.join(features) if features else ''

        header = '''"""
Tests extracted from documentation code examples.

This file is auto-generated by scripts/extract_tests.py.
Do not edit manually - update the documentation instead.

Features used:
{}
"""

{}

# Add src to path for imports
src_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_dir))

'''.format(features_text, '\n'.join(imports))
        # Add fixtures section
        if self.extracted_fixtures:
            header += "\n# ===== Fixtures =====\n"
            header += "\n".join(self.extracted_fixtures)
            header += "\n\n# ===== Tests =====\n"

        # Combine header + tests
        content = header + "\n".join(self.extracted_tests)

        # Write to file
        output_file.write_text(content, encoding="utf-8")

print("✅ Generated {}".format(output_file))print("   Extracted {} test functions".format(len(self.extracted_tests)))        if self.extracted_fixtures:
print("   Extracted {} fixtures".format(len(self.extracted_fixtures)))        if self.requires_async:
            print("   ⚠️  Requires pytest-asyncio: pip install pytest-asyncio")
        print()
        print("Run tests with: pytest tests/integration/test_from_docs.py")

    def _generate_bash_test_file(self) -> None:
        """Generate tests/integration/test_from_docs.sh."""
        output_dir = self.root_dir / "tests" / "integration"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "test_from_docs.sh"

        # Generate file header
        header = '''#!/usr/bin/env bash
# Bash tests extracted from documentation code examples.
#
# This file is auto-generated by scripts/extract_tests.py.
# Do not edit manually - update the documentation instead.

set -e  # Exit on error

# Color output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
NC='\\033[0m' # No Color

TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

'''

        # Add tests
        content = header + "\n".join(self.bash_tests)

        # Add test runner
        content += '''
# Run all tests
echo "Running bash tests extracted from documentation..."
echo

'''

        for bash_test in self.bash_tests:
            # Extract test name from function definition
            match = re.search(r'(test_\w+)\(\)', bash_test)
            if match:
                test_name = match.group(1)
                content += '''
if {}; then
    echo -e "$✓$ {}"
    ((TESTS_PASSED++))
else
    echo -e "$✗$ {}"
    ((TESTS_FAILED++))
fi
((TESTS_RUN++))
'''.format(test_name, test_name, test_name)
        content += '''
echo
echo "===== Results ====="
echo "Tests run: $TESTS_RUN"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo "All tests passed!"
    exit 0
fi
'''

        # Write to file
        output_file.write_text(content, encoding="utf-8")
        output_file.chmod(0o755)  # Make executable

print("✅ Generated {}".format(output_file))print("   Extracted {} bash tests".format(len(self.bash_tests)))        print()
        print("Run tests with: ./tests/integration/test_from_docs.sh")


def main():
    """Main entry point."""
    # Assume script is in scripts/ directory, project root is parent
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    extractor = TestExtractor(root_dir)
    extractor.run()


if __name__ == "__main__":
    main()
