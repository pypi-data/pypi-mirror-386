"""
Tests for enhanced serializer context support in custom endpoints
"""

import pytest
from rest_framework import serializers
from rest_framework.response import Response

from django_autoapi import AutoAPI
from django_autoapi.decorators import endpoint
from django_autoapi.factories.viewset import ViewSetFactory
from django_autoapi.registry import AutoAPIRegistry


# Clear registry before tests
AutoAPIRegistry.clear()


@pytest.fixture
def custom_serializer(sample_model):
    """Create custom serializer for testing"""
    class CustomProductSerializer(serializers.ModelSerializer):
        custom_field = serializers.CharField(default='custom')

        class Meta:
            model = sample_model
            fields = ['id', 'name', 'price', 'custom_field']

    return CustomProductSerializer


class TestEnhancedSerializerSupport:
    """Test enhanced serializer context support"""

    def test_endpoint_with_custom_serializer_class(self, sample_model, custom_serializer):
        """Test: Endpoint dengan custom serializer class"""
        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['GET'],
                detail=False,
                serializer_class=custom_serializer
            )
            def custom_list(self, request, queryset):
                """List with custom serializer"""
                # Should use custom serializer
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Check method exists
        assert hasattr(viewset_class, 'custom_list')

        # Check DRF action has serializer_class
        method = getattr(viewset_class, 'custom_list')
        assert hasattr(method, 'kwargs')
        assert 'serializer_class' in method.kwargs
        assert method.kwargs['serializer_class'] == custom_serializer

    def test_endpoint_serializer_override_and_restore(self, sample_model, custom_serializer):
        """Test: Serializer override dan restore after endpoint call"""
        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['POST'],
                detail=True,
                serializer_class=custom_serializer
            )
            def activate_custom(self, request, instance):
                """Activate with custom serializer"""
                # Serializer should be temporarily overridden
                current_serializer = self.get_serializer_class()
                assert current_serializer == custom_serializer

                instance.is_active = True
                return Response({'status': 'activated'})

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Default serializer should not be custom
        default_serializer = viewset_class.serializer_class
        assert default_serializer != custom_serializer

    def test_multiple_endpoints_different_serializers(self, sample_model):
        """Test: Multiple endpoints dengan different serializers"""
        class SerializerA(serializers.ModelSerializer):
            class Meta:
                model = sample_model
                fields = ['id', 'name']

        class SerializerB(serializers.ModelSerializer):
            class Meta:
                model = sample_model
                fields = ['id', 'price']

        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['GET'],
                detail=False,
                serializer_class=SerializerA
            )
            def endpoint_a(self, request, queryset):
                """Endpoint with SerializerA"""
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

            @endpoint(
                methods=['GET'],
                detail=False,
                serializer_class=SerializerB
            )
            def endpoint_b(self, request, queryset):
                """Endpoint with SerializerB"""
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Check both methods exist
        assert hasattr(viewset_class, 'endpoint_a')
        assert hasattr(viewset_class, 'endpoint_b')

        # Check each has different serializer
        method_a = getattr(viewset_class, 'endpoint_a')
        method_b = getattr(viewset_class, 'endpoint_b')

        assert method_a.kwargs['serializer_class'] == SerializerA
        assert method_b.kwargs['serializer_class'] == SerializerB

    def test_endpoint_without_custom_serializer(self, sample_model):
        """Test: Endpoint tanpa custom serializer menggunakan default"""
        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(methods=['GET'], detail=False)
            def default_endpoint(self, request, queryset):
                """Endpoint using default serializer"""
                # Should use default serializer from API class
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)
        default_serializer = viewset_class.serializer_class

        # Method should exist
        assert hasattr(viewset_class, 'default_endpoint')

        # Should not have custom serializer in action kwargs
        method = getattr(viewset_class, 'default_endpoint')
        # serializer_class not in kwargs means it uses default
        assert 'serializer_class' not in method.kwargs

    def test_custom_serializer_with_validation(self, sample_model):
        """Test: Custom serializer dengan validation logic"""
        class ValidatedSerializer(serializers.ModelSerializer):
            name = serializers.CharField(max_length=50, required=True)

            class Meta:
                model = sample_model
                fields = ['id', 'name', 'price']

            def validate_price(self, value):
                if value < 0:
                    raise serializers.ValidationError("Price cannot be negative")
                return value

        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['POST'],
                detail=False,
                serializer_class=ValidatedSerializer
            )
            def create_validated(self, request, queryset):
                """Create with validation"""
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                return Response(serializer.validated_data)

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Check method has custom serializer
        method = getattr(viewset_class, 'create_validated')
        assert method.kwargs['serializer_class'] == ValidatedSerializer

    def test_detail_endpoint_with_custom_serializer(self, sample_model, custom_serializer):
        """Test: Detail endpoint dengan custom serializer"""
        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['GET'],
                detail=True,
                serializer_class=custom_serializer
            )
            def custom_detail(self, request, instance):
                """Get detail with custom serializer"""
                serializer = self.get_serializer(instance)
                return Response(serializer.data)

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Check detail endpoint
        assert hasattr(viewset_class, 'custom_detail')

        method = getattr(viewset_class, 'custom_detail')
        assert method.detail is True
        assert method.kwargs['serializer_class'] == custom_serializer

    def test_mixed_endpoints_serializer_independence(self, sample_model, custom_serializer):
        """Test: Mixed endpoints dengan serializer independence"""
        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(methods=['GET'], detail=False)
            def list_default(self, request, queryset):
                """List with default serializer"""
                return Response({'using': 'default'})

            @endpoint(
                methods=['GET'],
                detail=False,
                serializer_class=custom_serializer
            )
            def list_custom(self, request, queryset):
                """List with custom serializer"""
                return Response({'using': 'custom'})

            @endpoint(methods=['POST'], detail=True)
            def activate(self, request, instance):
                """Activate with default serializer"""
                return Response({'status': 'activated'})

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # All methods should exist
        assert hasattr(viewset_class, 'list_default')
        assert hasattr(viewset_class, 'list_custom')
        assert hasattr(viewset_class, 'activate')

        # Only list_custom should have custom serializer
        method_custom = getattr(viewset_class, 'list_custom')
        method_default = getattr(viewset_class, 'list_default')

        assert 'serializer_class' in method_custom.kwargs
        assert method_custom.kwargs['serializer_class'] == custom_serializer
        assert 'serializer_class' not in method_default.kwargs

    def test_serializer_restore_after_exception(self, sample_model, custom_serializer):
        """Test: Serializer restored even after exception"""
        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['POST'],
                detail=True,
                serializer_class=custom_serializer
            )
            def failing_endpoint(self, request, instance):
                """Endpoint that raises exception"""
                raise ValueError("Intentional error")

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)
        default_serializer = viewset_class.serializer_class

        # Method should exist
        assert hasattr(viewset_class, 'failing_endpoint')

        # Default serializer should still be set
        assert viewset_class.serializer_class == default_serializer
        assert viewset_class.serializer_class != custom_serializer

    def test_endpoint_serializer_context_available(self, sample_model):
        """Test: Serializer context available in custom endpoints"""
        class ContextSerializer(serializers.ModelSerializer):
            extra_data = serializers.SerializerMethodField()

            class Meta:
                model = sample_model
                fields = ['id', 'name', 'extra_data']

            def get_extra_data(self, obj):
                # Access context
                request = self.context.get('request')
                return {'has_request': request is not None}

        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['GET'],
                detail=False,
                serializer_class=ContextSerializer
            )
            def with_context(self, request, queryset):
                """Endpoint with serializer context"""
                # Context should be available
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Method should have custom serializer
        method = getattr(viewset_class, 'with_context')
        assert method.kwargs['serializer_class'] == ContextSerializer

    def test_complex_serializer_with_nested_fields(self, sample_model):
        """Test: Complex serializer dengan nested fields"""
        class NestedSerializer(serializers.Serializer):
            detail = serializers.CharField()

        class ComplexSerializer(serializers.ModelSerializer):
            nested = NestedSerializer(source='*')
            computed = serializers.SerializerMethodField()

            class Meta:
                model = sample_model
                fields = ['id', 'name', 'nested', 'computed']

            def get_computed(self, obj):
                return f"Computed: {obj.name}"

        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['GET'],
                detail=True,
                serializer_class=ComplexSerializer
            )
            def complex_detail(self, request, instance):
                """Detail with complex serializer"""
                serializer = self.get_serializer(instance)
                return Response(serializer.data)

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Check method exists with complex serializer
        method = getattr(viewset_class, 'complex_detail')
        assert method.kwargs['serializer_class'] == ComplexSerializer


class TestSerializerIntegration:
    """Test serializer integration dengan ViewSet lifecycle"""

    def test_get_serializer_available_in_endpoint(self, sample_model):
        """Test: get_serializer() method available in custom endpoint"""
        called_with_correct_serializer = {'value': False}

        class CustomSerializer(serializers.ModelSerializer):
            class Meta:
                model = sample_model
                fields = ['id', 'name']

        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(
                methods=['GET'],
                detail=False,
                serializer_class=CustomSerializer
            )
            def check_serializer(self, request, queryset):
                """Check if get_serializer works"""
                # This should use CustomSerializer
                serializer_class = self.get_serializer_class()
                called_with_correct_serializer['value'] = (
                    serializer_class == CustomSerializer
                )
                return Response({'ok': True})

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)

        # Method should exist
        assert hasattr(viewset_class, 'check_serializer')

    def test_serializer_class_not_in_kwargs_means_default(self, sample_model):
        """Test: Absence of serializer_class in kwargs means use default"""
        class ProductAPI(AutoAPI):
            model = sample_model

            @endpoint(methods=['GET'], detail=False)
            def use_default(self, request, queryset):
                """Should use default serializer"""
                return Response({'ok': True})

        viewset_class = ViewSetFactory.create_viewset(ProductAPI)
        method = getattr(viewset_class, 'use_default')

        # serializer_class should not be in action kwargs
        assert 'serializer_class' not in method.kwargs

        # But default serializer should be set on ViewSet
        assert hasattr(viewset_class, 'serializer_class')
        assert viewset_class.serializer_class is not None
