# -*- encoding: utf-8 -*-
# @Time    :   2025/10/12 12:58:27
# @File    :   log_manage.py
# @Author  :   ciaoyizhen
# @Contact :   yizhen.ciao@gmail.com
# @Function:   日志的封装

import os
from .utils import singleton
from loguru import logger
from tqdm import tqdm

@singleton
class LoggerManager:
    """简洁生产级 Loguru 封装类
    
    用法：
        log = LoggerManager("logs/app.log")
        log.info("启动成功")
        log.error("错误信息")
    """

    def __init__(
        self,
        log_path: str|None = None,
        level: str = "INFO",
        rotation: str = "10 MB",
        retention: str = "7 days",
        compression: str = "zip",
        enqueue: bool = True,
        console: bool = True,
    ):
        
        logger.remove()  # 清空默认配置

        # 文件日志
        if log_path is not None:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            logger.add(
                log_path,
                rotation=rotation,
                retention=retention,
                compression=compression,
                enqueue=enqueue,  # ✅ 支持多进程
                level=level,
                encoding="utf-8",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | line:{line} | {message}",
            )

        # 控制台日志（可选）
        if console:
            logger.add(
                sink=lambda msg: tqdm.write(msg, end=""),
                level=level,
                format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | line:{line} | <level>{message}</level>",
            )
        self._logger = logger

    # ↓↓↓ 对 loguru 常用方法的封装 ↓↓↓
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)
