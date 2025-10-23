from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmClientTransactionAppConfig(AppConfig):

    name = 'dm_client.transaction'
    label = 'dm_client_transaction'

    # def __init__(self, app_name, app_module):
    #     super(DmTransactionClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import TransactionClient
    #     TransactionClient()
