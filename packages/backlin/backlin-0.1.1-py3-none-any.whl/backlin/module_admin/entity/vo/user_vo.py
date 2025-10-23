from pydantic import BaseModel
from typing import Union, Optional, List


class TokenData(BaseModel):
    """
    token解析结果
    """
    user_id: Union[int, None] = None


class UserModel(BaseModel):
    """
    用户表对应pydantic模型
    """
    user_id: Optional[int] = None
    dept_id: Optional[int] = None
    user_name: Optional[str] = None
    nick_name: Optional[str] = None
    user_type: Optional[str] = None
    email: Optional[str] = None
    phonenumber: Optional[str] = None
    sex: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = None
    locale: Optional[str] = None
    real_name_verified: Optional[bool] = None
    status: Optional[int] = None
    del_flag: Optional[int] = None
    login_ip: Optional[str] = None
    login_date: Optional[str] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class UserRoleModel(BaseModel):
    """
    用户和角色关联表对应pydantic模型
    """
    user_id: Optional[int] = None
    role_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserPostModel(BaseModel):
    """
    用户与岗位关联表对应pydantic模型
    """
    user_id: Optional[int] = None
    post_id: Optional[int] = None

    class Config:
        from_attributes = True


class DeptModel(BaseModel):
    """
    部门表对应pydantic模型
    """
    dept_id: Optional[int] = None
    parent_id: Optional[int] = None
    ancestors: Optional[List[int]] = None
    dept_name: Optional[str] = None
    order_num: Optional[int] = None
    leader: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[int] = None
    del_flag: Optional[int] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None

    class Config:
        from_attributes = True


class RoleModel(BaseModel):
    """
    角色表对应pydantic模型
    """
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    role_key: Optional[str] = None
    role_sort: Optional[int] = None
    data_scope: Optional[str] = None
    menu_check_strictly: Optional[int] = None
    dept_check_strictly: Optional[int] = None
    status: Optional[int] = None
    del_flag: Optional[int] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class PostModel(BaseModel):
    """
    岗位信息表对应pydantic模型
    """
    post_id: Optional[int] = None
    post_code: Optional[str] = None
    post_name: Optional[str] = None
    post_sort: Optional[int] = None
    status: Optional[int] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True

class MenuModel(BaseModel):
    """
    菜单表对应pydantic模型
    """
    menu_id: Optional[int] = None
    menu_name: Optional[str] = None
    parent_id: Optional[int] = None
    order_num: Optional[int] = None
    path: Optional[str] = None
    component: Optional[str] = None
    query: Optional[str] = None
    is_frame: Optional[int] = None
    is_cache: Optional[int] = None
    menu_type: Optional[str] = None
    visible: Optional[str] = None
    status: Optional[int] = None
    perms: Optional[str] = None
    icon: Optional[str] = None
    class Config:
        from_attributes = True


class CurrentUserInfo(BaseModel):
    """
    数据库返回当前用户信息
    """
    user_basic_info: Optional[UserModel] = None
    user_dept_info: Optional[DeptModel] = None
    user_role_info: List[RoleModel] = []
    user_post_info: List[PostModel] = []
    user_menu_info: List[MenuModel] = []


class UserDetailModel(BaseModel):
    """
    获取用户详情信息响应模型
    """
    user: Optional[UserModel] = None
    dept: Optional[DeptModel] = None
    role: List[RoleModel] = []
    post: List[PostModel] = []


class CurrentUserInfoServiceResponse(UserDetailModel):
    """
    获取当前用户信息响应模型
    """
    menu: List[MenuModel] = []


class UserQueryModel(UserModel):
    """
    用户管理不分页查询模型
    """
    create_time_start: Optional[str] = None
    create_time_end: Optional[str] = None


class UserPageObject(UserQueryModel):
    """
    用户管理分页查询模型
    """
    page_num: int
    page_size: int


class UserInfoJoinDept(UserModel):
    """
    数据库查询用户列表返回模型
    """
    dept_name: Optional[str] = None


class UserPageObjectResponse(BaseModel):
    """
    用户管理列表分页查询返回模型
    """
    rows: List[Union[UserInfoJoinDept, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class AddUserModel(UserModel):
    """
    新增用户模型
    """
    role_id: Optional[str] = None
    post_id: Optional[str] = None
    type: Optional[str] = None


class ResetUserModel(UserModel):
    """
    重置用户密码模型
    """
    old_password: Optional[str] = None
    sms_code: Optional[str] = None
    session_id: Optional[str] = None


class DeleteUserModel(BaseModel):
    """
    删除用户模型
    """
    user_ids: str
    update_by: Optional[str] = None
    update_time: Optional[str] = None


class UserRoleQueryModel(UserRoleModel):
    """
    用户角色关联管理不分页查询模型
    """
    user_name: Optional[str] = None
    phonenumber: Optional[str] = None
    role_name: Optional[str] = None
    role_key: Optional[str] = None


class UserRolePageObject(UserRoleQueryModel):
    """
    用户角色关联管理分页查询模型
    """
    page_num: int
    page_size: int


class UserRolePageObjectResponse(BaseModel):
    """
    用户角色关联管理列表分页查询返回模型
    """
    rows: List = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class CrudUserRoleModel(BaseModel):
    """
    新增、删除用户关联角色及角色关联用户模型
    """
    user_ids: Optional[str] = None
    role_ids: Optional[str] = None


class ImportUserModel(BaseModel):
    """
    批量导入用户模型
    """
    url: str
    is_update: bool


class CrudUserResponse(BaseModel):
    """
    操作用户响应模型
    """
    is_success: bool
    message: str


class DeptInfo(BaseModel):
    """
    查询部门树
    """
    dept_id: int
    dept_name: str
    ancestors: List[int]


class RoleInfo(BaseModel):
    """
    用户角色信息
    """
    role_info: Optional[List] = None


class MenuList(BaseModel):
    """
    用户菜单信息
    """
    menu_info: Optional[List] = None
