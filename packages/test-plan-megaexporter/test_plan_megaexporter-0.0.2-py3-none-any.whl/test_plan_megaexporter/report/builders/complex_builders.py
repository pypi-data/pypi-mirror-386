
import json
from typing import List

from django.utils import timezone
from reportlab.platypus import Flowable
from testy.core.models import Attachment
from testy.tests_representation.models import TestPlan

from test_plan_megaexporter.report.builders.base_builders import (
    BoldTextBuilder,
    ImageBuilder,
    LogoBuilder,
    PageBreakBuilder,
    PDFElementBuilder,
    SectionHeaderBuilder,
    SpacerBuilder,
    TextBuilder,
    TitlePageHeaderBuilder,
    TitlePageSubtitleBuilder,
    StepFieldBuilder,
    StepFieldBoldBuilder,
)
from test_plan_megaexporter.report.builders.markdown import MarkdownConverter


class MarkDownTextBuilder(PDFElementBuilder):
    @classmethod
    def build(cls, text: str, text_builder_class=TextBuilder, **builder_params) -> list[Flowable]:
        con = MarkdownConverter(text_builder_class=text_builder_class, **builder_params)
        elems = con.convert(str(text))
        if elems:
            return elems
        else:
            return [text_builder_class.build(text)]


class TextFieldPairBuilder(PDFElementBuilder):

    @classmethod
    def build(cls, label: str, value: str, is_md_format: bool = False) -> List[Flowable]:
        elements = [BoldTextBuilder.build(label)]
        if is_md_format:
            elements.extend(MarkDownTextBuilder.build(value))
        else:
            elements.append(TextBuilder.build(value))

        return elements


class StepTextFieldPairBuilder(PDFElementBuilder):

    @classmethod
    def build(cls, label: str, value: str, is_md_format: bool = False) -> List[Flowable]:
        elements = [StepFieldBoldBuilder.build(label)]
        if is_md_format:
            elements.extend(MarkDownTextBuilder.build(value, text_builder_class=StepFieldBuilder))
        else:
            elements.append(StepFieldBuilder.build(value))

        return elements


class AttachmentsBuilder(PDFElementBuilder):

    @classmethod
    def build(cls, attachments: list[Attachment]) -> List[Flowable]:
        elements = []
        for attachment in attachments:
            elements.extend(ImageBuilder.build(attachment.file.path, filename=attachment.filename))
        if elements:
            return [
                BoldTextBuilder.build('Вложения:'),
                *elements,
                SpacerBuilder.build(1, 5)
            ]
        return []


class CommentBlockBuilder(PDFElementBuilder):
    @classmethod
    def build(cls, text, attachments: list[Attachment], block_name: str = 'Комментарий') -> List[Flowable]:

        elements = []
        for attachment in attachments:
            elements.extend(ImageBuilder.build(attachment.file.path, filename=attachment.filename))

        if text or elements:
            return [
                *TextFieldPairBuilder.build(block_name, text, is_md_format=True),
                *elements,
                SpacerBuilder.build(1, 5)
            ]
        return []


class TitlePageBuilder(PDFElementBuilder):

    @classmethod
    def build(cls, report_name: str, plan_name: str, description: str) -> List[Flowable]:
        date_text = f'Дата формирования: {timezone.now().strftime("%d.%m.%Y")}'
        return [
            LogoBuilder.build(),
            SpacerBuilder.build(1, 50),
            TitlePageHeaderBuilder.build(report_name),
            TitlePageSubtitleBuilder.build(plan_name),
            SpacerBuilder.build(1, 10),
            TextBuilder.build(description),
            SpacerBuilder.build(1, 20),
            TextBuilder.build(date_text),
            PageBreakBuilder.build(),
        ]


class PlanInfoBuilder(PDFElementBuilder):

    @classmethod
    def build(cls, node: TestPlan) -> List[Flowable]:
        elements = [SectionHeaderBuilder.build('Информация о плане')]
        elements.extend(TextFieldPairBuilder.build('ID плана', str(node.id)))

        start_date = node.started_at.strftime('%d.%m.%Y') if node.started_at else ''
        finish_date = node.due_date.strftime('%d.%m.%Y') if node.due_date else ''
        elements.extend(TextFieldPairBuilder.build('Дата начала', start_date))
        elements.extend(TextFieldPairBuilder.build('Дата завершения', finish_date))

        elements.extend(TextFieldPairBuilder.build('Описание', node.description, is_md_format=True))
        attachments = node.attachments.all()
        elements.extend(AttachmentsBuilder.build(attachments))

        elements.append(SpacerBuilder.build(1, 20))
        return elements


class AttributesBuilder(PDFElementBuilder):
    _key_width = 70

    @classmethod
    def build(cls, attributes: dict) -> list[Flowable]:
        data = []
        for key, value in attributes.items():
            data.extend(
                    TextFieldPairBuilder.build(
                        key.ljust(cls._key_width),
                        json.dumps(value, indent=4, ensure_ascii=False) if isinstance(value, (dict, list)) else value,
                        is_md_format=True,
                    )
            )

        return data
