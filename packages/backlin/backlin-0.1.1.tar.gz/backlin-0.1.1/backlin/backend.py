import os
from typing import List, Tuple

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute

from backlin.database import SessionLocal, engine, Base
from backlin.routes import apilog
from backlin.module_saas import (
    route_apikey,
    api_v1,
    route_order,
)

from backlin.config.env import AppConfig
from backlin.config.get_redis import RedisUtil
from backlin.config.get_scheduler import SchedulerUtil
from backlin.utils.response_util import *
from backlin.utils.log_util import logger

# Base.metadata.create_all(bind=engine)

APP_NAME = os.getenv("APP_NAME", "app")

app = FastAPI(
    title="Backlin API",
    description="Built with FastAPI.",
    version="1.0.0",
    servers=[
        {"url": "http://127.0.0.1:8000", "description": "dev environment"},
    ],
)


async def init_create_table():
    """
    应用启动时初始化数据库连接
    :return:
    """
    logger.info("初始化数据库连接...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库连接成功")


@app.on_event("startup")
async def startup_event():
    logger.info(f"{AppConfig.app_name}开始启动")
    await init_create_table()
    app.state.redis = await RedisUtil.create_redis_pool()
    await RedisUtil.init_sys_dict(app.state.redis)
    await RedisUtil.init_sys_config(app.state.redis)
    await SchedulerUtil.init_system_scheduler()
    logger.info(f"{AppConfig.app_name}启动成功")


@app.on_event("shutdown")
async def shutdown_event():
    await RedisUtil.close_redis_pool(app)
    await SchedulerUtil.close_system_scheduler()


# 自定义token检验异常
@app.exception_handler(AuthException)
async def auth_exception_handler(request: Request, exc: AuthException):
    return response_401(data=exc.data, message=exc.message)


# 自定义权限检验异常
@app.exception_handler(PermissionException)
async def permission_exception_handler(request: Request, exc: PermissionException):
    return response_403(data=exc.data, message=exc.message)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content=jsonable_encoder({"message": exc.detail, "code": exc.status_code}),
        status_code=exc.status_code,
    )


# router
from backlin.routes import admin, client, openai

app.include_router(admin.app)
app.include_router(client.app)
app.include_router(openai.app)

app.include_router(apilog.app)

app.include_router(route_apikey.app)
app.include_router(route_apikey.app_billing)
app.include_router(route_apikey.app_usage)
app.include_router(api_v1.app)
app.include_router(route_order.router)

from backlin.module_admin.controller.login_controller import loginController
from backlin.module_admin.controller.captcha_controller import captchaController
from backlin.module_admin.controller.user_controller import userController
from backlin.module_admin.controller.menu_controller import menuController
from backlin.module_admin.controller.dept_controller import deptController
from backlin.module_admin.controller.role_controller import roleController
from backlin.module_admin.controller.post_controler import postController
from backlin.module_admin.controller.dict_controller import dictController
from backlin.module_admin.controller.config_controller import configController
from backlin.module_admin.controller.notice_controller import noticeController
from backlin.module_admin.controller.log_controller import logController
from backlin.module_admin.controller.online_controller import onlineController
from backlin.module_admin.controller.job_controller import jobController
from backlin.module_admin.controller.server_controller import serverController
from backlin.module_admin.controller.cache_controller import cacheController
from backlin.module_admin.controller.common_controller import commonController

app.include_router(loginController, prefix="/login", tags=["登录模块"])
app.include_router(captchaController, prefix="/captcha", tags=["验证码模块"])
app.include_router(userController, prefix="/system", tags=["系统管理-用户管理"])
app.include_router(menuController, prefix="/system", tags=["系统管理-菜单管理"])
app.include_router(deptController, prefix="/system", tags=["系统管理-部门管理"])
app.include_router(roleController, prefix="/system", tags=["系统管理-角色管理"])
app.include_router(postController, prefix="/system", tags=["系统管理-岗位管理"])
app.include_router(dictController, prefix="/system", tags=["系统管理-字典管理"])
app.include_router(configController, prefix="/system", tags=["系统管理-参数管理"])
app.include_router(noticeController, prefix="/system", tags=["系统管理-通知公告管理"])
app.include_router(logController, prefix="/system", tags=["系统管理-日志管理"])
app.include_router(onlineController, prefix="/monitor", tags=["系统监控-在线用户"])
app.include_router(jobController, prefix="/monitor", tags=["系统监控-定时任务"])
app.include_router(serverController, prefix="/monitor", tags=["系统监控-服务监控"])
app.include_router(cacheController, prefix="/monitor", tags=["系统监控-缓存监控"])
app.include_router(commonController, prefix="/common", tags=["通用模块"])

# mount
# from openai_forward.app import app as openai_app
# app.mount("/openai", openai_app)

# def use_route_names_as_operation_ids(app: FastAPI) -> None:
#     """
#     Simplify operation IDs so that generated API clients have simpler function
#     names.

#     Should be called only after all routes have been added.
#     """
#     for route in app.routes:
#         if isinstance(route, APIRoute):
#             route.operation_id = f"{route.path_format}_{list(route.methods)[0]}_{route.name}"  # in this case, 'read_items'


# use_route_names_as_operation_ids(app)

# middleware
# 前端页面url
# origins = [
#     "http://localhost:8088",
#     "http://127.0.0.1:8088",
# ]

# 后台api允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# class EndpointFilter(logging.Filter):
#     # Uvicorn endpoint access log filter
#     def filter(self, record: logging.LogRecord) -> bool:
#         return record.getMessage().find("GET /metrics") == -1


@app.get("/", summary="API 文档", include_in_schema=False)
async def document():
    return RedirectResponse(url="/docs")
