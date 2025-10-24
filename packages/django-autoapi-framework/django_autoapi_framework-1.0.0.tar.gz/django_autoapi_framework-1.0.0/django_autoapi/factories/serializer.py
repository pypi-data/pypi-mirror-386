"""
Factory untuk auto-generate DRF serializers dari Django models
"""

import inspect
from rest_framework import serializers


class SerializerFactory:
    """
    Factory untuk membuat serializer secara otomatis
    
    Features:
    - Auto-generate dari Django model
    - Support custom serializer override
    - Field-level control (read_only, write_only, exclude)
    - Validation customization
    
    Usage:
        serializer_class = SerializerFactory.create_serializer(ProductAPI)
        serializer = serializer_class(data={...})
    """
    
    @staticmethod
    def create_serializer(api_class):
        """
        Buat ModelSerializer dari AutoAPI class
        
        Args:
            api_class: AutoAPI class instance
        
        Returns:
            Generated serializer class
        
        Example:
            class ProductAPI(AutoAPI):
                model = Product
                read_only_fields = ['created_at']
            
            serializer = SerializerFactory.create_serializer(ProductAPI)
        """
        model = api_class.model
        
        # Check 1: Apakah user sudah provide custom serializer?
        if hasattr(api_class, 'serializer_class') and api_class.serializer_class:
            return api_class.serializer_class
        
        # Check 2: Build serializer automatically
        return SerializerFactory._build_serializer(api_class, model)
    
    @staticmethod
    def _build_serializer(api_class, model):
        """
        Build serializer class secara dinamis

        Args:
            api_class: AutoAPI class
            model: Django model

        Returns:
            Dynamically created serializer class
        """
        # First, collect info about custom fields that will be added
        custom_field_names = SerializerFactory._get_custom_field_names(api_class)

        # Prepare Meta class attributes (needs to know custom fields)
        meta_attrs = SerializerFactory._build_meta_attrs(api_class, model, custom_field_names)

        # Prepare serializer fields (custom fields, dll)
        serializer_attrs = SerializerFactory._build_serializer_attrs(api_class, model)

        # Add Meta class
        serializer_attrs['Meta'] = type('Meta', (), meta_attrs)

        # Create serializer class dynamically
        serializer_name = f'{model.__name__}Serializer'
        serializer_class = type(
            serializer_name,
            (serializers.ModelSerializer,),
            serializer_attrs
        )

        return serializer_class

    @staticmethod
    def _get_custom_field_names(api_class):
        """
        Get names of all custom fields that will be added to serializer

        Returns:
            set: Set of custom field names
        """
        custom_fields = set()
        # Reserved methods that should NOT become SerializerMethodFields
        reserved_methods = {
            'get_queryset', 'get_serializer', 'get_serializer_class',
            'get_model', 'get_model_name', 'get_app_label', 'get_model_key'
        }

        # SerializerMethodFields (from get_* methods)
        for attr_name in dir(api_class):
            if attr_name.startswith('get_') and attr_name not in reserved_methods:
                attr = getattr(api_class, attr_name, None)
                if callable(attr) and not attr_name.startswith('_'):
                    field_name = attr_name[4:]  # Remove 'get_' prefix
                    custom_fields.add(field_name)

        # Custom fields from custom_fields attribute
        if hasattr(api_class, 'custom_fields') and api_class.custom_fields:
            custom_fields.update(api_class.custom_fields.keys())

        # Nested serializers
        if hasattr(api_class, 'nested_serializers') and api_class.nested_serializers:
            custom_fields.update(api_class.nested_serializers.keys())

        return custom_fields

    @staticmethod
    def _build_meta_attrs(api_class, model, custom_field_names=None):
        """
        Build Meta class attributes untuk serializer

        Args:
            api_class: AutoAPI class
            model: Django model
            custom_field_names: Set of custom field names to add

        Returns:
            dict: Meta attributes
        """
        if custom_field_names is None:
            custom_field_names = set()

        meta_attrs = {
            'model': model,
            'fields': '__all__',  # Default: all fields
            'ref_name': f'AutoAPI{model.__name__}',  # Unique ref_name for Swagger
        }
        
        # Read-only fields
        if hasattr(api_class, 'read_only_fields') and api_class.read_only_fields:
            meta_attrs['read_only_fields'] = api_class.read_only_fields

        # Exclude fields
        if hasattr(api_class, 'exclude_fields') and api_class.exclude_fields:
            meta_attrs['exclude'] = api_class.exclude_fields
            # Remove 'fields' key karena conflict dengan 'exclude'
            del meta_attrs['fields']

        # Specific fields only
        elif hasattr(api_class, 'fields') and api_class.fields:
            # User specified fields - we need to keep only custom fields that are in the list
            user_fields = list(api_class.fields)

            # Don't add custom fields to Meta.fields - they're already declared
            # DRF will automatically include them because they're in serializer_attrs
            # We only keep model fields and custom fields explicitly requested by user
            meta_attrs['fields'] = user_fields
        
        # Extra kwargs (untuk field customization lebih detail)
        extra_kwargs = {}
        if hasattr(api_class, 'extra_kwargs') and api_class.extra_kwargs:
            extra_kwargs = api_class.extra_kwargs.copy()

        # Write-only fields (via extra_kwargs - more reliable than field override)
        if hasattr(api_class, 'write_only_fields') and api_class.write_only_fields:
            for field_name in api_class.write_only_fields:
                if field_name not in extra_kwargs:
                    extra_kwargs[field_name] = {}
                extra_kwargs[field_name]['write_only'] = True

        # Add extra_kwargs if not empty
        if extra_kwargs:
            meta_attrs['extra_kwargs'] = extra_kwargs

        return meta_attrs
    
    @staticmethod
    def _build_serializer_attrs(api_class, model):
        """
        Build serializer attributes (custom fields, methods, dll)

        Enhanced version dengan support untuk:
        - Custom SerializerMethodField
        - Nested serializers
        - Custom validation methods
        - Custom field definitions

        Returns:
            dict: Serializer attributes
        """
        attrs = {}

        # Note: write_only_fields now handled via extra_kwargs in _build_meta_attrs
        # This is more reliable and follows DRF conventions

        # Check if user specified specific fields
        user_fields = getattr(api_class, 'fields', None)

        # ===================================================================
        # 1. SerializerMethodFields (NEW)
        # ===================================================================
        # Auto-create SerializerMethodField untuk semua method 'get_<field_name>'
        # Skip reserved methods and private methods
        reserved_methods = {
            'get_queryset', 'get_serializer', 'get_serializer_class',
            'get_model', 'get_model_name', 'get_app_label', 'get_model_key'
        }

        for attr_name in dir(api_class):
            if attr_name.startswith('get_') and attr_name not in reserved_methods:
                attr = getattr(api_class, attr_name, None)

                if callable(attr) and not attr_name.startswith('_'):
                    # Extract field name dari method name
                    # get_full_name -> full_name
                    field_name = attr_name[4:]  # Remove 'get_' prefix

                    # Only add if: no specific fields, or field is in user's list
                    if user_fields is None or field_name in user_fields:
                        # Create SerializerMethodField
                        attrs[field_name] = serializers.SerializerMethodField()

                        # Add the method itself
                        # Check if it's a plain function (staticmethod) vs bound method
                        # Plain functions don't have __self__ attribute
                        is_static = inspect.isfunction(attr) and not hasattr(attr, '__self__')

                        if is_static:
                            # Wrap staticmethod to work with DRF (which passes self)
                            # Use lambda with immediate evaluation to capture value
                            attrs[attr_name] = (lambda func: lambda self, obj: func(obj))(attr)
                        else:
                            attrs[attr_name] = attr

        # ===================================================================
        # 2. Validation Methods (NEW)
        # ===================================================================
        # Copy validation methods: validate, validate_<field_name>
        # DRF expects validation methods to receive self as first param
        for attr_name in dir(api_class):
            if attr_name.startswith('validate'):
                attr = getattr(api_class, attr_name, None)

                if callable(attr) and not attr_name.startswith('_'):
                    # Check if it's a plain function (staticmethod) vs bound method
                    is_static = inspect.isfunction(attr) and not hasattr(attr, '__self__')

                    if is_static:
                        # Different wrapper based on validate vs validate_field
                        # Use lambda with immediate evaluation to capture variable
                        if attr_name == 'validate':
                            # Object-level validation: validate(self, data)
                            attrs[attr_name] = (lambda func: lambda self, data: func(data))(attr)
                        else:
                            # Field-level validation: validate_field(self, value)
                            attrs[attr_name] = (lambda func: lambda self, value: func(value))(attr)
                    else:
                        attrs[attr_name] = attr

        # ===================================================================
        # 3. Nested Serializers (NEW)
        # ===================================================================
        # Check for nested_serializers configuration
        if hasattr(api_class, 'nested_serializers') and api_class.nested_serializers:
            for field_name, nested_config in api_class.nested_serializers.items():
                # Only add if: no specific fields, or field is in user's list
                if user_fields is None or field_name in user_fields:
                    if isinstance(nested_config, dict):
                        # Configuration format: {'api_class': SomeAPI, 'many': True}
                        nested_api = nested_config.get('api_class')
                        many = nested_config.get('many', False)

                        if nested_api:
                            nested_serializer = SerializerFactory.create_serializer(nested_api)
                            if many:
                                attrs[field_name] = nested_serializer(many=True)
                            else:
                                attrs[field_name] = nested_serializer()
                    else:
                        # Simple format: just the API class
                        nested_serializer = SerializerFactory.create_serializer(nested_config)
                        attrs[field_name] = nested_serializer()

        # ===================================================================
        # 4. Custom Fields (NEW)
        # ===================================================================
        # Check for custom_fields configuration
        if hasattr(api_class, 'custom_fields') and api_class.custom_fields:
            for field_name, field_instance in api_class.custom_fields.items():
                # Only add if: no specific fields, or field is in user's list
                if user_fields is None or field_name in user_fields:
                    attrs[field_name] = field_instance

        return attrs
    
    @staticmethod
    def _get_drf_field_for_model_field(model_field):
        """
        Convert Django model field ke DRF serializer field
        
        Args:
            model_field: Django model field
        
        Returns:
            DRF field instance
        """
        from django.db import models as django_models
        
        # Mapping Django fields -> DRF fields
        field_mapping = {
            django_models.CharField: serializers.CharField,
            django_models.TextField: serializers.CharField,
            django_models.IntegerField: serializers.IntegerField,
            django_models.FloatField: serializers.FloatField,
            django_models.DecimalField: serializers.DecimalField,
            django_models.BooleanField: serializers.BooleanField,
            django_models.DateTimeField: serializers.DateTimeField,
            django_models.DateField: serializers.DateField,
            django_models.EmailField: serializers.EmailField,
            django_models.URLField: serializers.URLField,
            django_models.UUIDField: serializers.UUIDField,
            django_models.ForeignKey: serializers.PrimaryKeyRelatedField,
            django_models.ManyToManyField: serializers.PrimaryKeyRelatedField,
        }
        
        field_class = field_mapping.get(type(model_field))
        
        if field_class:
            # Prepare kwargs
            kwargs = {}
            
            if hasattr(model_field, 'blank') and model_field.blank:
                kwargs['required'] = False
                kwargs['allow_blank'] = True
            
            if hasattr(model_field, 'null') and model_field.null:
                kwargs['allow_null'] = True
            
            # For relational fields
            if isinstance(model_field, (django_models.ForeignKey, django_models.ManyToManyField)):
                kwargs['queryset'] = model_field.related_model.objects.all()
                if isinstance(model_field, django_models.ManyToManyField):
                    kwargs['many'] = True
            
            return field_class(**kwargs)
        
        # Default fallback
        return serializers.CharField(required=False, allow_blank=True, allow_null=True)


# Convenience function
def get_serializer_for_model(model, api_class=None):
    """
    Helper function untuk get serializer dari model
    
    Args:
        model: Django model
        api_class: Optional AutoAPI class, jika None akan buat default
    
    Returns:
        Serializer class
    """
    if api_class:
        return SerializerFactory.create_serializer(api_class)
    
    # Buat temporary API class dengan defaults
    from django_autoapi.core import AutoAPI
    
    class TempAPI(AutoAPI):
        pass
    
    TempAPI.model = model
    return SerializerFactory.create_serializer(TempAPI)

