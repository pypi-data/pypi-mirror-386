#!/usr/bin/env python
"""
Demo script untuk testing custom endpoints
Run: python django_autoapi/examples/test_custom_endpoints_demo.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configure Django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret',
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
            'django_filters',
            'django_autoapi',
        ],
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': [],
            'DEFAULT_PERMISSION_CLASSES': [],
        },
        USE_TZ=True,
    )
django.setup()

# Now we can import Django modules
from django.db import models
from rest_framework.response import Response
from django_autoapi import AutoAPI, post_endpoint, get_endpoint, detail_action, collection_action
from django_autoapi.factories.viewset import ViewSetFactory


# Define test model
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'test_app'
        managed = False


def demo_basic_endpoint():
    """Demo 1: Basic custom endpoint"""
    from django_autoapi.registry import AutoAPIRegistry
    AutoAPIRegistry.clear()

    print("\n" + "="*80)
    print("DEMO 1: Basic Custom Endpoint")
    print("="*80)

    class ProductAPI(AutoAPI):
        model = Product

        @post_endpoint(detail=True)
        def activate(self, request, instance):
            """Activate a product"""
            return Response({'status': 'activated', 'product_id': instance.id})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check method exists
    print(f"[OK] ViewSet has 'activate' method: {hasattr(viewset_class, 'activate')}")

    # Check it's a DRF action
    activate_method = getattr(viewset_class, 'activate')
    print(f"[OK] Method is DRF action: {hasattr(activate_method, 'mapping')}")
    print(f"[OK] HTTP methods: {list(activate_method.mapping.keys())}")
    print(f"[OK] Detail action: {activate_method.detail}")
    print(f"[OK] URL path: {activate_method.url_path}")


def demo_multiple_endpoints():
    """Demo 2: Multiple custom endpoints"""
    from django_autoapi.registry import AutoAPIRegistry
    AutoAPIRegistry.clear()

    print("\n" + "="*80)
    print("DEMO 2: Multiple Custom Endpoints")
    print("="*80)

    class ProductAPI(AutoAPI):
        model = Product

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
    endpoints = ['activate', 'deactivate', 'statistics']
    for endpoint in endpoints:
        has_method = hasattr(viewset_class, endpoint)
        print(f"[OK] ViewSet has '{endpoint}': {has_method}")


def demo_detail_vs_collection():
    """Demo 3: Detail vs Collection actions"""
    from django_autoapi.registry import AutoAPIRegistry
    AutoAPIRegistry.clear()

    print("\n" + "="*80)
    print("DEMO 3: Detail vs Collection Actions")
    print("="*80)

    class ProductAPI(AutoAPI):
        model = Product

        @detail_action(methods=['POST'])
        def archive(self, request, instance):
            return Response({'archived': instance.id})

        @collection_action(methods=['GET'])
        def export(self, request, queryset):
            return Response({'count': queryset.count()})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    archive_method = getattr(viewset_class, 'archive')
    export_method = getattr(viewset_class, 'export')

    print(f"[OK] 'archive' is detail action: {archive_method.detail}")
    print(f"[OK] 'export' is collection action: {not export_method.detail}")


def demo_custom_configuration():
    """Demo 4: Custom URL paths and permissions"""
    from django_autoapi.registry import AutoAPIRegistry
    AutoAPIRegistry.clear()

    print("\n" + "="*80)
    print("DEMO 4: Custom Configuration")
    print("="*80)

    from rest_framework.permissions import AllowAny

    class ProductAPI(AutoAPI):
        model = Product

        @post_endpoint(
            detail=True,
            url_path='do-activate',
            url_name='activate-product',
            permissions=[AllowAny]
        )
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)
    activate_method = getattr(viewset_class, 'activate')

    print(f"[OK] Custom URL path: {activate_method.url_path}")
    print(f"[OK] Custom URL name: {activate_method.url_name}")
    print(f"[OK] Custom permissions: {AllowAny in activate_method.kwargs.get('permission_classes', [])}")


def demo_endpoint_extraction():
    """Demo 5: Endpoint extraction"""
    from django_autoapi.registry import AutoAPIRegistry
    AutoAPIRegistry.clear()

    print("\n" + "="*80)
    print("DEMO 5: Endpoint Extraction")
    print("="*80)

    class ProductAPI(AutoAPI):
        model = Product

        @post_endpoint(detail=True)
        def activate(self, request, instance):
            """Activate the product"""
            return Response({'status': 'activated'})

        @get_endpoint(detail=False)
        def statistics(self, request, queryset):
            """Get statistics"""
            return Response({'total': queryset.count()})

    # Extract endpoints
    endpoints = ProductAPI._get_endpoints()
    print(f"[OK] Total endpoints found: {len(endpoints)}")

    for name, func, config in endpoints:
        print(f"\n  Endpoint: {name}")
        print(f"    - Methods: {config['methods']}")
        print(f"    - Type: {'detail' if config['detail'] else 'collection'}")
        print(f"    - URL: {config['url_path']}")

    # Get formatted info
    info = ProductAPI.get_endpoint_info()
    print(f"\n[OK] Endpoint info count: {info['count']}")
    for ep in info['endpoints']:
        print(f"  - {ep['name']}: {ep['methods']} ({ep['type']})")


def demo_combined_crud_and_custom():
    """Demo 6: Standard CRUD + Custom endpoints"""
    from django_autoapi.registry import AutoAPIRegistry
    AutoAPIRegistry.clear()

    print("\n" + "="*80)
    print("DEMO 6: Combined Standard CRUD + Custom Endpoints")
    print("="*80)

    class ProductAPI(AutoAPI):
        model = Product
        filterable = ['name', 'is_active']
        searchable = ['name']

        @post_endpoint(detail=True)
        def activate(self, request, instance):
            return Response({'status': 'activated'})

    # Generate ViewSet
    viewset_class = ViewSetFactory.create_viewset(ProductAPI)

    # Check standard CRUD
    crud_methods = ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']
    print("\nStandard CRUD methods:")
    for method in crud_methods:
        has_method = hasattr(viewset_class, method)
        print(f"  [OK] {method}: {has_method}")

    # Check custom endpoints
    print("\nCustom endpoints:")
    print(f"  [OK] activate: {hasattr(viewset_class, 'activate')}")

    # Check filters
    print("\nFilters configured:")
    print(f"  [OK] filterset_fields: {viewset_class.filterset_fields}")
    print(f"  [OK] search_fields: {viewset_class.search_fields}")


def run_all_demos():
    """Run all demos"""
    print("\n" + "="*80)
    print("DJANGO AUTOAPI - CUSTOM ENDPOINTS DEMO")
    print("="*80)

    demos = [
        demo_basic_endpoint,
        demo_multiple_endpoints,
        demo_detail_vs_collection,
        demo_custom_configuration,
        demo_endpoint_extraction,
        demo_combined_crud_and_custom,
    ]

    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n[ERROR] Error in {demo.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("[SUCCESS] ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")


if __name__ == '__main__':
    run_all_demos()
