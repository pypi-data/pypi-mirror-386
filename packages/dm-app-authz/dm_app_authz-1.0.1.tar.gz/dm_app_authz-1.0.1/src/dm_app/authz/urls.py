from django.urls import path
from .views import PermissionApiView

urlpatterns = [
    path('permissions/v1', PermissionApiView.as_view(), name='permissions'),
]