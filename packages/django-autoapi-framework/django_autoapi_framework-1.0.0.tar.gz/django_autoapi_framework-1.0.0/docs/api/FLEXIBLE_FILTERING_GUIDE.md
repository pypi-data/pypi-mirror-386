# Flexible Filtering System Guide

## Overview

This guide explains how to use the flexible filtering system implemented for APIs in the academic management system. The system supports complex filtering with multiple operators and field types.

## Basic Usage

### Filter Format
```
GET /api/v1/endpoint?field[operator]=value
```

### Default Operator
When no operator is specified, `eq` (equals) is used by default:
```
GET /api/v1/dosen?nama_dosen=John Doe
# Equivalent to: GET /api/v1/dosen?nama_dosen[eq]=John Doe
```

## Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals (default) | `?nama_dosen=John Doe` |
| `ne` | Not equals | `?jenis_kelamin[ne]=L` |
| `gt` | Greater than | `?tanggal_lahir[gt]=1990-01-01` |
| `gte` | Greater than or equal | `?tanggal_lahir[gte]=1990-01-01` |
| `lt` | Less than | `?tanggal_lahir[lt]=2000-01-01` |
| `lte` | Less than or equal | `?tanggal_lahir[lte]=2000-01-01` |
| `like` | Pattern matching with wildcards | `?nama_dosen[like]=John%` |
| `in` | In list of values | `?jenis_kelamin[in]=L,P` |
| `between` | Between two values | `?tanggal_lahir[between]=1990-01-01,2000-01-01` |

## Field Types and Examples

### String Fields
String fields support all operators. Examples with `nama_dosen`:

```bash
# Exact match
GET /api/v1/dosen?nama_dosen=Dr. John Doe

# Pattern matching (case insensitive)
GET /api/v1/dosen?nama_dosen[like]=John%        # Starts with "John"
GET /api/v1/dosen?nama_dosen[like]=%Doe        # Ends with "Doe"
GET /api/v1/dosen?nama_dosen[like]=%John%      # Contains "John"

# Not equals
GET /api/v1/dosen?nama_dosen[ne]=Dr. Jane Smith

# Multiple values
GET /api/v1/dosen?nama_dosen[in]=Dr. John Doe,Prof. Jane Smith
```

### Date Fields
Date fields support comparison and range operators. Format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`:

```bash
# Born after 1990
GET /api/v1/dosen?tanggal_lahir[gt]=1990-01-01

# Born between 1980 and 1990
GET /api/v1/dosen?tanggal_lahir[between]=1980-01-01,1990-12-31

# Born on or after January 1, 1985
GET /api/v1/dosen?tanggal_lahir[gte]=1985-01-01
```

### Foreign Key Fields
For foreign key relationships, use the primary key value:

```bash
# Filter by specific agama ID
GET /api/v1/dosen?id_agama=1

# Filter by multiple agama IDs
GET /api/v1/dosen?id_agama[in]=1,2,3

# Exclude specific status keaktifan
GET /api/v1/dosen?id_status_aktif[ne]=2
```

### Choice Fields
For choice fields like `jenis_kelamin`:

```bash
# Male lecturers only
GET /api/v1/dosen?jenis_kelamin=L

# Female lecturers only
GET /api/v1/dosen?jenis_kelamin=P

# Both male and female
GET /api/v1/dosen?jenis_kelamin[in]=L,P

# Not specified gender
GET /api/v1/dosen?jenis_kelamin[ne]=L&jenis_kelamin[ne]=P
```

## Combining Filters

You can combine multiple filters in a single request:

```bash
# Complex filter example
GET /api/v1/dosen?nama_dosen[like]=Dr.%&jenis_kelamin=L&tanggal_lahir[gte]=1980-01-01&id_agama[in]=1,2
```

This example finds:
- Lecturers whose name starts with "Dr."
- Who are male
- Born on or after 1980-01-01
- With agama ID 1 or 2

## Dosen API Specific Examples

### Available Filterable Fields
- `nama_dosen` (string)
- `nidn` (string)
- `nip` (string)
- `jenis_kelamin` (choice: L/P)
- `id_agama` (foreign key)
- `id_status_aktif` (foreign key)
- `tanggal_lahir` (date)

### Example Queries

```bash
# Find lecturers named containing "Ahmad"
GET /api/v1/dosen?nama_dosen[like]=%Ahmad%

# Find male lecturers with specific NIDN pattern
GET /api/v1/dosen?jenis_kelamin=L&nidn[like]=123%

# Find lecturers born in the 1980s
GET /api/v1/dosen?tanggal_lahir[between]=1980-01-01,1989-12-31

# Find active lecturers (assuming status ID 1 is active)
GET /api/v1/dosen?id_status_aktif=1

# Find lecturers with specific religions
GET /api/v1/dosen?id_agama[in]=1,2,3

# Complex query: Active male lecturers born after 1975 with Islam religion
GET /api/v1/dosen?jenis_kelamin=L&tanggal_lahir[gt]=1975-01-01&id_status_aktif=1&id_agama=1
```

## Implementation for Other APIs

### Step 1: Add FlexibleFilterMixin to your view

```python
from core.mixins.filter_mixins import FlexibleFilterMixin
from core.utils.filter_utils import generate_filter_parameters, create_filter_documentation_string

class YourAPIView(APIView, FlexibleFilterMixin):
    # Configure filtering
    filterable_fields = ['field1', 'field2', 'field3']
    date_fields = ['created_at', 'updated_at']
    boolean_fields = ['is_active']
    numeric_fields = ['price', 'quantity']
```

### Step 2: Update Swagger documentation

```python
@swagger_auto_schema(
    operation_summary="List Items",
    operation_description=f"""List items with flexible filtering.

{create_filter_documentation_string(
    filterable_fields=['field1', 'field2'],
    date_fields=['created_at'],
    boolean_fields=['is_active'],
    numeric_fields=['price']
)}
""",
    manual_parameters=[
        # Your existing parameters
        *generate_filter_parameters(
            filterable_fields=['field1', 'field2'],
            date_fields=['created_at'],
            boolean_fields=['is_active'],
            numeric_fields=['price']
        )
    ],
    responses={200: YourSerializer(many=True)},
)
```

### Step 3: Apply filters in your get method

```python
def get(self, request):
    queryset = YourModel.objects.filter(deleted=False)

    # Apply flexible filtering
    queryset = self.apply_flexible_filters(queryset, request)

    # Continue with other filtering, sorting, pagination...
```

## Error Handling

The system handles various error conditions gracefully:

### Invalid Operators
```bash
GET /api/v1/dosen?nama_dosen[invalid_operator]=value
# Filter is skipped, no error thrown
```

### Invalid Field Names
```bash
GET /api/v1/dosen?non_existent_field=value
# Filter is skipped, no error thrown
```

### Invalid Values
```bash
GET /api/v1/dosen?tanggal_lahir[gte]=invalid-date
# Filter is skipped, no error thrown
```

### Missing Values for Range Operators
```bash
GET /api/v1/dosen?tanggal_lahir[between]=2020-01-01
# Error: Operator 'between' requires 2 values separated by comma
```

## Performance Considerations

1. **Use select_related()**: When filtering on foreign keys, use `select_related()` to avoid N+1 queries:
   ```python
   queryset = Dosen.objects.filter(deleted=False).select_related('id_agama', 'id_status_aktif')
   ```

2. **Database Indexes**: Ensure frequently filtered fields have database indexes.

3. **Limit Filterable Fields**: Only expose fields that are actually needed for filtering to avoid potential performance issues.

## Security Considerations

1. **Field Validation**: Only fields listed in `filterable_fields` can be filtered.

2. **SQL Injection Protection**: The system uses Django's ORM, which provides protection against SQL injection.

3. **Performance Limits**: Consider implementing query complexity limits for production use.

## Testing

Example test cases for your API:

```python
def test_filter_by_name_like(self):
    response = self.client.get('/api/v1/dosen?nama_dosen[like]=John%')
    self.assertEqual(response.status_code, 200)

def test_filter_by_date_range(self):
    response = self.client.get('/api/v1/dosen?tanggal_lahir[between]=1980-01-01,1990-01-01')
    self.assertEqual(response.status_code, 200)

def test_combined_filters(self):
    response = self.client.get('/api/v1/dosen?jenis_kelamin=L&id_agama=1')
    self.assertEqual(response.status_code, 200)
```

## Conclusion

The flexible filtering system provides a powerful and consistent way to filter data across all APIs. It supports various data types and operators while maintaining security and performance considerations.

For questions or issues, refer to the source code in:
- `core/mixins/filter_mixins.py`
- `core/utils/filter_utils.py`