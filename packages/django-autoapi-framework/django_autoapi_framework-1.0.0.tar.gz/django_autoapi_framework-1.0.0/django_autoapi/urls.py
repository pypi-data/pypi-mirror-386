"""
AutoAPI URLs - Ready-to-use URL configuration

This module provides pre-configured URL patterns for AutoAPI router.
You can use this directly or customize your own.

Usage Option 1 - Direct include in main urls.py:
    from django.urls import path, include

    urlpatterns = [
        path('api/auto/', include('django_autoapi.urls')),
    ]

Usage Option 2 - Custom router in your urls.py:
    from django_autoapi.routers import AutoAPIRouter
    from apps.academic.autoapi import *  # Import your APIs

    router = AutoAPIRouter()
    router.autodiscover()  # Auto-register all APIs

    urlpatterns = [
        path('api/', include(router.urls)),
    ]
"""

from django.urls import path, include
from .routers import create_router

# Create router with autodiscovery
router = create_router(autodiscover=True)

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# App name for namespacing
app_name = 'autoapi'
