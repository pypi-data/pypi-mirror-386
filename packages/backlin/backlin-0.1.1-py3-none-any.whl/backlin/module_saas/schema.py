from typing import Optional
import uuid

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from decimal import Decimal

from backlin.database import Base
from backlin.crud.crud_mixin import (
    ManageMixin,
    IdentityMixin,
    ManageMixinModel,
    IdentityMixinModel,
    OrmConfig,
)


class ApiKey(Base, ManageMixin, IdentityMixin):
    __tablename__ = "sys_api_key"
    key = Column(String, index=True, default=lambda: f"sk-{str(uuid.uuid4().hex)}", comment="Secret Key")
    auth_key = Column(String, nullable=False, comment="Auth Key")
    is_active = Column(Boolean, default=True, comment="Active or not")

    # 统计字段（仅用于记录消耗）
    total_usage = Column(Float, default=0.0, comment="累计使用金额（人民币）")
    total_tokens = Column(Integer, default=0, comment="累计使用 tokens")

    # 关系（仅关联使用记录，不关联充值记录）
    usages = relationship("Usage", back_populates="api_key", cascade="all, delete-orphan")


class ApiKeyModel(BaseModel, OrmConfig, ManageMixinModel, IdentityMixinModel):
    key: Optional[str] = None
    is_active: Optional[bool] = None
    total_usage: Optional[float] = None
    total_tokens: Optional[int] = None


class ApiKeyCreationModel(ApiKeyModel):
    auth_key: Optional[str] = None


class Billing(Base, ManageMixin, IdentityMixin):
    __tablename__ = "sys_billing"
    user_id = Column(Integer, ForeignKey("sys_user.user_id", ondelete="CASCADE"), nullable=False, index=True, comment="用户 ID")
    amount = Column(Float, nullable=False, comment="充值金额（人民币）")
    status = Column(String, default="待支付", comment="支付状态：待支付、已支付、已取消、已退款")
    order_no = Column(String, unique=True, index=True, comment="订单号")
    payment_method = Column(String, nullable=True, comment="支付方式：微信、支付宝、银行卡等")
    payment_time = Column(DateTime, nullable=True, comment="支付时间")
    remark = Column(Text, nullable=True, comment="备注")


class BillingModel(BaseModel, OrmConfig, ManageMixinModel, IdentityMixinModel):
    user_id: Optional[int] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    order_no: Optional[str] = None
    payment_method: Optional[str] = None
    payment_time: Optional[str] = None
    remark: Optional[str] = None


# 新增：API 使用记录表
class Usage(Base, ManageMixin, IdentityMixin):
    __tablename__ = "sys_usage"
    api_key_id = Column(Integer, ForeignKey("sys_api_key.item_id", ondelete="CASCADE"), nullable=False, index=True, comment="API Key ID")
    model = Column(String, nullable=True, comment="使用的模型")
    prompt_tokens = Column(Integer, default=0, comment="输入 tokens")
    completion_tokens = Column(Integer, default=0, comment="输出 tokens")
    total_tokens = Column(Integer, default=0, comment="总 tokens")
    cost = Column(Float, default=0.0, comment="本次调用费用（人民币）")
    request_path = Column(String, nullable=True, comment="请求路径")
    request_method = Column(String, nullable=True, comment="请求方法")
    status_code = Column(Integer, nullable=True, comment="响应状态码")
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 关系
    api_key = relationship("ApiKey", back_populates="usages")


class UsageModel(BaseModel, OrmConfig, ManageMixinModel, IdentityMixinModel):
    api_key_id: Optional[int] = None
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: Optional[float] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
