from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmClientValidatorAppConfig(AppConfig):

    name = 'dm_client.validator'
    label = 'dm_client_validator'

    # def __init__(self, app_name, app_module):
    #     super(DmValidatorClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import ValidatorClient
    #     ValidatorClient()
