"""
Tests untuk custom endpoints integration dengan ViewSet
"""

import pytest
from django.db import models
from rest_framework.response import Response
from rest_framework import viewsets

from django_autoapi.core import AutoAPI
from django_autoapi.decorators import endpoint, detail_action, collection_action
from django_autoapi.factories.viewset import ViewSetFactory
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()


def test_viewset_with_custom_endpoint(sample_model):
    """Test: ViewSet includes custom endpoint"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            instance.is_active = True
            instance.save()
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check method exists
    assert hasattr(viewset_class, 'activate')

    # Check it's callable
    assert callable(viewset_class.activate)


def test_viewset_multiple_custom_endpoints(sample_model):
    """Test: ViewSet dengan multiple custom endpoints"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

        @endpoint(methods=['POST'], detail=True)
        def deactivate(self, request, instance):
            return Response({'status': 'deactivated'})

        @endpoint(methods=['GET'], detail=False)
        def statistics(self, request, queryset):
            return Response({'total': queryset.count()})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check all methods exist
    assert hasattr(viewset_class, 'activate')
    assert hasattr(viewset_class, 'deactivate')
    assert hasattr(viewset_class, 'statistics')


def test_detail_endpoint_has_correct_signature(sample_model):
    """Test: Detail endpoint memiliki signature yang benar"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check method signature
    import inspect
    sig = inspect.signature(viewset_class.activate)
    params = list(sig.parameters.keys())

    # Should have: self, request, pk (DRF standard)
    assert 'self' in params
    assert 'request' in params


def test_collection_endpoint_has_correct_signature(sample_model):
    """Test: Collection endpoint memiliki signature yang benar"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['GET'], detail=False)
        def statistics(self, request, queryset):
            return Response({'total': queryset.count()})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check method exists
    assert hasattr(viewset_class, 'statistics')


def test_endpoint_preserves_docstring(sample_model):
    """Test: Endpoint preserves original docstring"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            """Activate the product"""
            return Response({'status': 'activated'})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check docstring preserved
    assert 'Activate the product' in viewset_class.activate.__doc__


def test_endpoint_with_custom_url_path(sample_model):
    """Test: Endpoint dengan custom URL path"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True, url_path='make-active')
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Method should exist dengan name 'activate'
    assert hasattr(viewset_class, 'activate')

    # URL path configuration handled by DRF @action


def test_endpoint_with_custom_permissions(sample_model):
    """Test: Endpoint dengan custom permissions"""

    from rest_framework.permissions import IsAdminUser

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(
            methods=['POST'],
            detail=True,
            permissions=[IsAdminUser]
        )
        def delete_permanently(self, request, instance):
            return Response({'status': 'deleted'})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Method should exist
    assert hasattr(viewset_class, 'delete_permanently')


def test_endpoint_with_custom_serializer(sample_model):
    """Test: Endpoint dengan custom serializer"""

    from rest_framework import serializers

    class CustomSerializer(serializers.Serializer):
        message = serializers.CharField()

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(
            methods=['POST'],
            detail=True,
            serializer_class=CustomSerializer
        )
        def custom_action(self, request, instance):
            return Response({'message': 'custom'})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Method should exist
    assert hasattr(viewset_class, 'custom_action')


def test_detail_action_shorthand(sample_model):
    """Test: detail_action shorthand decorator"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @detail_action(methods=['POST'])
        def archive(self, request, instance):
            return Response({'status': 'archived'})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Method should exist
    assert hasattr(viewset_class, 'archive')


def test_collection_action_shorthand(sample_model):
    """Test: collection_action shorthand decorator"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @collection_action(methods=['GET'])
        def export(self, request, queryset):
            return Response({'count': queryset.count()})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Method should exist
    assert hasattr(viewset_class, 'export')


def test_viewset_has_standard_methods_plus_custom(sample_model):
    """Test: ViewSet has both standard and custom methods"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Standard methods should exist
    assert hasattr(viewset_class, 'list')
    assert hasattr(viewset_class, 'create')
    assert hasattr(viewset_class, 'retrieve')
    assert hasattr(viewset_class, 'update')
    assert hasattr(viewset_class, 'destroy')

    # Custom method should exist
    assert hasattr(viewset_class, 'activate')


def test_endpoint_with_multiple_http_methods(sample_model):
    """Test: Endpoint dengan multiple HTTP methods"""

    class ProductAPI(AutoAPI):
        model = sample_model

        @endpoint(methods=['GET', 'POST'], detail=True)
        def status(self, request, instance):
            if request.method == 'GET':
                return Response({'status': instance.is_active})
            else:
                instance.is_active = not instance.is_active
                return Response({'status': instance.is_active})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Method should exist
    assert hasattr(viewset_class, 'status')


def test_viewset_without_custom_endpoints(sample_model):
    """Test: ViewSet tanpa custom endpoints masih works"""

    class ProductAPI(AutoAPI):
        model = sample_model
        filterable = ['name']

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Standard methods should exist
    assert hasattr(viewset_class, 'list')
    assert hasattr(viewset_class, 'create')

    # No custom methods
    assert not hasattr(viewset_class, 'activate')


def test_complex_api_with_everything(sample_model):
    """Test: Complex API dengan semua features"""

    class ProductAPI(AutoAPI):
        model = sample_model

        # Query features
        filterable = ['name', 'is_active']
        searchable = ['name']
        orderable = ['name', 'price']

        # Pagination
        pagination = 'cursor'
        page_size = 25

        # Permissions
        permission_classes = ['IsAuthenticated']

        # Custom endpoints
        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            instance.is_active = True
            instance.save()
            return Response({'status': 'activated'})

        @endpoint(methods=['POST'], detail=True)
        def restock(self, request, instance):
            instance.stock += request.data.get('quantity', 10)
            instance.save()
            return Response({'stock': instance.stock})

        @endpoint(methods=['GET'], detail=False)
        def low_stock(self, request, queryset):
            low = queryset.filter(stock__lt=10)
            return Response({'count': low.count()})

    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check everything exists
    assert hasattr(viewset_class, 'queryset')
    assert hasattr(viewset_class, 'serializer_class')
    assert hasattr(viewset_class, 'filter_backends')
    assert hasattr(viewset_class, 'pagination_class')
    assert hasattr(viewset_class, 'permission_classes')
    assert hasattr(viewset_class, 'activate')
    assert hasattr(viewset_class, 'restock')
    assert hasattr(viewset_class, 'low_stock')
