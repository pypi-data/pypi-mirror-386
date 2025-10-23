from django.apps import AppConfig


class DmClientFileAppConfig(AppConfig):

    name = 'dm_client.file'
    label = 'dm_client_file'

    # def __init__(self, app_name, app_module):
    #     super(DmFileClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import FileClient
    #     FileClient()
