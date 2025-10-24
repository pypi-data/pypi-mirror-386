"""
Example: Multiple API Classes for Same Model
==============================================

This example demonstrates how to create multiple API classes
for the same Django model with different configurations.

Use Cases:
- List view with limited fields
- Detail view with all fields
- Summary view with aggregated data
- Different serializers for different user roles
"""

from django_autoapi import AutoAPI
from django_autoapi.registry import AutoAPIRegistry
from apps.feeder.models import Biodata  # Example model


# Example 1: List View (limited fields for performance)
class MahasiswaListAPI(AutoAPI):
    """API for listing students with minimal fields"""
    model = Biodata
    fields = ['id_mahasiswa', 'nama_mahasiswa', 'nim']
    filterable = ['nama_mahasiswa', 'nim']
    searchable = ['nama_mahasiswa', 'nim']
    orderable = ['nama_mahasiswa']
    pagination = 'cursor'
    page_size = 50


# Example 2: Detail View (all fields)
class MahasiswaDetailAPI(AutoAPI):
    """API for student details with all fields"""
    model = Biodata
    # fields = None means all fields
    exclude_fields = ['deleted']
    read_only_fields = ['created_at', 'updated_at', 'id_mahasiswa']
    pagination = 'offset'
    page_size = 1


# Example 3: Summary View (custom fields)
class MahasiswaSummaryAPI(AutoAPI):
    """API for student summary"""
    model = Biodata
    fields = [
        'id_mahasiswa',
        'nama_mahasiswa',
        'nim',
        'email',
        'handphone'
    ]
    read_only_fields = ['id_mahasiswa']


# Example 4: Public View (limited for public access)
class MahasiswaPublicAPI(AutoAPI):
    """API for public student info"""
    model = Biodata
    fields = ['nama_mahasiswa', 'id_mahasiswa']
    permission_classes = ['AllowAny']


# Usage Examples
# ==============

def demonstrate_registry():
    """Show how to work with multiple registered APIs"""

    # Get all API classes for Biodata model
    api_classes = AutoAPIRegistry.get_api_classes(Biodata)
    print(f"Found {len(api_classes)} API classes for Biodata:")
    for api in api_classes:
        print(f"  - {api.__name__}")

    # Get first registered API (backward compatibility)
    first_api = AutoAPIRegistry.get_api_class(Biodata)
    print(f"\nFirst registered API: {first_api.__name__}")

    # Get registry info
    info = AutoAPIRegistry.get_registry_info()
    print(f"\nTotal registered APIs: {info['total_registered']}")
    print(f"Total models: {info['total_models']}")
    print("\nDetails:")
    for model_key, api_names in info['details'].items():
        print(f"  {model_key}: {', '.join(api_names)}")


def create_serializers():
    """Create serializers from different API configs"""
    from django_autoapi.factories.serializer import SerializerFactory

    # Create different serializers for different use cases
    list_serializer = SerializerFactory.create_serializer(MahasiswaListAPI)
    detail_serializer = SerializerFactory.create_serializer(MahasiswaDetailAPI)
    summary_serializer = SerializerFactory.create_serializer(MahasiswaSummaryAPI)

    print("List Serializer Fields:", list_serializer.Meta.fields)
    print("Detail Serializer Fields:", detail_serializer.Meta.fields)
    print("Summary Serializer Fields:", summary_serializer.Meta.fields)


if __name__ == '__main__':
    print("=== Multiple APIs per Model Demo ===\n")
    demonstrate_registry()
    print("\n=== Serializer Creation Demo ===\n")
    create_serializers()
