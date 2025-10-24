"""
Advanced filter builders untuk record rules
"""

from typing import Any, Dict, List
from django.db.models import Q


class FilterBuilder:
    """
    Build complex Django filters dari domain expressions
    
    Supports:
    - Simple: {'status': 'active'}
    - Lookups: {'price__gte': 100}
    - IN queries: {'status__in': ['active', 'pending']}
    - NULL checks: {'deleted_at__isnull': True}
    - Range: {'price__range': [100, 200]}
    
    Example:
        builder = FilterBuilder()
        q = builder.build({
            'status': 'active',
            'price__gte': 100,
            'name__icontains': 'laptop'
        })
        
        queryset = Product.objects.filter(q)
    """
    
    # Valid Django field lookups
    VALID_LOOKUPS = [
        'exact', 'iexact',
        'contains', 'icontains',
        'in',
        'gt', 'gte', 'lt', 'lte',
        'startswith', 'istartswith',
        'endswith', 'iendswith',
        'range',
        'date',
        'year', 'month', 'day', 'week', 'week_day',
        'quarter',
        'time', 'hour', 'minute', 'second',
        'isnull',
        'regex', 'iregex',
    ]
    
    def build(self, domain: Dict[str, Any]) -> Q:
        """
        Build Q object from domain
        
        Args:
            domain: Domain filter dictionary
        
        Returns:
            Django Q object
        """
        if not domain:
            return Q()
        
        q_objects = []
        
        for field, value in domain.items():
            q_obj = self._build_condition(field, value)
            q_objects.append(q_obj)
        
        # Combine with AND
        if not q_objects:
            return Q()
        
        combined = q_objects[0]
        for q_obj in q_objects[1:]:
            combined &= q_obj
        
        return combined
    
    def _build_condition(self, field: str, value: Any) -> Q:
        """
        Build single condition
        
        Args:
            field: Field name (may include lookup)
            value: Expected value
        
        Returns:
            Q object
        """
        # Validate lookup if present
        if '__' in field:
            parts = field.split('__')
            lookup = parts[-1]
            
            # Check if valid lookup
            if lookup in self.VALID_LOOKUPS:
                # Valid lookup
                return Q(**{field: value})
            else:
                # Might be related field (e.g., unit__name)
                # Let Django handle it
                return Q(**{field: value})
        else:
            # Simple field
            return Q(**{field: value})
    
    def build_or(self, domains: List[Dict[str, Any]]) -> Q:
        """
        Build Q with OR conditions
        
        Args:
            domains: List of domain dictionaries
        
        Returns:
            Q object with OR
        
        Example:
            builder.build_or([
                {'status': 'active'},
                {'status': 'pending'}
            ])
            # Result: Q(status='active') | Q(status='pending')
        """
        if not domains:
            return Q()
        
        q_objects = [self.build(domain) for domain in domains]
        
        combined = q_objects[0]
        for q_obj in q_objects[1:]:
            combined |= q_obj
        
        return combined
    
    def build_and(self, domains: List[Dict[str, Any]]) -> Q:
        """
        Build Q with AND conditions
        
        Args:
            domains: List of domain dictionaries
        
        Returns:
            Q object with AND
        """
        if not domains:
            return Q()
        
        q_objects = [self.build(domain) for domain in domains]
        
        combined = q_objects[0]
        for q_obj in q_objects[1:]:
            combined &= q_obj
        
        return combined


class DomainValidator:
    """
    Validate domain filter expressions
    
    Usage:
        validator = DomainValidator()
        
        if validator.is_valid(domain):
            # Domain is valid
        
        errors = validator.get_errors(domain)
    """
    
    def __init__(self):
        self.errors = []
    
    def is_valid(self, domain: Dict[str, Any]) -> bool:
        """
        Check if domain is valid
        
        Args:
            domain: Domain dictionary
        
        Returns:
            bool: True if valid
        """
        self.errors = []
        
        if not isinstance(domain, dict):
            self.errors.append('Domain must be a dictionary')
            return False
        
        # Validate each field
        for field, value in domain.items():
            if not self._validate_field(field, value):
                return False
        
        return True
    
    def _validate_field(self, field: str, value: Any) -> bool:
        """Validate single field"""
        # Field name validation
        if not isinstance(field, str):
            self.errors.append(f'Field name must be string: {field}')
            return False
        
        if not field:
            self.errors.append('Field name cannot be empty')
            return False
        
        # Value validation
        # Allow None, strings, numbers, lists, bools
        if value is not None:
            if not isinstance(value, (str, int, float, bool, list)):
                self.errors.append(f'Invalid value type for {field}: {type(value)}')
                return False
        
        return True
    
    def get_errors(self, domain: Dict[str, Any]) -> List[str]:
        """Get validation errors"""
        self.is_valid(domain)
        return self.errors
    
    