import re


def parse_solidity(file_path):
    """
    Enhanced Solidity parser with richer features for GNN training.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    # Remove comments
    source_clean = re.sub(r"//.*?$", "", source, flags=re.MULTILINE)
    source_clean = re.sub(r"/\*.*?\*/", "", source_clean, flags=re.DOTALL)

    result = {
        "contracts": [],
        "functions": [],
        "modifiers": [],
        "state_variables": [],
        "external_call_count": 0,
        "unchecked_call_count": 0,
        "has_owner_check": False,
        "has_only_owner_modifier": False,
        "has_require_sender": False,
        "has_role_based_access": False,
        "has_tx_origin": False,
        "has_delegatecall": False,
        "has_selfdestruct": False,
        "has_constructor": False,
        "has_fallback": False,
        "has_payable": False,
        "total_require_count": 0,
        "total_function_count": 0,
        "public_function_count": 0,
        "external_function_count": 0,
        "private_function_count": 0,
        "internal_function_count": 0,
        "source_length": len(source),
    }

    try:
        # ===== Contracts =====
        result["contracts"] = re.findall(r"contract\s+(\w+)", source_clean)

        # ===== Functions =====
        # Match function headers with everything up to the body
        function_pattern = r"function\s+(\w+)\s*\(([^)]*)\)\s*([^{;]*)"
        for match in re.finditer(function_pattern, source_clean):
            func_name = match.group(1)
            params_str = match.group(2)
            modifiers_str = match.group(3)

            # Extract modifiers
            modifiers = re.findall(
                r"\b(onlyOwner|onlyAdmin|onlyRole|onlyMinter|only[A-Z]\w+)\b",
                modifiers_str,
            )

            # Visibility
            visibility = "public"
            if "external" in modifiers_str:
                visibility = "external"
                result["external_function_count"] += 1
            elif "private" in modifiers_str:
                visibility = "private"
                result["private_function_count"] += 1
            elif "internal" in modifiers_str:
                visibility = "internal"
                result["internal_function_count"] += 1
            else:
                result["public_function_count"] += 1

            # Payable
            is_payable = "payable" in modifiers_str

            # Find the function body (between first { and matching })
            body_start = match.end()
            body = extract_function_body(source_clean, body_start)

            # Analyze the body
            require_count = len(re.findall(r"\brequire\s*\(", body))
            has_state_write = bool(re.search(r"\w+\s*(=|\+=|-=|\*=|\/=)\s*", body))
            has_msg_sender = "msg.sender" in body
            has_tx_origin = "tx.origin" in body
            has_ext_call = bool(re.search(r"\.(call|send|delegatecall)\s*[\({]", body))
            has_revert = "revert" in body
            has_return = "return" in body

            result["functions"].append({
                "name": func_name,
                "modifiers": modifiers,
                "visibility": visibility,
                "is_payable": is_payable,
                "require_count": require_count,
                "has_state_write": has_state_write,
                "has_msg_sender": has_msg_sender,
                "has_tx_origin": has_tx_origin,
                "has_external_call": has_ext_call,
                "body_length": len(body),
            })

            result["total_require_count"] += require_count

        result["total_function_count"] = len(result["functions"])

        # ===== Modifiers =====
        result["modifiers"] = re.findall(r"modifier\s+(\w+)", source_clean)

        # ===== State Variables =====
        var_pattern = r"\b(uint256|uint|uint8|uint128|address|bool|bytes32|bytes|string|mapping)\s+(?:public\s+|private\s+|internal\s+|constant\s+)?(\w+)\s*[;=]"
        result["state_variables"] = re.findall(var_pattern, source_clean)

        # ===== External Calls =====
        call_count = 0
        call_count += len(re.findall(r"\.call\s*[\({]", source_clean))
        call_count += len(re.findall(r"\.send\s*\(", source_clean))
        call_count += len(re.findall(r"\.delegatecall\s*\(", source_clean))
        result["external_call_count"] = call_count

        # ===== Access Control Detection =====
        if "onlyOwner" in source_clean:
            result["has_only_owner_modifier"] = True

        if re.search(r"require\s*\(\s*msg\.sender\s*==", source_clean):
            result["has_require_sender"] = True

        if "hasRole" in source_clean or "AccessControl" in source_clean or "onlyRole" in source_clean:
            result["has_role_based_access"] = True

        result["has_owner_check"] = (
            result["has_only_owner_modifier"]
            or result["has_require_sender"]
            or result["has_role_based_access"]
        )

        # ===== Dangerous Patterns =====
        result["has_tx_origin"] = "tx.origin" in source_clean
        result["has_delegatecall"] = ".delegatecall(" in source_clean
        result["has_selfdestruct"] = "selfdestruct" in source_clean or "suicide" in source_clean
        result["has_constructor"] = "constructor(" in source_clean or "function " not in source_clean
        result["has_fallback"] = "fallback" in source_clean or "function()" in source_clean
        result["has_payable"] = "payable" in source_clean

        # ===== Unchecked Call Detection =====
        checked_require = len(re.findall(r"require\s*\(\s*\w*success", source_clean))
        checked_if = len(re.findall(r"if\s*\(\s*!\s*\w*success", source_clean))
        checked_or_require = len(re.findall(r"require\s*\([^)]*\.call", source_clean))
        total_checks = checked_require + checked_if + checked_or_require

        result["unchecked_call_count"] = max(0, call_count - total_checks)

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return result


def extract_function_body(source, start_index):
    """
    Extract the body of a function (between first { and its matching }).
    """
    # Find first {
    i = start_index
    while i < len(source) and source[i] != "{":
        if source[i] == ";":  # function declaration without body
            return ""
        i += 1

    if i >= len(source):
        return ""

    # Find matching }
    depth = 0
    j = i
    while j < len(source):
        if source[j] == "{":
            depth += 1
        elif source[j] == "}":
            depth -= 1
            if depth == 0:
                return source[i + 1:j]
        j += 1

    return source[i + 1:]