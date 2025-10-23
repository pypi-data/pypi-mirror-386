from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmClientSchedulerAppConfig(AppConfig):

    name = 'dm_client.scheduler'
    label = 'dm_client_scheduler'

    # def __init__(self, app_name, app_module):
    #     super(DmSchedulerClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import SchedulerClient
    #     SchedulerClient()
