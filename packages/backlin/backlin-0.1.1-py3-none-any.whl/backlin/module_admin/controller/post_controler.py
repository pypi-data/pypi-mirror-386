from fastapi import APIRouter, Request
from fastapi import Depends
from backlin.database import get_db
from backlin.module_admin.service.login_service import get_current_user, CurrentUserInfoServiceResponse
from backlin.module_admin.service.post_service import *
from backlin.module_admin.entity.vo.post_vo import *
from backlin.utils.response_util import *
from backlin.utils.log_util import *
from backlin.utils.page_util import get_page_obj
from backlin.utils.common_util import bytes2file_response
from backlin.module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from backlin.module_admin.annotation.log_annotation import log_decorator


postController = APIRouter(dependencies=[Depends(get_current_user)])


@postController.post("/post/forSelectOption", response_model=PostSelectOptionResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('common'))])
async def get_system_post_select(request: Request, query_db: Session = Depends(get_db)):
    try:
        role_query_result = PostService.get_post_select_option_services(query_db)
        logger.info('获取成功')
        return response_200(data=role_query_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@postController.post("/post/get", response_model=PostPageObjectResponse, dependencies=[Depends(CheckUserInterfaceAuth('system:post:list'))])
async def get_system_post_list(request: Request, post_page_query: PostPageObject, query_db: Session = Depends(get_db)):
    try:
        post_query = PostModel(**post_page_query.dict())
        # 获取全量数据
        post_query_result = PostService.get_post_list_services(query_db, post_query)
        # 分页操作
        post_page_query_result = get_page_obj(post_query_result, post_page_query.page_num, post_page_query.page_size)
        logger.info('获取成功')
        return response_200(data=post_page_query_result, message="获取成功")
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@postController.post("/post/add", response_model=CrudPostResponse, dependencies=[Depends(CheckUserInterfaceAuth('system:post:add'))])
@log_decorator(title='岗位管理', business_type=1)
async def add_system_post(request: Request, add_post: PostModel, query_db: Session = Depends(get_db), current_user: CurrentUserInfoServiceResponse = Depends(get_current_user)):
    try:
        add_post.create_by = current_user.user.user_name
        add_post.create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_post.update_by = current_user.user.user_name
        add_post.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_post_result = PostService.add_post_services(query_db, add_post)
        if add_post_result.is_success:
            logger.info(add_post_result.message)
            return response_200(data=add_post_result, message=add_post_result.message)
        else:
            logger.warning(add_post_result.message)
            return response_400(data="", message=add_post_result.message)
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@postController.patch("/post/edit", response_model=CrudPostResponse, dependencies=[Depends(CheckUserInterfaceAuth('system:post:edit'))])
@log_decorator(title='岗位管理', business_type=2)
async def edit_system_post(request: Request, edit_post: PostModel, query_db: Session = Depends(get_db), current_user: CurrentUserInfoServiceResponse = Depends(get_current_user)):
    try:
        edit_post.update_by = current_user.user.user_name
        edit_post.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        edit_post_result = PostService.edit_post_services(query_db, edit_post)
        if edit_post_result.is_success:
            logger.info(edit_post_result.message)
            return response_200(data=edit_post_result, message=edit_post_result.message)
        else:
            logger.warning(edit_post_result.message)
            return response_400(data="", message=edit_post_result.message)
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@postController.post("/post/delete", response_model=CrudPostResponse, dependencies=[Depends(CheckUserInterfaceAuth('system:post:remove'))])
@log_decorator(title='岗位管理', business_type=3)
async def delete_system_post(request: Request, delete_post: DeletePostModel, query_db: Session = Depends(get_db)):
    try:
        delete_post_result = PostService.delete_post_services(query_db, delete_post)
        if delete_post_result.is_success:
            logger.info(delete_post_result.message)
            return response_200(data=delete_post_result, message=delete_post_result.message)
        else:
            logger.warning(delete_post_result.message)
            return response_400(data="", message=delete_post_result.message)
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@postController.get("/post/{post_id}", response_model=PostModel, dependencies=[Depends(CheckUserInterfaceAuth('system:post:query'))])
async def query_detail_system_post(request: Request, post_id: int, query_db: Session = Depends(get_db)):
    try:
        detail_post_result = PostService.detail_post_services(query_db, post_id)
        logger.info(f'获取post_id为{post_id}的信息成功')
        return response_200(data=detail_post_result, message='获取成功')
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))


@postController.post("/post/export", dependencies=[Depends(CheckUserInterfaceAuth('system:post:export'))])
@log_decorator(title='岗位管理', business_type=5)
async def export_system_post_list(request: Request, post_query: PostModel, query_db: Session = Depends(get_db)):
    try:
        # 获取全量数据
        post_query_result = PostService.get_post_list_services(query_db, post_query)
        post_export_result = PostService.export_post_list_services(post_query_result)
        logger.info('导出成功')
        return streaming_response_200(data=bytes2file_response(post_export_result))
    except Exception as e:
        logger.exception(e)
        return response_500(data="", message=str(e))
