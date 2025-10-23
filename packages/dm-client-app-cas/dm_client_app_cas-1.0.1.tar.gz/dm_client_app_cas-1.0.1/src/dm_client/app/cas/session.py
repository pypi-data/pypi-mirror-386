from django.utils import dateparse
from django.utils.timezone import now
from django.conf import settings
from dm_core.meta.service import MetaClient
from dm_core.redis.service import RedisSessionManager
from dm_core.crypto.asymmetric import AsymmetricCrypto
from dm_core.redis.utils import singleton
from dm_core.meta.users import ExternalUser
from dm_client.app.cas.models import SignedSession, DecryptedUserModel
import importlib
import logging
import json

logger = logging.getLogger(__file__)


@singleton
class SessionWriteManager(object):

    def __init__(self):
        self.service = settings.SERVICE
        self.meta_client = MetaClient()
        response = self.meta_client.my_service_info()
        self.crypto = AsymmetricCrypto(private_key=response['private_key'], public_key=response['public_key'])

    def set_session(self, service: str, session: str, expires: str, application: str, user: DecryptedUserModel) -> ExternalUser:
        """
        set_session: Build the session based on the information received by CAS service and callback information
        """
        app_data = self._sso_cas_callback('USER_LOGIN_CALLBACK', application, user, service)
        session_data = self._build(session=session, expires=expires, application=application, user=user['id'], **app_data)
        session_dict = self._commit_session(session_data)
        instance = ExternalUser.build(session=session, expires=expires, application=application, user=user['id'],
                                      raw_data=session_dict, **app_data)
        return instance

    def unset_session(self, token: str):
        ret = RedisSessionManager().unset_session(token)
        if ret:
            self._sso_cas_callback('USER_LOGOUT_CALLBACK', token)
        return token

    def reset_session(self, session: str, resource: str = None, resource_type: str = None, group: str = None, permission: str = None) -> bool:
        signed_instance = RedisSessionManager().get(session)
        if signed_instance is None or not self.crypto.verify_sign(signed_instance['data'], signed_instance['sign']):
            return False
        session_data = json.loads(signed_instance['data'])
        session_data['resource'] = resource
        session_data['resource_type'] = resource_type
        session_data['group'] = group
        if permission is not None:
            session_data['permission'] = permission
        self._commit_session(self._build(**session_data))
        return True

    def _sso_cas_callback(self, call_back, *args, **kwargs):
        if hasattr(settings, 'SSO_CAS_APP_CONFIG') and call_back in settings.SSO_CAS_APP_CONFIG:
            cas_module, cas_klass = settings.SSO_CAS_APP_CONFIG[call_back].rsplit('.', 1)
            return getattr(importlib.import_module(cas_module), cas_klass)(*args, **kwargs)
        else:
            return kwargs

    def _commit_session(self, session_dict: dict) -> SignedSession:
        """
        Save session in memory and return signed_data dict
        """
        data = json.dumps(session_dict).encode()
        sign = self.crypto.sign(data)
        signed_data = {'data': data, 'sign': sign}
        expires = dateparse.parse_datetime(session_dict['expires'])
        timestamp = (expires - now()).total_seconds()
        RedisSessionManager().set_session(session_dict['session'], signed_data, timestamp)
        return signed_data

    def _build(self, **kwargs):
        return {
            'session': kwargs.pop('session'),
            'expires': kwargs.pop('expires'),
            'application': kwargs.pop('application'),
            'user': kwargs.pop('user'),
            'group': kwargs.pop('group'),
            'resource': kwargs.pop('resource'),
            'resource_type': kwargs.pop('resource_type'),
            'permission': kwargs.pop('permission')
        }