from rest_framework import serializers
from phonenumber_field import serializerfields


class SessionUserSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=512)
    name = serializers.CharField(max_length=1024)
    email = serializers.EmailField(max_length=1024)
    mobile = serializerfields.PhoneNumberField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['mobile'] = instance.mobile
        return data


class SessionSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512, source='session')
    application = serializers.CharField(max_length=32)
    expires = serializers.DateTimeField()
    user = serializers.CharField(max_length=32)
    resource = serializers.CharField(max_length=32)
    resource_type = serializers.CharField(max_length=16)
    group = serializers.CharField(max_length=32)


class LogoutInputSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)


class LogoutInputParamSerializer(serializers.Serializer):
    application = serializers.CharField(max_length=512, required=True)


class CasClientLoginParamSerializer(serializers.Serializer):
    service = serializers.CharField(max_length=512, required=True)
    ticket = serializers.CharField(max_length=4096, required=True)
