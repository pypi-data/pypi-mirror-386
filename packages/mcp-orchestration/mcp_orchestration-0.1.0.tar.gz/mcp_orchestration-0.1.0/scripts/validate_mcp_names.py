#!/usr/bin/env python3
"""Validate MCP tool/resource names against Chora MCP Conventions v1.0.

This script validates that all MCP tools and resources in the codebase follow
the naming conventions defined in Chora MCP Conventions v1.0.

Usage:
    python scripts/validate_mcp_names.py
    python scripts/validate_mcp_names.py --fix  # Auto-fix simple violations

Exit codes:
    0 - All names valid
    1 - Validation errors found
    2 - Script error (file not found, etc.)

Reference:
    https://github.com/liminalcommons/chora-base/blob/main/docs/standards/CHORA_MCP_CONVENTIONS_v1.0.md
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple

# === Configuration ===

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src" / "mcp_orchestration"
MCP_NAMESPACE = "mcporchestration"
ENABLE_NAMESPACING = true

# === Validation Patterns (from Chora MCP Conventions v1.0) ===
NAMESPACE_PATTERN = re.compile(r'^[a-z][a-z0-9]{2,19}$')
TOOL_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]+:[a-z][a-z0-9_]+$')
RESOURCE_URI_PATTERN = re.compile(r'^[a-z][a-z0-9]+://[a-z0-9_/\-\.]+(\?.*)?$')
NON_NAMESPACED_TOOL_PATTERN = re.compile(r'^[a-z][a-z0-9_]+$')

# === Validation Functions ===

class ValidationError:
    """Represents a naming convention violation."""

    def __init__(
        self,
        file_path: Path,
        line_number: int,
        violation_type: str,
        message: str,
        suggestion: str = "",
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.violation_type = violation_type
        self.message = message
        self.suggestion = suggestion

    def __str__(self) -> str:
        msg = "{}: {}: {}".format(self.file_path, self.line_number, self.violation_type) + ": {}".format(self.message)
        if self.suggestion:
            msg += "\n  Suggestion: {}".format(self.suggestion)
        return msg


def validate_namespace(namespace: str) -> bool:
    """Validate namespace follows conventions."""
    return bool(NAMESPACE_PATTERN.match(namespace))


def validate_tool_name(name: str, namespacing_enabled: bool) -> Tuple[bool, str]:
    """Validate tool name.

    Returns:
        (is_valid, error_message)
    """
    if namespacing_enabled:
        if not TOOL_NAME_PATTERN.match(name):
            return False, "Tool name must match pattern: {}:tool_name (snake_case)".format(MCP_NAMESPACE)

        namespace, tool = name.split(":", 1)
        if namespace != MCP_NAMESPACE:
            return False, "Wrong namespace. Expected: {}:*, got: {}".format(MCP_NAMESPACE, name)

        return True, ""
    else:
        if not NON_NAMESPACED_TOOL_PATTERN.match(name):
            return False, "Tool name must be snake_case (no namespace in standalone mode)"

        return True, ""


def validate_resource_uri(uri: str, namespacing_enabled: bool) -> Tuple[bool, str]:
    """Validate resource URI.

    Returns:
        (is_valid, error_message)
    """
    if not namespacing_enabled:
        # No strict validation for non-namespaced mode
        return True, ""

    if not RESOURCE_URI_PATTERN.match(uri):
        return False, "Resource URI must match pattern: {}://type/id".format(MCP_NAMESPACE)

    namespace = uri.split("://", 1)[0]
    if namespace != MCP_NAMESPACE:
        return False, "Wrong namespace. Expected: {}://*, got: {}".format(MCP_NAMESPACE, uri)

    return True, ""


def extract_tool_names_from_file(file_path: Path) -> List[Tuple[int, str}}:
    """Extract tool names from Python file using AST parsing.

    Returns:
        List of (line_number, tool_name) tuples
    """
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception as e:
        print("Warning: Could not parse {}: {}".format(file_path, e), file=sys.stderr)
        return []

    tool_names = []

    # Look for @mcp.tool() decorators and string literals that look like tool names
    for node in ast.walk(tree):
        # Check for string literals that match tool name patterns
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if ENABLE_NAMESPACING:
                if ":" in value and TOOL_NAME_PATTERN.match(value):
                    tool_names.append((node.lineno, value))
            else:
                if ":" not in value and NON_NAMESPACED_TOOL_PATTERN.match(value):
                    # Only flag if it looks like a tool name (snake_case identifier)
                    tool_names.append((node.lineno, value))

    return tool_names


def extract_resource_uris_from_file(file_path: Path) -> List[Tuple[int, str}}:
    """Extract resource URIs from Python file using AST parsing.

    Returns:
        List of (line_number, uri) tuples
    """
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception as e:
        print("Warning: Could not parse {}: {}".format(file_path, e), file=sys.stderr)
        return []

    uris = []

    # Look for strings that match URI patterns
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if "://" in value and (
                RESOURCE_URI_PATTERN.match(value) or
                value.startswith("{}://".format(MCP_NAMESPACE))
            ):
                uris.append((node.lineno, value))

    return uris


def validate_file(file_path: Path) -> List[ValidationError]:
    """Validate MCP naming in a single file.

    Returns:
        List of validation errors found
    """
    errors = []

    # Extract and validate tool names
    tool_names = extract_tool_names_from_file(file_path)
    for line_num, tool_name in tool_names:
        is_valid, error_msg = validate_tool_name(tool_name, ENABLE_NAMESPACING)
        if not is_valid:
            suggestion = ""
            if ENABLE_NAMESPACING and ":" not in tool_name:
                suggestion = "Use: {}:{}".format(MCP_NAMESPACE, tool_name)
            errors.append(
                ValidationError(
                    file_path=file_path,
                    line_number=line_num,
                    violation_type="InvalidToolName",
                    message=error_msg,
                    suggestion=suggestion,
                )
            )

    # Extract and validate resource URIs
    resource_uris = extract_resource_uris_from_file(file_path)
    for line_num, uri in resource_uris:
        is_valid, error_msg = validate_resource_uri(uri, ENABLE_NAMESPACING)
        if not is_valid:
            suggestion = ""
            if ENABLE_NAMESPACING and "://" in uri and not uri.startswith("{}://".format(MCP_NAMESPACE)):
                # Try to extract type/id and suggest correct URI
                try:
                    _, rest = uri.split("://", 1)
                    suggestion = "Use: {}://{}".format(MCP_NAMESPACE, rest)
                except Exception:
                    pass
            errors.append(
                ValidationError(
                    file_path=file_path,
                    line_number=line_num,
                    violation_type="InvalidResourceURI",
                    message=error_msg,
                    suggestion=suggestion,
                )
            )

    return errors


def validate_codebase() -> List[ValidationError]:
    """Validate all Python files in src directory.

    Returns:
        List of all validation errors found
    """
    if not SRC_DIR.exists():
        print("Error: Source directory not found: {}".format(SRC_DIR), file=sys.stderr)
        sys.exit(2)

    all_errors = []

    # Find all Python files
    python_files = list(SRC_DIR.rglob("*.py"))

    if not python_files:
        print("Warning: No Python files found in {}".format(SRC_DIR), file=sys.stderr)
        return []

    print("Validating {} Python files...".format(len(python_files)))

    for file_path in python_files:
        errors = validate_file(file_path)
        all_errors.extend(errors)

    return all_errors


def validate_namespace_config() -> List[ValidationError]:
    """Validate the configured namespace itself."""
    errors = []

    if not validate_namespace(MCP_NAMESPACE):
        errors.append(
            ValidationError(
                file_path=Path("copier.yml"),
                line_number=0,
                violation_type="InvalidNamespace",
                message="Namespace '{}' doesn't follow conventions".format(MCP_NAMESPACE),
                suggestion="Must be lowercase, 3-20 chars, alphanumeric only",
            )
        )

    return errors


# === Main ===

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate MCP naming conventions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix simple violations (not implemented yet)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation progress",
    )

    args = parser.parse_args()

    if args.verbose:
        print("Configuration:")
        print("  Namespace: {}".format(MCP_NAMESPACE))
        print("  Namespacing enabled: {}".format(ENABLE_NAMESPACING))
        print("  Source directory: {}".format(SRC_DIR))
        print()

    # Validate namespace configuration
    config_errors = validate_namespace_config()

    # Validate codebase
    code_errors = validate_codebase()

    all_errors = config_errors + code_errors

    if not all_errors:
        print("✅ All MCP names follow Chora MCP Conventions v1.0")
        return 0

    # Print errors
    print("\n❌ Found {} naming convention violation(s):\n".format(len(all_errors)))

    for error in all_errors:
        print(str(error))
        print()

    print("Total violations: {}".format(len(all_errors)))
    print()
    print("Reference:")
    print("  https://github.com/liminalcommons/chora-base/blob/main/docs/standards/CHORA_MCP_CONVENTIONS_v1.0.md")

    if args.fix:
        print("\nNote: Auto-fix not implemented yet. Please fix violations manually.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
