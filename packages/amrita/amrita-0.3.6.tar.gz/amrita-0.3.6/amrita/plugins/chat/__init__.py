from nonebot.plugin import PluginMetadata, require

require("amrita.plugins.perm")
require("amrita.plugins.menu")
require("amrita.plugins.webui")
require("nonebot_plugin_orm")
require("nonebot_plugin_localstore")


from . import (
    API,
    builtin_hook,
    config,
    matcher_manager,
    page,
    preprocess,
)

__all__ = [
    "API",
    "builtin_hook",
    "config",
    "matcher_manager",
    "page",
    "preprocess",
]

__plugin_meta__ = PluginMetadata(
    name="SuggarChat LLM聊天插件",
    description="强大的聊天插件，即配即用，内建OpenAI协议客户端实现，多模型切换，DeepSeek/Gemini支持，多模态模型支持，适配Onebot-V11适配器",
    usage="https://docs.suggar.top/project/suggarchat/",
    homepage="https://github.com/LiteSuggarDEV/nonebot_plugin_suggarchat/",
    type="application",
    supported_adapters={"~onebot.v11"},
)
