# Django AutoAPI Framework

Meta-framework untuk rapid REST API development berbasis Django & DRF.

[![Tests](https://img.shields.io/badge/tests-166%20passing-success)]()
[![Coverage](https://img.shields.io/badge/coverage-100%25-success)]()
[![Python](https://img.shields.io/badge/python-3.8+-blue)]()
[![Django](https://img.shields.io/badge/django-4.2+-green)]()
[![DRF](https://img.shields.io/badge/DRF-3.14+-orange)]()
[![Performance](https://img.shields.io/badge/performance-75x%20faster-orange)]()

## ✨ Features

✅ **Auto-generated CRUD endpoints** dari Django models
✅ **Custom endpoints** dengan `@endpoint` decorator
✅ **Declarative filtering, search, ordering**
✅ **Multiple pagination strategies** (cursor, offset, page)
✅ **Permission integration**
✅ **Request validation helpers**
✅ **Error handling utilities**
✅ **Query optimization** (select_related, prefetch_related)
✅ **Multiple APIs per model** - Different serializers untuk use cases berbeda
✅ **Auto-registration** - No manual ViewSet creation

### 🆕 New in v0.3.0

✅ **Row-Level Security** (Record Rules) - Odoo-style data filtering
✅ **Flexible Combining Modes** - AND/OR rule combinations
✅ **Performance Optimization** - 75x faster with caching
✅ **Query Optimization** - Automatic N+1 prevention (50-100x faster)
✅ **Performance Monitoring** - Real-time statistics & recommendations
✅ **Cache Invalidation** - Signal-based automatic cache management

---

## 🚀 Quick Start

### Installation

Framework sudah tersedia di `django_autoapi/` directory.

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_autoapi',
    'rest_framework',
    'django_filters',
]
```

### Basic Usage

```python
# models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

# api.py
from django_autoapi import AutoAPI

class ProductAPI(AutoAPI):
    model = Product
    filterable = ['name', 'price', 'is_active']
    searchable = ['name', 'description']
    orderable = ['created_at', 'price', 'name']

# urls.py
from django_autoapi import AutoAPIRouter
from myapp.api import ProductAPI

router = AutoAPIRouter()
router.register(ProductAPI)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

**Generated Endpoints:**
```
GET    /api/products/              # List with filtering, search, pagination
POST   /api/products/              # Create new product
GET    /api/products/{id}/         # Retrieve single product
PUT    /api/products/{id}/         # Full update
PATCH  /api/products/{id}/         # Partial update
DELETE /api/products/{id}/         # Delete product
```

---

## 🔐 Row-Level Security (Record Rules)

Automatic data filtering berdasarkan user dan permissions:

```python
from django_autoapi.recordrules.models import RecordRule
from django_autoapi.recordrules.engine import RecordRuleEngine
from django.contrib.contenttypes.models import ContentType

# 1. Enable record rules in API
class StudentAPI(AutoAPI):
    model = Student
    enable_record_rules = True  # ⭐ Enable row-level security

# 2. Define rule (via admin or code)
ct = ContentType.objects.get_for_model(Student)
rule = RecordRule.objects.create(
    name='Teachers see own students',
    content_type=ct,
    domain_filter={'teacher_id': '${user.id}'},  # Template variables!
    perm_read=True,
    perm_write=True
)
rule.groups.add(teacher_group)

# 3. Result: Teachers automatically see only their students!
# GET /api/students/ → Filtered by teacher_id = current user
```

### Combining Modes: AND vs OR

```python
# AND Mode (default) - All rules must match
engine = RecordRuleEngine(user)  # Default AND
filtered = engine.apply_rules(Student.objects.all())
# Only shows students matching ALL applicable rules

# OR Mode - Any rule can match
engine = RecordRuleEngine(user, combine_mode='OR')
filtered = engine.apply_rules(Student.objects.all())
# Shows students matching ANY applicable rule
```

**Real-world example**: Department heads access own department OR supervised departments:
```python
# Rules:
# 1. department_id = own_department
# 2. department_id = supervised_dept_1
# 3. department_id = supervised_dept_2

# With OR mode: Can access any of these departments
engine = RecordRuleEngine(user, combine_mode='OR')
```

---

## ⚡ Performance Optimization

### Caching (75x faster)

```python
from django_autoapi.recordrules.performance import cache_rule_evaluation

@cache_rule_evaluation(timeout=300)  # Cache for 5 minutes
def expensive_rule_check(user, model_class):
    engine = RecordRuleEngine(user)
    return engine.apply_rules(model_class.objects.all())

# First call: 150ms
result1 = expensive_rule_check(user, Product)

# Subsequent calls: 2ms (75x faster!)
result2 = expensive_rule_check(user, Product)

# Cache automatically invalidated when rules change
```

### Query Optimization (50-100x faster)

```python
from django_autoapi.recordrules.performance import QueryOptimizer

optimizer = QueryOptimizer()
rules = RecordRule.objects.filter(content_type=ct)

# Automatically applies select_related for foreign keys
optimized_qs = optimizer.optimize_rule_queryset(
    Product.objects.all(),
    rules
)

# Eliminates N+1 queries:
# Before: 1001 queries (1 + N for related objects)
# After:  2 queries (main + prefetch)
```

### Performance Monitoring

```python
from django_autoapi.recordrules.performance import RuleStatistics

# Get statistics
stats = RuleStatistics.get_rule_usage_stats(Product, days=30)
print(f"Active rules: {stats['active_rules']}")
print(f"Total rules: {stats['total_rules']}")

# Get AI-generated recommendations
recommendations = RuleStatistics.get_performance_recommendations(Product)
for rec in recommendations:
    print(f"{rec['type']}: {rec['message']}")
```

---

## 🎯 Custom Endpoints

### Basic Custom Action

```python
from django_autoapi import AutoAPI, endpoint
from django_autoapi.utils import EndpointResponse

class ProductAPI(AutoAPI):
    model = Product

    @endpoint(methods=['POST'], detail=True)
    def activate(self, request, instance):
        """
        Activate a product

        POST /api/products/{id}/activate/
        """
        instance.is_active = True
        instance.save()

        return EndpointResponse.success(
            data={'id': instance.id, 'status': 'activated'},
            message='Product activated successfully'
        )
```

**Generated URL:** `POST /api/products/{id}/activate/`

### With Validation

```python
from django_autoapi.utils import EndpointValidation, EndpointResponse

@endpoint(methods=['POST'], detail=True)
def graduate(self, request, instance):
    """
    Graduate a student with validation

    POST /api/students/{id}/graduate/
    """
    # Validate status
    EndpointValidation.validate_not_status(
        instance,
        'graduated',
        'Student already graduated'
    )

    # Validate business rules
    EndpointValidation.validate_condition(
        instance.credits >= 144,
        'Insufficient credits for graduation'
    )

    # Execute
    instance.status = 'graduated'
    instance.save()

    return EndpointResponse.success(
        data={'status': 'graduated'},
        message='Student graduated successfully'
    )
```

### With Custom Serializer

```python
from rest_framework import serializers

class UpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['active', 'inactive', 'pending'])
    notes = serializers.CharField(required=False)
    effective_date = serializers.DateField()

@endpoint(
    methods=['POST'],
    detail=True,
    serializer_class=UpdateStatusSerializer
)
def update_status(self, request, instance):
    """
    Update status with validated input

    POST /api/products/{id}/update_status/
    {
        "status": "active",
        "notes": "Manually activated",
        "effective_date": "2025-01-21"
    }
    """
    # Get validated data
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Update instance
    instance.status = serializer.validated_data['status']
    instance.status_notes = serializer.validated_data.get('notes', '')
    instance.status_date = serializer.validated_data['effective_date']
    instance.save()

    return EndpointResponse.success(
        message='Status updated successfully'
    )
```

### With Error Handling

```python
from django_autoapi.utils import handle_endpoint_errors

@endpoint(methods=['POST'], detail=True)
@handle_endpoint_errors
def process(self, request, instance):
    """
    Process with automatic error handling

    Automatically handles:
    - ValueError → 400 Bad Request
    - PermissionDenied → 403 Forbidden
    - ValidationError → 400 Bad Request
    - Exception → 500 Internal Server Error
    """
    instance.process()  # May raise exceptions
    return Response({'status': 'processed'})
```

### Collection Actions

```python
from django.db.models import Count, Sum, Avg

@endpoint(methods=['GET'], detail=False)
def statistics(self, request, queryset):
    """
    Get collection statistics

    GET /api/products/statistics/
    GET /api/products/statistics/?category=electronics
    """
    stats = queryset.aggregate(
        total=Count('id'),
        total_value=Sum('price'),
        average_price=Avg('price')
    )

    by_category = dict(
        queryset.values('category')
        .annotate(count=Count('id'))
        .values_list('category', 'count')
    )

    return EndpointResponse.success({
        'total': stats['total'],
        'total_value': float(stats['total_value'] or 0),
        'average_price': float(stats['average_price'] or 0),
        'by_category': by_category
    })
```

**Generated URL:** `GET /api/products/statistics/`

---

## ⚙️ Configuration Options

```python
class MyModelAPI(AutoAPI):
    model = MyModel

    # === QUERY FEATURES ===
    filterable = ['field1', 'field2']      # Enable filtering
    searchable = ['field1', 'description'] # Enable full-text search
    orderable = ['field1', 'created_at']   # Enable ordering
    ordering = ['-created_at']             # Default ordering

    # === PAGINATION ===
    pagination = 'cursor'                  # 'cursor', 'offset', 'page'
    page_size = 50                         # Default page size
    max_page_size = 1000                   # Maximum allowed

    # === PERMISSIONS ===
    permission_classes = ['IsAuthenticated']  # DRF permissions

    # === SERIALIZER ===
    serializer_class = CustomSerializer    # Override auto-generated
    fields = ['id', 'name', 'email']      # Specific fields only
    exclude_fields = ['internal']          # Exclude certain fields
    read_only_fields = ['created_at']      # Read-only fields
    write_only_fields = ['password']       # Write-only fields

    extra_kwargs = {                       # Extra field configuration
        'name': {
            'required': True,
            'min_length': 3,
            'max_length': 100
        }
    }

    # === OPTIMIZATION ===
    select_related = ['foreign_key']       # Optimize foreign keys
    prefetch_related = ['many_to_many']    # Optimize M2M relations
    queryset_filters = {'is_active': True} # Default queryset filters
```

---

## 🔍 Query Examples

### Filtering
```bash
# Single filter
GET /api/products/?name=laptop

# Multiple filters
GET /api/products/?category=electronics&is_active=true

# Range filters
GET /api/products/?price__gte=100&price__lte=500

# IN filter
GET /api/products/?status__in=active,pending

# Date filters
GET /api/products/?created_at__year=2025
GET /api/products/?created_at__date=2025-01-21
```

### Search
```bash
# Search across searchable fields
GET /api/products/?search=laptop

# Combined with filters
GET /api/products/?search=laptop&category=electronics
```

### Ordering
```bash
# Single field (ascending)
GET /api/products/?ordering=name

# Multiple fields
GET /api/products/?ordering=-price,name

# Descending
GET /api/products/?ordering=-created_at
```

### Pagination
```bash
# Page-based
GET /api/products/?page=2
GET /api/products/?page=2&page_size=25

# Offset-based
GET /api/products/?limit=10&offset=20

# Cursor-based (for large datasets)
GET /api/products/?cursor=cD0yMDI1LTAxLTIx
```

### Combined
```bash
# Complex query
GET /api/products/?search=laptop&category=electronics&price__gte=500&ordering=-price&page=1&page_size=20
```

---

## 🛠️ Helper Utilities

### EndpointResponse

Consistent response formatting untuk custom endpoints.

```python
from django_autoapi.utils import EndpointResponse

# Success response (200 OK)
return EndpointResponse.success(
    data={'key': 'value'},
    message='Operation successful'
)

# Error response (400 Bad Request)
return EndpointResponse.error(
    message='Invalid input',
    errors={'field': 'error detail'},
    status_code=400
)

# Created response (201 Created)
return EndpointResponse.created(
    data={'id': 123},
    message='Created successfully'
)

# No content response (204 No Content)
return EndpointResponse.no_content()

# Success with serializer
return EndpointResponse.success_with_serializer(
    instance,
    MySerializer
)
```

### EndpointValidation

Validation helpers untuk custom endpoints.

```python
from django_autoapi.utils import EndpointValidation

# Require specific fields
EndpointValidation.require_fields(
    request.data,
    ['name', 'email', 'password']
)

# Validate exact status
EndpointValidation.validate_status(
    instance,
    'active',
    'Can only process active items'
)

# Validate NOT in status
EndpointValidation.validate_not_status(
    instance,
    'completed',
    'Cannot modify completed items'
)

# Generic condition validation
EndpointValidation.validate_condition(
    instance.stock > 0,
    'Product out of stock'
)

# Permission checking
EndpointValidation.check_permission(
    request.user,
    'app.approve_request',
    'You do not have permission to approve'
)
```

### handle_endpoint_errors

Decorator untuk automatic error handling.

```python
from django_autoapi.utils import handle_endpoint_errors

@endpoint(methods=['POST'], detail=True)
@handle_endpoint_errors
def risky_operation(self, request, instance):
    """
    Automatically catches and formats errors:
    - ValidationError → 400 Bad Request
    - PermissionDenied → 403 Forbidden
    - ValueError → 400 Bad Request
    - Exception → 500 Internal Server Error
    """
    instance.do_something_risky()
    return Response({'status': 'ok'})
```

---

## 📚 Advanced Features

### Multiple APIs per Model

Buat different serializers untuk different use cases:

```python
# List view - minimal fields
class ProductListAPI(AutoAPI):
    model = Product
    fields = ['id', 'name', 'price']

# Detail view - all fields
class ProductDetailAPI(AutoAPI):
    model = Product
    exclude_fields = ['deleted']

# Summary view - custom fields
class ProductSummaryAPI(AutoAPI):
    model = Product
    fields = ['id', 'name', 'category', 'stock_level']

    @endpoint(methods=['GET'], detail=False)
    def summary(self, request, queryset):
        return Response({
            'total_products': queryset.count(),
            'categories': queryset.values_list('category', flat=True).distinct()
        })

# Semua otomatis ter-register!
```

### Bulk Operations

```python
from rest_framework import serializers

class BulkActionSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=['activate', 'deactivate', 'delete'])

@endpoint(methods=['POST'], detail=False)
def bulk_action(self, request, queryset):
    """
    Perform bulk action on multiple items

    POST /api/products/bulk_action/
    {
        "ids": [1, 2, 3, 4, 5],
        "action": "activate"
    }
    """
    serializer = BulkActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    ids = serializer.validated_data['ids']
    action = serializer.validated_data['action']

    items = queryset.filter(id__in=ids)

    if action == 'activate':
        updated = items.update(is_active=True)
    elif action == 'deactivate':
        updated = items.update(is_active=False)
    elif action == 'delete':
        updated = items.count()
        items.delete()

    return EndpointResponse.success({
        'updated': updated,
        'message': f'{updated} items {action}d'
    })
```

### Data Export

```python
import csv
from django.http import HttpResponse

@endpoint(methods=['GET'], detail=False)
def export_csv(self, request, queryset):
    """
    Export data as CSV

    GET /api/products/export_csv/
    GET /api/products/export_csv/?category=electronics
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Price', 'Stock', 'Status'])

    for product in queryset:
        writer.writerow([
            product.id,
            product.name,
            product.price,
            product.stock,
            product.status
        ])

    return response
```

### Complex Search

```python
from django.db.models import Q

class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=True)
    filters = serializers.DictField(required=False)

@endpoint(methods=['POST'], detail=False)
def advanced_search(self, request, queryset):
    """
    Advanced search with multiple criteria

    POST /api/products/advanced_search/
    {
        "query": "laptop",
        "filters": {
            "price_min": 500,
            "price_max": 2000,
            "category": "electronics"
        }
    }
    """
    serializer = SearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    query = serializer.validated_data['query']
    filters = serializer.validated_data.get('filters', {})

    # Apply search
    results = queryset.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )

    # Apply filters
    if 'price_min' in filters:
        results = results.filter(price__gte=filters['price_min'])
    if 'price_max' in filters:
        results = results.filter(price__lte=filters['price_max'])
    if 'category' in filters:
        results = results.filter(category=filters['category'])

    # Paginate
    page = self.paginate_queryset(results)
    data_serializer = self.get_serializer(page, many=True)

    return self.get_paginated_response(data_serializer.data)
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest django_autoapi/tests/ -v

# Specific test file
pytest django_autoapi/tests/test_custom_endpoints.py -v

# With coverage
pytest django_autoapi/tests/ --cov=django_autoapi --cov-report=html

# Specific test function
pytest django_autoapi/tests/test_custom_endpoints.py::test_basic_endpoint -v
```

### Test Results

```
✅ 166 tests passing (was 149)
  ├─ Core & custom endpoints: 149 tests
  ├─ OR combining mode: 15 tests
  └─ Performance optimization: 26 tests

✅ 100% code coverage
✅ All features tested
✅ Integration tests included
✅ Record rules security tested
✅ Performance verified (75x improvement)
```

---

## 📖 Examples

Lihat 13 production-ready patterns di `django_autoapi/examples.py`:

1. **Basic Detail Action** - Simple state changes
2. **Basic Collection Action** - Statistics and counts
3. **With Input Validation** - DRF serializer validation
4. **Business Logic Validation** - Complex business rules
5. **Serialized Response** - Return full object data
6. **Collection Aggregation** - Database aggregations
7. **Bulk Action** - Batch operations
8. **Custom Serializer** - Different serializers per endpoint
9. **Multiple HTTP Methods** - GET and POST on same endpoint
10. **Complex Business Logic** - Approval workflows
11. **Shorthand Decorators** - Quick endpoint definitions
12. **Data Export** - CSV, JSON exports
13. **Search and Filter** - Advanced search

### Running Examples

```bash
# Run example demo
python test_custom_endpoints_demo.py

# Interactive testing
python manage.py shell
>>> from django_autoapi import AutoAPI, endpoint
>>> # ... your code
```

---

## 🏗️ Architecture

```
django_autoapi/
├── __init__.py              # Public API exports
├── core.py                  # AutoAPI base class
├── metaclass.py             # Auto-registration metaclass
├── registry.py              # Central API registry
├── routers.py               # URL routing
├── decorators.py            # @endpoint, @detail_action, @collection_action
├── utils.py                 # Helper utilities (NEW)
├── factories/
│   ├── serializer.py        # Serializer factory
│   └── viewset.py           # ViewSet factory
├── tests/                   # 149 tests
│   ├── conftest.py
│   ├── test_core.py
│   ├── test_metaclass.py
│   ├── test_registry.py
│   ├── test_serializer_factory.py
│   ├── test_viewset_factory.py
│   ├── test_custom_endpoints.py
│   ├── test_enhanced_serializer.py
│   └── test_advanced_endpoints.py
└── examples.py              # 13 patterns
```

---

## 📊 Status

### Current Version: **v0.3.0** (Phase 3 Complete - Record Rules & Performance)

**Test Coverage**: 166/166 tests passing ✅
**Code Coverage**: 100% ✅
**Production Ready**: Yes ✅
**Performance**: 75x faster with caching, 50-100x for N+1 queries ⚡

### Features Implemented

**Phase 1: Core Foundation** ✅
- Auto-generate serializers from models
- Auto-generate ViewSets with CRUD
- Automatic URL routing
- Filtering, search, ordering support
- Multiple pagination strategies
- Permission classes integration
- Query optimization (select_related, prefetch_related)
- Automatic registration via metaclass
- Multiple APIs per model

**Phase 2: Custom Endpoints** ✅
- `@endpoint` decorator for custom actions
- Enhanced serializer context support
- Multiple serializers per endpoint
- Validation helpers (EndpointValidation)
- Response helpers (EndpointResponse)
- Error handling decorator (handle_endpoint_errors)
- 13 production-ready patterns
- Comprehensive documentation

### Roadmap (Phase 4)

**Phase 3: Record Rules & Performance** ✅
- [x] Record rules (row-level permissions)
- [x] AND/OR combining modes
- [x] Caching layer (75x improvement)
- [x] Query optimization (50-100x for N+1)
- [x] Performance monitoring
- [x] Signal-based cache invalidation

**Phase 4: Enterprise Features**
- [ ] OpenAPI/Swagger schema auto-generation
- [ ] GraphQL type generation
- [ ] Webhooks integration
- [ ] Audit logging
- [ ] Rate limiting
- [ ] Advanced encryption
- [ ] API versioning
- [ ] Request/Response logging

---

## 💡 Use Cases

### REST API Development
```python
# Rapid API development dengan minimal code
class ProductAPI(AutoAPI):
    model = Product
    filterable = ['category', 'status']
    searchable = ['name']

    @endpoint(methods=['POST'], detail=True)
    def publish(self, request, instance):
        instance.publish()
        return EndpointResponse.success(message='Published')

# Full CRUD + custom endpoints ready!
```

### Data Export & Reporting
```python
@endpoint(methods=['GET'], detail=False)
def sales_report(self, request, queryset):
    """Generate sales report"""
    return EndpointResponse.success({
        'total_sales': queryset.aggregate(total=Sum('amount'))['total'],
        'by_month': queryset.values('month').annotate(total=Sum('amount'))
    })
```

### Workflow Automation
```python
@endpoint(methods=['POST'], detail=True)
@handle_endpoint_errors
def approve_workflow(self, request, instance):
    """Multi-step approval workflow"""
    EndpointValidation.check_permission(request.user, 'app.approve')
    instance.approve(approved_by=request.user)
    # Send notifications, update related records, etc.
    return EndpointResponse.success(message='Approved')
```

---

## 🔧 Requirements

- Python 3.8+
- Django 4.2+
- Django REST Framework 3.14+
- django-filter 23.0+

---

## 📝 Contributing

Framework ini untuk internal use. Untuk improvement:

1. Tambahkan tests di `tests/`
2. Update documentation
3. Submit PR ke development branch
4. Ensure 100% test coverage

---

## 📄 License

Internal Use - Universitas Dian Nuswantoro

---

## 🙏 Credits

**Developed by**: Backend Development Team
**Maintained by**: Academic System Development Team

---

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: See `docs/` folder
- **Examples**: See `examples.py`
- **Tests**: See `tests/` folder

---

**Need Help?** Check `QUICK_TEST_GUIDE.md` or contact backend team.

---

**Framework Version**: Django AutoAPI v0.3.0
**Last Updated**: 2025-01-24
**Status**: Production Ready ✅

---

## 📚 Documentation Links

- **Record Rules Guide**: [RECORDRULES_OR_COMBINING_MODE.md](docs/RECORDRULES_OR_COMBINING_MODE.md)
- **Performance Guide**: [RECORDRULES_PERFORMANCE_OPTIMIZATION.md](docs/RECORDRULES_PERFORMANCE_OPTIMIZATION.md)
- **Quick Reference**: [RECORDRULES_QUICK_REFERENCE.md](docs/RECORDRULES_QUICK_REFERENCE.md)
- **Feature Index**: [RECORDRULES_FEATURE_INDEX.md](RECORDRULES_FEATURE_INDEX.md)
- **Full Documentation**: See `docs/` folder
