
from collections import defaultdict
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
    LinkBuilder,
    PageBreakBuilder,
    SpacerBuilder,
    StepFieldBoldBuilder,
    TextBuilder,
)


class EmptyLastResultBuilder(BaseLastResultBuilder):
    @classmethod
    def build(cls, test) -> List[Flowable]:
        elements = cls.make_result_title()
        elements.append(SpacerBuilder.build(1, 30))
        return elements


class StepWithOutResultBuilder(BaseStepBuilder):
    @classmethod
    def make_result(cls, step_result: TestStepResult) -> List[Flowable]:
        return [
            StepFieldBoldBuilder.build('Результат'),
            SpacerBuilder.build(1, 20),
        ]


class TestPlanSectionBuilder(BaseTestSectionBuilder):
    _step_builder = StepWithOutResultBuilder
    _last_result_builder = EmptyLastResultBuilder

    @staticmethod
    def calc_case_version(test) -> int:
        return getattr(test, 'version', 1)

    @classmethod
    def get_test_case(cls, test) -> TestCase:
        return test.case

    @classmethod
    def get_steps(cls, test) -> list[TestCaseStep]:
       return test.case.steps.all()


class TestPlanPDFReport(BasePDFReport):
    _test_section_builder = TestPlanSectionBuilder
    _table_of_content_headers = ['Case ID', 'Version', 'Test Name']
    _table_of_content_col_size = [1.0, 1.0, 5.0]

    @staticmethod
    def _group_tests(tests):
        grouped = defaultdict(list)
        for test in tests:
            grouped[test.case.suite.name].append(test)
        return dict(grouped)

    @staticmethod
    def _table_of_content_rows(tests):
        return [
            [
                TextBuilder.build(str(test.case.id)),
                TextBuilder.build(str(getattr(test, 'version', 1))),
                LinkBuilder.build(str(test.case.id), test.case.name),
            ] for test in tests
        ]

    @classmethod
    def _build_story(cls, node, tests, **kwargs):
        elements = []
        grouped_tests = cls._group_tests(tests)

        elements.extend(cls._add_title_page('Отчет о плане тестирования', node.name, ' '))
        elements.extend(cls._add_plan_info(node))
        elements.append(PageBreakBuilder.build())
        elements.extend(cls._add_table_of_contents(grouped_tests))
        elements.extend(cls._add_tests(grouped_tests))

        return elements




def generate_report_pdf(node, tests, attachment_map):
    return TestPlanPDFReport.generate_report(node, tests, attachment_map)
