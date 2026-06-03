from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# KONFIGURASI
SECRET_KEY = "ai-document-intelligence-secret-2026"  # ← ganti ini
ALGORITHM = "HS256"
TOKEN_EXPIRE_MENIT = 60     # ← sesuaikan kebutuhan

# Setup enkripsi password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:    # enkripsi password
    return pwd_context.hash(password)

def verifikasi_password(password: str, hashed: str) -> bool:    # cek password
    return pwd_context.verify(password, hashed)

def buat_token(data: dict) -> str:      # buat JWT token
    data_copy = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MENIT)
    data_copy.update({"exp": expire})
    return jwt.encode(data_copy, SECRET_KEY, algorithm=ALGORITHM)

def verifikasi_token(token: str) -> dict:   # cek JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None