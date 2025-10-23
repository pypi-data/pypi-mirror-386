from typing import List, Optional, Type, TypeVar
from pydantic import BaseModel
from sqlalchemy.ext.declarative import DeclarativeMeta as Model
from sqlalchemy.orm import Session

T = TypeVar("T", bound=Model)
M = TypeVar("M", bound=BaseModel)


class CrudDao:
    @staticmethod
    def exists(db: Session, db_model: Type[T], item_id: int) -> bool:
        _pk: str = db_model.__table__.primary_key.columns.keys()[0]
        q = db.query(db_model)
        conditions = []
        conditions.append(getattr(db_model, _pk) == item_id)
        if hasattr(db_model, "del_flag"):
            conditions.append(db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        result = q.count() > 0
        return result

    @staticmethod
    def get_all(db: Session, db_model: Type[T], query: BaseModel) -> List[T]:
        q = db.query(db_model)
        conditions = []
        if hasattr(db_model, "del_flag"):
            conditions.append(db_model.del_flag == 0)
        if hasattr(db_model, "status") and query.status:
            conditions.append(db_model.status == query.status)
        if hasattr(db_model, "name") and query.name:
            conditions.append(db_model.name.like(f"%{query.name}%"))
        if len(conditions) > 0:
            q = q.filter(*conditions)
        query_result = q.order_by(db_model.order_num).all()
        return query_result

    @staticmethod
    def get_model_detail_by_id(db: Session, db_model: Type[T], item_id: int) -> Optional[T]:
        """
        根据数据id获取数据详细信息
        :param db: orm对象
        :param item_id: 数据id
        :return: 数据信息对象
        """
        _pk: str = db_model.__table__.primary_key.columns.keys()[0]
        q = db.query(db_model)
        conditions = []
        conditions.append(getattr(db_model, _pk) == item_id)
        if hasattr(db_model, "del_flag"):
            conditions.append(db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        model_info = q.first()
        return model_info

    @staticmethod
    def get_all_ancestors(db: Session, db_model: Type[T]) -> List[T]:
        """
        获取所有数据的ancestors信息
        :param db: orm对象
        :return: ancestors信息列表
        """
        q = db.query(db_model.ancestors)
        if hasattr(db_model, "del_flag"):
            q = q.filter(getattr(db_model, "del_flag") == 0)
        ancestors = q.all()
        return ancestors

    @staticmethod
    def create_one(db: Session, db_model: Type[T], model: M) -> T:
        """
        新增数据数据库操作
        :param db: orm对象
        :param model: 数据对象
        :return: 新增校验结果
        """
        db_model = db_model(**model.model_dump(exclude_unset=True, exclude_none=True, exclude_defaults=True))
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        return db_model

    @staticmethod
    def update_one(db: Session, db_model: Type[T], item_id: int, model: M) -> T:
        """
        更新数据数据库操作
        :param db: orm对象
        :param item_id: 数据id
        :param model: 数据对象
        :return: 更新校验结果
        """
        _pk: str = db_model.__table__.primary_key.columns.keys()[0]
        q = db.query(db_model)
        conditions = []
        conditions.append(getattr(db_model, _pk) == item_id)
        if hasattr(db_model, "del_flag"):
            conditions.append(db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        db_model = q.first()
        if db_model is None:
            return None
        for key, value in model.model_dump(exclude={_pk}, exclude_unset=True, exclude_none=True, exclude_defaults=True).items():
            if hasattr(db_model, key):
                setattr(db_model, key, value)
        db.commit()
        db.refresh(db_model)
        return db_model

    @staticmethod
    def delete_one(db: Session, db_model: Type[T], item_id: int) -> T:
        """
        删除数据数据库操作
        :param db: orm对象
        :param item_id: 数据id
        :return: 删除校验结果
        """
        q = db.query(db_model)
        conditions = []
        _pk: str = db_model.__table__.primary_key.columns.keys()[0]
        conditions.append(getattr(db_model, _pk) == item_id)
        if hasattr(db_model, "del_flag"):
            conditions.append(db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        db_model = q.first()
        if db_model is None:
            return None
        if hasattr(db_model, "del_flag"):
            setattr(db_model, "del_flag", 2)
        else:
            db.delete(db_model)
        db.commit()
        return db_model

    @staticmethod
    def delete_all(db: Session, db_model: Type[T]) -> List[T]:
        """
        删除所有数据数据库操作
        :param db: orm对象
        :return: 删除校验结果列表
        """
        q = db.query(db_model)
        if hasattr(db_model, "del_flag"):
            q = q.filter(db_model.del_flag == 0)
        models = q.all()
        for model in models:
            if hasattr(model, "del_flag"):
                setattr(model, "del_flag", 2)
            else:
                db.delete(model)
        db.commit()
        return models


class TreeDao:

    @staticmethod
    def list_to_tree(data_list: list, _pk: str) -> list:
        """
        工具方法：根据数据列表信息生成树形嵌套数据
        :param data_list: 数据列表信息
        :return: 数据树形嵌套数据
        """
        data_list = [
            dict(
                title=item.name,
                key=str(getattr(item, _pk)),
                value=str(getattr(item, _pk)),
                parent_id=str(item.parent_id),
                item_id=item.item_id,
            )
            for item in data_list
        ]
        # 转成model_id为key的字典
        mapping: dict = dict(zip([i["key"] for i in data_list], data_list))

        # 树容器
        container: list = []

        for d in data_list:
            # 如果找不到父级项，则是根节点
            parent: dict = mapping.get(d["parent_id"])
            if parent is None:
                container.append(d)
            else:
                children: list = parent.get("children")
                if not children:
                    children = []
                children.append(d)
                parent.update({"children": children})

        return container
