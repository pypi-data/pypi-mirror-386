from typing import Optional

from fastapi import APIRouter, Request
from fastapi import Depends, File, Form
from sqlalchemy.orm import Session

from backlin.config.env import CachePathConfig
from backlin.database import get_db
from backlin.module_admin.service.login_service import get_current_user
from backlin.module_admin.service.common_service import *
from backlin.module_admin.service.config_service import ConfigService
from backlin.utils.response_util import *
from backlin.utils.log_util import *
from backlin.module_admin.aspect.interface_auth import CheckUserInterfaceAuth


commonController = APIRouter()


@commonController.post("/upload", dependencies=[Depends(get_current_user), Depends(CheckUserInterfaceAuth('common'))])
async def common_upload(request: Request, taskPath: str = Form(), uploadId: str = Form(), file: UploadFile = File(...)):
    try:
        cache_path = CachePathConfig.get_path()
        cache_pathstr = CachePathConfig.get_path_str()
        try:
            os.makedirs(os.path.join(cache_path, taskPath, uploadId))
        except FileExistsError:
            pass
        CommonService.upload_service(cache_path, taskPath, uploadId, file)
        logger.info('上传成功')
        return response_200(data={'filename': file.filename, 'path': f'/common/{cache_pathstr}?taskPath={taskPath}&taskId={uploadId}&filename={file.filename}'}, message="上传成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@commonController.post("/uploadForEditor", dependencies=[Depends(get_current_user), Depends(CheckUserInterfaceAuth('common'))])
async def editor_upload(request: Request, baseUrl: str = Form(), uploadId: str = Form(), taskPath: str = Form(), file: UploadFile = File(...)):
    try:
        cache_path = CachePathConfig.get_path()
        cache_pathstr = CachePathConfig.get_path_str()
        try:
            os.makedirs(os.path.join(cache_path, taskPath, uploadId))
        except FileExistsError:
            pass
        CommonService.upload_service(cache_path, taskPath, uploadId, file)
        logger.info('上传成功')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(
                {
                    'errno': 0,
                    'data': {
                        'url': f'{baseUrl}/common/{cache_pathstr}?taskPath={taskPath}&taskId={uploadId}&filename={file.filename}'
                    },
                }
            )
        )
    except Exception as e:
        logger.exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                {
                    'errno': 1,
                    'message': str(e),
                }
            )
        )


@commonController.get(f"/{CachePathConfig.get_path_str()}")
async def common_download(request: Request, taskPath: str, taskId: str, filename: str, token: Optional[str] = None, query_db: Session = Depends(get_db)):
    try:
        cache_path = CachePathConfig.get_path()
        def generate_file():
            with open(os.path.join(cache_path, taskPath, taskId, filename), 'rb') as response_file:
                yield from response_file
        if taskPath not in ['notice']:
            current_user = await get_current_user(request, token, query_db)
            if current_user:
                logger.info('获取成功')
                return streaming_response_200(data=generate_file())
        logger.info('获取成功')
        return streaming_response_200(data=generate_file())
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@commonController.get("/config/query/{config_key}")
async def query_system_config(request: Request, config_key: str):
    try:
        # 获取全量数据
        config_query_result = await ConfigService.query_config_list_from_cache_services(request.app.state.redis, config_key)
        logger.info('获取成功')
        return response_200(data=config_query_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))
