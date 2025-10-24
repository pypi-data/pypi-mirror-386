
from plugins.hooks import TestyPluginConfig, hookimpl


class TatlinAllureUploaderConfig(TestyPluginConfig):
    package_name = 'testrail_megamigrator'
    verbose_name = 'TestRail migrator'
    description = 'Migrate your data from testrail to testy'
    version = '0.3.0'
    plugin_base_url = 'migrator'
    index_reverse_name = 'migrator-index'
    urls_module = 'testrail_megamigrator.urls'


@hookimpl
def config():
    return TatlinAllureUploaderConfig
