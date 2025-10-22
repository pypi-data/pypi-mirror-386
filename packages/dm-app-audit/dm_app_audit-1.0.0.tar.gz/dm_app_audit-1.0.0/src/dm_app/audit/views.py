from django.conf import settings
from dm_core.meta.decorator import api_inbound_validator
from rest_framework.generics import RetrieveAPIView, ListAPIView
from .models import EventLogModelCd
from .serializers import PermissionParamInputSerializer


class AuditApiView(RetrieveAPIView):
    """
    Retrieve the permissions of a user
    """

    api_id = {
        'GET': '{}.audit.events'.format(settings.SERVICE)
    }
    params_serializer_class = PermissionParamInputSerializer

    def get_object(self):
        return EventLogModelCd.objects.filter(owner_id=self.request.user.user, owner_type=self.request.user.application)

    @api_inbound_validator()
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
