import asyncio
import os
import sys
import traceback
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import nonebot
from nonebot.log import default_format, logger_id

from amrita.config import get_amrita_config
from amrita.utils.logging import LoggingData, LoggingEvent
from amrita.utils.utils import get_amrita_version

if TYPE_CHECKING:
    # avoid sphinx autodoc resolve annotation failed
    # because loguru module do not have `Logger` class actually
    from loguru import Record


class EventRecorder:
    def write(self, message):
        record: Record = message.record
        data = LoggingEvent(
            log_level=record["level"].name,  # type: ignore
            description=record["message"],
            message=str(record.get("exception", "")),
        )
        logging_data = LoggingData._get_data_sync()
        logging_data.data.append(data)
        logging_data._save_sync()


CUSTOM_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <7}</level> | "
    "<magenta>{name}:{function}:{line}</magenta> | "
    "<level>{message}</level>"
)


def default_filter(record: "Record"):
    """默认的日志过滤器，根据 `config.log_level` 配置改变日志等级。"""
    log_level = record["extra"].get("nonebot_log_level", "INFO")
    levelno = (
        nonebot.logger.level(log_level).no if isinstance(log_level, str) else log_level
    )
    return record["level"].no >= levelno


def init():
    from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter
    from nonebot.adapters.onebot.v11 import Bot, MessageSegment

    from .admin import send_forward_msg_to_admin

    logger = nonebot.logger

    class AsyncErrorHandler:
        def write(self, message):
            try:
                self.task = asyncio.create_task(self.process(message))
            except RuntimeError:
                print(
                    "RuntimeWarning:\nThis is a known bug.\nPlease ignore this warning.\n----------\n"
                )

        async def process(self, message):
            try:
                record: Record = message.record
                if record["level"].name == "ERROR":
                    # 处理异常 traceback
                    if record["exception"]:
                        exc_info = record["exception"]
                        traceback_str = "".join(
                            traceback.format_exception(
                                exc_info.type,  # type: ignore
                                exc_info.value,  # type: ignore
                                exc_info.traceback,  # type: ignore
                            )
                        )
                    else:
                        traceback_str = "无堆栈信息"

                    content = (
                        f"错误信息: {record['message']}\n"
                        f"时间: {record['time']}\n"
                        f"模块: {record['name']}\n"
                        f"文件: {record['file'].path}\n"
                        f"行号: {record['line']}\n"
                        f"函数: {record['function']}\n"
                        f"堆栈信息:\n{traceback_str}"
                    )
                    try:
                        bot = nonebot.get_bot()
                    except Exception:
                        return
                    if isinstance(bot, Bot):
                        await send_forward_msg_to_admin(
                            bot,
                            "Amrita-Exception",
                            bot.self_id,
                            [MessageSegment.text(content)],
                        )

            except Exception as e:
                logger.warning(f"发送群消息失败: {e}")

    Path("plugins").mkdir(exist_ok=True)
    logger.remove(logger_id)
    logger.add(
        sys.stdout,
        level=0,
        diagnose=True,
        format=CUSTOM_FORMAT,
        filter=default_filter,
    )
    logger.add(AsyncErrorHandler(), level="ERROR")
    logger.add(EventRecorder(), level="WARNING")
    nonebot.init()
    logger.success(f"Amrita v{get_amrita_version()} is initializing......")
    driver = nonebot.get_driver()
    driver.register_adapter(ONEBOT_V11Adapter)
    config = get_amrita_config()
    log_dir = config.log_dir
    os.makedirs(log_dir, exist_ok=True)

    logger.add(
        f"{log_dir}/" + "{time}.log",  # 传入函数，每天自动更新日志路径
        level=config.amrita_log_level,
        format=default_format,
        rotation="00:00",
        retention=timedelta(days=7),
        encoding="utf-8",
        enqueue=True,
    )
