from typing import List, Union, TypeVar, Generic

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


# 定义模型配置，启用 `from_attributes`
class OrmConfig:
    model_config = ConfigDict(from_attributes=True)


class DataResponse(BaseModel, Generic[T], OrmConfig):
    data: T
    total: int = 1
    msg: str = "success"
    code: int = 200
