from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import Depends, Request
import math

from backlin.crud.crud_dao import CrudDao
from backlin.database import get_db

from backlin.module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from backlin.module_admin.entity.vo.user_vo import CurrentUserInfoServiceResponse
from backlin.module_admin.service.login_service import get_current_user
from backlin.module_saas.schema import ApiKey, ApiKeyCreationModel, ApiKeyModel, Billing, BillingModel, Usage, UsageModel
from backlin.module_saas.secure import create_auth_key
from backlin.crud.crud_route import SQLAlchemyCRUDRouter, SuccessResponse, PageResponse
from backlin.utils.response_util import response_200, response_500
from backlin.utils.log_util import logger


app = SQLAlchemyCRUDRouter(
    "ApiKey",
    schema=ApiKeyModel,
    create_schema=ApiKeyModel,
    update_schema=ApiKeyModel,
    db_model=ApiKey,
    db=get_db,
    prefix="/system/apikey",
    tags=["API Key"],
    get_all_route=[Depends(CheckUserInterfaceAuth("client:apikey:list"))],
    get_page_route=[Depends(CheckUserInterfaceAuth("client:apikey:list"))],
    get_one_route=[Depends(CheckUserInterfaceAuth("client:apikey:query"))],
    edit_route=[Depends(CheckUserInterfaceAuth("client:apikey:edit"))],
    delete_some_route=[Depends(CheckUserInterfaceAuth("client:apikey:remove"))],
    add_route=[Depends(CheckUserInterfaceAuth("client:apikey:add"))],
    export_all_route=[Depends(CheckUserInterfaceAuth("client:apikey:export"))],
)


app_billing = SQLAlchemyCRUDRouter(
    "Billing",
    schema=BillingModel,
    create_schema=BillingModel,
    update_schema=BillingModel,
    db_model=Billing,
    db=get_db,
    prefix="/system/billing",
    tags=["Billing"],
    get_all_route=[Depends(CheckUserInterfaceAuth("client:billing:list"))],
    get_page_route=[Depends(CheckUserInterfaceAuth("client:billing:list"))],
    get_one_route=[Depends(CheckUserInterfaceAuth("client:billing:query"))],
    edit_route=[Depends(CheckUserInterfaceAuth("client:billing:edit"))],
    delete_some_route=[Depends(CheckUserInterfaceAuth("client:billing:remove"))],
    add_route=[Depends(CheckUserInterfaceAuth("client:billing:add"))],
    export_all_route=[Depends(CheckUserInterfaceAuth("client:billing:export"))],
)


app_usage = SQLAlchemyCRUDRouter(
    "Usage",
    schema=UsageModel,
    create_schema=UsageModel,
    update_schema=UsageModel,
    db_model=Usage,
    db=get_db,
    prefix="/system/usage",
    tags=["Usage"],
    get_all_route=[Depends(CheckUserInterfaceAuth("client:usage:list"))],
    get_page_route=[Depends(CheckUserInterfaceAuth("client:usage:list"))],
    get_one_route=[Depends(CheckUserInterfaceAuth("client:usage:query"))],
    edit_route=False,  # 使用记录不允许编辑
    delete_some_route=[Depends(CheckUserInterfaceAuth("client:usage:remove"))],
    add_route=False,  # 使用记录不允许手动添加（通过 API 自动创建）
    export_all_route=[Depends(CheckUserInterfaceAuth("client:usage:export"))],
)


class ApiKeyCreateModel(BaseModel):
    name: str


@app.post(
    "/create_auth",
    response_model=SuccessResponse[ApiKeyModel],
    dependencies=[Depends(CheckUserInterfaceAuth("client:apikey:list"))],
    summary="Api Key Creation",
)
def create_auth(
    create: ApiKeyCreateModel,
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.user.user_id
    new_auth_key = create_auth_key(user_id)
    api_key = ApiKeyCreationModel(name=create.name, auth_key=new_auth_key, create_by=current_user.user.user_name)
    db_api_key = CrudDao.create_one(db, ApiKey, api_key)
    return response_200(data=db_api_key, message="创建成功")


# ==================== 自定义 Billing 分页查询（仅查询当前用户的订单） ====================

class BillingPageResponse(BaseModel):
    """Billing 分页响应（包含 API Key 名称）"""
    item_id: int
    order_no: str
    name: str | None = None  # API Key 名称
    status: str
    amount: float
    payment_method: str | None = None
    payment_time: str | None = None
    create_time: str | None = None
    remark: str | None = None

    class Config:
        from_attributes = True


@app_billing.post(
    "/page",
    response_model=SuccessResponse[PageResponse[BillingPageResponse]],
    dependencies=[Depends(CheckUserInterfaceAuth("client:billing:list"))],
    summary="Get Billing Page (Current User Only)",
)
def get_billing_page_for_current_user(
    request: Request,
    query: BillingModel,
    page_num: int = 1,
    page_size: int = 50,
    current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的充值订单列表（分页）
    注意：Billing 直接充值到用户账户，不关联 API Key
    """
    try:
        user_id = current_user.user.user_id

        # 构建查询：只查询 Billing 表（不关联 API Key）
        q = db.query(
            Billing.item_id,
            Billing.order_no,
            Billing.status,
            Billing.amount,
            Billing.payment_method,
            Billing.payment_time,
            Billing.create_time,
            Billing.remark,
        ).filter(
            Billing.user_id == user_id  # 只查询当前用户的订单
        )

        # 计数查询
        q_count = db.query(func.count(Billing.item_id)).filter(
            Billing.user_id == user_id
        )

        # 按状态过滤
        if query.status:
            q = q.filter(Billing.status == query.status)
            q_count = q_count.filter(Billing.status == query.status)

        # 分页计算
        skip = (page_num - 1) * page_size
        limit = page_size

        # 按创建时间倒序
        q = q.order_by(Billing.create_time.desc())

        # 执行查询
        paginated_data = q.limit(limit).offset(skip).all()
        total = q_count.scalar()

        # 转换为响应模型
        rows = []
        for row in paginated_data:
            rows.append(BillingPageResponse(
                item_id=row.item_id,
                order_no=row.order_no,
                name=None,  # 充值直接到用户账户，不关联 API Key
                status=row.status,
                amount=row.amount,
                payment_method=row.payment_method,
                payment_time=str(row.payment_time) if row.payment_time else None,
                create_time=str(row.create_time) if row.create_time else None,
                remark=row.remark,
            ))

        has_next = math.ceil(total / page_size) > page_num if page_size else False

        resp = PageResponse[BillingPageResponse](
            rows=rows,
            page_num=page_num,
            page_size=len(rows),
            total=total,
            has_next=has_next,
        )

        logger.info(f"查询用户 {current_user.user.user_name} 的订单列表成功，共 {total} 条")
        return response_200(data=resp, message="获取成功")

    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))
