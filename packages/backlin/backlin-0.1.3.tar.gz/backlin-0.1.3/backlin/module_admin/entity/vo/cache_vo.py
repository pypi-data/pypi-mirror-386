from pydantic import BaseModel
from typing import Optional, List, Any


class CacheMonitorModel(BaseModel):
    """
    缓存监控信息对应pydantic模型
    """
    command_stats: Optional[List] = None
    db_size: Optional[int] = None
    info: Optional[dict] = None


class CacheInfoModel(BaseModel):
    """
    缓存监控对象对应pydantic模型
    """
    cache_key: Optional[str] = None
    cache_name: Optional[str] = None
    cache_value: Optional[Any] = None
    remark: Optional[str] = None


class CrudCacheResponse(BaseModel):
    """
    操作缓存响应模型
    """
    is_success: bool
    message: str
