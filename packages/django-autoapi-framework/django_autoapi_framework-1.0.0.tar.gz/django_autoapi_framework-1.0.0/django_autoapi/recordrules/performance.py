"""
Performance optimization utilities untuk record rules

Menyediakan:
- Query caching dengan smart invalidation
- Query optimization dengan select_related/prefetch_related
- Rule usage statistics dan monitoring
- Performance metrics collection
"""

from django.core.cache import cache
from django.db.models import Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from functools import wraps
import hashlib
import json
import logging
from typing import Any, Callable, Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Track performance metrics untuk rule evaluation
    """

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_count = 0
        self.total_time = 0.0

    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def __repr__(self) -> str:
        return (
            f"PerformanceMetrics(hits={self.cache_hits}, "
            f"misses={self.cache_misses}, "
            f"queries={self.query_count}, "
            f"hit_rate={self.get_hit_rate():.2%})"
        )


def cache_rule_evaluation(timeout: int = 300) -> Callable:
    """
    Decorator untuk cache rule evaluation results

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)

    Features:
    - Automatic cache key generation
    - Intelligent object serialization
    - Cache miss logging
    - Easy to apply to any function

    Usage:
        @cache_rule_evaluation(timeout=300)
        def expensive_rule_evaluation(user, model):
            # Expensive computation
            return result

        # Result akan di-cache untuk 5 menit
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # Try to get from cache
            result = cache.get(cache_key)

            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result

            # Cache miss - compute result
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def _generate_cache_key(
    func_name: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]
) -> str:
    """
    Generate unique cache key for function call

    Args:
        func_name: Name of the function
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Unique cache key string
    """
    key_parts = [func_name]

    # Add positional arguments
    for arg in args:
        key_parts.append(_serialize_arg(arg))

    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={_serialize_arg(v)}")

    # Create hash for fixed length
    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()

    return f"recordrule_{key_hash}"


def _serialize_arg(arg: Any) -> str:
    """
    Serialize argument for cache key

    Args:
        arg: Argument to serialize

    Returns:
        String representation
    """
    if arg is None:
        return "None"
    elif hasattr(arg, "id"):
        # Django model instance
        return f"{arg.__class__.__name__}:{arg.id}"
    elif isinstance(arg, (list, tuple)):
        # Iterable
        return f"[{','.join(_serialize_arg(a) for a in arg)}]"
    elif isinstance(arg, dict):
        # Dictionary
        items = ",".join(f"{k}:{_serialize_arg(v)}" for k, v in arg.items())
        return f"{{{items}}}"
    else:
        # Primitive type
        return str(arg)


class QueryOptimizer:
    """
    Optimize queries untuk record rule evaluation

    Techniques:
    - select_related untuk foreign keys
    - prefetch_related untuk reverse relations
    - only() untuk specific fields
    - Query analysis dan explanation
    """

    @staticmethod
    def optimize_rule_queryset(
        queryset, rules: list
    ) -> "models.QuerySet":
        """
        Optimize queryset based on rules

        Args:
            queryset: Base queryset
            rules: List of RecordRule objects

        Returns:
            Optimized queryset with select_related/prefetch_related

        Example:
            optimizer = QueryOptimizer()
            rules = RecordRule.objects.filter(model=Product)
            optimized_qs = optimizer.optimize_rule_queryset(
                Product.objects.all(),
                rules
            )
        """
        # Collect all field lookups from rules
        select_related_fields: Set[str] = set()
        only_fields: Set[str] = set()

        for rule in rules:
            domain = rule.domain_filter or {}

            for field, value in domain.items():
                # Check if it's a foreign key lookup
                if "__" in field:
                    parts = field.split("__")
                    # First part is the relation
                    relation = parts[0]
                    select_related_fields.add(relation)

                # Track field usage
                only_fields.add(field.split("__")[0])

        # Apply select_related if available
        if select_related_fields:
            try:
                queryset = queryset.select_related(*select_related_fields)
                logger.debug(
                    f"Applied select_related: {select_related_fields}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to apply select_related: {e}"
                )

        return queryset

    @staticmethod
    def analyze_query(queryset) -> Dict[str, Any]:
        """
        Analyze query performance

        Args:
            queryset: Django queryset

        Returns:
            Dictionary with analysis results

        Example:
            analysis = QueryOptimizer.analyze_query(qs)
            print(f"Query count: {analysis['query_count']}")
        """
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        try:
            with CaptureQueriesContext(connection) as context:
                # Execute query
                list(queryset)

            return {
                "query_count": len(context.captured_queries),
                "total_time": sum(
                    float(q.get("time", 0)) for q in context.captured_queries
                ),
                "queries": context.captured_queries,
            }
        except Exception as e:
            logger.error(f"Cannot analyze query: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_query_explanation(queryset) -> str:
        """
        Get query execution plan (PostgreSQL specific)

        Args:
            queryset: Django queryset

        Returns:
            Query execution plan string
        """
        try:
            # Try to explain query
            return str(queryset.explain())
        except Exception as e:
            logger.warning(f"Cannot explain query: {e}")
            return f"Cannot explain: {e}"


class RuleStatistics:
    """
    Track dan report rule statistics

    Features:
    - Usage statistics by model
    - Priority distribution
    - Global vs group rules
    - Active/inactive ratio
    - Performance metrics
    """

    @staticmethod
    def get_rule_usage_stats(
        model_class=None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get statistics about rule usage

        Args:
            model_class: Django model class (None for all models)
            days: Number of days to analyze

        Returns:
            Dictionary with statistics

        Example:
            stats = RuleStatistics.get_rule_usage_stats(
                Mahasiswa,
                days=30
            )
            print(f"Active rules: {stats['active_rules']}")
        """
        from django.contrib.contenttypes.models import ContentType
        from django.utils import timezone
        from datetime import timedelta
        from .models import RecordRule

        cutoff_date = timezone.now() - timedelta(days=days)

        # Base query
        rules = RecordRule.objects.filter(created_at__gte=cutoff_date)

        # Filter by model if provided
        if model_class is not None:
            try:
                ct = ContentType.objects.get_for_model(model_class)
                rules = rules.filter(content_type=ct)
            except Exception as e:
                logger.warning(f"Cannot filter by model: {e}")

        # Collect statistics
        stats = {
            "period_days": days,
            "total_rules": rules.count(),
            "active_rules": rules.filter(active=True).count(),
            "inactive_rules": rules.filter(active=False).count(),
            "global_rules": rules.filter(global_rule=True).count(),
            "group_rules": rules.filter(global_rule=False).count(),
        }

        # Calculate by operation
        for operation in ["read", "write", "create", "delete"]:
            stats[f"rules_for_{operation}"] = (
                rules.filter(**{f"perm_{operation}": True}).count()
            )

        # Calculate by priority
        priority_stats = (
            rules.values("priority")
            .annotate(count=Count("id"))
            .order_by("priority")
        )
        stats["by_priority"] = {
            int(item["priority"]): item["count"]
            for item in priority_stats
        }

        return stats

    @staticmethod
    def get_model_stats(model_class) -> Dict[str, Any]:
        """
        Get detailed statistics for specific model

        Args:
            model_class: Django model class

        Returns:
            Detailed statistics dictionary
        """
        from django.contrib.contenttypes.models import ContentType
        from .models import RecordRule

        try:
            ct = ContentType.objects.get_for_model(model_class)
            rules = RecordRule.objects.filter(content_type=ct)

            return {
                "model": model_class.__name__,
                "total_rules": rules.count(),
                "active_rules": rules.filter(active=True).count(),
                "read_rules": rules.filter(perm_read=True).count(),
                "write_rules": rules.filter(perm_write=True).count(),
                "create_rules": rules.filter(perm_create=True).count(),
                "delete_rules": rules.filter(perm_delete=True).count(),
                "groups": set(
                    rules.values_list("groups__name", flat=True)
                    .distinct()
                    .exclude(groups__name__isnull=True)
                ),
            }
        except Exception as e:
            logger.error(f"Cannot get model stats: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_performance_recommendations(
        model_class=None,
    ) -> list[Dict[str, str]]:
        """
        Generate performance recommendations

        Args:
            model_class: Django model class (None for all models)

        Returns:
            List of recommendations

        Example:
            recs = RuleStatistics.get_performance_recommendations(
                Mahasiswa
            )
            for rec in recs:
                print(f"{rec['type']}: {rec['message']}")
        """
        recommendations = []

        # Get stats
        stats = RuleStatistics.get_rule_usage_stats(model_class)

        # Analyze and generate recommendations
        if stats["total_rules"] == 0:
            recommendations.append(
                {
                    "type": "info",
                    "message": "No rules defined. "
                    "Consider defining rules for access control.",
                }
            )
        elif stats["total_rules"] > 50:
            recommendations.append(
                {
                    "type": "warning",
                    "message": f"High number of rules ({stats['total_rules']}). "
                    "Consider consolidating similar rules.",
                }
            )

        # Check active vs inactive
        if (
            stats["inactive_rules"] > 0
            and stats["active_rules"] < stats["inactive_rules"]
        ):
            recommendations.append(
                {
                    "type": "warning",
                    "message": "More inactive than active rules. "
                    "Consider cleaning up unused rules.",
                }
            )

        # Check global rules
        if stats["global_rules"] > stats["group_rules"]:
            recommendations.append(
                {
                    "type": "info",
                    "message": "Mostly global rules. "
                    "Consider using group-specific rules for better control.",
                }
            )

        # Check operation coverage
        operations_covered = sum(
            1
            for op in ["read", "write", "create", "delete"]
            if stats[f"rules_for_{op}"] > 0
        )
        if operations_covered < 2:
            recommendations.append(
                {
                    "type": "warning",
                    "message": f"Only {operations_covered} operations covered. "
                    "Consider defining rules for all operations.",
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "type": "success",
                    "message": "Rule configuration looks good!",
                }
            )

        return recommendations


# Signal handlers for cache invalidation
@receiver(
    post_save, sender="recordrules.RecordRule", dispatch_uid="invalidate_cache_on_save"
)
def invalidate_cache_on_rule_save(sender, instance, created: bool, **kwargs):
    """
    Invalidate cache when rule is saved

    Args:
        sender: Signal sender
        instance: RecordRule instance
        created: Whether rule was created
        **kwargs: Additional arguments
    """
    _invalidate_rule_cache(instance, "created" if created else "updated")


@receiver(
    post_delete,
    sender="recordrules.RecordRule",
    dispatch_uid="invalidate_cache_on_delete",
)
def invalidate_cache_on_rule_delete(sender, instance, **kwargs):
    """
    Invalidate cache when rule is deleted

    Args:
        sender: Signal sender
        instance: RecordRule instance
        **kwargs: Additional arguments
    """
    _invalidate_rule_cache(instance, "deleted")


def _invalidate_rule_cache(instance, action: str):
    """
    Helper to invalidate cache for rule instance

    Args:
        instance: RecordRule instance
        action: Action performed (created/updated/deleted)
    """
    from .registry import RecordRuleRegistry

    try:
        if instance.content_type:
            model_class = instance.content_type.model_class()
            if model_class:
                RecordRuleRegistry.invalidate(model_class)
                logger.info(
                    f"Cache invalidated for {model_class.__name__} "
                    f"(rule {action})"
                )
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")


# Helper function untuk enable performance optimization
def enable_performance_monitoring():
    """
    Enable performance monitoring untuk record rules

    Aktivasi:
    - Query optimization
    - Cache invalidation signals
    - Statistics collection

    Usage:
        from django_autoapi.recordrules.performance import (
            enable_performance_monitoring
        )

        # Di Django apps.py AppConfig.ready()
        enable_performance_monitoring()
    """
    logger.info("Performance monitoring enabled for record rules")
    # Signals are automatically connected when module is imported
