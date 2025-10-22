from django.conf import settings
from dm_core.meta.service import MetaClient
from dm_core.meta.decorator import api_outbound_validator
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


@singleton
class AiClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'ai'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, api_id, method, url_path, *args, **kwargs):
        response, request = Requests(service, api_id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    #################### Version ########################

    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ################## TRANSFORMER ###################

    def transformer_internal_sentence(self, text: str) -> (Response, Request):
        data = {'text': text}
        return self._api(self.target_service, 'transformer.internal.sentence', json=data, request_auth=RequestAuthEnum.INTERNAL)

    ################## SCHEDULE ######################

    def schedule_internal_cleanup(self) -> (Response, Request):
        return self._api(self.target_service, 'schedule.internal.cleanup', request_auth=RequestAuthEnum.INTERNAL)

