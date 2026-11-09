import subprocess
import os

test_file = "dataset/access_control/4.sol"

print(f"Testing: {test_file}\n")

# Try Slither with a shorter timeout
result = subprocess.run(
    ["slither", test_file],
    capture_output=True,
    text=True,
    timeout=60
)

print("Return code:", result.returncode)
print()
print("=== STDOUT ===")
print(result.stdout[:2000] if result.stdout else "(empty)")
print()
print("=== STDERR ===")
print(result.stderr[:3000] if result.stderr else "(empty)")