from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmSupportClientConfig(AppConfig):

    name = 'dm_client.support'
    label = 'dm_client_support'

    # def __init__(self, app_name, app_module):
    #     super(DmSupportClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import SupportClient
    #     SupportClient()
