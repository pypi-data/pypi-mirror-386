from cassandra.cqlengine import columns
from django.db import models
from datetime import datetime
from django_cassandra_engine.models import DjangoCassandraModel
from typing import TypedDict
from enum import Enum
import logging


logger = logging.getLogger(__file__)


class UserSessionEventEnum(Enum):
    login = 'LOGIN'
    logout = 'LOGOUT'


class AuthTypeEnum(Enum):
    cas = 'CAS'


class CasClientModel(models.Model):
    service = models.CharField(max_length=512, primary_key=True)
    fernet_key = models.CharField(max_length=4096, unique=True)
    application = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'dm_client_app_cas_client'


class UserSessionLog(DjangoCassandraModel):
    id = columns.Text(max_length=128, primary_key=True)
    auth_type = columns.Text(max_length=32)
    user_id = columns.Text(max_length=32)
    ip_address = columns.Text(max_length=15)
    event = columns.Text(max_length=15, primary_key=True)
    event_at = columns.DateTime(default=datetime.utcnow, primary_key=True)

    class Meta:
        get_pk_field = 'id'
        db_table = 'user_session_log'
        managed = False

    @classmethod
    def login(cls, auth_id, user_id, ip_address):
        return cls.objects.create(id=auth_id,
                                  auth_type=AuthTypeEnum.cas.value,
                                  user_id=user_id,
                                  ip_address=ip_address,
                                  event=UserSessionEventEnum.login.value)

    @classmethod
    def logout(cls, auth_id, user_id, ip_address):
        return cls.objects.create(id=auth_id,
                                  auth_type=AuthTypeEnum.cas.value,
                                  user_id=user_id,
                                  ip_address=ip_address,
                                  event=UserSessionEventEnum.logout.value)

class SignedSession(TypedDict):
    data: str
    sign: str


class DecryptedUserModel(TypedDict):
    id: str
    email: str
    mobile: str
    name: str


class DecryptedModel(TypedDict):
    application: str
    expires: str
    session: str
    user: DecryptedUserModel

class UserResourceGroupPermissionModel(TypedDict):
    resource: str
    resource_type: str
    group: str
    permission: str
