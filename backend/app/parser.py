import subprocess
import json
import os
import re


def parse_with_slither(file_path):
    """
    Use Slither to get AST and CFG from a Solidity file.
    Falls back to simple parsing if Slither fails.
    """
    try:
        # Run slither to get the AST in JSON format
        result = subprocess.run(
            ["slither", file_path, "--print", "ast-compact-json"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Slither failed: {e}")

    # Fallback: simple parsing
    return simple_parse(file_path)


def simple_parse(file_path):
    """
    Simple parser if Slither doesn't work.
    Reads the file and finds key patterns.
    """
    with open(file_path, "r") as f:
        source = f.read()

    contracts = re.findall(r"contract\s+(\w+)", source)
    functions = re.findall(r"function\s+(\w+)", source)
    modifiers = re.findall(r"modifier\s+(\w+)", source)

    # Look for access control keywords
    has_only_owner = "onlyOwner" in source
    has_require_sender = "require(msg.sender" in source
    has_role_control = "AccessControl" in source or "hasRole" in source

    # Look for external calls
    external_calls = len(re.findall(r"\.call\(", source))
    external_calls += len(re.findall(r"\.send\(", source))
    external_calls += len(re.findall(r"\.transfer\(", source))

    # Look for return value checks
    checks_return = len(re.findall(r"\(bool\s+\w+\s*,", source))
    checks_return += len(re.findall(r"require\(success", source))

    return {
        "type": "simple",
        "contracts": contracts,
        "functions": functions,
        "modifiers": modifiers,
        "has_only_owner": has_only_owner,
        "has_require_sender": has_require_sender,
        "has_role_control": has_role_control,
        "external_calls": external_calls,
        "checks_return": checks_return,
        "source": source,
    }


def parse_solidity(file_path):
    """Main function to call."""
    return parse_with_slither(file_path)
