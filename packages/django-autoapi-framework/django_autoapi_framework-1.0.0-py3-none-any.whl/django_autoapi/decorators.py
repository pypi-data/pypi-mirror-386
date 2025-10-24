"""
Decorators untuk custom endpoints
"""

from functools import wraps


def endpoint(methods=None, detail=True, permissions=None, 
             serializer_class=None, url_path=None, url_name=None,
             **kwargs):
    """
    Decorator untuk mendefinisikan custom endpoint pada AutoAPI class
    
    Args:
        methods: List of HTTP methods (default: ['GET'])
        detail: True = instance-level (/model/{id}/action/)
                False = collection-level (/model/action/)
        permissions: List of permission classes untuk endpoint ini
        serializer_class: Custom serializer untuk endpoint ini
        url_path: Custom URL path (default: function name)
        url_name: Custom URL name (default: function name)
        **kwargs: Extra arguments untuk DRF @action
    
    Usage:
        @endpoint(methods=['POST'], detail=True)
        def activate(self, request, instance):
            instance.is_active = True
            instance.save()
            return Response({'status': 'activated'})
        
        @endpoint(methods=['GET'], detail=False)
        def statistics(self, request, queryset):
            return Response({'total': queryset.count()})
    
    Detail vs Collection:
        - detail=True: Operates on single instance
          URL: /api/model/{id}/action/
          Parameters: (self, request, instance)
        
        - detail=False: Operates on queryset/collection
          URL: /api/model/action/
          Parameters: (self, request, queryset)
    """
    
    # Default methods
    if methods is None:
        methods = ['GET']
    
    # Normalize methods to uppercase
    methods = [m.upper() for m in methods]
    
    def decorator(func):
        """Inner decorator function"""
        
        # Store endpoint configuration as function attribute
        func._endpoint_config = {
            'methods': methods,
            'detail': detail,
            'permissions': permissions or [],
            'serializer_class': serializer_class,
            'url_path': url_path or func.__name__,
            'url_name': url_name or func.__name__,
            'extra_kwargs': kwargs,
        }
        
        # Mark as endpoint
        func._is_endpoint = True
        
        @wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        
        return wrapper
    
    return decorator


def is_endpoint(func):
    """
    Check if function is decorated with @endpoint
    
    Args:
        func: Function to check
    
    Returns:
        bool: True if is endpoint
    """
    return hasattr(func, '_is_endpoint') and func._is_endpoint


def get_endpoint_config(func):
    """
    Get endpoint configuration dari decorated function
    
    Args:
        func: Decorated function
    
    Returns:
        dict: Endpoint configuration or None
    """
    if not is_endpoint(func):
        return None
    
    return getattr(func, '_endpoint_config', None)


# Shorthand decorators untuk common cases
def get_endpoint(detail=True, **kwargs):
    """Shorthand untuk GET endpoint"""
    return endpoint(methods=['GET'], detail=detail, **kwargs)


def post_endpoint(detail=True, **kwargs):
    """Shorthand untuk POST endpoint"""
    return endpoint(methods=['POST'], detail=detail, **kwargs)


def put_endpoint(detail=True, **kwargs):
    """Shorthand untuk PUT endpoint"""
    return endpoint(methods=['PUT'], detail=detail, **kwargs)


def patch_endpoint(detail=True, **kwargs):
    """Shorthand untuk PATCH endpoint"""
    return endpoint(methods=['PATCH'], detail=detail, **kwargs)


def delete_endpoint(detail=True, **kwargs):
    """Shorthand untuk DELETE endpoint"""
    return endpoint(methods=['DELETE'], detail=detail, **kwargs)


# Action shortcuts (semantic aliases)
def detail_action(methods=None, **kwargs):
    """
    Decorator untuk detail-level action (operates on single instance)
    
    Usage:
        @detail_action(methods=['POST'])
        def archive(self, request, instance):
            instance.archived = True
            instance.save()
            return Response({'status': 'archived'})
    """
    return endpoint(methods=methods, detail=True, **kwargs)


def collection_action(methods=None, **kwargs):
    """
    Decorator untuk collection-level action (operates on queryset)
    
    Usage:
        @collection_action(methods=['GET'])
        def statistics(self, request, queryset):
            return Response({'total': queryset.count()})
    """
    return endpoint(methods=methods, detail=False, **kwargs)

