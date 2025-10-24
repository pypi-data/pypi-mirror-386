


from testy.plugins.hooks import TestyPluginConfig, hookimpl


class TestPlanExporterConfig(TestyPluginConfig):
    package_name = 'test_plan_exporter'
    verbose_name = 'Test plan exporter'
    description = 'Export test plan and cases to PDF'
    version = '0.0.68'
    plugin_base_url = 'test-plan-exporter'
    index_reverse_name = 'test-plan-exporter-page'
    urls_module = 'test_plan_exporter.urls'


@hookimpl
def config():
    return TestPlanExporterConfig
