import os
import re

directories = ["dashboard", "predictions", "reports", "trips", "vehicles"]
base_dir = r"d:\PROJECT\LOJINEXT\frontend"


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Revert /legacy back to the original index
    new_content = re.sub(
        r'(from\s+[\'"](?:\.\./)*services/api)/legacy([\'"])', r"\1\2", content
    )
    new_content = re.sub(r'(from\s+[\'"]\./api)/legacy([\'"])', r"\1\2", new_content)

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"-> Reverted {filepath}")


# 1. Componentler
for d in directories:
    dir_path = os.path.join(base_dir, "src", "components", d)
    if os.path.exists(dir_path):
        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.endswith(".tsx") or f.endswith(".ts"):
                    process_file(os.path.join(root, f))

# 2. Pages
page_dir = os.path.join(base_dir, "src", "pages")
if os.path.exists(page_dir):
    for root, _, files in os.walk(page_dir):
        for f in files:
            process_file(os.path.join(root, f))

# 3. Context
context_dir = os.path.join(base_dir, "src", "context")
if os.path.exists(context_dir):
    for root, _, files in os.walk(context_dir):
        for f in files:
            process_file(os.path.join(root, f))

# 4. Services
service_dir = os.path.join(base_dir, "src", "services")
if os.path.exists(service_dir):
    for root, _, files in os.walk(service_dir):
        for f in files:
            process_file(os.path.join(root, f))
