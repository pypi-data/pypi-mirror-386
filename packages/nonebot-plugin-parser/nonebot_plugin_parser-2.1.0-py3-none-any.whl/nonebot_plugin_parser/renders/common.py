from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import ClassVar
from typing_extensions import override

from nonebot import logger
from PIL import Image, ImageDraw, ImageFont

from .base import ImageRenderer, ParseResult


@dataclass(eq=False, frozen=True, slots=True)
class FontInfo:
    """字体信息数据类"""

    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    line_height: int
    cjk_width: int

    def __hash__(self) -> int:
        """实现哈希方法以支持 @lru_cache"""
        return hash((id(self.font), self.line_height, self.cjk_width))

    @lru_cache(maxsize=400)
    def get_char_width(self, char: str) -> int:
        """获取字符宽度，使用缓存优化"""
        bbox = self.font.getbbox(char)
        width = int(bbox[2] - bbox[0])
        return width

    def get_char_width_fast(self, char: str) -> int:
        """快速获取单个字符宽度"""
        if "\u4e00" <= char <= "\u9fff":
            return self.cjk_width
        else:
            return self.get_char_width(char)

    def get_text_width(self, text: str) -> int:
        """计算文本宽度，使用预计算的字符宽度优化性能

        Args:
            text: 要计算宽度的文本

        Returns:
            文本宽度（像素）
        """
        if not text:
            return 0

        total_width = 0
        for char in text:
            total_width += self.get_char_width_fast(char)
        return total_width


@dataclass(eq=False, frozen=True, slots=True)
class FontSet:
    """字体集数据类"""

    FONT_SIZES: ClassVar[dict[str, int]] = {"name": 28, "title": 30, "text": 24, "extra": 24, "indicator": 60}
    """字体大小"""

    name_font: FontInfo
    title_font: FontInfo
    text_font: FontInfo
    extra_font: FontInfo
    indicator_font: FontInfo

    @classmethod
    def new(cls, font_path: Path):
        font_infos: dict[str, FontInfo] = {}
        for name, size in cls.FONT_SIZES.items():
            font = ImageFont.truetype(font_path, size)
            font_infos[f"{name}_font"] = FontInfo(font=font, line_height=size + 4, cjk_width=size)
        return FontSet(**font_infos)


@dataclass(eq=False, frozen=True, slots=True)
class SectionData:
    """基础部分数据类"""

    height: int


@dataclass(eq=False, frozen=True, slots=True)
class HeaderSectionData(SectionData):
    """Header 部分数据"""

    avatar: Image.Image | None
    name_lines: list[str]
    time_lines: list[str]
    text_height: int


@dataclass(eq=False, frozen=True, slots=True)
class TitleSectionData(SectionData):
    """标题部分数据"""

    lines: list[str]


@dataclass(eq=False, frozen=True, slots=True)
class CoverSectionData(SectionData):
    """封面部分数据"""

    cover_img: Image.Image


@dataclass(eq=False, frozen=True, slots=True)
class TextSectionData(SectionData):
    """文本部分数据"""

    lines: list[str]


@dataclass(eq=False, frozen=True, slots=True)
class ExtraSectionData(SectionData):
    """额外信息部分数据"""

    lines: list[str]


@dataclass(eq=False, frozen=True, slots=True)
class RepostSectionData(SectionData):
    """转发部分数据"""

    scaled_image: Image.Image


@dataclass(eq=False, frozen=True, slots=True)
class ImageGridSectionData(SectionData):
    """图片网格部分数据"""

    images: list[Image.Image]
    cols: int
    rows: int
    has_more: bool
    remaining_count: int


@dataclass(eq=False, frozen=True, slots=True)
class GraphicsSectionData(SectionData):
    """图文内容部分数据"""

    text_lines: list[str]
    image: Image.Image
    alt_text: str | None = None


class CommonRenderer(ImageRenderer):
    """统一的渲染器，将解析结果转换为消息"""

    __slots__ = ("font_path", "fontset", "platform_logos", "video_button_image")

    # 卡片配置常量
    PADDING = 25
    """内边距"""
    AVATAR_SIZE = 80
    """头像大小"""
    AVATAR_TEXT_GAP = 15
    """头像和文字之间的间距"""
    MAX_COVER_WIDTH = 1000
    """封面最大宽度"""
    MAX_COVER_HEIGHT = 800
    """封面最大高度"""
    DEFAULT_CARD_WIDTH = 800
    """默认卡片宽度"""
    MIN_CARD_WIDTH = 400
    """最小卡片宽度"""
    SECTION_SPACING = 15
    """部分间距"""
    NAME_TIME_GAP = 5
    """名称和时间之间的间距"""
    AVATAR_UPSCALE_FACTOR = 2
    """头像圆形框超采样倍数"""

    # 图片处理配置
    MIN_COVER_WIDTH = 300
    """最小封面宽度"""
    MIN_COVER_HEIGHT = 200
    """最小封面高度"""
    MAX_IMAGE_HEIGHT = 800
    """图片最大高度限制"""
    IMAGE_3_GRID_SIZE = 300
    """图片3列网格最大尺寸"""
    IMAGE_2_GRID_SIZE = 400
    """图片2列网格最大尺寸"""
    IMAGE_GRID_SPACING = 4
    """图片网格间距"""
    MAX_IMAGES_DISPLAY = 9
    """最大显示图片数量"""
    IMAGE_GRID_COLS = 3
    """图片网格列数"""

    # 颜色配置
    BG_COLOR: ClassVar[tuple[int, int, int]] = (255, 255, 255)
    """背景色"""
    TEXT_COLOR: ClassVar[tuple[int, int, int]] = (51, 51, 51)
    """文本色"""
    HEADER_COLOR: ClassVar[tuple[int, int, int]] = (0, 122, 255)
    """标题色"""
    EXTRA_COLOR: ClassVar[tuple[int, int, int]] = (136, 136, 136)
    """额外信息色"""

    # 转发内容配置
    REPOST_BG_COLOR: ClassVar[tuple[int, int, int]] = (247, 247, 247)
    """转发背景色"""
    REPOST_BORDER_COLOR: ClassVar[tuple[int, int, int]] = (230, 230, 230)
    """转发边框色"""
    REPOST_PADDING = 12
    """转发内容内边距"""
    REPOST_SCALE = 0.88
    """转发缩放比例"""

    RESOURCES_DIR: ClassVar[Path] = Path(__file__).parent / "resources"
    """资源目录"""
    DEFAULT_FONT_PATH: ClassVar[Path] = RESOURCES_DIR / "HYSongYunLangHeiW-1.ttf"
    """默认字体路径"""
    DEFAULT_VIDEO_BUTTON_PATH: ClassVar[Path] = RESOURCES_DIR / "media_button.png"
    """默认视频按钮路径"""

    def __init__(self, font_path: Path | None = None):
        self.font_path: Path = self.DEFAULT_FONT_PATH

    def load_resources(self):
        """加载资源"""
        self._load_fonts()
        self._load_video_button()
        self._load_platform_logos()

    def _load_fonts(self):
        """预加载自定义字体"""
        from ..config import pconfig

        font_path = pconfig.custom_font
        if font_path is not None and font_path.exists():
            self.font_path = font_path
        # 创建 FontSet 对象
        self.fontset = FontSet.new(self.font_path)
        logger.success(f"加载字体「{self.font_path.name}」成功")

    def _load_video_button(self):
        """预加载视频按钮"""
        self.video_button_image: Image.Image = Image.open(self.DEFAULT_VIDEO_BUTTON_PATH).convert("RGBA")

        # 设置透明度为 30%
        alpha = self.video_button_image.split()[-1]  # 获取 alpha 通道
        alpha = alpha.point(lambda x: int(x * 0.3))  # 将透明度设置为 30%
        self.video_button_image.putalpha(alpha)

    def _load_platform_logos(self):
        """预加载平台 logo"""
        self.platform_logos: dict[str, Image.Image] = {}
        platform_names = ["bilibili", "douyin", "youtube", "kuaishou", "twitter", "tiktok", "weibo", "xiaohongshu"]

        for platform_name in platform_names:
            logo_path = self.RESOURCES_DIR / f"{platform_name}.png"
            if logo_path.exists():
                self.platform_logos[platform_name] = Image.open(logo_path)

    # def __resize_platform_logos(self):
    #     """调整平台 logo 尺寸, 用于调整 logo 大小(仅开发时使用)"""
    #     # 平台 logo 对应的高度
    #     platform_names_height: dict[str, int] = {
    #         "bilibili": 30,
    #         "douyin": 30,
    #         "youtube": 24,
    #         "kuaishou": 36,
    #         "twitter": 30,
    #         "tiktok": 30,
    #         "weibo": 30,
    #         "xiaohongshu": 24,
    #     }
    #     for platform_name, target_height in platform_names_height.items():
    #         logo_path = Path() / "resources" / "logos" / f"{platform_name}.png"
    #         logger.info(f"logo_path: {logo_path}")
    #         save_path = self.RESOURCES_DIR / f"{platform_name}.png"
    #         if logo_path.exists():
    #             try:
    #                 logo_img = Image.open(logo_path).convert("RGBA")
    #                 # 调整 logo 尺寸, 只限制高度为30像素
    #                 ratio = target_height / logo_img.height
    #                 new_width = int(logo_img.width * ratio)
    #                 new_height = target_height
    #                 logo_img = logo_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    #                 # 保存图片
    #                 logo_img.save(save_path)
    #             except Exception:
    #                 # 如果加载失败，跳过这个 logo
    #                 logger.error(f"resize 平台 logo 失败: {platform_name}")
    #                 continue

    @override
    async def render_image(self, result: ParseResult) -> bytes:
        """使用 PIL 绘制通用社交媒体帖子卡片

        Args:
            result: 解析结果

        Returns:
            PNG 图片的字节数据，如果没有足够的内容则返回 None
        """
        # 调用内部方法生成图片
        image = await self._create_card_image(result)

        # 将图片转换为字节
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    async def _create_card_image(
        self, result: ParseResult, bg_color: tuple[int, int, int] | None = None, not_repost: bool = True
    ) -> Image.Image:
        """创建卡片图片（内部方法，用于递归调用）

        Args:
            result: 解析结果
            bg_color: 背景颜色，默认使用 BG_COLOR
            not_repost: 是否为非转发内容，转发内容为 False

        Returns:
            PIL Image 对象
        """

        # 使用默认卡片宽度
        card_width = self.DEFAULT_CARD_WIDTH
        content_width = card_width - 2 * self.PADDING

        # 加载并处理封面，传入内容区域宽度以确保封面不超过内容区域
        cover_img = self._load_and_resize_cover(
            await result.cover_path, content_width=content_width, apply_min_size=not_repost
        )

        # 计算各部分内容的高度
        sections = await self._calculate_sections(result, cover_img, content_width)

        # 计算总高度
        card_height = (
            sum(section.height for section in sections) + self.PADDING * 2 + self.SECTION_SPACING * (len(sections) - 1)
        )
        # 创建画布并绘制（使用指定的背景颜色，或默认背景颜色）
        background_color = bg_color if bg_color is not None else self.BG_COLOR
        image = Image.new("RGB", (card_width, card_height), background_color)
        self._draw_sections(image, sections, card_width, result, not_repost)

        return image

    def _load_and_resize_cover(
        self, cover_path: Path | None, content_width: int, apply_min_size: bool = True
    ) -> Image.Image | None:
        """加载并调整封面尺寸

        Args:
            cover_path: 封面路径
            content_width: 内容区域宽度，封面会缩放到此宽度以确保左右padding一致
            apply_min_size: 是否应用最小尺寸限制（转发内容不需要）
        """
        if not cover_path or not cover_path.exists():
            return None

        try:
            cover_img = Image.open(cover_path)

            # 转换为 RGB 模式以确保兼容性
            if cover_img.mode not in ("RGB", "RGBA"):
                cover_img = cover_img.convert("RGB")

            # 封面宽度应该等于内容区域宽度，以确保左右padding一致
            target_width = content_width

            # 计算缩放比例（保持宽高比）
            if cover_img.width != target_width:
                scale_ratio = target_width / cover_img.width
                new_width = target_width
                new_height = int(cover_img.height * scale_ratio)

                # 检查高度是否超过最大限制
                if new_height > self.MAX_COVER_HEIGHT:
                    # 如果高度超限，按高度重新计算
                    scale_ratio = self.MAX_COVER_HEIGHT / new_height
                    new_height = self.MAX_COVER_HEIGHT
                    new_width = int(new_width * scale_ratio)

                cover_img = cover_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            return cover_img
        except Exception:
            # 加载失败时返回 None
            return None

    def _load_and_process_avatar(self, avatar: Path | None) -> Image.Image | None:
        """加载并处理头像（圆形裁剪，带抗锯齿）"""
        if not avatar or not avatar.exists():
            return None

        try:
            avatar_img = Image.open(avatar)

            # 转换为 RGBA 模式（用于更好的抗锯齿效果）
            if avatar_img.mode != "RGBA":
                avatar_img = avatar_img.convert("RGBA")

            # 使用超采样技术提高质量：先放大到指定倍数
            scale = self.AVATAR_UPSCALE_FACTOR
            temp_size = self.AVATAR_SIZE * scale
            avatar_img = avatar_img.resize((temp_size, temp_size), Image.Resampling.LANCZOS)

            # 创建高分辨率圆形遮罩（带抗锯齿）
            mask = Image.new("L", (temp_size, temp_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, temp_size - 1, temp_size - 1), fill=255)

            # 应用遮罩
            output_avatar = Image.new("RGBA", (temp_size, temp_size), (0, 0, 0, 0))
            output_avatar.paste(avatar_img, (0, 0))
            output_avatar.putalpha(mask)

            # 缩小到目标尺寸（抗锯齿缩放）
            output_avatar = output_avatar.resize((self.AVATAR_SIZE, self.AVATAR_SIZE), Image.Resampling.LANCZOS)

            return output_avatar
        except Exception:
            return None

    async def _calculate_sections(
        self, result: ParseResult, cover_img: Image.Image | None, content_width: int
    ) -> list[SectionData]:
        """计算各部分内容的高度和数据"""
        sections = []

        # 1. Header 部分
        if result.author:
            header_section = await self._calculate_header_section(result, content_width)
            if header_section:
                sections.append(header_section)

        # 2. 标题部分
        if result.title:
            title_lines = self._wrap_text(result.title, content_width, self.fontset.title_font)
            title_height = len(title_lines) * self.fontset.title_font.line_height
            sections.append(TitleSectionData(height=title_height, lines=title_lines))

        # 3. 封面，图集，图文内容
        if cover_img:
            sections.append(CoverSectionData(height=cover_img.height, cover_img=cover_img))
        elif result.img_contents:
            # 如果没有封面但有图片，处理图片列表
            img_grid_section = await self._calculate_image_grid_section(result, content_width)
            if img_grid_section:
                sections.append(img_grid_section)
        elif result.graphics_contents:
            for graphics_content in result.graphics_contents:
                graphics_section = await self._calculate_graphics_section(graphics_content, content_width)
                if graphics_section:
                    sections.append(graphics_section)

        # 5. 文本内容
        if result.text:
            text_lines = self._wrap_text(result.text, content_width, self.fontset.text_font)
            text_height = len(text_lines) * self.fontset.text_font.line_height
            sections.append(TextSectionData(height=text_height, lines=text_lines))

        # 6. 额外信息
        if result.extra_info:
            extra_lines = self._wrap_text(result.extra_info, content_width, self.fontset.extra_font)
            extra_height = len(extra_lines) * self.fontset.extra_font.line_height
            sections.append(ExtraSectionData(height=extra_height, lines=extra_lines))

        # 6. 转发内容
        if result.repost:
            repost_section = await self._calculate_repost_section(result.repost)
            if repost_section:
                sections.append(repost_section)

        return sections

    async def _calculate_graphics_section(self, graphics_content, content_width: int) -> GraphicsSectionData | None:
        """计算图文内容部分的高度和内容"""
        try:
            # 加载图片
            img_path = await graphics_content.get_path()
            if not img_path or not img_path.exists():
                return None

            image = Image.open(img_path)

            # 调整图片尺寸以适应内容宽度
            if image.width > content_width:
                ratio = content_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((content_width, new_height), Image.Resampling.LANCZOS)

            # 处理文本内容
            text_lines = []
            if graphics_content.text:
                text_lines = self._wrap_text(graphics_content.text, content_width, self.fontset.text_font)

            # 计算总高度：文本高度 + 图片高度 + alt文本高度 + 间距
            text_height = len(text_lines) * self.fontset.text_font.line_height if text_lines else 0
            alt_height = self.fontset.extra_font.line_height if graphics_content.alt else 0
            total_height = text_height + image.height + alt_height
            if text_lines:
                total_height += self.SECTION_SPACING  # 文本和图片之间的间距
            if graphics_content.alt:
                total_height += self.SECTION_SPACING  # 图片和alt文本之间的间距

            return GraphicsSectionData(
                height=total_height, text_lines=text_lines, image=image, alt_text=graphics_content.alt
            )
        except Exception:
            return None

    async def _calculate_header_section(self, result: ParseResult, content_width: int) -> HeaderSectionData | None:
        """计算 header 部分的高度和内容"""
        if not result.author:
            return None

        # 加载头像
        avatar_img = self._load_and_process_avatar(await result.author.get_avatar_path())

        # 计算文字区域宽度（始终预留头像空间）
        text_area_width = content_width - (self.AVATAR_SIZE + self.AVATAR_TEXT_GAP)

        # 发布者名称
        name_lines = self._wrap_text(result.author.name, text_area_width, self.fontset.name_font)

        # 时间
        time_text = result.formartted_datetime
        time_lines = self._wrap_text(time_text, text_area_width, self.fontset.extra_font) if time_text else []

        # 计算 header 高度（取头像和文字中较大者）
        text_height = len(name_lines) * self.fontset.name_font.line_height
        if time_lines:
            text_height += self.NAME_TIME_GAP + len(time_lines) * self.fontset.extra_font.line_height
        header_height = max(self.AVATAR_SIZE, text_height)

        return HeaderSectionData(
            height=header_height,
            avatar=avatar_img,
            name_lines=name_lines,
            time_lines=time_lines,
            text_height=text_height,
        )

    async def _calculate_repost_section(self, repost: ParseResult) -> RepostSectionData | None:
        """计算转发内容的高度和内容（递归调用绘制方法）"""
        if not repost:
            return None

        # 递归调用内部方法，生成转发内容的完整卡片（使用转发背景颜色，不强制放大封面）
        repost_image = await self._create_card_image(repost, bg_color=self.REPOST_BG_COLOR, not_repost=False)
        if not repost_image:
            return None

        # 缩放图片
        scaled_width = int(repost_image.width * self.REPOST_SCALE)
        scaled_height = int(repost_image.height * self.REPOST_SCALE)
        repost_image_scaled = repost_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        return RepostSectionData(
            height=scaled_height + self.REPOST_PADDING * 2,  # 加上转发容器的内边距
            scaled_image=repost_image_scaled,
        )

    async def _calculate_image_grid_section(
        self, result: ParseResult, content_width: int
    ) -> ImageGridSectionData | None:
        """计算图片网格部分的高度和内容"""
        if not result.img_contents:
            return None

        # 检查是否有超过最大显示数量的图片
        total_images = len(result.img_contents)
        has_more = total_images > self.MAX_IMAGES_DISPLAY

        # 如果超过最大显示数量，处理前N张，最后一张显示+N效果
        if has_more:
            img_contents = result.img_contents[: self.MAX_IMAGES_DISPLAY]
            remaining_count = total_images - self.MAX_IMAGES_DISPLAY
        else:
            img_contents = result.img_contents[: self.MAX_IMAGES_DISPLAY]
            remaining_count = 0

        processed_images = []

        for img_content in img_contents:
            try:
                img_path = await img_content.get_path()
                if not img_path or not img_path.exists():
                    continue

                img = Image.open(img_path)

                # 根据图片数量决定处理方式
                if len(img_contents) >= 2:
                    # 2张及以上图片，统一为方形
                    img = self._crop_to_square(img)

                # 计算图片尺寸
                if len(img_contents) == 1:
                    # 单张图片，根据卡片宽度调整，与视频封面保持一致
                    max_width = content_width
                    max_height = min(self.MAX_IMAGE_HEIGHT, content_width)  # 限制最大高度
                    if img.width > max_width or img.height > max_height:
                        ratio = min(max_width / img.width, max_height / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    # 多张图片，计算最大尺寸
                    if len(img_contents) in (2, 4):
                        # 2张或4张图片，使用2列布局
                        num_gaps = 3  # 2列有3个间距
                        max_size = (content_width - self.IMAGE_GRID_SPACING * num_gaps) // 2
                        max_size = min(max_size, self.IMAGE_2_GRID_SIZE)
                    else:
                        # 多张图片，使用3列布局
                        num_gaps = self.IMAGE_GRID_COLS + 1
                        max_size = (content_width - self.IMAGE_GRID_SPACING * num_gaps) // self.IMAGE_GRID_COLS
                        max_size = min(max_size, self.IMAGE_3_GRID_SIZE)

                    # 调整多张图片的尺寸
                    if img.width > max_size or img.height > max_size:
                        ratio = min(max_size / img.width, max_size / img.height)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)

                processed_images.append(img)
            except Exception:
                continue

        if not processed_images:
            return None

        # 计算网格布局
        image_count = len(processed_images)

        if image_count == 1:
            # 单张图片
            cols, rows = 1, 1
        elif image_count in (2, 4):
            # 2张或4张图片，使用2列布局
            cols, rows = 2, (image_count + 1) // 2
        else:
            # 多张图片，使用3列布局（九宫格）
            cols = self.IMAGE_GRID_COLS
            rows = (image_count + cols - 1) // cols

        # 计算高度
        max_img_height = max(img.height for img in processed_images)
        if len(processed_images) == 1:
            # 单张图片
            grid_height = max_img_height
        else:
            # 多张图片：上间距 + (图片 + 间距) * 行数
            grid_height = self.IMAGE_GRID_SPACING + rows * (max_img_height + self.IMAGE_GRID_SPACING)

        return ImageGridSectionData(
            height=grid_height,
            images=processed_images,
            cols=cols,
            rows=rows,
            has_more=has_more,
            remaining_count=remaining_count,
        )

    def _crop_to_square(self, img: Image.Image) -> Image.Image:
        """将图片裁剪为方形（上下切割）"""
        width, height = img.size

        if width == height:
            return img

        if width > height:
            # 宽图片，左右切割
            left = (width - height) // 2
            right = left + height
            return img.crop((left, 0, right, height))
        else:
            # 高图片，上下切割
            top = (height - width) // 2
            bottom = top + width
            return img.crop((0, top, width, bottom))

    def _draw_sections(
        self,
        image: Image.Image,
        sections: list[SectionData],
        card_width: int,
        result: ParseResult,
        not_repost: bool = True,
    ) -> None:
        """绘制所有内容到画布上"""
        draw = ImageDraw.Draw(image)
        y_pos = self.PADDING

        for section in sections:
            match section:
                case HeaderSectionData() as header:
                    y_pos = self._draw_header(image, draw, header, y_pos, result, not_repost)
                case TitleSectionData() as title:
                    y_pos = self._draw_title(draw, title.lines, y_pos, self.fontset.title_font.font)
                case CoverSectionData() as cover:
                    y_pos = self._draw_cover(image, cover.cover_img, y_pos, card_width)
                case TextSectionData() as text:
                    y_pos = self._draw_text(draw, text.lines, y_pos, self.fontset.text_font.font)
                case GraphicsSectionData() as graphics:
                    y_pos = self._draw_graphics(image, draw, graphics, y_pos, card_width)
                case ExtraSectionData() as extra:
                    y_pos = self._draw_extra(draw, extra.lines, y_pos, self.fontset.extra_font.font)
                case RepostSectionData() as repost:
                    y_pos = self._draw_repost(image, draw, repost, y_pos, card_width)
                case ImageGridSectionData() as image_grid:
                    y_pos = self._draw_image_grid(image, image_grid, y_pos, card_width)

    def _create_avatar_placeholder(self) -> Image.Image:
        """创建默认头像占位符"""
        # 头像占位符配置常量
        placeholder_bg_color = (230, 230, 230, 255)
        placeholder_fg_color = (200, 200, 200, 255)
        head_ratio = 0.35  # 头部位置比例
        head_radius_ratio = 1 / 6  # 头部半径比例
        shoulder_y_ratio = 0.55  # 肩部 Y 位置比例
        shoulder_width_ratio = 0.55  # 肩部宽度比例
        shoulder_height_ratio = 0.6  # 肩部高度比例

        placeholder = Image.new("RGBA", (self.AVATAR_SIZE, self.AVATAR_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(placeholder)

        # 绘制圆形背景
        draw.ellipse((0, 0, self.AVATAR_SIZE - 1, self.AVATAR_SIZE - 1), fill=placeholder_bg_color)

        # 绘制简单的用户图标（圆形头部 + 肩部）
        center_x = self.AVATAR_SIZE // 2

        # 头部圆形
        head_radius = int(self.AVATAR_SIZE * head_radius_ratio)
        head_y = int(self.AVATAR_SIZE * head_ratio)
        draw.ellipse(
            (
                center_x - head_radius,
                head_y - head_radius,
                center_x + head_radius,
                head_y + head_radius,
            ),
            fill=placeholder_fg_color,
        )

        # 肩部
        shoulder_y = int(self.AVATAR_SIZE * shoulder_y_ratio)
        shoulder_width = int(self.AVATAR_SIZE * shoulder_width_ratio)
        shoulder_height = int(self.AVATAR_SIZE * shoulder_height_ratio)
        draw.ellipse(
            (
                center_x - shoulder_width // 2,
                shoulder_y,
                center_x + shoulder_width // 2,
                shoulder_y + shoulder_height,
            ),
            fill=placeholder_fg_color,
        )

        # 创建圆形遮罩确保不超出边界
        mask = Image.new("L", (self.AVATAR_SIZE, self.AVATAR_SIZE), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, self.AVATAR_SIZE - 1, self.AVATAR_SIZE - 1), fill=255)

        # 应用遮罩
        placeholder.putalpha(mask)
        return placeholder

    def _draw_header(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        section: HeaderSectionData,
        y_pos: int,
        result: ParseResult,
        not_repost: bool = True,
    ) -> int:
        """绘制 header 部分"""
        x_pos = self.PADDING

        # 绘制头像或占位符
        avatar = section.avatar if section.avatar else self._create_avatar_placeholder()
        image.paste(avatar, (x_pos, y_pos), avatar)

        # 文字始终从头像位置后面开始
        text_x = self.PADDING + self.AVATAR_SIZE + self.AVATAR_TEXT_GAP

        # 计算文字垂直居中位置（对齐头像中轴）
        avatar_center = y_pos + self.AVATAR_SIZE // 2
        text_start_y = avatar_center - section.text_height // 2
        text_y = text_start_y

        # 发布者名称（蓝色）
        for line in section.name_lines:
            draw.text((text_x, text_y), line, fill=self.HEADER_COLOR, font=self.fontset.name_font.font)
            text_y += self.fontset.name_font.line_height

        # 时间（灰色）
        if section.time_lines:
            text_y += self.NAME_TIME_GAP
            for line in section.time_lines:
                draw.text((text_x, text_y), line, fill=self.EXTRA_COLOR, font=self.fontset.extra_font.font)
                text_y += self.fontset.extra_font.line_height

        # 在右侧绘制平台 logo（仅在非转发内容时绘制）
        if not_repost:
            platform_name = result.platform.name
            if platform_name in self.platform_logos:
                logo_img = self.platform_logos[platform_name]
                # 计算 logo 位置（右侧对齐）
                logo_x = image.width - self.PADDING - logo_img.width
                # 垂直居中对齐头像
                logo_y = y_pos + (self.AVATAR_SIZE - logo_img.height) // 2
                image.paste(logo_img, (logo_x, logo_y), logo_img)

        return y_pos + section.height + self.SECTION_SPACING

    def _draw_title(self, draw: ImageDraw.ImageDraw, lines: list[str], y_pos: int, font) -> int:
        """绘制标题"""
        for line in lines:
            draw.text((self.PADDING, y_pos), line, fill=self.TEXT_COLOR, font=font)
            y_pos += self.fontset.title_font.line_height
        return y_pos + self.SECTION_SPACING

    def _draw_cover(self, image: Image.Image, cover_img: Image.Image, y_pos: int, card_width: int) -> int:
        """绘制封面"""
        # 封面从左边padding开始，和文字、头像对齐
        x_pos = self.PADDING
        image.paste(cover_img, (x_pos, y_pos))

        # 添加视频播放按钮（居中）
        button_size = 128  # 固定使用 128x128 尺寸
        button_x = x_pos + (cover_img.width - button_size) // 2
        button_y = y_pos + (cover_img.height - button_size) // 2
        image.paste(self.video_button_image, (button_x, button_y), self.video_button_image)

        return y_pos + cover_img.height + self.SECTION_SPACING

    def _draw_text(self, draw: ImageDraw.ImageDraw, lines: list[str], y_pos: int, font) -> int:
        """绘制文本内容"""
        for line in lines:
            draw.text((self.PADDING, y_pos), line, fill=self.TEXT_COLOR, font=font)
            y_pos += self.fontset.text_font.line_height
        return y_pos + self.SECTION_SPACING

    def _draw_graphics(
        self, image: Image.Image, draw: ImageDraw.ImageDraw, section: GraphicsSectionData, y_pos: int, card_width: int
    ) -> int:
        """绘制图文内容"""
        # 绘制文本内容（如果有）
        if section.text_lines:
            for line in section.text_lines:
                draw.text((self.PADDING, y_pos), line, fill=self.TEXT_COLOR, font=self.fontset.text_font.font)
                y_pos += self.fontset.text_font.line_height
            y_pos += self.SECTION_SPACING  # 文本和图片之间的间距

        # 绘制图片（居中）
        content_width = card_width - 2 * self.PADDING
        x_pos = self.PADDING + (content_width - section.image.width) // 2
        image.paste(section.image, (x_pos, y_pos))
        y_pos += section.image.height

        # 绘制 alt 文本（如果有，居中显示）
        if section.alt_text:
            y_pos += self.SECTION_SPACING  # 图片和alt文本之间的间距
            # 计算文本居中位置
            extra_font_info = self.fontset.extra_font
            text_width = extra_font_info.get_text_width(section.alt_text)
            text_x = self.PADDING + (content_width - text_width) // 2
            draw.text((text_x, y_pos), section.alt_text, fill=self.EXTRA_COLOR, font=extra_font_info.font)
            y_pos += extra_font_info.line_height

        return y_pos + self.SECTION_SPACING

    def _draw_extra(self, draw: ImageDraw.ImageDraw, lines: list[str], y_pos: int, font) -> int:
        """绘制额外信息"""
        for line in lines:
            draw.text((self.PADDING, y_pos), line, fill=self.EXTRA_COLOR, font=font)
            y_pos += self.fontset.extra_font.line_height
        return y_pos

    def _draw_repost(
        self, image: Image.Image, draw: ImageDraw.ImageDraw, section: RepostSectionData, y_pos: int, card_width: int
    ) -> int:
        """绘制转发内容"""
        # 获取缩放后的转发图片
        repost_image = section.scaled_image

        # 转发框占满整个内容区域，左右和边缘对齐
        content_width = card_width - 2 * self.PADDING
        repost_x = self.PADDING
        repost_y = y_pos
        repost_width = content_width  # 转发框宽度等于内容区域宽度
        repost_height = section.height

        # 绘制转发背景（圆角矩形）
        self._draw_rounded_rectangle(
            image,
            (repost_x, repost_y, repost_x + repost_width, repost_y + repost_height),
            self.REPOST_BG_COLOR,
            radius=8,
        )

        # 绘制转发边框
        self._draw_rounded_rectangle_border(
            draw,
            (repost_x, repost_y, repost_x + repost_width, repost_y + repost_height),
            self.REPOST_BORDER_COLOR,
            radius=8,
            width=1,
        )

        # 转发图片在转发容器中居中
        card_x = repost_x + (repost_width - repost_image.width) // 2
        card_y = repost_y + self.REPOST_PADDING

        # 将缩放后的转发图片贴到主画布上
        image.paste(repost_image, (card_x, card_y))

        return y_pos + repost_height + self.SECTION_SPACING

    def _draw_image_grid(self, image: Image.Image, section: ImageGridSectionData, y_pos: int, card_width: int) -> int:
        """绘制图片网格"""
        images = section.images
        cols = section.cols
        rows = section.rows
        has_more = section.has_more
        remaining_count = section.remaining_count

        if not images:
            return y_pos

        # 计算每个图片的尺寸和间距
        available_width = card_width - 2 * self.PADDING  # 可用宽度
        img_spacing = self.IMAGE_GRID_SPACING

        # 根据图片数量计算每个图片的尺寸
        if len(images) == 1:
            # 单张图片，使用完整的可用宽度，与视频封面保持一致
            max_img_size = available_width
        else:
            # 多张图片，统一使用间距计算，确保所有间距相同
            num_gaps = cols + 1  # 2列有3个间距，3列有4个间距
            calculated_size = (available_width - img_spacing * num_gaps) // cols
            max_img_size = self.IMAGE_2_GRID_SIZE if cols == 2 else self.IMAGE_3_GRID_SIZE
            max_img_size = min(calculated_size, max_img_size)

        current_y = y_pos

        for row in range(rows):
            row_start = row * cols
            row_end = min(row_start + cols, len(images))
            row_images = images[row_start:row_end]

            # 计算这一行的最大高度
            max_height = max(img.height for img in row_images)

            # 绘制这一行的图片
            for i, img in enumerate(row_images):
                # 统一使用间距计算方式
                img_x = self.PADDING + img_spacing + i * (max_img_size + img_spacing)

                img_y = current_y + img_spacing  # 每行上方都有间距

                # 居中放置图片
                y_offset = (max_height - img.height) // 2
                image.paste(img, (img_x, img_y + y_offset))

                # 如果是最后一张图片且有更多图片，绘制+N效果
                if has_more and row == rows - 1 and i == len(row_images) - 1 and len(images) == self.MAX_IMAGES_DISPLAY:
                    self._draw_more_indicator(image, img_x, img_y, max_img_size, max_height, remaining_count)

            current_y += img_spacing + max_height

        return current_y + img_spacing + self.SECTION_SPACING

    def _draw_more_indicator(
        self, image: Image.Image, img_x: int, img_y: int, img_width: int, img_height: int, count: int
    ):
        """在图片上绘制+N指示器"""
        draw = ImageDraw.Draw(image)

        # 创建半透明黑色遮罩（透明度 1/4）
        overlay = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle((0, 0, img_width - 1, img_height - 1), fill=(0, 0, 0, 100))

        # 将遮罩贴到图片上
        image.paste(overlay, (img_x, img_y), overlay)

        # 绘制+N文字
        text = f"+{count}"
        font_info = self.fontset.indicator_font
        # 计算文字位置（居中）
        text_width = font_info.get_text_width(text)
        text_x = img_x + (img_width - text_width) // 2
        text_y = img_y + (img_height - font_info.line_height) // 2

        # 绘制50%透明白色文字
        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font_info.font)

    def _draw_rounded_rectangle(
        self, image: Image.Image, bbox: tuple[int, int, int, int], fill_color: tuple[int, int, int], radius: int = 8
    ):
        """绘制圆角矩形"""
        x1, y1, x2, y2 = bbox
        draw = ImageDraw.Draw(image)

        # 绘制主体矩形
        draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill_color)
        draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill_color)

        # 绘制四个圆角
        draw.pieslice((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=fill_color)
        draw.pieslice((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=fill_color)
        draw.pieslice((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=fill_color)
        draw.pieslice((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=fill_color)

    def _draw_rounded_rectangle_border(
        self,
        draw: ImageDraw.ImageDraw,
        bbox: tuple[int, int, int, int],
        border_color: tuple[int, int, int],
        radius: int = 8,
        width: int = 1,
    ):
        """绘制圆角矩形边框"""
        x1, y1, x2, y2 = bbox

        # 绘制主体边框
        draw.rectangle((x1 + radius, y1, x2 - radius, y1 + width), fill=border_color)  # 上
        draw.rectangle((x1 + radius, y2 - width, x2 - radius, y2), fill=border_color)  # 下
        draw.rectangle((x1, y1 + radius, x1 + width, y2 - radius), fill=border_color)  # 左
        draw.rectangle((x2 - width, y1 + radius, x2, y2 - radius), fill=border_color)  # 右

        # 绘制四个圆角边框
        draw.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=border_color, width=width)
        draw.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=border_color, width=width)
        draw.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=border_color, width=width)
        draw.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=border_color, width=width)

    def _wrap_text(self, text: str, max_width: int, font_info: FontInfo) -> list[str]:
        """优化的文本自动换行算法，考虑中英文字符宽度相同

        Args:
            text: 要处理的文本
            max_width: 最大宽度（像素）
            font_info: 字体信息对象

        Returns:
            换行后的文本列表
        """
        if not text:
            return [""]

        lines = []
        paragraphs = text.split("\n")

        def is_punctuation(char: str) -> bool:
            """判断是否为不能为行首的标点符号"""
            # 中文标点符号
            chinese_punctuation = "，。！？；：、）】》〉」』〕〗〙〛…—·"
            # 英文标点符号
            english_punctuation = ",.;:!?)]}"

            return char in chinese_punctuation or char in english_punctuation

        for paragraph in paragraphs:
            if not paragraph:
                lines.append("")
                continue

            current_line = ""
            current_line_width = 0
            remaining_text = paragraph

            while remaining_text:
                next_char = remaining_text[0]
                char_width = font_info.get_char_width_fast(next_char)

                # 如果当前行为空，直接添加字符
                if not current_line:
                    current_line = next_char
                    current_line_width = char_width
                    remaining_text = remaining_text[1:]
                    continue

                # 如果是标点符号，直接添加到当前行（标点符号不应该单独成行）
                if is_punctuation(next_char):
                    current_line += next_char
                    current_line_width += char_width
                    remaining_text = remaining_text[1:]
                    continue

                # 测试添加下一个字符后的宽度
                test_width = current_line_width + char_width

                if test_width <= max_width:
                    # 宽度合适，继续添加
                    current_line += next_char
                    current_line_width = test_width
                    remaining_text = remaining_text[1:]
                else:
                    # 宽度超限，需要断行
                    lines.append(current_line)
                    current_line = next_char
                    current_line_width = char_width
                    remaining_text = remaining_text[1:]

            # 保存最后一行
            if current_line:
                lines.append(current_line)

        return lines if lines else [""]
