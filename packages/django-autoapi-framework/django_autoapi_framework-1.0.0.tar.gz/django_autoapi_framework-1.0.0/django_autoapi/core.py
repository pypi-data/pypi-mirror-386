"""
Core module untuk AutoAPI base class
"""

from django.db import models
from .metaclass import AutoAPIMetaclass  
from .decorators import is_endpoint, get_endpoint_config


class AutoAPI(metaclass=AutoAPIMetaclass):
    """
    Base class untuk AutoAPI definitions

    Enhanced dengan Record Rules support untuk row-level security.
    """

    # === REQUIRED ===
    model = None

    # === QUERY FEATURES ===
    filterable = []
    searchable = []
    orderable = []
    ordering = None

    # === PAGINATION ===
    pagination = 'cursor'
    page_size = 50
    max_page_size = 1000

    # === PERMISSIONS ===
    permission_classes = ['IsAuthenticated']

    # === FEATURES FLAGS ===
    record_rules = False
    enable_record_rules = False  # NEW: Enable row-level security dengan RecordRules ⭐
    audit = False
    webhooks = []

    # === SERIALIZER CUSTOMIZATION ===
    serializer_class = None
    fields = None
    exclude_fields = []
    read_only_fields = []
    write_only_fields = []
    extra_kwargs = {}

    # === QUERYSET OPTIMIZATION ===
    queryset_filters = {}
    select_related = []
    prefetch_related = [] 
    
    def __init_subclass__(cls, **kwargs):
        """
        Validasi saat subclass dibuat
        Called BEFORE metaclass.__new__
        """
        super().__init_subclass__(**kwargs)
        
        # Note: model validation di sini
        # Registration di metaclass
        
        if cls.model is None:
            raise ValueError(
                f'{cls.__name__} harus mendefinisikan attribute "model".\n'
                f'Contoh: model = YourModel'
            )
        
        if not (isinstance(cls.model, type) and issubclass(cls.model, models.Model)):
            raise ValueError(
                f'{cls.__name__}.model harus berupa Django model class.\n'
                f'Yang diberikan: {type(cls.model)}'
            )
        
        if not isinstance(cls.filterable, (list, tuple)):
            raise TypeError(
                f'{cls.__name__}.filterable harus berupa list atau tuple.\n'
                f'Yang diberikan: {type(cls.filterable)}'
            )
        
        if not isinstance(cls.searchable, (list, tuple)):
            raise TypeError(
                f'{cls.__name__}.searchable harus berupa list atau tuple.\n'
                f'Yang diberikan: {type(cls.searchable)}'
            )
        
        if not isinstance(cls.orderable, (list, tuple)):
            raise TypeError(
                f'{cls.__name__}.orderable harus berupa list atau tuple.\n'
                f'Yang diberikan: {type(cls.orderable)}'
            )
    
    @classmethod
    def get_model(cls):
        """Get model class"""
        return cls.model
    
    @classmethod
    def get_model_name(cls):
        """Get model name (lowercase)"""
        return cls.model._meta.model_name
    
    @classmethod
    def get_app_label(cls):
        """Get app label"""
        return cls.model._meta.app_label
    
    @classmethod
    def get_model_key(cls):
        """Get unique model key (app_label.model_name)"""
        return f"{cls.get_app_label()}.{cls.get_model_name()}"
    
    def __repr__(self):
        return f'<{self.__class__.__name__} model={self.model.__name__}>'
    
    @classmethod
    def _get_endpoints(cls):
        """
        Extract all custom endpoints dari API class
        
        Returns:
            list: List of tuples (method_name, method_func, config)
        
        Example:
            endpoints = MyAPI._get_endpoints()
            for name, func, config in endpoints:
                print(f"{name}: {config['methods']} {config['url_path']}")
        """
        endpoints = []
        
        # Iterate through all class attributes
        for attr_name in dir(cls):
            # Skip private/magic methods
            if attr_name.startswith('_'):
                continue
            
            # Get attribute
            attr = getattr(cls, attr_name, None)
            
            # Skip non-callables
            if not callable(attr):
                continue
            
            # Check if it's an endpoint
            if is_endpoint(attr):
                config = get_endpoint_config(attr)
                endpoints.append((attr_name, attr, config))
        
        return endpoints
    
    @classmethod
    def get_endpoint_info(cls):
        """
        Get formatted info about all endpoints
        
        Returns:
            dict: Endpoint information
        
        Example:
            info = MyAPI.get_endpoint_info()
            print(f"Total endpoints: {info['count']}")
            for ep in info['endpoints']:
                print(f"  {ep['name']}: {ep['methods']} ({ep['type']})")
        """
        endpoints = cls._get_endpoints()
        
        return {
            'count': len(endpoints),
            'endpoints': [
                {
                    'name': name,
                    'methods': config['methods'],
                    'type': 'detail' if config['detail'] else 'collection',
                    'url_path': config['url_path'],
                    'has_permissions': bool(config['permissions']),
                    'has_custom_serializer': config['serializer_class'] is not None,
                }
                for name, func, config in endpoints
            ]
        }
    
    