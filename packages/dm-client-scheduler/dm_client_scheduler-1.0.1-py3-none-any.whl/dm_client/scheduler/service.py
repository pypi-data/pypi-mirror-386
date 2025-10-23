from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


@singleton
class SchedulerClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'scheduler'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, id, method, url_path, *args, **kwargs):
        response, request = Requests(service, id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    ############### Version ############################

    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ############### Core ############################

    def core_internal_event_set(self, type: str, type_id: str, starts_on, payload=None, ends_on=None, recur_expressions=None) -> (Response, Request):
        data = {
            'type': type,
            'type_id': type_id, # rest api id OR message exchange:routing_key
            'starts_on': starts_on,
        }
        if payload is not None:
            data['payload'] = payload
        if ends_on is not None:
            data['ends_on'] = ends_on
        if recur_expressions is not None:
            data['recur_expressions'] = recur_expressions
        return self._api(self.target_service, 'core.internal.event.set', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def core_internal_event_unset(self, schedule_id) -> (Response, Request):
        url_params = {
            'id': schedule_id
        }
        return self._api(self.target_service, 'core.internal.event.unset', url_params=url_params, request_auth=RequestAuthEnum.INTERNAL)