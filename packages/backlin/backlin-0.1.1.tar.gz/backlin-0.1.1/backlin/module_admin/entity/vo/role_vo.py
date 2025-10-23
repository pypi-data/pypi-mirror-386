from pydantic import BaseModel
from typing import Union, Optional, List
from backlin.module_admin.entity.vo.user_vo import RoleModel
from backlin.module_admin.entity.vo.dept_vo import DeptModel
from backlin.module_admin.entity.vo.menu_vo import MenuModel


class RoleMenuModel(BaseModel):
    """
    角色和菜单关联表对应pydantic模型
    """
    role_id: Optional[int] = None
    menu_id: Optional[int] = None

    class Config:
        from_attributes = True


class RoleDeptModel(BaseModel):
    """
    角色和部门关联表对应pydantic模型
    """
    role_id: Optional[int] = None
    dept_id: Optional[int] = None

    class Config:
        from_attributes = True


class RoleQueryModel(RoleModel):
    """
    角色管理不分页查询模型
    """
    create_time_start: Optional[str] = None
    create_time_end: Optional[str] = None


class RolePageObject(RoleQueryModel):
    """
    角色管理分页查询模型
    """
    page_num: int
    page_size: int


class RolePageObjectResponse(BaseModel):
    """
    角色管理列表分页查询返回模型
    """
    rows: List[Union[RoleModel, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class RoleSelectOptionResponseModel(BaseModel):
    """
    角色管理不分页查询模型
    """
    role: List[RoleModel] = []


class CrudRoleResponse(BaseModel):
    """
    操作角色响应模型
    """
    is_success: bool
    message: str


class AddRoleModel(RoleModel):
    """
    新增角色模型
    """
    menu_id: Optional[str] = None
    type: Optional[str] = None


class RoleDataScopeModel(RoleModel):
    """
    角色数据权限模型
    """
    dept_id: Optional[str] = None


class DeleteRoleModel(BaseModel):
    """
    删除角色模型
    """
    role_ids: str
    update_by: Optional[str] = None
    update_time: Optional[str] = None


class RoleDetailModel(BaseModel):
    """
    获取角色详情信息响应模型
    """
    role: Union[RoleModel, None]
    menu: List[MenuModel] = []
    dept: List[DeptModel] = []
