from datetime import datetime, time

from sqlalchemy.orm import Session

from backlin.module_admin.entity.do.config_do import SysConfig
from backlin.module_admin.entity.vo.config_vo import ConfigModel, ConfigQueryModel
from backlin.utils.time_format_util import list_format_datetime


class ConfigDao:
    """
    参数配置管理模块数据库操作层
    """

    @classmethod
    def get_config_detail_by_id(cls, db: Session, config_id: int):
        """
        根据参数配置id获取参数配置详细信息
        :param db: orm对象
        :param config_id: 参数配置id
        :return: 参数配置信息对象
        """
        config_info = db.query(SysConfig) \
            .filter(SysConfig.config_id == config_id) \
            .first()

        return config_info

    @classmethod
    def get_config_detail_by_info(cls, db: Session, config: ConfigModel):
        """
        根据参数配置参数获取参数配置信息
        :param db: orm对象
        :param config: 参数配置参数对象
        :return: 参数配置信息对象
        """
        config_info = db.query(SysConfig) \
            .filter(SysConfig.config_key == config.config_key if config.config_key else True,
                    SysConfig.config_value == config.config_value if config.config_value else True) \
            .first()

        return config_info

    @classmethod
    def get_all_config(cls, db: Session):
        """
        获取所有的参数配置信息
        :param db: orm对象
        :return: 参数配置信息列表对象
        """
        config_info = db.query(SysConfig).all()

        return list_format_datetime(config_info)

    @classmethod
    def get_config_list(cls, db: Session, query_object: ConfigQueryModel):
        """
        根据查询参数获取参数配置列表信息
        :param db: orm对象
        :param query_object: 查询参数对象
        :return: 参数配置列表信息对象
        """
        config_list = db.query(SysConfig) \
            .filter(SysConfig.config_name.like(f'%{query_object.config_name}%') if query_object.config_name else True,
                    SysConfig.config_key.like(f'%{query_object.config_key}%') if query_object.config_key else True,
                    SysConfig.config_type == query_object.config_type if query_object.config_type else True,
                    SysConfig.create_time.between(
                        datetime.combine(datetime.strptime(query_object.create_time_start, '%Y-%m-%d'), time(00, 00, 00)),
                        datetime.combine(datetime.strptime(query_object.create_time_end, '%Y-%m-%d'), time(23, 59, 59)))
                    if query_object.create_time_start and query_object.create_time_end else True
                    ) \
            .distinct().all()

        return list_format_datetime(config_list)

    @classmethod
    def add_config_dao(cls, db: Session, config: ConfigModel):
        """
        新增参数配置数据库操作
        :param db: orm对象
        :param config: 参数配置对象
        :return:
        """
        db_config = SysConfig(**config.dict())
        db.add(db_config)
        db.flush()

        return db_config

    @classmethod
    def edit_config_dao(cls, db: Session, config: dict):
        """
        编辑参数配置数据库操作
        :param db: orm对象
        :param config: 需要更新的参数配置字典
        :return:
        """
        db.query(SysConfig) \
            .filter(SysConfig.config_id == config.get('config_id')) \
            .update(config)

    @classmethod
    def delete_config_dao(cls, db: Session, config: ConfigModel):
        """
        删除参数配置数据库操作
        :param db: orm对象
        :param config: 参数配置对象
        :return:
        """
        db.query(SysConfig) \
            .filter(SysConfig.config_id == config.config_id) \
            .delete()
