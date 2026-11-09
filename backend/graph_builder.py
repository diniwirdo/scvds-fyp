import torch
from torch_geometric.data import Data


# =============================================
# Feature vector layout (24 features per node):
# =============================================
# Node type (one-hot, 5):
#  0: is_contract
#  1: is_function
#  2: is_modifier
#  3: is_state_variable
#  4: is_external_call
#
# Contract features (2):
#  5: num_contracts (normalized)
#  6: source_length (normalized)
#
# Function features (10):
#  7:  has_access_control (modifiers)
#  8:  is_public_or_external
#  9:  is_payable
#  10: require_count (normalized)
#  11: has_state_write
#  12: has_msg_sender
#  13: has_tx_origin
#  14: has_external_call
#  15: body_length (normalized)
#  16: visibility_rank (0=private, 1=internal, 2=public, 3=external)
#
# Global features (7):
#  17: has_tx_origin (global)
#  18: has_delegatecall
#  19: has_selfdestruct
#  20: has_constructor
#  21: has_fallback
#  22: has_payable (global)
#  23: total_require_count (normalized)

FEATURE_DIM = 24


def build_graph(parsed):
    """
    Build a PyTorch Geometric graph from parsed Solidity data.
    Uses 24 features per node.
    """
    nodes = []
    edges = []
    node_id = 0

    # Normalization constants
    max_contracts = 5.0
    max_source_len = 100000.0
    max_require = 20.0
    max_body = 5000.0
    max_total_require = 100.0

    # ===== Contract nodes =====
    contract_ids = []
    for _ in parsed.get("contracts", []):
        features = [0.0] * FEATURE_DIM
        features[0] = 1.0  # is_contract
        features[5] = min(len(parsed["contracts"]) / max_contracts, 1.0)
        features[6] = min(parsed.get("source_length", 0) / max_source_len, 1.0)
        features[17] = 1.0 if parsed.get("has_tx_origin") else 0.0
        features[18] = 1.0 if parsed.get("has_delegatecall") else 0.0
        features[19] = 1.0 if parsed.get("has_selfdestruct") else 0.0
        features[20] = 1.0 if parsed.get("has_constructor") else 0.0
        features[21] = 1.0 if parsed.get("has_fallback") else 0.0
        features[22] = 1.0 if parsed.get("has_payable") else 0.0
        features[23] = min(parsed.get("total_require_count", 0) / max_total_require, 1.0)

        nodes.append({"id": node_id, "type": "contract", "features": features})
        contract_ids.append(node_id)
        node_id += 1

    # ===== Function nodes =====
    function_ids = []
    for func in parsed.get("functions", []):
        features = [0.0] * FEATURE_DIM
        features[1] = 1.0  # is_function

        # Function-specific
        features[7] = 1.0 if func["modifiers"] else 0.0
        features[8] = 1.0 if func["visibility"] in ["public", "external"] else 0.0
        features[9] = 1.0 if func.get("is_payable") else 0.0
        features[10] = min(func.get("require_count", 0) / max_require, 1.0)
        features[11] = 1.0 if func.get("has_state_write") else 0.0
        features[12] = 1.0 if func.get("has_msg_sender") else 0.0
        features[13] = 1.0 if func.get("has_tx_origin") else 0.0
        features[14] = 1.0 if func.get("has_external_call") else 0.0
        features[15] = min(func.get("body_length", 0) / max_body, 1.0)

        # Visibility rank
        vis_rank = {"private": 0.0, "internal": 1.0, "public": 2.0, "external": 3.0}
        features[16] = vis_rank.get(func["visibility"], 0.0) / 3.0

        # Global features (copied for consistency)
        features[17] = 1.0 if parsed.get("has_tx_origin") else 0.0
        features[18] = 1.0 if parsed.get("has_delegatecall") else 0.0
        features[19] = 1.0 if parsed.get("has_selfdestruct") else 0.0
        features[20] = 1.0 if parsed.get("has_constructor") else 0.0
        features[21] = 1.0 if parsed.get("has_fallback") else 0.0
        features[22] = 1.0 if parsed.get("has_payable") else 0.0
        features[23] = min(parsed.get("total_require_count", 0) / max_total_require, 1.0)

        nodes.append({"id": node_id, "type": "function", "features": features})
        function_ids.append(node_id)
        node_id += 1

    # ===== Modifier nodes =====
    modifier_ids = []
    for _ in parsed.get("modifiers", []):
        features = [0.0] * FEATURE_DIM
        features[2] = 1.0  # is_modifier
        nodes.append({"id": node_id, "type": "modifier", "features": features})
        modifier_ids.append(node_id)
        node_id += 1

    # ===== State variable nodes =====
    variable_ids = []
    for _ in parsed.get("state_variables", []):
        features = [0.0] * FEATURE_DIM
        features[3] = 1.0  # is_state_var
        nodes.append({"id": node_id, "type": "state_var", "features": features})
        variable_ids.append(node_id)
        node_id += 1

    # ===== External call nodes =====
    call_ids = []
    for _ in range(parsed.get("external_call_count", 0)):
        features = [0.0] * FEATURE_DIM
        features[4] = 1.0  # is_external_call
        nodes.append({"id": node_id, "type": "external_call", "features": features})
        call_ids.append(node_id)
        node_id += 1

    # ===== Build edges =====
    for cid in contract_ids:
        for fid in function_ids:
            edges.append([cid, fid])
        for mid in modifier_ids:
            edges.append([cid, mid])
        for vid in variable_ids:
            edges.append([cid, vid])

    # Function → Function flow
    for i in range(len(function_ids) - 1):
        edges.append([function_ids[i], function_ids[i + 1]])

    # Function → External Call
    for fid in function_ids:
        for cid in call_ids:
            edges.append([fid, cid])

    # Modifier → Function (which modifiers apply to which functions)
    # Simplified: connect every modifier to every function with AC
    for mid in modifier_ids:
        for fid in function_ids:
            edges.append([mid, fid])

    # Convert to tensors
    if nodes:
        x = torch.tensor([n["features"] for n in nodes], dtype=torch.float)
    else:
        x = torch.zeros((1, FEATURE_DIM), dtype=torch.float)

    if edges:
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    return Data(x=x, edge_index=edge_index)