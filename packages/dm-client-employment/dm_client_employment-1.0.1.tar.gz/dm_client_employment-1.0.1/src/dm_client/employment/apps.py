from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger()


class DmClientEmploymentConfig(AppConfig):

    name = 'dm_client.employment'
    label = 'dm_client_employment'

    # def __init__(self, app_name, app_module):
    #     super(DmEmploymentClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import EmploymentClient
    #     EmploymentClient()
