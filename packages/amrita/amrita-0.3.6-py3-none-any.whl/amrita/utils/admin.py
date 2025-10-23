from __future__ import annotations

import typing

import nonebot
from nonebot.adapters.onebot.v11 import Bot, MessageSegment

from amrita.config import get_amrita_config


async def send_to_admin(msg: str, bot: Bot | None = None):
    """发送消息到管理

    Args:
        bot (Bot): Bot
        msg (str): 消息内容
    """
    config = get_amrita_config()
    if config.admin_group == -1:
        return nonebot.logger.warning("SEND_TO_ADMIN\n" + msg)
    if bot is None:
        bot = typing.cast(Bot, nonebot.get_bot())
    await bot.send_group_msg(group_id=config.admin_group, message=msg)


async def send_forward_msg_to_admin(
    bot: Bot, name: str, uin: str, msgs: list[MessageSegment]
):
    """发送消息到管理

    Args:
        bot (Bot): Bot
        name (str): 名称
        uin (str): UID
        msgs (list[MessageSegment]): 消息列表

    Returns:
        dict: 发送消息后的结果
    """
    def to_json(msg: MessageSegment) -> dict:
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    config = get_amrita_config()
    if config.admin_group == -1:
        return nonebot.logger.warning(
            "LOG_MSG_FORWARD\n".join(
                [msg.data.get("text", "") for msg in msgs if msg.is_text()]
            )
        )

    messages = [to_json(msg) for msg in msgs]
    await bot.send_group_forward_msg(group_id=config.admin_group, messages=messages)
