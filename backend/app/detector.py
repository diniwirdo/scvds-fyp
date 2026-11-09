import torch
import os
from app.model import GATv2EdgeAwareNet
from app.graph_builder import build_graph_from_code
from app.parser import simple_parse

MODEL_PATH = "model_files/trained_model.pt"

# Vulnerability names
VULN_NAMES = ["Access Control", "Unchecked External Call"]

SEVERITY = {
    "Access Control": "Critical",
    "Unchecked External Call": "High",
}

RECOMMENDATIONS = {
    "Access Control": "Add onlyOwner modifier or role-based access control. Use OpenZeppelin AccessControl.",
    "Unchecked External Call": "Always check return values. Use require(success, 'Failed').",
}


def detect(file_path):
    """
    Detect vulnerabilities in a Solidity file.
    """
    # Step 1: Parse the file
    parsed = simple_parse(file_path)

    # Step 2: Build graph
    graph = build_graph_from_code(file_path)

    # Step 3: Try to use the trained model
    if os.path.exists(MODEL_PATH):
        # Use real GNN model
        predictions = run_gnn_model(graph)
    else:
        # Use rule-based fallback (until model is trained)
        predictions = rule_based_detection(parsed)

    # Step 4: Format results
    results = []
    for i, name in enumerate(VULN_NAMES):
        if predictions[i] > 0.5:
            results.append({
                "type": name,
                "confidence": float(predictions[i]),
                "severity": SEVERITY[name],
                "recommendation": RECOMMENDATIONS[name],
            })

    return results


def run_gnn_model(graph):
    """Load trained model and predict."""
    model = GATv2EdgeAwareNet()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    graph.batch = torch.zeros(graph.x.size(0), dtype=torch.long)

    with torch.no_grad():
        output = model(graph.x, graph.edge_index, graph.batch)
        probabilities = torch.softmax(output, dim=1)[0]

    return probabilities.tolist()


def rule_based_detection(parsed):
    """
    Simple rules until your GNN model is trained.
    """
    results = [0.0, 0.0]

    # Check access control
    has_control = (
        parsed.get("has_only_owner", False)
        or parsed.get("has_require_sender", False)
        or parsed.get("has_role_control", False)
    )
    if not has_control and len(parsed.get("functions", [])) > 0:
        results[0] = 0.85

    # Check external calls
    if parsed.get("external_calls", 0) > 0:
        unchecked = parsed.get("external_calls", 0) - parsed.get("checks_return", 0)
        if unchecked > 0:
            results[1] = 0.80

    return results
