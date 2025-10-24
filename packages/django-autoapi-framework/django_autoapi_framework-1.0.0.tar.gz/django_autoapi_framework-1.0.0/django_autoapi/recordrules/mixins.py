"""
Mixins untuk integrate record rules dengan DRF ViewSets
"""

from rest_framework.exceptions import PermissionDenied, NotFound
from django.core.exceptions import ValidationError as DjangoValidationError

from .engine import RecordRuleEngine
from .registry import RecordRuleRegistry


class RecordRuleQuerySetMixin:
    """
    Mixin untuk apply record rules to ViewSet queryset
    
    Usage:
        class MyViewSet(RecordRuleQuerySetMixin, ModelViewSet):
            queryset = MyModel.objects.all()
            enable_record_rules = True
    
    Features:
    - Automatic queryset filtering
    - Instance access validation
    - Create/update validation
    """
    
    # Configuration
    enable_record_rules = True
    record_rule_operations = {
        'list': 'read',
        'retrieve': 'read',
        'create': 'create',
        'update': 'write',
        'partial_update': 'write',
        'destroy': 'delete',
    }
    
    def get_queryset(self):
        """
        Override get_queryset untuk apply record rules
        
        Returns:
            Filtered queryset based on user's record rules
        """
        queryset = super().get_queryset()
        
        # Check if record rules enabled
        if not self._should_apply_record_rules():
            return queryset
        
        # Get current operation
        operation = self._get_current_operation()
        
        if not operation:
            return queryset
        
        # Apply record rules
        user = self.request.user
        engine = RecordRuleEngine(user)
        
        try:
            filtered_queryset = engine.apply_rules(queryset, operation=operation)
            return filtered_queryset
        except Exception as e:
            # Log error but don't break
            # In production, use proper logging
            # logger.exception("Error applying record rules")
            return queryset
    
    def get_object(self):
        """
        Override get_object untuk validate access
        
        Returns:
            Object instance
        
        Raises:
            NotFound: If object not accessible by user
        """
        obj = super().get_object()
        
        # Check if record rules enabled
        if not self._should_apply_record_rules():
            return obj
        
        # Get current operation
        operation = self._get_current_operation()
        
        if not operation:
            return obj
        
        # Check access
        user = self.request.user
        engine = RecordRuleEngine(user)
        
        if not engine.can_access(obj, operation=operation):
            # Object exists but user can't access it
            # Return 404 to avoid leaking existence
            raise NotFound('Object not found.')
        
        return obj
    
    def perform_create(self, serializer):
        """
        Override perform_create untuk validate against rules
        
        Args:
            serializer: Serializer instance
        
        Raises:
            PermissionDenied: If creation violates record rules
        """
        # Save instance first
        instance = serializer.save()
        
        # Check if record rules enabled
        if not self._should_apply_record_rules():
            return
        
        # Validate created instance against rules
        user = self.request.user
        engine = RecordRuleEngine(user)
        
        if not engine.can_access(instance, operation='create'):
            # Roll back creation
            instance.delete()
            raise PermissionDenied(
                'You do not have permission to create this record.'
            )
    
    def perform_update(self, serializer):
        """
        Override perform_update untuk validate changes
        
        Args:
            serializer: Serializer instance
        
        Raises:
            PermissionDenied: If update violates record rules
        """
        instance = serializer.save()
        
        # Check if record rules enabled
        if not self._should_apply_record_rules():
            return
        
        # Validate updated instance still matches rules
        user = self.request.user
        engine = RecordRuleEngine(user)
        
        if not engine.can_access(instance, operation='write'):
            raise PermissionDenied(
                'You do not have permission to modify this record.'
            )
    
    def perform_destroy(self, instance):
        """
        Override perform_destroy untuk validate deletion
        
        Args:
            instance: Model instance
        
        Raises:
            PermissionDenied: If deletion violates record rules
        """
        # Check if record rules enabled
        if not self._should_apply_record_rules():
            super().perform_destroy(instance)
            return
        
        # Validate deletion permission
        user = self.request.user
        engine = RecordRuleEngine(user)
        
        if not engine.can_access(instance, operation='delete'):
            raise PermissionDenied(
                'You do not have permission to delete this record.'
            )
        
        # Proceed with deletion
        super().perform_destroy(instance)
    
    def _should_apply_record_rules(self):
        """
        Check if record rules should be applied
        
        Returns:
            bool: True if should apply
        """
        # Check enable flag
        if not getattr(self, 'enable_record_rules', False):
            return False
        
        # Check if user authenticated
        if not self.request.user.is_authenticated:
            return False
        
        # Check if model has rules
        model_class = self.queryset.model
        has_rules = RecordRuleRegistry.get_rules_for_model(model_class)
        
        return bool(has_rules)
    
    def _get_current_operation(self):
        """
        Get current operation type
        
        Returns:
            str: 'read', 'write', 'create', 'delete', or None
        """
        action = getattr(self, 'action', None)
        
        if not action:
            return None
        
        # Map action to operation
        operation_map = getattr(
            self,
            'record_rule_operations',
            {}
        )
        
        return operation_map.get(action)
    
    def check_record_rule_permissions(self, obj, operation):
        """
        Manually check record rule permissions
        
        Args:
            obj: Model instance
            operation: 'read', 'write', 'create', 'delete'
        
        Returns:
            bool: True if allowed
        
        Raises:
            PermissionDenied: If not allowed
        """
        if not self._should_apply_record_rules():
            return True
        
        user = self.request.user
        engine = RecordRuleEngine(user)
        
        if not engine.can_access(obj, operation=operation):
            raise PermissionDenied(
                f'You do not have permission to {operation} this record.'
            )
        
        return True


class RecordRulePermissionMixin:
    """
    Simplified mixin hanya untuk permission checking
    
    Usage:
        class MyViewSet(RecordRulePermissionMixin, ModelViewSet):
            enable_record_rules = True
    
    Note: Tidak auto-filter queryset, hanya check permissions
    """
    
    enable_record_rules = True
    
    def check_object_permissions(self, request, obj):
        """
        Check object permissions including record rules
        
        Args:
            request: Request object
            obj: Model instance
        """
        # Call parent
        super().check_object_permissions(request, obj)
        
        # Check record rules
        if not getattr(self, 'enable_record_rules', False):
            return
        
        if not request.user.is_authenticated:
            return
        
        # Determine operation
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            operation = 'read'
        elif request.method in ['POST']:
            operation = 'create'
        elif request.method in ['PUT', 'PATCH']:
            operation = 'write'
        elif request.method in ['DELETE']:
            operation = 'delete'
        else:
            return
        
        # Check access
        engine = RecordRuleEngine(request.user)
        
        if not engine.can_access(obj, operation=operation):
            raise PermissionDenied(
                'You do not have permission to access this record.'
            )
        
        