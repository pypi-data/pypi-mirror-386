"""
Router untuk auto-generate URL patterns dari AutoAPI classes
"""

from rest_framework.routers import DefaultRouter
from .registry import AutoAPIRegistry
from .factories.viewset import ViewSetFactory


class AutoAPIRouter(DefaultRouter):
    """
    Custom router yang auto-generate URLs dari AutoAPI classes
    
    Features:
    - Manual registration via register()
    - Auto-discovery via autodiscover()
    - URL prefix customization
    - Basename customization
    
    Usage:
        # Manual registration
        router = AutoAPIRouter()
        router.register(ProductAPI)
        
        # Or auto-discover all
        router.autodiscover()
        
        # In urls.py
        urlpatterns = [
            path('api/', include(router.urls)),
        ]
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize router"""
        super().__init__(*args, **kwargs)
        self._auto_registered = False
        self._registered_apis = {}  # Track registered APIs
    
    def register(self, api_class, prefix=None, basename=None, viewset=None):
        """
        Register AutoAPI class ke router
        
        Args:
            api_class: AutoAPI class to register
            prefix: URL prefix (default: model name plural)
            basename: URL name prefix (default: model name)
            viewset: Custom ViewSet (default: auto-generated)
        
        Example:
            router.register(ProductAPI)
            # Generates: /products/
            
            router.register(ProductAPI, prefix='items')
            # Generates: /items/
        
        Raises:
            ValueError: If api_class invalid
        """
        # Validation
        if not hasattr(api_class, 'model') or api_class.model is None:
            raise ValueError(
                f"{api_class.__name__} must have 'model' attribute"
            )
        
        model = api_class.model
        
        # Generate ViewSet if not provided
        if viewset is None:
            viewset = ViewSetFactory.create_viewset(api_class)
        
        # Generate prefix if not provided
        if prefix is None:
            prefix = self._generate_prefix(model)
        
        # Generate basename if not provided
        if basename is None:
            basename = self._generate_basename(model)
        
        # Store reference
        model_key = f"{model._meta.app_label}.{model._meta.model_name}"
        self._registered_apis[model_key] = {
            'api_class': api_class,
            'prefix': prefix,
            'basename': basename,
            'viewset': viewset,
        }
        
        # Register to DRF router
        super().register(prefix, viewset, basename=basename)
        
        # Debug info (optional, comment out for production)
        # print(f"✅ Registered: {api_class.__name__} at /{prefix}/")
    
    def autodiscover(self):
        """
        Auto-discover dan register semua AutoAPI classes dari registry
        
        Example:
            router = AutoAPIRouter()
            router.autodiscover()
            
            # All registered AutoAPI classes will be included
        
        Note:
            - Only discovers classes already registered in AutoAPIRegistry
            - Safe to call multiple times (won't duplicate)
        """
        if self._auto_registered:
            # Already autodiscovered, skip
            return
        
        # Get all registered API classes
        api_classes = AutoAPIRegistry.get_all()
        
        # Register each one
        for api_class in api_classes:
            model_key = f"{api_class.model._meta.app_label}.{api_class.model._meta.model_name}"
            
            # Skip if already manually registered
            if model_key in self._registered_apis:
                continue
            
            try:
                self.register(api_class)
            except Exception as e:
                # Log error but continue with others
                print(f"⚠️  Failed to register {api_class.__name__}: {e}")
        
        self._auto_registered = True
    
    def unregister(self, api_class_or_prefix):
        """
        Unregister API class dari router
        
        Args:
            api_class_or_prefix: AutoAPI class or URL prefix string
        
        Example:
            router.unregister(ProductAPI)
            # or
            router.unregister('products')
        
        Returns:
            bool: True if unregistered, False if not found
        """
        # If it's a string, treat as prefix
        if isinstance(api_class_or_prefix, str):
            prefix = api_class_or_prefix
            # Find and remove from DRF router
            # Note: DRF doesn't have unregister, we track manually
            for key, info in list(self._registered_apis.items()):
                if info['prefix'] == prefix:
                    del self._registered_apis[key]
                    return True
            return False
        
        # If it's an API class
        api_class = api_class_or_prefix
        model = api_class.model
        model_key = f"{model._meta.app_label}.{model._meta.model_name}"
        
        if model_key in self._registered_apis:
            del self._registered_apis[model_key]
            return True
        
        return False
    
    def get_registered_apis(self):
        """
        Get all registered API classes
        
        Returns:
            dict: Mapping of model_key -> registration info
        
        Example:
            apis = router.get_registered_apis()
            for key, info in apis.items():
                print(f"{key}: /{info['prefix']}/")
        """
        return self._registered_apis.copy()
    
    def get_api_info(self, api_class):
        """
        Get registration info untuk specific API class
        
        Args:
            api_class: AutoAPI class
        
        Returns:
            dict: Registration info or None
        """
        model = api_class.model
        model_key = f"{model._meta.app_label}.{model._meta.model_name}"
        return self._registered_apis.get(model_key)
    
    def _generate_prefix(self, model):
        """
        Generate URL prefix dari model name
        
        Args:
            model: Django model class
        
        Returns:
            str: URL prefix (pluralized model name)
        
        Example:
            Product -> 'products'
            Category -> 'categories'
            Person -> 'people' (manual override needed)
        """
        model_name = model._meta.model_name
        
        # Simple pluralization (add 's')
        # TODO: Add proper pluralization library for complex cases
        if model_name.endswith('y'):
            # category -> categories
            return model_name[:-1] + 'ies'
        elif model_name.endswith('s'):
            # status -> statuses (or keep as 'status')
            return model_name + 'es'
        else:
            # product -> products
            return model_name + 's'
    
    def _generate_basename(self, model):
        """
        Generate basename dari model name
        
        Args:
            model: Django model class
        
        Returns:
            str: Basename (model name)
        
        Example:
            Product -> 'product'
            Category -> 'category'
        """
        return model._meta.model_name
    
    def get_urls_info(self):
        """
        Get info about all generated URLs
        
        Returns:
            list: List of dicts with URL info
        
        Example:
            for info in router.get_urls_info():
                print(f"{info['pattern']} -> {info['name']}")
        """
        urls_info = []
        
        for pattern in self.urls:
            urls_info.append({
                'pattern': str(pattern.pattern),
                'name': pattern.name if hasattr(pattern, 'name') else None,
                'callback': pattern.callback if hasattr(pattern, 'callback') else None,
            })
        
        return urls_info


# Convenience functions
def create_router(autodiscover=False):
    """
    Create AutoAPIRouter dengan optional autodiscovery
    
    Args:
        autodiscover: If True, call autodiscover() automatically
    
    Returns:
        AutoAPIRouter instance
    
    Example:
        # Manual registration
        router = create_router()
        router.register(ProductAPI)
        
        # Auto-discover all
        router = create_router(autodiscover=True)
    """
    router = AutoAPIRouter()
    
    if autodiscover:
        router.autodiscover()
    
    return router


def get_default_router():
    """
    Get or create default global router (singleton pattern)
    
    Returns:
        AutoAPIRouter instance
    
    Example:
        router = get_default_router()
        router.register(ProductAPI)
    """
    global _default_router
    
    if '_default_router' not in globals():
        _default_router = AutoAPIRouter()
    
    return _default_router

