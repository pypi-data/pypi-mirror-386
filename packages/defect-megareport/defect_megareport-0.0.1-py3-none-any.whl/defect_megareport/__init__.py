


from testy.plugins.hooks import TestyPluginConfig, hookimpl


class DefectReportConfig(TestyPluginConfig):
    package_name = 'defect_report'
    verbose_name = 'Defect Report'
    description = 'Prepare defect report'
    version = '0.0.23'
    plugin_base_url = 'defect-report'
    index_reverse_name = 'defect-report-page'
    urls_module = 'defect_report.urls'


@hookimpl
def config():
    return DefectReportConfig
