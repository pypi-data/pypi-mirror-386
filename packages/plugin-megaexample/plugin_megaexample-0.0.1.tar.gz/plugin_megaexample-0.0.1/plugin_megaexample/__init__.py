
from testy.plugins.hooks import TestyPluginConfig, hookimpl


class ExamplePluginConfig(TestyPluginConfig):
    package_name = 'plugin_example'
    verbose_name = 'Plugin example'
    description = 'It is very simple plugin example'
    version = '0.2.0'
    plugin_base_url = 'plugin-example'
    index_reverse_name = 'upload-file'
    urls_module = 'plugin_example.urls'


@hookimpl
def config():
    return ExamplePluginConfig
