# Swagger Role Integration Examples

Contoh implementasi enhanced API documentation dengan role matrix menggunakan utilities yang telah dibuat.

## Cara Menggunakan Role-Based Swagger Decorators

### 1. Import Required Utilities

```python
# Tambahkan import ini di view files
from core.utils.swagger_role_utils import (
    academic_role_swagger_decorator,
    kaprodi_admin_only,
    staff_only,
    student_accessible,
    mahasiswa_only
)
```

### 2. Update Existing Views dengan Role Documentation

#### Example: Update DosenView di `api/v1/academic/dosen/views.py`

**Before (current):**
```python
@swagger_auto_schema(
    operation_summary="List Dosen",
    operation_description="Get all dosen (dengan fitur search, sort, dan filter berdasarkan penugasan)",
    manual_parameters=[...],
    responses={200: custom_paginated_response(DosenSerializer, title="Dosen")},
    tags=['Dosen'],
    security=[{'Bearer': []}]
)
def get(self, request):
```

**After (enhanced with role info):**
```python
@kaprodi_admin_only(
    operation_summary="List Dosen",
    operation_description="Get all dosen with search, sort, and assignment filtering. Access restricted to administrative roles.",
    manual_parameters=[
        openapi.Parameter(
            'search', openapi.IN_QUERY,
            description="Cari dosen berdasarkan nama, NIDN, atau NIP",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'sort', openapi.IN_QUERY,
            description="Urutkan berdasarkan: `nama_dosen`, `nidn`, `nip`. Gunakan `-` untuk urutan descending.",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'has_penugasan', openapi.IN_QUERY,
            description="Filter dosen berdasarkan penugasan",
            type=openapi.TYPE_BOOLEAN
        )
    ],
    responses={200: custom_paginated_response(DosenSerializer, title="Dosen")},
    tags=['Dosen - Administrative']
)
def get(self, request):
```

#### Example: Update MataKuliahListView di `api/v1/academic/matakuliah/views.py`

**Enhanced version:**
```python
@staff_only(
    operation_summary="List Mata Kuliah",
    operation_description="Get all mata kuliah with role-based filtering. Kaprodi sees all subjects, Dosen sees only taught subjects.",
    manual_parameters=[
        openapi.Parameter(
            'search', openapi.IN_QUERY,
            description="Cari berdasarkan kode atau nama mata kuliah",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'prodi_id', openapi.IN_QUERY,
            description="Filter berdasarkan ID Prodi (optional untuk Kaprodi)",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'sort', openapi.IN_QUERY,
            description="Urutkan berdasarkan field tertentu",
            type=openapi.TYPE_STRING
        )
    ],
    tags=['Mata Kuliah']
)
def get(self, request):
```

#### Example: Student-Accessible Endpoint

```python
@student_accessible(
    operation_summary="Get Academic Schedule",
    operation_description="Retrieve academic schedule with role-based data scope",
    tags=['SIADIN - Schedule']
)
def get_jadwal(self, request):
    # Implementation with automatic role filtering
    pass
```

### 3. Custom Role Documentation untuk Use Cases Khusus

```python
@academic_role_swagger_decorator(
    operation_summary="Manage Grade Components",
    operation_description="Create and manage assessment components for subjects",
    allowed_roles=['superuser', 'kaprodi', 'dosen'],
    scope_description="Kaprodi: all subjects in managed prodi, Dosen: only taught subjects",
    manual_parameters=[
        openapi.Parameter(
            'subject_id', openapi.IN_PATH,
            description="ID mata kuliah",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    tags=['Assessment Management']
)
def manage_komponen_evaluasi(self, request, subject_id):
    # Implementation
    pass
```

## Complete View Example dengan Role Integration

### Enhanced DosenView Implementation

```python
from core.utils.swagger_role_utils import kaprodi_admin_only, staff_only
from api.common.permissions import AdminOnlyPermission

class DosenView(APIView):
    permission_classes = [AdminOnlyPermission]  # Updated permission
    authentication_classes = [CustomJWTAuthentication]

    @kaprodi_admin_only(
        operation_summary="List All Dosen",
        operation_description="""
        Retrieve paginated list of lecturers with advanced filtering and search capabilities.

        **Data Scope by Role:**
        - **Kaprodi**: Lecturers in managed program studies only
        - **Admin**: All lecturers across the institution

        **Available Filters:**
        - Search by name, NIDN, or NIP
        - Filter by assignment status
        - Sort by various fields
        """,
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description="Search lecturers by name, NIDN, or NIP",
                type=openapi.TYPE_STRING,
                example="Dr. Ahmad"
            ),
            openapi.Parameter(
                'sort', openapi.IN_QUERY,
                description="Sort by field. Use `-` prefix for descending order",
                type=openapi.TYPE_STRING,
                enum=['nama_dosen', '-nama_dosen', 'nidn', '-nidn', 'nip', '-nip'],
                example="-nama_dosen"
            ),
            openapi.Parameter(
                'has_penugasan', openapi.IN_QUERY,
                description="Filter by assignment status",
                type=openapi.TYPE_BOOLEAN,
                example=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Success - Lecturers retrieved with role-based filtering",
                schema=custom_paginated_response(DosenSerializer, title="Dosen"),
                examples={
                    'application/json': {
                        'results': [
                            {
                                'id': 1,
                                'nama_dosen': 'Dr. Ahmad Rahman',
                                'nip': '198501012010011001',
                                'nidn': '0101018501'
                            }
                        ],
                        'count': 25,
                        'user_role': 'kaprodi',
                        'scope_applied': 'Filtered by managed prodi: Teknik Informatika'
                    }
                }
            )
        },
        tags=['👨‍🏫 Dosen Management']
    )
    def get(self, request):
        # Existing implementation with automatic role filtering
        # The permission class will handle role-based data filtering
        pass

    @kaprodi_admin_only(
        operation_summary="Create New Dosen",
        operation_description="""
        Create a new lecturer record in the system.

        **Authorization:**
        - **Kaprodi**: Can create lecturers for managed program studies
        - **Admin**: Can create lecturers for any program study
        """,
        request_body=DosenSerializer,
        responses={
            201: openapi.Response(
                description="Dosen created successfully",
                schema=DosenSerializer
            ),
            400: openapi.Response(
                description="Validation error",
                examples={
                    'application/json': {
                        'error': 'VALIDATION_ERROR',
                        'message': 'Validasi gagal',
                        'details': [
                            {'field': 'nip', 'message': 'NIP sudah digunakan'}
                        ]
                    }
                }
            )
        },
        tags=['👨‍🏫 Dosen Management']
    )
    def post(self, request):
        # Existing implementation
        pass
```

### Enhanced MahasiswaViewSet Example

```python
from core.utils.swagger_role_utils import student_accessible, mahasiswa_only

class MahasiswaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [UniversalRoleBasedPermission]
    authentication_classes = [CustomJWTAuthentication]

    @student_accessible(
        operation_summary="List Students",
        operation_description="""
        Retrieve student data with automatic role-based filtering.

        **Data Access by Role:**
        - **Admin**: All students
        - **Kaprodi**: Students in managed program studies
        - **Dosen**: Students in taught classes
        - **Mahasiswa**: Own profile only
        """,
        tags=['👨‍🎓 Student Data']
    )
    def list(self, request):
        # Automatic filtering via permission classes
        return super().list(request)

    @mahasiswa_only(
        operation_summary="Get Student Academic Schedule",
        operation_description="""
        Retrieve personal academic schedule for the current semester.

        **Personal Data Access:**
        - Students can only view their own schedule
        - Admin can view any student's schedule
        """,
        tags=['👨‍🎓 Student Services']
    )
    @action(detail=True, methods=['get'])
    def jadwal(self, request, pk=None):
        # Implementation for student schedule
        pass
```

## OpenAPI Schema Configuration

### Update settings untuk include role-based schema

```python
# config/settings/base.py

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Bearer token. Format: Bearer <your_token>'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'model',
}

# Add custom schema view
REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
    'HIDE_HOSTNAME': True,
    'EXPAND_RESPONSES': ['200', '201'],
    'PATH_IN_MIDDLE_PANEL': True,
}
```

### Custom Schema View dengan Role Information

```python
# config/urls.py

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from core.utils.swagger_role_utils import get_role_based_schema_registry

schema_registry = get_role_based_schema_registry()

schema_view = get_schema_view(
    openapi.Info(
        title="Academic Management API",
        default_version='v1',
        description="""
        ## Role-Based Academic Management System API

        This API implements role-based access control with the following user types:

        ### 👨‍💼 **Superuser/Admin**
        - **Access**: Complete system access
        - **Scope**: All data without restrictions
        - **Use Case**: System administration, reporting, data management

        ### 🎓 **Kaprodi (Program Head)**
        - **Access**: Program study management
        - **Scope**: Data limited to managed program studies
        - **Use Case**: Academic program management, curriculum oversight

        ### 👨‍🏫 **Dosen (Lecturer)**
        - **Access**: Teaching-related data
        - **Scope**: Classes taught, subjects assigned, student grades
        - **Use Case**: Class management, grading, academic guidance

        ### 👨‍🎓 **Mahasiswa (Student)**
        - **Access**: Personal academic data
        - **Scope**: Own academic records, schedule, grades
        - **Use Case**: Academic tracking, schedule viewing, grade checking

        ## Authentication
        All endpoints require JWT Bearer token authentication:
        ```
        Authorization: Bearer <your_jwt_token>
        ```

        ## Data Filtering
        Data is automatically filtered based on user role and permissions:
        - **Automatic Scope Application**: No additional parameters needed
        - **Permission Validation**: Both endpoint and object-level checks
        - **Error Handling**: Clear role-based error messages
        """,
        contact=openapi.Contact(email="admin@academic-system.edu"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[],
    authentication_classes=[],
)

urlpatterns = [
    # Enhanced API documentation with role info
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]
```

## Implementation Checklist

### ✅ Files to Update

1. **Core Utilities** ✅
   - `core/utils/swagger_role_utils.py` - Created
   - Role-based decorators ready for use

2. **View Files to Update** 📝
   - `api/v1/academic/dosen/views.py`
   - `api/v1/academic/matakuliah/views.py`
   - `api/v1/academic/mhs/views.py`
   - `api/v1/academic/kuliah/views.py`
   - All SIADIN endpoints

3. **Configuration Updates** 📝
   - `config/settings/base.py` - Swagger settings
   - `config/urls.py` - Enhanced schema view

4. **Documentation** ✅
   - Role access matrix documented
   - Implementation examples provided

### Example Migration Script

```python
# scripts/update_swagger_with_roles.py

import re
import os

def update_view_decorators():
    """Script to help migrate existing swagger decorators to role-based ones"""

    view_files = [
        'api/v1/academic/dosen/views.py',
        'api/v1/academic/matakuliah/views.py',
        # Add other view files
    ]

    for file_path in view_files:
        # Read current content
        with open(file_path, 'r') as f:
            content = f.read()

        # Add imports
        if 'swagger_role_utils' not in content:
            import_section = "from core.utils.swagger_role_utils import kaprodi_admin_only, staff_only, student_accessible\n"
            content = re.sub(
                r'(from drf_yasg.*?\n)',
                r'\1' + import_section,
                content
            )

        # Suggest replacements (manual review needed)
        print(f"Review {file_path} for decorator updates")
        print("Consider replacing @swagger_auto_schema with appropriate role decorators")

if __name__ == "__main__":
    update_view_decorators()
```

## Testing Enhanced Documentation

### 1. Access Swagger UI
```bash
# Navigate to enhanced Swagger documentation
http://localhost:8000/swagger/

# Check for role information in endpoint descriptions
# Verify security requirements are displayed
# Test authentication with different role tokens
```

### 2. Verify Role Matrix Display
- Each endpoint should show allowed roles with icons
- Scope descriptions should be clear
- Error responses should include role-specific examples

### 3. Test with Different Tokens
```bash
# Test with Kaprodi token
curl -H "Authorization: Bearer <kaprodi_token>" http://localhost:8000/api/v1/mata-kuliah/

# Test with Dosen token
curl -H "Authorization: Bearer <dosen_token>" http://localhost:8000/api/v1/mata-kuliah/

# Test with Mahasiswa token (should get 403)
curl -H "Authorization: Bearer <mahasiswa_token>" http://localhost:8000/api/v1/dosen/
```

This enhanced documentation system provides clear role-based API information while maintaining the existing functionality.