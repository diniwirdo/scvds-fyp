import torch
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv, global_mean_pool


class GATv2EdgeAwareNet(torch.nn.Module):
    """
    The GNN model with 4 GATv2 layers.
    Detects 2 vulnerabilities: Access Control and Unchecked External Call.
    """

    def __init__(self, input_dim=4, hidden_dim=64, num_heads=4):
        super().__init__()

        # Layer 1
        self.conv1 = GATv2Conv(input_dim, hidden_dim, heads=num_heads)
        self.norm1 = torch.nn.LayerNorm(hidden_dim * num_heads)

        # Layer 2
        self.conv2 = GATv2Conv(hidden_dim * num_heads, hidden_dim, heads=num_heads)
        self.norm2 = torch.nn.LayerNorm(hidden_dim * num_heads)

        # Layer 3
        self.conv3 = GATv2Conv(hidden_dim * num_heads, hidden_dim, heads=num_heads)
        self.norm3 = torch.nn.LayerNorm(hidden_dim * num_heads)

        # Layer 4
        self.conv4 = GATv2Conv(hidden_dim * num_heads, hidden_dim, heads=1)
        self.norm4 = torch.nn.LayerNorm(hidden_dim)

        # Final classifier
        self.fc1 = torch.nn.Linear(hidden_dim, 32)
        self.fc2 = torch.nn.Linear(32, 2)  # 2 vulnerabilities

        self.dropout = torch.nn.Dropout(0.3)

    def forward(self, x, edge_index, batch):
        # Layer 1
        x1 = self.conv1(x, edge_index)
        x1 = self.norm1(x1)
        x1 = F.relu(x1)
        x1 = self.dropout(x1)

        # Layer 2 with residual
        x2 = self.conv2(x1, edge_index)
        x2 = self.norm2(x2)
        x2 = F.relu(x2 + x1)
        x2 = self.dropout(x2)

        # Layer 3 with residual
        x3 = self.conv3(x2, edge_index)
        x3 = self.norm3(x3)
        x3 = F.relu(x3 + x2)
        x3 = self.dropout(x3)

        # Layer 4
        x4 = self.conv4(x3, edge_index)
        x4 = self.norm4(x4)
        x4 = F.relu(x4 + x3)

        # Pool the graph
        x_pooled = global_mean_pool(x4, batch)

        # Classifier
        x_out = F.relu(self.fc1(x_pooled))
        x_out = self.dropout(x_out)
        x_out = self.fc2(x_out)

        return x_out
