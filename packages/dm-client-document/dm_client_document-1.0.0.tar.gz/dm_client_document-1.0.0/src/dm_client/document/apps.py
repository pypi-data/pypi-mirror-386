from django.apps import AppConfig
import logging

logger = logging.getLogger()


class DmClientDocumentAppConfig(AppConfig):

    name = 'dm_client.document'
    label = 'dm_client_document'
