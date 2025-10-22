from dm_app.authz.models import ResourceUserGroupModel, GroupResourcePermissionModel
from typing import Union
from rest_framework import serializers
from django.apps import apps


class PermissionParamInputSerializer(serializers.Serializer):

    filter = serializers.CharField(max_length=255, required=False)


class PermissionsOutputSerializer(serializers.Serializer):

    permission = serializers.CharField(max_length=255)


class ResourceOutputSerializer(serializers.ModelSerializer):

    resource = serializers.CharField(source='resource_id')
    group = serializers.CharField(source='group')

    class Meta:
        model = ResourceUserGroupModel
        fields = ['resource', 'group']


class GroupResourcePermissionOutputSerializer(serializers.ModelSerializer):

    resource_type = serializers.SerializerMethodField()
    resource_alias = serializers.SerializerMethodField()

    def get_resource_type(self, obj):
        return self.context.get('resource_type')

    def get_resource_alias(self, obj) -> Union[str, None]:
        # If model does not exist, then we return None
        model = apps.get_model('core', 'AccountModel')
        try:
            return model.objects.get(id=obj.resource_id).alias
        except model.DoesNotExist:
            return None

    class Meta:
        model = GroupResourcePermissionModel
        fields = ['resource_id', 'resource_type', 'resource_alias', 'permissions']
