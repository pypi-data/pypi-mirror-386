"""
Record Rule Engine - Evaluate dan apply rules ke queryset
"""

from typing import Any, Dict, Optional, List
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from .expressions import DomainExpression
from .registry import RecordRuleRegistry


class RecordRuleEngine:
    """
    Engine untuk evaluate dan apply record rules

    Features:
    - Evaluate domain expressions
    - Substitute variables (${user.field})
    - Apply filters to queryset
    - Combine multiple rules (AND/OR)
    - Handle bypasses

    Combining modes:
    - 'AND': All rules must match (default)
    - 'OR': Any rule can match

    Usage:
        # AND mode (default)
        engine = RecordRuleEngine(user)
        filtered_qs = engine.apply_rules(
            Mahasiswa.objects.all(),
            operation='read'
        )

        # OR mode
        engine = RecordRuleEngine(user, combine_mode='OR')
        filtered_qs = engine.apply_rules(
            Mahasiswa.objects.all(),
            operation='read'
        )
    """

    def __init__(self, user: User, combine_mode: str = 'AND'):
        """
        Initialize engine for specific user

        Args:
            user: Django user object
            combine_mode: 'AND' or 'OR' (default: 'AND')
                - 'AND': All rules must match
                - 'OR': Any rule can match
        """
        self.user = user
        self.combine_mode = combine_mode.upper()
    
    def apply_rules(
        self,
        queryset: models.QuerySet,
        operation: str = 'read',
        combine_mode: Optional[str] = None
    ) -> models.QuerySet:
        """
        Apply record rules to queryset

        Args:
            queryset: Django queryset to filter
            operation: 'read', 'write', 'create', 'delete'
            combine_mode: 'AND' or 'OR' (overrides instance default)

        Returns:
            Filtered queryset

        Example:
            engine = RecordRuleEngine(kaprodi_user)
            students = engine.apply_rules(
                Mahasiswa.objects.all(),
                operation='read'
            )
            # Returns: Only students from kaprodi's unit
        """
        model_class = queryset.model

        # Check if user can bypass rules
        if RecordRuleRegistry.has_bypass(self.user, model_class):
            return queryset

        # Get applicable rules
        rules = RecordRuleRegistry.get_rules_for_user(
            self.user,
            model_class,
            operation
        )

        # No rules = no filtering
        if not rules:
            return queryset

        # Determine combine mode (parameter overrides instance default)
        mode = combine_mode or self.combine_mode

        # Apply rules
        return self._apply_rule_list(queryset, rules, mode)
    
    def _apply_rule_list(
        self,
        queryset: models.QuerySet,
        rules: List,
        combine_mode: str = 'AND'
    ) -> models.QuerySet:
        """
        Apply list of rules to queryset

        Args:
            queryset: Django queryset
            rules: List of RecordRule objects
            combine_mode: 'AND' or 'OR'

        Returns:
            Filtered queryset

        Example:
            # AND mode - all rules must match
            # Returns records that match ALL rule conditions

            # OR mode - any rule can match
            # Returns records that match ANY rule condition
        """
        if not rules:
            return queryset

        # Build Q objects for each rule
        q_objects = []

        for rule in rules:
            q_obj = self._rule_to_q_object(rule)
            if q_obj is not None:
                q_objects.append(q_obj)

        # No valid filters
        if not q_objects:
            return queryset

        # Combine Q objects based on mode
        mode = combine_mode.upper()

        if mode == 'OR':
            # OR: Record matches if ANY rule matches
            combined_q = q_objects[0]
            for q_obj in q_objects[1:]:
                combined_q |= q_obj
        else:
            # AND: Record matches if ALL rules match (default)
            combined_q = q_objects[0]
            for q_obj in q_objects[1:]:
                combined_q &= q_obj

        # Apply to queryset
        return queryset.filter(combined_q)
    
    def _rule_to_q_object(self, rule) -> Optional[Q]:
        """
        Convert RecordRule to Django Q object
        
        Args:
            rule: RecordRule instance
        
        Returns:
            Q object or None
        """
        # Get domain with variables substituted
        domain = rule.get_domain_for_user(self.user)
        
        if not domain:
            return None
        
        # Convert domain dict to Q object
        return self._domain_to_q_object(domain)
    
    def _domain_to_q_object(self, domain: Dict[str, Any]) -> Q:
        """
        Convert domain dictionary to Django Q object
        
        Args:
            domain: Domain filter dictionary
        
        Returns:
            Q object
        
        Example:
            domain = {'unit_id': 5, 'status': 'active'}
            Result: Q(unit_id=5, status='active')
        """
        if not domain:
            return Q()
        
        # Build Q object from domain
        q_kwargs = {}
        
        for field, value in domain.items():
            q_kwargs[field] = value
        
        return Q(**q_kwargs)
    
    @staticmethod
    def substitute_variables(domain: Dict[str, Any], user: User) -> Dict[str, Any]:
        """
        Substitute variables in domain filter
        
        Args:
            domain: Domain filter with variables (e.g., ${user.unit_id})
            user: Django user object
        
        Returns:
            Domain with substituted values
        
        Example:
            domain = {'unit_id': '${user.profile.unit_id}'}
            user.profile.unit_id = 5
            
            Result: {'unit_id': 5}
        """
        expression = DomainExpression(domain)
        context = {'user': user}
        return expression.evaluate(context)
    
    def can_access(
        self,
        instance: models.Model,
        operation: str = 'read',
        combine_mode: Optional[str] = None
    ) -> bool:
        """
        Check if user can access specific instance

        Args:
            instance: Model instance
            operation: 'read', 'write', 'create', 'delete'
            combine_mode: 'AND' or 'OR' (overrides instance default)

        Returns:
            bool: True if user can access

        Example:
            # AND mode (default)
            engine = RecordRuleEngine(user)
            student = Mahasiswa.objects.get(id=1)

            if engine.can_access(student, 'read'):
                # User can read this student (matches ALL rules)

            # OR mode
            engine = RecordRuleEngine(user, combine_mode='OR')
            if engine.can_access(student, 'read'):
                # User can read this student (matches ANY rule)
        """
        model_class = instance.__class__

        # Check bypass
        if RecordRuleRegistry.has_bypass(self.user, model_class):
            return True

        # Get applicable rules
        rules = RecordRuleRegistry.get_rules_for_user(
            self.user,
            model_class,
            operation
        )

        # No rules = allowed
        if not rules:
            return True

        # Determine combine mode
        mode = (combine_mode or self.combine_mode).upper()

        # Check access based on combining mode
        if mode == 'OR':
            # OR: Check if instance matches ANY rule
            for rule in rules:
                if self._instance_matches_rule(instance, rule):
                    return True
            return False
        else:
            # AND: Check if instance matches ALL rules (default)
            for rule in rules:
                if not self._instance_matches_rule(instance, rule):
                    return False
            return True
    
    def _instance_matches_rule(self, instance: models.Model, rule) -> bool:
        """
        Check if instance matches rule domain
        
        Args:
            instance: Model instance
            rule: RecordRule instance
        
        Returns:
            bool: True if instance matches
        """
        domain = rule.get_domain_for_user(self.user)
        
        if not domain:
            return True
        
        # Check each condition
        for field, expected_value in domain.items():
            # Handle lookups (e.g., price__gte)
            if '__' in field:
                # Complex lookup - use queryset
                model_class = instance.__class__
                pk = instance.pk
                
                q_obj = Q(**{field: expected_value})
                exists = model_class.objects.filter(pk=pk).filter(q_obj).exists()
                
                if not exists:
                    return False
            else:
                # Simple field comparison
                actual_value = getattr(instance, field, None)
                
                if actual_value != expected_value:
                    return False
        
        return True
    
    def get_accessible_ids(
        self,
        model_class: type,
        operation: str = 'read'
    ) -> List[int]:
        """
        Get list of IDs user can access
        
        Args:
            model_class: Django model class
            operation: 'read', 'write', 'create', 'delete'
        
        Returns:
            List of accessible IDs
        
        Note: This can be expensive for large datasets
        """
        queryset = model_class.objects.all()
        filtered = self.apply_rules(queryset, operation)
        return list(filtered.values_list('id', flat=True))
    
    def filter_queryset(
        self,
        queryset: models.QuerySet,
        operation: str = 'read'
    ) -> models.QuerySet:
        """
        Alias for apply_rules (more explicit name)
        
        Args:
            queryset: Django queryset
            operation: Operation type
        
        Returns:
            Filtered queryset
        """
        return self.apply_rules(queryset, operation)


class RecordRuleChecker:
    """
    Helper class untuk check access tanpa filtering queryset

    Supports both AND and OR combining modes:
    - 'AND': User must pass ALL applicable rules (default)
    - 'OR': User must pass ANY applicable rule

    Usage:
        # AND mode (default)
        checker = RecordRuleChecker(user)

        if checker.can_read(student):
            # User can read this student

        if checker.can_write(student):
            # User can modify this student

        # OR mode
        checker = RecordRuleChecker(user, combine_mode='OR')

        if checker.can_read(student):
            # User can read this student (matches any rule)
    """

    def __init__(self, user: User, combine_mode: str = 'AND'):
        """
        Initialize checker

        Args:
            user: Django user object
            combine_mode: 'AND' or 'OR' (default: 'AND')
        """
        self.engine = RecordRuleEngine(user, combine_mode)

    def can_read(self, instance: models.Model) -> bool:
        """Check if user can read instance"""
        return self.engine.can_access(instance, 'read')

    def can_write(self, instance: models.Model) -> bool:
        """Check if user can write instance"""
        return self.engine.can_access(instance, 'write')

    def can_create(self, instance: models.Model) -> bool:
        """Check if user can create instance"""
        return self.engine.can_access(instance, 'create')

    def can_delete(self, instance: models.Model) -> bool:
        """Check if user can delete instance"""
        return self.engine.can_access(instance, 'delete')


# Convenience functions
def apply_record_rules(
    queryset: models.QuerySet,
    user: User,
    operation: str = 'read',
    combine_mode: str = 'AND'
) -> models.QuerySet:
    """
    Apply record rules to queryset

    Args:
        queryset: Django queryset
        user: User object
        operation: 'read', 'write', 'create', 'delete'
        combine_mode: 'AND' or 'OR' (default: 'AND')

    Returns:
        Filtered queryset

    Example:
        # AND mode (default)
        filtered = apply_record_rules(
            Mahasiswa.objects.all(),
            user,
            operation='read'
        )

        # OR mode
        filtered = apply_record_rules(
            Mahasiswa.objects.all(),
            user,
            operation='read',
            combine_mode='OR'
        )
    """
    engine = RecordRuleEngine(user, combine_mode)
    return engine.apply_rules(queryset, operation)


def can_access_instance(
    instance: models.Model,
    user: User,
    operation: str = 'read',
    combine_mode: str = 'AND'
) -> bool:
    """
    Check if user can access instance

    Args:
        instance: Model instance
        user: User object
        operation: 'read', 'write', 'create', 'delete'
        combine_mode: 'AND' or 'OR' (default: 'AND')

    Returns:
        bool: True if user can access

    Example:
        # AND mode (default)
        can_read = can_access_instance(
            student,
            user,
            operation='read'
        )

        # OR mode
        can_read = can_access_instance(
            student,
            user,
            operation='read',
            combine_mode='OR'
        )
    """
    engine = RecordRuleEngine(user, combine_mode)
    return engine.can_access(instance, operation)

