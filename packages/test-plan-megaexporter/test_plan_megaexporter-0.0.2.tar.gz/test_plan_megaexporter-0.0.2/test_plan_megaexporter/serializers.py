
from rest_framework import serializers
from testy.tests_representation.api.v2.serializers import (
    TestPlanOutputSerializer,
    TestSerializer,
)
from testy.tests_representation.models import Test, TestPlan

from test_plan_megaexporter.models import DocumentRequest

TESTPLAN = 'testplan'
TESTREPORT = 'testreport'


class TestTreeSerializer(TestSerializer):
    name = serializers.CharField(source='case.name')

    class Meta:
        model = Test
        fields = ('id', 'name')


class TestPlanSerializer(TestPlanOutputSerializer):
    tests = TestTreeSerializer(many=True, read_only=True)

    class Meta:
        model = TestPlan
        fields = ('tests', 'id', 'name', 'parent')
        read_only_fields = fields


class BaseDocumentInputParamsSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(min_value=1)
    testplan_id = serializers.IntegerField(min_value=1)


class TestPlanDocumentInputParamsSerializer(BaseDocumentInputParamsSerializer):
    selected_test_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False, min_length=1,
    )


class TestReportDocumentInputParamsSerializer(BaseDocumentInputParamsSerializer):
    conclusion = serializers.CharField(max_length=5000, allow_blank=True, required=False, default='')


class DocumentRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    can_download = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    project_id = serializers.IntegerField(source='project_id', read_only=True)
    testplan_id = serializers.IntegerField(source='testplan_id', read_only=True)

    class Meta:
        model = DocumentRequest
        fields = [
            'id',
            'document_type',
            'document_type_display',
            'status',
            'status_display',
            'project_id',
            'testplan_id',
            'request_params',
            'file_name',
            'error_message',
            'task_id',
            'created_at',
            'updated_at',
            'completed_at',
            'can_download',
            'download_url',
        ]
        read_only_fields = [
            'id',
            'status',
            'file_name',
            'error_message',
            'task_id',
            'created_at',
            'updated_at',
            'completed_at',
        ]

    def get_can_download(self, obj):
        return obj.status == DocumentRequest.Status.DONE and obj.file_path

    def get_download_url(self, obj):
        if self.get_can_download(obj):
            return f'/plugins/test-plan-megaexporter/api/download/{obj.id}/'
        return None
