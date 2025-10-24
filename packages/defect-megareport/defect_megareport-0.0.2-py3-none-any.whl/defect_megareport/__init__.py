


from testy.plugins.hooks import TestyPluginConfig, hookimpl


class DefectReportConfig(TestyPluginConfig):
    package_name = 'defect_megareport'
    verbose_name = 'Defect Report'
    description = 'Prepare defect report'
    version = '0.0.23'
    plugin_base_url = 'defect-megareport'
    index_reverse_name = 'defect-megareport-page'
    urls_module = 'defect_megareport.urls'


@hookimpl
def config():
    return DefectReportConfig
