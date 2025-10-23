"""
订单相关路由
"""
import uuid
import random
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
from loguru import logger

from backlin.database import get_db, SessionLocal
from backlin.module_saas.schema import Billing, ApiKey
from backlin.module_admin.entity.do.user_do import SysUser
from backlin.module_admin.service.login_service import get_current_user
from backlin.module_admin.entity.vo.user_vo import CurrentUserInfoServiceResponse
from backlin.utils.response_util import response_200


router = APIRouter(prefix="/api/v1/order", tags=["订单"])


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    amount: float  # 充值金额
    payment_method: str  # 支付方式: 支付宝 or 微信支付


class CreateOrderResponse(BaseModel):
    """创建订单响应"""
    order_id: int  # 订单ID
    order_no: str  # 订单号
    amount: float  # 金额
    payment_url: str  # 支付URL (实际应该是支付宝/微信的支付页面URL)
    qr_code_url: str  # 二维码URL (用于展示给用户扫码支付)


class OrderStatusResponse(BaseModel):
    """订单状态响应"""
    order_id: int
    order_no: str
    status: str  # 待支付、已支付、已取消、已退款
    amount: float
    payment_method: str
    payment_time: Optional[str] = None
    remark: Optional[str] = None  # 备注信息（如支付超时等）


class PaymentCallbackRequest(BaseModel):
    """支付回调请求 (实际项目中需要根据支付平台的回调格式调整)"""
    order_no: str  # 订单号
    transaction_id: str  # 第三方交易号
    status: str  # 支付状态
    sign: str  # 签名 (用于验证回调的真实性)


@router.post("/create", summary="创建订单")
async def create_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
):
    """
    创建充值订单
    1. 验证金额范围 (1-10000)
    2. 创建订单记录
    3. 调用支付平台生成支付URL
    4. 返回订单信息和支付URL
    """
    # 验证金额
    if not 1 <= request.amount <= 10000:
        raise HTTPException(status_code=400, detail="充值金额必须在1-10000之间")

    # 验证支付方式
    if request.payment_method not in ["支付宝", "微信支付"]:
        raise HTTPException(status_code=400, detail="不支持的支付方式")

    # 生成订单号
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    # 获取用户ID（直接充值到用户账户）
    user_id = current_user.user.user_id

    logger.info(f"[订单创建] 准备创建订单 - 用户ID: {user_id}, 用户名: {current_user.user.user_name}")

    # 创建订单（充值直接到用户账户）
    billing = Billing(
        user_id=user_id,
        amount=request.amount,
        status="待支付",
        order_no=order_no,
        payment_method=request.payment_method,
        remark=f"用户充值 - {request.payment_method}",
    )
    db.add(billing)
    db.commit()
    db.refresh(billing)

    # 记录订单创建日志
    logger.info(
        f"[订单创建] 订单创建成功\n"
        f"  订单ID: {billing.item_id}\n"
        f"  订单号: {order_no}\n"
        f"  用户: {current_user.user.user_name}\n"
        f"  充值金额: ¥{request.amount}\n"
        f"  支付方式: {request.payment_method}\n"
        f"  订单状态: {billing.status}"
    )

    # TODO: 实际项目中需要调用支付宝/微信的API生成真实的支付URL
    # 这里先返回模拟的URL
    payment_url = generate_payment_url(order_no, request.amount, request.payment_method)
    qr_code_url = f"/api/v1/order/qrcode/{order_no}"

    response_data = CreateOrderResponse(
        order_id=billing.item_id,
        order_no=order_no,
        amount=request.amount,
        payment_url=payment_url,
        qr_code_url=qr_code_url,
    )

    return response_200(data=response_data.dict(), message="订单创建成功")


@router.get("/status/{order_no}", summary="查询订单状态")
async def get_order_status(
    order_no: str,
    db: Session = Depends(get_db),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
):
    """
    查询订单支付状态
    前端会定期轮询此接口来检查订单是否支付成功
    """
    # 查询订单
    billing = db.query(Billing).filter(Billing.order_no == order_no).first()

    if not billing:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 验证订单归属（通过 user_id）
    if billing.user_id != current_user.user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此订单")

    response_data = OrderStatusResponse(
        order_id=billing.item_id,
        order_no=billing.order_no,
        status=billing.status,
        amount=billing.amount,
        payment_method=billing.payment_method or "",
        payment_time=billing.payment_time.isoformat() if billing.payment_time else None,
        remark=billing.remark,
    )

    return response_200(data=response_data.dict(), message="查询成功")


@router.post("/callback/{payment_method}", summary="支付回调")
async def payment_callback(
    payment_method: str,
    request: PaymentCallbackRequest,
    db: Session = Depends(get_db),
):
    """
    支付平台回调接口
    当用户完成支付后，支付宝/微信会调用此接口通知支付结果

    注意：
    1. 此接口不需要用户认证，由支付平台调用
    2. 需要验证签名确保回调的真实性
    3. 需要保证接口的幂等性（重复调用结果一致）
    """
    # TODO: 验证签名
    # if not verify_payment_signature(request, payment_method):
    #     raise HTTPException(status_code=400, detail="签名验证失败")

    # 查询订单
    billing = db.query(Billing).filter(Billing.order_no == request.order_no).first()

    if not billing:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 如果订单已经是已支付状态，直接返回成功（幂等性）
    if billing.status == "已支付":
        return {"code": 0, "message": "success"}

    # 更新订单状态
    if request.status == "SUCCESS":
        billing.status = "已支付"
        billing.payment_time = datetime.now()

        # 更新用户余额（从用户表）
        user = db.query(SysUser).filter(SysUser.user_id == billing.user_id).first()
        if user:
            # 余额以分为单位存储
            user.balance = (user.balance or 0) + int(billing.amount * 100)

        db.commit()

    return {"code": 0, "message": "success"}


@router.post("/cancel/{order_no}", summary="取消订单")
async def cancel_order(
    order_no: str,
    db: Session = Depends(get_db),
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
):
    """
    取消未支付的订单
    """
    # 查询订单
    billing = db.query(Billing).filter(Billing.order_no == order_no).first()

    if not billing:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 验证订单归属（通过 user_id）
    if billing.user_id != current_user.user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此订单")

    # 只能取消待支付的订单
    if billing.status != "待支付":
        raise HTTPException(status_code=400, detail="只能取消待支付的订单")

    old_status = billing.status
    billing.status = "已取消"
    billing.remark = (billing.remark or "") + " [用户主动取消]"
    db.commit()

    logger.info(
        f"[订单取消] 订单已取消\n"
        f"  订单号: {order_no}\n"
        f"  用户: {current_user.user.user_name}\n"
        f"  充值金额: ¥{billing.amount}\n"
        f"  订单状态: {old_status} → {billing.status}\n"
        f"  备注: {billing.remark}"
    )

    return response_200(message="订单已取消")


def generate_payment_url(order_no: str, amount: float, payment_method: str) -> str:
    """
    生成支付URL
    TODO: 实际项目中需要调用支付宝/微信的SDK生成真实的支付URL
    """
    if payment_method == "支付宝":
        # 模拟支付宝支付URL
        return f"https://openapi.alipay.com/gateway.do?order_no={order_no}&amount={amount}"
    elif payment_method == "微信支付":
        # 模拟微信支付URL
        return f"https://api.mch.weixin.qq.com/pay/unifiedorder?order_no={order_no}&amount={amount}"
    else:
        return ""


def verify_payment_signature(request: PaymentCallbackRequest, payment_method: str) -> bool:
    """
    验证支付回调签名
    TODO: 实际项目中需要根据支付平台的签名算法进行验证
    """
    # 这里简化处理，实际需要严格验证
    return True


async def mock_payment_callback(order_no: str):
    """
    模拟支付回调
    随机在5-15秒后触发支付成功或失败的回调

    注意：此函数在后台任务中执行，需要创建新的数据库会话
    """
    # 随机等待 5-15 秒
    wait_time = random.randint(5, 15)
    logger.info(f"[Mock Payment] 订单 {order_no} - 将在 {wait_time} 秒后处理")
    await asyncio.sleep(wait_time)

    # 70% 概率支付成功，30% 概率支付超时失败
    success = random.random() < 0.7

    # 创建新的数据库会话（重要！后台任务需要独立的会话）
    db = SessionLocal()
    try:
        # 查询订单
        billing = db.query(Billing).filter(Billing.order_no == order_no).first()

        if not billing:
            logger.error(f"[Mock Payment] 订单 {order_no} - 订单不存在")
            return

        # 如果订单已经不是待支付状态，不做处理
        if billing.status != "待支付":
            logger.warning(f"[Mock Payment] 订单 {order_no} - 订单状态已变更为 {billing.status}，跳过处理")
            return

        if success:
            # 支付成功
            old_status = billing.status
            billing.status = "已支付"
            billing.payment_time = datetime.now()

            # 更新用户余额（从用户表，单位：分）
            user = db.query(SysUser).filter(SysUser.user_id == billing.user_id).first()
            if user:
                old_balance_yuan = (user.balance or 0) / 100.0
                user.balance = (user.balance or 0) + int(billing.amount * 100)
                new_balance_yuan = user.balance / 100.0
                logger.info(
                    f"[Mock Payment] 订单 {order_no} - 支付成功！\n"
                    f"  订单状态: {old_status} → {billing.status}\n"
                    f"  充值金额: ¥{billing.amount}\n"
                    f"  用户余额: ¥{old_balance_yuan:.2f} → ¥{new_balance_yuan:.2f}\n"
                    f"  用户ID: {user.user_id}\n"
                    f"  支付时间: {billing.payment_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                logger.error(f"[Mock Payment] 订单 {order_no} - 用户不存在 (ID: {billing.user_id})")
        else:
            # 支付超时失败
            old_status = billing.status
            billing.status = "已取消"
            billing.remark = (billing.remark or "") + " [支付超时]"
            logger.warning(
                f"[Mock Payment] 订单 {order_no} - 支付超时！\n"
                f"  订单状态: {old_status} → {billing.status}\n"
                f"  充值金额: ¥{billing.amount}\n"
                f"  备注: {billing.remark}"
            )

        # 提交事务
        db.commit()

        # 刷新对象以获取最新数据
        db.refresh(billing)

        logger.info(f"[Mock Payment] 订单 {order_no} - 处理完成，最终状态: {billing.status}")

    except Exception as e:
        logger.error(f"[Mock Payment] 订单 {order_no} - 处理异常: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/mock-payment/{order_no}", summary="模拟支付（仅用于测试）")
async def trigger_mock_payment(
    order_no: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    触发模拟支付流程

    此接口会在后台随机等待5-15秒后，以70%的概率返回支付成功，30%的概率返回支付超时。

    **仅用于开发测试，生产环境请删除此接口**
    """
    # 查询订单
    billing = db.query(Billing).filter(Billing.order_no == order_no).first()

    if not billing:
        raise HTTPException(status_code=404, detail="订单不存在")

    if billing.status != "待支付":
        raise HTTPException(status_code=400, detail=f"订单状态不是待支付（当前状态：{billing.status}），无法模拟支付")

    # 记录触发信息
    logger.info(
        f"[Mock Payment] 触发模拟支付\n"
        f"  订单号: {order_no}\n"
        f"  充值金额: ¥{billing.amount}\n"
        f"  支付方式: {billing.payment_method}\n"
        f"  当前状态: {billing.status}\n"
        f"  将在5-15秒后随机返回结果（70%成功，30%超时）"
    )

    # 在后台执行模拟支付（不传入 db，在任务内部创建新会话）
    background_tasks.add_task(mock_payment_callback, order_no)

    return response_200(
        data={"order_no": order_no},
        message="模拟支付已触发，将在5-15秒后随机返回支付结果"
    )
