"""
Metaclass untuk auto-registration AutoAPI classes
"""


class AutoAPIMetaclass(type):
    """
    Metaclass yang automatically register AutoAPI classes ke registry
    
    How it works:
    1. Saat class dibuat (inherit dari AutoAPI)
    2. __new__ method ini dipanggil
    3. Class otomatis di-register ke AutoAPIRegistry
    
    Example:
        class ProductAPI(AutoAPI):  # ← __new__ dipanggil di sini
            model = Product
        
        # ProductAPI otomatis registered!
    """
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        """
        Dipanggil saat class baru dibuat
        
        Args:
            mcs: Metaclass itself
            name: Nama class yang dibuat (e.g., 'ProductAPI')
            bases: Parent classes (e.g., (AutoAPI,))
            namespace: Dict berisi attributes dan methods class
            **kwargs: Extra arguments
        
        Returns:
            New class object
        """
        # Step 1: Buat class seperti biasa
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Step 2: Skip untuk base AutoAPI class
        if name == 'AutoAPI':
            return cls
        
        # Step 3: Skip kalau tidak ada model (abstract class)
        if not hasattr(cls, 'model') or cls.model is None:
            return cls
        
        # Step 4: Register ke registry
        # Import di sini untuk avoid circular import
        from .registry import AutoAPIRegistry
        
        try:
            AutoAPIRegistry.register(cls)
        except ValueError as e:
            # Re-raise dengan context lebih jelas
            raise ValueError(
                f"Failed to register {name}: {str(e)}"
            ) from e
        
        return cls


# Helper untuk debugging (optional)
def get_class_info(cls):
    """Helper untuk debug - show class info"""
    return {
        'name': cls.__name__,
        'module': cls.__module__,
        'bases': [b.__name__ for b in cls.__bases__],
        'has_model': hasattr(cls, 'model'),
        'model': getattr(cls, 'model', None),
    }

