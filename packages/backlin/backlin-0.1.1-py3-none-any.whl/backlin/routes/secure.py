from typing import Dict, Any
import datetime

import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backlin.config.env import JwtConfig
from backlin.database import get_db


def encode(json: Dict[str, Any]) -> str:
    encoded = jwt.encode(json, JwtConfig.jwt_secret_key, algorithm="HS256")
    return encoded


def decode(code: str) -> Dict[str, Any]:
    try:
        decoded = jwt.decode(code, JwtConfig.jwt_secret_key, algorithms=["HS256"])
        return decoded
    except jwt.InvalidTokenError:
        # Handle invalid token
        return {}


def decode_function_call(code: str):
    decoded_json = decode(code)
    function_name = decoded_json["function"]
    args = decoded_json["args"]
    return function_name, args


def encode_function_call(function_name: str, args: dict):
    function_call = {
        "function": function_name,
        "args": args,
    }
    encoded_code = encode(function_call)
    return encoded_code


def create_auth_key(user_id: int):
    payload = {
        "user_id": user_id,
    }
    token = jwt.encode(payload, JwtConfig.jwt_secret_key, algorithm=JwtConfig.jwt_algorithm)
    return token


def create_access_token(user_id, group):
    expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=JwtConfig.jwt_expire_minutes)
    payload = {
        "user_id": user_id,
        "group": group,
        "exp": expiry,
    }
    token = jwt.encode(payload, JwtConfig.jwt_secret_key, algorithm=JwtConfig.jwt_algorithm)
    return token


def decode_access_token(token: str):
    try:
        print(token)
        payload = jwt.decode(token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm])
        print(payload)
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


bearer_scheme = HTTPBearer()

# JWT required decorator
def jwt_required(token: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session=Depends(get_db)):
    print("checking jwt_required")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    credentials = token.credentials
    if isinstance(credentials, str) and credentials.startswith("Bearer "):
        credentials = credentials.split("Bearer ")[1]
    decoded_token = decode_access_token(credentials)
    return decoded_token