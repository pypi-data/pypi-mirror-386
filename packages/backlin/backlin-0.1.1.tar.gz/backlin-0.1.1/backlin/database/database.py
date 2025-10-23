import os
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, DeclarativeMeta

from backlin.config.env import DataBaseConfig


# connection_string = URL.create(
#   'postgresql',
#   username='linxueyuandlinking',
#   password='HARtGnu3Js4k',
#   host='ep-soft-unit-44308222.cloud.argon.aws.neon.build',
#   database='neondb',
#   query={
#       "sslmode": "require",
#     #   "sslrootcert": "/root/.postgresql/root.crt"
#   }
# )

# engine = create_engine(connection_string)
# DATABASE_FILE = "app.db"
# SQLALCHEMY_DATABASE_URL = f"sqlite:///./{DATABASE_FILE}"
# SQLALCHEMY_DATABASE_URL = f"postgresql:///./{DATABASE_FILE}"
# SQLALCHEMY_DATABASE_URL = f"mongodb:///./{DATABASE_FILE}"
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/saaskit")
"""
sudo apt-get install postgresql
sudo passwd postgres
122425

"""

# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
# SQLALCHEMY_DATABASE_URL = "mongodb+srv://linxueyuan:V4SefxDx5FcaGJzJ@cluster0.i3tjnh2.mongodb.net/?retryWrites=true&w=majority"
# SQLALCHEMY_DATABASE_URL = "cockroachdb://dlinking:sEf_XOxSIY2-nzGYZgvr7Q@jade-corgi-5476.6xw.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full"

# SQLALCHEMY_DATABASE_URL = "postgresql://linxueyuandlinking:HARtGnu3Js4k@ep-falling-dust-42679711.ap-southeast-1.aws.neon.tech/memoformer?sslmode=verify-full"
# engine = create_engine(SQLALCHEMY_DATABASE_URL,
#     pool_size=10,
#     max_overflow=2,
#     pool_recycle=300,
#     pool_pre_ping=True,
#     pool_use_lifo=True)

remote_engine_args = dict()
if "localhost" not in SQLALCHEMY_DATABASE_URL:
    remote_engine_args = dict(
        # connect_args={
        #     "sslmode": "require",
        #     # "sslrootcert": "/path/to/your/root.crt"
        # }
        # expire_on_commit=DataBaseConfig.db_expire_on_commit,
        pool_pre_ping=DataBaseConfig.db_pool_pre_ping,
    )
    # SSL根证书下载地址：https://www.postgresql.org/ftp/pgadmin/pgadmin4/v6.17/
    # 放置路径：/root/.postgresql/root.crt

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args={"check_same_thread": False}
    echo=DataBaseConfig.db_echo,
    max_overflow=DataBaseConfig.db_max_overflow,
    pool_size=DataBaseConfig.db_pool_size,
    pool_recycle=DataBaseConfig.db_pool_recycle,
    pool_timeout=DataBaseConfig.db_pool_timeout,
    **remote_engine_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: DeclarativeMeta = declarative_base()
