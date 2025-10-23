import os
import time
from loguru import logger

from backlin.config.env import AppConfig

# 从配置获取日志路径
log_dir = AppConfig.app_log_dir
if os.path.isabs(log_dir):
    log_path = log_dir
else:
    log_path = os.path.join(os.getcwd(), log_dir)

if not os.path.exists(log_path):
    os.makedirs(log_path, exist_ok=True)

log_path_error = os.path.join(log_path, f'{time.strftime("%Y-%m-%d")}_error.log')

logger.add(log_path_error, rotation="50MB", encoding="utf-8", enqueue=True, compression="zip")
