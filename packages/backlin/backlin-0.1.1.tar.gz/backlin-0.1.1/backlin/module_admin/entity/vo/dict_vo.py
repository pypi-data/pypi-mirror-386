from pydantic import BaseModel
from typing import Union, Optional, List


class DictTypeModel(BaseModel):
    """
    字典类型表对应pydantic模型
    """
    dict_id: Optional[int] = None
    dict_name: Optional[str] = None
    dict_type: Optional[str] = None
    status: Optional[int] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class DictDataModel(BaseModel):
    """
    字典数据表对应pydantic模型
    """
    dict_code: Optional[int] = None
    dict_sort: Optional[int] = None
    dict_label: Optional[str] = None
    dict_value: Optional[str] = None
    dict_type: Optional[str] = None
    css_class: Optional[str] = None
    list_class: Optional[str] = None
    is_default: Optional[str] = None
    status: Optional[int] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class DictTypeQueryModel(DictTypeModel):
    """
    字典类型管理不分页查询模型
    """
    create_time_start: Optional[str] = None
    create_time_end: Optional[str] = None


class DictTypePageObject(DictTypeQueryModel):
    """
    字典类型管理分页查询模型
    """
    page_num: int
    page_size: int


class DictTypePageObjectResponse(BaseModel):
    """
    字典类型管理列表分页查询返回模型
    """
    rows: List[Union[DictTypeModel, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class DeleteDictTypeModel(BaseModel):
    """
    删除字典类型模型
    """
    dict_ids: str


class DictDataPageObject(DictDataModel):
    """
    字典数据管理分页查询模型
    """
    page_num: int
    page_size: int


class DictDataPageObjectResponse(BaseModel):
    """
    字典数据管理列表分页查询返回模型
    """
    rows: List[Union[DictDataModel, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class DeleteDictDataModel(BaseModel):
    """
    删除字典数据模型
    """
    dict_codes: str


class CrudDictResponse(BaseModel):
    """
    操作字典响应模型
    """
    is_success: bool
    message: str
