"""
API 使用量计费工具模块
提供计费计算、余额扣费、使用记录等功能
"""
from typing import Optional, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from loguru import logger

from backlin.module_saas.schema import ApiKey, Usage
from backlin.module_admin.entity.do.user_do import SysUser


# 价格配置（单位：人民币/1K tokens）
PRICING = {
    "gpt-4": {
        "prompt": 0.21,  # ¥0.21/1K prompt tokens
        "completion": 0.42,  # ¥0.42/1K completion tokens
    },
    "gpt-4-turbo": {
        "prompt": 0.07,
        "completion": 0.14,
    },
    "gpt-3.5-turbo": {
        "prompt": 0.01,
        "completion": 0.02,
    },
    "text-embedding-ada-002": {
        "prompt": 0.0007,
        "completion": 0.0,
    },
    "default": {
        "prompt": 0.01,
        "completion": 0.02,
    }
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    计算本次 API 调用的费用

    Args:
        model: 模型名称
        prompt_tokens: 输入 tokens 数量
        completion_tokens: 输出 tokens 数量

    Returns:
        费用（人民币）
    """
    # 获取价格配置，如果模型不存在则使用默认价格
    pricing = PRICING.get(model, PRICING["default"])

    # 计算费用：(tokens / 1000) * 单价
    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]
    total_cost = prompt_cost + completion_cost

    # 保留 6 位小数
    return round(total_cost, 6)


def check_balance(db: Session, api_key: ApiKey, required_cost: float = 0.0) -> tuple[bool, str]:
    """
    检查用户余额是否充足

    Args:
        db: 数据库会话
        api_key: API Key 对象
        required_cost: 需要的费用

    Returns:
        (是否通过, 错误信息)
    """
    # 检查是否激活
    if not api_key.is_active:
        return False, "API Key 已被禁用"

    # 获取用户信息
    user = db.query(SysUser).filter(SysUser.user_id == api_key.create_by_id).first()
    if not user:
        return False, "用户不存在"

    # 将余额从分转换为元
    user_balance = user.balance / 100.0

    # 检查余额是否充足
    if user_balance < required_cost:
        return False, f"余额不足，当前余额: ¥{user_balance:.4f}"

    return True, ""


def deduct_balance(
    db: Session,
    api_key: ApiKey,
    cost: float,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    request_path: str = None,
    request_method: str = None,
    status_code: int = 200,
    error_message: str = None
) -> Usage:
    """
    从用户余额扣费，并记录到 API Key 的使用量统计

    Args:
        db: 数据库会话
        api_key: API Key 对象
        cost: 费用（元）
        model: 模型名称
        prompt_tokens: 输入 tokens
        completion_tokens: 输出 tokens
        total_tokens: 总 tokens
        request_path: 请求路径
        request_method: 请求方法
        status_code: 响应状态码
        error_message: 错误信息

    Returns:
        Usage 对象
    """
    try:
        # 获取用户信息
        user = db.query(SysUser).filter(SysUser.user_id == api_key.create_by_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 将费用转换为分
        cost_in_cents = int(cost * 100)

        # 从用户余额扣费
        user.balance -= cost_in_cents

        # 更新 API Key 的累计使用量统计
        api_key.total_usage += cost
        api_key.total_tokens += total_tokens

        # 创建使用记录
        usage = Usage(
            api_key_id=api_key.item_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            error_message=error_message,
        )

        db.add(usage)
        db.commit()
        db.refresh(user)
        db.refresh(api_key)
        db.refresh(usage)

        user_balance = user.balance / 100.0
        logger.info(
            f"API Key {api_key.item_id} 扣费成功: "
            f"模型={model}, tokens={total_tokens}, 费用=¥{cost:.6f}, "
            f"用户剩余余额=¥{user_balance:.4f}"
        )

        return usage

    except Exception as e:
        db.rollback()
        logger.error(f"扣费失败: {str(e)}")
        raise


def recharge_balance(
    db: Session,
    user_id: int,
    amount: float,
    order_no: str = None,
    payment_method: str = None,
    remark: str = None,
    api_key_id: int = None
) -> SysUser:
    """
    充值到用户余额池

    Args:
        db: 数据库会话
        user_id: 用户 ID
        amount: 充值金额（元）
        order_no: 订单号
        payment_method: 支付方式
        remark: 备注
        api_key_id: API Key ID（可选，用于记录充值来源）

    Returns:
        更新后的用户对象
    """
    try:
        # 获取用户
        user = db.query(SysUser).filter(SysUser.user_id == user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 将金额转换为分
        amount_in_cents = int(amount * 100)

        # 更新余额
        user.balance += amount_in_cents

        db.commit()
        db.refresh(user)

        user_balance = user.balance / 100.0
        logger.info(
            f"用户 {user_id} 充值成功: "
            f"金额=¥{amount:.2f}, 当前余额=¥{user_balance:.4f}"
        )

        return user

    except Exception as e:
        db.rollback()
        logger.error(f"充值失败: {str(e)}")
        raise


def get_usage_stats(db: Session, user_id: int = None, api_key_id: int = None, days: int = 30) -> Dict:
    """
    获取使用量统计

    Args:
        db: 数据库会话
        user_id: 用户 ID（获取用户整体统计）
        api_key_id: API Key ID（获取单个 key 的统计）
        days: 统计天数

    Returns:
        统计数据字典
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func

    start_date = datetime.now() - timedelta(days=days)

    # 构建查询条件
    query_filter = [Usage.create_time >= start_date]

    if api_key_id:
        query_filter.append(Usage.api_key_id == api_key_id)
    elif user_id:
        # 查询用户的所有 API Keys
        api_keys = db.query(ApiKey.item_id).filter(ApiKey.create_by_id == user_id).all()
        api_key_ids = [k.item_id for k in api_keys]
        if not api_key_ids:
            return {
                "user_balance": 0.0,
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_cost": 0.0,
                "by_model": [],
                "by_api_key": []
            }
        query_filter.append(Usage.api_key_id.in_(api_key_ids))

    # 查询统计数据
    stats = db.query(
        func.count(Usage.item_id).label("total_requests"),
        func.sum(Usage.total_tokens).label("total_tokens"),
        func.sum(Usage.cost).label("total_cost"),
        func.avg(Usage.cost).label("avg_cost"),
    ).filter(*query_filter).first()

    # 按模型分组统计
    model_stats = db.query(
        Usage.model,
        func.count(Usage.item_id).label("count"),
        func.sum(Usage.total_tokens).label("tokens"),
        func.sum(Usage.cost).label("cost"),
    ).filter(*query_filter).group_by(Usage.model).all()

    result = {
        "total_requests": stats.total_requests or 0,
        "total_tokens": stats.total_tokens or 0,
        "total_cost": float(stats.total_cost or 0),
        "avg_cost": float(stats.avg_cost or 0),
        "by_model": [
            {
                "model": m.model,
                "count": m.count,
                "tokens": m.tokens,
                "cost": float(m.cost)
            }
            for m in model_stats
        ]
    }

    # 如果查询用户统计，添加用户余额和各 API Key 的统计
    if user_id:
        user = db.query(SysUser).filter(SysUser.user_id == user_id).first()
        result["user_balance"] = user.balance / 100.0 if user else 0.0

        # 按 API Key 分组统计
        api_key_stats = db.query(
            ApiKey.item_id,
            ApiKey.key,
            func.sum(Usage.total_tokens).label("tokens"),
            func.sum(Usage.cost).label("cost"),
        ).join(Usage, ApiKey.item_id == Usage.api_key_id)\
         .filter(ApiKey.create_by_id == user_id, Usage.create_time >= start_date)\
         .group_by(ApiKey.item_id, ApiKey.key).all()

        result["by_api_key"] = [
            {
                "api_key_id": k.item_id,
                "key": k.key,
                "tokens": k.tokens or 0,
                "cost": float(k.cost or 0)
            }
            for k in api_key_stats
        ]

    return result
