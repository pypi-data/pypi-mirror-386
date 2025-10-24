"""
Central registry untuk track semua AutoAPI classes
"""

from typing import List, Dict, Optional, Type, Any


class AutoAPIRegistry:
    """
    Central registry yang menyimpan mapping: Model -> List[AutoAPI classes]

    Design pattern: Singleton registry
    - Single source of truth
    - Thread-safe (untuk production nanti)
    - Supports multiple API classes per model

    Usage:
        # Register (biasanya automatic via metaclass)
        AutoAPIRegistry.register(ProductAPI)
        AutoAPIRegistry.register(ProductDetailAPI)  # Same model, different API

        # Retrieve
        api_classes = AutoAPIRegistry.get_api_classes(Product)  # Returns list
        api_class = AutoAPIRegistry.get_api_class(Product)  # Returns first one

        # List all
        all_apis = AutoAPIRegistry.get_all()
    """

    # Class variable - shared across all instances
    # Structure: {model_key: [api_class1, api_class2, ...]}
    _registry: Dict[str, List[Type[Any]]] = {}
    
    @classmethod
    def register(cls, api_class: Type[Any], allow_multiple: bool = True) -> None:
        """
        Register AutoAPI class ke registry

        Args:
            api_class: Class yang inherit dari AutoAPI
            allow_multiple: Allow multiple API classes for same model (default: True)

        Raises:
            ValueError: Jika validation gagal atau duplicate (when allow_multiple=False)
            TypeError: Jika api_class invalid

        Example:
            AutoAPIRegistry.register(ProductAPI)
            AutoAPIRegistry.register(ProductDetailAPI)  # Same model, OK!
            AutoAPIRegistry.register(ProductAPI3, allow_multiple=False)  # Error if exists
        """
        # Validasi 1: api_class harus ada
        if api_class is None:
            raise TypeError("api_class cannot be None")

        # Validasi 2: harus punya model
        if not hasattr(api_class, 'model') or api_class.model is None:
            raise ValueError(
                f"{api_class.__name__} must have 'model' attribute"
            )

        model = api_class.model

        # Buat unique key: "app_label.model_name"
        # Example: "products.product"
        model_key = f"{model._meta.app_label}.{model._meta.model_name}"

        # Initialize list if model_key doesn't exist
        if model_key not in cls._registry:
            cls._registry[model_key] = []

        # Validasi 3: Check duplicate API class (by name)
        existing_names = [api.__name__ for api in cls._registry[model_key]]
        if api_class.__name__ in existing_names:
            raise ValueError(
                f"API class '{api_class.__name__}' already registered for model {model_key}. "
                f"Use a different class name."
            )

        # Validasi 4: Check if multiple registrations allowed
        if not allow_multiple and len(cls._registry[model_key]) > 0:
            existing = cls._registry[model_key][0]
            raise ValueError(
                f"Model {model_key} already registered by {existing.__name__}. "
                f"Cannot register {api_class.__name__} (allow_multiple=False)."
            )

        # Register! Add to list
        cls._registry[model_key].append(api_class)

        # Debug log (optional, comment out for production)
        # print(f"✅ Registered: {api_class.__name__} for {model_key}")
    
    @classmethod
    def unregister(cls, api_class: Type[Any]) -> bool:
        """
        Unregister AutoAPI class (useful untuk testing)

        Args:
            api_class: Class yang mau di-unregister

        Returns:
            bool: True jika berhasil, False jika tidak ketemu
        """
        if not hasattr(api_class, 'model') or api_class.model is None:
            return False

        model = api_class.model
        model_key = f"{model._meta.app_label}.{model._meta.model_name}"

        if model_key in cls._registry:
            # Remove specific API class from list
            try:
                cls._registry[model_key].remove(api_class)
                # Clean up empty lists
                if not cls._registry[model_key]:
                    del cls._registry[model_key]
                return True
            except ValueError:
                return False

        return False
    
    @classmethod
    def get_api_class(cls, model: Type[Any]) -> Optional[Type[Any]]:
        """
        Get first AutoAPI class untuk model tertentu (backward compatibility)

        Args:
            model: Django model class

        Returns:
            AutoAPI class or None (returns first registered API class)

        Example:
            api_class = AutoAPIRegistry.get_api_class(Product)
            if api_class:
                print(f"Found: {api_class.__name__}")
        """
        if model is None:
            return None

        model_key = f"{model._meta.app_label}.{model._meta.model_name}"
        api_classes = cls._registry.get(model_key, [])
        return api_classes[0] if api_classes else None

    @classmethod
    def get_api_classes(cls, model: Type[Any]) -> List[Type[Any]]:
        """
        Get all AutoAPI classes untuk model tertentu

        Args:
            model: Django model class

        Returns:
            list: List of AutoAPI classes (empty list if none found)

        Example:
            api_classes = AutoAPIRegistry.get_api_classes(Product)
            for api in api_classes:
                print(f"Found: {api.__name__}")
        """
        if model is None:
            return []

        model_key = f"{model._meta.app_label}.{model._meta.model_name}"
        return cls._registry.get(model_key, [])
    
    @classmethod
    def is_registered(cls, model: Type[Any]) -> bool:
        """
        Check apakah model sudah registered

        Args:
            model: Django model class

        Returns:
            bool: True jika registered

        Example:
            if AutoAPIRegistry.is_registered(Product):
                print("Product API is registered!")
        """
        return cls.get_api_class(model) is not None
    
    @classmethod
    def get_all(cls) -> List[Type[Any]]:
        """
        Get semua registered AutoAPI classes (flattened list)

        Returns:
            list: List of AutoAPI classes

        Example:
            for api_class in AutoAPIRegistry.get_all():
                print(api_class.__name__)
        """
        # Flatten the nested lists
        all_apis = []
        for api_list in cls._registry.values():
            all_apis.extend(api_list)
        return all_apis
    
    @classmethod
    def get_registry_info(cls) -> Dict[str, Any]:
        """
        Get info tentang registry (untuk debugging)

        Returns:
            dict: Registry information
        """
        all_apis = cls.get_all()
        return {
            'total_registered': len(all_apis),
            'total_models': len(cls._registry),
            'models': list(cls._registry.keys()),
            'api_classes': [api.__name__ for api in all_apis],
            'details': {
                model_key: [api.__name__ for api in api_list]
                for model_key, api_list in cls._registry.items()
            }
        }
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear semua registry (ONLY for testing!)

        Warning:
            Jangan pakai di production code!
        """
        cls._registry.clear()


# Convenience functions
def get_registered_models() -> List[Type[Any]]:
    """
    Get list of all registered models

    Returns:
        list: List of Django model classes

    Example:
        models = get_registered_models()
        for model in models:
            print(f"Registered: {model.__name__}")
    """
    result = []
    for api in AutoAPIRegistry.get_all():
        if hasattr(api, 'model'):
            result.append(api.model)
    return result


def get_registered_count() -> int:
    """
    Get total number of registered APIs

    Returns:
        int: Total count of registered API classes

    Example:
        count = get_registered_count()
        print(f"Total registered APIs: {count}")
    """
    return len(AutoAPIRegistry.get_all())

