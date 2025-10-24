"""
Logging dan debugging utilities untuk record rules
"""

import logging
from typing import Any, Dict, List
from django.contrib.auth.models import User

logger = logging.getLogger('django_autoapi.recordrules')


class RuleLogger:
    """
    Logger untuk record rule operations
    """
    
    @staticmethod
    def log_rule_application(user: User, model_class, operation: str, rules: List):
        """
        Log when rules are applied
        
        Args:
            user: User object
            model_class: Model class
            operation: Operation type
            rules: List of applied rules
        """
        logger.info(
            f"Record Rules Applied | User: {user.username} | "
            f"Model: {model_class.__name__} | Operation: {operation} | "
            f"Rules: {len(rules)}"
        )
        
        for rule in rules:
            logger.debug(
                f"  - Rule: {rule.name} | Priority: {rule.priority} | "
                f"Domain: {rule.domain_filter}"
            )
    
    @staticmethod
    def log_access_denied(user: User, instance, operation: str):
        """
        Log when access is denied
        
        Args:
            user: User object
            instance: Model instance
            operation: Operation type
        """
        logger.warning(
            f"Access Denied | User: {user.username} | "
            f"Model: {instance.__class__.__name__} | "
            f"Instance ID: {instance.pk} | Operation: {operation}"
        )
    
    @staticmethod
    def log_bypass(user: User, model_class, reason: str = ''):
        """
        Log when user bypasses rules
        
        Args:
            user: User object
            model_class: Model class
            reason: Bypass reason
        """
        logger.info(
            f"Rules Bypassed | User: {user.username} | "
            f"Model: {model_class.__name__} | Reason: {reason or 'N/A'}"
        )
    
    @staticmethod
    def log_rule_evaluation_error(user: User, rule, error: Exception):
        """
        Log errors during rule evaluation
        
        Args:
            user: User object
            rule: RecordRule instance
            error: Exception that occurred
        """
        logger.error(
            f"Rule Evaluation Error | User: {user.username} | "
            f"Rule: {rule.name} | Error: {str(error)}",
            exc_info=True
        )


class RuleDebugger:
    """
    Debugging utilities untuk record rules
    """
    
    @staticmethod
    def explain_rules(user: User, model_class, operation: str = 'read'):
        """
        Explain which rules apply to user
        
        Args:
            user: User object
            model_class: Model class
            operation: Operation type
        
        Returns:
            Dictionary with explanation
        """
        from .registry import RecordRuleRegistry
        from .engine import RecordRuleEngine
        
        # Get rules
        all_rules = RecordRuleRegistry.get_rules_for_model(model_class, operation)
        applicable_rules = RecordRuleRegistry.get_rules_for_user(user, model_class, operation)
        
        # Check bypass
        has_bypass = RecordRuleRegistry.has_bypass(user, model_class)
        
        explanation = {
            'user': {
                'username': user.username,
                'is_superuser': user.is_superuser,
                'groups': [g.name for g in user.groups.all()]
            },
            'model': model_class.__name__,
            'operation': operation,
            'has_bypass': has_bypass,
            'total_rules': len(all_rules),
            'applicable_rules': len(applicable_rules),
            'rules': []
        }
        
        for rule in applicable_rules:
            # Get substituted domain
            engine = RecordRuleEngine(user)
            domain = engine.substitute_variables(rule.domain_filter, user)
            
            explanation['rules'].append({
                'name': rule.name,
                'priority': rule.priority,
                'global': rule.global_rule,
                'groups': [g.name for g in rule.groups.all()],
                'domain_original': rule.domain_filter,
                'domain_substituted': domain,
                'permissions': {
                    'read': rule.perm_read,
                    'write': rule.perm_write,
                    'create': rule.perm_create,
                    'delete': rule.perm_delete
                }
            })
        
        return explanation
    
    @staticmethod
    def test_rule_on_instance(user: User, instance, operation: str = 'read'):
        """
        Test if user can access specific instance
        
        Args:
            user: User object
            instance: Model instance
            operation: Operation type
        
        Returns:
            Dictionary with test results
        """
        from .engine import RecordRuleEngine
        
        engine = RecordRuleEngine(user)
        can_access = engine.can_access(instance, operation)
        
        # Get explanation
        explanation = RuleDebugger.explain_rules(
            user,
            instance.__class__,
            operation
        )
        
        return {
            'can_access': can_access,
            'instance': {
                'model': instance.__class__.__name__,
                'id': instance.pk,
                'str': str(instance)
            },
            'explanation': explanation
        }
    
    @staticmethod
    def get_filter_sql(user: User, model_class, operation: str = 'read'):
        """
        Get the SQL that will be generated by rules
        
        Args:
            user: User object
            model_class: Model class
            operation: Operation type
        
        Returns:
            SQL string
        """
        from .engine import RecordRuleEngine
        
        engine = RecordRuleEngine(user)
        queryset = model_class.objects.all()
        filtered = engine.apply_rules(queryset, operation)
        
        return {
            'sql': str(filtered.query),
            'params': filtered.query.sql_with_params()[1] if hasattr(filtered.query, 'sql_with_params') else []
        }


def debug_rules(user: User, model_class, operation: str = 'read', verbose: bool = True):
    """
    Debug helper function
    
    Args:
        user: User object
        model_class: Model class
        operation: Operation type
        verbose: Print detailed output
    
    Returns:
        Explanation dictionary
    """
    explanation = RuleDebugger.explain_rules(user, model_class, operation)
    
    if verbose:
        import json
        print("=" * 70)
        print("RECORD RULES DEBUG")
        print("=" * 70)
        print(json.dumps(explanation, indent=2))
        print("=" * 70)
    
    return explanation

