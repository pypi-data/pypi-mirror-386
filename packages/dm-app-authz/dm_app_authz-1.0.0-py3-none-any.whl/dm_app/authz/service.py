from django.apps import apps
from dm_app.authz.models import ResourceUserGroupModel, GroupResourcePermissionModel
import logging


logger = logging.getLogger()


class AuthzAppClientService(object):

    def get_model(self, model_name):
        return apps.get_model('dm_app_authz', model_name)

    def register_user(self, user_id, account_id, *args, **kwargs) -> ResourceUserGroupModel:
        return ResourceUserGroupModel.objects.register_user(user_id, account_id, *args, **kwargs)

    def get_resource_groups(self, user_id, *args, **kwargs):
        return ResourceUserGroupModel.objects.get_resource_groups(user_id)

    def get_resource_group(self, user_id, *args, **kwargs) -> ResourceUserGroupModel:
        return ResourceUserGroupModel.objects.get(user_id=user_id)

    def get_last_accessed_resource_group(self, user_id, *args, **kwargs) -> ResourceUserGroupModel:
        return ResourceUserGroupModel.objects.get_last_accessed_resource_group(user_id, *args, **kwargs)

    def get_group(self, user_id, resource_id) -> ResourceUserGroupModel:
        return ResourceUserGroupModel.objects.get_group(user_id, resource_id)
    
    def get_permissions_expression(self, group_id) -> str:
        try:
            permissions = sorted(GroupResourcePermissionModel.objects.get(group_id=group_id).permissions)
            return '|'.join([ '^' + permission.replace('.', r'\.').replace('*', '.*') + '$' for permission in permissions ])
        except GroupResourcePermissionModel.DoesNotExist as e:
            logger.info(f"Permissions are not set for group_id ${group_id}")
            return ''