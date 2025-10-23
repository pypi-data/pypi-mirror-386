import pydantic
from nonebot.plugin import PluginMetadata


class MatcherData(pydantic.BaseModel):
    """功能模型"""

    name: str = pydantic.Field(..., description="功能名称")
    usage: str | None = pydantic.Field(default=None, description="功能用法")
    description: str = pydantic.Field(..., description="功能描述")
    related: str | None = pydantic.Field(description="父级菜单", default=None)


class PluginData:
    """插件模型"""

    metadata: PluginMetadata | None
    matchers: list[MatcherData]
    matcher_grouping: dict[str, list[MatcherData]]

    def __init__(
        self, matchers: list[MatcherData], metadata: PluginMetadata | None = None
    ):
        self.metadata = metadata
        self.matchers = matchers
        self.matcher_grouping = {}

        # 先处理所有顶级菜单（没有related的）
        for matcher in self.matchers:
            if matcher.related is None:
                self.matcher_grouping[matcher.name] = [matcher]

        # 然后处理子菜单（有related的）
        for matcher in self.matchers:
            if matcher.related is not None:
                # 确保父菜单存在
                if matcher.related not in self.matcher_grouping:
                    # 如果父菜单不存在，先创建一个空列表
                    self.matcher_grouping[matcher.related] = []

                found = any(
                    existing_matcher.name == matcher.name
                    for existing_matcher in self.matcher_grouping[matcher.related]
                )
                if not found:
                    self.matcher_grouping[matcher.related].append(matcher)
