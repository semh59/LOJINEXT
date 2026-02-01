
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from app.config import settings
from jose import jwt
from datetime import datetime, timedelta

print(f"DEBUG: Loading settings from: {settings.model_config.get('env_file')}")
print(f"DEBUG: SECRET_KEY prefix: {settings.SECRET_KEY.get_secret_value()[:5]}...")
print(f"DEBUG: ALGORITHM: {settings.ALGORITHM}")

# Create a test token
data = {"sub": "admin"}
expire = datetime.utcnow() + timedelta(minutes=15)
to_encode = data.copy()
to_encode.update({"exp": expire})
encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM)

print(f"DEBUG: Generated Token: {encoded_jwt}")

# Decode logic (simulating deps.py)
try:
    payload = jwt.decode(
        encoded_jwt, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM]
    )
    username = payload.get("sub")
    print(f"DEBUG: Decoded Username: {username}")
    if username == "admin":
        print("SUCCESS: Token verification passed locally.")
    else:
        print("FAILURE: Username mismatch.")
except Exception as e:
    print(f"FAILURE: Decode error: {e}")

