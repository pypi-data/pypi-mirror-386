
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Window, F, Q
from django.db.models.functions import RowNumber

from testy.comments.models import Comment
from testy.core.models import Attachment
from testy.tests_description.models import TestCase
from testy.tests_representation.models import TestPlan, Test, TestResult, TestStepResult
from django.db.models import Count, OuterRef, Subquery

def map_attachments(attachments: list[Attachment]) -> dict[int, Attachment]:
    return {attachment.id: attachment for attachment in attachments}


class TestPlanSelector:


    @staticmethod
    def get_test_plan_tests(node: TestPlan, selected_test_ids: list[int]):
        tests_qs = (
            Test.objects.filter(plan__path__descendant=node.path, id__in=selected_test_ids)
            .select_related('case', 'case__suite', 'plan')
            .prefetch_related(
                'comments',
                'plan__attachments',
                'plan__comments',
                'plan__comments__attachments',
                'case__comments',
                'case__comments__attachments',
                'case__steps',
                'case__steps__attachments',
                'case__attachments',
            )
            .annotate(
                version=Subquery(
                    TestCase.history.filter(
                        id=OuterRef('case__id')
                    ).values('id').annotate(
                        count=Count('history_id')
                    ).values('count')[:1]
                )
            )
            .order_by('case__suite__name')
        )
        for test in tests_qs:
            comments = test.case.comments.all()
            last_comment = comments[0] if comments else None
            test.case.last_comment = last_comment

        attachments = []

        for test in tests_qs:
            attachments.extend(test.plan.attachments.all())
            attachments.extend(test.case.attachments.all())

            for plan_comment in test.plan.comments.all():
                attachments.extend(plan_comment.attachments.all())

            for case_comment in test.case.comments.all():
                attachments.extend(case_comment.attachments.all())

            for step in test.case.steps.all():
                attachments.extend(step.attachments.all())



        return tests_qs, attachments



class TestResultsSelector:

    @staticmethod
    def get_versions_info(case_ids: list[int], case_history_ids: list[int]) -> dict[int, dict[str, int]] | None:
        case_ids_str = ','.join([str(case_id) for case_id in case_ids])
        case_history_ids_str = ','.join([str(history_id) for history_id in case_history_ids])
        with connection.cursor() as cursor:
            cursor.execute(f"""
                  with version_query as (
                      SELECT
                          id,
                          history_id,
                          ROW_NUMBER() OVER (PARTITION BY id ORDER BY history_id ASC) as version
                      FROM tests_description_historicaltestcase
                      WHERE id IN ({case_ids_str})
                  )
                  select id, version
                  from version_query
                  where history_id in ({case_history_ids_str})
            """)

            return {row[0]: row[1] for row in cursor.fetchall()}

    @staticmethod
    def set_prefetch_cache(obj, key, data):
        prefetched_objects_cache = getattr(obj, '_prefetched_objects_cache', {})
        prefetched_objects_cache[key] = data
        setattr(obj, '_prefetched_objects_cache', prefetched_objects_cache)


    @classmethod
    def get_testplan_tests(cls, node: TestPlan):
        tests_qs = (
            Test.objects
            .filter(plan__path__descendant=node.path, is_archive=False)
            .select_related('case', 'plan', 'case__suite', 'last_status')
            .prefetch_related('case__steps','case__steps__result','case__steps__result__status',)
        )

        test_ids = []
        plan_ids = []
        case_ids = []
        result_ids = []
        step_ids = []
        comment_ids = []

        case_history_ids = []
        tests_map = {}

        for test in tests_qs:
            test_ids.append(test.id)
            case_ids.append(test.case.id)
            plan_ids.append(test.plan_id)
            test.last_result = None

            tests_map[test.id] = test


        results_qs = (
            TestResult.objects
            .filter(test_id__in=test_ids)
            .select_related('status', 'test')
            .prefetch_related('steps_results', 'steps_results__step', 'steps_results__status')
            .annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F('test_id')],
                    order_by=F('id').desc()
                )
            )
            .filter(row_number=1)
        )

        steps_version_maps = {}
        for result in results_qs:
            tests_map[result.test_id].last_result = result
            case_history_ids.append(result.test_case_version)
            result_ids.append(result.id)

            step_results = []
            for step_result in result.steps_results.all():
                step_result.step.version_result = step_result
                step_results.append(step_result.step)

            if step_results:
                steps_version_maps[result.test.case_id] = step_results



        history_qs = TestCase.history.model.objects.filter(history_id__in=case_history_ids)
        case_history_map = {case_history.id: case_history.history_object for case_history in history_qs}
        case_version_map = cls.get_versions_info(case_ids, case_history_ids) if case_history_ids else {}

        steps_map = {test.case.id: list(test.case.steps.all()) for test in tests_qs}
        steps_map.update(steps_version_maps)

        step_ids = [step.id for step in sum(steps_map.values(), [])]


        test_content_type = ContentType.objects.get_for_model(Test)
        plan_content_type = ContentType.objects.get_for_model(TestPlan)
        case_content_type = ContentType.objects.get_for_model(TestCase)
        result_content_type = ContentType.objects.get_for_model(TestResult)
        step_content_type = ContentType.objects.get_for_model(TestStepResult)
        comment_content_type = ContentType.objects.get_for_model(Comment)

        comments_qs = (
            Comment.objects
            .filter(
                Q(content_type_id=test_content_type.id, object_id__in=test_ids) |
                # Q(content_type_id=case_content_type.id, object_id__in=case_ids) |
                Q(content_type_id=result_content_type.id, object_id__in=result_ids)
            )
            .annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F('content_type_id'), F('object_id')],
                    order_by=F('created_at').desc()
                )
            )
            .filter(row_number=1)
            .select_related('content_type')
        )

        comment_map = {}
        for comment in comments_qs:
            comment_ids.append(comment.id)
            comment_map[(comment.content_type.model.lower(), comment.object_id)] = comment

        attachments_qs = Attachment.objects.select_related('content_type').filter(
            Q(content_type_id=test_content_type.id, object_id__in=test_ids) |
            Q(content_type_id=case_content_type.id, object_id__in=case_ids) |
            Q(content_type_id=plan_content_type.id, object_id__in=plan_ids) |
            Q(content_type_id=result_content_type.id, object_id__in=result_ids) |
            Q(content_type_id=step_content_type.id, object_id__in=step_ids) |
            Q(content_type_id=comment_content_type.id, object_id__in=comment_ids)
        )

        attachments_map = defaultdict(list)
        for attachment in attachments_qs:
            attachments_map[(attachment.content_type.model.lower(), attachment.object_id)].append(attachment)


        for test in tests_qs:
            test.last_comment = comment_map.get((test_content_type.model.lower(), test.id))
            if test.last_comment:
                cls.set_prefetch_cache(
                    test.last_comment,
                    'attachments',
                    attachments_map.get((comment_content_type.model.lower(), test.last_comment.id), []),
                )

            case_prefetched_objects_cache = test.case._prefetched_objects_cache
            test.case = case_history_map.get(test.case_id, test.case)
            test.case._prefetched_objects_cache = case_prefetched_objects_cache

            test.case.version = case_version_map.get(test.case.id, 1)

            cls.set_prefetch_cache(
                test.case,
                'attachments',
                attachments_map.get((case_content_type.model.lower(), test.case.id), []),
            )

            cls.set_prefetch_cache(
                test.plan,
                'attachments',
                attachments_map.get((plan_content_type.model.lower(), test.case.id), []),
            )

            if test.last_result:
                cls.set_prefetch_cache(
                    test.last_result,
                    'attachments',
                    attachments_map.get((result_content_type.model.lower(), test.last_result.id), []),
                )


            test.case._prefetched_objects_cache['steps'] = steps_map.get(test.case.id, [])
            for step in test.case.steps.all():
                cls.set_prefetch_cache(
                    step,
                    'attachments',
                    attachments_map.get((step_content_type.model.lower(), step.id), []),
                )
        return tests_qs, list(attachments_qs)
