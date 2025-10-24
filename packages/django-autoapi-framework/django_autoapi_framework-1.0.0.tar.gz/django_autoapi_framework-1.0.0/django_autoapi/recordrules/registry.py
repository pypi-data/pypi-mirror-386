"""
Registry untuk record rules - cache rules untuk performance
"""

from typing import List, Optional
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models


class RecordRuleRegistry:
    """
    Central registry untuk record rules
    
    Features:
    - Cache rules untuk performance
    - Quick lookup by model
    - Invalidation on rule changes
    
    Usage:
        # Get rules for model
        rules = RecordRuleRegistry.get_rules_for_model(Mahasiswa)
        
        # Get rules for user
        rules = RecordRuleRegistry.get_rules_for_user(user, Mahasiswa)
        
        # Invalidate cache
        RecordRuleRegistry.invalidate(Mahasiswa)
    """
    
    CACHE_PREFIX = 'autoapi_recordrules'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @classmethod
    def get_rules_for_model(cls, model_class, operation='read'):
        """
        Get all active rules for a model
        
        Args:
            model_class: Django model class
            operation: 'read', 'write', 'create', 'delete'
        
        Returns:
            QuerySet of RecordRule objects
        """
        from .models import RecordRule
        
        # Get or create cache key
        cache_key = cls._get_cache_key(model_class, operation)
        
        # Try cache first
        rules = cache.get(cache_key)
        
        if rules is None:
            # Get content type
            content_type = ContentType.objects.get_for_model(model_class)
            
            # Query rules
            rules = RecordRule.objects.filter(
                content_type=content_type,
                active=True
            ).prefetch_related('groups')
            
            # Filter by operation
            if operation == 'read':
                rules = rules.filter(perm_read=True)
            elif operation == 'write':
                rules = rules.filter(perm_write=True)
            elif operation == 'create':
                rules = rules.filter(perm_create=True)
            elif operation == 'delete':
                rules = rules.filter(perm_delete=True)
            
            # Order by priority
            rules = rules.order_by('-priority', 'id')
            
            # Convert to list for caching
            rules = list(rules)
            
            # Cache it
            cache.set(cache_key, rules, cls.CACHE_TIMEOUT)
        
        return rules
    
    @classmethod
    def get_rules_for_user(cls, user, model_class, operation='read'):
        """
        Get rules that apply to specific user
        
        Args:
            user: Django user object
            model_class: Django model class
            operation: 'read', 'write', 'create', 'delete'
        
        Returns:
            List of RecordRule objects applicable to user
        """
        # Get all rules for model
        all_rules = cls.get_rules_for_model(model_class, operation)
        
        # Filter rules that apply to this user
        applicable_rules = [
            rule for rule in all_rules
            if rule.applies_to_user(user)
        ]
        
        return applicable_rules
    
    @classmethod
    def has_bypass(cls, user, model_class=None):
        """
        Check if user has bypass for given model
        
        Args:
            user: Django user object
            model_class: Django model class (None = check for any bypass)
        
        Returns:
            bool: True if user can bypass rules
        """
        from .models import RecordRuleBypass
        
        # Superusers always bypass
        if user.is_superuser:
            return True
        
        # Check bypass cache
        cache_key = f'{cls.CACHE_PREFIX}_bypass_{user.id}'
        if model_class:
            cache_key += f'_{model_class.__name__}'
        
        has_bypass = cache.get(cache_key)
        
        if has_bypass is None:
            # Query bypasses
            bypasses = RecordRuleBypass.objects.filter(
                user=user,
                active=True
            )
            
            if model_class:
                content_type = ContentType.objects.get_for_model(model_class)
                bypasses = bypasses.filter(
                    models.Q(content_type=content_type) | models.Q(content_type__isnull=True)
                )
            
            has_bypass = bypasses.exists()
            
            # Cache result
            cache.set(cache_key, has_bypass, cls.CACHE_TIMEOUT)
        
        return has_bypass
    
    @classmethod
    def invalidate(cls, model_class=None):
        """
        Invalidate cache for model

        Args:
            model_class: Django model class (None = invalidate all)
        """
        if model_class:
            # Invalidate specific model
            for operation in ['read', 'write', 'create', 'delete']:
                cache_key = cls._get_cache_key(model_class, operation)
                cache.delete(cache_key)
        else:
            # Invalidate all
            # Note: Some cache backends (like LocMemCache) don't support delete_pattern
            # So we use clear() as fallback for test compatibility
            try:
                cache.delete_pattern(f'{cls.CACHE_PREFIX}_*')
            except (AttributeError, NotImplementedError):
                # Fallback for cache backends that don't support delete_pattern
                # This is mainly for LocMemCache used in tests
                cache.clear()
    
    @classmethod
    def _get_cache_key(cls, model_class, operation):
        """Generate cache key for model and operation"""
        model_name = f'{model_class._meta.app_label}.{model_class._meta.model_name}'
        return f'{cls.CACHE_PREFIX}_{model_name}_{operation}'


# Helper functions
def get_rules_for_model(model_class, operation='read'):
    """Shortcut untuk RecordRuleRegistry.get_rules_for_model"""
    return RecordRuleRegistry.get_rules_for_model(model_class, operation)


def get_rules_for_user(user, model_class, operation='read'):
    """Shortcut untuk RecordRuleRegistry.get_rules_for_user"""
    return RecordRuleRegistry.get_rules_for_user(user, model_class, operation)


def invalidate_rules(model_class=None):
    """Shortcut untuk RecordRuleRegistry.invalidate"""
    return RecordRuleRegistry.invalidate(model_class)

