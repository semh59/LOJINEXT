# MCP Configuration Guide (Project: Excel / TIR Yakıt Takip)

This configuration enables your AI to have "God Mode" access to your specific project environment.

## 1. Primary Servers (Mandatory)

### 📂 Filesystem MCP (Built-in)

- **Scope**: Allow access to `D:\PROJECT\LOJINEXT` and all subdirectories.
- **Why**: Standard read/write access.

### 🗄️ SQLite MCP

- **Use Case**: Direct DB querying without writing `check_db` scripts.
- **Args**:
  ```json
  {
    "dbPaths": ["D:/PROJECT/LOJINEXT/app.db"] // Update with actual DB path
  }
  ```
- **Prompt Example**: "Check if the vehicle with plate '34 ABC 12' exists in the database."

### 🌐 Fetch MCP

- **Use Case**: Reading verifying external docs for library updates.
- **Why**: You use `nicegui`, `pydantic`, `zustand`. Docs change fast.
- **Prompt Example**: "Read https://nicegui.io/documentation/section/table to fix the sorting issue."

## 2. Advanced Servers (Optional but Recommended)

### 🕵️‍♂️ Sequential Thinking MCP

- **Why**: For complex debugging logic (like the "Event loop is closed" error).
- **Prompt Example**: "Use sequential thinking to analyze the race condition in `verify_db_connection.py`."

### 🧪 Playwright/Puppeteer MCP

- **Why**: You have `e2e_upload_test.py` and UI tests.
- **Prompt Example**: "Go to localhost:3000, login as admin, and attempt to upload 'test.xlsx'. Screenshot the result."

---

## 🚀 How to Enable

Update your AI Client's configuration file (e.g., `claude_desktop_config.json` or equivalent) with the arguments above.
