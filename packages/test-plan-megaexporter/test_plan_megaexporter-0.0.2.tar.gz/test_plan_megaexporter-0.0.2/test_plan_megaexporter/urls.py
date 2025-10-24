
from django.urls import path
from rest_framework.routers import SimpleRouter

from test_plan_megaexporter import views

router = SimpleRouter()

router.register(r'api/documents', views.DocumentsView, basename='documents')
urlpatterns = [
    path(
        'test-plan-megaexporter-page/',
        views.TestPlanExporterPageView.as_view(),
        name='test-plan-megaexporter-page',
    ),
    path(
        'documents-list/',
        views.DocumentsListPageView.as_view(),
        name='documents-list-page',
    ),
    path(
        'api/plan/<int:plan_id>/tests/hierarchy/',
        views.PlanTestsHierarchyAPIView.as_view(),
        name='plan-tests-hierarchy',
    ),
    path(
        'download/<int:doc_id>/',
        views.DownloadDocumentView.as_view(),
        name='download-document',
    ),
]
urlpatterns += router.urls
