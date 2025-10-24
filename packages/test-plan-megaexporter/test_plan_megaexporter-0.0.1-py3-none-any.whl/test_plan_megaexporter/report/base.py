
from abc import ABC, abstractmethod
from io import BytesIO
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    PageTemplate,
)
from testy.tests_description.models import TestCase, TestCaseStep
from testy.tests_representation.models import TestStepResult
from testy.utilities.time import WorkTimeProcessor

from test_plan_megaexporter.report.builders.base_builders import (
    BoldTextBuilder,
    BookmarkBuilder,
    PageBreakBuilder,
    PageHeaderBuilder,
    PDFElementBuilder,
    SectionHeaderBuilder,
    SpacerBuilder,
    StepFieldListBuilder,
    StepTitleBuilder,
    TextBuilder,
)
from test_plan_megaexporter.report.builders.complex_builders import (
    AttachmentsBuilder,
    AttributesBuilder,
    CommentBlockBuilder,
    PlanInfoBuilder,
    TextFieldPairBuilder,
    TitlePageBuilder,
    StepTextFieldPairBuilder,
)
from test_plan_megaexporter.report.builders.table import TableOfContentBuilder
from test_plan_megaexporter.report.common import (
    FontManager,
    FooterCanvas,
)
from test_plan_megaexporter.report.builders.utils import FILE_LINK_REGISTRY



class BaseLastResultBuilder(PDFElementBuilder):

    @staticmethod
    def make_result_title() -> List[Flowable]:
        return [
            BoldTextBuilder.build('Последний результат выполнения:'),
        ]

    @classmethod
    @abstractmethod
    def build(cls, test) -> List[Flowable]:
        ...

class BaseStepBuilder(PDFElementBuilder):
    @classmethod
    @abstractmethod
    def make_result(cls, step_result: TestStepResult) -> List[Flowable]:
        ...



    @classmethod
    def build(cls, step: TestCaseStep) -> list[Flowable]:
        step_scenario = step.scenario
        step_expected = step.expected

        step_elements = [StepFieldListBuilder.build(step.name)]
        step_elements.extend(StepTextFieldPairBuilder.build('Процедура', step_scenario, is_md_format=True))
        step_elements.extend(StepTextFieldPairBuilder.build('Ожидаемый результат', step_expected, is_md_format=True))

        step_elements.extend(cls.make_result(getattr(step, 'version_result', None)))
        step_elements.extend(AttachmentsBuilder.build(step.attachments.all()))

        return step_elements


class BaseTestSectionBuilder(PDFElementBuilder):
    _step_builder: BaseStepBuilder
    _last_result_builder: BaseLastResultBuilder

    @classmethod
    def get_steps(cls, test) -> list[TestCaseStep]:
        ...

    @classmethod
    def make_test_case_fields(cls, test, case) -> List[Flowable]:
        estimate = WorkTimeProcessor.format_duration(case.estimate) if case.estimate else None
        elements = []
        elements.extend(TextFieldPairBuilder.build('Описание', case.description, is_md_format=True))
        elements.extend(TextFieldPairBuilder.build('Предусловия', case.setup, is_md_format=True))

        if case.is_steps:
            steps = cls.get_steps(test)
            elements.extend(cls.make_steps(steps))
        else:
            elements.extend(TextFieldPairBuilder.build('Процедура', case.scenario, is_md_format=True))

        elements.extend(TextFieldPairBuilder.build('Постусловия', case.teardown, is_md_format=True))

        if not case.is_steps:
            elements.extend(TextFieldPairBuilder.build('Ожидаемый результат', case.expected, is_md_format=True))

        elements.extend(TextFieldPairBuilder.build('Оценка времени', estimate))

        elements.extend(cls.make_attributes(case.attributes))

        elements.extend(AttachmentsBuilder.build(case.attachments.all()))

        last_comment = getattr(test, 'last_comment', None)
        if last_comment and (last_comment.content or len(last_comment.attachments.all()) > 0):
            elements.extend(CommentBlockBuilder.build(
                last_comment.content,
                last_comment.attachments.all(),
                'Комментарий к тесту'
            ))
        return elements


    @classmethod
    def get_test_case(cls, test) -> TestCase:
        ...

    @classmethod
    def build(cls, test) -> List[Flowable]:
        test_case = cls.get_test_case(test)

        elements = []
        elements.extend(cls.make_header(test))
        elements.extend(cls.make_test_case_fields(test, test_case))
        elements.extend(cls._last_result_builder.build(test))
        elements.append(PageBreakBuilder.build())
        return elements


    @classmethod
    def make_header(cls, test):
        return [
            BookmarkBuilder.build(f'test_{test.case.id}'),
            PageHeaderBuilder.build(test.case.name),
            TextBuilder.build(f'Test ID: {test.case.id}, Version: {cls.calc_case_version(test)}'),
            SpacerBuilder.build(1, 15),
        ]

    @staticmethod
    def make_attributes(attributes):
        elements = []
        if attributes:
            elements.append(BoldTextBuilder.build('Атрибуты:'))
            elements.extend(AttributesBuilder.build(attributes))
            elements.append(SpacerBuilder.build(1, 5))
        return elements

    @classmethod
    def make_steps(cls, steps: list[TestCaseStep]):
        elements = []
        if len(steps):
            elements.append(StepTitleBuilder.build('Шаги выполнения:'))
            for step in steps:
                elements.extend(cls._step_builder.build(step))
        return elements



class BasePDFReport(ABC):
    _test_section_builder: BaseTestSectionBuilder
    _table_of_content_headers: List['str']
    _table_of_content_col_size: List[float]
    _footer_canvas = FooterCanvas()

    FontManager.setup_fonts()

    @staticmethod
    def _add_title_page(report_name, plan_name, description):
        return TitlePageBuilder.build(report_name, plan_name, description)

    @staticmethod
    def _add_plan_info(node):
        return PlanInfoBuilder.build(node)

    @classmethod
    def _add_tests(cls, grouped_tests):
        elements = []

        for section_name, tests in grouped_tests.items():
            elements.append(SectionHeaderBuilder.build(section_name))
            elements.append(SpacerBuilder.build(1, 10))

            for test in tests:
                elements.extend(cls._create_test_section(test))

        return elements

    @staticmethod
    @abstractmethod
    def _group_tests(tests):
        ...

    @staticmethod
    @abstractmethod
    def _table_of_content_rows(tests):
        ...

    @abstractmethod
    def _build_story(self, node, tests, **kwargs):
        ...

    @classmethod
    def _add_table_of_contents(cls, grouped_tests):
        elements = [SectionHeaderBuilder.build('Оглавление')]

        for group_name, tests in grouped_tests.items():
            elements.append(SectionHeaderBuilder.build(group_name))
            elements.extend([
                TableOfContentBuilder.build(
                    headers=cls._table_of_content_headers,
                    data_rows=cls._table_of_content_rows(tests),
                    col_widths=cls._table_of_content_col_size,
                ),
                SpacerBuilder.build(1, 20),
            ])

        elements.append(PageBreakBuilder.build())
        return elements

    @classmethod
    def _create_test_section(cls, test):
        return cls._test_section_builder.build(test)

    @classmethod
    def generate_report(cls, node, tests, attachment_map, **kwargs):
        buffer = BytesIO()
        doc = cls._create_document(buffer)
        story = cls._build_story(node, tests, **kwargs)
        for linkfile in FILE_LINK_REGISTRY:
            linkfile.make_real_path(attachment_map)
        doc.build(story)
        buffer.seek(0)
        return buffer

    @classmethod
    def _create_document(cls, buffer):
        margins = {'rightMargin': 40, 'leftMargin': 40, 'topMargin': 40, 'bottomMargin': 20}
        doc = BaseDocTemplate(buffer, pagesize=A4, **margins)

        frame = Frame(
            doc.leftMargin,
            doc.topMargin,
            doc.width,
            doc.height,
            topPadding=10,
            id='normal',
        )
        template = PageTemplate(
            id='with_footer',
            frames=[frame],
            onPage=cls._footer_canvas.draw_footer
        )
        doc.addPageTemplates([template])
        return doc
