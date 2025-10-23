from pydantic import BaseModel
from typing import Optional


class UserLogin(BaseModel):
    user_name: str
    password: str
    captcha: Optional[str] = None
    session_id: Optional[str] = None
    login_info: Optional[dict] = None
    captcha_enabled: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class SmsCode(BaseModel):
    is_success: Optional[bool] = None
    sms_code: str
    session_id: str
    message: Optional[str] = None
