from django.db import models
from uuid import uuid4
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from dm_app.authz.managers import ResourceUserGroupManager
from dm_core.meta.utils import uuid_generator


class DefaultAppPermissionTemplateModel(models.Model):
    """
    Default Permissions created for any resource
    """
    name = models.CharField(primary_key=True, max_length=128)
    permissions = ArrayField(models.CharField(max_length=255), blank=True)

    class Meta:
        db_table = 'dm_app_authz_default_app_permission_template'

    def __str__(self):
        return self.name


class AppPermissionModel(models.Model):
    """
    List of all possible permissions for the application
    """
    name = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=255, blank=False)
    value = models.CharField(max_length=255, blank=False)
    description = models.CharField(max_length=255)

    class Meta:
        db_table = 'dm_app_authz_app_permission'


class GroupResourcePermissionModel(models.Model):
    resource_id = models.CharField(max_length=32)
    group_id = models.CharField(max_length=32, primary_key=True, default=uuid_generator)
    permissions = ArrayField(models.CharField(max_length=255), blank=True, default=list)
    editable = models.BooleanField(default=False)
    name = models.CharField(null=False, blank=False, max_length=255)

    class Meta:
        unique_together = [['group_id', 'resource_id']]
        db_table = 'dm_app_authz_group_resource_permission'


class ResourceUserGroupModel(models.Model):
    """
    Resource is tenant_id or account_id
    User is user_id
    Group: User can belong to only one group for a given resource
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id = models.CharField(max_length=32, db_index=True)
    resource_id = models.CharField(max_length=32, db_index=True)
    group = models.ForeignKey(GroupResourcePermissionModel, on_delete=models.CASCADE, db_index=True)
    last_accessed = models.DateTimeField(default=timezone.now, blank=True, null=True)

    objects = ResourceUserGroupManager()

    class Meta:
        unique_together = [['user_id', 'resource_id'],]
        db_table = 'dm_app_authz_resource_group'
