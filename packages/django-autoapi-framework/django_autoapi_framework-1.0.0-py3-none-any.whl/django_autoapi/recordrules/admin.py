"""
Django Admin untuk Record Rules
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from .models import RecordRule, RecordRuleBypass


@admin.register(RecordRule)
class RecordRuleAdmin(admin.ModelAdmin):
    """
    Admin interface untuk RecordRule
    """
    
    list_display = [
        'name',
        'content_type',
        'active_badge',
        'priority',
        'permissions_display',
        'scope_display',
        'created_at'
    ]
    
    list_filter = [
        'active',
        'global_rule',
        'content_type',
        'perm_read',
        'perm_write',
        'perm_create',
        'perm_delete',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'domain_filter'
    ]
    
    filter_horizontal = ['groups']
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'domain_preview'
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': (
                'name',
                'active',
                'content_type',
                'priority'
            )
        }),
        ('Domain Filter', {
            'fields': (
                'domain_filter',
                'domain_preview'
            ),
            'description': 'Use ${user.field} for variable substitution'
        }),
        ('Permissions', {
            'fields': (
                'perm_read',
                'perm_write',
                'perm_create',
                'perm_delete'
            )
        }),
        ('Scope', {
            'fields': (
                'global_rule',
                'groups'
            ),
            'description': 'Global rules apply to all users. Otherwise, select groups.'
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def active_badge(self, obj):
        """Display active status as badge"""
        if obj.active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    active_badge.short_description = 'Status'
    
    def permissions_display(self, obj):
        """Display permissions as badges"""
        perms = []
        if obj.perm_read:
            perms.append('R')
        if obj.perm_write:
            perms.append('W')
        if obj.perm_create:
            perms.append('C')
        if obj.perm_delete:
            perms.append('D')
        
        return format_html(
            '<span style="background-color: #007bff; color: white; '
            'padding: 3px 8px; border-radius: 3px; font-family: monospace;">{}</span>',
            ' '.join(perms) if perms else 'None'
        )
    permissions_display.short_description = 'Permissions'
    
    def scope_display(self, obj):
        """Display scope (global or groups)"""
        if obj.global_rule:
            return format_html(
                '<span style="background-color: #ffc107; color: black; '
                'padding: 3px 10px; border-radius: 3px;">Global</span>'
            )
        
        group_count = obj.groups.count()
        if group_count == 0:
            return format_html(
                '<span style="color: #dc3545;">No groups assigned</span>'
            )
        
        return format_html(
            '{} group(s)',
            group_count
        )
    scope_display.short_description = 'Scope'
    
    def domain_preview(self, obj):
        """Preview domain filter"""
        import json
        return format_html(
            '<pre style="background-color: #f8f9fa; padding: 10px; '
            'border-radius: 5px; max-width: 600px;">{}</pre>',
            json.dumps(obj.domain_filter, indent=2)
        )
    domain_preview.short_description = 'Domain Preview'
    
    def save_model(self, request, obj, form, change):
        """Override save to invalidate cache"""
        super().save_model(request, obj, form, change)
        
        # Invalidate cache for this model
        from .registry import RecordRuleRegistry
        if obj.content_type:
            model_class = obj.content_type.model_class()
            if model_class:
                RecordRuleRegistry.invalidate(model_class)
    
    def delete_model(self, request, obj):
        """Override delete to invalidate cache"""
        model_class = obj.content_type.model_class() if obj.content_type else None
        
        super().delete_model(request, obj)
        
        # Invalidate cache
        if model_class:
            from .registry import RecordRuleRegistry
            RecordRuleRegistry.invalidate(model_class)
    
    actions = ['activate_rules', 'deactivate_rules', 'test_rule']
    
    def activate_rules(self, request, queryset):
        """Bulk activate rules"""
        count = queryset.update(active=True)
        
        # Invalidate cache
        from .registry import RecordRuleRegistry
        RecordRuleRegistry.invalidate()
        
        self.message_user(request, f'{count} rule(s) activated.')
    activate_rules.short_description = 'Activate selected rules'
    
    def deactivate_rules(self, request, queryset):
        """Bulk deactivate rules"""
        count = queryset.update(active=False)
        
        # Invalidate cache
        from .registry import RecordRuleRegistry
        RecordRuleRegistry.invalidate()
        
        self.message_user(request, f'{count} rule(s) deactivated.')
    deactivate_rules.short_description = 'Deactivate selected rules'


@admin.register(RecordRuleBypass)
class RecordRuleBypassAdmin(admin.ModelAdmin):
    """
    Admin interface untuk RecordRuleBypass
    """
    
    list_display = [
        'user',
        'content_type',
        'active_badge',
        'reason',
        'created_at'
    ]
    
    list_filter = [
        'active',
        'content_type',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'reason'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Bypass Info', {
            'fields': (
                'user',
                'content_type',
                'active',
                'reason'
            ),
            'description': 'Leave content_type blank to bypass all models'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def active_badge(self, obj):
        """Display active status as badge"""
        if obj.active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    active_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Override save to invalidate cache"""
        super().save_model(request, obj, form, change)
        
        # Invalidate bypass cache
        from .registry import RecordRuleRegistry
        RecordRuleRegistry.invalidate()
    
    def delete_model(self, request, obj):
        """Override delete to invalidate cache"""
        super().delete_model(request, obj)
        
        # Invalidate cache
        from .registry import RecordRuleRegistry
        RecordRuleRegistry.invalidate()


# Register to admin site
# This happens automatically via @admin.register decorators

