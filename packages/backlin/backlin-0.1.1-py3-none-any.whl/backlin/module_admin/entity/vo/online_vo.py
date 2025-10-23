from pydantic import BaseModel
from typing import Union, Optional, List


class OnlineModel(BaseModel):
    """
    在线用户对应pydantic模型
    """
    session_id: Optional[str] = None
    user_name: Optional[str] = None
    dept_name: Optional[str] = None
    ipaddr: Optional[str] = None
    login_location: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    login_time: Optional[str] = None


class OnlinePageObject(OnlineModel):
    """
    在线用户分页查询模型
    """
    page_num: int
    page_size: int


class OnlinePageObjectResponse(BaseModel):
    """
    在线用户列表分页查询返回模型
    """
    rows: List[Union[OnlineModel, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class CrudOnlineResponse(BaseModel):
    """
    操作在线用户响应模型
    """
    is_success: bool
    message: str


class DeleteOnlineModel(BaseModel):
    """
    强退在线用户模型
    """
    session_ids: str
