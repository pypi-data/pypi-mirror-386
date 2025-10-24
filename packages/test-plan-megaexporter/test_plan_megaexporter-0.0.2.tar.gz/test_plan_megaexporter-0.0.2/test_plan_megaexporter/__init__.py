


from testy.plugins.hooks import TestyPluginConfig, hookimpl


class TestPlanExporterConfig(TestyPluginConfig):
    package_name = 'test_plan_megaexporter'
    verbose_name = 'Test plan megaexporter'
    description = 'Export test plan and cases to PDF'
    version = '0.0.1'
    plugin_base_url = 'test-plan-megaexporter'
    index_reverse_name = 'test-plan-megaexporter-page'
    urls_module = 'test_plan_megaexporter.urls'


@hookimpl
def config():
    return TestPlanExporterConfig
