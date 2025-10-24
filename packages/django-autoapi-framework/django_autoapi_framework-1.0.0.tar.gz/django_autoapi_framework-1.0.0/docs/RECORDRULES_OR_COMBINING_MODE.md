# Record Rules - OR Combining Mode

## Overview

Record Rules Engine now supports both **AND** and **OR** combining modes for handling multiple rules. This feature allows flexible access control scenarios.

- **AND mode (default)**: User must pass ALL applicable rules to access data
- **OR mode**: User must pass ANY applicable rule to access data

## Quick Start

### AND Mode (Default)

```python
from django_autoapi.recordrules.engine import RecordRuleEngine

# Default behavior - AND mode
engine = RecordRuleEngine(user)
filtered_qs = engine.apply_rules(Mahasiswa.objects.all())
```

### OR Mode

```python
from django_autoapi.recordrules.engine import RecordRuleEngine

# Enable OR mode
engine = RecordRuleEngine(user, combine_mode='OR')
filtered_qs = engine.apply_rules(Mahasiswa.objects.all())
```

## Usage Patterns

### 1. Engine with Instance Initialization

**AND Mode (All rules must match):**
```python
engine = RecordRuleEngine(user)  # Default AND

# User must satisfy ALL rules
students = engine.apply_rules(Mahasiswa.objects.all(), operation='read')
```

**OR Mode (Any rule can match):**
```python
engine = RecordRuleEngine(user, combine_mode='OR')

# User must satisfy ANY rule
students = engine.apply_rules(Mahasiswa.objects.all(), operation='read')
```

### 2. Per-Call Mode Override

```python
engine = RecordRuleEngine(user)  # Defaults to AND

# Override with OR for this specific call
students = engine.apply_rules(
    Mahasiswa.objects.all(),
    operation='read',
    combine_mode='OR'  # Override default AND
)
```

### 3. Instance Access Checking

**AND Mode:**
```python
engine = RecordRuleEngine(user, combine_mode='AND')

# User must satisfy ALL rules to access this instance
can_read = engine.can_access(student, 'read')
```

**OR Mode:**
```python
engine = RecordRuleEngine(user, combine_mode='OR')

# User must satisfy ANY rule to access this instance
can_read = engine.can_access(student, 'read')
```

### 4. RecordRuleChecker Helper Class

```python
from django_autoapi.recordrules.engine import RecordRuleChecker

# OR mode
checker = RecordRuleChecker(user, combine_mode='OR')

if checker.can_read(student):
    # User can access (matches ANY rule)
    pass
```

### 5. Convenience Functions

```python
from django_autoapi.recordrules.engine import (
    apply_record_rules,
    can_access_instance
)

# OR mode filtering
filtered = apply_record_rules(
    Mahasiswa.objects.all(),
    user,
    operation='read',
    combine_mode='OR'
)

# OR mode instance check
can_access = can_access_instance(
    student,
    user,
    operation='read',
    combine_mode='OR'
)
```

## Combining Mode Behavior

### AND Mode (Default)

Records are included in results **ONLY** if they match **ALL** applicable rules.

**Example:**
```
Rule 1: unit_id = 1
Rule 2: status = 'active'

With AND mode:
- Record (unit_id=1, status='active') ✓ MATCH
- Record (unit_id=1, status='inactive') ✗ NO MATCH
- Record (unit_id=2, status='active') ✗ NO MATCH
- Record (unit_id=2, status='inactive') ✗ NO MATCH
```

SQL Generated:
```sql
WHERE unit_id = 1 AND status = 'active'
```

### OR Mode

Records are included in results if they match **ANY** applicable rule.

**Example:**
```
Rule 1: unit_id = 1
Rule 2: status = 'active'

With OR mode:
- Record (unit_id=1, status='active') ✓ MATCH
- Record (unit_id=1, status='inactive') ✓ MATCH
- Record (unit_id=2, status='active') ✓ MATCH
- Record (unit_id=2, status='inactive') ✗ NO MATCH
```

SQL Generated:
```sql
WHERE unit_id = 1 OR status = 'active'
```

## Real-World Scenarios

### Scenario 1: Multi-Unit Access (OR Mode)

**Use Case:** Department head can access data from their own unit OR any unit they supervise.

```python
# Create rules
rule1 = RecordRule.objects.create(
    name='Own unit access',
    content_type=ct,
    domain_filter={'unit_id': '${user.unit_id}'},
    perm_read=True
)

rule2 = RecordRule.objects.create(
    name='Supervised units access',
    content_type=ct,
    domain_filter={'unit_id': '${user.supervised_units}'},
    perm_read=True
)

# Apply with OR mode
engine = RecordRuleEngine(user, combine_mode='OR')
data = engine.apply_rules(queryset, operation='read')
# User sees: Own unit data + Supervised unit data
```

### Scenario 2: Strict Multi-Criteria Access (AND Mode)

**Use Case:** Accountant can only access active students from their unit with approved status.

```python
# Create rules
rule1 = RecordRule.objects.create(
    name='Own unit',
    domain_filter={'unit_id': '${user.unit_id}'},
    perm_read=True
)

rule2 = RecordRule.objects.create(
    name='Active students',
    domain_filter={'status': 'active'},
    perm_read=True
)

rule3 = RecordRule.objects.create(
    name='Approved only',
    domain_filter={'approval_status': 'approved'},
    perm_read=True
)

# Apply with AND mode (default)
engine = RecordRuleEngine(user)
data = engine.apply_rules(queryset, operation='read')
# User sees: Only active, approved students from own unit
```

### Scenario 3: Role-Based Categories (OR Mode)

**Use Case:** User can access any data matching their role-based rules.

```python
# Rule for each role-based category
rules = [
    RecordRule.objects.create(
        name=f'{role} access',
        domain_filter={'category': role},
        perm_read=True
    )
    for role in user.roles
]

# OR mode: User can access ANY category matching their roles
engine = RecordRuleEngine(user, combine_mode='OR')
data = engine.apply_rules(queryset)
```

## Case Sensitivity

The combine_mode parameter is **case-insensitive**:

```python
# All are equivalent
engine1 = RecordRuleEngine(user, combine_mode='OR')
engine2 = RecordRuleEngine(user, combine_mode='or')
engine3 = RecordRuleEngine(user, combine_mode='Or')

# All work
assert engine1.combine_mode == 'OR'
assert engine2.combine_mode == 'OR'
assert engine3.combine_mode == 'OR'
```

## Performance Considerations

### AND Mode
- More restrictive
- Results in smaller datasets
- Generally faster queries
- Good for secure/narrow access

### OR Mode
- More permissive
- Results in larger datasets
- Slightly slower queries (more conditions)
- Good for flexible/broad access

**Tip:** Use AND mode for security-sensitive operations, OR mode for convenience/discovery scenarios.

## Backward Compatibility

The OR combining mode feature is fully backward compatible:

1. **Existing code continues to work**: Default is AND mode
2. **No breaking changes**: API signatures are additive
3. **Gradual adoption**: Can migrate mode by mode

## API Reference

### RecordRuleEngine

```python
class RecordRuleEngine:
    def __init__(self, user: User, combine_mode: str = 'AND'):
        """Initialize with optional combine_mode"""

    def apply_rules(
        self,
        queryset: QuerySet,
        operation: str = 'read',
        combine_mode: Optional[str] = None
    ) -> QuerySet:
        """Apply rules with optional mode override"""

    def can_access(
        self,
        instance: Model,
        operation: str = 'read',
        combine_mode: Optional[str] = None
    ) -> bool:
        """Check access with optional mode override"""
```

### RecordRuleChecker

```python
class RecordRuleChecker:
    def __init__(self, user: User, combine_mode: str = 'AND'):
        """Initialize with optional combine_mode"""

    def can_read(self, instance: Model) -> bool:
        """Check read access"""

    def can_write(self, instance: Model) -> bool:
        """Check write access"""

    def can_create(self, instance: Model) -> bool:
        """Check create access"""

    def can_delete(self, instance: Model) -> bool:
        """Check delete access"""
```

### Convenience Functions

```python
def apply_record_rules(
    queryset: QuerySet,
    user: User,
    operation: str = 'read',
    combine_mode: str = 'AND'
) -> QuerySet:
    """Apply record rules with optional mode"""

def can_access_instance(
    instance: Model,
    user: User,
    operation: str = 'read',
    combine_mode: str = 'AND'
) -> bool:
    """Check instance access with optional mode"""
```

## Testing

Comprehensive tests are provided in `test_recordrules_engine.py`:

```bash
# Run all OR mode tests
pytest apps/backend/django_autoapi/tests/test_recordrules_engine.py -k "or_mode"

# Run specific test
pytest apps/backend/django_autoapi/tests/test_recordrules_engine.py::test_engine_with_or_mode_initialization -v
```

### Test Coverage

- Engine initialization with OR mode
- Default AND mode
- Case-insensitive mode handling
- Multiple rule combination (AND and OR)
- Parameter override at call time
- Instance access checking with both modes
- RecordRuleChecker class with both modes
- Convenience functions with both modes

## Migration Guide

### From Simple Filtering to OR Mode

**Before:**
```python
# Had to create separate rules and manually combine
engine = RecordRuleEngine(user)
qs1 = engine.apply_rules(queryset, combine_mode='AND')
```

**After:**
```python
# Can use OR mode directly
engine = RecordRuleEngine(user, combine_mode='OR')
qs = engine.apply_rules(queryset)
```

### Enabling OR Mode in Existing Code

1. Identify scenarios where OR logic is needed
2. Update engine initialization or add combine_mode parameter
3. Test thoroughly with both modes
4. Monitor performance impact

## Troubleshooting

### Issue: Mode is Case Sensitive
**Solution:** Combine mode is case-insensitive. Use 'AND', 'and', 'And', etc.

### Issue: Mode Not Applied to Instance Check
**Solution:** Ensure you pass combine_mode to can_access():
```python
# ✓ Correct
engine.can_access(instance, 'read', combine_mode='OR')

# ✗ Wrong (uses instance default)
engine.can_access(instance, 'read')
```

### Issue: Performance Degradation with OR Mode
**Solution:** OR mode can generate larger result sets. Consider:
1. Adding pagination
2. Using select_related/prefetch_related
3. Filtering by additional conditions
4. Reverting to AND mode if possible

## FAQ

**Q: What's the default combining mode?**
A: AND mode. All rules must match.

**Q: Can I override the mode per call?**
A: Yes, pass combine_mode parameter to apply_rules() or can_access().

**Q: Is OR mode less secure?**
A: OR mode is more permissive, not less secure. Use AND mode for restrictive access policies.

**Q: How do global rules interact with combining modes?**
A: Global rules are combined using the specified mode alongside group-specific rules.

**Q: Can I mix AND and OR across multiple rule sets?**
A: Currently, all rules for a user/operation use the same combining mode. For complex logic, consider splitting into separate calls.

## See Also

- [Record Rules Overview](RECORDRULES_OVERVIEW.md)
- [Record Rules Implementation](RECORDRULES_IMPLEMENTATION.md)
- [RecordRuleEngine Tests](../tests/test_recordrules_engine.py)
