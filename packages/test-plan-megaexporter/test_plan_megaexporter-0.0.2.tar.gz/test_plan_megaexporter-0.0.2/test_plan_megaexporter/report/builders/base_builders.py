
import os
from abc import ABC
from typing import List

from django.contrib.staticfiles import finders
from reportlab.lib import colors, units
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Flowable,
    Image,
    PageBreak,
    Paragraph,
    Spacer,
)

from test_plan_megaexporter.report.builders.utils import escape
from test_plan_megaexporter.report.common import BookmarkFlowable, FontManager


class PDFElementBuilder(ABC):

    @classmethod
    def build(cls, *args, **kwargs) -> Flowable | List[Flowable]:
        raise NotImplementedError()


class BaseContentBuilder(PDFElementBuilder):
    _css_styles: dict = {}
    style: ParagraphStyle

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.style = ParagraphStyle(name=cls.__qualname__, **cls._css_styles)


class TextBuilder(BaseContentBuilder):
    _css_styles = {
        'leftIndent': 0,
        'fontSize': 10,
        'leading': 12,
        'fontName': FontManager.regular,
    }

    @classmethod
    def build(cls, text: str, need_escape: bool = True) -> Flowable:
        if text and need_escape:
            text = escape(text)
        text = text or f'<font color={colors.lightgrey}>Не указано</font>'
        return Paragraph(text, cls.style)


class BoldTextBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 10,
        'leading': 12,
        'spaceAfter': 4,
        'spaceBefore': 12,
        'leftIndent': 0,
        'fontName': FontManager.bold,
    }


class LinkBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 10,
        'leading': 12,
        'fontName': FontManager.regular,
        'textColor': 'darkBlue',
    }
    @classmethod
    def build(cls, url: str, text: str) -> Flowable:
        text = escape(text)
        link = f'<a href="#test_{url}">{text}</a>'
        return Paragraph(link, cls.style)

class StepTitleBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 10,
        'leading': 12,
        'spaceBefore': 12,
        'spaceAfter': 4,
        'leftIndent': 0,
        'fontName': FontManager.bold,
    }


class StepFieldListBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 9,
        'leading': 12,
        'spaceBefore': 12,
        'spaceAfter': 4,
        'leftIndent': 3,
        'fontName': FontManager.bold,
    }
    bullet = '<font name="Helvetica" size=6>▪</font>'

    @classmethod
    def build(cls, text: str) -> Flowable:
        return Paragraph(f'{cls.bullet} {escape(text)}', cls.style)


class StepFieldBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 9,
        'leading': 12,
        'spaceAfter': 4,
        'leftIndent': 10,
        'fontName': FontManager.regular,
    }


class StepFieldBoldBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 9,
        'leading': 12,
        'spaceAfter': 4,
        'leftIndent': 10,
        'fontName': FontManager.bold,
    }


class TitlePageHeaderBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 24,
        'spaceAfter': 30,
        'spaceBefore': 100,
        'fontName': FontManager.bold,
        'textColor': colors.darkblue,
    }


class TitlePageSubtitleBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 14,
        'spaceAfter': 20,
        'fontName': FontManager.regular,
        'textColor': colors.black,
    }


class SectionHeaderBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 14,
        'spaceAfter': 12,
        'spaceBefore': 20,
        'fontName': FontManager.bold,
        'textColor': colors.darkblue,
        'leftIndent': 0,
    }


class PageHeaderBuilder(TextBuilder):
    _css_styles = {
        'fontSize': 12,
        'spaceAfter': 8,
        'spaceBefore': 12,
        'fontName': FontManager.bold,
        'leftIndent': 0,
    }


class CodeBlockBuilder(BaseContentBuilder):
    _css_styles = {
        'splitLongWords': '1',
        'wordWrap': 'LTR',
        'backColor': colors.lightgrey,
        'textColor': colors.black,
        'fontSize': 10,
        'leading': 12,
        'borderColor': colors.black,
        'borderPadding': 2,
        'leftIndent': 4,
        'spaceBefore': 8,
        'spaceAfter': 12,
        'fontName': FontManager.regular,
    }

    @classmethod
    def build(cls, text: str) -> Flowable:
        return Paragraph(text, cls.style)



class SpacerBuilder(PDFElementBuilder):
    @classmethod
    def build(cls, width: int = 1, height: int = 50) -> Flowable:
        return Spacer(width, height)


class PageBreakBuilder(PDFElementBuilder):
    @classmethod
    def build(cls) -> Flowable:
        return PageBreak()


class FilenameTextBuilder(TextBuilder):
    _css_styles = {
        'leftIndent': 0,
        'fontSize': 8,
        'leading': 12,
        'textColor': colors.gray,
        'fontName': FontManager.regular,
    }

class ImageBuilder(PDFElementBuilder):
    max_width: int = 140 * units.mm
    max_height: int = 180 * units.mm

    @staticmethod
    def prepare_full_path(path):
        if not path:
            return None

        if os.path.exists(path):
            return path

        if path.startswith(('http://', 'https://')):
            return path

        try:
            path = finders.find(path)
        except Exception:
            return None

        if path and os.path.exists(path):
            return path

        return None



    @classmethod
    def build(
            cls, path: str,
            filename: str = None,
            width: int = None,
            height: int = None,
            align: str = 'LEFT',
    ) -> list[Flowable]:

        elements = []
        full_path = cls.prepare_full_path(path)

        kwargs = {}
        if width:
            kwargs['width'] = width
        if height:
            kwargs['height'] = height
        if align:
            kwargs['hAlign'] = align
        try:
            img = Image(full_path, **kwargs)
            if not width and hasattr(img, 'imageWidth') and img.imageWidth > cls.max_width:
                img.drawWidth = cls.max_width
                img.drawHeight = img.imageHeight * (cls.max_width / img.imageWidth)

            elements.append(img)
        except Exception:
            pass
        elements.append(FilenameTextBuilder.build(f'File: {filename or path}'))
        elements.append(SpacerBuilder.build(1, 5))

        return elements



class LogoBuilder(ImageBuilder):
    _logo_path: str = 'test_plan_megaexporter/img/logo.png'

    @classmethod
    def build(cls) -> Flowable:
        return super().build(cls._logo_path, filename='logo.png', width=120, height=88)[0]


class BookmarkBuilder(PDFElementBuilder):
    @classmethod
    def build(cls, key: str) -> Flowable:
        return BookmarkFlowable(key)
