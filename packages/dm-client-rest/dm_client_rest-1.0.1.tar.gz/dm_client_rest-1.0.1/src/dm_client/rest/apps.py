from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmClientRestAppConfig(AppConfig):

    name = 'dm_client.rest'
    label = 'dm_client_rest'

    # def __init__(self, app_name, app_module):
    #     super(DmRestClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import RestClient
    #     RestClient()
