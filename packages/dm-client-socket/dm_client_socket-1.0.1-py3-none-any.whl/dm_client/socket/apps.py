from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmClientSocketAppConfig(AppConfig):

    name = 'dm_client.socket'
    label = 'dm_client_socket'

    # def __init__(self, app_name, app_module):
    #     super(DmSocketClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import SocketClient
    #     SocketClient()
