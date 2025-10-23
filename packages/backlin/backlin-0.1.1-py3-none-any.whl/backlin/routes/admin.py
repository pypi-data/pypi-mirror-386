import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import datetime
from datetime import timedelta
from fastapi.responses import FileResponse, JSONResponse
from io import BytesIO
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy.util import FacadeDict
from sqlalchemy import MetaData, Table

from backlin.database import get_db, engine

NOW = datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=8)

app = APIRouter(prefix="/admin", tags=["admin"])


@app.get("/export")
def export_database(db: Session = Depends(get_db)):
    # 反射数据库中的表
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # 创建一个临时文件用于存储Excel
    output_file = Path("files/export/all_tables_export.xlsx")
    if output_file.exists():
        output_file.unlink()

    # 使用Pandas的ExcelWriter来管理Excel文件的写入
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # 遍历数据库中的所有表
        for table_name in metadata.tables.keys():
            table = Table(table_name, metadata, autoload_with=engine)

            # 使用SQLAlchemy ORM进行查询
            query = db.query(table)

            # 将结果转换为Pandas DataFrame
            df = pd.DataFrame([row._asdict() for row in query.all()])

            # 将每个表的数据写入Excel的不同工作表
            df.to_excel(writer, sheet_name=table_name, index=False)

    # 返回生成的Excel文件
    return FileResponse(path=output_file, filename=output_file.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.post("/import")
def import_database(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 反射数据库中的表
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # 验证文件类型
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file (.xlsx).")

    # 将上传的文件内容读取为BytesIO对象
    content = BytesIO(file.file.read())

    # 读取Excel文件
    xls = pd.ExcelFile(content)

    warnings = []

    for sheet_name in xls.sheet_names:
        # 检查表是否存在于数据库中
        if sheet_name not in metadata.tables:
            warnings.append(f"Table {sheet_name} does not exist in the database.")
            continue

        # 读取工作表数据
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # 获取表对象
        table = metadata.tables[sheet_name]

        # 将DataFrame中的数据转换为字典列表
        data = df.to_dict(orient="records")

        # 获取表的主键列
        primary_keys = [key.name for key in table.primary_key.columns]

        # 插入或更新数据
        for row in data:
            # 创建主键过滤器
            filters = {key: row[key] for key in primary_keys}

            # 查找是否已有记录
            existing_record = db.query(table).filter_by(**filters).first()

            if existing_record:
                # 如果记录存在，则执行更新
                db.query(table).filter_by(**filters).update(row)
            else:
                # 如果记录不存在，则插入新记录
                db.execute(table.insert().values(row))

        # 提交事务
        db.commit()

    return JSONResponse(content={"message": "Data imported successfully.", "warnings": warnings})


# 清理临时文件
@app.on_event("shutdown")
def cleanup_temp_files():
    if os.path.exists("all_tables_export.xlsx"):
        os.remove("all_tables_export.xlsx")
