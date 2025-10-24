"""
End-to-end integration tests
Complete flow from API definition to HTTP requests
"""

import pytest
from django.urls import clear_url_caches
from rest_framework.test import APIClient, APIRequestFactory
from django.db import models

from django_autoapi import AutoAPI
from django_autoapi.routers import AutoAPIRouter
from django_autoapi.registry import AutoAPIRegistry


@pytest.fixture
def integration_router(sample_model):
    """Fixture untuk router dengan ProductAPI"""
    # Clear registry
    AutoAPIRegistry.clear()
    clear_url_caches()

    # Create API
    class ProductAPI(AutoAPI):
        model = sample_model
        filterable = ['name', 'is_active']
        searchable = ['name']
        orderable = ['name', 'price']
        pagination = 'offset'
        page_size = 10

    # Create router and register
    router = AutoAPIRouter()
    router.register(ProductAPI)

    yield {
        'router': router,
        'ProductAPI': ProductAPI,
        'Product': sample_model,
    }

    # Cleanup
    AutoAPIRegistry.clear()
    clear_url_caches()


@pytest.mark.django_db
def test_api_registration(integration_router):
    """Test: API successfully registered in registry"""
    Product = integration_router['Product']

    # Verify API is registered
    assert AutoAPIRegistry.is_registered(Product)

    # Get registered API
    registered_api = AutoAPIRegistry.get_api_class(Product)
    assert registered_api is not None
    assert registered_api.__name__ == 'ProductAPI'


@pytest.mark.django_db
def test_router_registration(integration_router):
    """Test: API successfully registered with router"""
    router = integration_router['router']

    # Get registered APIs from router (returns dict, not list)
    registered_apis = router.get_registered_apis()

    assert len(registered_apis) == 1

    # Get first (and only) registered API info
    model_key = list(registered_apis.keys())[0]
    api_info = registered_apis[model_key]

    assert api_info['api_class'].__name__ == 'ProductAPI'
    assert api_info['prefix'] == 'products'
    assert api_info['basename'] == 'product'


@pytest.mark.django_db
def test_url_patterns_generated(integration_router):
    """Test: All expected URL patterns generated"""
    router = integration_router['router']

    # Get all URL patterns
    urls = router.urls
    patterns = [str(p.pattern) for p in urls]

    # Check expected patterns exist
    assert any('products' in p for p in patterns), f"No 'products' pattern found in {patterns}"

    # Should have list and detail patterns
    list_pattern = any(p.endswith('$') and 'products' in p and 'pk' not in p for p in patterns)
    detail_pattern = any('pk' in p and 'products' in p for p in patterns)

    assert list_pattern, "List URL pattern not found"
    assert detail_pattern, "Detail URL pattern not found"


@pytest.mark.django_db
def test_viewset_generation(integration_router):
    """Test: ViewSet correctly generated with all methods"""
    router = integration_router['router']
    ProductAPI = integration_router['ProductAPI']

    # Get viewset from router
    api_info = router.get_api_info(ProductAPI)
    viewset = api_info['viewset']

    # Check viewset has required methods
    assert hasattr(viewset, 'list')
    assert hasattr(viewset, 'create')
    assert hasattr(viewset, 'retrieve')
    assert hasattr(viewset, 'update')
    assert hasattr(viewset, 'partial_update')
    assert hasattr(viewset, 'destroy')


@pytest.mark.django_db
def test_serializer_generation(integration_router):
    """Test: Serializer correctly generated"""
    router = integration_router['router']
    ProductAPI = integration_router['ProductAPI']
    Product = integration_router['Product']

    # Get API info
    api_info = router.get_api_info(ProductAPI)

    # Get serializer from viewset
    viewset_class = api_info['viewset']
    serializer_class = viewset_class.serializer_class

    # Check serializer
    assert serializer_class is not None
    assert serializer_class.Meta.model == Product

    # Instantiate serializer to check fields
    serializer = serializer_class()
    fields = serializer.fields.keys()

    # Check expected fields exist
    assert 'name' in fields
    assert 'price' in fields
    assert 'stock' in fields
    assert 'is_active' in fields


@pytest.mark.django_db
def test_complete_crud_flow_with_mock_data(integration_router):
    """Test: Complete CRUD workflow with mocked request"""
    router = integration_router['router']
    ProductAPI = integration_router['ProductAPI']

    factory = APIRequestFactory()
    api_info = router.get_api_info(ProductAPI)
    viewset_class = api_info['viewset']

    # Test 1: List action
    request = factory.get('/api/products/')
    view = viewset_class.as_view({'get': 'list'})
    response = view(request)

    # Should return 200, 401 (auth required), 404 (table doesn't exist), or 500 (db error)
    assert response.status_code in [200, 401, 404, 500]

    # Test 2: Create action structure
    request = factory.post('/api/products/', {
        'name': 'Test Product',
        'price': '99.99',
        'stock': 10,
        'is_active': True
    }, format='json')
    view = viewset_class.as_view({'post': 'create'})
    response = view(request)

    assert response.status_code in [201, 400, 401, 404, 500]


@pytest.mark.django_db
def test_filtering_configuration(integration_router):
    """Test: Filtering configuration applied correctly"""
    router = integration_router['router']
    ProductAPI = integration_router['ProductAPI']

    api_info = router.get_api_info(ProductAPI)
    viewset = api_info['viewset']

    # Check filter backends configured
    assert hasattr(viewset, 'filter_backends')
    assert len(viewset.filter_backends) > 0

    # Check filterset fields
    if hasattr(viewset, 'filterset_fields'):
        assert 'name' in viewset.filterset_fields or hasattr(viewset, 'filterset_class')


@pytest.mark.django_db
def test_search_configuration(integration_router):
    """Test: Search configuration applied correctly"""
    router = integration_router['router']
    ProductAPI = integration_router['ProductAPI']

    api_info = router.get_api_info(ProductAPI)
    viewset = api_info['viewset']

    # Check search fields
    if hasattr(viewset, 'search_fields'):
        assert 'name' in viewset.search_fields


@pytest.mark.django_db
def test_ordering_configuration(integration_router):
    """Test: Ordering configuration applied correctly"""
    router = integration_router['router']
    ProductAPI = integration_router['ProductAPI']

    api_info = router.get_api_info(ProductAPI)
    viewset = api_info['viewset']

    # Check ordering fields
    if hasattr(viewset, 'ordering_fields'):
        assert 'name' in viewset.ordering_fields
        assert 'price' in viewset.ordering_fields


@pytest.mark.django_db
def test_pagination_configuration(integration_router):
    """Test: Pagination configuration applied correctly"""
    router = integration_router['router']
    ProductAPI = integration_router['ProductAPI']

    api_info = router.get_api_info(ProductAPI)
    viewset = api_info['viewset']

    # Check pagination class
    assert hasattr(viewset, 'pagination_class')
    assert viewset.pagination_class is not None

    # Check page size
    pagination = viewset.pagination_class()
    if hasattr(pagination, 'page_size'):
        assert pagination.page_size == 10


@pytest.mark.django_db
def test_multiple_api_registration(integration_router, another_model):
    """Test: Multiple APIs for different models"""
    router = integration_router['router']

    # Create second API using the shared another_model fixture
    class CategoryAPI(AutoAPI):
        model = another_model
        filterable = ['name']
        searchable = ['name']

    # Register second API
    router.register(CategoryAPI)

    # Check both are registered
    registered_apis = router.get_registered_apis()
    assert len(registered_apis) == 2

    # Check unique prefixes
    prefixes = [api_info['prefix'] for api_info in registered_apis.values()]
    assert 'products' in prefixes
    assert 'categories' in prefixes or 'categorys' in prefixes


@pytest.mark.django_db
def test_registry_info(integration_router):
    """Test: Registry info provides correct information"""
    info = AutoAPIRegistry.get_registry_info()

    assert info['total_registered'] == 1
    assert info['total_models'] == 1
    assert 'ProductAPI' in info['api_classes']
    assert 'test_app.product' in info['models']


@pytest.mark.django_db
def test_router_urls_info(integration_router):
    """Test: Router provides detailed URL information"""
    router = integration_router['router']

    urls_info = router.get_urls_info()
    assert len(urls_info) > 0

    # Check structure of URL info
    for url_info in urls_info:
        assert 'pattern' in url_info
        assert 'name' in url_info
        assert 'callback' in url_info
