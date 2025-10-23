from django.apps import AppConfig
# from django.conf import settings
# import logging
#
# logger = logging.getLogger()


class DmProxyoutClientConfig(AppConfig):

    name = 'dm_client.proxyout'
    lable = 'dm_client_proxyout'

    # def __init__(self, app_name, app_module):
    #     super(DmProxyoutClientConfig, self).__init__(app_name, app_module)
    #
    # def ready(self):
    #     from .service import ProxyoutClient
    #     ProxyoutClient()
