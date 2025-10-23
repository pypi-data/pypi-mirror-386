from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger()


class DmClientGraphAppConfig(AppConfig):

    name = 'dm_client.graphql'
    label = 'dm_client_graphql'

    # def __init__(self, app_name, app_module):
    #     super(DmGraphqlClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import GraphqlClient
    #     GraphqlClient()
