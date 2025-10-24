"""
Factory untuk auto-generate DRF ViewSets dari AutoAPI class.

Enhanced dengan Record Rules support untuk row-level security.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializer import SerializerFactory


class ViewSetFactory:
    """
    Factory untuk membuat ViewSet secara otomatis

    Enhanced dengan Record Rules support untuk row-level security.
    """

    @staticmethod
    def create_viewset(api_class):
        """
        Buat ModelViewSet dari AutoAPI class

        Mendukung Record Rules untuk filtering data berdasarkan
        user, group, dan domain filter yang dikonfigurasi.
        """

        model = api_class.model

        # Build ViewSet attributes
        attrs = {}

        # 1. Queryset
        attrs['queryset'] = ViewSetFactory._build_queryset(api_class, model)

        # 2. Serializer
        attrs['serializer_class'] = SerializerFactory.create_serializer(api_class)

        # 3. Filter backends
        filter_backends = ViewSetFactory._build_filter_backends(api_class)
        if filter_backends:
            attrs['filter_backends'] = filter_backends

        # 4. Filterset fields
        filterable = getattr(api_class, 'filterable', None)
        if filterable:
            attrs['filterset_fields'] = filterable

        # 5. Search fields
        searchable = getattr(api_class, 'searchable', None)
        if searchable:
            attrs['search_fields'] = searchable

        # 6. Ordering fields
        orderable = getattr(api_class, 'orderable', None)
        if orderable:
            attrs['ordering_fields'] = orderable
            # Set default ordering if specified
            if getattr(api_class, 'ordering', None):
                attrs['ordering'] = getattr(api_class, 'ordering')

        # 7. Pagination
        pagination_class = ViewSetFactory._build_pagination_class(api_class)
        if pagination_class:
            attrs['pagination_class'] = pagination_class

        # 8. Permissions
        permission_classes = ViewSetFactory._build_permission_classes(api_class)
        if permission_classes:
            attrs['permission_classes'] = permission_classes

        # 9. Authentication classes - use CustomJWTAuthentication
        try:
            from api.common.authentication import CustomJWTAuthentication
            attrs['authentication_classes'] = [CustomJWTAuthentication]
        except ImportError:
            pass  # Fallback to default

        # 10. Record Rules (NEW) ⭐
        # Enable record rules filtering jika dikonfigurasi
        if getattr(api_class, 'enable_record_rules', False):
            attrs['enable_record_rules'] = True

        # 11. Custom endpoints
        custom_endpoints = ViewSetFactory._build_custom_endpoints(api_class)
        attrs.update(custom_endpoints)

        # Determine base classes
        base_classes = ViewSetFactory._get_base_classes(api_class)

        # Create ViewSet class dynamically
        viewset_name = f'{model.__name__}ViewSet'
        viewset_class = type(
            viewset_name,
            base_classes,
            attrs
        )
        return viewset_class

    @staticmethod
    def _get_base_classes(api_class):
        """
        Tentukan base classes untuk ViewSet

        Jika record rules enabled, tambahkan RecordRuleQuerySetMixin
        untuk filtering row-level.

        Args:
            api_class: AutoAPI class

        Returns:
            tuple: Base classes untuk ViewSet
        """
        # Start with ModelViewSet
        bases = [viewsets.ModelViewSet]

        # Add RecordRuleMixin if enabled
        if getattr(api_class, 'enable_record_rules', False):
            try:
                from ..recordrules.mixins import RecordRuleQuerySetMixin
                bases.insert(0, RecordRuleQuerySetMixin)
            except ImportError:
                pass  # Fallback jika mixin tidak tersedia

        return tuple(bases)

    @staticmethod
    def _build_queryset(api_class, model):
        """
        Build queryset untuk ViewSet
        """
        # Base queryset
        queryset = model.objects.all()

        # Apply default filters if specified
        if getattr(api_class, 'queryset_filters', None):
            queryset = queryset.filter(**api_class.queryset_filters)

        # Optimization: select_related
        if getattr(api_class, 'select_related', None):
            queryset = queryset.select_related(*api_class.select_related)

        # Optimization: prefetch_related
        if getattr(api_class, 'prefetch_related', None):
            queryset = queryset.prefetch_related(*api_class.prefetch_related)

        return queryset

    @staticmethod
    def _build_filter_backends(api_class):
        """
        Build filter backends berdasarkan configuration
        """
        # Lazy import semua backend filter
        from rest_framework.filters import SearchFilter, OrderingFilter
        try:
            # django_filters opsional; hanya dipakai jika ada filterable
            from django_filters.rest_framework import DjangoFilterBackend
        except Exception:
            DjangoFilterBackend = None

        backends = []

        if getattr(api_class, 'filterable', None) and DjangoFilterBackend is not None:
            backends.append(DjangoFilterBackend)

        if getattr(api_class, 'searchable', None):
            backends.append(SearchFilter)

        if getattr(api_class, 'orderable', None):
            backends.append(OrderingFilter)

        return backends if backends else None

    @staticmethod
    def _build_pagination_class(api_class):
        """
        Build pagination class berdasarkan configuration
        """
        # Lazy import DRF pagination
        from rest_framework.pagination import (
            PageNumberPagination,
            LimitOffsetPagination,
            CursorPagination
        )

        pagination_map = {
            'page': PageNumberPagination,
            'offset': LimitOffsetPagination,
            'cursor': CursorPagination,
        }

        pagination_type = getattr(api_class, 'pagination', None)
        if not pagination_type:
            return None

        base_pagination_class = pagination_map.get(pagination_type)
        if not base_pagination_class:
            return None

        page_size = getattr(api_class, 'page_size', 50)

        class CustomPagination(base_pagination_class):
            pass

        # Common
        CustomPagination.page_size = page_size

        if pagination_type == 'page':
            CustomPagination.page_size_query_param = 'page_size'
            CustomPagination.max_page_size = getattr(api_class, 'max_page_size', 1000)
        elif pagination_type == 'offset':
            CustomPagination.default_limit = page_size
            CustomPagination.max_limit = getattr(api_class, 'max_page_size', 1000)
        elif pagination_type == 'cursor':
            CustomPagination.ordering = getattr(api_class, 'ordering', '-created_at')

        return CustomPagination

    @staticmethod
    def _build_permission_classes(api_class):
        """
        Build permission classes dari configuration
        """
        # Lazy import DRF permissions
        from rest_framework.permissions import (
            IsAuthenticated,
            IsAuthenticatedOrReadOnly,
            AllowAny,
            IsAdminUser,
        )

        permission_map = {
            'IsAuthenticated': IsAuthenticated,
            'IsAuthenticatedOrReadOnly': IsAuthenticatedOrReadOnly,
            'AllowAny': AllowAny,
            'IsAdminUser': IsAdminUser,
        }

        permission_classes = []
        perms = getattr(api_class, 'permission_classes', ['IsAuthenticated'])

        for perm in perms:
            if isinstance(perm, str):
                perm_class = permission_map.get(perm)
                if perm_class:
                    permission_classes.append(perm_class)
            else:
                # Asumsikan sudah berupa class permission
                permission_classes.append(perm)

        return permission_classes or [IsAuthenticated]

    @staticmethod
    def _build_custom_endpoints(api_class):
        """
        Build custom endpoint methods untuk ViewSet

        Args:
            api_class: AutoAPI class

        Returns:
            dict: Dictionary of method_name -> method_function
        """
        custom_methods = {}

        # Get all endpoints dari API class
        endpoints = api_class._get_endpoints()

        for method_name, method_func, config in endpoints:
            # Create ViewSet action method
            viewset_method = ViewSetFactory._create_viewset_action(
                method_name,
                method_func,
                config,
                api_class
            )

            custom_methods[method_name] = viewset_method

        return custom_methods

    @staticmethod
    def _create_viewset_action(method_name, original_func, config, api_class):
        """
        Create ViewSet action method dari endpoint function

        Enhanced dengan serializer integration dan context support

        Args:
            method_name: Name of the method
            original_func: Original decorated function
            config: Endpoint configuration
            api_class: AutoAPI class

        Returns:
            Decorated method untuk ViewSet
        """
        # Extract config
        methods = config['methods']
        detail = config['detail']
        url_path = config['url_path']
        url_name = config['url_name']

        # Build action decorator kwargs
        action_kwargs = {
            'detail': detail,
            'methods': [m.lower() for m in methods],
            'url_path': url_path,
            'url_name': url_name,
        }

        # Add permission_classes if specified
        if config.get('permissions'):
            action_kwargs['permission_classes'] = config['permissions']

        # Add serializer_class if specified
        if config.get('serializer_class'):
            action_kwargs['serializer_class'] = config['serializer_class']

        # Create wrapper function dengan enhanced features
        def viewset_action_method(self, request, pk=None):
            """
            Enhanced wrapper dengan serializer support

            Automatically injects correct parameters based on detail/collection
            Supports custom serializer_class per endpoint
            """
            # Get custom serializer if specified
            custom_serializer = config.get('serializer_class')

            # Temporarily override get_serializer_class if custom serializer specified
            original_get_serializer = None
            if custom_serializer:
                original_get_serializer = self.get_serializer_class
                self.get_serializer_class = lambda: custom_serializer

            try:
                if detail:
                    # Detail action - get instance
                    instance = self.get_object()

                    # Call original function dengan instance
                    result = original_func(self, request, instance)
                else:
                    # Collection action - get queryset
                    queryset = self.filter_queryset(self.get_queryset())

                    # Call original function dengan queryset
                    result = original_func(self, request, queryset)

                return result

            finally:
                # Restore original get_serializer_class
                if custom_serializer and original_get_serializer:
                    self.get_serializer_class = original_get_serializer

        # Set function name dan docstring
        viewset_action_method.__name__ = method_name
        viewset_action_method.__doc__ = original_func.__doc__

        # Apply DRF @action decorator
        decorated_method = action(**action_kwargs)(viewset_action_method)

        return decorated_method


# Convenience function
def get_viewset_for_model(model, api_class=None):
    """
    Helper function untuk get viewset dari model
    """
    if api_class:
        return ViewSetFactory.create_viewset(api_class)

    # Lazy import AutoAPI agar tidak memicu import-time side effects
    from django_autoapi.core import AutoAPI

    class TempAPI(AutoAPI):
        pass

    TempAPI.model = model
    return ViewSetFactory.create_viewset(TempAPI)

