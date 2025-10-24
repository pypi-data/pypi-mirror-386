"""
Test URLs configuration
"""

from django.urls import path, include
from django_autoapi.routers import AutoAPIRouter

# Create router
router = AutoAPIRouter()

# URLs will be populated by tests
urlpatterns = [
    path('api/', include(router.urls)),
]

