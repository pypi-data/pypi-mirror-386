from pydantic import BaseModel
from typing import Union, Optional, List


class JobModel(BaseModel):
    """
    定时任务调度表对应pydantic模型
    """
    job_id: Optional[int] = None
    job_name: Optional[str] = None
    job_group: Optional[str] = None
    job_executor: Optional[str] = None
    invoke_target: Optional[str] = None
    job_args: Optional[str] = None
    job_kwargs: Optional[str] = None
    cron_expression: Optional[str] = None
    misfire_policy: Optional[str] = None
    concurrent: Optional[str] = None
    status: Optional[int] = None
    create_by: Optional[str] = None
    create_time: Optional[str] = None
    update_by: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class JobLogModel(BaseModel):
    """
    定时任务调度日志表对应pydantic模型
    """
    job_log_id: Optional[int] = None
    job_name: Optional[str] = None
    job_group: Optional[str] = None
    job_executor: Optional[str] = None
    invoke_target: Optional[str] = None
    job_args: Optional[str] = None
    job_kwargs: Optional[str] = None
    job_trigger: Optional[str] = None
    job_message: Optional[str] = None
    status: Optional[int] = None
    exception_info: Optional[str] = None
    create_time: Optional[str] = None

    class Config:
        from_attributes = True


class JobPageObject(JobModel):
    """
    定时任务管理分页查询模型
    """
    page_num: int
    page_size: int


class JobPageObjectResponse(BaseModel):
    """
    定时任务管理列表分页查询返回模型
    """
    rows: List[Union[JobModel, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class CrudJobResponse(BaseModel):
    """
    操作定时任务及日志响应模型
    """
    is_success: bool
    message: str


class EditJobModel(JobModel):
    """
    编辑定时任务模型
    """
    type: Optional[str] = None


class DeleteJobModel(BaseModel):
    """
    删除定时任务模型
    """
    job_ids: str


class JobLogQueryModel(JobLogModel):
    """
    定时任务日志不分页查询模型
    """
    create_time_start: Optional[str] = None
    create_time_end: Optional[str] = None


class JobLogPageObject(JobLogQueryModel):
    """
    定时任务日志管理分页查询模型
    """
    page_num: int
    page_size: int


class JobLogPageObjectResponse(BaseModel):
    """
    定时任务日志管理列表分页查询返回模型
    """
    rows: List[Union[JobLogModel, None]] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool


class DeleteJobLogModel(BaseModel):
    """
    删除定时任务日志模型
    """
    job_log_ids: str


class ClearJobLogModel(BaseModel):
    """
    清除定时任务日志模型
    """
    oper_type: str
