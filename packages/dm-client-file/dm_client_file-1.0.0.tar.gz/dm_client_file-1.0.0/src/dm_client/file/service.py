from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from datetime import datetime
from requests.models import Response, Request
from typing import NamedTuple, List


class FileParam(NamedTuple):
    location: str
    types: list[str]
    max_kilo_bytes: int


@singleton
class FileClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'file'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, id, method, url_path, *args, **kwargs) -> (Response, Request):
        response, request = Requests(service, id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    ############### Version ############################

    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ##################### Core ##########################

    def core_internal_upload_initiate(self, files: List[FileParam], **kwargs) -> (Response, Request):
        """
        Initiate file upload
        :return: token
        """
        data = {
            'files': list(map(lambda x: x._asdict(), files))
        }
        if 'timeout' in kwargs:
            data['timeout'] = kwargs.pop('timeout')
        if 'sign_required' in kwargs:
            data['sign_required'] = kwargs.pop('sign_required')
        return self._api(self.target_service, 'core.internal.upload-initiate', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def core_internal_upload_complete(self, upload_id: str, expires_at: datetime, deprecated_file_ids: list[str] = []) -> (Response, Request):
        """
        Mark file upload completed
        :return:
        """
        url_params = {
            'upload_id': upload_id
        }
        data = {
            'expires_at': expires_at.isoformat(),
            'deprecated_file_ids': deprecated_file_ids
        }
        return self._api(self.target_service, 'core.internal.upload-complete', url_params=url_params, json=data, request_auth=RequestAuthEnum.INTERNAL)

    def core_upload_refresh(self, upload_id):
        url_params = {
            'upload_id': upload_id
        }
        return self._api(self.target_service, 'core.upload-refresh', url_params=url_params, request_auth=RequestAuthEnum.INTERNAL)

    def core_upload(self, upload_id: str, expires_at: str, files: list):
        url_params = {
            'id': upload_id
        }
        data = {
            'expires_at': expires_at
        }
        return self._api(self.target_service, 'core.upload', url_params=url_params, data=data, files=files, request_auth=RequestAuthEnum.ANONYMOUS)

    def core_download(self, file_id):
        url_params = {
            'file_id': file_id
        }
        return self._api(self.target_service, 'core.download', url_params=url_params)
    
    def core_internal_download_url(self, file_id: str, sign_duration: int = 0):
        data = {
            'file_id': file_id,
        }
        if sign_duration > 0:
            data['sign_duration'] = sign_duration
        return self._api(self.target_service, 'core.internal.download-url', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def core_internal_download_urls(self, file_ids: list[str], sign_duration: int = 0):
        data = {
            'file_ids': file_ids
        }
        if sign_duration > 0:
            data['sign_duration'] = sign_duration
        return self._api(self.target_service, 'core.internal.download-urls', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def core_internal_files_patch(self, deletes: List[str] = None, updates: List[dict] = None):
        data = {}
        if deletes and len(deletes) > 0:
            data['deletes'] = deletes
        if updates and len(updates) > 0:
            data['updates'] = updates
        return self._api(self.target_service, 'core.internal.files.patch', json=data, request_auth=RequestAuthEnum.INTERNAL)

    ################## SCHEDULE ######################
    def schedule_internal_cleanup(self) -> (Response, Request):
        """
        Remove incomplete or partially uploaded files
        """
        return self._api(self.target_service, 'schedule.internal.cleanup', request_auth=RequestAuthEnum.INTERNAL)