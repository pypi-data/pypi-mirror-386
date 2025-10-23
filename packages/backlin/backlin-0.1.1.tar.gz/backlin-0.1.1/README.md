
# Backlin - SaaS Backend API

基于 FastAPI 构建的 SaaS 后端服务，提供完整的用户管理、权限控制、API 密钥管理等功能。

## 🚀 特性

- **FastAPI 框架**：高性能异步 Web 框架
- **模块化设计**：清晰的模块划分，易于扩展
- **权限管理**：基于 RBAC 的权限控制系统
- **API 密钥管理**：支持 API Key 认证
- **日志系统**：基于 Loguru 的日志记录
- **缓存支持**：Redis 缓存集成
- **任务调度**：APScheduler 定时任务
- **数### 4. 初始化数据库

**方式 1: 使用自动化脚本（PostgreSQL - 推荐）**

我们提供了一个自动化脚本来快速初始化 PostgreSQL 数据库：

```bash
cd backend/backlin

# 使用默认配置（数据库: dash_fastapi，用户: backlin，密码: backlin123）
./scripts/init_postgres.sh

# 或使用自定义配置
DB_NAME="my_db" DB_USER="my_user" DB_PASSWORD="my_pass" ./scripts/init_postgres.sh
```

脚本会自动：
- 启动 PostgreSQL 服务（如果未运行）
- 创建数据库和用户
- 配置权限
- 显示数据库连接信息

**方式 2: 手动创建 PostgreSQL 数据库**

```bash
# 启动 PostgreSQL（WSL）
sudo service postgresql start

# 切换到 postgres 用户
sudo -u postgres psql

# 在 psql 命令行中执行
CREATE USER backlin WITH PASSWORD 'your_password';
CREATE DATABASE dash_fastapi OWNER backlin;
GRANT ALL PRIVILEGES ON DATABASE dash_fastapi TO backlin;
GRANT ALL ON SCHEMA public TO backlin;
\q
```

**方式 3: 手动创建 MySQL 数据库**

```bash
# 启动 MySQL（WSL）
sudo service mysql start

# 登录 MySQL
mysql -u root -p

# 在 MySQL 命令行中执行
CREATE DATABASE `dash_fastapi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'backlin'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dash_fastapi.* TO 'backlin'@'localhost';
FLUSH PRIVILEGES;
exit;
```

**运行 SQL 文件（如果提供）:**
```bash
# PostgreSQL
psql -U backlin -d dash_fastapi -f sql/dash-fastapi.sql

# MySQL
mysql -u backlin -p dash_fastapi < sql/dash-fastapi.sql
```my 数据库操作
- **接口文档**：自动生成 OpenAPI 文档

## 📋 技术栈

- **Web 框架**：FastAPI + Uvicorn
- **CLI 工具**：Typer
- **数据库**：SQLAlchemy（支持 MySQL、PostgreSQL 等）
- **缓存**：Redis 5.0.8
- **任务调度**：APScheduler
- **认证**：JWT (python-jose) + Passlib
- **日志**：Loguru
- **数据处理**：Pandas、OpenPyXL
- **可视化**：Matplotlib、Seaborn、Plotly、Gradio
- **AI 集成**：OpenAI、LangChain、LangServe

## 📦 项目结构

```
backlin/
├── backlin/
│   ├── __init__.py
│   ├── __main__.py          # CLI 入口
│   ├── backend.py           # FastAPI 应用主文件
│   ├── base/                # 基础类（DTO 等）
│   ├── config/              # 配置模块
│   │   ├── env.py          # 环境变量配置
│   │   ├── get_redis.py    # Redis 配置
│   │   └── get_scheduler.py # 调度器配置
│   ├── crud/                # CRUD 基础操作
│   ├── database/            # 数据库配置
│   ├── middleware/          # 中间件
│   ├── module_admin/        # 管理模块
│   │   ├── annotation/     # 注解（日志等）
│   │   ├── aspect/         # 切面（权限、数据范围）
│   │   ├── controller/     # 控制器
│   │   ├── dao/            # 数据访问层
│   │   ├── entity/         # 实体类
│   │   └── service/        # 业务逻辑层
│   ├── module_saas/         # SaaS 模块
│   │   ├── api_require.py
│   │   ├── api_v1.py
│   │   ├── route_apikey.py
│   │   ├── schema.py
│   │   └── secure.py
│   ├── routes/              # 路由模块
│   └── utils/               # 工具类
├── data/                    # 数据文件
├── .env.dev                 # 开发环境配置
├── .env.prod                # 生产环境配置
├── pyproject.toml           # Poetry 配置
├── requirements.txt         # 依赖清单
└── README.md
```

## 🔧 环境要求

- Python >= 3.11
- Redis >= 5.0
- MySQL/PostgreSQL（根据配置）

## 📝 安装步骤

### 1. 安装 Redis

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-start
sudo systemctl enable redis-server
```

**Fedora/RHEL/CentOS:**
```bash
sudo dnf install redis
sudo systemctl start redis
sudo systemctl enable redis
```

**MacOS:**
```bash
brew install redis
brew services start redis
```

**验证 Redis 安装:**
```bash
redis-cli ping
# 应返回 PONG
```

### 2. 安装数据库

#### 选项 A：安装 PostgreSQL（推荐）

**Ubuntu/Debian:**
```bash
# 安装 PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# 启动 PostgreSQL 服务
# 如果使用 systemd（原生 Linux）
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 如果使用 WSL（Windows Subsystem for Linux）
sudo service postgresql start

# 检查服务状态
sudo service postgresql status

# 切换到 postgres 用户
sudo -i -u postgres

# 进入 PostgreSQL 命令行
psql

# 创建数据库和用户（在 psql 命令行中）
CREATE USER backlin WITH PASSWORD 'your_password';
CREATE DATABASE dash_fastapi OWNER backlin;
GRANT ALL PRIVILEGES ON DATABASE dash_fastapi TO backlin;
\q

# 退出 postgres 用户
exit
```

**Fedora/RHEL/CentOS:**
```bash
# 安装 PostgreSQL
sudo dnf install postgresql-server postgresql-contrib

# 初始化数据库
sudo postgresql-setup --initdb

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 后续步骤与 Ubuntu 相同
```

**配置 PostgreSQL 允许密码认证（如需要）:**
```bash
# 编辑 pg_hba.conf
sudo nano /etc/postgresql/{version}/main/pg_hba.conf

# 将以下行的 peer 改为 md5（或 scram-sha-256）
# 找到: local   all   all   peer
# 改为: local   all   all   md5

# 重启 PostgreSQL
sudo systemctl restart postgresql
```

**在 .env.dev 中配置 PostgreSQL 连接:**
```bash
# -------- PostgreSQL 配置 --------
DB_HOST = 'localhost'
DB_PORT = 5432
DB_USERNAME = 'backin'
DB_PASSWORD = 'your_password'
DB_DATABASE = 'dash_fastapi'
```

#### 选项 B：安装 MySQL

**Ubuntu/Debian:**
```bash
# 安装 MySQL
sudo apt-get update
sudo apt-get install mysql-server

# 启动 MySQL 服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 运行安全配置脚本
sudo mysql_secure_installation
```

**Fedora/RHEL/CentOS:**
```bash
# 安装 MySQL
sudo dnf install mysql-server

# 启动服务
sudo systemctl start mysqld
sudo systemctl enable mysqld

# 获取临时密码
sudo grep 'temporary password' /var/log/mysqld.log

# 运行安全配置
sudo mysql_secure_installation
```

**创建数据库（MySQL）:**
```bash
# 登录 MySQL
mysql -u root -p

# 在 MySQL 命令行中
CREATE DATABASE `dash_fastapi` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'backin'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dash_fastapi.* TO 'backin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**在 .env.dev 中配置 MySQL:**
```bash
# -------- MySQL 配置 ----
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USERNAME = 'backin'
DB_PASSWORD = 'your_password'
DB_DATABASE = 'dash_fastapi'
```

### 3. 安装 Python 依赖

**方式一：使用 Poetry（推荐）**
```bash
cd backend/backlin

# 安装 Poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

**方式二：使用 pip**
```bash
cd backend/backlin

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

编辑 `.env.dev` 文件，配置数据库和 Redis 连接信息：

```bash
# -------- 数据库配置 --------
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USERNAME = 'root'
DB_PASSWORD = 'your_password'
DB_DATABASE = 'dash-fastapi'

# -------- Redis配置 --------
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_PASSWORD = ''
REDIS_DATABASE = 0

# -------- 应用配置 --------
APP_HOST = '127.0.0.1'
APP_PORT = 9099
```

### 4. 初始化数据库

**创建数据库:**
```bash
# MySQL
mysql -u root -p
CREATE DATABASE `dash-fastapi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;

# 或使用数据库管理工具（如 Navicat、DBeaver）创建数据库
```

**运行 SQL 文件（如果提供）:**
```bash
# 假设 sql 文件在 sql/ 目录下
mysql -u root -p dash-fastapi < sql/dash-fastapi.sql
```

## 🚀 运行应用

### 开发模式

**使用 CLI 命令（推荐）:**
```bash
# 使用 Poetry
poetry run backlin serve --env dev --host 127.0.0.1 --port 8000

# 或在激活虚拟环境后
backlin serve --env dev --host 127.0.0.1 --port 8000

# 重建数据库并启动（首次运行）
backlin serve --env dev --recreate-db
```

**使用 Python 模块:**
```bash
python -m backlin serve --env dev
```

**直接运行:**
```bash
python backlin/__main__.py serve --env dev
```

### 生产模式

```bash
backlin serve --env prod --host 0.0.0.0 --port 8000
```

### 查看帮助

```bash
backlin --help
backlin serve --help
```

## 📚 API 文档

启动应用后，访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## 🔑 主要模块说明

### module_admin - 管理模块
- **用户管理**：用户 CRUD、角色分配
- **角色管理**：角色权限配置
- **菜单管理**：动态菜单配置
- **部门管理**：组织架构管理
- **字典管理**：数据字典维护
- **日志管理**：操作日志、登录日志
- **缓存管理**：Redis 缓存监控

### module_saas - SaaS 模块
- **API Key 管理**：生成、验证 API 密钥
- **API 接口代理**：统一 API 网关
- **安全认证**：JWT + API Key 双重认证

### routes - 路由模块
- **admin**: 管理后台路由
- **apilog**: API 调用日志
- **client**: 客户端接口
- **openai**: OpenAI 代理接口

## 🛠️ 开发指南

### 添加新模块

1. 在对应模块目录创建文件
2. 定义 Schema（entity/）
3. 创建 DAO（dao/）
4. 实现 Service（service/）
5. 添加 Controller（controller/）
6. 注册路由（routes/）

### 数据库迁移

```bash
# 自动创建表（应用启动时）
backlin serve --env dev --recreate-db

# 或在代码中使用
from backlin.database import Base, engine
Base.metadata.create_all(bind=engine)
```

### 测试

```bash
# 运行测试
pytest

# 代码格式化
black backlin/
```

## 📄 配置说明

### 应用配置 (APP_*)
- `APP_ENV`: 运行环境（dev/prod）
- `APP_NAME`: 应用名称
- `APP_HOST`: 监听地址
- `APP_PORT`: 监听端口
- `APP_RELOAD`: 热重载（开发模式）

### JWT 配置 (JWT_*)
- `JWT_SECRET_KEY`: JWT 密钥
- `JWT_ALGORITHM`: 加密算法（默认 HS256）
- `JWT_EXPIRE_MINUTES`: Token 过期时间

### 数据库配置 (DB_*)
- `DB_HOST`: 数据库地址
- `DB_PORT`: 数据库端口
- `DB_USERNAME`: 用户名
- `DB_PASSWORD`: 密码
- `DB_DATABASE`: 数据库名

### Redis 配置 (REDIS_*)
- `REDIS_HOST`: Redis 地址
- `REDIS_PORT`: Redis 端口
- `REDIS_PASSWORD`: Redis 密码
- `REDIS_DATABASE`: 数据库编号

## 🐛 常见问题

### WSL 环境特别说明

如果你在 WSL（Windows Subsystem for Linux）中运行项目：

**启动服务使用 `service` 命令，而不是 `systemctl`：**
```bash
# 启动 PostgreSQL
sudo service postgresql start

# 启动 Redis
sudo service redis-server start

# 查看状态
sudo service postgresql status
sudo service redis-server status
```

**WSL 重启后服务不会自动启动**，需要手动启动：
```bash
# 每次启动 WSL 后执行
sudo service postgresql start
sudo service redis-server start
```

**可选：创建启动脚本**
```bash
# 创建脚本
cat << 'EOF' > ~/start-services.sh
#!/bin/bash
sudo service postgresql start
sudo service redis-server start
echo "Services started!"
EOF

# 添加执行权限
chmod +x ~/start-services.sh

# 使用
~/start-services.sh
```

### 数据库连接失败
- 检查数据库服务是否启动：`sudo service postgresql status`
- 验证 `.env.dev` 中的连接信息
- 确认数据库已创建
- WSL 用户检查是否已运行 `sudo service postgresql start`

### Redis 连接失败
- 检查 Redis 服务：`redis-cli ping`
- 验证 Redis 配置信息
- 检查防火墙设置

### 依赖安装失败
- 升级 pip：`pip install --upgrade pip`
- 使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
- 检查 Python 版本：`python --version`（需要 >= 3.11）

### 端口被占用
```bash
# 查看端口占用
lsof -i :8000

# 更换端口启动
backlin serve --port 8001
```

## 📖 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Typer 文档](https://typer.tiangolo.com/)
- [Poetry 文档](https://python-poetry.org/docs/)

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**Author**: LinXueyuanStdio
**Version**: 1.4.2