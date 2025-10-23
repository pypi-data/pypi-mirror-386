from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from backlin.database import Base
from datetime import datetime


class SysPost(Base):
    """
    岗位信息表
    """
    __tablename__ = 'sys_post'

    post_id = Column(Integer, primary_key=True, autoincrement=True, comment='岗位ID')
    post_code = Column(String(64), nullable=False, comment='岗位编码')
    post_name = Column(String(50), nullable=False, comment='岗位名称')
    post_sort = Column(Integer, nullable=False, comment='显示顺序')
    status = Column(Integer, nullable=False, default=0, comment='状态（0正常 1停用）')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, nullable=True, server_default=func.now(), comment='创建时间')
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, server_default=func.now(), comment='更新时间', onupdate=datetime.now)
    remark = Column(String(500), nullable=True, default='', comment='备注')
