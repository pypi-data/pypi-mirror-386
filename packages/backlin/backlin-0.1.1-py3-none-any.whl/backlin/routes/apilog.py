from typing import List, Optional
import datetime
import uuid

from sqlalchemy import Column, event, ForeignKey, ForeignKeyConstraint, func
from sqlalchemy import BigInteger, Boolean, Integer, String, Float, DateTime, Text, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backlin.database import get_db, Base
from backlin.routes.crud_router import SQLAlchemyCRUDRouter


app = APIRouter(prefix="", tags=["API Log"])


class DbApiLog(Base):
    __tablename__ = "api_log"  # api 日志
    trace_id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True, default=None)
    api_header = Column(JSON, nullable=False)
    api_input = Column(JSON, nullable=False)
    api_output = Column(JSON, nullable=False)

    create_time = Column(DateTime, nullable=False, server_default=func.now())


class ApiLogCreate(BaseModel):
    user_id: str
    api_header: dict
    api_input: dict
    api_output: dict
    create_time: datetime.datetime

class ApiLogUpdate(ApiLogCreate):
    pass


class ApiLog(ApiLogCreate):
    trace_id: str

    class Config:
        from_attributes = True


router_ApiLog = SQLAlchemyCRUDRouter(
    schema=ApiLog,
    create_schema=ApiLogCreate,
    update_schema=ApiLogUpdate,
    db_model=DbApiLog,
    db=get_db,
    prefix="",
    tags=["API Log"],
)
app.include_router(router_ApiLog)


async def log_api_request(request: Request, response: dict, inputs: Optional[dict]=None):
    """
    记录 API 请求日志
    """
    api_header = {k: v for k, v in request.headers.items()}
    if inputs:
        api_input = inputs
    else:
        api_input = await request.json()
    user_id = api_input.get("user_id", None)
    for db in get_db():
        log = DbApiLog(
            user_id=user_id,
            api_header=api_header,
            api_input=api_input,
            api_output=response,
        )
        db.add(log)
        db.commit()