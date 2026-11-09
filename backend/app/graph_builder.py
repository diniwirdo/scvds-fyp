import re
import torch
from torch_geometric.data import Data


def build_graph_from_code(file_path):
    """
    Build a graph from Solidity code for the GNN model.
    
    Nodes = functions, variables, statements
    Edges = relationships between them
    """
    with open(file_path, "r") as f:
        source = f.read()

    nodes = []
    edges = []
    node_id = 0

    # Add contract node
    contracts = re.findall(r"contract\s+(\w+)", source)
    for c in contracts:
        nodes.append({"id": node_id, "type": "contract", "name": c, "features": [1, 0, 0, 0]})
        node_id += 1

    # Add function nodes
    functions = re.findall(r"function\s+(\w+)", source)
    function_ids = []
    for f in functions:
        # Check if function has access control
        pattern = rf"function\s+{f}\s*\([^)]*\)\s*(public|external|internal|private)?\s*(onlyOwner|onlyAdmin)?"
        match = re.search(pattern, source)

        has_access_control = 0
        if match and match.group(2):
            has_access_control = 1
        if "onlyOwner" in source or "onlyAdmin" in source:
            has_access_control = 1

        nodes.append({
            "id": node_id,
            "type": "function",
            "name": f,
            "features": [0, 1, 0, has_access_control],
        })
        function_ids.append(node_id)
        node_id += 1

    # Add external call nodes
    calls = re.findall(r"\.call\(|\.send\(|\.transfer\(", source)
    for _ in calls:
        nodes.append({"id": node_id, "type": "external_call", "name": "call", "features": [0, 0, 1, 0]})
        node_id += 1

    # Add edges (functions connect to each other and to calls)
    for i in range(len(function_ids) - 1):
        edges.append([function_ids[i], function_ids[i + 1]])

    # Connect functions to external calls
    for i, fid in enumerate(function_ids):
        for cid in range(len(functions) + len(contracts), node_id):
            edges.append([fid, cid])

    # Build feature matrix
    if nodes:
        x = torch.tensor([n["features"] for n in nodes], dtype=torch.float)
    else:
        x = torch.tensor([[0, 0, 0, 0]], dtype=torch.float)

    # Build edge index
    if edges:
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    return Data(x=x, edge_index=edge_index)
