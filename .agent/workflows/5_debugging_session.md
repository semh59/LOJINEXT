---
description: Systematic approach to fixing bugs.
---

# Step 5: DEBUGGING SESSION (Hata Ayıklama)

Don't guess. Investigate.

## 1. Reproduce (Tekrar Et)
- Can you make it happen again?
- What are the exact steps?
- Environment: Browser, OS, User Role?

## 2. Isolate (İzole Et)
- **Frontend vs Backend**: Check Network tab. 
    - Request sent? Correct payload?
    - Response received? Correct status code?
- **Component vs Global**: Does it happen everywhere or just here?

## 3. Hypothesis (Varsayım)
- "I think X is null because Y didn't load."
- "The database transaction isn't committing."

## 4. Proposal (Çözüm Önerisi)
Present the fix with:
- **Root Cause**: Why it happened.
- **Fix**: The code change.
- **Prevention**: How to stop it from happening again (e.g., stricter types, tests).

## 5. Verification (Doğrulama)
- Fix the bug.
- Verify the fix.
- **Regression Check**: Did we break anything else?
