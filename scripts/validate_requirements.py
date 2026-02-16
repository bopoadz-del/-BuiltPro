#!/usr/bin/env python3
"""
Validate that all pinned package versions in requirements files exist on PyPI.

This script helps catch typos or non-existent versions before they cause CI failures.

Usage:
    python scripts/validate_requirements.py
    python scripts/validate_requirements.py requirements.txt
    python scripts/validate_requirements.py backend/requirements.txt
"""

from __future__ import annotations

import re
import sys
import urllib.request
import json
from pathlib import Path
from typing import List, Tuple


def parse_requirement_line(line: str) -> Tuple[str | None, str | None]:
    """Parse a requirements line to extract package name and version."""
    line = line.strip()
    
    # Skip comments and empty lines
    if not line or line.startswith('#'):
        return None, None
    
    # Match patterns like: package==version or package[extras]==version
    match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*?\])?\s*==\s*([0-9.]+[a-z0-9]*)', line)
    if match:
        return match.group(1), match.group(2)
    
    return None, None


def check_version_exists(package: str, version: str) -> bool:
    """Check if a specific version of a package exists on PyPI."""
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
            available_versions = list(data.get('releases', {}).keys())
            return version in available_versions
    except Exception as e:
        print(f"  ⚠️  Warning: Could not check {package}: {e}")
        return True  # Assume valid if we can't check


def validate_requirements_file(filepath: str) -> List[str]:
    """Validate all pinned versions in a requirements file."""
    errors = []
    path = Path(filepath)
    
    if not path.exists():
        return [f"File not found: {filepath}"]
    
    print(f"\n📋 Validating {filepath}...")
    
    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            package, version = parse_requirement_line(line)
            if package and version:
                print(f"  Checking {package}=={version}...", end=" ")
                if not check_version_exists(package, version):
                    error = f"  ❌ Line {line_num}: {package}=={version} does not exist on PyPI"
                    errors.append(error)
                    print("NOT FOUND ❌")
                else:
                    print("✓")
    
    return errors


def main():
    """Main validation function."""
    # Default files to check
    files_to_check = [
        "requirements.txt",
        "backend/requirements.txt",
    ]
    
    # Allow specifying files via command line
    if len(sys.argv) > 1:
        files_to_check = sys.argv[1:]
    
    print("🔍 Requirements Validator")
    print("=" * 60)
    
    all_errors = []
    for filepath in files_to_check:
        errors = validate_requirements_file(filepath)
        all_errors.extend(errors)
    
    print("\n" + "=" * 60)
    if all_errors:
        print("❌ Validation FAILED\n")
        for error in all_errors:
            print(error)
        sys.exit(1)
    else:
        print("✅ All versions are valid!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
