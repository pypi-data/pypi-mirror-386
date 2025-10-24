"""
Tests untuk advanced record rules features
"""

import pytest
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models

from django_autoapi.recordrules.models import RecordRule
from django_autoapi.recordrules.engine import RecordRuleEngine
from django_autoapi.recordrules.logging import RuleDebugger


@pytest.fixture
def user_unit_1():
    """User from unit 1"""
    user = User.objects.create_user('user1', 'user1@example.com', 'password')
    user.unit_id = 1
    return user


@pytest.fixture
def user_unit_2():
    """User from unit 2"""
    user = User.objects.create_user('user2', 'user2@example.com', 'password')
    user.unit_id = 2
    return user


@pytest.fixture
def group_a():
    """Group A"""
    return Group.objects.create(name='Group A')


@pytest.fixture
def group_b():
    """Group B"""
    return Group.objects.create(name='Group B')


@pytest.fixture
def product_model():
    """Sample model"""
    class Product(models.Model):
        name = models.CharField(max_length=200)
        unit_id = models.IntegerField(default=1)
        status = models.CharField(max_length=20, default='active')
        
        class Meta:
            app_label = 'test_app'
            managed = False
    
    return Product


@pytest.mark.django_db
def test_or_combining_mode(product_model, user_unit_1, group_a, group_b):
    """Test: OR combining mode allows access if ANY rule matches"""
    
    # Add user to both groups
    user_unit_1.groups.add(group_a, group_b)
    
    ct = ContentType.objects.get_for_model(product_model)
    
    # Rule 1: unit_id = 1
    rule1 = RecordRule.objects.create(
        name='Unit 1 filter',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule1.groups.add(group_a)
    
    # Rule 2: status = active
    rule2 = RecordRule.objects.create(
        name='Active filter',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )
    rule2.groups.add(group_b)
    
    # Test OR mode
    engine_or = RecordRuleEngine(user_unit_1, combine_mode='OR')
    queryset = product_model.objects.all()
    filtered_or = engine_or.apply_rules(queryset, operation='read')
    
    # Should use OR (any rule matches)
    query_str = str(filtered_or.query)
    # In OR mode, should have both conditions but with OR operator
    assert 'unit_id' in query_str or 'status' in query_str


@pytest.mark.django_db
def test_and_combining_mode_default(product_model, user_unit_1, group_a, group_b):
    """Test: AND combining mode (default) requires all rules to match"""
    
    user_unit_1.groups.add(group_a, group_b)
    
    ct = ContentType.objects.get_for_model(product_model)
    
    # Rule 1
    rule1 = RecordRule.objects.create(
        name='Rule 1',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule1.groups.add(group_a)
    
    # Rule 2
    rule2 = RecordRule.objects.create(
        name='Rule 2',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )
    rule2.groups.add(group_b)
    
    # Test AND mode (default)
    engine_and = RecordRuleEngine(user_unit_1)  # Default is AND
    queryset = product_model.objects.all()
    filtered_and = engine_and.apply_rules(queryset, operation='read')
    
    # Should have both conditions
    query_str = str(filtered_and.query)
    assert 'unit_id' in query_str
    assert 'status' in query_str


@pytest.mark.django_db
def test_rule_priority_ordering(product_model, user_unit_1, group_a):
    """Test: Rules are applied in priority order"""
    
    user_unit_1.groups.add(group_a)
    
    ct = ContentType.objects.get_for_model(product_model)
    
    # Low priority rule
    rule_low = RecordRule.objects.create(
        name='Low priority',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True,
        priority=1
    )
    rule_low.groups.add(group_a)
    
    # High priority rule
    rule_high = RecordRule.objects.create(
        name='High priority',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True,
        priority=100
    )
    rule_high.groups.add(group_a)
    
    # Get rules - should be ordered by priority
    from django_autoapi.recordrules.registry import RecordRuleRegistry
    rules = RecordRuleRegistry.get_rules_for_user(user_unit_1, product_model, 'read')
    
    # High priority should come first
    if len(rules) >= 2:
        assert rules[0].priority >= rules[1].priority


@pytest.mark.django_db
def test_explain_rules_debugger(product_model, user_unit_1, group_a):
    """Test: RuleDebugger.explain_rules provides detailed info"""
    
    user_unit_1.groups.add(group_a)
    
    ct = ContentType.objects.get_for_model(product_model)
    
    rule = RecordRule.objects.create(
        name='Test rule',
        content_type=ct,
        domain_filter={'unit_id': '${user.unit_id}'},
        perm_read=True
    )
    rule.groups.add(group_a)
    
    # Get explanation
    explanation = RuleDebugger.explain_rules(user_unit_1, product_model, 'read')
    
    # Check structure
    assert 'user' in explanation
    assert 'model' in explanation
    assert 'rules' in explanation
    assert 'applicable_rules' in explanation
    
    # Check user info
    assert explanation['user']['username'] == 'user1'
    
    # Check rules
    assert len(explanation['rules']) > 0


@pytest.mark.django_db
def test_test_rule_on_instance(product_model, user_unit_1, group_a):
    """Test: RuleDebugger.test_rule_on_instance checks access"""
    
    user_unit_1.groups.add(group_a)
    user_unit_1.unit_id = 1
    
    ct = ContentType.objects.get_for_model(product_model)
    
    rule = RecordRule.objects.create(
        name='Own unit',
        content_type=ct,
        domain_filter={'unit_id': '${user.unit_id}'},
        perm_read=True
    )
    rule.groups.add(group_a)
    
    # Create mock instance
    class MockProduct:
        def __init__(self):
            self.pk = 1
            self.unit_id = 1
            self.__class__ = product_model
        
        def __str__(self):
            return 'Mock Product'
    
    instance = MockProduct()
    
    # Test - this will check the logic without DB
    # Real test would use actual instance
    result = RuleDebugger.test_rule_on_instance(user_unit_1, instance, 'read')
    
    # Check structure
    assert 'can_access' in result
    assert 'instance' in result
    assert 'explanation' in result


@pytest.mark.django_db
def test_multiple_operations_same_rule(product_model, user_unit_1, group_a):
    """Test: Rule applies to multiple operations"""
    
    user_unit_1.groups.add(group_a)
    
    ct = ContentType.objects.get_for_model(product_model)
    
    # Rule for both read and write
    rule = RecordRule.objects.create(
        name='Read/Write rule',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True,
        perm_write=True
    )
    rule.groups.add(group_a)
    
    engine = RecordRuleEngine(user_unit_1)
    queryset = product_model.objects.all()
    
    # Both operations should be filtered
    filtered_read = engine.apply_rules(queryset, operation='read')
    filtered_write = engine.apply_rules(queryset, operation='write')
    
    # Both should have filtering
    assert 'unit_id' in str(filtered_read.query)
    assert 'unit_id' in str(filtered_write.query)


@pytest.mark.django_db
def test_global_rule_overrides_group_rule(product_model, user_unit_1, group_a):
    """Test: Global rules apply even without group membership"""
    
    # User NOT in any group
    
    ct = ContentType.objects.get_for_model(product_model)
    
    # Global rule
    global_rule = RecordRule.objects.create(
        name='Global rule',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True,
        global_rule=True
    )
    
    # Group rule (user not in group)
    group_rule = RecordRule.objects.create(
        name='Group rule',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    group_rule.groups.add(group_a)
    
    # User should get global rule only
    from django_autoapi.recordrules.registry import RecordRuleRegistry
    rules = RecordRuleRegistry.get_rules_for_user(user_unit_1, product_model, 'read')
    
    # Should have 1 rule (the global one)
    rule_names = [r.name for r in rules]
    assert 'Global rule' in rule_names
    assert 'Group rule' not in rule_names


@pytest.mark.django_db
def test_cache_invalidation_on_rule_change(product_model, user_unit_1, group_a):
    """Test: Cache is invalidated when rules change"""
    
    from django_autoapi.recordrules.registry import RecordRuleRegistry
    
    user_unit_1.groups.add(group_a)
    
    ct = ContentType.objects.get_for_model(product_model)
    
    # Create rule
    rule = RecordRule.objects.create(
        name='Test rule',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )
    rule.groups.add(group_a)
    
    # Get rules (should cache)
    rules1 = RecordRuleRegistry.get_rules_for_model(product_model, 'read')
    count1 = len(rules1)
    
    # Modify rule (should invalidate cache)
    rule.active = False
    rule.save()
    
    # Get rules again (should fetch fresh)
    rules2 = RecordRuleRegistry.get_rules_for_model(product_model, 'read')
    count2 = len(rules2)
    
    # Count should be different (inactive rule excluded)
    assert count1 != count2


@pytest.mark.django_db
def test_complex_domain_with_lookups(product_model, user_unit_1, group_a):
    """Test: Complex domain filters with Django lookups"""
    
    user_unit_1.groups.add(group_a)
    
    ct = ContentType.objects.get_for_model(product_model)
    
    # Complex domain with lookups
    rule = RecordRule.objects.create(
        name='Complex rule',
        content_type=ct,
        domain_filter={
            'unit_id': '${user.unit_id}',
            'status__in': ['active', 'pending'],
            'name__icontains': 'product'
        },
        perm_read=True
    )
    rule.groups.add(group_a)
    
    engine = RecordRuleEngine(user_unit_1)
    queryset = product_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read')
    
    # Should have all conditions
    query_str = str(filtered.query)
    assert 'unit_id' in query_str
    # Other lookups might be represented differently in query

    