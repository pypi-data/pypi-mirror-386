import json
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_ALL

from backlin.database import engine, SQLALCHEMY_DATABASE_URL, SessionLocal
from backlin.config.env import RedisConfig
from backlin.module_admin.service.job_log_service import JobLogService, JobLogModel
from backlin.module_admin.dao.job_dao import Session, JobDao
from backlin.utils.log_util import logger


# 重写Cron定时
class MyCronTrigger(CronTrigger):
    @classmethod
    def from_crontab(cls, expr, timezone=None):
        values = expr.split()
        if len(values) != 6 and len(values) != 7:
            raise ValueError('Wrong number of fields; got {}, expected 6 or 7'.format(len(values)))

        second = values[0]
        minute = values[1]
        hour = values[2]
        if '?' in values[3]:
            day = None
        elif 'L' in values[5]:
            day = f"last {values[5].replace('L', '')}"
        elif 'W' in values[3]:
            day = cls.__find_recent_workday(int(values[3].split('W')[0]))
        else:
            day = values[3].replace('L', 'last')
        month = values[4]
        if '?' in values[5] or 'L' in values[5]:
            week = None
        elif '#' in values[5]:
            week = int(values[5].split('#')[1])
        else:
            week = values[5]
        if '#' in values[5]:
            day_of_week = int(values[5].split('#')[0]) - 1
        else:
            day_of_week = None
        year = values[6] if len(values) == 7 else None
        return cls(second=second, minute=minute, hour=hour, day=day, month=month, week=week,
                   day_of_week=day_of_week, year=year, timezone=timezone)

    @classmethod
    def __find_recent_workday(cls, day):
        now = datetime.now()
        date = datetime(now.year, now.month, day)
        if date.weekday() < 5:
            return date.day
        else:
            diff = 1
            while True:
                previous_day = date - timedelta(days=diff)
                if previous_day.weekday() < 5:
                    return previous_day.day
                else:
                    diff += 1


job_stores = {
    'default': MemoryJobStore(),
    'sqlalchemy': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL, engine=engine),
    'redis': RedisJobStore(
        db=RedisConfig.redis_database,
        host=RedisConfig.redis_host,
        port=RedisConfig.redis_port,
        username=RedisConfig.redis_username,
        password=RedisConfig.redis_password,
    )
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instance': 1
}
scheduler = BackgroundScheduler()
scheduler.configure(jobstores=job_stores, executors=executors, job_defaults=job_defaults)


class SchedulerUtil:
    """
    定时任务相关方法
    """

    @classmethod
    async def init_system_scheduler(cls, result_db: Session = SessionLocal()):
        """
        应用启动时初始化定时任务
        :return:
        """
        logger.info("开始启动定时任务...")
        scheduler.start()
        job_list = JobDao.get_job_list_for_scheduler(result_db)
        for item in job_list:
            query_job = cls.get_scheduler_job(job_id=str(item.job_id))
            if query_job:
                cls.remove_scheduler_job(job_id=str(item.job_id))
            cls.add_scheduler_job(item)
        result_db.close()
        scheduler.add_listener(cls.scheduler_event_listener, EVENT_ALL)
        logger.info("系统初始定时任务加载成功")

    @classmethod
    async def close_system_scheduler(cls):
        """
        应用关闭时关闭定时任务
        :return:
        """
        scheduler.shutdown()
        logger.info("关闭定时任务成功")

    @classmethod
    def get_scheduler_job(cls, job_id):
        """
        根据任务id获取任务对象
        :param job_id: 任务id
        :return: 任务对象
        """
        query_job = scheduler.get_job(job_id=str(job_id))

        return query_job

    @classmethod
    def add_scheduler_job(cls, job_info):
        """
        根据输入的任务对象信息添加任务
        :param job_info: 任务对象信息
        :return:
        """
        scheduler.add_job(
            func=eval(job_info.invoke_target),
            trigger=MyCronTrigger.from_crontab(job_info.cron_expression),
            args=job_info.job_args.split(',') if job_info.job_args else None,
            kwargs=json.loads(job_info.job_kwargs) if job_info.job_kwargs else None,
            id=str(job_info.job_id),
            name=job_info.job_name,
            misfire_grace_time=1000000000000 if job_info.misfire_policy == '3' else None,
            coalesce=True if job_info.misfire_policy == '2' else False,
            max_instances=3 if job_info.concurrent == '0' else 1,
            jobstore=job_info.job_group,
            executor=job_info.job_executor
        )

    @classmethod
    def execute_scheduler_job_once(cls, job_info):
        """
        根据输入的任务对象执行一次任务
        :param job_info: 任务对象信息
        :return:
        """
        scheduler.add_job(
            func=eval(job_info.invoke_target),
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            args=job_info.job_args.split(',') if job_info.job_args else None,
            kwargs=json.loads(job_info.job_kwargs) if job_info.job_kwargs else None,
            id=str(job_info.job_id),
            name=job_info.job_name,
            misfire_grace_time=1000000000000 if job_info.misfire_policy == '3' else None,
            coalesce=True if job_info.misfire_policy == '2' else False,
            max_instances=3 if job_info.concurrent == '0' else 1,
            jobstore=job_info.job_group,
            executor=job_info.job_executor
        )

    @classmethod
    def remove_scheduler_job(cls, job_id):
        """
        根据任务id移除任务
        :param job_id: 任务id
        :return:
        """
        scheduler.remove_job(job_id=str(job_id))

    @classmethod
    def scheduler_event_listener(cls, event):
        # 获取事件类型和任务ID
        event_type = event.__class__.__name__
        # 获取任务执行异常信息
        status = '0'
        exception_info = ''
        if event_type == 'JobExecutionEvent' and event.exception:
            exception_info = str(event.exception)
            status = '1'
        if not hasattr(event, "job_id"):
            return
        job_id = event.job_id
        query_job = cls.get_scheduler_job(job_id=job_id)
        if query_job:
            query_job_info = query_job.__getstate__()
            # 获取任务名称
            job_name = query_job_info.get('name')
            # 获取任务组名
            job_group = query_job._jobstore_alias
            # 获取任务执行器
            job_executor = query_job_info.get('executor')
            # 获取调用目标字符串
            invoke_target = query_job_info.get('func')
            # 获取调用函数位置参数
            job_args = ','.join(query_job_info.get('args'))
            # 获取调用函数关键字参数
            job_kwargs = json.dumps(query_job_info.get('kwargs'))
            # 获取任务触发器
            job_trigger = str(query_job_info.get('trigger'))
            # 构造日志消息
            job_message = f"事件类型: {event_type}, 任务ID: {job_id}, 任务名称: {job_name}, 执行于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            job_log = dict(
                job_name=job_name,
                job_group=job_group,
                job_executor=job_executor,
                invoke_target=invoke_target,
                job_args=job_args,
                job_kwargs=job_kwargs,
                job_trigger=job_trigger,
                job_message=job_message,
                status=status,
                exception_info=exception_info
            )
            session = SessionLocal()
            JobLogService.add_job_log_services(session, JobLogModel(**job_log))
            session.close()
