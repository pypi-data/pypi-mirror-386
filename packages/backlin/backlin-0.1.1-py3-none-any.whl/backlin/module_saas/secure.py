import jwt
from fastapi import HTTPException, status

from backlin.config.env import JwtConfig


def create_auth_key(user_id: int):
    payload = {
        "user_id": user_id,
    }
    token = jwt.encode(payload, JwtConfig.jwt_secret_key, algorithm=JwtConfig.jwt_algorithm)
    return token


def decode_auth_key(token: str):
    try:
        print(token)
        payload = jwt.decode(token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm])
        print(payload)
        user_id: int = payload.get("user_id")
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

