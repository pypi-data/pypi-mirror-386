# Record Rules - Quick Reference

## Combining Modes at a Glance

| Feature | AND Mode (Default) | OR Mode |
|---------|-------------------|---------|
| **Rules** | ALL must match | ANY can match |
| **SQL** | Uses `AND` between conditions | Uses `OR` between conditions |
| **Result** | Smaller, more restrictive | Larger, more permissive |
| **Speed** | Faster | Slightly slower |
| **Use Case** | Strict, security-sensitive | Flexible, discovery-friendly |

## Quick Start

### Initialize Engine

```python
# AND mode (default)
engine = RecordRuleEngine(user)

# OR mode
engine = RecordRuleEngine(user, combine_mode='OR')
```

### Filter Queryset

```python
# AND mode
students = engine.apply_rules(Mahasiswa.objects.all())

# OR mode at call time
students = engine.apply_rules(
    Mahasiswa.objects.all(),
    combine_mode='OR'
)
```

### Check Instance Access

```python
# AND mode
can_read = engine.can_access(student, 'read')

# OR mode
can_read = engine.can_access(student, 'read', combine_mode='OR')
```

### Use Helper Class

```python
# AND mode
checker = RecordRuleChecker(user)

# OR mode
checker = RecordRuleChecker(user, combine_mode='OR')

# Methods automatically use set mode
if checker.can_read(student):
    pass
```

### Use Convenience Functions

```python
# Filter with OR
students = apply_record_rules(
    Mahasiswa.objects.all(),
    user,
    combine_mode='OR'
)

# Check instance with OR
can_access = can_access_instance(
    student,
    user,
    combine_mode='OR'
)
```

## Common Scenarios

### Department Head - Access Multiple Units (OR)

```python
engine = RecordRuleEngine(user, combine_mode='OR')

# Rules:
# - unit_id = own_unit
# - unit_id = supervised_unit_1
# - unit_id = supervised_unit_2

students = engine.apply_rules(Mahasiswa.objects.all())
# Result: From own unit OR any supervised unit
```

### Accountant - Strict Criteria (AND)

```python
engine = RecordRuleEngine(user)  # AND mode

# Rules:
# - unit_id = own_unit
# - status = 'active'
# - approval = 'approved'

students = engine.apply_rules(Mahasiswa.objects.all())
# Result: From own unit AND active AND approved
```

### Researcher - Role-Based Access (OR)

```python
engine = RecordRuleEngine(user, combine_mode='OR')

# Rules (one per role):
# - category = 'students'
# - category = 'research_subjects'
# - category = 'alumni'

data = engine.apply_rules(Person.objects.all())
# Result: Any category matching user's roles
```

## Mode Override Examples

```python
# Engine defaults to AND
engine = RecordRuleEngine(user)

# But can override for specific calls
result1 = engine.apply_rules(qs, combine_mode='OR')   # Use OR for this call
result2 = engine.apply_rules(qs, combine_mode='AND')  # Use AND for this call
result3 = engine.apply_rules(qs)                       # Uses default AND
```

## Performance Tips

**AND Mode (Faster)**
- More restrictive
- Smaller result sets
- Better for secure operations
- Preferred default

**OR Mode (Slightly Slower)**
- More permissive
- Larger result sets
- Use pagination
- Add additional filters if needed

```python
# Optimize OR mode with pagination and filters
students = engine.apply_rules(
    Mahasiswa.objects.all(),
    combine_mode='OR'
).filter(
    status='active'
).order_by('-created_at')[:100]
```

## Testing Rules

### Test AND Mode Behavior

```python
def test_and_mode():
    engine = RecordRuleEngine(user)

    # Create rules
    rule1: unit_id = 1
    rule2: status = 'active'

    # Both conditions must match
    result = engine.apply_rules(queryset)
    # Only records with unit_id=1 AND status='active'
```

### Test OR Mode Behavior

```python
def test_or_mode():
    engine = RecordRuleEngine(user, combine_mode='OR')

    # Create rules
    rule1: unit_id = 1
    rule2: unit_id = 2

    # Either condition can match
    result = engine.apply_rules(queryset)
    # Records with unit_id=1 OR unit_id=2
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Mode not applied | Ensure you're using correct parameter name |
| Case sensitivity | Mode is case-insensitive: 'OR', 'or', 'Or' all work |
| Wrong result set | Verify rules are correct; check SQL with `str(qs.query)` |
| Performance issue | Consider using AND mode or adding pagination |

## Common Mistakes

❌ **Wrong:**
```python
# Mode specified but not used
engine = RecordRuleEngine(user, combine_mode='OR')
result = engine.apply_rules(qs)  # Forgetting combine_mode parameter
```

✓ **Correct:**
```python
# Either set at init or pass to method
engine = RecordRuleEngine(user, combine_mode='OR')
result = engine.apply_rules(qs)  # Uses OR from init

# Or pass at method call
engine = RecordRuleEngine(user)
result = engine.apply_rules(qs, combine_mode='OR')  # Override to OR
```

## API Cheat Sheet

```python
# Engine initialization
RecordRuleEngine(user)                          # AND mode (default)
RecordRuleEngine(user, combine_mode='OR')       # OR mode

# Apply rules
engine.apply_rules(qs)                          # Uses engine's mode
engine.apply_rules(qs, combine_mode='OR')       # Override mode

# Check access
engine.can_access(instance)                     # Uses engine's mode
engine.can_access(instance, combine_mode='OR')  # Override mode

# Helper checker
RecordRuleChecker(user)                         # AND mode (default)
RecordRuleChecker(user, combine_mode='OR')      # OR mode

# Convenience functions
apply_record_rules(qs, user)                           # AND mode
apply_record_rules(qs, user, combine_mode='OR')        # OR mode

can_access_instance(instance, user)                    # AND mode
can_access_instance(instance, user, combine_mode='OR') # OR mode
```

## When to Use Each Mode

### Use AND Mode When:
- ✅ Security is paramount
- ✅ Need restrictive access
- ✅ User must meet multiple criteria
- ✅ Performance is critical
- ✅ Data is sensitive

### Use OR Mode When:
- ✅ Need flexible access
- ✅ Supporting discovery
- ✅ Multi-category access
- ✅ Administrative overrides
- ✅ Data is public/non-sensitive

## References

- Full Documentation: [RECORDRULES_OR_COMBINING_MODE.md](RECORDRULES_OR_COMBINING_MODE.md)
- Tests: `django_autoapi/tests/test_recordrules_engine.py`
- Source: `django_autoapi/recordrules/engine.py`
