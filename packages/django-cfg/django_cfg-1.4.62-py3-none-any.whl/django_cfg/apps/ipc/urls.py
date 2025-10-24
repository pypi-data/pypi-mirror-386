"""
URL patterns for IPC/RPC module.

Public API endpoints for RPC monitoring and testing using DRF router.
"""

from django.urls import include, path
from rest_framework import routers

from .views.monitoring import RPCMonitorViewSet
from .views.testing import RPCTestingViewSet

app_name = 'django_cfg_ipc'

# Create router
router = routers.DefaultRouter()
router.register(r'monitor', RPCMonitorViewSet, basename='monitor')
router.register(r'test', RPCTestingViewSet, basename='test')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]
