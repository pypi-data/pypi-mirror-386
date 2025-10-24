"""
Record Rule models
"""

from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
import json


class RecordRule(models.Model):
    """
    Record Rule untuk row-level security
    
    Mirip Odoo Record Rules - filter data berdasarkan user/group
    
    Example:
        # Kaprodi only sees their unit's students
        RecordRule.objects.create(
            name='Kaprodi: Own Unit',
            content_type=ContentType.objects.get_for_model(Mahasiswa),
            domain_filter={'unit': '${user.unit}'},
            perm_read=True
        ).groups.add(kaprodi_group)
    """
    
    # Basic info
    name = models.CharField(
        max_length=200,
        help_text='Descriptive name for this rule'
    )
    
    active = models.BooleanField(
        default=True,
        help_text='Enable/disable this rule'
    )
    
    # Target model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Model to apply this rule to'
    )
    
    # Domain filter (JSON)
    domain_filter = models.JSONField(
        help_text='Filter criteria in JSON format. Use ${} for variables.',
        default=dict,
        blank=True  # Allow empty dict for global rules
    )
    
    # Permissions
    perm_read = models.BooleanField(
        default=True,
        help_text='Apply rule for read operations (GET)'
    )
    
    perm_write = models.BooleanField(
        default=False,
        help_text='Apply rule for write operations (POST, PUT, PATCH)'
    )
    
    perm_create = models.BooleanField(
        default=False,
        help_text='Apply rule for create operations (POST)'
    )
    
    perm_delete = models.BooleanField(
        default=False,
        help_text='Apply rule for delete operations (DELETE)'
    )
    
    # Who does this apply to?
    groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text='Groups this rule applies to'
    )
    
    global_rule = models.BooleanField(
        default=False,
        help_text='Apply to all users (ignore groups)'
    )
    
    # Priority (higher = applied first)
    priority = models.IntegerField(
        default=0,
        help_text='Higher priority rules are applied first'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'django_autoapi'
        ordering = ['-priority', 'name']
        verbose_name = 'Record Rule'
        verbose_name_plural = 'Record Rules'
    
    def __str__(self):
        return f"{self.name} ({self.content_type})"
    
    def clean(self):
        """Validate domain filter JSON"""
        if not isinstance(self.domain_filter, dict):
            raise ValidationError('domain_filter must be a dictionary')
    
    def save(self, *args, **kwargs):
        # Only validate domain_filter, skip content_type validation
        # Content type validation fails with dynamically created test models
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def model_class(self):
        """Get the Django model class"""
        return self.content_type.model_class()
    
    def applies_to_user(self, user):
        """
        Check if this rule applies to given user

        Args:
            user: Django user object

        Returns:
            bool: True if rule applies to this user
        """
        # Superusers bypass ALL rules, including global ones
        if user.is_superuser:
            return False

        # Global rules apply to everyone else
        if self.global_rule:
            return True

        # Check if user is in any of the rule's groups
        if self.groups.exists():
            user_groups = user.groups.all()
            return self.groups.filter(id__in=user_groups).exists()

        return False
    
    def applies_to_operation(self, operation):
        """
        Check if rule applies to given operation
        
        Args:
            operation: 'read', 'write', 'create', 'delete'
        
        Returns:
            bool: True if rule applies to this operation
        """
        operation_map = {
            'read': self.perm_read,
            'write': self.perm_write,
            'create': self.perm_create,
            'delete': self.perm_delete,
        }
        
        return operation_map.get(operation, False)
    
    def get_domain_for_user(self, user):
        """
        Get domain filter dengan variable substitution
        
        Args:
            user: Django user object
        
        Returns:
            dict: Processed domain filter
        
        Example:
            domain_filter = {'unit': '${user.unit_id}'}
            user.unit_id = 5
            
            Result: {'unit': 5}
        """
        from .engine import RecordRuleEngine
        return RecordRuleEngine.substitute_variables(self.domain_filter, user)


class RecordRuleBypass(models.Model):
    """
    Allow specific users to bypass record rules
    
    Example:
        # Dekan can bypass all Mahasiswa rules
        RecordRuleBypass.objects.create(
            user=dekan_user,
            content_type=ContentType.objects.get_for_model(Mahasiswa)
        )
    """
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        help_text='User who can bypass rules'
    )
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Specific model to bypass (null = all models)'
    )
    
    active = models.BooleanField(
        default=True,
        help_text='Enable/disable this bypass'
    )
    
    reason = models.CharField(
        max_length=200,
        blank=True,
        help_text='Reason for bypass (for auditing)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'django_autoapi'
        verbose_name = 'Record Rule Bypass'
        verbose_name_plural = 'Record Rule Bypasses'
        unique_together = [['user', 'content_type']]
    
    def __str__(self):
        model_name = self.content_type.model if self.content_type else 'All Models'
        return f"{self.user.username} - {model_name}"
    
    