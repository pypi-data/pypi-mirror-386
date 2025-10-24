"""
Tests untuk RecordRule models
"""

import pytest
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models

from django_autoapi.recordrules.models import RecordRule, RecordRuleBypass


@pytest.fixture
def user():
    """Create test user"""
    return User.objects.create_user('testuser', 'test@example.com', 'password')


@pytest.fixture
def group():
    """Create test group"""
    return Group.objects.create(name='Test Group')


# Use sample_model from conftest.py instead of creating duplicate fixture
# to avoid model conflicts. sample_model already has all required fields.


@pytest.mark.django_db(transaction=True)
def test_create_record_rule(sample_model):
    """Test: Create record rule"""
    ct = ContentType.objects.get_for_model(sample_model)

    rule = RecordRule.objects.create(
        name='Test Rule',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True
    )

    assert rule.name == 'Test Rule'
    assert rule.perm_read is True
    assert rule.domain_filter == {'status': 'active'}


@pytest.mark.django_db(transaction=True)
def test_record_rule_applies_to_user(user, group, sample_model):
    """Test: Check if rule applies to user"""
    ct = ContentType.objects.get_for_model(sample_model)

    rule = RecordRule.objects.create(
        name='Group Rule',
        content_type=ct,
        domain_filter={},
        perm_read=True
    )
    rule.groups.add(group)

    # User not in group - rule doesn't apply
    assert rule.applies_to_user(user) is False

    # Add user to group
    user.groups.add(group)

    # Now rule applies
    assert rule.applies_to_user(user) is True


@pytest.mark.django_db(transaction=True)
def test_global_rule_applies_to_all(user, sample_model):
    """Test: Global rule applies to all users"""
    ct = ContentType.objects.get_for_model(sample_model)

    rule = RecordRule.objects.create(
        name='Global Rule',
        content_type=ct,
        domain_filter={},
        perm_read=True,
        global_rule=True
    )

    # Applies to any user
    assert rule.applies_to_user(user) is True


@pytest.mark.django_db(transaction=True)
def test_superuser_bypasses_rules(sample_model):
    """Test: Superusers bypass all rules"""
    superuser = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    ct = ContentType.objects.get_for_model(sample_model)

    rule = RecordRule.objects.create(
        name='Rule',
        content_type=ct,
        domain_filter={},
        perm_read=True,
        global_rule=True
    )

    # Superuser bypasses
    assert rule.applies_to_user(superuser) is False


@pytest.mark.django_db(transaction=True)
def test_record_rule_bypass(user, sample_model):
    """Test: Record rule bypass"""
    ct = ContentType.objects.get_for_model(sample_model)

    bypass = RecordRuleBypass.objects.create(
        user=user,
        content_type=ct,
        reason='Testing'
    )

    assert bypass.user == user
    assert bypass.content_type == ct
    assert bypass.active is True

    