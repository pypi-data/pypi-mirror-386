from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from backlin.database import Base
from datetime import datetime


class SysUser(Base):
    """
    用户信息表
    """
    __tablename__ = 'sys_user'

    user_id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    dept_id = Column(Integer, comment='部门ID')
    user_name = Column(String(30), nullable=False, comment='用户账号')
    nick_name = Column(String(30), nullable=False, comment='用户昵称')
    user_type = Column(String(2), default='00', comment='用户类型（00系统用户）')
    email = Column(String(50), default='', comment='用户邮箱')
    phonenumber = Column(String(11), default='', comment='手机号码')
    sex = Column(String(1), default='0', comment='用户性别（0男 1女 2未知）')
    avatar = Column(String(100), default='', comment='头像地址')
    password = Column(String(100), default='', comment='密码')
    locale = Column(String, nullable=True, default="zh", comment='语言')
    real_name_verified = Column(Boolean, default=False, comment='实名验证状态（False未验证 True已验证）')
    balance = Column(Integer, default=0, comment='账户余额（分）')
    status = Column(Integer, default=0, comment='帐号状态（0正常 1停用）')
    del_flag = Column(Integer, default=0, comment='删除标志（0代表存在 2代表删除）')
    login_ip = Column(String(128), default='', comment='最后登录IP')
    login_date = Column(DateTime, comment='最后登录时间')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, comment='创建时间', server_default=func.now())
    update_by = Column(String(64), default='', comment='更新者')
    update_time = Column(DateTime, comment='更新时间', server_default=func.now(), onupdate=datetime.now)
    remark = Column(String(500), comment='备注')


class SysUserRole(Base):
    """
    用户和角色关联表
    """
    __tablename__ = 'sys_user_role'

    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
    role_id = Column(Integer, primary_key=True, nullable=False, comment='角色ID')


class SysUserPost(Base):
    """
    用户与岗位关联表
    """
    __tablename__ = 'sys_user_post'

    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
    post_id = Column(Integer, primary_key=True, nullable=False, comment='岗位ID')
