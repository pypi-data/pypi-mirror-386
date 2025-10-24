"""渲染器模块 - 负责将解析结果渲染为消息"""

from typing_extensions import override

from ..helper import Segment, Text
from .base import BaseRenderer, ParseResult, UniHelper, UniMessage


class DefaultRenderer(BaseRenderer):
    """统一的渲染器，将解析结果转换为消息"""

    @override
    async def render_messages(self, result: ParseResult):
        """渲染内容消息

        Args:
            result (ParseResult): 解析结果

        Returns:
            Generator[UniMessage[Any], None, None]: 消息生成器
        """

        texts = [
            result.header,
            result.text,
            result.extra_info,
        ]

        if self.append_url:
            texts.extend((result.display_url, result.repost_display_url))

        texts = [text for text in texts if text]
        texts[:-1] = [text + "\n" for text in texts[:-1]]
        segs: list[Segment] = [Text(text) for text in texts]

        if cover_path := await result.cover_path:
            segs.insert(1, UniHelper.img_seg(cover_path))

        yield UniMessage(segs)

        async for message in self.render_contents(result):
            yield message
