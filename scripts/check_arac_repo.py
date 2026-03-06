import sys
import os

sys.path.append(os.getcwd())

try:
    from app.database.repositories.arac_repo import get_arac_repo

    print("Import success")
    repo = get_arac_repo()
    print(f"Repo instance: {repo}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
