import os
import glob
import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GATv2Conv, global_mean_pool
import random


# ============================
# Configuration
# ============================
CACHE_DIR = "dataset/graph_cache"
MODEL_SAVE_PATH = "model_files/trained_model.pt"

# Training hyperparameters
BATCH_SIZE = 32
EPOCHS = 30
LEARNING_RATE = 0.001
HIDDEN_DIM = 64
NUM_HEADS = 4
DROPOUT = 0.3

# Number of vulnerability classes to detect
NUM_CLASSES = 2  # [Access Control, Unchecked Call]


class GATv2EdgeAwareNet(torch.nn.Module):
    def __init__(self, input_dim=24, hidden_dim=64, num_heads=4, output_dim=2):
        super().__init__()

        self.hidden_total = hidden_dim * num_heads  # 256

        # Layer 1
        self.conv1 = GATv2Conv(input_dim, hidden_dim, heads=num_heads)
        self.norm1 = torch.nn.LayerNorm(self.hidden_total)

        # Layer 2
        self.conv2 = GATv2Conv(self.hidden_total, hidden_dim, heads=num_heads)
        self.norm2 = torch.nn.LayerNorm(self.hidden_total)

        # Layer 3
        self.conv3 = GATv2Conv(self.hidden_total, hidden_dim, heads=num_heads)
        self.norm3 = torch.nn.LayerNorm(self.hidden_total)

        # Layer 4 - keep output as hidden_total so residual with x3 works
        self.conv4 = GATv2Conv(self.hidden_total, hidden_dim, heads=num_heads)
        self.norm4 = torch.nn.LayerNorm(self.hidden_total)

        # Classifier
        self.fc1 = torch.nn.Linear(self.hidden_total, 32)
        self.fc2 = torch.nn.Linear(32, output_dim)

        self.dropout = torch.nn.Dropout(DROPOUT)

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

        # Layer 4 with residual (now shapes match)
        x4 = self.conv4(x3, edge_index)
        x4 = self.norm4(x4)
        x4 = F.relu(x4 + x3)

        # Global pooling
        x_pool = global_mean_pool(x4, batch)

        # Classifier
        out = F.relu(self.fc1(x_pool))
        out = self.dropout(out)
        out = self.fc2(out)

        return out


# ============================
# Load Dataset
# ============================
def load_all_graphs():
    print("Loading cached graphs...")

    all_graphs = []

    for category in ["access_control", "unchecked_call", "safe"]:
        folder = os.path.join(CACHE_DIR, category)
        files = glob.glob(os.path.join(folder, "*.pt"))
        print(f"  {category}: {len(files)} graphs")

        for file in files:
            try:
                graph = torch.load(file, weights_only=False)
                all_graphs.append(graph)
            except Exception as e:
                print(f"  Skipping {file}: {e}")

    print(f"Total graphs loaded: {len(all_graphs)}")
    return all_graphs


def split_dataset(graphs, train_ratio=0.8, val_ratio=0.1):
    random.seed(42)
    random.shuffle(graphs)

    n = len(graphs)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train = graphs[:n_train]
    val = graphs[n_train:n_train + n_val]
    test = graphs[n_train + n_val:]

    return train, val, test


# ============================
# Training
# ============================
def train_one_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()

        out = model(batch.x, batch.edge_index, batch.batch)
        loss = F.binary_cross_entropy_with_logits(out, batch.y)

        loss.backward()
        optimizer.step()

        total_loss += loss.item() * batch.num_graphs

        # Accuracy
        probs = torch.sigmoid(out)
        preds = (probs > 0.5).float()
        correct += (preds == batch.y).sum().item()
        total += batch.y.numel()

    return total_loss / total, correct / total


def evaluate(model, loader, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = F.binary_cross_entropy_with_logits(out, batch.y)

            total_loss += loss.item() * batch.num_graphs

            probs = torch.sigmoid(out)
            preds = (probs > 0.5).float()
            correct += (preds == batch.y).sum().item()
            total += batch.y.numel()

            all_preds.append(preds.cpu())
            all_labels.append(batch.y.cpu())

    all_preds = torch.cat(all_preds)
    all_labels = torch.cat(all_labels)

    # Per-class accuracy
    ac_correct = ((all_preds[:, 0] == all_labels[:, 0]).sum().item())
    uc_correct = ((all_preds[:, 1] == all_labels[:, 1]).sum().item())
    n = len(all_labels)

    return total_loss / total, correct / total, ac_correct / n, uc_correct / n


def main():
    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load data
    graphs = load_all_graphs()
    train_graphs, val_graphs, test_graphs = split_dataset(graphs)

    print(f"\nSplit:")
    print(f"  Train: {len(train_graphs)}")
    print(f"  Val:   {len(val_graphs)}")
    print(f"  Test:  {len(test_graphs)}")

    # Data loaders
    train_loader = DataLoader(train_graphs, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_graphs, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_graphs, batch_size=BATCH_SIZE, shuffle=False)

    # Model
    model = GATv2EdgeAwareNet(
        input_dim=24,
        hidden_dim=HIDDEN_DIM,
        num_heads=NUM_HEADS,
        output_dim=NUM_CLASSES,
    ).to(device)

    print(f"\nModel parameters: {sum(p.numel() for p in model.parameters()):,}")

    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)

    # Training loop
    best_val_loss = float("inf")
    os.makedirs("model_files", exist_ok=True)

    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)

    for epoch in range(1, EPOCHS + 1):
        train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, device)
        val_loss, val_acc, ac_acc, uc_acc = evaluate(model, val_loader, device)

        print(
            f"Epoch {epoch:02d}/{EPOCHS} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
            f"AC Acc: {ac_acc:.4f} UC Acc: {uc_acc:.4f}"
        )

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
            }, MODEL_SAVE_PATH)
            print(f"  → Saved best model to {MODEL_SAVE_PATH}")

    # Final evaluation on test set
    print("\n" + "=" * 60)
    print("Final test evaluation:")
    print("=" * 60)

    # Load best model
    checkpoint = torch.load(MODEL_SAVE_PATH, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_loss, test_acc, ac_acc, uc_acc = evaluate(model, test_loader, device)
    print(f"Test Loss:      {test_loss:.4f}")
    print(f"Test Accuracy:  {test_acc:.4f}")
    print(f"  Access Control Accuracy:        {ac_acc:.4f}")
    print(f"  Unchecked Call Accuracy:        {uc_acc:.4f}")

    print("\nTraining complete!")


if __name__ == "__main__":
    main()