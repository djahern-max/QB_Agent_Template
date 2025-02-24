#!/usr/bin/env python3
"""
Script to find inconsistencies between 'realm' and 'realm_id' usage in a Python codebase.
Run this from the root of your project directory.
"""

import os
import re
from collections import defaultdict
import sys


def find_realm_inconsistencies(directory="."):
    """Find inconsistencies between 'realm' and 'realm_id' usage in Python files."""
    results = defaultdict(list)
    pattern = re.compile(r"\b(realm|realm_id|realmId)\b")

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        if matches:
                            results[file_path] = matches
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return results


def print_results(results):
    """Print the results in a readable format."""
    print("\n===== Files with realm/realm_id/realmId usage =====\n")

    for file_path, matches in sorted(results.items()):
        count_realm = matches.count("realm")
        count_realm_id = matches.count("realm_id")
        count_realmId = matches.count("realmId")

        if count_realm + count_realm_id + count_realmId > 0:
            print(f"\n{file_path}:")
            print(f"  - 'realm': {count_realm} occurrences")
            print(f"  - 'realm_id': {count_realm_id} occurrences")
            print(f"  - 'realmId': {count_realmId} occurrences")

    print("\n===== Summary =====\n")
    all_matches = [match for matches in results.values() for match in matches]
    print(f"Total 'realm' occurrences: {all_matches.count('realm')}")
    print(f"Total 'realm_id' occurrences: {all_matches.count('realm_id')}")
    print(f"Total 'realmId' occurrences: {all_matches.count('realmId')}")


def suggest_fixes():
    """Provide suggestions for standardizing the naming."""
    print("\n===== Suggested Fixes =====\n")
    print(
        "Based on your API routes, 'realm_id' seems to be your standard naming convention."
    )
    print("Consider these steps to standardize your codebase:")
    print("1. Update database models to use 'realm_id' consistently")
    print("2. Update schemas/Pydantic models to use 'realm_id'")
    print("3. Make sure route parameters use 'realm_id'")
    print("4. Update service functions to accept 'realm_id'")
    print("5. Special consideration for QuickBooks API:")
    print("   - QuickBooks API might use 'realmId' in their responses")
    print("   - Consider mapping this to 'realm_id' as soon as you receive responses")
    print("\nExample code for converting QuickBooks 'realmId' to your 'realm_id':")
    print(
        """
# When receiving data from QuickBooks
qb_response = quickbooks_api_call()
if 'realmId' in qb_response:
    # Map to your standardized naming
    data = {
        'realm_id': qb_response['realmId'],
        # Other fields...
    }
    """
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."

    print(f"Scanning directory: {directory}")
    results = find_realm_inconsistencies(directory)
    print_results(results)
    suggest_fixes()
