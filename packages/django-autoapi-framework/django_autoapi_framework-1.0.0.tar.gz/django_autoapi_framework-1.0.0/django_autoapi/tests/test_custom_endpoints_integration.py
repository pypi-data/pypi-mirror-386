"""
Tests untuk custom endpoints integration dengan ViewSet
"""

import pytest
from django.db import models
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from django_autoapi.core import AutoAPI
from django_autoapi.decorators import endpoint, get_endpoint, post_endpoint, detail_action, collection_action
from django_autoapi.factories.viewset import ViewSetFactory
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


def test_viewset_includes_custom_endpoint(sample_model):
    """Test: ViewSet includes custom endpoints from API class"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check that activate method exists
    assert hasattr(viewset_class, 'activate')

    # Check that it's decorated as DRF action
    activate_method = getattr(viewset_class, 'activate')
    assert hasattr(activate_method, 'mapping')  # DRF action has mapping attribute


def test_viewset_multiple_custom_endpoints(sample_model):
    """Test: ViewSet includes multiple custom endpoints"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @post_endpoint(detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

        @post_endpoint(detail=True)
        def deactivate(self, request, instance):
            return Response({'status': 'deactivated'})

        @get_endpoint(detail=False)
        def statistics(self, request, queryset):
            return Response({'total': queryset.count()})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check all methods exist
    assert hasattr(viewset_class, 'activate')
    assert hasattr(viewset_class, 'deactivate')
    assert hasattr(viewset_class, 'statistics')


def test_detail_action_configuration(sample_model):
    """Test: Detail action is configured correctly"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @detail_action(methods=['POST'])
        def archive(self, request, instance):
            return Response({'status': 'archived'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action method
    archive_method = getattr(viewset_class, 'archive')

    # Check detail=True
    assert archive_method.detail is True

    # Check methods
    assert 'post' in archive_method.mapping


def test_collection_action_configuration(sample_model):
    """Test: Collection action is configured correctly"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @collection_action(methods=['GET'])
        def export(self, request, queryset):
            return Response({'count': queryset.count()})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action method
    export_method = getattr(viewset_class, 'export')

    # Check detail=False
    assert export_method.detail is False

    # Check methods
    assert 'get' in export_method.mapping


def test_custom_url_path_and_name(sample_model):
    """Test: Custom url_path and url_name are applied"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(
            methods=['POST'],
            detail=True,
            url_path='do-activate',
            url_name='activate-product'
        )
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action method
    activate_method = getattr(viewset_class, 'activate')

    # Check url_path
    assert activate_method.url_path == 'do-activate'

    # Check url_name
    assert activate_method.url_name == 'activate-product'


def test_endpoint_with_custom_permissions(sample_model):
    """Test: Custom permissions are applied to endpoint"""
    from rest_framework.permissions import AllowAny

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(
            methods=['GET'],
            detail=False,
            permissions=[AllowAny]
        )
        def public_stats(self, request, queryset):
            return Response({'total': queryset.count()})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action method
    public_stats_method = getattr(viewset_class, 'public_stats')

    # Check permission_classes
    assert hasattr(public_stats_method, 'kwargs')
    assert AllowAny in public_stats_method.kwargs.get('permission_classes', [])


def test_endpoint_with_custom_serializer(sample_model):
    """Test: Custom serializer is applied to endpoint"""
    from rest_framework import serializers

    class CustomSerializer(serializers.Serializer):
        status = serializers.CharField()

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(
            methods=['POST'],
            detail=True,
            serializer_class=CustomSerializer
        )
        def special_action(self, request, instance):
            return Response({'status': 'ok'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action method
    special_action_method = getattr(viewset_class, 'special_action')

    # Check serializer_class
    assert hasattr(special_action_method, 'kwargs')
    assert special_action_method.kwargs.get('serializer_class') == CustomSerializer


def test_endpoint_preserves_method_metadata(sample_model):
    """Test: Endpoint preserves function name and docstring"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            """Activate the product"""
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action method
    activate_method = getattr(viewset_class, 'activate')

    # Check name is preserved
    assert activate_method.__name__ == 'activate'

    # Check docstring is preserved
    assert 'Activate the product' in activate_method.__doc__


def test_viewset_without_custom_endpoints(sample_model):
    """Test: ViewSet works fine without custom endpoints"""

    class ProductAPI(AutoAPI):
        model = sample_model
        filterable = ['name']
        searchable = ['name']

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Should have standard CRUD methods
    assert hasattr(viewset_class, 'list')
    assert hasattr(viewset_class, 'retrieve')
    assert hasattr(viewset_class, 'create')
    assert hasattr(viewset_class, 'update')
    assert hasattr(viewset_class, 'destroy')


def test_combined_standard_and_custom_endpoints(sample_model):
    """Test: ViewSet has both standard CRUD and custom endpoints"""

    class ProductAPI(AutoAPI):
        model = sample_model
        filterable = ['name']

        @post_endpoint(detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check standard CRUD methods exist
    assert hasattr(viewset_class, 'list')
    assert hasattr(viewset_class, 'retrieve')
    assert hasattr(viewset_class, 'create')

    # Check custom endpoint exists
    assert hasattr(viewset_class, 'activate')


def test_endpoint_methods_case_insensitive(sample_model):
    """Test: HTTP methods are converted to lowercase for DRF"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST', 'PUT'], detail=True)
        def update_status(self, request, instance):
            return Response({'status': 'updated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action method
    update_status_method = getattr(viewset_class, 'update_status')

    # Check methods are lowercase
    assert 'post' in update_status_method.mapping
    assert 'put' in update_status_method.mapping


def test_shorthand_decorators_integration(sample_model):
    """Test: Shorthand decorators (@get_endpoint, @post_endpoint) work"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @get_endpoint(detail=True)
        def status(self, request, instance):
            return Response({'is_active': instance.is_active})

        @post_endpoint(detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Get action methods
    status_method = getattr(viewset_class, 'status')
    activate_method = getattr(viewset_class, 'activate')

    # Check correct HTTP methods
    assert 'get' in status_method.mapping
    assert 'post' in activate_method.mapping
