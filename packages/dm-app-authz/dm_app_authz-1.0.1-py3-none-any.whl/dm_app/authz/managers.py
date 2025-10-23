from django.apps import apps
from django.db import models
from django.db.models.query import QuerySet
from uuid import uuid4


class ResourceUserGroupManager(models.Manager):

    def register_user(self, user_id, resource_id, group=None, template='OWNER'):
        """
        Register user
        """
        default_app_permission_template_model = apps.get_model('dm_app_authz', 'DefaultAppPermissionTemplateModel')
        group_resource_permission_model = apps.get_model('dm_app_authz', 'GroupResourcePermissionModel')
        app_permission_model = apps.get_model('dm_app_authz', 'AppPermissionModel')
        if group is None:
            permission_template = default_app_permission_template_model.objects.get(name=template)
            permissions = app_permission_model.objects.filter(name__in=permission_template.permissions).values_list('value', flat=True)
            group = group_resource_permission_model.objects.create(resource_id=resource_id,
                                                                   permissions=list(permissions),
                                                                   name=permission_template.name)
        instance = self.model.objects.create(user_id=user_id, resource_id=resource_id, group=group)
        return instance

    def get_resource_groups(self, user_id) -> QuerySet:
        """
        Return all the resource_id, group_id related to user_id
        """
        return self.model.objects.filter(user_id=user_id)

    def get_resource_group(self, user_id):
        """
        Return single record of resource_id and group_id related to user_id
        """
        return self.model.objects.get(user_id=user_id)

    def get_last_accessed_resource_group(self, user_id):
        """
        Return last accessed resource_id, group_id related to user_id
        """
        return self.model.objects.order_by('-last_accessed').filter(user_id=user_id).first()

    def get_group(self, user_id, resource_id):
        """
        Return ResourceUserGroup model given user_id nd resource_id
        """
        return self.model.objects.filter(user_id=user_id, resource_id=resource_id).first()