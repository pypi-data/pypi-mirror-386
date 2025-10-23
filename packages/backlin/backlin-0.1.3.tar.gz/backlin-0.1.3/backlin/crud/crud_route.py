from abc import ABC, abstractmethod
import math
from typing import Any, Callable, Generic, List, Optional, Tuple, Type, TypeAlias, Union, TypeVar

from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.types import DecoratedCallable
from fastapi_crudrouter.core._types import DEPENDENCIES, PAGINATION
from fastapi_crudrouter.core._utils import create_query_validation_exception

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta as Model
from sqlalchemy.exc import IntegrityError

import fastapi_crudrouter

from pydantic import BaseModel, Field, ConfigDict, create_model

from backlin.crud.crud_dao import CrudDao
from backlin.utils.response_util import *
from backlin.utils.log_util import *
from backlin.utils.common_util import bytes2file_response, export_list2excel
from backlin.module_admin.service.login_service import get_current_user, CurrentUserInfoServiceResponse
from backlin.module_admin.annotation.log_annotation import log_decorator


sqlalchemy_installed = True
CALLABLE = Callable[..., Model]
CALLABLE_LIST = Callable[..., List[Model]]
T = TypeVar("T", bound=BaseModel)
SCHEMA = BaseModel

# 定义模型配置，启用 `from_attributes`
class OrmConfig:
    model_config = ConfigDict(from_attributes=True)



def get_pk_type_patch(schema: Type[BaseModel], pk_field: str) -> Any:
    try:
        return schema.model_fields[pk_field].annotation
    except KeyError:
        return int


def schema_factory_patch(schema_cls: Type[T], pk_field_name: str = "id", name: str = "Create") -> Type[T]:
    """
    Is used to create a CreateSchema which does not contain pk
    """

    fields = {name: (f.annotation, ...) for name, f in schema_cls.model_fields.items() if name != pk_field_name}

    name = schema_cls.__name__ + name
    schema: Type[T] = create_model(name, **fields)  # type: ignore
    return schema


def pagination_factory(max_limit: Optional[int] = None) -> Any:
    """
    Created the pagination dependency to be used in the router
    """

    def pagination(page_num: int = 1, page_size: Optional[int] = max_limit) -> PAGINATION:
        if page_num < 1:
            raise create_query_validation_exception(
                field="page_num",
                msg="page_num query parameter must be greater or equal to one",
            )
        if page_size is not None:
            if page_size <= 0:
                raise create_query_validation_exception(
                    field="page_size", msg="page_size query parameter must be greater than zero"
                )

            elif max_limit and max_limit < page_size:
                raise create_query_validation_exception(
                    field="page_size",
                    msg=f"page_size query parameter must be less than {max_limit}",
                )
        else:
            page_size = max_limit

        offset = (page_num - 1) * page_size
        return {"skip": offset, "limit": page_size}

    return Depends(pagination)

fastapi_crudrouter.core._utils.get_pk_type = get_pk_type_patch
fastapi_crudrouter.core._utils.schema_factory = schema_factory_patch
fastapi_crudrouter.core._base.schema_factory = schema_factory_patch

NOT_FOUND = HTTPException(404, {"msg": "Item not found"})


class ActionResponse(BaseModel):
    """
    操作响应模型
    """

    is_success: bool
    message: str


class DeleteModel(BaseModel):
    """
    删除数据模型
    """

    item_ids: str


class ModelTree(BaseModel, Generic[T], OrmConfig):
    """
    数据树响应模型
    """

    tree: List[T] = []


class PageResponse(BaseModel, Generic[T], OrmConfig):
    """
    分页查询返回模型
    """

    rows: List[T] = []
    page_num: int
    page_size: int
    total: int
    has_next: bool

class SuccessResponse(BaseModel, Generic[T], OrmConfig):
    code: int
    message: str
    data: T
    success: bool
    time: str

class AllResponse(BaseModel, Generic[T], OrmConfig):
    """
    不分页查询返回模型
    """

    rows: List[T] = []


class CRUDGenerator(Generic[T], APIRouter, ABC):
    schema: Type[T]
    create_schema: Type[T]
    update_schema: Type[T]
    _base_path: str = "/"

    def __init__(
        self,
        schema: Type[T],
        create_schema: Optional[Type[T]] = None,
        update_schema: Optional[Type[T]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = 50,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_page_route: Union[bool, DEPENDENCIES] = True,
        get_tree_route: Union[bool, DEPENDENCIES] = True,
        get_tree_option_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        add_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        edit_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_some_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        export_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:

        self.schema: Type[T] = schema
        if not paginate:
            paginate = 50
        self.pagination = pagination_factory(max_limit=paginate)
        self._pk: str = self._pk if hasattr(self, "_pk") else "id"
        self.create_schema = create_schema if create_schema else schema_factory_patch(self.schema, pk_field_name=self._pk, name="Create")
        self.update_schema = update_schema if update_schema else schema_factory_patch(self.schema, pk_field_name=self._pk, name="Update")

        prefix = str(prefix if prefix else self.schema.__name__).lower()
        prefix = self._base_path + prefix.strip("/")
        tags = tags or [prefix.strip("/").capitalize()]

        super().__init__(prefix=prefix, tags=tags, **kwargs)

        if get_all_route:
            self._add_api_route(
                "/all",
                self._get_all(),
                methods=["GET"],
                response_model=SuccessResponse[AllResponse[self.schema]],  # type: ignore
                summary="Get All",
                dependencies=get_all_route,
            )

        if get_page_route:
            self._add_api_route(
                "/page",
                self._get_page(),
                methods=["POST"],
                response_model=SuccessResponse[PageResponse[self.schema]],  # type: ignore
                summary="Get Page",
                dependencies=get_page_route,
            )

        if get_tree_route:
            self._add_api_route(
                "/tree",
                self._get_tree(),
                methods=["POST"],
                response_model=SuccessResponse[ModelTree[self.schema]],  # type: ignore
                summary="Get Tree",
                dependencies=get_tree_route,
            )

        if get_tree_option_route:
            self._add_api_route(
                "/tree_option",
                self._get_tree_option(),
                methods=["POST"],
                response_model=SuccessResponse[ModelTree[self.schema]],  # type: ignore
                summary="Get Tree Option",
                dependencies=get_tree_option_route,
            )

        if create_route:
            self._add_api_route(
                "",
                self._create(),
                methods=["POST"],
                response_model=SuccessResponse[self.schema],
                summary="Create One",
                dependencies=create_route,
            )
        if add_route:
            self._add_api_route(
                "/add",
                self._add(),
                methods=["POST"],
                response_model=SuccessResponse[self.schema],
                summary="Add One",
                dependencies=add_route,
            )

        if get_one_route:
            self._add_api_route(
                "/{item_id}",
                self._get_one(),
                methods=["GET"],
                response_model=SuccessResponse[self.schema],
                summary="Get One",
                dependencies=get_one_route,
            )

        if update_route:
            self._add_api_route(
                "/{item_id}",
                self._update(),
                methods=["PUT"],
                response_model=SuccessResponse[self.schema],
                summary="Update One",
                dependencies=update_route,
            )

        if edit_route:
            self._add_api_route(
                "/edit",
                self._edit(),
                methods=["PATCH"],
                response_model=SuccessResponse[self.schema],
                summary="Edit One",
                dependencies=edit_route,
            )

        if delete_one_route:
            self._add_api_route(
                "/{item_id}",
                self._delete_one(),
                methods=["DELETE"],
                response_model=SuccessResponse[self.schema],
                summary="Delete One",
                dependencies=delete_one_route,
            )

        if delete_some_route:
            self._add_api_route(
                "/delete",
                self._delete_some(),
                methods=["POST"],
                response_model=SuccessResponse[List[self.schema]],  # type: ignore
                summary="Delete Some",
                dependencies=delete_some_route,
            )

        if delete_all_route:
            self._add_api_route(
                "",
                self._delete_all(),
                methods=["DELETE"],
                response_model=SuccessResponse[List[self.schema]],  # type: ignore
                summary="Delete All",
                dependencies=delete_all_route,
            )
        if export_all_route:
            self._add_api_route(
                "",
                self._export_all(),
                response_class=StreamingResponse,
                methods=["POST"],
                summary="Export All",
                dependencies=export_all_route,
            )

    def _add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        dependencies: Union[bool, DEPENDENCIES],
        error_responses: Optional[List[HTTPException]] = None,
        **kwargs: Any,
    ) -> None:
        dependencies = [] if isinstance(dependencies, bool) else dependencies
        responses: Any = {err.status_code: {"detail": err.detail} for err in error_responses} if error_responses else None

        super().add_api_route(path, endpoint, dependencies=dependencies, responses=responses, **kwargs)

    def api_route(self, path: str, *args: Any, **kwargs: Any) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """Overrides and exiting route if it exists"""
        methods = kwargs["methods"] if "methods" in kwargs else ["GET"]
        self.remove_api_route(path, methods)
        return super().api_route(path, *args, **kwargs)

    def get(self, path: str, *args: Any, **kwargs: Any) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["Get"])
        return super().get(path, *args, **kwargs)

    def post(self, path: str, *args: Any, **kwargs: Any) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["POST"])
        return super().post(path, *args, **kwargs)

    def put(self, path: str, *args: Any, **kwargs: Any) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["PUT"])
        return super().put(path, *args, **kwargs)

    def delete(self, path: str, *args: Any, **kwargs: Any) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.remove_api_route(path, ["DELETE"])
        return super().delete(path, *args, **kwargs)

    def remove_api_route(self, path: str, methods: List[str]) -> None:
        methods_ = set(methods)

        for route in self.routes:
            if (
                route.path == f"{self.prefix}{path}"  # type: ignore
                and route.methods == methods_  # type: ignore
            ):
                self.routes.remove(route)

    @abstractmethod
    def _get_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_page(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_tree(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_tree_option(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _create(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _add(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _update(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _edit(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_some(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _export_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    def _raise(self, e: Exception, status_code: int = 422) -> HTTPException:
        raise HTTPException(422, ", ".join(e.args)) from e

    @staticmethod
    def get_routes() -> List[str]:
        return [
            "get_all",
            "get_page",
            "get_tree",
            "get_tree_option",
            "get_one",
            "create",
            "add",
            "edit",
            "update",
            "delete_one",
            "delete_some",
            "delete_all",
            "export_all",
        ]


class SQLAlchemyCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        model_name: str,
        schema: Type[SCHEMA],
        db_model: "Model",
        db: "Session",
        create_schema: Optional[Type[SCHEMA]] = None,
        update_schema: Optional[Type[SCHEMA]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = 50,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_page_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        add_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        edit_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_some_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        export_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:
        assert sqlalchemy_installed, "SQLAlchemy must be installed to use the SQLAlchemyCRUDRouter."

        self.db_model = db_model
        self.db_func = db
        self.model_name = model_name
        self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
        self._db_cols = db_model.metadata.tables.get(db_model.__tablename__).columns.keys()
        self._pk_type: TypeAlias = get_pk_type_patch(schema, self._pk)

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_page_route=get_page_route,
            get_tree_route=False,
            get_tree_option_route=False,
            get_one_route=get_one_route,
            create_route=create_route,
            add_route=add_route,
            update_route=update_route,
            edit_route=edit_route,
            delete_one_route=delete_one_route,
            delete_some_route=delete_some_route,
            delete_all_route=delete_all_route,
            export_all_route=export_all_route,
            **kwargs,
        )

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def get_all(
            request: Request,
            query: self.schema,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[AllResponse[self.schema]]:
            try:
                q = db.query(self.db_model)
                conditions = []
                if "del_flag" in self._db_cols:
                    conditions.append(self.db_model.del_flag == 0)
                if "status" in self._db_cols and query.status:
                    conditions.append(self.db_model.status == query.status)
                if "name" in self._db_cols and query.name:
                    conditions.append(self.db_model.name.like(f"%{query.name}%"))
                if len(conditions) > 0:
                    q = q.filter(*conditions)

                if "order_num" in self._db_cols:
                    q = q.order_by(self.db_model.order_num)
                query_result = q.all()
                logger.info(query)
                logger.info(query_result)
                query_result = AllResponse[self.schema](rows=query_result)
                logger.info("获取成功")
                return response_200(data=query_result, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return get_all

    def _get_page(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def get_page(
            request: Request,
            query: self.schema,
            pagination: PAGINATION = self.pagination,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[PageResponse[self.schema]]:
            try:
                q = db.query(self.db_model)
                q_count = db.query(func.count(getattr(self.db_model, self._pk)))
                if "del_flag" in self._db_cols:
                    q = q.where(self.db_model.del_flag == 0)
                    q_count = q_count.where(self.db_model.del_flag == 0)
                if "status" in self._db_cols and query.status:
                    q = q.where(self.db_model.status == query.status)
                    q_count = q_count.where(self.db_model.status == query.status)
                if "name" in self._db_cols and query.name:
                    q = q.where(self.db_model.name.like(f"%{query.name}%"))
                    q_count = q_count.where(self.db_model.name.like(f"%{query.name}%"))
                if "head_dialog_id" in self._db_cols:
                    if query.head_dialog_id:
                        q = q.where(self.db_model.head_dialog_id == query.head_dialog_id)
                        q_count = q_count.where(self.db_model.head_dialog_id == query.head_dialog_id)
                    else:
                        q = q.where(self.db_model.head_dialog_id > 0)
                        q_count = q_count.where(self.db_model.head_dialog_id > 0)
                skip, limit = pagination.get("skip"), pagination.get("limit")
                if "order_num" in self._db_cols:
                    q = q.order_by(self.db_model.order_num)
                paginated_data: List[Model] = q.limit(limit).offset(skip).all()
                total = q_count.scalar()
                page_size = len(paginated_data)
                page_num = skip // limit + 1
                has_next = math.ceil(total / page_size) > page_num if page_size else False
                resp = PageResponse[self.schema](
                    rows=paginated_data,
                    page_num=page_num,
                    page_size=page_size,
                    total=total,
                    has_next=has_next,
                )
                logger.info("获取成功")
                return response_200(data=resp, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return get_page

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def get_one(
            request: Request,
            item_id: self._pk_type,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[self.schema]:  # type: ignore
            try:
                detail_result: Optional[self.db_model] = self._get_model_detail_by_id(db, item_id)
                logger.info(f"获取 {item_id} 的信息成功")
                return response_200(data=detail_result, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return get_one

    def _get_tree(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    def _get_tree_option(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def create(
            request: Request,
            model: self.create_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[self.schema]:
            print(model)
            try:
                new_model = CrudDao.create_one(db, self.db_model, model)
                print(new_model)
                return response_200(data=new_model, message="创建成功")
            except IntegrityError:
                db.rollback()
                raise HTTPException(422, "Key already exists") from None

        return create

    def _add(self, *args: Any, **kwargs: Any) -> CALLABLE:

        @log_decorator(title=f"{self.model_name}管理", business_type=1)
        async def add(
            request: Request,
            model: self.create_schema,  # type: ignore
            db: Session = Depends(self.db_func),
            current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
        ) -> SuccessResponse[self.schema]:
            try:
                if "create_by" in self._db_cols:
                    model.create_by = current_user.user.user_name
                if "update_by" in self._db_cols:
                    model.update_by = current_user.user.user_name
                if "speaker_id" in self._db_cols and "role" in self._db_cols and model.role == "user":
                    model.speaker_id = current_user.user.user_id
                new_model = CrudDao.create_one(db, self.db_model, model)
                logger.info(new_model)
                return response_200(data=new_model, message="创建成功")
            except Exception as e:
                db.rollback()
                logger.exception(e)
                return response_500(data=None, message=str(e))

        return add

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def update(
            request: Request,
            item_id: self._pk_type,  # type: ignore
            model: self.update_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[self.schema]:
            try:
                new_model = CrudDao.update_one(db, self.db_model, item_id, model)
                return response_200(data=new_model, message="更新成功")
            except IntegrityError as e:
                db.rollback()
                self._raise(e)

        return update

    def _get_model_by_id(self, db: Session, item_id: int):
        """
        根据数据id获取在用数据信息
        :param db: orm对象
        :param item_id: 数据id
        :return: 在用数据信息对象
        """
        q = db.query(self.db_model)
        conditions = []
        conditions.append(getattr(self.db_model, self._pk) == item_id)
        if "status" in self._db_cols:
            conditions.append(self.db_model.status == 0)
        if "del_flag" in self._db_cols:
            conditions.append(self.db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        model_info = q.first()
        return model_info

    def _get_model_detail_by_id(self, db: Session, item_id: int):
        """
        根据数据id获取数据详细信息
        :param db: orm对象
        :param item_id: 数据id
        :return: 数据信息对象
        """
        q = db.query(self.db_model)
        conditions = []
        conditions.append(getattr(self.db_model, self._pk) == item_id)
        if "del_flag" in self._db_cols:
            conditions.append(self.db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        model_info = q.first()
        return model_info

    def _get_model_detail_by_info(self, db: Session, name: Optional[str] = None):
        """
        根据数据参数获取数据信息
        :param db: orm对象
        :param parent_id: 父数据id
        :param name: 数据名称
        :return: 数据信息对象
        """
        q = db.query(self.db_model)
        conditions = []
        if "name" in self._db_cols:
            conditions.append(self.db_model.name == name)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        model_info = q.first()
        return model_info

    def _edit_model_dao(self, db: Session, model: dict):
        """
        编辑数据数据库操作
        :param db: orm对象
        :param model: 需要更新的数据字典
        :return: 编辑校验结果
        """
        db.query(self.db_model).filter(getattr(self.db_model, self._pk) == model.get(self._pk)).update(model)

    def _edit(self, *args: Any, **kwargs: Any) -> CALLABLE:

        @log_decorator(title=f"{self.model_name}管理", business_type=2)
        async def edit(
            request: Request,
            model: self.update_schema,  # type: ignore
            db: Session = Depends(self.db_func),
            current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
        ) -> SuccessResponse[self.schema]:
            try:
                update_by = current_user.user.user_name
                edit_model = model.dict(exclude_unset=True)
                if "update_by" in self._db_cols:
                    edit_model["update_by"] = update_by
                item_id = edit_model.get(self._pk)
                if CrudDao.exists(db, self.db_model, item_id):
                    self._edit_model_dao(db, edit_model)
                    db.commit()
                    model_info = self._get_model_detail_by_id(db, item_id)
                    return response_200(data=model_info, message="更新成功")
                else:
                    return response_200(data=None, message="数据不存在")
            except Exception as e:
                db.rollback()
                logger.exception(e)
                return response_500(data="", message=str(e))

        return edit

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        @log_decorator(title=f'{self.model_name}管理', business_type=9)
        async def delete_all(
            request: Request,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[List[self.schema]]:
            data = CrudDao.delete_all(db, self.db_model)
            return response_200(data=data, message="删除成功")

        return delete_all

    def _delete_some(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def delete_model_services(db: Session, item_ids: str, user_name: str) -> Tuple[List[self.schema], str]:
            if item_ids.split(","):
                delete_id_list = item_ids.split(",")
                try:
                    deleted_models = []
                    for delete_id in delete_id_list:
                        q = db.query(self.db_model).filter(getattr(self.db_model, self._pk) == delete_id)
                        if "del_flag" in self._db_cols:
                            update_dict = {}
                            update_dict[self.db_model.del_flag] = 2
                            if "update_by" in self._db_cols:
                                update_dict[self.db_model.update_by] = user_name
                            q.update(update_dict)
                        else:
                            q.delete()
                        deleted_model = q.first()
                        if deleted_model:
                            deleted_models.append(deleted_model)
                    db.commit()
                    return deleted_models, "删除成功"
                except Exception as e:
                    db.rollback()
                    return [], str(e)
            else:
                return [], "传入数据id为空"

        @log_decorator(title=f"{self.model_name}管理", business_type=3)
        async def delete_some(
            request: Request,
            delete_model: DeleteModel,
            db: Session = Depends(self.db_func),
            current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
        ) -> SuccessResponse[List[self.schema]]:  # type: ignore
            try:
                update_by = current_user.user.user_name
                delete_model_result, message = delete_model_services(db, delete_model.item_ids, update_by)
                if delete_model_result:
                    logger.info(message)
                    return response_200(data=delete_model_result, message=message)
                else:
                    logger.warning(message)
                    return response_400(data=delete_model_result, message=message)
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return delete_some

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            request: Request,
            item_id: self._pk_type,
            db: Session = Depends(self.db_func),
        ) -> self.schema:  # type: ignore
            return CrudDao.delete_one(db, self.db_model, item_id)

        return route

    def _export_list_services(self, data_list: List):
        """
        导出岗位信息service
        :param data_list: 岗位信息列表
        :return: 岗位信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            c.name : c.comment if c.comment else c.name
            for i, c in self.db_model.metadata.tables.get(self.db_model.__tablename__).columns.items()
        }

        data = [self.schema(**vars(row)).model_dump() for row in data_list]

        for item in data:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        new_data = [{mapping_dict.get(key): value for key, value in item.items() if mapping_dict.get(key)} for item in data]
        binary_data = export_list2excel(new_data)

        return binary_data

    def _export_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        @log_decorator(title=f'{self.model_name}管理', business_type=5)
        async def export_all(
            request: Request,
            query: self.schema,
            db: Session = Depends(self.db_func),
        ) -> StreamingResponse:
            try:
                q = db.query(self.db_model)
                conditions = []
                if "del_flag" in self._db_cols:
                    conditions.append(self.db_model.del_flag == 0)
                if "status" in self._db_cols and query.status:
                    conditions.append(self.db_model.status == query.status)
                if "name" in self._db_cols and query.name:
                    conditions.append(self.db_model.name.like(f"%{query.name}%"))
                if len(conditions) > 0:
                    q = q.filter(*conditions)
                if "order_num" in self._db_cols:
                    q = q.order_by(self.db_model.order_num)
                query_result = q.all()
                export_result = self._export_list_services(query_result)
                logger.info('导出成功')
                return streaming_response_200(data=bytes2file_response(export_result))
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return export_all


class TreeSQLAlchemyCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        model_name: str,
        schema: Type[SCHEMA],
        db_model: "Model",
        db: "Session",
        create_schema: Optional[Type[SCHEMA]] = None,
        update_schema: Optional[Type[SCHEMA]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = 50,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_page_route: Union[bool, DEPENDENCIES] = True,
        get_tree_route: Union[bool, DEPENDENCIES] = True,
        get_tree_option_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        add_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        edit_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_some_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        export_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:
        assert sqlalchemy_installed, "SQLAlchemy must be installed to use the SQLAlchemyCRUDRouter."

        self.db_model = db_model
        self.db_func = db
        self.model_name = model_name
        self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
        self._db_cols = db_model.metadata.tables.get(db_model.__tablename__).columns.keys()
        self._pk_type: type = get_pk_type_patch(schema, self._pk)

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_page_route=get_page_route,
            get_tree_route=get_tree_route,
            get_tree_option_route=get_tree_option_route,
            get_one_route=get_one_route,
            create_route=create_route,
            add_route=add_route,
            update_route=update_route,
            edit_route=edit_route,
            delete_one_route=delete_one_route,
            delete_some_route=delete_some_route,
            delete_all_route=delete_all_route,
            export_all_route=export_all_route,
            **kwargs,
        )

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def get_all(
            request: Request,
            query: self.schema,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[AllResponse[self.schema]]:
            try:
                q = db.query(self.db_model)
                conditions = []
                if "del_flag" in self._db_cols:
                    conditions.append(self.db_model.del_flag == 0)
                if "status" in self._db_cols and query.status:
                    conditions.append(self.db_model.status == query.status)
                if "name" in self._db_cols and query.name:
                    conditions.append(self.db_model.name.like(f"%{query.name}%"))
                if len(conditions) > 0:
                    q = q.filter(*conditions)
                if "order_num" in self._db_cols:
                    q = q.order_by(self.db_model.order_num)
                query_result = q.all()
                logger.info(query)
                logger.info(query_result)
                query_result = AllResponse[self.schema](rows=query_result)
                logger.info(query_result)
                logger.info("获取成功")
                return response_200(data=query_result, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return get_all

    def _get_page(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def get_page(
            request: Request,
            query: self.schema,
            pagination: PAGINATION = self.pagination,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[PageResponse[self.schema]]:
            try:
                q = db.query(self.db_model)
                q_count = db.query(func.count(getattr(self.db_model, self._pk)))
                if "del_flag" in self._db_cols:
                    q = q.where(self.db_model.del_flag == 0)
                    q_count = q_count.where(self.db_model.del_flag == 0)
                if "status" in self._db_cols and query.status:
                    q = q.where(self.db_model.status == query.status)
                    q_count = q_count.where(self.db_model.status == query.status)
                if "name" in self._db_cols and query.name:
                    q = q.where(self.db_model.name.like(f"%{query.name}%"))
                    q_count = q_count.where(self.db_model.name.like(f"%{query.name}%"))
                if "head_dialog_id" in self._db_cols:
                    if query.head_dialog_id:
                        q = q.where(self.db_model.head_dialog_id == query.head_dialog_id)
                        q_count = q_count.where(self.db_model.head_dialog_id == query.head_dialog_id)
                    else:
                        q = q.where(self.db_model.head_dialog_id > 0)
                        q_count = q_count.where(self.db_model.head_dialog_id > 0)
                skip, limit = pagination.get("skip"), pagination.get("limit")

                if "order_num" in self._db_cols:
                    q = q.order_by(self.db_model.order_num)
                paginated_data: List[Model] = q.limit(limit).offset(skip).all()
                total = q_count.scalar()
                page_size = len(paginated_data)
                page_num = skip // limit + 1
                has_next = math.ceil(total / page_size) > page_num
                resp = PageResponse[self.schema](
                    rows=paginated_data,
                    page_num=page_num,
                    page_size=page_size,
                    total=total,
                    has_next=has_next,
                )
                logger.info("获取成功")
                return response_200(data=resp, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return get_page

    def list_to_tree(self, data_list: list) -> list:
        """
        工具方法：根据数据列表信息生成树形嵌套数据
        :param data_list: 数据列表信息
        :return: 数据树形嵌套数据
        """
        data_list = [
            dict(
                title=item.name,
                key=str(getattr(item, self._pk)),
                value=str(getattr(item, self._pk)),
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

    def _get_tree(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def get_tree_services(db: Session, query: self.schema):
            """
            获取数据树信息service
            :param result_db: orm对象
            :param page_object: 查询参数对象
            :param data_scope_sql: 数据权限对应的查询sql语句
            :return: 数据树信息对象
            """
            q = db.query(self.db_model)
            conditions = []
            if "status" in self._db_cols:
                conditions.append(self.db_model.status == 0)
            if "del_flag" in self._db_cols:
                conditions.append(self.db_model.del_flag == 0)
            if query.name:
                conditions.append(self.db_model.name.like(f"%{query.name}%"))
            if len(conditions) > 0:
                q = q.filter(*conditions)
            if "order_num" in self._db_cols:
                q = q.order_by(self.db_model.order_num)
            model_list_result = q.all()
            model_tree_result = self.list_to_tree(model_list_result)

            return model_tree_result

        @log_decorator(title=f"{self.model_name}管理", business_type=4)
        async def get_tree(
            request: Request,
            query: self.update_schema,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[ModelTree[self.schema]]:
            try:
                model_query_result = get_tree_services(db, query)
                logger.info("获取成功")
                return response_200(data=model_query_result, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return get_tree

    def _get_tree_option(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def get_tree_services(db: Session, query: self.schema):
            """
            获取数据编辑数据树信息service
            :param result_db: orm对象
            :param page_object: 查询参数对象
            :param data_scope_sql: 数据权限对应的查询sql语句
            :return: 数据树信息对象
            """
            q = db.query(self.db_model)
            conditions = []
            conditions.append(getattr(self.db_model, self._pk) != getattr(query, self._pk))
            conditions.append(self.db_model.parent_id != getattr(query, self._pk))
            if "status" in self._db_cols:
                conditions.append(self.db_model.status == 0)
            if "del_flag" in self._db_cols:
                conditions.append(self.db_model.del_flag == 0)
            if len(conditions) > 0:
                q = q.filter(*conditions)
            if "order_num" in self._db_cols:
                q = q.order_by(self.db_model.order_num)
            model_list_result = q.all()
            model_tree_result = self.list_to_tree(model_list_result)

            return model_tree_result

        def get_tree_option(
            request: Request,
            query: self.update_schema,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[ModelTree[self.schema]]:
            try:
                model_query_result = get_tree_services(db, query)
                logger.info("获取成功")
                return response_200(data=model_query_result, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return get_tree_option

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            request: Request,
            item_id: self._pk_type,
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[self.schema]:  # type: ignore
            try:
                detail_result: Optional[self.db_model] = self._get_model_detail_by_id(db, item_id)
                logger.info(f"获取 {item_id} 的信息成功")
                return response_200(data=detail_result, message="获取成功")
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def create(
            request: Request,
            model: self.create_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[self.schema]:
            print(model)
            try:
                new_model = CrudDao.create_one(db, self.db_model, model)
                print(new_model)
                return response_200(data=new_model, message="创建成功")
            except IntegrityError:
                db.rollback()
                raise HTTPException(422, "Key already exists") from None

        return create

    def _add(self, *args: Any, **kwargs: Any) -> CALLABLE:

        def add_model_services(db: Session, query_object: self.create_schema):
            """
            新增数据信息service
            :param result_db: orm对象
            :param page_object: 新增数据对象
            :return: 新增数据校验结果
            """
            parent_info = self._get_model_by_id(db, query_object.parent_id)
            if parent_info:
                query_object.ancestors = list(parent_info.ancestors) + [query_object.parent_id]
            else:
                query_object.ancestors = [0]
            model = self._get_model_detail_by_info(db, parent_id=query_object.parent_id, name=query_object.name)
            if model:
                result = dict(is_success=False, message="同一数据下不允许存在同名的数据")
            else:
                try:
                    CrudDao.create_one(db, self.db_model, query_object)
                    result = dict(is_success=True, message="新增成功")
                except Exception as e:
                    db.rollback()
                    result = dict(is_success=False, message=str(e))

            return ActionResponse(**result)

        @log_decorator(title=f"{self.model_name}管理", business_type=1)
        async def add(
            request: Request,
            model: self.create_schema,  # type: ignore
            db: Session = Depends(self.db_func),
            current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
        ) -> ActionResponse:
            try:
                if "create_by" in self._db_cols:
                    model.create_by = current_user.user.user_name
                if "update_by" in self._db_cols:
                    model.update_by = current_user.user.user_name
                model_result = add_model_services(db, model)
                if model_result.is_success:
                    logger.info(model_result.message)
                    return response_200(data=model_result, message=model_result.message)
                else:
                    logger.warning(model_result.message)
                    return response_400(data="", message=model_result.message)
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return add

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            request: Request,
            item_id: self._pk_type,  # type: ignore
            model: self.update_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> SuccessResponse[self.schema]:
            try:
                new_model = CrudDao.update_one(db, self.db_model, item_id, model)
                return response_200(data=new_model, message="更新成功")
            except IntegrityError as e:
                db.rollback()
                self._raise(e)

        return route

    def _get_model_by_id(self, db: Session, item_id: int):
        """
        根据数据id获取在用数据信息
        :param db: orm对象
        :param item_id: 数据id
        :return: 在用数据信息对象
        """
        q = db.query(self.db_model)
        conditions = []
        conditions.append(getattr(self.db_model, self._pk) == item_id)
        if "status" in self._db_cols:
            conditions.append(self.db_model.status == 0)
        if "del_flag" in self._db_cols:
            conditions.append(self.db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        model_info = q.first()
        return model_info

    def _get_model_detail_by_id(self, db: Session, item_id: int):
        """
        根据数据id获取数据详细信息
        :param db: orm对象
        :param item_id: 数据id
        :return: 数据信息对象
        """
        q = db.query(self.db_model)
        conditions = []
        conditions.append(getattr(self.db_model, self._pk) == item_id)
        if "del_flag" in self._db_cols:
            conditions.append(self.db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        model_info = q.first()
        return model_info

    def _get_model_detail_by_info(self, db: Session, parent_id: Optional[int] = None, name: Optional[str] = None):
        """
        根据数据参数获取数据信息
        :param db: orm对象
        :param parent_id: 父数据id
        :param name: 数据名称
        :return: 数据信息对象
        """
        model_info = (
            db.query(self.db_model)
            .filter(
                self.db_model.parent_id == parent_id if parent_id else True,
                self.db_model.name == name if name else True,
            )
            .first()
        )

        return model_info

    def _get_children_models(self, db: Session, item_id: int):
        """
        根据数据id查询当前数据的子数据列表信息
        :param db: orm对象
        :param item_id: 数据id
        :return: 子数据信息列表
        """
        q = db.query(self.db_model)
        conditions = []
        conditions.append(self.db_model.parent_id == item_id)
        if "del_flag" in self._db_cols:
            conditions.append(self.db_model.del_flag == 0)
        if len(conditions) > 0:
            q = q.filter(*conditions)
        model_info = q.all()

        return model_info

    def _edit_model_dao(self, db: Session, model: dict):
        """
        编辑数据数据库操作
        :param db: orm对象
        :param model: 需要更新的数据字典
        :return: 编辑校验结果
        """
        db.query(self.db_model).filter(getattr(self.db_model, self._pk) == model.get(self._pk)).update(model)

    def _update_children_info(self, db: Session, model: dict):
        """
        工具方法：递归更新子数据信息
        :param result_db: orm对象
        :param page_object: 编辑数据对象
        :return:
        """
        children_info = self._get_children_models(db, model.get(self._pk))
        if children_info:
            for child in children_info:
                child.ancestors = list(model.ancestors) + [model.get(self._pk)]
                self._edit_model_dao(
                    db,
                    {
                        self._pk: getattr(child, self._pk),
                        "ancestors": child.ancestors,
                        "update_by": model.update_by,
                    },
                )
                self._update_children_info(
                    db,
                    {
                        self._pk: getattr(child, self._pk),
                        "ancestors": child.ancestors,
                        "update_by": model.update_by,
                    },
                )

    def _edit(self, *args: Any, **kwargs: Any) -> CALLABLE:

        def edit_model_services(db: Session, model: self.update_schema, update_by: str):
            """
            编辑数据信息service
            :param result_db: orm对象
            :param page_object: 编辑对象
            :return: 编辑校验结果
            """
            parent_info = self._get_model_by_id(db, model.parent_id)
            if parent_info:
                model.ancestors = list(parent_info.ancestors) + [model.parent_id]
            else:
                model.ancestors = [0]
            edit_model = model.dict(exclude_unset=True)
            model_info = self._get_model_detail_by_id(db, edit_model.get(self._pk))
            if model_info:
                if model_info.parent_id != model.parent_id or model_info.name != model.name:
                    model_detail = self._get_model_detail_by_info(db, parent_id=model.parent_id, name=model.name)
                    if model_detail:
                        result = dict(is_success=False, message="同一数据下不允许存在同名的数据")
                        return ActionResponse(**result)
                try:
                    self._edit_model_dao(db, edit_model)
                    self._update_children_info(
                        db,
                        {
                            self._pk: getattr(model, self._pk),
                            "ancestors": model.ancestors,
                            "update_by": model.update_by,
                        },
                    )
                    db.commit()
                    result = dict(is_success=True, message="更新成功")
                except Exception as e:
                    db.rollback()
                    result = dict(is_success=False, message=str(e))
            else:
                result = dict(is_success=False, message="数据不存在")

            return ActionResponse(**result)

        @log_decorator(title=f"{self.model_name}管理", business_type=2)
        async def edit(
            request: Request,
            model: self.update_schema,  # type: ignore
            db: Session = Depends(self.db_func),
            current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
        ) -> SuccessResponse[self.schema]:
            try:
                update_by = current_user.user.user_name
                edit_result = edit_model_services(db, model, update_by)
                if edit_result.is_success:
                    logger.info(edit_result.message)
                    return response_200(data=edit_result, message=edit_result.message)
                else:
                    logger.warning(edit_result.message)
                    return response_400(data="", message=edit_result.message)
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return edit

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        @log_decorator(title=f'{self.model_name}管理', business_type=9)
        async def delete_all(
            request: Request,
            db: Session = Depends(self.db_func),
        ) -> List[self.schema]:
            data = CrudDao.delete_all(db, self.db_model)
            return response_200(data=data, message="删除成功")

        return delete_all

    def _get_all_ancestors(self, db: Session):
        """
        获取所有数据的ancestors信息
        :param db: orm对象
        :return: ancestors信息列表
        """
        q = db.query(self.db_model.ancestors)
        if "del_flag" in self._db_cols:
            q = q.filter(getattr(self.db_model, "del_flag") == 0)
        ancestors = q.all()
        return ancestors

    def _delete_some(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def delete_model_services(db: Session, item_ids: str, user_name: str) -> Tuple[List[self.db_model], str]:
            if item_ids.split(","):
                delete_id_list = item_ids.split(",")
                ancestors = self._get_all_ancestors(db)
                try:
                    deleted_models = []
                    for delete_id in delete_id_list:
                        for ancestor in ancestors:
                            if delete_id in ancestor[0]:
                                result = dict(is_success=False, message="该数据下有子数据，不允许删除")
                                return ActionResponse(**result)

                        q = db.query(self.db_model).filter(getattr(self.db_model, self._pk) == delete_id)
                        update_dict = {
                            self.db_model.update_by: user_name,
                        }
                        if "del_flag" in self._db_cols:
                            update_dict[self.db_model.del_flag] = 2
                        q.update(update_dict)
                        deleted_model = q.first()
                        if deleted_model:
                            deleted_models.append(deleted_model)
                    db.commit()
                    return deleted_models, "删除成功"
                except Exception as e:
                    db.rollback()
                    return [], str(e)
            else:
                return [], "传入数据id为空"

        @log_decorator(title=f"{self.model_name}管理", business_type=3)
        async def delete_some(
            request: Request,
            delete_model: DeleteModel,
            db: Session = Depends(self.db_func),
            current_user: CurrentUserInfoServiceResponse = Depends(get_current_user),
        ) -> SuccessResponse[List[self.schema]]:  # type: ignore
            try:
                update_by = current_user.user.user_name
                delete_model_result, message = delete_model_services(db, delete_model.item_ids, update_by)
                if delete_model_result:
                    logger.info(message)
                    return response_200(data=delete_model_result, message=message)
                else:
                    logger.warning(message)
                    return response_400(data=delete_model_result, message=message)
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return delete_some

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        async def route(
            request: Request,
            item_id: self._pk_type,
            db: Session = Depends(self.db_func),
        ) -> self.schema:  # type: ignore
            return CrudDao.delete_one(db, self.db_model, item_id)

        return route

    def _export_list_services(self, data_list: List):
        """
        导出岗位信息service
        :param data_list: 岗位信息列表
        :return: 岗位信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            i.name : i.comment if i.comment else i.name
            for i in self.db_model.metadata.tables.get(self.db_model.__tablename__).columns
        }

        data = [self.schema(**vars(row)).model_dump() for row in data_list]

        for item in data:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        new_data = [{mapping_dict.get(key): value for key, value in item.items() if mapping_dict.get(key)} for item in data]
        binary_data = export_list2excel(new_data)

        return binary_data

    def _export_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        @log_decorator(title=f'{self.model_name}管理', business_type=5)
        async def export_all(
            request: Request,
            query: self.schema,
            db: Session = Depends(self.db_func),
        ) -> StreamingResponse:
            try:
                q = db.query(self.db_model)
                conditions = []
                if "del_flag" in self._db_cols:
                    conditions.append(self.db_model.del_flag == 0)
                if "status" in self._db_cols and query.status:
                    conditions.append(self.db_model.status == query.status)
                if "name" in self._db_cols and query.name:
                    conditions.append(self.db_model.name.like(f"%{query.name}%"))
                if len(conditions) > 0:
                    q = q.filter(*conditions)
                if "order_num" in self._db_cols:
                    q = q.order_by(self.db_model.order_num)
                query_result = q.all()
                export_result = self._export_list_services(query_result)
                logger.info('导出成功')
                return streaming_response_200(data=bytes2file_response(export_result))
            except Exception as e:
                logger.exception(e)
                return response_500(data="", message=str(e))

        return export_all
