
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from testy.core.models import Project
from testy.tests_representation.models import TestPlan

from .models import DocumentRequest
from .serializers import (
    TestPlanDocumentInputParamsSerializer,
    TestPlanSerializer,
    TestReportDocumentInputParamsSerializer,
)
from .tasks import generate_testplan_document, generate_testreport_document


class TestPlanExporterPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return render(
            request,
            template_name='test_plan_megaexporter.html',
        )


class PlanTestsHierarchyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id):
        node = TestPlan.objects.get(id=plan_id)
        plans = TestPlan.objects.prefetch_related('tests', 'tests__case').filter(
            path__descendant=node.path,
            is_archive=False,
            tests__is_archive=False,
        ).distinct()
        serializer = TestPlanSerializer(plans, many=True)
        return Response({'data': serializer.data})


@method_decorator(csrf_exempt, name='dispatch')
class DocumentsView(GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='testplan', url_name='testplan')
    def add_testplan(self, request):
        serializer = TestPlanDocumentInputParamsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_request = DocumentRequest.objects.create(
            user_id=request.user.id,
            document_type=DocumentRequest.DocumentType.TESTPLAN,
            request_params=serializer.validated_data,
            status=DocumentRequest.Status.PENDING,
        )

        generate_testplan_document.delay(doc_request.id)

        return Response(
            {
                'request_id': doc_request.id,
                'status': doc_request.status,
                'message': 'Запрос на генерацию документа принят в обработку',
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=['post'], url_path='testreport', url_name='testreport')
    def add_testreport(self, request):
        serializer = TestReportDocumentInputParamsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_request = DocumentRequest.objects.create(
            user_id=request.user.id,
            document_type=DocumentRequest.DocumentType.TESTREPORT,
            request_params=serializer.validated_data,
            status=DocumentRequest.Status.PENDING,
        )

        generate_testreport_document.delay(doc_request.id)

        return Response(
            {
                'request_id': doc_request.id,
                'status': doc_request.status,
                'message': 'Запрос на генерацию документа принят в обработку',
            },
            status=status.HTTP_202_ACCEPTED,
        )


class DocumentsListPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        docs = DocumentRequest.objects.filter(user_id=request.user.id).order_by('-created_at')

        project_ids = [doc.project_id for doc in docs if doc.project_id]
        testplan_ids = [doc.testplan_id for doc in docs if doc.testplan_id]

        projects = {p.id: p for p in Project.objects.filter(id__in=project_ids)}
        testplans = {tp.id: tp for tp in TestPlan.objects.filter(id__in=testplan_ids)}

        for doc in docs:
            doc.project_name = projects.get(doc.project_id).name if doc.project_id in projects else None
            doc.testplan_name = testplans.get(doc.testplan_id).name if doc.testplan_id in testplans else None

        return render(
            request,
            template_name='documents_list.html',
            context={
                'documents': docs,
            },
        )


class DownloadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, doc_id):
        doc = get_object_or_404(
            DocumentRequest,
            id=doc_id,
            user_id=request.user.id,
            status=DocumentRequest.Status.DONE,
        )

        full_path = default_storage.path(doc.file_path.lstrip('/'))
        if not default_storage.exists(full_path):
            raise Http404('Файл не найден')

        return FileResponse(
            default_storage.open(full_path, 'rb'),
            as_attachment=True,
            filename=doc.file_name,
        )
