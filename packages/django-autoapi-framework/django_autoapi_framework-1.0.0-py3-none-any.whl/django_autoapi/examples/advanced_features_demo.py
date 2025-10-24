"""
Advanced Features Demo - Django AutoAPI
========================================

Demonstrasi fitur advanced:
1. SerializerMethodField - Custom computed fields
2. Custom Validation - Field & object-level validation
3. Nested Serializers - Relational data
4. Custom Fields - Additional field types

Run: python manage.py shell < django_autoapi/examples/advanced_features_demo.py
"""

print("=" * 70)
print("🚀 Django AutoAPI - Advanced Features Demo")
print("=" * 70)
print()

from django_autoapi import AutoAPI
from django_autoapi.factories.serializer import SerializerFactory
from rest_framework import serializers as drf_serializers

# Import models
from apps.feeder.models.mahasiswa import Biodata as Mahasiswa
from apps.feeder.models.dosen import Dosen
from apps.feeder.models.kelas_kuliah import KelasKuliah

# ============================================================================
# Feature 1: SerializerMethodField - Computed Fields
# ============================================================================
print("-" * 70)
print("FEATURE 1: SerializerMethodField - Computed Fields")
print("-" * 70)

class MahasiswaWithComputedFieldsAPI(AutoAPI):
    """API dengan custom computed fields"""
    model = Mahasiswa
    fields = ['id_mahasiswa', 'nama_mahasiswa', 'nim', 'email',
              'full_info', 'email_status', 'contact_summary']

    @staticmethod
    def get_full_info(obj):
        """Computed field: Combine NIM and name"""
        nim = getattr(obj, 'nim', 'N/A')
        return f"{nim} - {obj.nama_mahasiswa}"

    @staticmethod
    def get_email_status(obj):
        """Computed field: Check if email exists"""
        return "Has Email" if obj.email else "No Email"

    @staticmethod
    def get_contact_summary(obj):
        """Computed field: Contact information"""
        email = obj.email or "No email"
        phone = obj.handphone or "No phone"
        return f"Email: {email}, Phone: {phone}"

serializer_class = SerializerFactory.create_serializer(MahasiswaWithComputedFieldsAPI)

print(f"✅ Created serializer with computed fields")
print(f"   Fields: {serializer_class().fields.keys()}")

try:
    mahasiswa = Mahasiswa.objects.first()
    if mahasiswa:
        serializer = serializer_class(mahasiswa)
        data = serializer.data
        print(f"\n📊 Sample data with computed fields:")
        print(f"   - Nama: {data.get('nama_mahasiswa')}")
        print(f"   - Full Info: {data.get('full_info')}")
        print(f"   - Email Status: {data.get('email_status')}")
        print(f"   - Contact Summary: {data.get('contact_summary')}")
except Exception as e:
    print(f"⚠️  Note: {e}")

print()

# ============================================================================
# Feature 2: Custom Validation
# ============================================================================
print("-" * 70)
print("FEATURE 2: Custom Validation")
print("-" * 70)

class MahasiswaWithValidationAPI(AutoAPI):
    """API dengan custom validation"""
    model = Mahasiswa
    fields = ['id_mahasiswa', 'nama_mahasiswa', 'nim', 'email', 'jenis_kelamin']

    @staticmethod
    def validate_nama_mahasiswa(value):
        """Validation: Name must be at least 3 characters"""
        if len(value.strip()) < 3:
            raise drf_serializers.ValidationError(
                "Nama mahasiswa harus minimal 3 karakter"
            )
        return value.strip().title()  # Capitalize each word

    @staticmethod
    def validate_nim(value):
        """Validation: NIM format check"""
        if value and not value.startswith('A11'):
            raise drf_serializers.ValidationError(
                "NIM harus dimulai dengan 'A11'"
            )
        return value

    @staticmethod
    def validate_email(value):
        """Validation: Email domain check"""
        if value and '@' in value:
            domain = value.split('@')[1]
            allowed_domains = ['mhs.dinus.ac.id', 'dinus.ac.id', 'gmail.com']
            if domain not in allowed_domains:
                raise drf_serializers.ValidationError(
                    f"Email domain harus salah satu dari: {', '.join(allowed_domains)}"
                )
        return value

    @staticmethod
    def validate_jenis_kelamin(value):
        """Validation: Gender must be L or P"""
        if value not in ['L', 'P']:
            raise drf_serializers.ValidationError(
                "Jenis kelamin harus 'L' atau 'P'"
            )
        return value

    @staticmethod
    def validate(data):
        """Object-level validation"""
        # Check if email exists when NIM is provided
        if data.get('nim') and not data.get('email'):
            raise drf_serializers.ValidationError(
                "Mahasiswa dengan NIM harus memiliki email"
            )
        return data

validation_serializer = SerializerFactory.create_serializer(MahasiswaWithValidationAPI)

print("✅ Created serializer with custom validation")
print("\n📋 Validation Rules:")
print("   1. Nama minimal 3 karakter, auto-capitalize")
print("   2. NIM harus dimulai dengan 'A11'")
print("   3. Email harus dari domain yang diizinkan")
print("   4. Jenis kelamin harus 'L' atau 'P'")
print("   5. Mahasiswa dengan NIM harus punya email")

# Test validation
print("\n🧪 Testing validation:")

# Test 1: Invalid NIM
test_data_1 = {
    'nama_mahasiswa': 'Test Student',
    'nim': 'B12.2024.12345',  # Invalid - doesn't start with A11
    'email': 'test@mhs.dinus.ac.id',
    'jenis_kelamin': 'L'
}

serializer = validation_serializer(data=test_data_1)
if not serializer.is_valid():
    print("   ❌ Test 1 (Invalid NIM): Validation failed as expected")
    print(f"      Errors: {dict(serializer.errors)}")

# Test 2: Valid data
test_data_2 = {
    'nama_mahasiswa': 'valid student name',
    'nim': 'A11.2024.12345',
    'email': 'test@mhs.dinus.ac.id',
    'jenis_kelamin': 'L'
}

serializer = validation_serializer(data=test_data_2)
if serializer.is_valid():
    print("   ✅ Test 2 (Valid data): Validation passed")
    print(f"      Validated name: {serializer.validated_data['nama_mahasiswa']}")

print()

# ============================================================================
# Feature 3: Custom Fields
# ============================================================================
print("-" * 70)
print("FEATURE 3: Custom Fields")
print("-" * 70)

class DosenWithCustomFieldsAPI(AutoAPI):
    """API dengan custom additional fields"""
    model = Dosen
    fields = ['id_dosen', 'nama_dosen', 'nidn', 'nip',
              'status_badge', 'metadata', 'profile_url']

    # Define custom fields
    custom_fields = {
        'status_badge': drf_serializers.CharField(
            read_only=True,
            help_text="Status badge for UI display"
        ),
        'metadata': drf_serializers.JSONField(
            required=False,
            help_text="Additional metadata as JSON"
        ),
        'profile_url': drf_serializers.URLField(
            required=False,
            help_text="URL to dosen profile page"
        )
    }

custom_fields_serializer = SerializerFactory.create_serializer(DosenWithCustomFieldsAPI)

print("✅ Created serializer with custom fields")
print("\n📋 Custom Fields:")
serializer = custom_fields_serializer()
for field_name, field in serializer.fields.items():
    if field_name in ['status_badge', 'metadata', 'profile_url']:
        print(f"   - {field_name}: {field.__class__.__name__}")
        if hasattr(field, 'help_text'):
            print(f"     Help: {field.help_text}")

print()

# ============================================================================
# Feature 4: Combined Advanced Features
# ============================================================================
print("-" * 70)
print("FEATURE 4: Combined Advanced Features")
print("-" * 70)

class MahasiswaAdvancedAPI(AutoAPI):
    """
    API dengan kombinasi semua advanced features:
    - Computed fields via SerializerMethodField
    - Custom validation
    - Custom fields
    """
    model = Mahasiswa
    fields = [
        'id_mahasiswa', 'nama_mahasiswa', 'nim', 'email', 'jenis_kelamin',
        'full_identity', 'age_category', 'status', 'tags'
    ]

    # Custom fields
    custom_fields = {
        'status': drf_serializers.ChoiceField(
            choices=['active', 'inactive', 'graduated'],
            default='active',
            help_text="Student status"
        ),
        'tags': drf_serializers.ListField(
            child=drf_serializers.CharField(max_length=50),
            required=False,
            help_text="Tags for categorization"
        )
    }

    # Computed fields
    @staticmethod
    def get_full_identity(obj):
        """Complete identity string"""
        nim = getattr(obj, 'nim', 'No NIM')
        return f"{nim} | {obj.nama_mahasiswa} | {obj.jenis_kelamin}"

    @staticmethod
    def get_age_category(obj):
        """Calculate age category"""
        # Simple categorization based on data
        if obj.tanggal_lahir:
            from datetime import date
            today = date.today()
            age = today.year - obj.tanggal_lahir.year
            if age < 20:
                return "Under 20"
            elif age < 25:
                return "20-25"
            else:
                return "Over 25"
        return "Unknown"

    # Validation
    @staticmethod
    def validate_email(value):
        """Email validation"""
        if value:
            if not '@' in value:
                raise drf_serializers.ValidationError("Email tidak valid")
            if not value.endswith('.id') and not value.endswith('.com'):
                raise drf_serializers.ValidationError(
                    "Email harus berakhiran .id atau .com"
                )
        return value

    @staticmethod
    def validate_tags(value):
        """Tags validation"""
        if value and len(value) > 5:
            raise drf_serializers.ValidationError("Maksimal 5 tags")
        return value

advanced_serializer = SerializerFactory.create_serializer(MahasiswaAdvancedAPI)

print("✅ Created advanced serializer with combined features")
print("\n📊 Features Overview:")
print("   1. Computed Fields:")
print("      - full_identity: Combined NIM, name, and gender")
print("      - age_category: Age-based categorization")
print("   2. Custom Fields:")
print("      - status: Choice field with predefined options")
print("      - tags: List of strings for categorization")
print("   3. Validation:")
print("      - Email format and domain validation")
print("      - Tags count limit (max 5)")

print("\n🔍 Serializer Fields:")
serializer = advanced_serializer()
for field_name in serializer.fields.keys():
    field = serializer.fields[field_name]
    field_type = field.__class__.__name__
    print(f"   - {field_name}: {field_type}")

print()

# ============================================================================
# Feature 5: Real World Example - Nested Data
# ============================================================================
print("-" * 70)
print("FEATURE 5: Real World Example")
print("-" * 70)

class KelasKuliahEnhancedAPI(AutoAPI):
    """API untuk kelas kuliah dengan enhanced fields"""
    model = KelasKuliah
    fields = [
        'id_kelas_kuliah', 'nama_kelas_kuliah', 'sks', 'jumlah_mahasiswa',
        'capacity_status', 'formatted_schedule', 'class_info'
    ]

    @staticmethod
    def get_capacity_status(obj):
        """Check class capacity"""
        mahasiswa_count = obj.jumlah_mahasiswa or 0
        if mahasiswa_count == 0:
            return "Empty"
        elif mahasiswa_count < 20:
            return "Available"
        elif mahasiswa_count < 40:
            return "Almost Full"
        else:
            return "Full"

    @staticmethod
    def get_formatted_schedule(obj):
        """Format schedule information"""
        if obj.tanggal_mulai_efektif and obj.tanggal_akhir_efektif:
            start = obj.tanggal_mulai_efektif.strftime("%d/%m/%Y")
            end = obj.tanggal_akhir_efektif.strftime("%d/%m/%Y")
            return f"{start} - {end}"
        return "No schedule"

    @staticmethod
    def get_class_info(obj):
        """Complete class information"""
        return {
            'name': obj.nama_kelas_kuliah,
            'sks': obj.sks,
            'students': obj.jumlah_mahasiswa or 0,
            'code': obj.id_kelas_kuliah
        }

kelas_serializer = SerializerFactory.create_serializer(KelasKuliahEnhancedAPI)

print("✅ Created enhanced kelas kuliah serializer")

try:
    kelas = KelasKuliah.objects.first()
    if kelas:
        serializer = kelas_serializer(kelas)
        data = serializer.data
        print(f"\n📊 Sample Kelas Data:")
        print(f"   - Nama: {data.get('nama_kelas_kuliah')}")
        print(f"   - SKS: {data.get('sks')}")
        print(f"   - Jumlah Mahasiswa: {data.get('jumlah_mahasiswa')}")
        print(f"   - Capacity Status: {data.get('capacity_status')}")
        print(f"   - Schedule: {data.get('formatted_schedule')}")
        print(f"   - Class Info: {data.get('class_info')}")
except Exception as e:
    print(f"⚠️  Note: {e}")

print()

# ============================================================================
# Summary
# ============================================================================
print("=" * 70)
print("📊 Advanced Features Summary")
print("=" * 70)
print()
print("✅ Feature 1: SerializerMethodField - Custom computed fields")
print("   - get_<field_name> methods auto-generate fields")
print("   - Perfect for calculated/derived data")
print()
print("✅ Feature 2: Custom Validation - Field & object-level")
print("   - validate_<field_name> for field-specific validation")
print("   - validate() for object-level validation")
print("   - Must return validated value")
print()
print("✅ Feature 3: Custom Fields - Additional field types")
print("   - Define via custom_fields attribute")
print("   - Supports any DRF field type")
print()
print("✅ Feature 4: Combined Features - All features together")
print("   - Mix computed fields, validation, and custom fields")
print("   - Create powerful, feature-rich APIs")
print()
print("🎉 All advanced features demonstrated successfully!")
print()
print("📖 Next Steps:")
print("   1. Test features with your models")
print("   2. Run advanced tests: pytest django_autoapi/tests/test_advanced_features.py")
print("   3. Create your own custom serializers")
print("   4. Explore nested serializers (coming soon)")
print()
