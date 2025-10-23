from pydantic import BaseModel
from typing import Union, Optional, List


class NoticeModel(BaseModel):
    """
    通知公告表对应pydantic模型
    """
    notice_id: Optional[int] = None
    notice_title: Optional[str] = None
    notice_type: Optional[int] = None
    notice_content: Optional[str] = None
    status: Optional[int] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class NoticeQueryModel(NoticeModel):
    """
    通知公告管理不分页查询模型
    """
    create_time_start: Optional[str] = None
    create_time_end: Optional[str] = None


class NoticePageObject(NoticeQueryModel):
    """
    通知公告管理分页查询模型
    """
    page_num: int
    page_size: int


class NoticePageObjectResponse(BaseModel):
    """
    通知公告管理列表分页查询返回模型
    """
    rows: List[Union[NoticeModel, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool

    class Config:
        from_attributes = True

class CrudNoticeResponse(BaseModel):
    """
    操作通知公告响应模型
    """
    is_success: bool
    message: str


class DeleteNoticeModel(BaseModel):
    """
    删除通知公告模型
    """
    notice_ids: str
