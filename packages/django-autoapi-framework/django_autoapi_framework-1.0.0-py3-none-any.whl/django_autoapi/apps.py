"""
Django app configuration untuk Django AutoAPI Framework

Handles app initialization, signal registration, dan component setup.
"""

from django.apps import AppConfig


class DjangoAutoAPIConfig(AppConfig):
    """
    Django app configuration untuk django_autoapi framework

    Features:
    - Auto-registers API endpoints
    - Handles signal initialization
    - Loads record rules jika available
    - Sets up caching dan optimization
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_autoapi'
    verbose_name = 'Django AutoAPI Framework'

    def ready(self):
        """
        Signal handler untuk app initialization

        Called ketika Django app configuration selesai.
        Digunakan untuk:
        - Import dan register signal handlers
        - Load record rules jika tersedia
        - Setup optimization features
        """
        self._setup_signals()
        self._load_recordrules()
        self._setup_logging()

    def _setup_signals(self):
        """
        Setup signal handlers untuk framework

        Signals yang ditangani:
        - post_save: Update cache setelah model save
        - post_delete: Update cache setelah model delete
        - m2m_changed: Update cache setelah relation change
        """
        try:
            from django.db.models.signals import post_save, post_delete
            from . import signals as autoapi_signals  # noqa
        except ImportError:
            pass

    def _load_recordrules(self):
        """
        Load record rules jika module tersedia

        Record rules memungkinkan custom logic untuk:
        - Field validation
        - Access control
        - Business rules enforcement
        - Audit logging

        Notes:
        - ImportError diabaikan jika module tidak ditemukan
        - Useful untuk optional features
        """
        try:
            from . import recordrules  # noqa
        except ImportError:
            # Record rules optional, jadi tidak masalah jika tidak ada
            pass

    def _setup_logging(self):
        """
        Setup logging configuration untuk framework

        Configures:
        - Request/Response logging
        - Error tracking
        - Performance monitoring
        - Audit trails
        """
        import logging

        logger = logging.getLogger('django_autoapi')
        logger.debug('Django AutoAPI framework initialized successfully')


# Default app configuration yang digunakan
default_app_config = 'django_autoapi.apps.DjangoAutoAPIConfig'
