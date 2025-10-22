import cryptography.exceptions
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from dm_core.meta.decorator import api_inbound_validator
from rest_framework.generics import RetrieveAPIView, CreateAPIView
from rest_framework import status
from rest_framework.response import Response
from dm_client.app.cas.models import CasClientModel, UserSessionLog, DecryptedModel
from dm_client.app.cas.session import SessionWriteManager
from dm_client.app.cas.crypto import SecureMessage
from dm_client.app.cas.serializers import SessionSerializer, LogoutInputSerializer, LogoutInputParamSerializer, CasClientLoginParamSerializer
from dm_client.auth.service import AuthClient
from dm_core.meta import exceptions
from dm_core.crypto.symmetric import SymmetricCrypto
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from .errors import GET_ERROR
import re


class CasClientLoginApiView(RetrieveAPIView):

    api_id = {
        'GET': '{}.sso.cas-client.login'.format(settings.SERVICE)
    }
    params_serializer_class = CasClientLoginParamSerializer

    def validate_service_ticket(self, service_ticket):
        """
        Validate the service ticket
            Return True if None or if match the pattern
        """
        if service_ticket is not None:
            return re.compile(r"ST-[0-9a-z]{32}").fullmatch(service_ticket)
        return True
            

    def validate_service_param(self, service_param):
        """
        Validate service param to be valid URL
            Return True if None or if valid URL
        """
        if service_param is None:
            return True
        try:
            URLValidator(service_param)
            return True
        except ValidationError as e:
            return   False

    @api_inbound_validator()
    def get(self, request, *args, **kwargs):
        """
        Accept the ST token
        """
        service_ticket = request.query_params.get('ticket')
        if not self.validate_service_ticket(service_ticket):
            return Response(data=GET_ERROR('DMCLIENTAPPCAS001'), status=status.HTTP_401_UNAUTHORIZED)
        if not self.validate_service_param(service_ticket):
            return Response(data=GET_ERROR('DMCLIENTAPPCAS002'), status=status.HTTP_401_UNAUTHORIZED)
        service = request.query_params.get('service')
        cas_client_config = self.get_cas_config(service)
        encrypted_service_ticket = self._encrypt(cas_client_config.fernet_key, service_ticket)
        response, _ = AuthClient().sso_cas_service_validate(encrypted_service_ticket, service)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            return Response(data=GET_ERROR('DMCLIENTAPPCAS003'), status=status.HTTP_401_UNAUTHORIZED)
        decrypted_data: DecryptedModel = SecureMessage().decrypt(cas_client_config.fernet_key, response.json())
        data = SessionWriteManager().set_session(service, **decrypted_data)
        serialized_data = SessionSerializer(instance=data)
        ip_address = self._get_client_ip(request)
        UserSessionLog.login(serialized_data.data['token'], serialized_data.data['user'], ip_address)
        return Response(status=status.HTTP_201_CREATED, data=serialized_data.data)

    def get_serializer_class(self):
        return None

    def get_cas_config(self, service):
        try:
            return CasClientModel.objects.extra(
                    where=["%s like service || '%%' "],
                    params=[service],
                ).get()
        except (CasClientModel.DoesNotExist, CasClientModel.MultipleObjectsReturned) as e:
            raise exceptions.RestAuthenticationException(detail=GET_ERROR('DMCLIENTAPPCAS004', service))

    def _encrypt(self, key, service_ticket: str):
        return SymmetricCrypto(key).encrypt_data(service_ticket.encode())

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CasClientLogoutApiView(CreateAPIView):
    
    """
    Logout API for CAS App Client
    
    This API will be invoked by CAS Service (Part of Auth Service) 
    Auth Type: Anonymous, but the data is encrypted using the key
    """

    api_id = {
        'POST': '{}.sso.cas-client.logout'.format(settings.SERVICE)
    }
    serializer_class = LogoutInputSerializer
    input_serializer_class = LogoutInputSerializer
    params_serializer_class = LogoutInputParamSerializer

    @api_inbound_validator()
    def post(self, request, *args, **kwargs):
        serializer = kwargs['serializer']
        decrypt_token = self._decrypt_data(serializer.data)
        SessionWriteManager().unset_session(decrypt_token['token'])
        ip_address = self._get_client_ip(request)
        UserSessionLog.login(decrypt_token['token'], ip_address, ip_address)
        return Response(status=status.HTTP_200_OK)

    def _decrypt_data(self, data):
        try:
            cas_client = CasClientModel.objects.get(application=self.request.query_params['application'])
        except CasClientModel.DoesNotExist:
            raise exceptions.RestAuthenticationException()
        try:
            return SecureMessage().decrypt(cas_client.fernet_key, data)
        except cryptography.exceptions.InvalidKey:
            raise exceptions.RestAuthenticationException()

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
