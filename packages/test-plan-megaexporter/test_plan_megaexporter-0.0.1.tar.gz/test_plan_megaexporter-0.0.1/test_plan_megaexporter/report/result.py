
from collections import Counter, defaultdict
from typing import List

from reportlab.platypus import Flowable
from testy.tests_description.models import TestCase, TestCaseStep
from testy.tests_representation.models import TestStepResult

from test_plan_megaexporter.report.base import (
    BaseLastResultBuilder,
    BasePDFReport,
    BaseStepBuilder,
    BaseTestSectionBuilder,
)
from test_plan_megaexporter.report.builders.base_builders import (
    BoldTextBuilder,
    LinkBuilder,
    PageBreakBuilder,
    SectionHeaderBuilder,
    SpacerBuilder,
    StepFieldBoldBuilder,
    StepFieldBuilder,
    TextBuilder,
)
from test_plan_megaexporter.report.builders.complex_builders import (
    AttachmentsBuilder,
    AttributesBuilder,
    TextFieldPairBuilder,
    CommentBlockBuilder,
)
from test_plan_megaexporter.report.builders.table import TableOfContentBuilder

NOT_COMPLETED_YET = 'Не выполнено'


class LastResultBuilder(BaseLastResultBuilder):
    @staticmethod
    def make_attributes(attributes):
        elements = []
        if attributes:
            elements.append(BoldTextBuilder.build('Атрибуты результата:'))
            elements.extend(AttributesBuilder.build(attributes))
            elements.append(SpacerBuilder.build(1, 5))
        return elements

    @classmethod
    def build(cls, test) -> List[Flowable]:
        elements = cls.make_result_title()

        if test.last_result:
            status = test.last_result.status.name
            last_result_comment = test.last_result.comment
            attributes = test.last_result.attributes
            last_result_attachments = test.last_result.attachments.all()


        else:
            status = NOT_COMPLETED_YET
            last_result_comment = None
            attributes = []
            last_result_attachments = []


        elements.append(TextBuilder.build(status))
        elements.extend(cls.make_attributes(attributes))
        elements.extend(AttachmentsBuilder.build(last_result_attachments))

        if last_result_comment:
            elements.extend(
                CommentBlockBuilder.build(last_result_comment,[], 'Комментарий к результату'),
            )


        return elements


class StepWithResultBuilder(BaseStepBuilder):
    @classmethod
    def make_result(cls, step_result: TestStepResult | None) -> List[Flowable]:
        step_result_status = step_result.status.name if step_result else NOT_COMPLETED_YET
        return [
            StepFieldBoldBuilder.build('Статус'),
            StepFieldBuilder.build(step_result_status),
        ]


class TestResultSectionBuilder(BaseTestSectionBuilder):
    _step_builder = StepWithResultBuilder
    _last_result_builder = LastResultBuilder

    @staticmethod
    def calc_case_version(test) -> int:
        return getattr(test.case, 'version', 1)


    @classmethod
    def get_test_case(cls, test) -> TestCase:
        return test.case

    @classmethod
    def get_steps(cls, test) -> list[TestCaseStep]:
        return test.case.steps.all()


class TestResultPDFReport(BasePDFReport):
    _test_section_builder = TestResultSectionBuilder
    _table_of_content_headers = ['Case ID', 'Version', 'Test Name', 'Status']
    _table_of_content_col_size = [1, 1, 4, 1.0]

    @staticmethod
    def _add_conclusion(conclusion):
        elements = TextFieldPairBuilder.build('Заключение', conclusion, is_md_format=True)
        elements.append(SpacerBuilder.build(1, 20))
        return elements

    @staticmethod
    def _add_status_summary(tests):
        elements = [SectionHeaderBuilder.build('Сводная информация по статусам тестов')]

        status_counts = Counter()
        for test in tests:
            if test.last_status:
                status_counts[test.last_status.name] += 1
            else:
                status_counts[NOT_COMPLETED_YET] += 1

        elements.extend([
            TableOfContentBuilder.build(
                headers=[
                    'Статус',
                    'Количество'
                ],
                data_rows=[
                    [
                        BoldTextBuilder.build(status),
                        TextBuilder.build(str(count)),
                    ] for status, count in status_counts.items()
                ],
                col_widths=[4.0, 3],
            ),
            SpacerBuilder.build(1, 20),
        ])
        return elements

    @staticmethod
    def _add_defects_appendix(defects):
        elements = []

        elements.extend([
            TableOfContentBuilder.build(
                headers=['JIRA Key', 'Plan ID', 'Plan Name', 'Test Name', 'Result Status'],
                data_rows=[
                    [
                        TextBuilder.build(defect.jira_key),
                        TextBuilder.build(str(defect.test.plan_id)),
                        TextBuilder.build(defect.test.plan.name),
                        TextBuilder.build(defect.test.case.name),
                        TextBuilder.build(defect.status.name),
                    ] for defect in defects
                ],
                col_widths=[0.7, 0.8, 2.0, 2.5, 1.0],
            ),
            SpacerBuilder.build(1, 20),
        ])
        return elements

    @staticmethod
    def _group_tests(tests):
        grouped = defaultdict(list)
        for test in tests:
            grouped[test.plan.name].append(test)
        return grouped

    @staticmethod
    def _table_of_content_rows(tests):
        elements = []

        for test in tests:
            version = getattr(test.case, 'version', 1)
            elements.append([
                TextBuilder.build(str(test.case.id)),
                TextBuilder.build(str(version)),
                LinkBuilder.build(str(test.case.id), test.case.name),
                TextBuilder.build(getattr(test.last_status, 'name', NOT_COMPLETED_YET)),
            ])
        return elements


    @classmethod
    def _build_story(cls, node, tests, defects, conclusion=''):
        elements = []
        grouped_tests = cls._group_tests(tests)

        elements.extend(cls._add_title_page('Отчет о результатах тестирования', node.name, ' '))
        elements.extend(cls._add_plan_info(node))
        elements.extend(cls._add_conclusion(conclusion))
        elements.extend(cls._add_status_summary(tests))
        elements.append(PageBreakBuilder.build())
        elements.extend(cls._add_table_of_contents(grouped_tests))
        elements.extend([
            SectionHeaderBuilder.build('Приложение 1: Подробная информация о тестах'),
            SpacerBuilder.build(1, 10),
        ])
        elements.extend(cls._add_tests(grouped_tests))

        elements.extend([
            SectionHeaderBuilder.build('Приложение 2: Найденные дефекты'),
            SpacerBuilder.build(1, 10),
        ])
        elements.extend(cls._add_defects_appendix(defects))

        return elements



def generate_report_pdf(node, tests, attachment_map, defects, conclusion=''):
    return TestResultPDFReport.generate_report(
        node,
        tests,
        attachment_map,
        defects=defects,
        conclusion=conclusion,
    )