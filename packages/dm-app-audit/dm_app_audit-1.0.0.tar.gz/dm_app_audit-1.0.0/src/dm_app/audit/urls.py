from django.urls import path
from .views import AuditApiView

urlpatterns = [
    path('audit/events/v1', AuditApiView.as_view(), name='audit-events'),
]