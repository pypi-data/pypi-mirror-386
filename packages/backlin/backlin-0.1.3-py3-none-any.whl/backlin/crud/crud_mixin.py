from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, Boolean, JSON, String, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY


class ManageMixin:
    create_by = Column(String(64), nullable=True, default="", comment="创建者")
    create_time = Column(DateTime, nullable=True, server_default=func.now(), comment="创建时间")
    update_by = Column(String(64), nullable=True, default="", comment="更新者")
    update_time = Column(DateTime, nullable=True, server_default=func.now(), comment="更新时间", onupdate=datetime.now)


class SoftManageMixin(ManageMixin):
    status = Column(Integer, nullable=True, default=0, comment="状态（0正常 1停用）")
    del_flag = Column(Integer, nullable=True, default=0, comment="删除标志（0代表存在 2代表删除）")


class IdentityMixin:
    item_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="数据id")
    name = Column(String, nullable=True, default="", comment="名称")
    order_num = Column(Integer, default=0, comment="显示顺序")


class TreeMixin(IdentityMixin):
    parent_id = Column(Integer, default=0, comment="父id")
    ancestors = Column(ARRAY(Integer), nullable=True, default=[], comment="祖级列表")


class ManageMixinModel(object):
    create_by: Optional[str] = None
    create_time: Optional[datetime] = None
    update_by: Optional[str] = None
    update_time: Optional[datetime] = None


class SoftManageMixinModel(ManageMixinModel):
    status: Optional[int] = None
    del_flag: Optional[int] = None


class IdentityMixinModel(object):
    item_id: Optional[int] = None
    name: Optional[str] = None
    order_num: Optional[int] = None


class TreeMixinModel(IdentityMixinModel):
    parent_id: Optional[int] = None
    ancestors: Optional[List[int]] = None


# 定义模型配置，启用 `from_attributes`
class OrmConfig:
    model_config = ConfigDict(from_attributes=True)


class PageObject(object):
    """
    分页查询模型
    """

    page_num: int
    page_size: int
