from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


@singleton
class ProxyoutClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'proxyout'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, id, method, url_path, *args, **kwargs):
        response, request = Requests(service, id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    ############### Version ############################

    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ################## SCHEDULE ######################
    def schedule_internal_cleanup(self) -> (Response, Request):
        return self._api(self.target_service, 'schedule.internal.cleanup', request_auth=RequestAuthEnum.INTERNAL)

    ############## Notify ################################
    def notify_email(self, to: list, subject: str, content_html: str, content_text: str, cc: list = [], bcc: list = [], files: list = []) -> (Request, Response):
        data = {
            'to': to,
            'cc': cc,
            'bcc': bcc,
            'subject': subject,
            'html': content_html,
            'text': content_text,
            'files': files
        }
        return self._api(self.target_service, 'notify.internal.email', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def notify_sms(self, to: list, message: str) -> (Request, Response):
        data = {
            'to': to,
            'message': message
        }
        return self._api(self.target_service, 'notify.internal.sms', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def notify_mpn(self, source: str, to: list, title: str, message: str) -> (Request, Response):
        data = {
            'source': source,
            'to': to,
            'title': title,
            'message': message
        }
        return self._api(self.target_service, 'notify.internal.mpn', json=data, request_auth=RequestAuthEnum.INTERNAL)

    ##################### Validator ##############################

    def validator_email(self, email: str) -> (Request, Response):
        data = {
            'email': email
        }
        return self._api(self.target_service, 'validator.internal.email', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def validator_phone(self, number: str) -> (Request, Response):
        data = {
            'number': number
        }
        return self._api(self.target_service, 'validator.internal.phone', json=data, request_auth=RequestAuthEnum.INTERNAL)

    ################### Geo ######################################

    def geo_internal_ip(self, ip: str) -> (Request, Response):
        data = {
            'ip': ip
        }
        return self._api(self.target_service, 'geo.internal.ip', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def geo_internal_code(self, address: str, country: str = None, language: str = 'en') -> (Request, Response):
        data = {
            'address': address,
            'language': language
        }
        if country is not None:
            data['country'] = country
        return self._api(self.target_service, 'geo.internal.geo-code', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def geo_internal_reverse_code(self, latitude: str, longitude: str, language: str = 'en', country: str = None, types: str = None) -> (Request, Response):
        data = {
            'latitude': latitude,
            'longitude': longitude
        }
        if country is not None:
            data['country'] = country
        if types is not None:
            if types in ['full_address', 'country', 'administrative_area', 'locality', 'sub_locality']:
                data['types'] = types 
        return self._api(self.target_service, 'geo.internal.reverse-geo-code', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def geo_internal_auto_complete(self, address: str, country: str = None, language: str = 'en', **kwargs):
        data = {
            'address': address,
            'language': language
        }
        if country is not None:
            data['country'] = country
        if kwargs.get('types') is not None:
            if kwargs.get('types') in ['full_address', 'country', 'administrative_area', 'locality', 'sub_locality']:
                data['types'] = kwargs.get('types')
        return self._api(self.target_service, 'geo.internal.auto-complete', json=data, request_auth=RequestAuthEnum.INTERNAL)
