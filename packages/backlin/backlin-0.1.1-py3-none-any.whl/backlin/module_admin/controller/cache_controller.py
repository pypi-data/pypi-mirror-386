from fastapi import APIRouter
from fastapi import Depends

from backlin.module_admin.service.login_service import get_current_user
from backlin.module_admin.service.cache_service import *
from backlin.module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from backlin.utils.response_util import *
from backlin.utils.log_util import *


cacheController = APIRouter(prefix='/cache', dependencies=[Depends(get_current_user)])


@cacheController.post("/statisticalInfo", response_model=CacheMonitorModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def get_monitor_cache_info(request: Request):
    try:
        # 获取全量数据
        cache_info_query_result = await CacheService.get_cache_monitor_statistical_info_services(request)
        logger.info('获取成功')
        return response_200(data=cache_info_query_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@cacheController.post("/getNames", response_model=List[CacheInfoModel], dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def get_monitor_cache_name(request: Request):
    try:
        # 获取全量数据
        cache_name_list_result = CacheService.get_cache_monitor_cache_name_services()
        logger.info('获取成功')
        return response_200(data=cache_name_list_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@cacheController.post("/getKeys/{cache_name}", response_model=List[str], dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def get_monitor_cache_key(request: Request, cache_name: str):
    try:
        # 获取全量数据
        cache_key_list_result = await CacheService.get_cache_monitor_cache_key_services(request, cache_name)
        logger.info('获取成功')
        return response_200(data=cache_key_list_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@cacheController.post("/getValue/{cache_name}/{cache_key}", response_model=CacheInfoModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def get_monitor_cache_value(request: Request, cache_name: str, cache_key: str):
    try:
        # 获取全量数据
        cache_value_list_result = await CacheService.get_cache_monitor_cache_value_services(request, cache_name, cache_key)
        logger.info('获取成功')
        return response_200(data=cache_value_list_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@cacheController.post("/clearCacheName/{cache_name}", response_model=CrudCacheResponse, dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def clear_monitor_cache_name(request: Request, cache_name: str):
    try:
        clear_cache_name_result = await CacheService.clear_cache_monitor_cache_name_services(request, cache_name)
        if clear_cache_name_result.is_success:
            logger.info(clear_cache_name_result.message)
            return response_200(data=clear_cache_name_result, message=clear_cache_name_result.message)
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@cacheController.post("/clearCacheKey/{cache_name}/{cache_key}", response_model=CrudCacheResponse, dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def clear_monitor_cache_key(request: Request, cache_name: str, cache_key: str):
    try:
        clear_cache_key_result = await CacheService.clear_cache_monitor_cache_key_services(request, cache_name, cache_key)
        if clear_cache_key_result.is_success:
            logger.info(clear_cache_key_result.message)
            return response_200(data=clear_cache_key_result, message=clear_cache_key_result.message)
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@cacheController.post("/clearCacheAll", response_model=CrudCacheResponse, dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def clear_monitor_cache_all(request: Request):
    try:
        clear_cache_all_result = await CacheService.clear_cache_monitor_all_services(request)
        if clear_cache_all_result.is_success:
            logger.info(clear_cache_all_result.message)
            return response_200(data=clear_cache_all_result, message=clear_cache_all_result.message)
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))
