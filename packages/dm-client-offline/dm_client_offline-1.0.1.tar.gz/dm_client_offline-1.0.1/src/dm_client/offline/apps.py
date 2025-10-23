from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmClientOfflineAppConfig(AppConfig):

    name = 'dm_client.offline'
    label = 'dm_client_offline'

    # def __init__(self, app_name, app_module):
    #     super(DmOfflineClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import OfflineClient
    #     OfflineClient()
