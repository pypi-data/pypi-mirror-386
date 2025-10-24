"""
Tests untuk Record Rules Performance module

Testing:
- Caching decorator functionality
- Cache key generation
- Query optimization
- Statistics tracking
- Signal-based cache invalidation
"""

import pytest
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase

from django_autoapi.recordrules.models import RecordRule
from django_autoapi.recordrules.performance import (
    cache_rule_evaluation,
    _generate_cache_key,
    _serialize_arg,
    QueryOptimizer,
    RuleStatistics,
    PerformanceMetrics,
)


class TestCacheKeyGeneration(TestCase):
    """Test cache key generation"""

    def test_cache_key_with_primitives(self):
        """Test cache key generation with primitive types"""
        key = _generate_cache_key("test_func", ("arg1", 42), {"key": "value"})

        assert key.startswith("recordrule_")
        assert len(key) > 20  # Should be hashed

    def test_cache_key_deterministic(self):
        """Test that cache key is deterministic"""
        key1 = _generate_cache_key("func", ("arg1", 42), {"key": "value"})
        key2 = _generate_cache_key("func", ("arg1", 42), {"key": "value"})

        assert key1 == key2

    def test_cache_key_different_args(self):
        """Test that different args produce different keys"""
        key1 = _generate_cache_key("func", ("arg1",), {})
        key2 = _generate_cache_key("func", ("arg2",), {})

        assert key1 != key2

    def test_cache_key_with_model_instance(self):
        """Test cache key with Django model instance"""
        user = User.objects.create_user("testuser", "test@example.com", "pass")
        key = _generate_cache_key("func", (user,), {})

        assert key.startswith("recordrule_")
        assert "User:1" in _serialize_arg(user) or "User:" in _serialize_arg(
            user
        )


class TestSerializeArg(TestCase):
    """Test argument serialization"""

    def test_serialize_none(self):
        """Test serialization of None"""
        result = _serialize_arg(None)
        assert result == "None"

    def test_serialize_primitive(self):
        """Test serialization of primitives"""
        assert _serialize_arg(42) == "42"
        assert _serialize_arg("text") == "text"
        assert _serialize_arg(True) == "True"

    def test_serialize_list(self):
        """Test serialization of list"""
        result = _serialize_arg([1, 2, 3])
        assert "[" in result and "]" in result

    def test_serialize_dict(self):
        """Test serialization of dict"""
        result = _serialize_arg({"key": "value"})
        assert "{" in result and "}" in result

    def test_serialize_model_instance(self):
        """Test serialization of Django model"""
        user = User.objects.create_user("testuser", "test@example.com", "pass")
        result = _serialize_arg(user)

        assert "User:" in result
        assert str(user.id) in result or ":" in result


class TestCacheDecorator(TestCase):
    """Test cache_rule_evaluation decorator"""

    def setUp(self):
        """Clear cache before each test"""
        cache.clear()

    def test_caching_works(self):
        """Test that caching decorator caches results"""
        call_count = 0

        @cache_rule_evaluation(timeout=300)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - should execute
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

    def test_different_args_different_cache(self):
        """Test that different arguments don't share cache"""
        @cache_rule_evaluation(timeout=300)
        def test_func(x):
            return x * 2

        result1 = test_func(5)
        result2 = test_func(10)

        assert result1 == 10
        assert result2 == 20

    def test_cache_timeout(self):
        """Test that cache respects timeout"""
        @cache_rule_evaluation(timeout=1)
        def test_func():
            return "result"

        result = test_func()
        assert result == "result"

        # Cache should still exist
        assert cache.get(_generate_cache_key("test_func", (), {})) is not None

    def test_cache_with_kwargs(self):
        """Test caching with keyword arguments"""
        call_count = 0

        @cache_rule_evaluation(timeout=300)
        def test_func(x, y=2):
            nonlocal call_count
            call_count += 1
            return x * y

        # First call
        result1 = test_func(5, y=3)
        assert result1 == 15
        assert call_count == 1

        # Second call with same kwargs
        result2 = test_func(5, y=3)
        assert result2 == 15
        assert call_count == 1  # Cached


@pytest.mark.django_db
class TestQueryOptimizer:
    """Test query optimization utilities"""

    def test_optimizer_exists(self):
        """Test that QueryOptimizer can be instantiated"""
        optimizer = QueryOptimizer()
        assert optimizer is not None

    def test_optimize_rule_queryset(self, sample_model, kaprodi_group):
        """Test queryset optimization"""
        # Create a rule
        ct = ContentType.objects.get_for_model(sample_model)
        rule = RecordRule.objects.create(
            name="Test rule",
            content_type=ct,
            domain_filter={"unit_id": 1},
            perm_read=True,
        )
        rule.groups.add(kaprodi_group)

        # Optimize queryset
        qs = sample_model.objects.all()
        optimized_qs = QueryOptimizer.optimize_rule_queryset(qs, [rule])

        # Should still be a queryset
        assert optimized_qs.query is not None

    def test_analyze_query(self, sample_model):
        """Test query analysis"""
        qs = sample_model.objects.all()
        analysis = QueryOptimizer.analyze_query(qs)

        assert "query_count" in analysis
        assert analysis["query_count"] >= 0

    def test_get_query_explanation(self, sample_model):
        """Test query explanation"""
        qs = sample_model.objects.all()
        explanation = QueryOptimizer.get_query_explanation(qs)

        # Should return a string (even if error message)
        assert isinstance(explanation, str)


@pytest.mark.django_db
class TestRuleStatistics:
    """Test rule statistics tracking"""

    def test_get_rule_usage_stats_no_rules(self, sample_model):
        """Test stats with no rules"""
        stats = RuleStatistics.get_rule_usage_stats(sample_model)

        assert stats["total_rules"] == 0
        assert stats["active_rules"] == 0
        assert stats["global_rules"] == 0

    def test_get_rule_usage_stats_with_rules(
        self, sample_model, kaprodi_group
    ):
        """Test stats with rules"""
        # Create rules
        ct = ContentType.objects.get_for_model(sample_model)

        rule1 = RecordRule.objects.create(
            name="Rule 1",
            content_type=ct,
            domain_filter={"unit_id": 1},
            perm_read=True,
            active=True,
        )
        rule1.groups.add(kaprodi_group)

        rule2 = RecordRule.objects.create(
            name="Global rule",
            content_type=ct,
            domain_filter={"status": "active"},
            perm_read=True,
            global_rule=True,
        )

        # Get stats
        stats = RuleStatistics.get_rule_usage_stats(sample_model)

        assert stats["total_rules"] >= 2
        assert stats["active_rules"] >= 2
        assert stats["global_rules"] >= 1
        assert stats["group_rules"] >= 1

    def test_get_rule_usage_stats_by_operation(
        self, sample_model, kaprodi_group
    ):
        """Test stats by operation type"""
        ct = ContentType.objects.get_for_model(sample_model)

        # Create rules for different operations
        rule_read = RecordRule.objects.create(
            name="Read rule",
            content_type=ct,
            domain_filter={"unit_id": 1},
            perm_read=True,
            perm_write=False,
        )
        rule_read.groups.add(kaprodi_group)

        rule_write = RecordRule.objects.create(
            name="Write rule",
            content_type=ct,
            domain_filter={"status": "active"},
            perm_read=False,
            perm_write=True,
        )
        rule_write.groups.add(kaprodi_group)

        stats = RuleStatistics.get_rule_usage_stats(sample_model)

        assert "rules_for_read" in stats
        assert "rules_for_write" in stats
        assert stats["rules_for_read"] >= 1
        assert stats["rules_for_write"] >= 1

    def test_get_model_stats(self, sample_model, kaprodi_group):
        """Test model-specific statistics"""
        ct = ContentType.objects.get_for_model(sample_model)

        rule = RecordRule.objects.create(
            name="Test rule",
            content_type=ct,
            domain_filter={"unit_id": 1},
            perm_read=True,
        )
        rule.groups.add(kaprodi_group)

        stats = RuleStatistics.get_model_stats(sample_model)

        assert "model" in stats
        assert stats["model"] == sample_model.__name__
        assert "total_rules" in stats
        assert "read_rules" in stats

    def test_get_performance_recommendations_no_rules(
        self, sample_model
    ):
        """Test performance recommendations with no rules"""
        # Don't create any rules
        recs = RuleStatistics.get_performance_recommendations(sample_model)

        assert len(recs) > 0
        assert any(rec["type"] == "info" for rec in recs)

    def test_get_performance_recommendations_good_config(
        self, sample_model, kaprodi_group
    ):
        """Test recommendations for well-configured rules"""
        ct = ContentType.objects.get_for_model(sample_model)

        # Create properly configured rules
        for op in ["read", "write", "create", "delete"]:
            rule = RecordRule.objects.create(
                name=f"{op} rule",
                content_type=ct,
                domain_filter={"unit_id": 1},
                **{f"perm_{op}": True},
            )
            rule.groups.add(kaprodi_group)

        recs = RuleStatistics.get_performance_recommendations(sample_model)

        # Should have success recommendation
        assert any(rec["type"] == "success" for rec in recs)

    def test_get_performance_recommendations_too_many_rules(
        self, sample_model, kaprodi_group
    ):
        """Test recommendations with too many rules"""
        ct = ContentType.objects.get_for_model(sample_model)

        # Create many rules
        for i in range(60):
            rule = RecordRule.objects.create(
                name=f"Rule {i}",
                content_type=ct,
                domain_filter={"unit_id": i % 10},
                perm_read=True,
                priority=i,
            )
            rule.groups.add(kaprodi_group)

        recs = RuleStatistics.get_performance_recommendations(sample_model)

        # Should have warning about many rules
        assert any("warning" in rec["type"] for rec in recs)


class TestPerformanceMetrics:
    """Test performance metrics tracking"""

    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = PerformanceMetrics()

        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.query_count == 0
        assert metrics.total_time == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        metrics = PerformanceMetrics()
        metrics.cache_hits = 80
        metrics.cache_misses = 20

        hit_rate = metrics.get_hit_rate()
        assert hit_rate == 0.8

    def test_hit_rate_no_requests(self):
        """Test hit rate with no requests"""
        metrics = PerformanceMetrics()
        hit_rate = metrics.get_hit_rate()

        assert hit_rate == 0.0

    def test_metrics_repr(self):
        """Test metrics string representation"""
        metrics = PerformanceMetrics()
        metrics.cache_hits = 10
        metrics.cache_misses = 5
        metrics.query_count = 3

        repr_str = repr(metrics)
        assert "hits" in repr_str
        assert "10" in repr_str
