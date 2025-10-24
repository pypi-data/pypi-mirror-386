# Todo: 重构Event类实现
from __future__ import annotations

import typing
from enum import Enum
from typing import Literal

from nonebot.adapters.onebot.v11 import (
    Event,
    GroupMessageEvent,
    MessageEvent,
    PokeNotifyEvent,
)
from typing_extensions import override

from amrita.plugins.chat.utils.models import Message, ToolResult

SEND_MESSAGES = list[Message[str | None] | ToolResult]


class EventTypeEnum(str, Enum):
    """
    EventTypeEnum类用于定义和管理不同的事件类型。
    它封装了事件类型的字符串标识，提供了一种结构化的方式 来处理和获取事件类型。

    """

    CHAT = "chat"
    Nil = ""
    POKE = "poke"
    BEFORE_CHAT = "before_chat"
    BEFORE_POKE = "before_poke"

    def validate(self, name: str) -> bool:
        return name in self


class BasicEvent:
    """
    所有事件的基类
    """


class SuggarEvent(BasicEvent):
    """
    与消息收发相关的事件基类
    """

    def __init__(
        self,
        model_response: str,
        nbevent: Event,
        user_id: int,
        send_message: SEND_MESSAGES,
    ):
        """
        初始化SuggarEvent对象

        :param model_response: 模型的响应文本位于列表0的位置
        :param nbevent: NoneBot事件对象
        :param user_id: 用户ID
        :param send_message: 发送的模型的上下文
        """
        # 初始化事件类型为none
        self._event_type = EventTypeEnum.Nil
        # 保存NoneBot事件对象
        self._nbevent = nbevent
        # 初始化模型响应文本
        self._modelResponse: list[str] = [model_response]
        # 初始化用户ID
        self._user_id: int = user_id
        # 初始化要发送的消息内容
        self._send_message: SEND_MESSAGES = send_message

    def __str__(self):
        """
        返回SuggarEvent对象的字符串表示
        """
        return f"SUGGAREVENT({self._event_type},{self._nbevent},{self._modelResponse},{self._user_id},{self._send_message})"

    @property
    def event_type(self) -> str:
        """
        获取事件类型

        :return: 事件类型字符串
        """
        return self._event_type

    def get_nonebot_event(self) -> Event:
        """
        获取NoneBot事件对象

        :return: NoneBot事件对象
        """
        return self._nbevent

    @property
    def message(self) -> SEND_MESSAGES:
        """
        获取传入到模型的上下文

        :return: 消息内容
        """
        return self._send_message

    @property
    def user_id(self) -> int:
        """
        获取用户ID

        :return: 用户ID
        """
        return self._user_id

    @property
    def model_response(self) -> str:
        """
        获取模型响应文本

        :return: 模型响应文本
        """
        return self._modelResponse[0]

    @model_response.setter
    def model_response(self, value: str):
        """
        设置模型响应文本
        """
        self._modelResponse[0] = value

    def get_send_message(self) -> SEND_MESSAGES:
        """
        获取传入到模型的上下文

        :return: 消息内容
        """
        return self._send_message

    def get_event_type(self) -> str:
        """
        获取事件类型，此方法在基类中未实现，应在子类中重写

        :raise NotImplementedError: 当方法未在子类中实现时抛出异常
        """
        raise NotImplementedError

    def get_model_response(self) -> str:
        """
        获取模型响应文本

        :return: 模型响应文本
        """
        return self._modelResponse[0]

    def get_user_id(self) -> int:
        """
        获取用户ID

        :return: 用户ID
        """
        return self._user_id

    def get_event_on_location(self) -> Literal["group", "private"]:
        """
        获取事件发生的位置，此方法在基类中未实现，应在子类中重写

        :raise NotImplementedError: 当方法未在子类中实现时抛出异常
        """
        raise NotImplementedError


class ChatEvent(SuggarEvent):
    """
    聊天事件类，继承自SuggarEvent。

    该类用于处理聊天相关事件，封装了事件的各个属性，如消息事件、发送的消息、模型响应和用户ID。

    参数:
    - nbevent: MessageEvent - 消息事件对象，包含事件的相关信息。
    - send_message: SEND_MESSAGES - 发送到模型的上下文。
    - model_response: str - 模型的响应内容。
    - user_id: int - 用户ID。
    """

    def __init__(
        self,
        nbevent: MessageEvent,
        send_message: SEND_MESSAGES,
        model_response: str,
        user_id: int,
    ):
        """
        构造函数，初始化聊天事件对象。
        """
        super().__init__(
            model_response=model_response,
            nbevent=nbevent,
            user_id=user_id,
            send_message=send_message,
        )
        # 初始化事件类型为聊天事件
        self._event_type = EventTypeEnum.CHAT

    def __str__(self):
        """
        重写__str__方法，返回聊天事件对象的字符串表示。

        返回:
        字符串，包含事件类型、消息事件、模型响应、用户ID和发送到模型的上下文信息。
        """
        return f"SUGGARCHATEVENT({self._event_type},{self._nbevent},{self._modelResponse},{self._user_id},{self._send_message})"

    @override
    def get_event_type(self) -> str:
        """
        获取事件类型。

        返回:
        字符串，表示事件类型为聊天事件。
        """
        return EventTypeEnum.CHAT

    @property
    def event_type(self) -> str:
        """
        事件类型属性，用于获取事件类型。

        返回:
        字符串，表示事件类型为聊天事件。
        """
        return EventTypeEnum.CHAT

    @override
    def get_event_on_location(self) -> Literal["group", "private"]:
        """
        获取事件发生的位置。

        返回:
        字符串，如果是群聊消息事件，则返回"group"，否则返回"private"。
        """
        return "group" if isinstance(self._nbevent, GroupMessageEvent) else "private"

    @property
    def event_message(self):
        return typing.cast(MessageEvent, self._nbevent).message


class PokeEvent(SuggarEvent):
    """
    继承自SuggarEvent的PokeEvent类，用于处理戳一戳事件。

    参数:
    - nbevent: PokeNotifyEvent类型，表示戳一戳通知事件。
    - send_message: SEND_MESSAGES 发送到模型的上下文。
    - model_response: str类型，模型的响应。
    - user_id: int类型，用户ID。
    """

    def __init__(
        self,
        nbevent: PokeNotifyEvent,
        send_message: SEND_MESSAGES,
        model_response: str,
        user_id: int,
    ):
        # 初始化PokeEvent类，并设置相关属性
        super().__init__(
            model_response=model_response,
            nbevent=nbevent,
            user_id=user_id,
            send_message=send_message,
        )
        self._event_type = EventTypeEnum.POKE

    def __str__(self):
        # 重写__str__方法，返回PokeEvent的字符串表示
        return f"SUGGARPOKEEVENT({self._event_type},{self._nbevent},{self._modelResponse},{self._user_id},{self._send_message})"

    @property
    def event_type(self) -> str:
        # event_type属性，返回戳一戳事件类型
        return EventTypeEnum.POKE

    @override
    def get_event_type(self) -> str:
        # 重写get_event_type方法，返回戳一戳事件类型
        return EventTypeEnum.POKE

    @override
    def get_event_on_location(self):
        # 重写get_event_on_location方法，判断戳一戳事件发生的地点是群聊还是私聊
        return "group" if PokeNotifyEvent.group_id else "private"


class BeforePokeEvent(PokeEvent):
    """
    继承自PokeEvent的BeforePokeEvent类，用于处理调用模型之前的事件，通常用于依赖注入或权限控制的写法中。
    参数:
    - nbevent: PokeNotifyEvent类型，表示戳一戳通知事件。
    - send_message: SEND_MESSAGES 发送到模型的上下文。
    - model_response: str类型，模型的响应。
    - user_id: int类型，用户ID。
    """

    def __init__(
        self,
        nbevent: PokeNotifyEvent,
        send_message: SEND_MESSAGES,
        model_response: str,
        user_id: int,
    ):
        # 初始化BeforePokeEvent类，并设置相关属性
        super().__init__(
            model_response=model_response,
            nbevent=nbevent,
            user_id=user_id,
            send_message=send_message,
        )
        self._event_type = EventTypeEnum.BEFORE_POKE

    @property
    def event_type(self) -> str:
        # event_type属性，返回戳一戳事件类型
        return self._event_type

    @override
    def get_event_type(self) -> str:
        # 重写get_event_type方法，返回戳一戳事件类型
        return self._event_type


class BeforeChatEvent(ChatEvent):
    """
    继承自ChatEvent的BeforeChatEvent类，用于处理调用模型之前的事件，通常用于依赖注入或权限控制的写法中。
    参数:
    - nbevent: MessageEvent类型，表示消息事件。
    - send_message: SEND_MESSAGES 发送到模型的上下文。
    - model_response: str类型，模型的响应。
    - user_id: int类型，用户ID。

    """

    def __init__(
        self,
        nbevent: MessageEvent,
        send_message: SEND_MESSAGES,
        model_response: str,
        user_id: int,
    ):
        # 初始化BeforeChatEvent类，并设置相关属性
        super().__init__(
            model_response=model_response,
            nbevent=nbevent,
            user_id=user_id,
            send_message=send_message,
        )
        self._event_type = EventTypeEnum.BEFORE_CHAT

    @property
    def event_type(self) -> str:
        # event_type属性，返回聊天事件类型
        return self._event_type

    @override
    def get_event_type(self) -> str:
        # 重写get_event_type方法，返回聊天事件类型
        return self._event_type
