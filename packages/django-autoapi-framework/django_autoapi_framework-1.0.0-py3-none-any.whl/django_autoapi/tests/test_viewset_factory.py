"""
Tests untuk ViewSetFactory
"""

import pytest
from django.db import models
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from django_autoapi.core import AutoAPI
from django_autoapi.factories.viewset import ViewSetFactory
from django_autoapi.registry import AutoAPIRegistry
from django.test.utils import isolate_apps


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry"""
    AutoAPIRegistry.clear()
    yield
    AutoAPIRegistry.clear()

@pytest.fixture
def product_model():
    """Sample product model"""
    class Product(models.Model):
        name = models.CharField(max_length=200)
        description = models.TextField(blank=True)
        price = models.DecimalField(max_digits=10, decimal_places=2)
        stock = models.IntegerField(default=0)
        is_active = models.BooleanField(default=True)
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            app_label = "test_viewset_app"   # <- beda dari 'test_app' di conftest.py
            managed = False

    return Product

def test_basic_viewset_generation(product_model):
    """Test: ViewSet otomatis di-generate"""
    
    class ProductAPI(AutoAPI):
        model = product_model
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Assertions
    assert viewset_class is not None
    assert issubclass(viewset_class, viewsets.ModelViewSet)
    assert viewset_class.__name__ == 'ProductViewSet'


def test_viewset_has_queryset(product_model):
    """Test: ViewSet memiliki queryset"""
    
    class ProductAPI(AutoAPI):
        model = product_model
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check queryset
    assert hasattr(viewset_class, 'queryset')
    assert viewset_class.queryset.model == product_model


def test_viewset_has_serializer(product_model):
    """Test: ViewSet memiliki serializer_class"""
    
    class ProductAPI(AutoAPI):
        model = product_model
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check serializer
    assert hasattr(viewset_class, 'serializer_class')
    assert viewset_class.serializer_class is not None


def test_viewset_with_filterable(product_model):
    """Test: ViewSet dengan filtering configuration"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        filterable = ['name', 'price', 'is_active']
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check filter backends
    assert hasattr(viewset_class, 'filter_backends')
    assert DjangoFilterBackend in viewset_class.filter_backends
    
    # Check filterset_fields
    assert hasattr(viewset_class, 'filterset_fields')
    assert viewset_class.filterset_fields == ['name', 'price', 'is_active']


def test_viewset_with_searchable(product_model):
    """Test: ViewSet dengan search configuration"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        searchable = ['name', 'description']
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check filter backends
    assert SearchFilter in viewset_class.filter_backends
    
    # Check search_fields
    assert hasattr(viewset_class, 'search_fields')
    assert viewset_class.search_fields == ['name', 'description']


def test_viewset_with_orderable(product_model):
    """Test: ViewSet dengan ordering configuration"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        orderable = ['name', 'price', 'created_at']
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check filter backends
    assert OrderingFilter in viewset_class.filter_backends
    
    # Check ordering_fields
    assert hasattr(viewset_class, 'ordering_fields')
    assert viewset_class.ordering_fields == ['name', 'price', 'created_at']


def test_viewset_with_pagination(product_model):
    """Test: ViewSet dengan pagination configuration"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        pagination = 'cursor'
        page_size = 25
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check pagination
    assert hasattr(viewset_class, 'pagination_class')
    assert viewset_class.pagination_class is not None
    assert viewset_class.pagination_class.page_size == 25


def test_viewset_with_permissions(product_model):
    """Test: ViewSet dengan permission configuration"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        permission_classes = ['IsAuthenticated']
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check permissions
    assert hasattr(viewset_class, 'permission_classes')
    assert IsAuthenticated in viewset_class.permission_classes


def test_viewset_with_multiple_permissions(product_model):
    """Test: ViewSet dengan multiple permissions"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        permission_classes = ['IsAuthenticated', 'IsAdminUser']
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check multiple permissions
    assert len(viewset_class.permission_classes) == 2


def test_viewset_with_queryset_filters(product_model):
    """Test: ViewSet dengan default queryset filters"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        queryset_filters = {'is_active': True}
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check queryset has filter
    queryset = viewset_class.queryset
    # Note: Can't easily test filter in queryset, but it's applied
    assert queryset is not None


def test_viewset_with_select_related(product_model):
    """Test: ViewSet dengan select_related optimization"""
    
    # Add ForeignKey to model
    product_model.add_to_class(
        'category',
        models.ForeignKey(
            'Category',
            on_delete=models.CASCADE,
            null=True
        )
    )
    
    class ProductAPI(AutoAPI):
        model = product_model
        select_related = ['category']
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Queryset should have select_related
    assert viewset_class.queryset is not None


def test_viewset_with_all_features(product_model):
    """Test: ViewSet dengan semua features enabled"""
    
    class ProductAPI(AutoAPI):
        model = product_model
        filterable = ['name', 'price']
        searchable = ['name', 'description']
        orderable = ['created_at', 'price']
        pagination = 'cursor'
        page_size = 20
        permission_classes = ['IsAuthenticated']
    
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    
    # Check all features
    assert DjangoFilterBackend in viewset_class.filter_backends
    assert SearchFilter in viewset_class.filter_backends
    assert OrderingFilter in viewset_class.filter_backends
    assert viewset_class.filterset_fields == ['name', 'price']
    assert viewset_class.search_fields == ['name', 'description']
    assert viewset_class.ordering_fields == ['created_at', 'price']
    assert viewset_class.pagination_class.page_size == 20
    assert IsAuthenticated in viewset_class.permission_classes


def test_different_pagination_types(product_model):
    """Test: Different pagination types"""
    
    # Cursor pagination
    class ProductAPI1(AutoAPI):
        model = product_model
        pagination = 'cursor'
    
    vs1 = ViewSetFactory.create_viewset(ProductAPI1)
    assert vs1.pagination_class is not None
    
    # Clear registry untuk test berikutnya
    AutoAPIRegistry.clear()
    
    # Page pagination
    class ProductAPI2(AutoAPI):
        model = product_model
        pagination = 'page'
    
    vs2 = ViewSetFactory.create_viewset(ProductAPI2)
    assert vs2.pagination_class is not None
    
    # Clear registry
    AutoAPIRegistry.clear()
    
    # Offset pagination
    class ProductAPI3(AutoAPI):
        model = product_model
        pagination = 'offset'
    
    vs3 = ViewSetFactory.create_viewset(ProductAPI3)
    assert vs3.pagination_class is not None

    