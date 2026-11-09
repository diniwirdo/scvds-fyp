import os
import pandas as pd
from parser import parse_solidity
from graph_builder import build_graph


# Load labels
LABELS = pd.read_csv("dataset/DIVE_Labels.csv")
LABELS = LABELS.set_index("contractID")


def test_file(file_path):
    print(f"\n--- Testing: {file_path} ---")

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    contract_id = int(os.path.basename(file_path).replace(".sol", ""))
    parsed = parse_solidity(file_path)

    print(f"Contract ID: {contract_id}")
    print(f"Contracts: {parsed['contracts']}")
    print(f"Functions: {len(parsed['functions'])}")
    print(f"Modifiers: {parsed['modifiers']}")
    print(f"State variables: {len(parsed['state_variables'])}")
    print(f"External calls: {parsed['external_call_count']}")
    print(f"Unchecked calls: {parsed['unchecked_call_count']}")
    print(f"Has owner check: {parsed['has_owner_check']}")

    if contract_id in LABELS.index:
        true_ac = int(LABELS.loc[contract_id, "Access Control"])
        true_uc = int(LABELS.loc[contract_id, "Unchecked Return Values"])
        print(f"\nTRUE LABELS (from CSV):")
        print(f"  Access Control: {true_ac}")
        print(f"  Unchecked Return Values: {true_uc}")

    graph = build_graph(parsed)
    print(f"\nGraph: {graph}")


print("=" * 60)
print("TEST 1: Access Control vulnerable")
print("=" * 60)
test_file("dataset/access_control/4.sol")

print("\n" + "=" * 60)
print("TEST 2: Unchecked Call vulnerable")
print("=" * 60)
test_file("dataset/unchecked_call/5.sol")

print("\n" + "=" * 60)
print("TEST 3: Safe contract")
print("=" * 60)
test_file("dataset/safe/1.sol")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)