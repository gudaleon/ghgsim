#!/usr/bin/env python3
"""
License compliance checker for ghgsim.

Ensures no GPL code enters Apache-2.0 core modules.

Usage:
    python scripts/check_licenses.py
    
Exit codes:
    0: All checks passed
    1: License violations found
"""

import re
import sys
from pathlib import Path


# GPL indicators in source files
GPL_PATTERNS = [
    re.compile(r"GNU\s+General\s+Public\s+License", re.IGNORECASE),
    re.compile(r"\bGPL\b"),
    re.compile(r"GNU\s+GPL", re.IGNORECASE),
    re.compile(r"copyleft", re.IGNORECASE),
    re.compile(r"Free\s+Software\s+Foundation", re.IGNORECASE),
]

# Allowed license indicators
ALLOWED_PATTERNS = [
    re.compile(r"Apache\s+License,?\s+Version\s+2\.0", re.IGNORECASE),
    re.compile(r"SPDX-License-Identifier:\s*Apache-2\.0"),
    re.compile(r"MIT\s+License", re.IGNORECASE),
    re.compile(r"BSD\s+License", re.IGNORECASE),
]

# Paths to check
CORE_DIRS = [
    "src/ghgsim/core",
    "src/ghgsim/modules",
    "src/ghgsim/services",
    "src/ghgsim/api",
    "src/ghgsim/io",
]

# Allowed to reference GPL (docs, comments about external tools)
EXEMPT_PATHS = [
    "docs/",
    "tests/",
    "legacy/",
    "scripts/",
]


def check_file(path: Path) -> tuple[bool, list[str]]:
    """
    Check file for GPL violations.
    
    Returns:
        (is_clean, violations)
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        # Skip binary files or missing files
        return True, []
    
    violations = []
    
    for pattern in GPL_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            # Check if it's just a reference vs actual GPL licensing
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    # Allow citations and references
                    if "cite" in line.lower() or "reference" in line.lower():
                        continue
                    if "#" in line or "//" in line or "/*" in line:
                        # Comment - check context
                        if "holos" in line.lower() and "gpl" in line.lower():
                            # Reference to Holos GPL = OK in comments
                            continue
                    
                    violations.append(f"Line {i}: {line.strip()[:80]}")
    
    return len(violations) == 0, violations


def main():
    """Run license checks."""
    root = Path(".")
    violations_found = False
    
    print("=" * 70)
    print("License Compliance Check")
    print("=" * 70)
    print(f"Checking core directories for GPL violations:\n")
    
    for core_dir in CORE_DIRS:
        dir_path = root / core_dir
        if not dir_path.exists():
            continue
        
        print(f"📁 {core_dir}")
        
        for py_file in dir_path.rglob("*.py"):
            # Check if exempt
            is_exempt = any(str(py_file).startswith(exempt) for exempt in EXEMPT_PATHS)
            if is_exempt:
                continue
            
            is_clean, violations = check_file(py_file)
            
            if not is_clean:
                violations_found = True
                print(f"  ❌ {py_file.relative_to(root)}")
                for violation in violations:
                    print(f"     {violation}")
            else:
                print(f"  ✓ {py_file.relative_to(root)}")
    
    print("\n" + "=" * 70)
    
    if violations_found:
        print("❌ LICENSE VIOLATIONS FOUND")
        print("=" * 70)
        print("\nGPL code must not be included in Apache-2.0 core modules.")
        print("Options:")
        print("  1. Remove GPL code")
        print("  2. Re-implement from original sources (IPCC, AAFC, peer-reviewed papers)")
        print("  3. Cite Holos/GPL sources in comments but implement independently")
        print("  4. Move GPL-derived code to separate optional plugin (if necessary)")
        sys.exit(1)
    else:
        print("✅ All checks passed - no GPL violations found")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
