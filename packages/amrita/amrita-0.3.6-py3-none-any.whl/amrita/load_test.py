import importlib
import os
from typing import Any

import nonebot
import nonebot.plugin.manager
from nonebot.plugin.model import Plugin
from nonebot.utils import escape_tag

import amrita

logger = nonebot.logger


class LoadError(Exception):
    def __init__(self, data: Any):
        self.data = data


def _load_plugin(self, name: str) -> Plugin | None:
    """加载指定插件。

    可以使用完整插件模块名或者插件标识符加载。

    参数:
        name: 插件名称或插件标识符。
    """

    try:
        # load using plugin id
        if name in self._third_party_plugin_ids:
            module = importlib.import_module(self._third_party_plugin_ids[name])
        elif name in self._searched_plugin_ids:
            module = importlib.import_module(self._searched_plugin_ids[name])
        # load using module name
        elif (
            name in self._third_party_plugin_ids.values()
            or name in self._searched_plugin_ids.values()
        ):
            module = importlib.import_module(name)
        else:
            raise RuntimeError(f"Plugin not found: {name}! Check your plugin name")

        if (plugin := getattr(module, "__plugin__", None)) is None or not isinstance(
            plugin, Plugin
        ):
            raise RuntimeError(
                f"Module {module.__name__} is not loaded as a plugin! "
                f"Make sure not to import it before loading."
            )
        logger.opt(colors=True).success(
            f'Succeeded to load plugin "<y>{escape_tag(plugin.id_)}</y>"'
            + (
                f' from "<m>{escape_tag(plugin.module_name)}</m>"'
                if plugin.module_name != plugin.id_
                else ""
            )
        )
        return plugin
    except Exception as e:
        logger.opt(colors=True, exception=e).error(
            f'<r><bg #f8bbd0>Failed to import "{escape_tag(name)}"</bg #f8bbd0></r>'
        )
        raise LoadError(e) from e


def main():
    global __name__
    __name__ = "Amrita Loader"
    nonebot.plugin.manager.PluginManager.load_plugin = _load_plugin

    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["ALEMBIC_STARTUP_CHECK"] = "false"
    print("---AMRITA LOADER IS LOADING---")
    amrita.init()
    logger.info("Loading driver...")
    driver = nonebot.get_driver()
    logger.info("Loading plugins...")
    try:
        amrita.load_plugins()
        logger.info("plugin import done!")
    except LoadError:
        logger.error("Test FAILED! Good luck to you next time!")
        exit(1)
    except Exception as e:
        logger.error("OOPS!There is something wrong while this process is running!")
        logger.opt(exception=True).error(f"Error!：{type(e).__name__}")
        exit(1)
    driver.on_startup(exit_test)
    logger.info("Testing pre-startup...")
    amrita.run()


async def exit_test():
    logger.info("Finished!")
    os._exit(0)
