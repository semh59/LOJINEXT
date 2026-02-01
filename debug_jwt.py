
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from app.config import settings
from app.core.security import create_access_token
from jose import jwt, JWTError
from app.api.deps import get_current_user

# Mock dependencies
class MockDB:
    async def execute(self, stmt):
        print(f"DEBUG: DB Query executed: {stmt}")
        return self

    def scalar_one_or_none(self):
        # Simulate user found
        print("DEBUG: Simulate DB returning user 'admin'")
        from app.database.models import Kullanici
        return Kullanici(kullanici_adi="admin", aktif=True, rol="admin", ad_soyad="Admin User")

async def debug_token():
    print(f"--- SECURITY CONFIG ---")
    print(f"SECRET_KEY starts with: {settings.SECRET_KEY.get_secret_value()[:5]}...")
    print(f"ALGORITHM: {settings.ALGORITHM}")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    
    # 1. Generate Token
    print(f"\n--- GENERATING TOKEN ---")
    data = {"sub": "admin", "role": "admin"}
    token = create_access_token(data)
    print(f"Token: {token[:20]}...{token[-20:]}")
    
    # 2. Decode Manually
    print(f"\n--- DECODING TOKEN (Manual) ---")
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY.get_secret_value(), 
            algorithms=[settings.ALGORITHM]
        )
        print(f"Decoded Payload: {payload}")
    except Exception as e:
        print(f"ERROR Decoding: {e}")
        return

    # 3. Simulate Deps Validation
    print(f"\n--- VALIDATING VIA DEPS LOGIC ---")
    try:
        # Re-implement logic from deps.py to see where it fails
        decode_result = jwt.decode(
            token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM]
        )
        username = decode_result.get("sub")
        print(f"Username from token: {username}")
        
        if username != "admin":
             print("ERROR: Username mismatch!")
        else:
             print("SUCCESS: Token logic is self-consistent.")
             
    except Exception as e:
        print(f"ERROR in Deps Logic: {e}")

if __name__ == "__main__":
    asyncio.run(debug_token())
