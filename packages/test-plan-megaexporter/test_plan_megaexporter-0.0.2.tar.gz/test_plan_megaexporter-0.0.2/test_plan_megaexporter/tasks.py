
import logging
import os

from celery import shared_task
from django.db import DatabaseError, transaction
from django.utils import timezone
from testy.tests_representation.models import TestPlan
import test_plan_megaexporter.report.plan
import test_plan_megaexporter.report.result
from test_plan_megaexporter import report
from .models import DocumentRequest

from test_plan_megaexporter.selectors import TestPlanSelector, TestResultsSelector, map_attachments

CAN_USE_DEFECT_REPORT = False
try:
    from defect_report.selectors import DefectReportSelector
    CAN_USE_DEFECT_REPORT = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


@shared_task()
def generate_testplan_document(document_request_id):
    try:
        with transaction.atomic():
            doc_request = DocumentRequest.objects.select_for_update().get(
                id=document_request_id,
                status=DocumentRequest.Status.PENDING,
            )
            doc_request.status = DocumentRequest.Status.IN_PROGRESS
            doc_request.save()
    except DatabaseError as e:
        logger.error(e)
        return

    params = doc_request.request_params
    testplan_id = params.get('testplan_id')
    selected_test_ids = params.get('selected_test_ids', [])

    node = TestPlan.objects.get(id=testplan_id)

    tests, attachments = TestPlanSelector.get_test_plan_tests(node, selected_test_ids)
    attachments_map = map_attachments(attachments)
    try:
        pdf_buffer = test_plan_megaexporter.report.plan.generate_report_pdf(node, tests, attachments_map)
        file_path = report.common.save_pdf_to_file(pdf_buffer, node.name, 'testplan')

        doc_request.status = DocumentRequest.Status.DONE
        doc_request.file_path = file_path
        doc_request.file_name = os.path.basename(file_path)

    except Exception as e:
        doc_request.status = DocumentRequest.Status.FAILED
        doc_request.error_message = str(e)

    doc_request.completed_at = timezone.now()
    doc_request.save()


@shared_task()
def generate_testreport_document(document_request_id):
    try:
        with transaction.atomic():
            doc_request = DocumentRequest.objects.select_for_update().get(
                id=document_request_id,
                status=DocumentRequest.Status.PENDING,
            )
            doc_request.status = DocumentRequest.Status.IN_PROGRESS
            doc_request.save()
    except DatabaseError as e:
        logger.error(e)
        return

    params = doc_request.request_params
    project_id = params.get('project_id')
    testplan_id = params.get('testplan_id')
    conclusion = params.get('conclusion', '')

    node = TestPlan.objects.get(id=testplan_id)
    tests, attachments = TestResultsSelector.get_testplan_tests(node)
    attachments_map = map_attachments(attachments)

    if CAN_USE_DEFECT_REPORT:
        try:
            root_plan = TestPlan.objects.get(id=testplan_id)
            all_defects_qs = (
                DefectReportSelector.prepare_defect_list(attributes=['Defects'])
                .filter(project_id=project_id)
                .filter(test__plan__path__descendant=root_plan.path)
            )
        except Exception as e:
            logger.warning(f'Не удалось получить данные о дефектах: {str(e)}')

    try:
        pdf_buffer = test_plan_megaexporter.report.result.generate_report_pdf(
            node,
            tests,
            attachments_map,
            defects=all_defects_qs,
            conclusion=conclusion,
        )
        file_path = report.common.save_pdf_to_file(pdf_buffer, node.name, 'testreport')

        doc_request.status = DocumentRequest.Status.DONE
        doc_request.file_path = file_path
        doc_request.file_name = os.path.basename(file_path)

    except Exception as e:
        doc_request.status = DocumentRequest.Status.FAILED
        doc_request.error_message = str(e)
        logger.exception(e)

    doc_request.completed_at = timezone.now()
    doc_request.save()
