from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


class FinanceClient(object):

    def __init__(self):
        self.service = settings.SERVICE
        self.meta_client = MetaClient()
        self.target_service = 'finance'
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

    ################ Authz #############################

    def authz_permissions(self):
        return self._api(self.target_service, 'authz.permissions')

    ################# Core #############################

    def core_register(self, token, account_type_id: str=None, alias=None, name=None, mobile=None, email=None, address=None) -> (Response, Request):
        data = {
            'alias': alias,
            'profile': {
                'name': name,
                'mobile': mobile,
                'email': email,
                'address': address
            }
        }
        params = {}
        if account_type_id:
            params['account_type_id'] = account_type_id
        return self._api(self.target_service, 'core.register', json=data, params=params,
                         request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def core_list(self, token) -> (Response, Request):
        return self._api(self.target_service, 'core.list',
                         request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def core_set(self, token, account_id) -> (Response, Request):
        url_params = {'account_id': account_id}
        return self._api(self.target_service, 'core.set', url_params=url_params,
                         request_auth=RequestAuthEnum.EXTERNAL, auth=token)


    ############################### CAS Client ##########################
    #             Not required, as client is invoked separately         #
    #####################################################################

    ########################### Transaction #############################
    def transaction_list(self, token) -> (Response, Request):
        return self._api(self.target_service, 'transaction.list',
                         request_auth=RequestAuthEnum.EXTERNAL, auth=token)