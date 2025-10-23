from typing import Annotated
import typer
import uvicorn
from dotenv import load_dotenv


cli = typer.Typer(name="server", help="服务器")


@cli.command("serve")
def serve(
    env: Annotated[str, typer.Option(envvar="APP_ENV", help="运行环境")] = "dev",
    host: Annotated[str, typer.Option(help="host")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="port")] = 8000,
    recreate_db: Annotated[bool, typer.Option(help="重建数据库")] = False,
):
    # 运行环境未指定时默认加载.env.dev
    env_file = ".env.dev"
    # 运行环境不为空时按命令行参数加载对应.env文件
    if env != "":
        env_file = f".env.{env}"
    # 加载配置
    load_dotenv(env_file)

    from backlin.database import load_database

    # 使用 import 就可以注册 schema 到数据库，无需做其他操作
    from backlin.routes import apilog
    from backlin.module_saas.schema import (
        ApiKey,
    )

    load_database(recreate_db)

    uvicorn.run("backlin.backend:app", host=host, port=port)


if __name__ == "__main__":
    cli()
