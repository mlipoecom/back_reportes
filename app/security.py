
from fastapi import HTTPException
from datetime import datetime, timedelta
from jose import jwt
from config import TOKEN_CONFIG


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=TOKEN_CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"]))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, TOKEN_CONFIG["SECRET_KEY"], algorithm=TOKEN_CONFIG["ALGORITHM"])

def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(days=TOKEN_CONFIG["REFRESH_TOKEN_EXPIRE_DAYS"]))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, TOKEN_CONFIG["SECRET_KEY"], algorithm=TOKEN_CONFIG["ALGORITHM"])

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, TOKEN_CONFIG["SECRET_KEY"], algorithms=TOKEN_CONFIG["ALGORITHM"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
