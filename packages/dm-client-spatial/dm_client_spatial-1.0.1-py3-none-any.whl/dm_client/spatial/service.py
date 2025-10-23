from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request
from .models import AddressModel
from .exceptions import SpatialUnknownAddressException
import logging

logger = logging.getLogger()


@singleton
class SpatialClient(object):

    def __init__(self):
        self.service = settings.SERVICE
        self.meta_client = MetaClient()
        self.target_service = 'spatial'
        response = self.meta_client.service_info(self.target_service, cache_key=self.target_service)
        self.url = '{}'.format(response['url'])
        my_service_response = self.meta_client.my_service_info()
        self.private_key = my_service_response['private_key']

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

    ############## Core ################################

    def core_languages(self) -> (Response, Request):
        return self._api(self.target_service, 'core.languages')

    def core_timezone(self) -> (Response, Request):
        return self._api(self.target_service, 'core.time-zones')

    ############## Location ###############################

    def location_internal_geocode(self, address: str, country: str = None, language: str = 'en'):
        data = {
            'address': address,
            'language': language
        }
        if country is not None:
            data['country'] = country
        return self._api(self.target_service, 'location.internal.geo-code', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def location_geo_auto_complete(self, token: str, address: str, country=None, language=None, types: list| None=None):
        data = {
            'address': address
        }
        if country is not None:
            data['country'] = country
        if language is not None:
            data['language'] = language
        if types is not None:
            data['types'] = types
        return self._api(self.target_service, 'location.geo-auto-complete', params=data, request_auth=RequestAuthEnum.EXTERNAL, auth=token)

@singleton
class SpatialAppService(object):

    def get_object(self, address_id) -> AddressModel:
        return AddressModel.objects.get(pk=address_id)

    def save(self, address: str, entity_type: str) -> AddressModel:
        response, request = SpatialClient().location_internal_geocode(address)
        if response.status_code != 201:
            logger.info(request.__dict__)
            logger.info(response.__dict__)
            raise SpatialUnknownAddressException(message=response.json(), error_code=response.status_code)
        address_instance = AddressModel.objects.create_address(entity_type, **response.json())
        return address_instance
