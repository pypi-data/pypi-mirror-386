from contextlib import contextmanager
from datetime import datetime
import traceback

from .database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
from backlin.module_admin.entity.do.config_do import *
from backlin.module_admin.entity.do.dept_do import *
from backlin.module_admin.entity.do.dict_do import *
from backlin.module_admin.entity.do.job_do import *
from backlin.module_admin.entity.do.log_do import *
from backlin.module_admin.entity.do.menu_do import *
from backlin.module_admin.entity.do.notice_do import *
from backlin.module_admin.entity.do.post_do import *
from backlin.module_admin.entity.do.role_do import *
from backlin.module_admin.entity.do.user_do import *
from backlin.module_saas import schema as saas_schema
from backlin.module_saas import secure as saas_secure
from backlin.crud.crud_dao import CrudDao
from backlin.utils.pwd_util import PwdUtil


def str2datetime(datetime_str: str):
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def auto_commit(db: Session):
    # 高并发下的数据库问题
    try:
        yield
        db.commit()
    except Exception as e:
        # 加入数据库commit提交失败，必须回滚！！！
        db.rollback()
        print(e)
        raise e


def load_database(recreate_db):
    db = SessionLocal()
    try:
        init(db, recreate_db)
    finally:
        db.close()


def init(session: Session, recreate_db: bool):
    if recreate_db:
        try:
            recreate_database(session)
            print("新数据库初始化完成")
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            print("初始化失败,请检查数据库设置、防火墙、以及是否初始化完成")
        return
    try:
        res = session.query(SysUser).filter_by(user_name="admin").one_or_none()
    except Exception as e:
        print(e)
        session.commit()
        res = False
    if res:
        print("检测到已存在数据库")
    else:
        init(session, True)


def recreate_database(db: Session):
    # 清空表
    print("清空表")
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    print("创建表")
    # 创建表
    Base.metadata.create_all(bind=engine)
    print("初始化表")
    # 初始化表
    init_database(db)


def init_database(db: Session):
    admin_creation = dict(status=0, del_flag=0, create_by="admin", create_time=str2datetime("2024-05-23 16:13:33"), update_by="admin", update_time=str2datetime("2024-08-08 15:57:58"))
    user_creation = dict(status=0, del_flag=0, create_by="linxueyuan", create_time=str2datetime("2024-05-23 16:13:33"), update_by="linxueyuan", update_time=str2datetime("2024-08-08 15:57:58"))

    def crud_menus(name: str, parent_id: int, order_num: int, path: str, component: str, icon: str, remark: str, prem_prefix: str, role_id=1, editor=True):
        menu_id = parent_id * 100 + order_num
        perms = [
            SysRoleMenu(role_id=role_id, menu_id=menu_id),
            SysRoleMenu(role_id=role_id, menu_id=menu_id * 10 + 1),
            SysRoleMenu(role_id=role_id, menu_id=menu_id * 10 + 3),
            SysRoleMenu(role_id=role_id, menu_id=menu_id * 10 + 6),
        ]
        if editor:
            perms.append(SysRoleMenu(role_id=role_id, menu_id=menu_id * 10 + 2))
            perms.append(SysRoleMenu(role_id=role_id, menu_id=menu_id * 10 + 4))
            perms.append(SysRoleMenu(role_id=role_id, menu_id=menu_id * 10 + 5))
        return [
            SysMenu(menu_id=menu_id, menu_name=name, parent_id=parent_id, order_num=order_num, path=path, component=component, query="", is_frame=1, is_cache=0, menu_type="C", visible="0", perms=f"{prem_prefix}:list", icon=icon, remark=remark, **admin_creation),
            SysMenu(menu_id=menu_id * 10 + 1, menu_name=f"{name}查询", parent_id=menu_id, order_num=1, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", perms=f"{prem_prefix}:query", icon="#", remark=f"{name}查询", **admin_creation),
            SysMenu(menu_id=menu_id * 10 + 2, menu_name=f"{name}新增", parent_id=menu_id, order_num=2, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", perms=f"{prem_prefix}:add", icon="#", remark=f"{name}新增", **admin_creation),
            SysMenu(menu_id=menu_id * 10 + 3, menu_name=f"{name}修改", parent_id=menu_id, order_num=3, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", perms=f"{prem_prefix}:edit", icon="#", remark=f"{name}修改", **admin_creation),
            SysMenu(menu_id=menu_id * 10 + 4, menu_name=f"{name}删除", parent_id=menu_id, order_num=4, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", perms=f"{prem_prefix}:remove", icon="#", remark=f"{name}删除", **admin_creation),
            SysMenu(menu_id=menu_id * 10 + 5, menu_name=f"{name}导入", parent_id=menu_id, order_num=5, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", perms=f"{prem_prefix}:import", icon="#", remark=f"{name}导入", **admin_creation),
            SysMenu(menu_id=menu_id * 10 + 6, menu_name=f"{name}导出", parent_id=menu_id, order_num=6, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", perms=f"{prem_prefix}:export", icon="#", remark=f"{name}导出", **admin_creation),
        ] + perms

    items = [
        SysConfig(config_id=1, config_name="主框架页-默认皮肤样式名称", config_key="sys.index.skinName", config_value="#1890ff", config_type="Y", create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="admin", update_time=str2datetime("2023-05-23 16:13:34"), remark="蓝色 #1890ff"),
        SysConfig(config_id=2, config_name="账号自助-验证码开关", config_key="sys.account.captchaEnabled", config_value="true", config_type="Y", create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="admin", update_time=str2datetime("2023-05-23 16:13:34"), remark="是否开启验证码功能（true开启，false关闭）"),
        SysConfig(config_id=3, config_name="用户登录-黑名单列表", config_key="sys.login.blackIPList", config_value="", config_type="Y", create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="", update_time=None, remark="设置登录IP黑名单限制，多个匹配项以;分隔，支持匹配（*通配、网段）"),
        SysConfig(config_id=4, config_name="账号自助-是否开启忘记密码功能", config_key="sys.account.forgetUser", config_value="true", config_type="Y", create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="admin", update_time=str2datetime("2023-05-23 16:13:34"), remark="是否开启忘记密码功能（true开启，false关闭）"),
        SysDictData(dict_code=1, dict_sort=1, dict_label="男", dict_value="0", dict_type="sys_user_sex", css_class="", list_class="", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="性别男"),
        SysDictData(dict_code=2, dict_sort=2, dict_label="女", dict_value="1", dict_type="sys_user_sex", css_class="", list_class="", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="性别女"),
        SysDictData(dict_code=3, dict_sort=3, dict_label="未知", dict_value="2", dict_type="sys_user_sex", css_class="", list_class="", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="性别未知"),
        SysDictData(dict_code=4, dict_sort=1, dict_label="显示", dict_value="0", dict_type="sys_show_hide", css_class="", list_class="primary", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="显示菜单"),
        SysDictData(dict_code=5, dict_sort=2, dict_label="隐藏", dict_value="1", dict_type="sys_show_hide", css_class="", list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="隐藏菜单"),
        SysDictData(dict_code=6, dict_sort=1, dict_label="正常", dict_value="0", dict_type="sys_normal_disable", css_class='{"color": "blue"}', list_class="primary", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="正常状态"),
        SysDictData(dict_code=7, dict_sort=2, dict_label="停用", dict_value="1", dict_type="sys_normal_disable", css_class='{"color": "volcano"}', list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="admin", update_time=str2datetime("2023-08-18 11:24:23"), remark="停用状态"),
        SysDictData(dict_code=8, dict_sort=1, dict_label="正常", dict_value="0", dict_type="sys_job_status", css_class="", list_class="primary", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="正常状态"),
        SysDictData(dict_code=9, dict_sort=2, dict_label="暂停", dict_value="1", dict_type="sys_job_status", css_class="", list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="停用状态"),
        SysDictData(dict_code=10, dict_sort=1, dict_label="默认", dict_value="default", dict_type="sys_job_group", css_class='{"color": "blue"}', list_class="", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="admin", update_time=str2datetime("2023-08-20 16:33:32"), remark="默认分组"),
        SysDictData(dict_code=11, dict_sort=2, dict_label="数据库", dict_value="sqlalchemy", dict_type="sys_job_group", css_class='{"color": "green"}', list_class="", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="admin", update_time=str2datetime("2023-08-27 22:54:40"), remark="数据库分组"),
        SysDictData(dict_code=12, dict_sort=1, dict_label="是", dict_value="Y", dict_type="sys_yes_no", css_class="", list_class="primary", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="系统默认是"),
        SysDictData(dict_code=13, dict_sort=2, dict_label="否", dict_value="N", dict_type="sys_yes_no", css_class="", list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="系统默认否"),
        SysDictData(dict_code=14, dict_sort=1, dict_label="通知", dict_value="1", dict_type="sys_notice_type", css_class='{"color": "gold"}', list_class="warning", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="admin", update_time=str2datetime("2023-08-20 16:12:53"), remark="通知"),
        SysDictData(dict_code=15, dict_sort=2, dict_label="公告", dict_value="2", dict_type="sys_notice_type", css_class='{"color": "green"}', list_class="success", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="admin", update_time=str2datetime("2023-08-20 16:13:03"), remark="公告"),
        SysDictData(dict_code=16, dict_sort=1, dict_label="正常", dict_value="0", dict_type="sys_notice_status", css_class="", list_class="primary", is_default="Y", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="正常状态"),
        SysDictData(dict_code=17, dict_sort=2, dict_label="关闭", dict_value="1", dict_type="sys_notice_status", css_class="", list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="关闭状态"),
        SysDictData(dict_code=18, dict_sort=99, dict_label="其他", dict_value="0", dict_type="sys_oper_type", css_class='{"color": "purple"}', list_class="info", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="其他操作"),
        SysDictData(dict_code=19, dict_sort=1, dict_label="新增", dict_value="1", dict_type="sys_oper_type", css_class='{"color": "green"}', list_class="info", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="新增操作"),
        SysDictData(dict_code=20, dict_sort=2, dict_label="修改", dict_value="2", dict_type="sys_oper_type", css_class='{"color": "orange"}', list_class="info", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="修改操作"),
        SysDictData(dict_code=21, dict_sort=3, dict_label="删除", dict_value="3", dict_type="sys_oper_type", css_class='{"color": "red"}', list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="删除操作"),
        SysDictData(dict_code=22, dict_sort=4, dict_label="授权", dict_value="4", dict_type="sys_oper_type", css_class='{"color": "lime"}', list_class="primary", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="授权操作"),
        SysDictData(dict_code=23, dict_sort=5, dict_label="导出", dict_value="5", dict_type="sys_oper_type", css_class='{"color": "geekblue"}', list_class="warning", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="导出操作"),
        SysDictData(dict_code=24, dict_sort=6, dict_label="导入", dict_value="6", dict_type="sys_oper_type", css_class='{"color": "blue"}', list_class="warning", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="导入操作"),
        SysDictData(dict_code=25, dict_sort=7, dict_label="强退", dict_value="7", dict_type="sys_oper_type", css_class='{"color": "magenta"}', list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="强退操作"),
        SysDictData(dict_code=26, dict_sort=8, dict_label="生成代码", dict_value="8", dict_type="sys_oper_type", css_class='{"color": "cyan"}', list_class="warning", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="生成操作"),
        SysDictData(dict_code=27, dict_sort=9, dict_label="清空数据", dict_value="9", dict_type="sys_oper_type", css_class='{"color": "volcano"}', list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="清空操作"),
        SysDictData(dict_code=28, dict_sort=1, dict_label="成功", dict_value="0", dict_type="sys_common_status", css_class="", list_class="primary", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="正常状态"),
        SysDictData(dict_code=29, dict_sort=2, dict_label="失败", dict_value="1", dict_type="sys_common_status", css_class="", list_class="danger", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="停用状态"),
        SysDictData(dict_code=100, dict_sort=3, dict_label="Redis", dict_value="redis", dict_type="sys_job_group", css_class='{"color": "gold"}', list_class="default", is_default="N", status=0, create_by="admin", create_time=str2datetime("2023-08-27 22:52:05"), update_by="admin", update_time=str2datetime("2023-08-27 22:52:05"), remark="redis分组"),
        SysDictType(dict_id=1, dict_name="用户性别", dict_type="sys_user_sex", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="用户性别列表"),
        SysDictType(dict_id=2, dict_name="菜单状态", dict_type="sys_show_hide", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="菜单状态列表"),
        SysDictType(dict_id=3, dict_name="系统开关", dict_type="sys_normal_disable", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="admin", update_time=str2datetime("2023-08-18 11:23:39"), remark="系统开关列表"),
        SysDictType(dict_id=4, dict_name="任务状态", dict_type="sys_job_status", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="任务状态列表"),
        SysDictType(dict_id=5, dict_name="任务分组", dict_type="sys_job_group", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="任务分组列表"),
        SysDictType(dict_id=6, dict_name="系统是否", dict_type="sys_yes_no", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="系统是否列表"),
        SysDictType(dict_id=7, dict_name="通知类型", dict_type="sys_notice_type", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="通知类型列表"),
        SysDictType(dict_id=8, dict_name="通知状态", dict_type="sys_notice_status", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="通知状态列表"),
        SysDictType(dict_id=9, dict_name="操作类型", dict_type="sys_oper_type", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="操作类型列表"),
        SysDictType(dict_id=10, dict_name="系统状态", dict_type="sys_common_status", status=0, create_by="admin", create_time=str2datetime("2023-02-11 22:23:38"), update_by="", update_time=None, remark="登录状态列表"),
        SysJob(job_id=1, job_name="系统默认（无参）", job_group="default", job_executor="default", invoke_target="module_task.scheduler_test.job", job_args="test", job_kwargs=None, cron_expression="0/10 * * * * ?", misfire_policy="2", concurrent="0", status=1, create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="admin", update_time=str2datetime("2023-05-23 16:13:34"), remark=""),
        SysJob(job_id=2, job_name="系统默认（有参）", job_group="sqlalchemy", job_executor="default", invoke_target="module_task.scheduler_test.job", job_args="new", job_kwargs='{"test": 111}', cron_expression="0/15 * * * * ?", misfire_policy="1", concurrent="1", status=1, create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="admin", update_time=str2datetime("2023-05-23 16:13:34"), remark=""),
        SysJob(job_id=3, job_name="系统默认（多参）", job_group="redis", job_executor="default", invoke_target="module_task.scheduler_test.job", job_args=None, job_kwargs=None, cron_expression="0/20 * * * * ?", misfire_policy="3", concurrent="1", status=1, create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="", update_time=None, remark=""),
        SysNotice(notice_id=1, notice_title="温馨提醒：2024-07-01 若依新版本发布啦", notice_type=2, notice_content="0xE696B0E78988E69CACE58685E5AEB9", status=0, create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="", update_time=None, remark="管理员"),
        SysNotice(notice_id=2, notice_title="维护通知：2024-07-01 若依系统凌晨维护", notice_type=1, notice_content="0xE7BBB4E68AA4E58685E5AEB9", status=0, create_by="admin", create_time=str2datetime("2023-05-23 16:13:34"), update_by="", update_time=None, remark="管理员"),
        SysPost(post_id=1, post_code="ceo", post_name="董事长", post_sort=1, status=0, create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysPost(post_id=2, post_code="se", post_name="项目经理", post_sort=2, status=0, create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysPost(post_id=3, post_code="hr", post_name="人力资源", post_sort=3, status=0, create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="ry", update_time=str2datetime("2023-06-05 15:49:31"), remark=""),
        SysPost(post_id=4, post_code="user", post_name="普通员工", post_sort=4, status=0, create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
    ]
    items += [
        SysMenu(menu_id=1, menu_name="系统管理", parent_id=0, order_num=3, path="/system", component=None, query="", is_frame=1, is_cache=0, menu_type="M", visible="0", status=0, perms="", icon="antd-setting", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="系统管理目录"),
        SysMenu(menu_id=2, menu_name="系统监控", parent_id=0, order_num=4, path="/monitor", component=None, query="", is_frame=1, is_cache=0, menu_type="M", visible="0", status=0, perms="", icon="antd-fund-projection-screen", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="系统监控目录"),
        SysMenu(menu_id=3, menu_name="开发者工具", parent_id=0, order_num=5, path="/tool", component=None, query="", is_frame=1, is_cache=0, menu_type="M", visible="0", status=0, perms="", icon="antd-repair", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="开发者工具目录"),
        SysMenu(menu_id=4, menu_name="Github", parent_id=0, order_num=6, path="http://github.com/LinXueyuanStdio", component=None, query=None, is_frame=0, is_cache=0, menu_type="M", visible="0", status=0, perms="", icon="antd-send", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="Github"),
        SysMenu(menu_id=100, menu_name="用户管理", parent_id=1, order_num=1, path="/system/user", component="system.user", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:user:list", icon="antd-user", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="用户管理菜单"),
        SysMenu(menu_id=101, menu_name="角色管理", parent_id=1, order_num=2, path="/system/role", component="system.role", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:role:list", icon="antd-team", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="角色管理菜单"),
        SysMenu(menu_id=102, menu_name="菜单管理", parent_id=1, order_num=3, path="/system/menu", component="system.menu", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:menu:list", icon="antd-app-store-add", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="菜单管理菜单"),
        SysMenu(menu_id=103, menu_name="部门管理", parent_id=1, order_num=4, path="/system/dept", component="system.dept", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:dept:list", icon="antd-cluster", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="部门管理菜单"),
        SysMenu(menu_id=104, menu_name="岗位管理", parent_id=1, order_num=5, path="/system/post", component="system.post", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:post:list", icon="antd-idcard", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="ry", update_time=str2datetime("2023-07-06 09:47:26"), remark="岗位管理菜单"),
        SysMenu(menu_id=105, menu_name="字典管理", parent_id=1, order_num=6, path="/system/dict", component="system.dict", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:dict:list", icon="antd-read", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="ry", update_time=str2datetime("2023-07-06 16:25:44"), remark="字典管理菜单"),
        SysMenu(menu_id=106, menu_name="参数设置", parent_id=1, order_num=7, path="/system/config", component="system.config", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:config:list", icon="antd-calculator", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="参数设置菜单"),
        SysMenu(menu_id=107, menu_name="通知公告", parent_id=1, order_num=8, path="/system/notice", component="system.notice", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="system:notice:list", icon="antd-notification", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="通知公告菜单"),
        SysMenu(menu_id=108, menu_name="日志管理", parent_id=1, order_num=9, path="/log", component="", query="", is_frame=1, is_cache=0, menu_type="M", visible="0", status=0, perms="", icon="antd-bug", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="日志管理菜单"),
        SysMenu(menu_id=1081, menu_name="操作日志", parent_id=108, order_num=1, path="/monitor/operlog", component="monitor.operlog", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:operlog:list", icon="antd-clear", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="操作日志菜单"),
        SysMenu(menu_id=1039, menu_name="操作查询", parent_id=1081, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:operlog:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1040, menu_name="操作删除", parent_id=1081, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:operlog:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1041, menu_name="日志导出", parent_id=1081, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:operlog:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1082, menu_name="登录日志", parent_id=108, order_num=2, path="/monitor/logininfor", component="monitor.logininfor", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:logininfor:list", icon="antd-control", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="登录日志菜单"),
        SysMenu(menu_id=1042, menu_name="登录查询", parent_id=1082, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:logininfor:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1043, menu_name="登录删除", parent_id=1082, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:logininfor:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1044, menu_name="日志导出", parent_id=1082, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:logininfor:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1045, menu_name="账户解锁", parent_id=1082, order_num=4, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:logininfor:unlock", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=109, menu_name="在线用户", parent_id=2, order_num=1, path="/monitor/online", component="monitor.online", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:online:list", icon="antd-desktop", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="在线用户菜单"),
        SysMenu(menu_id=110, menu_name="定时任务", parent_id=2, order_num=2, path="/monitor/job", component="monitor.job", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:job:list", icon="antd-deployment-unit", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="定时任务菜单"),
        SysMenu(menu_id=111, menu_name="数据监控", parent_id=2, order_num=3, path="/monitor/druid", component="monitor.druid", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:druid:list", icon="antd-database", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="数据监控菜单"),
        SysMenu(menu_id=112, menu_name="服务监控", parent_id=2, order_num=4, path="/monitor/server", component="monitor.server", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:server:list", icon="antd-cloud-server", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="服务监控菜单"),
        SysMenu(menu_id=113, menu_name="缓存监控", parent_id=2, order_num=5, path="/monitor/cache/control", component="monitor.cache.control", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:cache:list", icon="antd-cloud-sync", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="admin", update_time=str2datetime("2023-08-11 10:52:56"), remark="缓存监控菜单"),
        SysMenu(menu_id=114, menu_name="缓存列表", parent_id=2, order_num=6, path="/monitor/cache/list", component="monitor.cache.list", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="monitor:cache:list", icon="antd-table", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="admin", update_time=str2datetime("2023-08-11 10:53:11"), remark="缓存列表菜单"),
        SysMenu(menu_id=115, menu_name="表单构建", parent_id=3, order_num=1, path="/tool/build", component="tool.build", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="tool:build:list", icon="antd-build", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="表单构建菜单"),
        SysMenu(menu_id=116, menu_name="代码生成", parent_id=3, order_num=2, path="/tool/gen", component="tool.gen", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="tool:gen:list", icon="antd-console-sql", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="代码生成菜单"),
        SysMenu(menu_id=117, menu_name="系统接口", parent_id=3, order_num=3, path="/tool/swagger", component="tool.swagger", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", status=0, perms="tool:swagger:list", icon="antd-api", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark="系统接口菜单"),
        SysMenu(menu_id=1000, menu_name="用户查询", parent_id=100, order_num=1, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:user:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1001, menu_name="用户新增", parent_id=100, order_num=2, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:user:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1002, menu_name="用户修改", parent_id=100, order_num=3, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:user:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1003, menu_name="用户删除", parent_id=100, order_num=4, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:user:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1004, menu_name="用户导出", parent_id=100, order_num=5, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:user:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1005, menu_name="用户导入", parent_id=100, order_num=6, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:user:import", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1006, menu_name="重置密码", parent_id=100, order_num=7, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:user:resetPwd", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1007, menu_name="角色查询", parent_id=101, order_num=1, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:role:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1008, menu_name="角色新增", parent_id=101, order_num=2, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:role:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1009, menu_name="角色修改", parent_id=101, order_num=3, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:role:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1010, menu_name="角色删除", parent_id=101, order_num=4, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:role:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1011, menu_name="角色导出", parent_id=101, order_num=5, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:role:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1012, menu_name="菜单查询", parent_id=102, order_num=1, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:menu:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1013, menu_name="菜单新增", parent_id=102, order_num=2, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:menu:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1014, menu_name="菜单修改", parent_id=102, order_num=3, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:menu:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1015, menu_name="菜单删除", parent_id=102, order_num=4, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:menu:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1016, menu_name="部门查询", parent_id=103, order_num=1, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dept:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1017, menu_name="部门新增", parent_id=103, order_num=2, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dept:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1018, menu_name="部门修改", parent_id=103, order_num=3, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dept:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1019, menu_name="部门删除", parent_id=103, order_num=4, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dept:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1020, menu_name="岗位查询", parent_id=104, order_num=1, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:post:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1021, menu_name="岗位新增", parent_id=104, order_num=2, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:post:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1022, menu_name="岗位修改", parent_id=104, order_num=3, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:post:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1023, menu_name="岗位删除", parent_id=104, order_num=4, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:post:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1024, menu_name="岗位导出", parent_id=104, order_num=5, path="", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:post:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1025, menu_name="字典查询", parent_id=105, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dict:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1026, menu_name="字典新增", parent_id=105, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dict:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1027, menu_name="字典修改", parent_id=105, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dict:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1028, menu_name="字典删除", parent_id=105, order_num=4, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dict:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1029, menu_name="字典导出", parent_id=105, order_num=5, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:dict:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1030, menu_name="参数查询", parent_id=106, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:config:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1031, menu_name="参数新增", parent_id=106, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:config:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1032, menu_name="参数修改", parent_id=106, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:config:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1033, menu_name="参数删除", parent_id=106, order_num=4, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:config:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1034, menu_name="参数导出", parent_id=106, order_num=5, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:config:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1035, menu_name="公告查询", parent_id=107, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:notice:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1036, menu_name="公告新增", parent_id=107, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:notice:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1037, menu_name="公告修改", parent_id=107, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:notice:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1038, menu_name="公告删除", parent_id=107, order_num=4, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="system:notice:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1046, menu_name="在线查询", parent_id=109, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:online:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1047, menu_name="批量强退", parent_id=109, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:online:batchLogout", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1048, menu_name="单条强退", parent_id=109, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:online:forceLogout", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1049, menu_name="任务查询", parent_id=110, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:job:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1050, menu_name="任务新增", parent_id=110, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:job:add", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1051, menu_name="任务修改", parent_id=110, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:job:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1052, menu_name="任务删除", parent_id=110, order_num=4, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:job:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1053, menu_name="状态修改", parent_id=110, order_num=5, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:job:changeStatus", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1054, menu_name="任务导出", parent_id=110, order_num=6, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="monitor:job:export", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1055, menu_name="生成查询", parent_id=116, order_num=1, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="tool:gen:query", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1056, menu_name="生成修改", parent_id=116, order_num=2, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="tool:gen:edit", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1057, menu_name="生成删除", parent_id=116, order_num=3, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="tool:gen:remove", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1058, menu_name="导入代码", parent_id=116, order_num=4, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="tool:gen:import", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1059, menu_name="预览代码", parent_id=116, order_num=5, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="tool:gen:preview", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysMenu(menu_id=1060, menu_name="生成代码", parent_id=116, order_num=6, path="#", component="", query="", is_frame=1, is_cache=0, menu_type="F", visible="0", status=0, perms="tool:gen:code", icon="#", create_by="admin", create_time=str2datetime("2023-05-23 16:13:33"), update_by="", update_time=None, remark=""),
        SysRole(role_id=1, role_name="超级管理员", role_key="admin", role_sort=1, data_scope="1", menu_check_strictly=1, dept_check_strictly=1, remark="超级管理员", **admin_creation),
        SysRole(role_id=2, role_name="普通角色", role_key="common", role_sort=2, data_scope="2", menu_check_strictly=1, dept_check_strictly=1, remark="普通角色", **admin_creation),
        SysRoleMenu(role_id=1, menu_id=1),
        SysRoleMenu(role_id=1, menu_id=2),
        SysRoleMenu(role_id=1, menu_id=3),
        SysRoleMenu(role_id=1, menu_id=4),
        SysRoleMenu(role_id=1, menu_id=5),
        SysRoleMenu(role_id=1, menu_id=6),
        SysRoleMenu(role_id=1, menu_id=601),
        SysRoleMenu(role_id=1, menu_id=6011),
        SysRoleMenu(role_id=1, menu_id=6012),
        SysRoleMenu(role_id=1, menu_id=6013),
        SysRoleMenu(role_id=1, menu_id=6014),
        SysRoleMenu(role_id=1, menu_id=602),
        SysRoleMenu(role_id=1, menu_id=6021),
        SysRoleMenu(role_id=1, menu_id=6022),
        SysRoleMenu(role_id=1, menu_id=6023),
        SysRoleMenu(role_id=1, menu_id=6024),
        SysRoleMenu(role_id=1, menu_id=100),
        SysRoleMenu(role_id=1, menu_id=101),
        SysRoleMenu(role_id=1, menu_id=102),
        SysRoleMenu(role_id=1, menu_id=103),
        SysRoleMenu(role_id=1, menu_id=104),
        SysRoleMenu(role_id=1, menu_id=105),
        SysRoleMenu(role_id=1, menu_id=106),
        SysRoleMenu(role_id=1, menu_id=107),
        SysRoleMenu(role_id=1, menu_id=108),
        SysRoleMenu(role_id=1, menu_id=109),
        SysRoleMenu(role_id=1, menu_id=110),
        SysRoleMenu(role_id=1, menu_id=111),
        SysRoleMenu(role_id=1, menu_id=112),
        SysRoleMenu(role_id=1, menu_id=113),
        SysRoleMenu(role_id=1, menu_id=114),
        SysRoleMenu(role_id=1, menu_id=115),
        SysRoleMenu(role_id=1, menu_id=116),
        SysRoleMenu(role_id=1, menu_id=117),
        SysRoleMenu(role_id=1, menu_id=1081),
        SysRoleMenu(role_id=1, menu_id=1082),
        SysRoleMenu(role_id=1, menu_id=1000),
        SysRoleMenu(role_id=1, menu_id=1001),
        SysRoleMenu(role_id=1, menu_id=1002),
        SysRoleMenu(role_id=1, menu_id=1003),
        SysRoleMenu(role_id=1, menu_id=1004),
        SysRoleMenu(role_id=1, menu_id=1005),
        SysRoleMenu(role_id=1, menu_id=1006),
        SysRoleMenu(role_id=1, menu_id=1007),
        SysRoleMenu(role_id=1, menu_id=1008),
        SysRoleMenu(role_id=1, menu_id=1009),
        SysRoleMenu(role_id=1, menu_id=1010),
        SysRoleMenu(role_id=1, menu_id=1011),
        SysRoleMenu(role_id=1, menu_id=1012),
        SysRoleMenu(role_id=1, menu_id=1013),
        SysRoleMenu(role_id=1, menu_id=1014),
        SysRoleMenu(role_id=1, menu_id=1015),
        SysRoleMenu(role_id=1, menu_id=1016),
        SysRoleMenu(role_id=1, menu_id=1017),
        SysRoleMenu(role_id=1, menu_id=1018),
        SysRoleMenu(role_id=1, menu_id=1019),
        SysRoleMenu(role_id=1, menu_id=1020),
        SysRoleMenu(role_id=1, menu_id=1021),
        SysRoleMenu(role_id=1, menu_id=1022),
        SysRoleMenu(role_id=1, menu_id=1023),
        SysRoleMenu(role_id=1, menu_id=1024),
        SysRoleMenu(role_id=1, menu_id=1025),
        SysRoleMenu(role_id=1, menu_id=1026),
        SysRoleMenu(role_id=1, menu_id=1027),
        SysRoleMenu(role_id=1, menu_id=1028),
        SysRoleMenu(role_id=1, menu_id=1029),
        SysRoleMenu(role_id=1, menu_id=1030),
        SysRoleMenu(role_id=1, menu_id=1031),
        SysRoleMenu(role_id=1, menu_id=1032),
        SysRoleMenu(role_id=1, menu_id=1033),
        SysRoleMenu(role_id=1, menu_id=1034),
        SysRoleMenu(role_id=1, menu_id=1035),
        SysRoleMenu(role_id=1, menu_id=1036),
        SysRoleMenu(role_id=1, menu_id=1037),
        SysRoleMenu(role_id=1, menu_id=1038),
        SysRoleMenu(role_id=1, menu_id=1039),
        SysRoleMenu(role_id=1, menu_id=1040),
        SysRoleMenu(role_id=1, menu_id=1041),
        SysRoleMenu(role_id=1, menu_id=1042),
        SysRoleMenu(role_id=1, menu_id=1043),
        SysRoleMenu(role_id=1, menu_id=1044),
        SysRoleMenu(role_id=1, menu_id=1045),
        SysRoleMenu(role_id=1, menu_id=1046),
        SysRoleMenu(role_id=1, menu_id=1047),
        SysRoleMenu(role_id=1, menu_id=1048),
        SysRoleMenu(role_id=1, menu_id=1049),
        SysRoleMenu(role_id=1, menu_id=1050),
        SysRoleMenu(role_id=1, menu_id=1051),
        SysRoleMenu(role_id=1, menu_id=1052),
        SysRoleMenu(role_id=1, menu_id=1053),
        SysRoleMenu(role_id=1, menu_id=1054),
        SysRoleMenu(role_id=1, menu_id=1055),
        SysRoleMenu(role_id=1, menu_id=1056),
        SysRoleMenu(role_id=1, menu_id=1057),
        SysRoleMenu(role_id=1, menu_id=1058),
        SysRoleMenu(role_id=1, menu_id=1059),
        SysRoleMenu(role_id=1, menu_id=1060),
        SysRoleMenu(role_id=2, menu_id=1035),
        SysUser(user_id=1, dept_id=103, user_name="admin", nick_name="超级管理员", user_type="00", email="linxy59@mail2.sysu.edu.cn", phonenumber="18811572707", sex="1", avatar="/common/cache?taskPath=avatar&taskId=admin&filename=空.jpg", password=PwdUtil.get_password_hash("admin123"), login_ip="127.0.0.1", login_date=str2datetime("2023-05-23 16:13:33"), remark="管理员", **admin_creation),
        SysUser(user_id=2, dept_id=105, user_name="linxueyuan", nick_name="林学渊", user_type="00", email="linxy59@mail2.sysu.edu.cn", phonenumber="18811572707", sex="0", avatar="/common/cache?taskPath=avatar&taskId=linxueyuan&filename=荧.jpg", password=PwdUtil.get_password_hash("123456"), login_ip="127.0.0.1", login_date=str2datetime("2023-05-23 16:13:33"), remark="测试员", **admin_creation),
        SysUserRole(user_id=1, role_id=1),
        SysUserRole(user_id=2, role_id=2),
        SysDept(dept_id=100, parent_id=0, ancestors=[0], dept_name="集团总公司", order_num=1, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=101, parent_id=100, ancestors=[0, 100], dept_name="上海分公司", order_num=1, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=103, parent_id=101, ancestors=[0, 100, 101], dept_name="研发部门", order_num=1, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=104, parent_id=101, ancestors=[0, 100, 101], dept_name="市场部门", order_num=2, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=105, parent_id=101, ancestors=[0, 100, 101], dept_name="测试部门", order_num=3, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=106, parent_id=101, ancestors=[0, 100, 101], dept_name="财务部门", order_num=4, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=107, parent_id=101, ancestors=[0, 100, 101], dept_name="运维部门", order_num=5, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=102, parent_id=100, ancestors=[0, 100], dept_name="广东分公司", order_num=2, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=108, parent_id=102, ancestors=[0, 100, 102], dept_name="市场部门", order_num=1, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysDept(dept_id=109, parent_id=102, ancestors=[0, 100, 102], dept_name="财务部门", order_num=2, leader="兮尘", phone="18811572707", email="linxy59@mail2.sysu.edu.cn"),
        SysRoleDept(dept_id=100, role_id=1),
        SysRoleDept(dept_id=101, role_id=1),
        SysRoleDept(dept_id=103, role_id=1),
        SysRoleDept(dept_id=105, role_id=2),
    ]
    items += sum(
        [
            crud_menus(name="API Key", parent_id=0, order_num=8, path="/apikey", component="client.apikey", icon="antd-insurance", remark="Apikey目录", prem_prefix="client:apikey", role_id=2),
            crud_menus(name="Billing", parent_id=0, order_num=10000, path="/billing", component="client.billing", icon="antd-money-collect", remark="账单", prem_prefix="client:billing", role_id=2, editor=False),
        ],
        [],
    )
    items += [
        SysMenu(menu_id=7, menu_name="Usage", parent_id=0, order_num=7, path="/usage", component="client.usage", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", perms="", icon="fc-line-chart", remark="Usage", **admin_creation),
        SysMenu(menu_id=9, menu_name="Buy", parent_id=0, order_num=9, path="/buy", component="client.buy", query="", is_frame=1, is_cache=0, menu_type="C", visible="0", perms="", icon="antd-shopping-cart", remark="Buy", **admin_creation),
        SysRoleMenu(role_id=2, menu_id=7),
        SysRoleMenu(role_id=2, menu_id=9),
    ]
    for item in items:
        db.add(item)
    db.commit()

    user_id = 1
    new_auth_key = saas_secure.create_auth_key(user_id)
    api_key = saas_schema.ApiKeyCreationModel(name="Agent", auth_key=new_auth_key, create_by="admin")
    db_api_key = CrudDao.create_one(db, saas_schema.ApiKey, api_key)
    new_auth_key = saas_secure.create_auth_key(user_id)
    api_key = saas_schema.ApiKeyCreationModel(name="Agent2", auth_key=new_auth_key, create_by="admin")
    db_api_key = CrudDao.create_one(db, saas_schema.ApiKey, api_key)
    new_auth_key = saas_secure.create_auth_key(user_id)
    api_key = saas_schema.ApiKeyCreationModel(name="Agent3", auth_key=new_auth_key, create_by="admin")
    db_api_key = CrudDao.create_one(db, saas_schema.ApiKey, api_key)


