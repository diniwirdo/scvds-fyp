import os
import torch
import pandas as pd
from tqdm import tqdm
from parser import parse_solidity
from graph_builder import build_graph


# Configuration
LABELS_CSV = "dataset/DIVE_Labels.csv"
CACHE_DIR = "dataset/graph_cache"

# Sample size (start small, then scale up)
ACCESS_CONTROL_SAMPLE = 3000
UNCHECKED_CALL_SAMPLE = 3000
SAFE_SAMPLE = 3000


def prebuild_graphs():
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Load labels
    df = pd.read_csv(LABELS_CSV)
    print(f"Total contracts: {len(df)}")

    # --- Access Control vulnerable ---
    ac_df = df[df["Access Control"] == 1].sample(
        n=min(ACCESS_CONTROL_SAMPLE, len(df[df["Access Control"] == 1])),
        random_state=42,
    )
    # --- Unchecked Call vulnerable ---
    uc_df = df[df["Unchecked Return Values"] == 1].sample(
        n=min(UNCHECKED_CALL_SAMPLE, len(df[df["Unchecked Return Values"] == 1])),
        random_state=42,
    )
    # --- Safe ---
    safe_df = df[(df["Access Control"] == 0) & (df["Unchecked Return Values"] == 0)].sample(
        n=min(SAFE_SAMPLE, len(df[(df["Access Control"] == 0) & (df["Unchecked Return Values"] == 0)])),
        random_state=42,
    )

    print(f"Access Control samples: {len(ac_df)}")
    print(f"Unchecked Call samples: {len(uc_df)}")
    print(f"Safe samples: {len(safe_df)}")

    # Process each category
    process_category(ac_df, "access_control", CACHE_DIR)
    process_category(uc_df, "unchecked_call", CACHE_DIR)
    process_category(safe_df, "safe", CACHE_DIR)

    print("\nDone! Graphs cached in", CACHE_DIR)


def process_category(df, category, cache_dir):
    output_dir = os.path.join(cache_dir, category)
    os.makedirs(output_dir, exist_ok=True)

    source_dir = f"dataset/{category}"
    if category == "unchecked_call":
        source_dir = "dataset/unchecked_call"
    elif category == "safe":
        source_dir = "dataset/safe"

    processed = 0
    skipped = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Building {category}"):
        contract_id = int(row["contractID"])
        sol_path = os.path.join(source_dir, f"{contract_id}.sol")

        if not os.path.exists(sol_path):
            skipped += 1
            continue

        try:
            parsed = parse_solidity(sol_path)
            graph = build_graph(parsed)

            # Attach labels
            graph.y = torch.tensor(
                [[
                    int(row["Access Control"]),
                    int(row["Unchecked Return Values"]),
                ]],
                dtype=torch.float,
            )
            graph.contract_id = contract_id

            # Save
            torch.save(graph, os.path.join(output_dir, f"{contract_id}.pt"))
            processed += 1

        except Exception as e:
            skipped += 1
            continue

    print(f"{category}: processed={processed}, skipped={skipped}")


if __name__ == "__main__":
    prebuild_graphs()
