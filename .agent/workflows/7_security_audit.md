---
description: Comprehensive security audit workflow based on previous sessions.
---

# Step 7: SECURITY AUDIT (Güvenlik Denetimi)

Paranoid-level check for vulnerabilities.

## 1. Secrets & Config
- [ ] Scan for hardcoded passwords/API keys in `app/`, `scripts/`.
- [ ] Verify `.env` is in `.gitignore`.
- [ ] Check `debug_jwt.py` and `debug_output.txt` for leaked tokens.

## 2. Input Validation (The "Never Trust User" Rule)
- [ ] **SQL Injection**: Are we using ORM/params everywhere? (Audit `db_manager.py`).
- [ ] **XSS**: Are we sanitizing inputs in React? (Audit `dashboard.html`, React forms).
- [ ] **File Upload**: Does `add_missing_columns.py` or upload endpoints check mime types?

## 3. Data Protection
- [ ] **PII**: Is driver phone/TCKH masked in logs? (Check `startup.log`, `logs/`).
- [ ] **Encryption**: Are passwords hashed with `bcrypt`? (See `requirements.txt`).

## 4. Infrastructure
- [ ] **Middleware**: Is CORS configured correctly?
- [ ] **Rate Limiting**: Is it enabled on Login/Register endpoints?

## Automation
Run the existing sanitizer script:
```bash
python scripts/security_sanitizer.py
```
