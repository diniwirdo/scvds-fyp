import pandas as pd
import shutil
import os
from tqdm import tqdm

CSV_PATH = "dataset/DIVE_Labels.csv"
SOURCE_DIR = "dataset/DIVE_Raw_Data/Raw/PRE/Source codes"
AC_OUTPUT = "dataset/access_control"
UC_OUTPUT = "dataset/unchecked_call"
SAFE_OUTPUT = "dataset/safe"

os.makedirs(AC_OUTPUT, exist_ok=True)
os.makedirs(UC_OUTPUT, exist_ok=True)
os.makedirs(SAFE_OUTPUT, exist_ok=True)

df = pd.read_csv(CSV_PATH)
print(f"Total contracts: {len(df)}")

# Build lists of what to copy
ac_list = []
uc_list = []
safe_list = []

for _, row in df.iterrows():
    cid = int(row["contractID"])
    src = os.path.join(SOURCE_DIR, f"{cid}.sol")
    if not os.path.exists(src):
        continue
    if row["Access Control"] == 1:
        ac_list.append((src, os.path.join(AC_OUTPUT, f"{cid}.sol")))
    if row["Unchecked Return Values"] == 1:
        uc_list.append((src, os.path.join(UC_OUTPUT, f"{cid}.sol")))
    if row["Access Control"] == 0 and row["Unchecked Return Values"] == 0:
        safe_list.append((src, os.path.join(SAFE_OUTPUT, f"{cid}.sol")))

print(f"To copy: AC={len(ac_list)}, UC={len(uc_list)}, Safe={len(safe_list)}")

# Copy with progress bars
for src, dst in tqdm(ac_list, desc="Copying AC"):
    shutil.copy2(src, dst)

for src, dst in tqdm(uc_list, desc="Copying UC"):
    shutil.copy2(src, dst)

for src, dst in tqdm(safe_list, desc="Copying Safe"):
    shutil.copy2(src, dst)

print("Done!")