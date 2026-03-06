import sys
sys.path.append(r"d:\PROJECT\excel")

try:
    print("Importing SeferService...")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
