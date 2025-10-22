from django.conf import settings
from dm_core.meta.decorator import api_inbound_validator
from rest_framework.generics import RetrieveAPIView, ListAPIView
from dm_app.authz.models import GroupResourcePermissionModel
from .serializers import PermissionParamInputSerializer, GroupResourcePermissionOutputSerializer


class PermissionApiView(RetrieveAPIView):
    """
    Retrieve the permissions of a user

    Invoked by user
    """

    api_id = {
        'GET': '{}.authz.permissions'.format(settings.SERVICE)
    }
    params_serializer_class = PermissionParamInputSerializer

    def get_serializer_context(self):
        return {'resource_type': self.request.user.resource_type}

    def get_object(self):
        # Group ID is set in session and has to be extracted
        try:
            return GroupResourcePermissionModel.objects.get(group_id=self.request.user.group)
        except GroupResourcePermissionModel.DoesNotExist as e:
            return GroupResourcePermissionModel(resource_id=None, permissions=[])

    def get_serializer_class(self, *args, **kwargs):
        return GroupResourcePermissionOutputSerializer

    @api_inbound_validator()
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# TODO: CRUD to create, update, delete and list group resource permissions

# TODO: Add remove users to ResourceUserGroupModel