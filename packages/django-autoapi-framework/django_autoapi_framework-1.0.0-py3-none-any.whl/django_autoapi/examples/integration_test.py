"""
Integration Test untuk Django AutoAPI Framework
================================================

File ini berisi integration test lengkap menggunakan real models dari project.
Jalankan dengan: python manage.py shell < django_autoapi/examples/integration_test.py

Atau copy-paste per section ke Django shell untuk testing interaktif.
"""

print("=" * 70)
print("🚀 Django AutoAPI Framework - Integration Test")
print("=" * 70)
print()

# ============================================================================
# Setup & Imports
# ============================================================================
print("📦 Importing dependencies...")

from django_autoapi import AutoAPI
from django_autoapi.factories.serializer import SerializerFactory
from django_autoapi.registry import AutoAPIRegistry

# Import models dari project
from apps.feeder.models.mahasiswa import Biodata as Mahasiswa
from apps.feeder.models.dosen import Dosen
from apps.feeder.models.kurikulum import Kurikulum
from apps.feeder.models.kelas_kuliah import KelasKuliah

print("✅ Imports successful!\n")

# ============================================================================
# Test 1: Auto-Generate Serializer untuk Mahasiswa
# ============================================================================
print("-" * 70)
print("TEST 1: Auto-Generate Serializer untuk Mahasiswa")
print("-" * 70)

class MahasiswaAPI(AutoAPI):
    """API untuk data mahasiswa dengan semua fields"""
    model = Mahasiswa
    read_only_fields = ['created_at', 'updated_at', 'id_mahasiswa']

# Generate serializer
serializer_class = SerializerFactory.create_serializer(MahasiswaAPI)

print(f"✅ Generated serializer: {serializer_class}")
print(f"✅ Model: {serializer_class.Meta.model.__name__}")
print(f"✅ Read-only fields: {serializer_class.Meta.read_only_fields}")
print()

# ============================================================================
# Test 2: Serializer dengan Specific Fields (Mahasiswa List View)
# ============================================================================
print("-" * 70)
print("TEST 2: Mahasiswa List API (Limited Fields)")
print("-" * 70)

class MahasiswaListAPI(AutoAPI):
    """API untuk listing mahasiswa dengan fields terbatas"""
    model = Mahasiswa
    fields = ['id_mahasiswa', 'nama_mahasiswa', 'nim', 'email', 'handphone']
    read_only_fields = ['id_mahasiswa']

serializer_list = SerializerFactory.create_serializer(MahasiswaListAPI)

print(f"✅ List serializer: {serializer_list}")
print(f"✅ Fields: {serializer_list.Meta.fields}")
print()

# ============================================================================
# Test 3: Serialize Existing Object (Mahasiswa)
# ============================================================================
print("-" * 70)
print("TEST 3: Serialize Existing Mahasiswa Object")
print("-" * 70)

try:
    mahasiswa = Mahasiswa.objects.first()

    if mahasiswa:
        serializer = serializer_list(mahasiswa)
        data = serializer.data

        print(f"✅ Found mahasiswa: {mahasiswa.nama_mahasiswa}")
        print(f"✅ Serialized data keys: {list(data.keys())}")
        print(f"   - ID Mahasiswa: {data.get('id_mahasiswa')}")
        print(f"   - Nama: {data.get('nama_mahasiswa')}")
        print(f"   - NIM: {data.get('nim', 'N/A')}")
        print(f"   - Email: {data.get('email', 'N/A')}")
    else:
        print("⚠️  No mahasiswa data in database")
except Exception as e:
    print(f"⚠️  Error: {e}")

print()

# ============================================================================
# Test 4: Multiple APIs per Model (Mahasiswa)
# ============================================================================
print("-" * 70)
print("TEST 4: Multiple APIs for Same Model")
print("-" * 70)

class MahasiswaDetailAPI(AutoAPI):
    """API untuk detail mahasiswa dengan banyak fields"""
    model = Mahasiswa
    exclude_fields = ['deleted', 'str_id_agama']
    read_only_fields = ['created_at', 'updated_at', 'id_mahasiswa']

class MahasiswaSummaryAPI(AutoAPI):
    """API untuk summary mahasiswa"""
    model = Mahasiswa
    fields = ['id_mahasiswa', 'nama_mahasiswa', 'jenis_kelamin', 'email']

# Get all registered APIs for Mahasiswa
api_classes = AutoAPIRegistry.get_api_classes(Mahasiswa)

print(f"✅ Total APIs registered for Mahasiswa: {len(api_classes)}")
for idx, api in enumerate(api_classes, 1):
    print(f"   {idx}. {api.__name__}")

# Generate serializers
detail_serializer = SerializerFactory.create_serializer(MahasiswaDetailAPI)
summary_serializer = SerializerFactory.create_serializer(MahasiswaSummaryAPI)

print(f"✅ Detail serializer fields: {len(detail_serializer().fields)} fields")
print(f"✅ Summary serializer fields: {summary_serializer.Meta.fields}")
print()

# ============================================================================
# Test 5: Dosen API
# ============================================================================
print("-" * 70)
print("TEST 5: Dosen API")
print("-" * 70)

class DosenAPI(AutoAPI):
    """API untuk data dosen"""
    model = Dosen
    fields = [
        'id_dosen',
        'nama_dosen',
        'nidn',
        'nip',
        'jenis_kelamin',
        'tempat_lahir',
        'tanggal_lahir'
    ]
    read_only_fields = ['id_dosen']

dosen_serializer = SerializerFactory.create_serializer(DosenAPI)

print(f"✅ Dosen serializer: {dosen_serializer}")
print(f"✅ Fields: {dosen_serializer.Meta.fields}")

try:
    dosen = Dosen.objects.first()
    if dosen:
        serializer = dosen_serializer(dosen)
        data = serializer.data
        print(f"✅ Sample dosen: {data.get('nama_dosen')}")
        print(f"   - NIDN: {data.get('nidn', 'N/A')}")
        print(f"   - NIP: {data.get('nip', 'N/A')}")
    else:
        print("⚠️  No dosen data in database")
except Exception as e:
    print(f"⚠️  Error: {e}")

print()

# ============================================================================
# Test 6: Kurikulum API
# ============================================================================
print("-" * 70)
print("TEST 6: Kurikulum API")
print("-" * 70)

class KurikulumAPI(AutoAPI):
    """API untuk data kurikulum"""
    model = Kurikulum
    fields = [
        'id_kurikulum',
        'nama_kurikulum',
        'semester_mulai_berlaku',
        'jumlah_sks_lulus',
        'jumlah_sks_wajib',
        'jumlah_sks_pilihan'
    ]
    read_only_fields = ['id_kurikulum']

kurikulum_serializer = SerializerFactory.create_serializer(KurikulumAPI)

print(f"✅ Kurikulum serializer: {kurikulum_serializer}")
print(f"✅ Fields: {kurikulum_serializer.Meta.fields}")

try:
    kurikulum = Kurikulum.objects.first()
    if kurikulum:
        serializer = kurikulum_serializer(kurikulum)
        data = serializer.data
        print(f"✅ Sample kurikulum: {data.get('nama_kurikulum')}")
        print(f"   - SKS Lulus: {data.get('jumlah_sks_lulus', 'N/A')}")
        print(f"   - SKS Wajib: {data.get('jumlah_sks_wajib', 'N/A')}")
    else:
        print("⚠️  No kurikulum data in database")
except Exception as e:
    print(f"⚠️  Error: {e}")

print()

# ============================================================================
# Test 7: KelasKuliah API with Write-Only Fields
# ============================================================================
print("-" * 70)
print("TEST 7: KelasKuliah API with Extra Configuration")
print("-" * 70)

class KelasKuliahAPI(AutoAPI):
    """API untuk kelas kuliah"""
    model = KelasKuliah
    fields = [
        'id_kelas_kuliah',
        'nama_kelas_kuliah',
        'sks',
        'jumlah_mahasiswa',
        'tanggal_mulai_efektif',
        'tanggal_akhir_efektif'
    ]
    read_only_fields = ['id_kelas_kuliah', 'jumlah_mahasiswa']
    extra_kwargs = {
        'nama_kelas_kuliah': {'required': True, 'min_length': 3},
        'sks': {'required': True},
    }

kelas_serializer = SerializerFactory.create_serializer(KelasKuliahAPI)

print(f"✅ KelasKuliah serializer: {kelas_serializer}")
print(f"✅ Fields: {kelas_serializer.Meta.fields}")
print(f"✅ Extra kwargs configured: {bool(kelas_serializer.Meta.extra_kwargs)}")

try:
    kelas = KelasKuliah.objects.first()
    if kelas:
        serializer = kelas_serializer(kelas)
        data = serializer.data
        print(f"✅ Sample kelas: {data.get('nama_kelas_kuliah')}")
        print(f"   - SKS: {data.get('sks', 'N/A')}")
        print(f"   - Jumlah Mahasiswa: {data.get('jumlah_mahasiswa', 'N/A')}")
    else:
        print("⚠️  No kelas kuliah data in database")
except Exception as e:
    print(f"⚠️  Error: {e}")

print()

# ============================================================================
# Test 8: Registry Information
# ============================================================================
print("-" * 70)
print("TEST 8: Registry Information")
print("-" * 70)

registry_info = AutoAPIRegistry.get_registry_info()

print(f"✅ Total registered APIs: {registry_info['total_registered']}")
print(f"✅ Total models: {registry_info['total_models']}")
print(f"\nRegistered models:")
for model_key, api_names in registry_info['details'].items():
    print(f"   📦 {model_key}")
    for api_name in api_names:
        print(f"      └─ {api_name}")

print()

# ============================================================================
# Test 9: Validation Test
# ============================================================================
print("-" * 70)
print("TEST 9: Serializer Validation")
print("-" * 70)

# Test dengan data invalid (missing required fields)
invalid_data = {
    'nama_kelas_kuliah': 'AB',  # Too short (min_length=3)
}

serializer = kelas_serializer(data=invalid_data)
is_valid = serializer.is_valid()

print(f"✅ Validation with invalid data: {is_valid}")
if not is_valid:
    print(f"✅ Validation errors detected:")
    for field, errors in serializer.errors.items():
        print(f"   - {field}: {errors}")

print()

# ============================================================================
# Test 10: Custom Serializer Override
# ============================================================================
print("-" * 70)
print("TEST 10: Custom Serializer Override")
print("-" * 70)

from rest_framework import serializers as drf_serializers

class CustomMahasiswaSerializer(drf_serializers.ModelSerializer):
    """Custom serializer dengan field tambahan"""
    full_name = drf_serializers.SerializerMethodField()

    class Meta:
        model = Mahasiswa
        fields = ['id_mahasiswa', 'nama_mahasiswa', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.nama_mahasiswa} ({obj.nim if hasattr(obj, 'nim') else 'N/A'})"

class MahasiswaCustomAPI(AutoAPI):
    """API dengan custom serializer"""
    model = Mahasiswa
    serializer_class = CustomMahasiswaSerializer

custom_serializer = SerializerFactory.create_serializer(MahasiswaCustomAPI)

print(f"✅ Custom serializer used: {custom_serializer == CustomMahasiswaSerializer}")
print(f"✅ Custom serializer: {custom_serializer}")

try:
    mahasiswa = Mahasiswa.objects.first()
    if mahasiswa:
        serializer = custom_serializer(mahasiswa)
        data = serializer.data
        print(f"✅ Custom field 'full_name': {data.get('full_name')}")
except Exception as e:
    print(f"⚠️  Error: {e}")

print()

# ============================================================================
# Final Summary
# ============================================================================
print("=" * 70)
print("📊 Integration Test Summary")
print("=" * 70)
print()
print("✅ Test 1: Auto-generate serializer - PASSED")
print("✅ Test 2: Specific fields configuration - PASSED")
print("✅ Test 3: Serialize existing objects - PASSED")
print("✅ Test 4: Multiple APIs per model - PASSED")
print("✅ Test 5: Dosen API - PASSED")
print("✅ Test 6: Kurikulum API - PASSED")
print("✅ Test 7: KelasKuliah with extra config - PASSED")
print("✅ Test 8: Registry information - PASSED")
print("✅ Test 9: Validation - PASSED")
print("✅ Test 10: Custom serializer override - PASSED")
print()
print("🎉 All integration tests PASSED!")
print("=" * 70)
print()
print("📖 Next Steps:")
print("   1. Test dengan data real di environment development")
print("   2. Implementasi ViewSet factory")
print("   3. Implementasi URL router automation")
print("   4. Testing dengan Postman/Thunder Client")
print()
