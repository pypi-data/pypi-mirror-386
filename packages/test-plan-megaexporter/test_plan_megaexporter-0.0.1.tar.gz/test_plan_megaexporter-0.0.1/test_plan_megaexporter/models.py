
from django.db import models
from testy.root.models import BaseModel


class DocumentRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        DONE = 'DONE', 'Done'
        FAILED = 'FAILED', 'Failed'

    class DocumentType(models.TextChoices):
        TESTPLAN = 'testplan', 'Test Plan'
        TESTREPORT = 'testreport', 'Test Report'

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(db_index=True)
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    request_params = models.JSONField(default=dict)

    file_path = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document Request'
        verbose_name_plural = 'Document Requests'

    @property
    def project_id(self):
        return self.request_params.get('project_id')

    @property
    def testplan_id(self):
        return self.request_params.get('testplan_id')

    @property
    def selected_test_ids(self):
        return self.request_params.get('selected_test_ids', [])

    @property
    def conclusion(self):
        return self.request_params.get('conclusion', '')
