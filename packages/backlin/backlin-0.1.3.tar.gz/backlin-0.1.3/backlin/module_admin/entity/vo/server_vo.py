from pydantic import BaseModel
from typing import Optional, List


class CpuInfo(BaseModel):
    cpu_num: Optional[int] = None
    used: Optional[str] = None
    sys: Optional[str] = None
    free: Optional[str] = None


class MemoryInfo(BaseModel):
    total: Optional[str] = None
    used: Optional[str] = None
    free: Optional[str] = None
    usage: Optional[str] = None


class SysInfo(BaseModel):
    computer_ip: Optional[str] = None
    computer_name: Optional[str] = None
    os_arch: Optional[str] = None
    os_name: Optional[str] = None


class PyInfo(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    start_time: Optional[str] = None
    run_time: Optional[str] = None
    home: Optional[str] = None
    project_dir: Optional[str] = None


class SysFiles(BaseModel):
    dir_name: Optional[str] = None
    sys_type_name: Optional[str] = None
    disk_name: Optional[str] = None
    total: Optional[str] = None
    used: Optional[str] = None
    free: Optional[str] = None
    usage: Optional[str] = None


class ServerMonitorModel(BaseModel):
    """
    服务监控对应pydantic模型
    """
    cpu: Optional[CpuInfo] = None
    py: Optional[PyInfo] = None
    mem: Optional[MemoryInfo] = None
    sys: Optional[SysInfo] = None
    sys_files: Optional[List[SysFiles]]
