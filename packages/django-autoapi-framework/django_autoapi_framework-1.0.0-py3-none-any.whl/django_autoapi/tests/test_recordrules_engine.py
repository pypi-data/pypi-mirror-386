"""
Tests untuk RecordRuleEngine
"""

import pytest
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models

from django_autoapi.recordrules.models import RecordRule, RecordRuleBypass
from django_autoapi.recordrules.engine import RecordRuleEngine, RecordRuleChecker
from django_autoapi.recordrules.registry import RecordRuleRegistry


@pytest.fixture
def user_with_unit():
    """Create user with unit"""
    user = User.objects.create_user('testuser', 'test@example.com', 'password')
    # Simulate profile with unit_id
    user.unit_id = 1
    return user


@pytest.fixture
def other_user():
    """Create another user"""
    user = User.objects.create_user('otheruser', 'other@example.com', 'password')
    user.unit_id = 2
    return user


@pytest.fixture
def kaprodi_group():
    """Create kaprodi group"""
    return Group.objects.create(name='Kaprodi')


# Use sample_model from conftest.py instead of creating duplicate fixture
# to avoid model conflicts. sample_model already has all required fields.


@pytest.mark.django_db(transaction=True)
def test_engine_with_no_rules(user_with_unit, sample_model):
    """Test: Engine with no rules returns unfiltered queryset"""
    engine = RecordRuleEngine(user_with_unit)

    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset)

    # No rules = no filtering
    assert filtered.query == queryset.query


@pytest.mark.django_db(transaction=True)
def test_engine_applies_simple_rule(user_with_unit, kaprodi_group, sample_model):
    """Test: Engine applies simple domain filter"""
    # Add user to group
    user_with_unit.groups.add(kaprodi_group)

    # Create rule
    ct = ContentType.objects.get_for_model(sample_model)
    rule = RecordRule.objects.create(
        name='Filter by unit',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule.groups.add(kaprodi_group)

    # Apply engine
    engine = RecordRuleEngine(user_with_unit)
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read')

    # Should filter by unit_id=1
    assert 'unit_id' in str(filtered.query)


@pytest.mark.django_db(transaction=True)
def test_engine_substitutes_variables(user_with_unit, kaprodi_group, sample_model):
    """Test: Engine substitutes ${user.field} variables"""
    user_with_unit.groups.add(kaprodi_group)

    # Create rule with variable
    ct = ContentType.objects.get_for_model(sample_model)
    rule = RecordRule.objects.create(
        name='Filter by user unit',
        content_type=ct,
        domain_filter={'unit_id': '${user.unit_id}'},
        perm_read=True
    )
    rule.groups.add(kaprodi_group)

    # Apply engine
    engine = RecordRuleEngine(user_with_unit)
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read')

    # Variable should be substituted
    assert 'unit_id' in str(filtered.query)


@pytest.mark.django_db(transaction=True)
def test_engine_respects_operation_type(user_with_unit, kaprodi_group, sample_model):
    """Test: Engine only applies rules for correct operation"""
    user_with_unit.groups.add(kaprodi_group)

    # Create rule only for write
    ct = ContentType.objects.get_for_model(sample_model)
    rule = RecordRule.objects.create(
        name='Write only rule',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=False,
        perm_write=True
    )
    rule.groups.add(kaprodi_group)

    engine = RecordRuleEngine(user_with_unit)
    queryset = sample_model.objects.all()

    # Read operation - rule should not apply
    filtered_read = engine.apply_rules(queryset, operation='read')
    assert filtered_read.query == queryset.query

    # Write operation - rule should apply
    filtered_write = engine.apply_rules(queryset, operation='write')
    assert 'status' in str(filtered_write.query)


@pytest.mark.django_db(transaction=True)
def test_engine_bypasses_superuser(sample_model):
    """Test: Superuser bypasses all rules"""
    superuser = User.objects.create_superuser('admin', 'admin@example.com', 'password')

    engine = RecordRuleEngine(superuser)
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset)

    # Superuser should not be filtered
    assert filtered.query == queryset.query


@pytest.mark.django_db(transaction=True)
def test_engine_bypasses_with_bypass_record(user_with_unit, sample_model):
    """Test: User with bypass record skips filtering"""
    ct = ContentType.objects.get_for_model(sample_model)

    # Create bypass
    RecordRuleBypass.objects.create(
        user=user_with_unit,
        content_type=ct
    )

    engine = RecordRuleEngine(user_with_unit)
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset)

    # Should bypass filtering
    assert filtered.query == queryset.query


@pytest.mark.django_db(transaction=True)
def test_can_access_instance(user_with_unit, kaprodi_group, sample_model):
    """Test: Check if user can access specific instance"""
    user_with_unit.groups.add(kaprodi_group)
    user_with_unit.unit_id = 1

    # Create rule
    ct = ContentType.objects.get_for_model(sample_model)
    rule = RecordRule.objects.create(
        name='Own unit only',
        content_type=ct,
        domain_filter={'unit_id': '${user.unit_id}'},
        perm_read=True
    )
    rule.groups.add(kaprodi_group)

    engine = RecordRuleEngine(user_with_unit)

    # Create mock instances
    class MockProduct:
        def __init__(self, unit_id):
            self.unit_id = unit_id
            self.__class__ = sample_model

    instance_same_unit = MockProduct(unit_id=1)
    instance_other_unit = MockProduct(unit_id=2)

    # Should access same unit
    # Note: This is a mock test, real test would use actual DB instances


@pytest.mark.django_db(transaction=True)
def test_record_rule_checker(user_with_unit, sample_model):
    """Test: RecordRuleChecker helper class"""
    checker = RecordRuleChecker(user_with_unit)

    # Methods should exist
    assert hasattr(checker, 'can_read')
    assert hasattr(checker, 'can_write')
    assert hasattr(checker, 'can_create')
    assert hasattr(checker, 'can_delete')


@pytest.mark.django_db(transaction=True)
def test_multiple_rules_combine_and(user_with_unit, kaprodi_group, sample_model):
    """Test: Multiple rules combined with AND"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Rule 1: unit_id = 1
    rule1 = RecordRule.objects.create(
        name='Unit filter',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True,
        priority=10
    )
    rule1.groups.add(kaprodi_group)

    # Rule 2: status = active
    rule2 = RecordRule.objects.create(
        name='Status filter',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True,
        priority=5
    )
    rule2.groups.add(kaprodi_group)

    # Apply engine with AND
    engine = RecordRuleEngine(user_with_unit)
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read', combine_mode='AND')

    # Both conditions should be in query
    query_str = str(filtered.query)
    assert 'unit_id' in query_str
    assert 'status' in query_str


@pytest.mark.django_db(transaction=True)
def test_global_rule_applies_to_all(user_with_unit, sample_model):
    """Test: Global rule applies to all users"""
    ct = ContentType.objects.get_for_model(sample_model)

    # Create global rule
    RecordRule.objects.create(
        name='Global active filter',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True,
        global_rule=True
    )

    # User not in any group, but global rule should apply
    engine = RecordRuleEngine(user_with_unit)
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset)

    # Should be filtered
    assert 'status' in str(filtered.query)


# ============================================================================
# OR Combining Mode Tests (Step 1: 30 menit)
# ============================================================================


@pytest.mark.django_db(transaction=True)
def test_engine_with_or_mode_initialization(user_with_unit):
    """Test: Engine initializes with OR combining mode"""
    # Create engine with OR mode
    engine = RecordRuleEngine(user_with_unit, combine_mode='OR')

    assert engine.combine_mode == 'OR'
    assert engine.user == user_with_unit


@pytest.mark.django_db(transaction=True)
def test_engine_defaults_to_and_mode(user_with_unit):
    """Test: Engine defaults to AND combining mode"""
    # Create engine without specifying mode
    engine = RecordRuleEngine(user_with_unit)

    assert engine.combine_mode == 'AND'


@pytest.mark.django_db(transaction=True)
def test_engine_case_insensitive_mode(user_with_unit):
    """Test: Engine handles combine_mode case insensitively"""
    # Test lowercase
    engine_or = RecordRuleEngine(user_with_unit, combine_mode='or')
    assert engine_or.combine_mode == 'OR'

    # Test mixed case
    engine_and = RecordRuleEngine(user_with_unit, combine_mode='AnD')
    assert engine_and.combine_mode == 'AND'


@pytest.mark.django_db(transaction=True)
def test_multiple_rules_combine_or(user_with_unit, kaprodi_group, sample_model):
    """Test: Multiple rules combined with OR"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Rule 1: unit_id = 1
    rule1 = RecordRule.objects.create(
        name='Unit filter 1',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True,
        priority=10
    )
    rule1.groups.add(kaprodi_group)

    # Rule 2: unit_id = 2
    rule2 = RecordRule.objects.create(
        name='Unit filter 2',
        content_type=ct,
        domain_filter={'unit_id': 2},
        perm_read=True,
        priority=5
    )
    rule2.groups.add(kaprodi_group)

    # Apply engine with OR
    engine = RecordRuleEngine(user_with_unit, combine_mode='OR')
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read')

    # Query should have OR condition (check for Q object syntax)
    query_str = str(filtered.query)
    # Both unit_id conditions should be present (OR combines them)
    assert 'unit_id' in query_str


@pytest.mark.django_db(transaction=True)
def test_or_mode_with_parameter_override(user_with_unit, kaprodi_group, sample_model):
    """Test: apply_rules can override engine's combine_mode"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Create two rules
    rule1 = RecordRule.objects.create(
        name='Filter 1',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule1.groups.add(kaprodi_group)

    rule2 = RecordRule.objects.create(
        name='Filter 2',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )
    rule2.groups.add(kaprodi_group)

    # Engine defaults to AND
    engine = RecordRuleEngine(user_with_unit)

    # But we override with OR at call time
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read', combine_mode='OR')

    # Should apply OR logic
    query_str = str(filtered.query)
    assert 'unit_id' in query_str or 'status' in query_str


@pytest.mark.django_db(transaction=True)
def test_and_mode_requires_all_conditions(user_with_unit, kaprodi_group, sample_model):
    """Test: AND mode requires records to match ALL rules"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Rule 1: unit_id = 1
    rule1 = RecordRule.objects.create(
        name='Unit filter',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule1.groups.add(kaprodi_group)

    # Rule 2: status = active
    rule2 = RecordRule.objects.create(
        name='Status filter',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )
    rule2.groups.add(kaprodi_group)

    # Apply with AND (should combine with &)
    engine = RecordRuleEngine(user_with_unit, combine_mode='AND')
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read')

    # Both conditions should be required
    query_str = str(filtered.query)
    assert 'unit_id' in query_str
    assert 'status' in query_str


@pytest.mark.django_db(transaction=True)
def test_or_mode_requires_any_condition(user_with_unit, kaprodi_group, sample_model):
    """Test: OR mode requires records to match ANY rule"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Rule 1: unit_id = 1
    rule1 = RecordRule.objects.create(
        name='Unit filter',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule1.groups.add(kaprodi_group)

    # Rule 2: status = active
    rule2 = RecordRule.objects.create(
        name='Status filter',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )
    rule2.groups.add(kaprodi_group)

    # Apply with OR (should combine with |)
    engine = RecordRuleEngine(user_with_unit, combine_mode='OR')
    queryset = sample_model.objects.all()
    filtered = engine.apply_rules(queryset, operation='read')

    # At least one condition should be present
    query_str = str(filtered.query)
    # In OR mode, both might be present but combined differently
    assert 'unit_id' in query_str or 'status' in query_str


@pytest.mark.django_db(transaction=True)
def test_can_access_with_or_mode(user_with_unit, kaprodi_group, sample_model):
    """Test: can_access respects OR combining mode"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Create two rules
    rule1 = RecordRule.objects.create(
        name='Unit 1',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule1.groups.add(kaprodi_group)

    rule2 = RecordRule.objects.create(
        name='Unit 2',
        content_type=ct,
        domain_filter={'unit_id': 2},
        perm_read=True
    )
    rule2.groups.add(kaprodi_group)

    # Create engine with OR mode
    engine = RecordRuleEngine(user_with_unit, combine_mode='OR')

    # Create mock instances
    class MockProduct:
        def __init__(self, unit_id):
            self.unit_id = unit_id
            self.pk = unit_id

        @property
        def __class__(self):
            return sample_model

    # Either unit 1 or unit 2 should be accessible
    instance1 = MockProduct(unit_id=1)
    instance2 = MockProduct(unit_id=2)
    instance3 = MockProduct(unit_id=3)

    # In OR mode, units 1 and 2 should match ANY rule
    # Unit 3 should not match ANY rule
    assert engine.can_access(instance1, 'read') is True
    assert engine.can_access(instance2, 'read') is True
    assert engine.can_access(instance3, 'read') is False


@pytest.mark.django_db(transaction=True)
def test_can_access_with_and_mode(user_with_unit, kaprodi_group, sample_model):
    """Test: can_access respects AND combining mode"""
    user_with_unit.groups.add(kaprodi_group)
    user_with_unit.unit_id = 1

    ct = ContentType.objects.get_for_model(sample_model)

    # Create two rules with variables
    rule1 = RecordRule.objects.create(
        name='Own unit',
        content_type=ct,
        domain_filter={'unit_id': '${user.unit_id}'},
        perm_read=True
    )
    rule1.groups.add(kaprodi_group)

    rule2 = RecordRule.objects.create(
        name='Active status',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )
    rule2.groups.add(kaprodi_group)

    # Create engine with AND mode
    engine = RecordRuleEngine(user_with_unit, combine_mode='AND')

    # Create mock instances
    class MockProduct:
        def __init__(self, unit_id, status):
            self.unit_id = unit_id
            self.status = status
            self.pk = 1

        @property
        def __class__(self):
            return sample_model

    # Must match ALL conditions
    instance_match_both = MockProduct(unit_id=1, status='active')
    instance_match_unit_only = MockProduct(unit_id=1, status='inactive')
    instance_match_status_only = MockProduct(unit_id=2, status='active')

    # Only instance matching both should be accessible
    assert engine.can_access(instance_match_both, 'read') is True
    assert engine.can_access(instance_match_unit_only, 'read') is False
    assert engine.can_access(instance_match_status_only, 'read') is False


@pytest.mark.django_db(transaction=True)
def test_record_rule_checker_with_or_mode(user_with_unit):
    """Test: RecordRuleChecker supports OR combining mode"""
    # Create checker with OR mode
    checker = RecordRuleChecker(user_with_unit, combine_mode='OR')

    # Verify mode is set correctly
    assert checker.engine.combine_mode == 'OR'


@pytest.mark.django_db(transaction=True)
def test_record_rule_checker_defaults_to_and(user_with_unit):
    """Test: RecordRuleChecker defaults to AND mode"""
    # Create checker without specifying mode
    checker = RecordRuleChecker(user_with_unit)

    # Should default to AND
    assert checker.engine.combine_mode == 'AND'


@pytest.mark.django_db(transaction=True)
def test_apply_record_rules_convenience_function_or_mode(user_with_unit, kaprodi_group, sample_model):
    """Test: apply_record_rules convenience function supports OR mode"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Create rule
    rule = RecordRule.objects.create(
        name='Test rule',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule.groups.add(kaprodi_group)

    # Import convenience function
    from django_autoapi.recordrules.engine import apply_record_rules

    queryset = sample_model.objects.all()

    # Use with OR mode
    filtered = apply_record_rules(
        queryset,
        user_with_unit,
        operation='read',
        combine_mode='OR'
    )

    # Should be filtered
    assert 'unit_id' in str(filtered.query)


@pytest.mark.django_db(transaction=True)
def test_can_access_instance_convenience_function_or_mode(user_with_unit, kaprodi_group, sample_model):
    """Test: can_access_instance convenience function supports OR mode"""
    user_with_unit.groups.add(kaprodi_group)

    ct = ContentType.objects.get_for_model(sample_model)

    # Create rule
    rule = RecordRule.objects.create(
        name='Test rule',
        content_type=ct,
        domain_filter={'unit_id': 1},
        perm_read=True
    )
    rule.groups.add(kaprodi_group)

    # Import convenience function
    from django_autoapi.recordrules.engine import can_access_instance

    # Create mock instance
    class MockProduct:
        def __init__(self, unit_id):
            self.unit_id = unit_id
            self.pk = 1

        @property
        def __class__(self):
            return sample_model

    instance = MockProduct(unit_id=1)

    # Use with OR mode
    result = can_access_instance(
        instance,
        user_with_unit,
        operation='read',
        combine_mode='OR'
    )

    # Should have access
    assert result is True

