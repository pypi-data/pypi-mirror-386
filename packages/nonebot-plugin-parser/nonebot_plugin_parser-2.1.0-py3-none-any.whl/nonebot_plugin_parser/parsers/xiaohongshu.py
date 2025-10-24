import json
import re
from typing import Any, ClassVar
from typing_extensions import override
from urllib.parse import urlparse

import httpx
import msgspec
from msgspec import Struct, field
from nonebot import logger

from ..exception import ParseException
from .base import BaseParser, Platform


class XiaoHongShuParser(BaseParser):
    # 平台信息
    platform: ClassVar[Platform] = Platform(name="xiaohongshu", display_name="小红书")

    # URL 正则表达式模式（keyword, pattern）
    patterns: ClassVar[list[tuple[str, str]]] = [
        ("xiaohongshu.com", r"https?://(?:www\.)?xiaohongshu\.com/[A-Za-z0-9._?%&+=/#@-]*"),
        ("xhslink.com", r"https?://xhslink\.com/[A-Za-z0-9._?%&+=/#@-]*"),
    ]

    def __init__(self):
        super().__init__()
        explore_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
            "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        }
        self.headers.update(explore_headers)
        discovery_headers = {
            "origin": "https://www.xiaohongshu.com",
            "x-requested-with": "XMLHttpRequest",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
        }
        self.ios_headers.update(discovery_headers)

    @override
    async def parse(self, matched: re.Match[str]):
        """解析 URL 获取内容信息并下载资源

        Args:
            matched: 正则表达式匹配对象，由平台对应的模式匹配得到

        Returns:
            ParseResult: 解析结果

        Raises:
            ParseException: 解析失败时抛出
        """
        # 从匹配对象中获取原始URL
        url = matched.group(0)
        # 处理 xhslink 短链
        if "xhslink" in url:
            url = await self.get_redirect_url(url, self.ios_headers)
            logger.debug(f"xhslink redirect url: {url}")

        urlpath = urlparse(url).path

        if urlpath.startswith("/explore/"):
            xhs_id = urlpath.split("/")[-1]
            return await self._parse_explore(url, xhs_id)
        elif urlpath.startswith("/discovery/item/"):
            return await self._parse_discovery(url)
        else:
            raise ParseException(f"不支持的小红书链接: {url}, urlpath: {urlpath}")

    async def _parse_explore(self, url: str, xhs_id: str):
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
        ) as client:
            response = await client.get(url)
            html = response.text
            logger.info(f"url: {response.url} | status_code: {response.status_code}")

        json_obj = self._extract_initial_state_json(html)

        # ["note"]["noteDetailMap"][xhs_id]["note"]
        note_data = json_obj.get("note", {}).get("noteDetailMap", {}).get(xhs_id, {}).get("note", {})
        if not note_data:
            raise ParseException("can't find note detail in json_obj")

        class Image(Struct):
            urlDefault: str

        class User(Struct):
            nickname: str
            avatar: str

        class NoteDetail(Struct):
            type: str
            title: str
            desc: str
            user: User
            imageList: list[Image] = field(default_factory=list)
            video: Video | None = None

            @property
            def nickname(self) -> str:
                return self.user.nickname

            @property
            def avatar_url(self) -> str:
                return self.user.avatar

            @property
            def image_urls(self) -> list[str]:
                return [item.urlDefault for item in self.imageList]

            @property
            def video_url(self) -> str | None:
                if self.type != "video" or not self.video:
                    return None
                return self.video.video_url

        note_detail = msgspec.convert(note_data, type=NoteDetail)

        contents = []
        # 添加视频内容
        if video_url := note_detail.video_url:
            # 使用第一张图片作为封面
            cover_url = note_detail.image_urls[0] if note_detail.image_urls else None
            contents.append(self.create_video_content(video_url, cover_url))

        # 添加图片内容
        elif image_urls := note_detail.image_urls:
            contents.extend(self.create_image_contents(image_urls))

        # 构建作者
        author = self.create_author(note_detail.nickname, note_detail.avatar_url)

        return self.result(
            title=note_detail.title,
            text=note_detail.desc,
            author=author,
            contents=contents,
        )

    async def _parse_discovery(self, url: str):
        async with httpx.AsyncClient(
            headers=self.ios_headers,
            timeout=self.timeout,
            follow_redirects=True,
            cookies=httpx.Cookies(),
            trust_env=False,
        ) as client:
            response = await client.get(url)
            html = response.text

        json_obj = self._extract_initial_state_json(html)
        note_data = json_obj.get("noteData")
        if not note_data:
            raise ParseException("can't find noteData in json_obj")
        preload_data = note_data.get("normalNotePreloadData", {})
        note_data = note_data.get("data", {}).get("noteData", {})
        if not note_data:
            raise ParseException("can't find noteData in noteData.data")

        class Image(Struct):
            url: str
            urlSizeLarge: str | None = None

        class User(Struct):
            nickName: str
            avatar: str

        class NoteData(Struct):
            type: str
            title: str
            desc: str
            user: User
            time: int
            lastUpdateTime: int
            imageList: list[Image] = []  # 有水印
            video: Video | None = None

            @property
            def image_urls(self) -> list[str]:
                return [item.url for item in self.imageList]

            @property
            def video_url(self) -> str | None:
                if self.type != "video" or not self.video:
                    return None
                return self.video.video_url

        class NormalNotePreloadData(Struct):
            title: str
            desc: str
            imagesList: list[Image] = []  # 无水印, 但只有一只，用于视频封面

            @property
            def image_urls(self) -> list[str]:
                return [item.urlSizeLarge or item.url for item in self.imagesList]

        note_data = msgspec.convert(note_data, type=NoteData)

        contents = []
        if video_url := note_data.video_url:
            if preload_data:
                preload_data = msgspec.convert(preload_data, type=NormalNotePreloadData)
                img_urls = preload_data.image_urls
            else:
                img_urls = note_data.image_urls
            contents.append(self.create_video_content(video_url, img_urls[0]))
        elif img_urls := note_data.image_urls:
            contents.extend(self.create_image_contents(img_urls))

        return self.result(
            title=note_data.title,
            author=self.create_author(note_data.user.nickName, note_data.user.avatar),
            contents=contents,
            text=note_data.desc,
            timestamp=note_data.time // 1000,
        )

    def _extract_initial_state_json(self, html: str) -> dict[str, Any]:
        pattern = r"window\.__INITIAL_STATE__=(.*?)</script>"
        matched = re.search(pattern, html)
        if not matched:
            raise ParseException("小红书分享链接失效或内容已删除")

        json_str = matched.group(1).replace("undefined", "null")
        return json.loads(json_str)


class Stream(Struct):
    h264: list[dict[str, Any]] | None = None
    h265: list[dict[str, Any]] | None = None
    av1: list[dict[str, Any]] | None = None
    h266: list[dict[str, Any]] | None = None


class Media(Struct):
    stream: Stream


class Video(Struct):
    media: Media

    @property
    def video_url(self) -> str | None:
        stream = self.media.stream

        # h264 有水印，h265 无水印
        if stream.h265:
            return stream.h265[0]["masterUrl"]
        elif stream.h264:
            return stream.h264[0]["masterUrl"]
        elif stream.av1:
            return stream.av1[0]["masterUrl"]
        elif stream.h266:
            return stream.h266[0]["masterUrl"]
        return None
