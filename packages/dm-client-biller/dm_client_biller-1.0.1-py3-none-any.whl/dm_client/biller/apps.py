from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger()


class DmClientBillerAppConfig(AppConfig):

    name = 'dm_client.biller'
    label = 'dm_client_biller'
