import json
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query, Request
from fastapi.responses import HTMLResponse
import datetime
from datetime import timedelta
from loguru import logger
import requests
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from pydantic import BaseModel
from backlin.crud.crud_mixin import OrmConfig
from backlin.crud.crud_route import SuccessResponse
from backlin.database import get_db
from backlin.module_admin.entity.vo.user_vo import CurrentUserInfoServiceResponse
from backlin.module_admin.service.login_service import get_current_user
from backlin.module_saas.api_require import api_key_required, api_key_required_simple
from backlin.module_saas import schema as saas_schema
from backlin.module_saas.billing_utils import get_usage_stats, recharge_balance
from backlin.middleware.billing import manual_record_usage
from backlin.utils.response_util import response_200


app = APIRouter(prefix="/api/v1", tags=["API V1"])


class UsageStatsResponse(BaseModel, OrmConfig):
    """使用量统计响应"""
    user_balance: float  # 用户余额
    total_usage: float  # 累计使用金额
    total_tokens: int  # 累计使用 tokens
    total_requests: int  # 总请求数
    avg_cost: float  # 平均每次请求费用
    by_model: List[Dict]  # 按模型统计
    by_api_key: Optional[List[Dict]] = None  # 按 API Key 统计（用户级别查询时返回）


class RechargeRequest(BaseModel):
    """充值请求"""
    amount: float
    payment_method: Optional[str] = None
    remark: Optional[str] = None


class RecordUsageRequest(BaseModel):
    """手动记录使用量请求"""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: Optional[int] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    status_code: Optional[int] = 200
    error_message: Optional[str] = None


@app.get(
    "/usage/stats",
    response_model=SuccessResponse[UsageStatsResponse],
    summary="获取使用量统计"
)
def get_usage_statistics(
    request: Request,
    days: int = Query(30, description="统计天数", ge=1, le=365),
    api_key_id: Optional[int] = Query(None, description="API Key ID（可选，不传则返回用户整体统计）"),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取使用量统计信息

    - **days**: 统计天数（1-365）
    - **api_key_id**: API Key ID（可选，不传则返回用户所有 API Key 的整体统计）
    """
    user_id = current_user.user.user_id

    # 获取统计数据
    if api_key_id:
        # 单个 API Key 统计
        stats = get_usage_stats(db, api_key_id=api_key_id, days=days)
    else:
        # 用户整体统计
        stats = get_usage_stats(db, user_id=user_id, days=days)

    # 组合响应数据
    response_data = UsageStatsResponse(
        user_balance=stats.get("user_balance", 0.0),
        total_usage=stats["total_cost"],
        total_tokens=stats["total_tokens"],
        total_requests=stats["total_requests"],
        avg_cost=stats["avg_cost"],
        by_model=stats["by_model"],
        by_api_key=stats.get("by_api_key")
    )

    return response_200(data=response_data, message="获取成功")


@app.get(
    "/usage/history",
    response_model=SuccessResponse[List[saas_schema.UsageModel]],
    summary="获取使用历史"
)
def get_usage_history(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_info: dict = Depends(api_key_required),
    db: Session = Depends(get_db),
):
    """
    获取 API Key 的使用历史记录

    - **page**: 页码
    - **page_size**: 每页数量
    """
    api_key = user_info["api_key"]

    # 查询使用记录
    query = db.query(saas_schema.Usage).filter(
        saas_schema.Usage.api_key_id == api_key.id
    ).order_by(saas_schema.Usage.create_time.desc())

    # 分页
    total = query.count()
    usages = query.offset((page - 1) * page_size).limit(page_size).all()

    return response_200(
        data={
            "items": usages,
            "total": total,
            "page": page,
            "page_size": page_size
        },
        message="获取成功"
    )


@app.post(
    "/usage/record",
    response_model=SuccessResponse,
    summary="手动记录使用量"
)
def record_usage(
    request: Request,
    usage_data: RecordUsageRequest,
    user_info: dict = Depends(api_key_required),
    db: Session = Depends(get_db),
):
    """
    手动记录 API 使用量并扣费

    用于在无法自动拦截的场景下手动记录使用量
    """
    api_key = user_info["api_key"]

    # 记录使用量
    result = manual_record_usage(db, api_key, usage_data.model_dump())

    if result["success"]:
        return response_200(data=result, message="记录成功")
    else:
        raise HTTPException(status_code=500, detail=result["error"])


@app.post(
    "/billing/recharge",
    response_model=SuccessResponse,
    summary="充值余额"
)
def recharge(
    recharge_req: RechargeRequest,
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    为用户账户充值余额（直接充值到用户账户，不关联 API Key）

    - **amount**: 充值金额
    - **payment_method**: 支付方式
    - **remark**: 备注
    """
    user_id = current_user.user.user_id

    # 充值
    import uuid
    order_no = f"RCG{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    # 创建充值记录（直接充值到用户账户）
    billing = saas_schema.Billing(
        user_id=user_id,
        amount=recharge_req.amount,
        status="已支付",  # 这里简化处理，实际应该先创建待支付订单，支付成功后再更新
        order_no=order_no,
        payment_method=recharge_req.payment_method,
        payment_time=datetime.datetime.now(),
        remark=recharge_req.remark,
        create_by=current_user.user.user_name
    )
    db.add(billing)

    # 更新用户余额
    updated_user = recharge_balance(
        db=db,
        user_id=user_id,
        amount=recharge_req.amount,
        order_no=order_no,
        payment_method=recharge_req.payment_method,
        remark=recharge_req.remark,
        api_key_id=None  # 不关联 API Key
    )

    return response_200(
        data={
            "user_id": user_id,
            "balance": updated_user.balance / 100.0,  # 转换为元
            "order_no": order_no
        },
        message="充值成功"
    )


@app.get(
    "/billing/history",
    response_model=SuccessResponse,
    summary="获取充值历史"
)
def get_billing_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取用户的充值历史
    """
    user_id = current_user.user.user_id

    # 查询充值记录
    query = db.query(saas_schema.Billing).filter(
        saas_schema.Billing.user_id == user_id
    ).order_by(saas_schema.Billing.create_time.desc())

    total = query.count()
    billings = query.offset((page - 1) * page_size).limit(page_size).all()

    return response_200(
        data={
            "items": billings,
            "total": total,
            "page": page,
            "page_size": page_size
        },
        message="获取成功"
    )


@app.get("/dashboard")
def dashboard(
    user_info=Depends(api_key_required_simple),
    db: Session = Depends(get_db),
):
    """API 使用面板（待实现）"""
    pass
