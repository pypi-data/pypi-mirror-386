"""
计费中间件
自动记录 API 使用量并扣费
"""
import json
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from loguru import logger

from backlin.database import get_db
from backlin.module_saas.schema import ApiKey
from backlin.module_admin.entity.do.user_do import SysUser
from backlin.module_saas.billing_utils import calculate_cost, deduct_balance


class BillingMiddleware(BaseHTTPMiddleware):
    """
    计费中间件
    拦截 API 请求，在响应后自动记录使用量并扣费
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 只处理特定路径的请求（例如 OpenAI API 相关）
        if not self._should_bill(request.url.path):
            return await call_next(request)

        # 获取 API Key
        api_key = getattr(request.state, "api_key", None)
        if not api_key:
            # 如果没有 API Key，继续执行但不计费
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        # 执行请求
        response = await call_next(request)

        # 计算耗时
        duration = time.time() - start_time

        # 异步记录计费信息
        # 注意：这里需要在后台任务中处理，避免阻塞响应
        request.app.state.background_tasks = request.app.state.background_tasks or []

        # 如果响应是成功的，尝试从响应体中提取 token 使用量
        if response.status_code == 200:
            # 这里需要根据实际的响应格式提取 token 信息
            # 由于我们需要读取响应体，可能需要特殊处理
            pass

        return response

    def _should_bill(self, path: str) -> bool:
        """
        判断是否需要计费

        Args:
            path: 请求路径

        Returns:
            是否需要计费
        """
        # 定义需要计费的路径前缀
        billable_paths = [
            "/api/v1/chat/completions",
            "/api/v1/completions",
            "/api/v1/embeddings",
            "/openai/v1/chat/completions",
            "/openai/v1/completions",
            "/openai/v1/embeddings",
        ]

        return any(path.startswith(prefix) for prefix in billable_paths)


async def record_usage_background(
    api_key_id: int,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    request_path: str,
    request_method: str,
    status_code: int,
    error_message: str = None
):
    """
    后台任务：记录使用量并扣费

    Args:
        api_key_id: API Key ID
        model: 模型名称
        prompt_tokens: 输入 tokens
        completion_tokens: 输出 tokens
        total_tokens: 总 tokens
        request_path: 请求路径
        request_method: 请求方法
        status_code: 响应状态码
        error_message: 错误信息
    """
    try:
        # 获取数据库会话
        for db in get_db():
            # 查询 API Key
            api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
            if not api_key:
                logger.error(f"API Key {api_key_id} 不存在")
                return

            # 计算费用
            cost = calculate_cost(model, prompt_tokens, completion_tokens)

            # 扣费并记录
            deduct_balance(
                db=db,
                api_key=api_key,
                cost=cost,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_path=request_path,
                request_method=request_method,
                status_code=status_code,
                error_message=error_message
            )

            logger.info(f"成功记录 API Key {api_key_id} 的使用量并扣费")

    except Exception as e:
        logger.error(f"记录使用量失败: {str(e)}")


def manual_record_usage(
    db: Session,
    api_key: ApiKey,
    usage_data: dict
) -> dict:
    """
    手动记录使用量（用于从响应中提取 token 信息后调用）

    Args:
        db: 数据库会话
        api_key: API Key 对象
        usage_data: 使用量数据，包含 model, prompt_tokens, completion_tokens 等

    Returns:
        记录结果
    """
    try:
        model = usage_data.get("model", "unknown")
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", prompt_tokens + completion_tokens)

        # 计算费用
        cost = calculate_cost(model, prompt_tokens, completion_tokens)

        # 扣费并记录
        usage = deduct_balance(
            db=db,
            api_key=api_key,
            cost=cost,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            request_path=usage_data.get("request_path"),
            request_method=usage_data.get("request_method"),
            status_code=usage_data.get("status_code", 200),
            error_message=usage_data.get("error_message")
        )

        # 获取用户余额
        user = db.query(SysUser).filter(SysUser.user_id == api_key.create_by_id).first()
        user_balance = (user.balance / 100.0) if user else 0.0

        return {
            "success": True,
            "usage_id": usage.item_id,
            "cost": cost,
            "remaining_balance": user_balance  # 返回用户余额（元）
        }

    except Exception as e:
        logger.error(f"手动记录使用量失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
