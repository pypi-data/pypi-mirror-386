import jwt
from fastapi import Depends, Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from backlin.database import get_db
from sqlalchemy.orm import Session
from loguru import logger

from backlin.config.env import JwtConfig
from backlin.module_admin.dao.user_dao import UserDao
from backlin.module_saas import schema as saas_schema
from backlin.module_saas import secure as saas_secure
from backlin.module_saas.billing_utils import check_balance
from backlin.utils.response_util import AuthException


api_key_header = APIKeyHeader(name="X-API-Key")


def api_key_required(
    request: Request,
    key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """
    API Key 验证，包含余额和配额检查

    Args:
        request: FastAPI 请求对象
        key: API Key
        db: 数据库会话

    Returns:
        包含 user 和 api_key 的字典

    Raises:
        HTTPException: 验证失败
    """
    if isinstance(key, str) and key.startswith("sk-"):
        key = key.split("sk-")[1]
        api_key = db.query(saas_schema.ApiKey).where(saas_schema.ApiKey.key == key).first()
        if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

        # 检查余额和配额
        is_valid, error_msg = check_balance(db, api_key)
        if not is_valid:
            logger.warning(f"API Key {api_key.item_id} 验证失败: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=error_msg
            )

        auth_key = api_key.auth_key
        user_id = saas_secure.decode_auth_key(auth_key)
        if user_id is None:
            logger.warning("用户token不合法")
            raise AuthException(data="", message="用户token不合法")
        user = UserDao.get_user_by_id(db, user_id=user_id)
        if user is None:
            logger.warning("用户token不合法")
            raise AuthException(data="", message="用户token不合法")

        # 将 API Key 存储到 request.state 中，供后续使用
        request.state.api_key = api_key
        request.state.user = user

        return {
            "user": user,
            "api_key": api_key
        }
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")


def api_key_required_simple(key: str = Security(api_key_header), db: Session = Depends(get_db)):
    """
    简化版 API Key 验证（向后兼容，只返回 user）
    """
    if isinstance(key, str) and key.startswith("sk-"):
        key = key.split("sk-")[1]
        api_key = db.query(saas_schema.ApiKey).where(saas_schema.ApiKey.key == key).first()
        if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

        # 检查余额和配额
        is_valid, error_msg = check_balance(db, api_key)
        if not is_valid:
            logger.warning(f"API Key {api_key.item_id} 验证失败: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=error_msg
            )

        auth_key = api_key.auth_key
        user_id = saas_secure.decode_auth_key(auth_key)
        if user_id is None:
            logger.warning("用户token不合法")
            raise AuthException(data="", message="用户token不合法")
        user = UserDao.get_user_by_id(db, user_id=user_id)
        if user is None:
            logger.warning("用户token不合法")
            raise AuthException(data="", message="用户token不合法")
        return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")

