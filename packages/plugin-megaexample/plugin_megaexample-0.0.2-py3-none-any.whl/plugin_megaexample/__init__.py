
from testy.plugins.hooks import TestyPluginConfig, hookimpl


class ExamplePluginConfig(TestyPluginConfig):
    package_name = 'plugin_megaexample'
    verbose_name = 'Plugin Mega example'
    description = 'It is very simple plugin example'
    version = '0.0.1'
    plugin_base_url = 'plugin-megaexample'
    index_reverse_name = 'upload-file'
    urls_module = 'plugin_megaexample.urls'


@hookimpl
def config():
    return ExamplePluginConfig
