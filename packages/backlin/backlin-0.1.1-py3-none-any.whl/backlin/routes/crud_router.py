from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List, Optional, Type, Union, TypeVar

from fastapi import Depends, APIRouter, HTTPException
from fastapi.types import DecoratedCallable
from fastapi_crudrouter.core import NOT_FOUND
from fastapi_crudrouter.core._types import DEPENDENCIES, PAGINATION, PYDANTIC_SCHEMA as SCHEMA
from fastapi_crudrouter.core._utils import pagination_factory

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta as Model
from sqlalchemy.exc import IntegrityError

sqlalchemy_installed = True

CALLABLE = Callable[..., Model]
CALLABLE_LIST = Callable[..., List[Model]]

import fastapi_crudrouter

from pydantic import BaseModel, Field, ConfigDict, create_model

T = TypeVar("T", bound=BaseModel)

# 定义模型配置，启用 `from_attributes`
class OrmConfig:
    model_config = ConfigDict(from_attributes=True)


class DataResponse(BaseModel, Generic[T], OrmConfig):
    data: T
    total: int = 1
    msg: str = "success"
    code: int = 200


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


fastapi_crudrouter.core._utils.get_pk_type = get_pk_type_patch
fastapi_crudrouter.core._utils.schema_factory = schema_factory_patch
fastapi_crudrouter.core._base.schema_factory = schema_factory_patch

NOT_FOUND = HTTPException(404, {"msg": "Item not found"})


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
        paginate: Optional[int] = None,
        get_everything_route: Union[bool, DEPENDENCIES] = True,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:

        self.schema = schema
        self.pagination = pagination_factory(max_limit=paginate)
        self._pk: str = self._pk if hasattr(self, "_pk") else "id"
        self.create_schema = create_schema if create_schema else schema_factory_patch(self.schema, pk_field_name=self._pk, name="Create")
        self.update_schema = update_schema if update_schema else schema_factory_patch(self.schema, pk_field_name=self._pk, name="Update")

        prefix = str(prefix if prefix else self.schema.__name__).lower()
        prefix = self._base_path + prefix.strip("/")
        tags = tags or [prefix.strip("/").capitalize()]

        super().__init__(prefix=prefix, tags=tags, **kwargs)

        if get_everything_route:
            self._add_api_route(
                "/everything",
                self._get_everything(),
                methods=["GET"],
                response_model=DataResponse[List[self.schema]],  # type: ignore
                summary="Get Everything",
                dependencies=get_everything_route,
            )

        if get_all_route:
            self._add_api_route(
                "",
                self._get_all(),
                methods=["GET"],
                response_model=DataResponse[List[self.schema]],  # type: ignore
                summary="Get All",
                dependencies=get_all_route,
            )

        if create_route:
            self._add_api_route(
                "",
                self._create(),
                methods=["POST"],
                response_model=self.schema,
                summary="Create One",
                dependencies=create_route,
            )

        if delete_all_route:
            self._add_api_route(
                "",
                self._delete_all(),
                methods=["DELETE"],
                response_model=Optional[List[self.schema]],  # type: ignore
                summary="Delete All",
                dependencies=delete_all_route,
            )

        if get_one_route:
            self._add_api_route(
                "/{item_id}",
                self._get_one(),
                methods=["GET"],
                response_model=self.schema,
                summary="Get One",
                dependencies=get_one_route,
            )

        if update_route:
            self._add_api_route(
                "/{item_id}",
                self._update(),
                methods=["PUT"],
                response_model=self.schema,
                summary="Update One",
                dependencies=update_route,
            )

        if delete_one_route:
            self._add_api_route(
                "/{item_id}",
                self._delete_one(),
                methods=["DELETE"],
                response_model=self.schema,
                summary="Delete One",
                dependencies=delete_one_route,
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
    def _get_everything(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _get_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _create(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _update(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_one(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    @abstractmethod
    def _delete_all(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        raise NotImplementedError

    def _raise(self, e: Exception, status_code: int = 422) -> HTTPException:
        raise HTTPException(422, ", ".join(e.args)) from e

    @staticmethod
    def get_routes() -> List[str]:
        return ["get_all", "create", "delete_all", "get_one", "update", "delete_one"]


class SQLAlchemyCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        schema: Type[SCHEMA],
        db_model: "Model",
        db: "Session",
        create_schema: Optional[Type[SCHEMA]] = None,
        update_schema: Optional[Type[SCHEMA]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = None,
        get_everything_route: Union[bool, DEPENDENCIES] = True,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:
        assert sqlalchemy_installed, "SQLAlchemy must be installed to use the SQLAlchemyCRUDRouter."

        self.db_model = db_model
        self.db_func = db
        self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = get_pk_type_patch(schema, self._pk)

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            paginate=paginate,
            get_everything_route=get_everything_route,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs,
        )

    def _get_everything(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(
            db: Session = Depends(self.db_func),
        ) -> DataResponse[List[self.schema]]:
            db_models: List[Model] = db.query(self.db_model).order_by(getattr(self.db_model, self._pk)).all()
            resp = DataResponse(data=db_models, total=len(db_models))
            return resp

        return route

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(
            db: Session = Depends(self.db_func),
            pagination: PAGINATION = self.pagination,
        ) -> DataResponse[List[self.schema]]:
            skip, limit = pagination.get("skip"), pagination.get("limit")
            q_count = db.query(func.count(getattr(self.db_model, self._pk)))
            q = db.query(self.db_model)
            db_models: List[Model] = q.order_by(getattr(self.db_model, self._pk)).limit(limit).offset(skip).all()
            count = q_count.scalar()
            resp = DataResponse(data=db_models, total=count)
            return resp

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            item_id: self._pk_type,
            db: Session = Depends(self.db_func),
        ) -> Model:  # type: ignore
            model: Model = db.query(self.db_model).get(item_id)

            if model:
                return model
            else:
                raise NOT_FOUND from None

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            model: self.create_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> self.schema:
            try:
                db_model: self.db_model = self.db_model(**model.dict())
                db.add(db_model)
                db.commit()
                db.refresh(db_model)
                return db_model
            except IntegrityError:
                db.rollback()
                raise HTTPException(422, "Key already exists") from None

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            item_id: self._pk_type,  # type: ignore
            model: self.update_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> self.schema:
            try:
                db_model: self.schema = self._get_one()(item_id, db)

                for key, value in model.dict(exclude={self._pk}).items():
                    if hasattr(db_model, key):
                        setattr(db_model, key, value)

                db.commit()
                db.refresh(db_model)

                return db_model
            except IntegrityError as e:
                db.rollback()
                self._raise(e)

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(db: Session = Depends(self.db_func)) -> List[self.schema]:
            db.query(self.db_model).delete()
            db.commit()

            return self._get_all()(db=db, pagination={"skip": 0, "limit": None})

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: self._pk_type, db: Session = Depends(self.db_func)) -> self.schema:  # type: ignore
            db_model: self.schema = self._get_one()(item_id, db)
            db.delete(db_model)
            db.commit()

            return db_model

        return route


class UserSQLAlchemyCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
        self,
        schema: Type[SCHEMA],
        db_model: "Model",
        db: "Session",
        create_schema: Optional[Type[SCHEMA]] = None,
        update_schema: Optional[Type[SCHEMA]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paginate: Optional[int] = None,
        get_all_filter_attr: str = "user_id",
        get_everything_route: Union[bool, DEPENDENCIES] = True,
        get_all_route: Union[bool, DEPENDENCIES] = True,
        get_one_route: Union[bool, DEPENDENCIES] = True,
        create_route: Union[bool, DEPENDENCIES] = True,
        update_route: Union[bool, DEPENDENCIES] = True,
        delete_one_route: Union[bool, DEPENDENCIES] = True,
        delete_all_route: Union[bool, DEPENDENCIES] = True,
        **kwargs: Any,
    ) -> None:
        assert sqlalchemy_installed, "SQLAlchemy must be installed to use the SQLAlchemyCRUDRouter."

        self.db_model = db_model
        self.db_func = db
        self._pk: str = db_model.__table__.primary_key.columns.keys()[0]
        self._pk_type: type = get_pk_type_patch(schema, self._pk)
        self.get_all_filter_attr = get_all_filter_attr

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__,
            tags=tags,
            paginate=paginate,
            get_everything_route=get_everything_route,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            **kwargs,
        )

    def _get_everything(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(
            filter_attr: Optional[str]=None,
            db: Session = Depends(self.db_func),
        ) -> DataResponse[List[self.schema]]:
            q = db.query(self.db_model)
            if filter_attr:
                q = q.where(getattr(self.db_model, self.get_all_filter_attr) == filter_attr)
            db_models: List[Model] = q.order_by(getattr(self.db_model, self._pk)).all()
            resp = DataResponse(data=db_models, total=len(db_models))
            return resp

        return route

    def _get_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(
            filter_attr: Optional[str]=None,
            db: Session = Depends(self.db_func),
            pagination: PAGINATION = self.pagination,
        ) -> DataResponse[List[self.schema]]:
            q = db.query(self.db_model)
            q_count = db.query(func.count(getattr(self.db_model, self._pk)))
            if filter_attr:
                q = q.where(getattr(self.db_model, self.get_all_filter_attr) == filter_attr)
                q_count = q_count.where(getattr(self.db_model, self.get_all_filter_attr) == filter_attr)
            skip, limit = pagination.get("skip"), pagination.get("limit")
            db_models: List[Model] = q.order_by(getattr(self.db_model, self._pk)).limit(limit).offset(skip).all()
            count = q_count.scalar()
            resp = DataResponse(data=db_models, total=count)
            return resp

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            item_id: self._pk_type,
            db: Session = Depends(self.db_func),
        ) -> Model:  # type: ignore
            model: Model = db.query(self.db_model).get(item_id)

            if model:
                return model
            else:
                raise NOT_FOUND from None

        return route

    def _create(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            model: self.create_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> self.schema:
            print(model)
            try:
                db_model: self.db_model = self.db_model(**model.dict())
                db.add(db_model)
                db.commit()
                db.refresh(db_model)
                print(db_model)
                return db_model
            except IntegrityError:
                db.rollback()
                raise HTTPException(422, "Key already exists") from None

        return route

    def _update(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(
            item_id: self._pk_type,  # type: ignore
            model: self.update_schema,  # type: ignore
            db: Session = Depends(self.db_func),
        ) -> self.schema:
            try:
                db_model: self.schema = self._get_one()(item_id, db)

                for key, value in model.dict(exclude={self._pk}).items():
                    if hasattr(db_model, key):
                        setattr(db_model, key, value)

                db.commit()
                db.refresh(db_model)

                return db_model
            except IntegrityError as e:
                db.rollback()
                self._raise(e)

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> CALLABLE_LIST:
        def route(
            db: Session = Depends(self.db_func),
        ) -> List[self.schema]:
            db.query(self.db_model).delete()
            db.commit()

            return self._get_all()(db=db, pagination={"skip": 0, "limit": None})

        return route

    def _delete_one(self, *args: Any, **kwargs: Any) -> CALLABLE:
        def route(item_id: self._pk_type, db: Session = Depends(self.db_func)) -> self.schema:  # type: ignore
            db_model: self.schema = self._get_one()(item_id, db)
            db.delete(db_model)
            db.commit()

            return db_model

        return route
