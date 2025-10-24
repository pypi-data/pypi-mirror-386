"""
Domain expression parser untuk record rules
"""

import re
from typing import Any, Dict


class DomainExpression:
    """
    Parse dan evaluate domain expressions
    
    Supports:
    - Simple filters: {'status': 'active'}
    - Variable substitution: {'unit': '${user.unit_id}'}
    - Lookups: {'price__gte': 100}
    - Multiple conditions (AND): {'status': 'active', 'is_public': True}
    
    Example:
        domain = DomainExpression({'unit': '${user.unit_id}'})
        result = domain.evaluate(user)
        # Returns: {'unit': 5} (if user.unit_id = 5)
    """
    
    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(self, domain: Dict[str, Any]):
        """
        Initialize domain expression
        
        Args:
            domain: Dictionary of field: value pairs
        """
        self.domain = domain or {}
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate domain dengan variable substitution
        
        Args:
            context: Dictionary dengan variables (e.g., {'user': user_obj})
        
        Returns:
            Evaluated domain dictionary
        """
        evaluated = {}
        
        for field, value in self.domain.items():
            evaluated[field] = self._evaluate_value(value, context)
        
        return evaluated
    
    def _evaluate_value(self, value: Any, context: Dict[str, Any]) -> Any:
        """
        Evaluate single value (with variable substitution jika ada)
        
        Args:
            value: Value to evaluate
            context: Context dictionary
        
        Returns:
            Evaluated value
        """
        # If value is string with variable, substitute
        if isinstance(value, str) and '${' in value:
            return self._substitute_variable(value, context)
        
        # If value is dict, recursively evaluate
        if isinstance(value, dict):
            return {k: self._evaluate_value(v, context) for k, v in value.items()}
        
        # If value is list, evaluate each item
        if isinstance(value, list):
            return [self._evaluate_value(v, context) for v in value]
        
        # Otherwise return as-is
        return value
    
    def _substitute_variable(self, value: str, context: Dict[str, Any]) -> Any:
        """
        Substitute variable in string
        
        Args:
            value: String with variable (e.g., '${user.unit_id}')
            context: Context dictionary
        
        Returns:
            Substituted value
        
        Example:
            value = '${user.unit_id}'
            context = {'user': user_obj}  # user_obj.unit_id = 5
            
            Result: 5
        """
        match = self.VARIABLE_PATTERN.search(value)
        
        if not match:
            return value
        
        variable_path = match.group(1)  # e.g., 'user.unit_id'
        
        # Get value from context
        result = self._get_nested_value(context, variable_path)
        
        # If entire string is just the variable, return the value
        if value == f'${{{variable_path}}}':
            return result
        
        # Otherwise, replace variable in string
        return value.replace(f'${{{variable_path}}}', str(result))
    
    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """
        Get nested value dari object using dot notation
        
        Args:
            obj: Object or dictionary
            path: Dot-separated path (e.g., 'user.profile.unit_id')
        
        Returns:
            Value at path
        
        Example:
            obj = {'user': user_obj}
            path = 'user.unit_id'
            
            Result: user_obj.unit_id
        """
        parts = path.split('.')
        current = obj
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
            
            if current is None:
                return None
        
        return current
    
    def is_empty(self) -> bool:
        """Check if domain is empty"""
        return not self.domain
    
    def __str__(self):
        return str(self.domain)
    
    def __repr__(self):
        return f"DomainExpression({self.domain})"


def parse_domain(domain: Dict[str, Any]) -> DomainExpression:
    """
    Helper function untuk create DomainExpression
    
    Args:
        domain: Domain dictionary
    
    Returns:
        DomainExpression instance
    """
    return DomainExpression(domain)

