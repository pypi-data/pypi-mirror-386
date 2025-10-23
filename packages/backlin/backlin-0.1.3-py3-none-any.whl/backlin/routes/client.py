import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from fastapi.responses import HTMLResponse
import datetime
from datetime import timedelta
from loguru import logger
import requests
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import and_, extract
from pydantic import BaseModel

from backlin.database import get_db
from backlin.module_admin.entity.vo.user_vo import CurrentUserInfoServiceResponse
from backlin.module_admin.service.login_service import get_current_user
from backlin.module_admin.entity.do.user_do import SysUser
from backlin.module_saas.schema import ApiKey, Usage, Billing
from backlin.crud.crud_route import SuccessResponse
from backlin.utils.response_util import response_200


NOW = datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=8)

app = APIRouter(prefix="/client", tags=["client"])


# ==================== 响应模型 ====================

class UsageStatisticsModel(BaseModel):
    """使用统计模型"""
    topup_balance: float  # 充值余额
    granted_balance: float  # 赠送余额（未来功能）
    monthly_expenses: float  # 本月开销
    available_tokens: int  # 可用 tokens（基于余额估算）

    class Config:
        from_attributes = True


class DailyUsageModel(BaseModel):
    """每日使用统计模型"""
    date: str  # 日期 YYYY-MM-DD
    api_requests: int  # API 请求次数
    total_tokens: int  # 总 tokens
    total_cost: float  # 总费用

    class Config:
        from_attributes = True


class ModelUsageModel(BaseModel):
    """模型使用统计"""
    model: str  # 模型名称
    api_requests: int  # API 请求次数
    total_tokens: int  # 总 tokens
    total_cost: float  # 总费用

    class Config:
        from_attributes = True


class UsageDetailResponse(BaseModel):
    """使用详情响应"""
    statistics: UsageStatisticsModel  # 统计信息
    daily_usage: List[DailyUsageModel]  # 每日使用情况
    model_usage: List[ModelUsageModel]  # 按模型统计

    class Config:
        from_attributes = True


# ==================== API 端点 ====================

@app.get(
    "/usage/statistics",
    response_model=SuccessResponse[UsageStatisticsModel],
    summary="获取客户端使用统计",
)
def get_usage_statistics(
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的使用统计信息

    包括：
    - 充值余额
    - 赠送余额（当前为0，未来功能）
    - 本月开销
    - 可用 tokens 估算
    """
    user_id = current_user.user.user_id

    # 获取用户余额
    user = db.query(SysUser).filter(SysUser.user_id == user_id).first()
    total_balance = (user.balance / 100.0) if user and user.balance else 0.0

    # 获取用户的所有 API Keys
    api_keys = db.query(ApiKey).filter(
        ApiKey.create_by == current_user.user.user_name
    ).all()

    if not api_keys:
        # 如果用户没有 API Key，返回空数据
        statistics = UsageStatisticsModel(
            topup_balance=total_balance,
            granted_balance=0.0,
            monthly_expenses=0.0,
            available_tokens=0
        )
        return response_200(data=statistics, message="获取成功")

    api_key_ids = [key.item_id for key in api_keys]

    # 计算本月开销（当前月份的所有使用记录）
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month

    monthly_cost = db.query(func.sum(Usage.cost)).filter(
        and_(
            Usage.api_key_id.in_(api_key_ids),
            extract('year', Usage.create_time) == current_year,
            extract('month', Usage.create_time) == current_month
        )
    ).scalar() or 0.0

    # 估算可用 tokens（假设平均每 1000 tokens 消耗 0.01 元）
    avg_cost_per_1k_tokens = 0.01
    available_tokens = int(total_balance / avg_cost_per_1k_tokens * 1000)

    statistics = UsageStatisticsModel(
        topup_balance=round(total_balance, 2),
        granted_balance=0.0,  # 未来功能
        monthly_expenses=round(monthly_cost, 2),
        available_tokens=available_tokens
    )

    return response_200(data=statistics, message="获取成功")


@app.get(
    "/usage/daily",
    response_model=SuccessResponse[List[DailyUsageModel]],
    summary="获取每日使用统计",
)
def get_daily_usage(
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份 (1-12)"),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取指定月份的每日使用统计

    Args:
        year: 年份
        month: 月份 (1-12)

    Returns:
        每日使用统计列表
    """
    # 获取用户的所有 API Keys
    api_keys = db.query(ApiKey).filter(
        ApiKey.create_by == current_user.user.user_name
    ).all()

    if not api_keys:
        return response_200(data=[], message="获取成功")

    api_key_ids = [key.item_id for key in api_keys]

    # 查询该月的所有使用记录，按日期分组
    daily_stats = db.query(
        func.date(Usage.create_time).label('date'),
        func.count(Usage.item_id).label('api_requests'),
        func.sum(Usage.total_tokens).label('total_tokens'),
        func.sum(Usage.cost).label('total_cost')
    ).filter(
        and_(
            Usage.api_key_id.in_(api_key_ids),
            extract('year', Usage.create_time) == year,
            extract('month', Usage.create_time) == month
        )
    ).group_by(
        func.date(Usage.create_time)
    ).order_by(
        func.date(Usage.create_time)
    ).all()

    # 转换为响应模型
    daily_usage = []
    for stat in daily_stats:
        daily_usage.append(DailyUsageModel(
            date=stat.date.strftime('%Y-%m-%d') if stat.date else '',
            api_requests=stat.api_requests or 0,
            total_tokens=stat.total_tokens or 0,
            total_cost=round(stat.total_cost or 0.0, 4)
        ))

    return response_200(data=daily_usage, message="获取成功")


@app.get(
    "/usage/by-model",
    response_model=SuccessResponse[List[ModelUsageModel]],
    summary="获取按模型分组的使用统计",
)
def get_usage_by_model(
    year: int = Query(..., description="年份"),
    month: int = Query(..., description="月份 (1-12)"),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取指定月份按模型分组的使用统计

    Args:
        year: 年份
        month: 月份 (1-12)

    Returns:
        按模型分组的使用统计列表
    """
    # 获取用户的所有 API Keys
    api_keys = db.query(ApiKey).filter(
        ApiKey.create_by == current_user.user.user_name
    ).all()

    if not api_keys:
        return response_200(data=[], message="获取成功")

    api_key_ids = [key.item_id for key in api_keys]

    # 查询该月的所有使用记录，按模型分组
    model_stats = db.query(
        Usage.model,
        func.count(Usage.item_id).label('api_requests'),
        func.sum(Usage.total_tokens).label('total_tokens'),
        func.sum(Usage.cost).label('total_cost')
    ).filter(
        and_(
            Usage.api_key_id.in_(api_key_ids),
            extract('year', Usage.create_time) == year,
            extract('month', Usage.create_time) == month
        )
    ).group_by(
        Usage.model
    ).order_by(
        func.sum(Usage.cost).desc()
    ).all()

    # 转换为响应模型
    model_usage = []
    for stat in model_stats:
        model_usage.append(ModelUsageModel(
            model=stat.model or 'unknown',
            api_requests=stat.api_requests or 0,
            total_tokens=stat.total_tokens or 0,
            total_cost=round(stat.total_cost or 0.0, 4)
        ))

    return response_200(data=model_usage, message="获取成功")


@app.get(
    "/usage/detail",
    response_model=SuccessResponse[UsageDetailResponse],
    summary="获取使用详情（综合接口）",
)
def get_usage_detail(
    year: Optional[int] = Query(None, description="年份，默认当前年"),
    month: Optional[int] = Query(None, description="月份 (1-12)，默认当前月"),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取使用详情综合信息

    包括：
    - 统计信息（余额、本月开销等）
    - 每日使用情况
    - 按模型统计

    Args:
        year: 年份，默认当前年
        month: 月份，默认当前月

    Returns:
        使用详情综合信息
    """
    # 使用当前年月作为默认值
    if year is None:
        year = datetime.datetime.now().year
    if month is None:
        month = datetime.datetime.now().month

    user_id = current_user.user.user_id

    # 获取用户余额
    user = db.query(SysUser).filter(SysUser.user_id == user_id).first()
    total_balance = (user.balance / 100.0) if user and user.balance else 0.0

    # 获取用户的所有 API Keys
    api_keys = db.query(ApiKey).filter(
        ApiKey.create_by == current_user.user.user_name
    ).all()

    if not api_keys:
        # 返回空数据
        statistics = UsageStatisticsModel(
            topup_balance=total_balance,
            granted_balance=0.0,
            monthly_expenses=0.0,
            available_tokens=0
        )
        detail_response = UsageDetailResponse(
            statistics=statistics,
            daily_usage=[],
            model_usage=[]
        )
        return response_200(data=detail_response, message="获取成功")

    api_key_ids = [key.item_id for key in api_keys]

    # 1. 获取统计信息

    monthly_cost = db.query(func.sum(Usage.cost)).filter(
        and_(
            Usage.api_key_id.in_(api_key_ids),
            extract('year', Usage.create_time) == year,
            extract('month', Usage.create_time) == month
        )
    ).scalar() or 0.0

    avg_cost_per_1k_tokens = 0.01
    available_tokens = int(total_balance / avg_cost_per_1k_tokens * 1000)

    statistics = UsageStatisticsModel(
        topup_balance=round(total_balance, 2),
        granted_balance=0.0,
        monthly_expenses=round(monthly_cost, 2),
        available_tokens=available_tokens
    )

    # 2. 获取每日使用统计
    daily_stats = db.query(
        func.date(Usage.create_time).label('date'),
        func.count(Usage.item_id).label('api_requests'),
        func.sum(Usage.total_tokens).label('total_tokens'),
        func.sum(Usage.cost).label('total_cost')
    ).filter(
        and_(
            Usage.api_key_id.in_(api_key_ids),
            extract('year', Usage.create_time) == year,
            extract('month', Usage.create_time) == month
        )
    ).group_by(
        func.date(Usage.create_time)
    ).order_by(
        func.date(Usage.create_time)
    ).all()

    daily_usage = []
    for stat in daily_stats:
        daily_usage.append(DailyUsageModel(
            date=stat.date.strftime('%Y-%m-%d') if stat.date else '',
            api_requests=stat.api_requests or 0,
            total_tokens=stat.total_tokens or 0,
            total_cost=round(stat.total_cost or 0.0, 4)
        ))

    # 3. 获取按模型统计
    model_stats = db.query(
        Usage.model,
        func.count(Usage.item_id).label('api_requests'),
        func.sum(Usage.total_tokens).label('total_tokens'),
        func.sum(Usage.cost).label('total_cost')
    ).filter(
        and_(
            Usage.api_key_id.in_(api_key_ids),
            extract('year', Usage.create_time) == year,
            extract('month', Usage.create_time) == month
        )
    ).group_by(
        Usage.model
    ).order_by(
        func.sum(Usage.cost).desc()
    ).all()

    model_usage = []
    for stat in model_stats:
        model_usage.append(ModelUsageModel(
            model=stat.model or 'unknown',
            api_requests=stat.api_requests or 0,
            total_tokens=stat.total_tokens or 0,
            total_cost=round(stat.total_cost or 0.0, 4)
        ))

    # 组装响应
    detail_response = UsageDetailResponse(
        statistics=statistics,
        daily_usage=daily_usage,
        model_usage=model_usage
    )

    return response_200(data=detail_response, message="获取成功")

