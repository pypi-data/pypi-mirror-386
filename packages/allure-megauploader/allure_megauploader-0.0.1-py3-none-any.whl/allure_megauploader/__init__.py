from testy.plugins.hooks import TestyPluginConfig, hookimpl


class AllureUploaderConfig(TestyPluginConfig):
    package_name = 'allure_uploader_v2'
    verbose_name = 'Allure uploader v2'
    description = 'Upload your allure report into testy'
    version = '2.1.2'
    plugin_base_url = 'allure-uploader-v2'
    author = 'Roman Kabaev'
    author_email = 'r.kabaev@yadro.com'
    index_reverse_name = 'config-list'
    urls_module = 'allure_uploader_v2.urls'
    min_version = '2.0.0'


@hookimpl
def config():
    return AllureUploaderConfig
