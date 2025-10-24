"""
Pytest configuration untuk testing framework
"""

import os
import sys

# Configure Django settings BEFORE any imports
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key-for-testing',

        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },

        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
            'django_filters',
            'django_autoapi',
        ],

        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
        ],

        ROOT_URLCONF='django_autoapi.tests.urls',

        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': [],
            'DEFAULT_PERMISSION_CLASSES': [],
            'TEST_REQUEST_DEFAULT_FORMAT': 'json',
        },

        USE_TZ=True,
    )
    django.setup()

# NOW we can import pytest and other modules
import pytest
from django.db import models


def pytest_configure():
    """Configure Django settings before running tests"""
    # Settings already configured above
    pass


@pytest.fixture(autouse=True)
def cleanup_registry():
    """
    Fixture untuk membersihkan registry dan cache sebelum setiap test
    autouse=True berarti fixture ini akan dijalankan otomatis untuk setiap test
    """
    from django_autoapi.registry import AutoAPIRegistry
    from django_autoapi.recordrules.registry import RecordRuleRegistry
    from django.core.cache import cache

    # Clear AutoAPI registry sebelum test
    AutoAPIRegistry.clear()

    # Clear RecordRule cache sebelum test (important for transaction=True tests)
    RecordRuleRegistry.invalidate()

    # Clear all caches
    cache.clear()

    yield  # Test akan dijalankan di sini

    # Clear registry setelah test (cleanup)
    AutoAPIRegistry.clear()
    RecordRuleRegistry.invalidate()
    cache.clear()


@pytest.fixture(scope='session')
def sample_model():
    """
    Fixture untuk model testing.

    Returns a Product model with common fields for testing.
    Model is marked as managed=False to prevent Django from creating tables.

    Note: Using scope='session' to prevent model conflicts when running multiple tests.
    """
    # Import at function level to avoid early import issues
    from django.db import models

    # Check if model already exists to prevent re-registration
    from django.apps import apps
    try:
        # Try to get existing model
        return apps.get_model('test_app', 'Product')
    except LookupError:
        # Model doesn't exist, create it
        pass

    class Product(models.Model):
        name = models.CharField(max_length=200)
        description = models.TextField(blank=True)
        price = models.DecimalField(max_digits=10, decimal_places=2)
        stock = models.IntegerField(default=0)
        is_active = models.BooleanField(default=True)
        status = models.CharField(max_length=20, default='active')  # Added for validation tests
        unit_id = models.IntegerField(default=0)  # Added for RecordRule tests
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        def can_activate(self):
            """Check if product can be activated (for validation tests)"""
            return self.stock > 0

        class Meta:
            app_label = 'test_app'
            managed = True  # Allow Django to create/manage the table for testing
            db_table = 'test_product'

    return Product


@pytest.fixture(scope='session')
def another_model():
    """
    Fixture untuk second model testing (Category).

    Returns a Category model for testing multiple APIs.
    Model is marked as managed=False to prevent Django from creating tables.

    Note: Using scope='session' to prevent model conflicts when running multiple tests.
    """
    from django.db import models
    from django.apps import apps

    # Check if model already exists to prevent re-registration
    try:
        return apps.get_model('test_app', 'Category')
    except LookupError:
        pass

    class Category(models.Model):
        name = models.CharField(max_length=200)

        class Meta:
            app_label = 'test_app'
            managed = True  # Allow Django to create/manage the table for testing
            db_table = 'test_category'

    return Category

