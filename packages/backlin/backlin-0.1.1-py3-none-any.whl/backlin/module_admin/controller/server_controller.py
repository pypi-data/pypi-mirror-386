from fastapi import APIRouter, Request
from fastapi import Depends

from backlin.utils.response_util import *
from backlin.utils.log_util import *
from backlin.module_admin.service.login_service import get_current_user
from backlin.module_admin.service.server_service import *
from backlin.module_admin.aspect.interface_auth import CheckUserInterfaceAuth


serverController = APIRouter(prefix='/server', dependencies=[Depends(get_current_user)])


@serverController.post("/statisticalInfo", response_model=ServerMonitorModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:server:list'))])
async def get_monitor_server_info(request: Request):
    try:
        # 获取全量数据
        server_info_query_result = ServerService.get_server_monitor_info()
        logger.info('获取成功')
        return response_200(data=server_info_query_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))
