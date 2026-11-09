import os
import torch
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv, global_mean_pool

from parser import parse_solidity
from graph_builder import build_graph


# ============================================
# Model definition (same as train_model.py)
# ============================================
class GATv2EdgeAwareNet(torch.nn.Module):
    def __init__(self, input_dim=24, hidden_dim=64, num_heads=4, output_dim=2):
        super().__init__()
        self.hidden_total = hidden_dim * num_heads

        self.conv1 = GATv2Conv(input_dim, hidden_dim, heads=num_heads)
        self.norm1 = torch.nn.LayerNorm(self.hidden_total)

        self.conv2 = GATv2Conv(self.hidden_total, hidden_dim, heads=num_heads)
        self.norm2 = torch.nn.LayerNorm(self.hidden_total)

        self.conv3 = GATv2Conv(self.hidden_total, hidden_dim, heads=num_heads)
        self.norm3 = torch.nn.LayerNorm(self.hidden_total)

        self.conv4 = GATv2Conv(self.hidden_total, hidden_dim, heads=num_heads)
        self.norm4 = torch.nn.LayerNorm(self.hidden_total)

        self.fc1 = torch.nn.Linear(self.hidden_total, 32)
        self.fc2 = torch.nn.Linear(32, output_dim)
        self.dropout = torch.nn.Dropout(0.3)

    def forward(self, x, edge_index, batch):
        x1 = F.relu(self.norm1(self.conv1(x, edge_index)))
        x1 = self.dropout(x1)

        x2 = self.norm2(self.conv2(x1, edge_index))
        x2 = F.relu(x2 + x1)
        x2 = self.dropout(x2)

        x3 = self.norm3(self.conv3(x2, edge_index))
        x3 = F.relu(x3 + x2)
        x3 = self.dropout(x3)

        x4 = self.norm4(self.conv4(x3, edge_index))
        x4 = F.relu(x4 + x3)

        x_pool = global_mean_pool(x4, batch)
        out = F.relu(self.fc1(x_pool))
        out = self.dropout(out)
        out = self.fc2(out)
        return out


# ============================================
# Predictor class
# ============================================
class VulnerabilityPredictor:
    VULN_NAMES = ["Access Control", "Unchecked External Call"]

    RECOMMENDATIONS = {
        "Access Control": "Add onlyOwner modifier or role-based access control. Use OpenZeppelin AccessControl.",
        "Unchecked External Call": "Always check return values. Use require(success, 'Failed').",
    }

    SEVERITY = {
        "Access Control": "Critical",
        "Unchecked External Call": "High",
    }

    def __init__(self, model_path="model_files/trained_model.pt"):
        self.device = torch.device("cpu")
        self.model = GATv2EdgeAwareNet()

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

        print(f"Model loaded from {model_path}")

    def predict(self, file_path):
        """
        Predict vulnerabilities and extract the vulnerable code lines.
        """
        # Read the source code to find the bad lines
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source_lines = f.readlines()

        # Parse and build graph
        parsed = parse_solidity(file_path)
        graph = build_graph(parsed)

        # Add batch dimension
        graph.batch = torch.zeros(graph.x.size(0), dtype=torch.long)

        with torch.no_grad():
            output = self.model(graph.x, graph.edge_index, graph.batch)
            probs = torch.sigmoid(output)[0]

        results = []
        for i, name in enumerate(self.VULN_NAMES):
            confidence = float(probs[i].item())

            if confidence > 0.60: # Threshold
                # NEW: Find the bad code lines
                bad_lines = []
                for line_num, line in enumerate(source_lines, 1):
                    line_clean = line.strip()
                    
                    if name == "Access Control":
                        # Look for functions without modifiers
                        if "function " in line_clean and "public" in line_clean and "only" not in line_clean:
                            bad_lines.append(f"Line {line_num}: {line_clean}")
                    
                    elif name == "Unchecked External Call":
                        # Look for external calls
                        if ".call(" in line_clean or ".send(" in line_clean:
                            bad_lines.append(f"Line {line_num}: {line_clean}")

                # Limit to first 3 lines for UI neatness
                bad_lines = bad_lines[:3] 
                if not bad_lines:
                    bad_lines = ["Vulnerability detected in function logic. Manual review recommended."]

                results.append({
                    "type": name,
                    "confidence": confidence,
                    "severity": self.SEVERITY[name],
                    "recommendation": self.RECOMMENDATIONS[name],
                    "code_snippets": bad_lines, # NEW FIELD
                })

        return results