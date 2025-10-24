# 🚀 Advanced Testing Patterns untuk Django

## 📋 Overview

Pattern testing lanjutan untuk skenario kompleks:
- Factory Pattern untuk test data
- Parameterized tests
- Data-driven testing
- Performance testing
- Integration testing
- E2E testing

---

## 1. Factory Pattern (Factory Boy)

### **1.1 Installation**

```bash
pip install factory-boy
```

### **1.2 Define Factories**

```python
# apps/academic/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from apps.feeder.models.mahasiswa import RiwayatPendidikan, Biodata
from apps.feeder.models.dosen import Dosen
from apps.feeder.models.master import Prodi
from datetime import datetime


class BiodataFactory(DjangoModelFactory):
    """Factory for Biodata model"""

    class Meta:
        model = Biodata

    nama_mahasiswa = factory.Sequence(lambda n: f"Student {n}")
    jenis_kelamin = factory.Iterator(['L', 'P'])
    tanggal_lahir = factory.LazyFunction(
        lambda: datetime(2000, 1, 1).date()
    )
    tempat_lahir = 'Jakarta'
    deleted = False


class RiwayatPendidikanFactory(DjangoModelFactory):
    """Factory for RiwayatPendidikan model"""

    class Meta:
        model = RiwayatPendidikan

    nim = factory.Sequence(lambda n: f"TEST{n:04d}")
    id_mahasiswa = factory.SubFactory(BiodataFactory)
    nama_status_mahasiswa = 'Aktif'
    ipk = factory.Faker('pyfloat', min_value=2.0, max_value=4.0, right_digits=2)
    deleted = False

    @factory.post_generation
    def set_biodata_name(self, create, extracted, **kwargs):
        """Set biodata name to match"""
        if create and self.id_mahasiswa:
            self.id_mahasiswa.nama_mahasiswa = f"Mahasiswa {self.nim}"
            self.id_mahasiswa.save()


class DosenFactory(DjangoModelFactory):
    """Factory for Dosen model"""

    class Meta:
        model = Dosen

    nip = factory.Sequence(lambda n: f"DOSEN{n:04d}")
    nama_dosen = factory.Sequence(lambda n: f"Dr. Dosen {n}")
    nidn = factory.Sequence(lambda n: f"NIDN{n:06d}")
    jenis_kelamin = factory.Iterator(['L', 'P'])
    deleted = False


class ProdiFactory(DjangoModelFactory):
    """Factory for Prodi model"""

    class Meta:
        model = Prodi

    kode_program_studi = factory.Sequence(lambda n: f"PRODI{n:02d}")
    nama_program_studi = factory.Sequence(lambda n: f"Program Studi {n}")
    nama_jenjang_pendidikan = 'S1'
    deleted = False


# Advanced: Factory with Traits
class MahasiswaFactory(RiwayatPendidikanFactory):
    """Extended factory with traits"""

    class Params:
        # Traits (reusable configurations)
        aktif = factory.Trait(
            nama_status_mahasiswa='Aktif',
            ipk=factory.Faker('pyfloat', min_value=3.0, max_value=4.0)
        )
        cuti = factory.Trait(
            nama_status_mahasiswa='Cuti',
            ipk=factory.Faker('pyfloat', min_value=2.5, max_value=3.5)
        )
        lulus = factory.Trait(
            nama_status_mahasiswa='Lulus',
            ipk=factory.Faker('pyfloat', min_value=3.0, max_value=4.0)
        )
        prestasi = factory.Trait(
            ipk=factory.Faker('pyfloat', min_value=3.7, max_value=4.0)
        )
```

### **1.3 Usage in Tests**

```python
# apps/academic/tests/test_with_factories.py
from django.test import TestCase
from apps.academic.tests.factories import (
    MahasiswaFactory, DosenFactory, BiodataFactory
)


class FactoryTest(TestCase):
    """Test using Factory Boy"""

    def test_create_single_mahasiswa(self):
        """Test: Create single mahasiswa with factory"""
        # Simple creation
        mhs = MahasiswaFactory()

        self.assertIsNotNone(mhs.nim)
        self.assertIsNotNone(mhs.id_mahasiswa)
        print(f"✓ Created: {mhs.nim} - {mhs.id_mahasiswa.nama_mahasiswa}")

    def test_create_with_custom_data(self):
        """Test: Override factory defaults"""
        mhs = MahasiswaFactory(
            nim='CUSTOM001',
            ipk=3.9,
            id_mahasiswa__nama_mahasiswa='Custom Name'  # SubFactory syntax
        )

        self.assertEqual(mhs.nim, 'CUSTOM001')
        self.assertEqual(mhs.ipk, 3.9)
        self.assertEqual(mhs.id_mahasiswa.nama_mahasiswa, 'Custom Name')

    def test_create_batch(self):
        """Test: Create multiple instances"""
        # Create 10 mahasiswa
        mahasiswa_list = MahasiswaFactory.create_batch(10)

        self.assertEqual(len(mahasiswa_list), 10)

        # All have unique NIMs
        nims = [m.nim for m in mahasiswa_list]
        self.assertEqual(len(nims), len(set(nims)))  # All unique

        print(f"✓ Created batch: {nims}")

    def test_create_with_traits(self):
        """Test: Use factory traits"""
        # Create mahasiswa with different traits
        mhs_aktif = MahasiswaFactory(aktif=True)
        mhs_cuti = MahasiswaFactory(cuti=True)
        mhs_lulus = MahasiswaFactory(lulus=True)
        mhs_prestasi = MahasiswaFactory(prestasi=True)

        self.assertEqual(mhs_aktif.nama_status_mahasiswa, 'Aktif')
        self.assertEqual(mhs_cuti.nama_status_mahasiswa, 'Cuti')
        self.assertEqual(mhs_lulus.nama_status_mahasiswa, 'Lulus')
        self.assertGreaterEqual(mhs_prestasi.ipk, 3.7)

    def test_build_without_save(self):
        """Test: Build instance without saving to DB"""
        # Build only (not saved to DB)
        mhs = MahasiswaFactory.build()

        self.assertIsNone(mhs.pk)  # No primary key
        self.assertIsNotNone(mhs.nim)

        # Save manually if needed
        mhs.save()
        self.assertIsNotNone(mhs.pk)

    def test_stub_for_serialization_tests(self):
        """Test: Create stub for testing serializers"""
        # Stub (no DB interaction at all)
        mhs_stub = MahasiswaFactory.stub()

        self.assertIsNone(mhs_stub.pk)
        self.assertIsNotNone(mhs_stub.nim)
        # Use for testing serializers, forms, etc.
```

---

## 2. Parameterized Tests

### **2.1 Using unittest.TestCase**

```python
# apps/academic/tests/test_parameterized.py
from django.test import TestCase
from apps.academic.tests.factories import MahasiswaFactory


class ParameterizedTest(TestCase):
    """Test with multiple input combinations"""

    def _test_ipk_validation(self, ipk, should_be_valid):
        """Helper method for IPK validation"""
        mhs = MahasiswaFactory(ipk=ipk)

        if should_be_valid:
            self.assertIsNotNone(mhs.pk)
            self.assertEqual(mhs.ipk, ipk)
        else:
            # Add your validation logic
            pass

    def test_valid_ipk_values(self):
        """Test: Multiple valid IPK values"""
        valid_ipks = [0.0, 2.0, 2.5, 3.0, 3.5, 4.0]

        for ipk in valid_ipks:
            with self.subTest(ipk=ipk):
                self._test_ipk_validation(ipk, should_be_valid=True)
                print(f"✓ Valid IPK: {ipk}")

    def test_invalid_ipk_values(self):
        """Test: Multiple invalid IPK values"""
        invalid_ipks = [-1.0, 4.5, 5.0]

        for ipk in invalid_ipks:
            with self.subTest(ipk=ipk):
                with self.assertRaises(Exception):
                    self._test_ipk_validation(ipk, should_be_valid=False)
                print(f"✓ Invalid IPK rejected: {ipk}")
```

### **2.2 Using pytest parametrize**

```python
# apps/academic/tests/test_pytest_params.py
import pytest
from apps.academic.tests.factories import MahasiswaFactory


@pytest.mark.django_db
class TestIPKValidation:
    """Test IPK validation with pytest parametrize"""

    @pytest.mark.parametrize("ipk,expected", [
        (0.0, True),
        (2.0, True),
        (2.5, True),
        (3.0, True),
        (3.5, True),
        (4.0, True),
        (-1.0, False),
        (4.5, False),
        (5.0, False),
    ])
    def test_ipk_range(self, ipk, expected):
        """Test: IPK should be between 0.0 and 4.0"""
        if expected:
            mhs = MahasiswaFactory(ipk=ipk)
            assert mhs.ipk == ipk
        else:
            with pytest.raises(Exception):
                MahasiswaFactory(ipk=ipk)

    @pytest.mark.parametrize("status", [
        'Aktif', 'Cuti', 'Lulus', 'Non-Aktif', 'Mengundurkan Diri'
    ])
    def test_status_values(self, status):
        """Test: Different status values"""
        mhs = MahasiswaFactory(nama_status_mahasiswa=status)
        assert mhs.nama_status_mahasiswa == status
```

---

## 3. Data-Driven Testing

### **3.1 CSV Data Source**

```python
# apps/academic/tests/test_data_driven.py
import csv
from django.test import TestCase
from apps.academic.tests.factories import MahasiswaFactory


class DataDrivenTest(TestCase):
    """Test using external data files"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load test data from CSV
        cls.test_data = []
        with open('apps/academic/tests/data/mahasiswa_test_data.csv', 'r') as f:
            reader = csv.DictReader(f)
            cls.test_data = list(reader)

    def test_create_from_csv(self):
        """Test: Create mahasiswa from CSV data"""
        for row in self.test_data:
            with self.subTest(nim=row['nim']):
                mhs = MahasiswaFactory(
                    nim=row['nim'],
                    ipk=float(row['ipk']),
                    id_mahasiswa__nama_mahasiswa=row['nama']
                )

                self.assertEqual(mhs.nim, row['nim'])
                self.assertAlmostEqual(mhs.ipk, float(row['ipk']), places=2)
                print(f"✓ Created from CSV: {mhs.nim}")
```

**CSV File:**
```csv
# apps/academic/tests/data/mahasiswa_test_data.csv
nim,nama,ipk,status
TEST0001,John Doe,3.5,Aktif
TEST0002,Jane Smith,3.8,Aktif
TEST0003,Bob Johnson,2.9,Cuti
```

### **3.2 JSON Data Source**

```python
import json
from django.test import TestCase


class JSONDataDrivenTest(TestCase):
    """Test using JSON test data"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open('apps/academic/tests/data/test_scenarios.json', 'r') as f:
            cls.scenarios = json.load(f)

    def test_scenarios(self):
        """Test: Run all scenarios from JSON"""
        for scenario in self.scenarios:
            with self.subTest(name=scenario['name']):
                # Run scenario
                result = self.run_scenario(scenario)
                self.assertEqual(result, scenario['expected'])

    def run_scenario(self, scenario):
        """Execute test scenario"""
        # Your test logic here
        pass
```

---

## 4. Performance Testing

### **4.1 Query Performance Test**

```python
# apps/academic/tests/test_performance.py
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from apps.academic.tests.factories import MahasiswaFactory
import time


class PerformanceTest(TestCase):
    """Test query performance"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test data
        cls.mahasiswa_list = MahasiswaFactory.create_batch(100)

    def test_query_count(self):
        """Test: Should not have N+1 query problem"""
        from apps.feeder.models.mahasiswa import RiwayatPendidikan

        with CaptureQueriesContext(connection) as context:
            # Fetch mahasiswa with related biodata
            mahasiswa = RiwayatPendidikan.objects.select_related(
                'id_mahasiswa'
            ).filter(deleted=False)[:10]

            # Access related data
            for mhs in mahasiswa:
                _ = mhs.id_mahasiswa.nama_mahasiswa

        # Should be minimal queries (1-2 queries max)
        query_count = len(context.captured_queries)
        self.assertLessEqual(query_count, 2,
                            f"Too many queries: {query_count}")

        print(f"✓ Query count: {query_count}")
        for query in context.captured_queries:
            print(f"  SQL: {query['sql'][:100]}...")

    def test_bulk_create_performance(self):
        """Test: Bulk create should be fast"""
        start_time = time.time()

        # Create 1000 mahasiswa
        MahasiswaFactory.create_batch(1000)

        elapsed = time.time() - start_time

        # Should complete in reasonable time
        self.assertLess(elapsed, 10.0,  # 10 seconds
                       f"Bulk create too slow: {elapsed:.2f}s")

        print(f"✓ Created 1000 records in {elapsed:.2f}s")

    def test_query_optimization(self):
        """Test: Compare query performance"""
        from apps.feeder.models.mahasiswa import RiwayatPendidikan

        # Without optimization
        start = time.time()
        mhs_list = list(RiwayatPendidikan.objects.all()[:50])
        for mhs in mhs_list:
            _ = mhs.id_mahasiswa.nama_mahasiswa  # N+1 queries
        time_without = time.time() - start

        # With optimization
        start = time.time()
        mhs_list = list(
            RiwayatPendidikan.objects.select_related('id_mahasiswa')[:50]
        )
        for mhs in mhs_list:
            _ = mhs.id_mahasiswa.nama_mahasiswa  # Single query
        time_with = time.time() - start

        print(f"✓ Without select_related: {time_without:.4f}s")
        print(f"✓ With select_related: {time_with:.4f}s")
        print(f"✓ Improvement: {time_without/time_with:.2f}x faster")

        # Optimized should be significantly faster
        self.assertLess(time_with, time_without)
```

### **4.2 Load Testing**

```python
from django.test import TestCase
import concurrent.futures
from apps.academic.tests.factories import MahasiswaFactory


class LoadTest(TestCase):
    """Test system under load"""

    def test_concurrent_requests(self):
        """Test: Handle concurrent database operations"""

        def create_mahasiswa(i):
            """Create single mahasiswa"""
            try:
                mhs = MahasiswaFactory(nim=f"LOAD{i:04d}")
                return True
            except Exception as e:
                print(f"✗ Failed: {e}")
                return False

        # Create 100 mahasiswa concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(create_mahasiswa, i)
                for i in range(100)
            ]

            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(results)
        self.assertEqual(success_count, 100,
                        f"Only {success_count}/100 succeeded")

        print(f"✓ Concurrent create: {success_count}/100 succeeded")
```

---

## 5. Integration Testing

### **5.1 Multi-Component Test**

```python
# apps/academic/tests/test_integration.py
from django.test import TestCase
from apps.academic.tests.factories import MahasiswaFactory, DosenFactory
from apps.academic.graph_sync import GraphSyncManager


class IntegrationTest(TestCase):
    """Test integration between components"""

    def setUp(self):
        """Setup integration test"""
        self.graph_manager = GraphSyncManager()

    def tearDown(self):
        """Cleanup"""
        self.graph_manager.close()

    def test_mahasiswa_to_graph_sync(self):
        """Test: PostgreSQL → Neo4j sync"""
        # 1. Create in PostgreSQL
        mhs = MahasiswaFactory(nim='INTEG001')
        self.assertIsNotNone(mhs.pk)

        # 2. Sync to Neo4j
        node = self.graph_manager.sync_mahasiswa_node(mhs)
        self.assertIsNotNone(node)

        # 3. Verify in Neo4j
        from apps.academic.graph_models import MahasiswaNode
        found = MahasiswaNode.nodes.get(nim='INTEG001')
        self.assertEqual(found.nim, mhs.nim)

        print(f"✓ Integration: PostgreSQL → Neo4j successful")

    def test_full_workflow(self):
        """Test: Complete academic workflow"""
        # 1. Create mahasiswa
        mhs = MahasiswaFactory(nim='WORK001')

        # 2. Create dosen
        dosen = DosenFactory(nip='DOSEN001')

        # 3. Create kelas (if you have factory)
        # kelas = KelasFactory(...)

        # 4. Assign mahasiswa to kelas
        # ...

        # 5. Sync to graph
        self.graph_manager.sync_mahasiswa_node(mhs)
        self.graph_manager.sync_dosen_node(dosen)

        # 6. Query relationships
        from apps.academic.services.graph_service import AcademicGraphService
        result = AcademicGraphService.get_classmates('WORK001')

        self.assertIsInstance(result, list)
        print(f"✓ Full workflow completed")
```

### **5.2 API Integration Test**

```python
from django.test import TestCase
from rest_framework.test import APIClient
from apps.academic.tests.factories import MahasiswaFactory
from apps.users.models import User


class APIIntegrationTest(TestCase):
    """Test API integration flows"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_complete_crud_flow(self):
        """Test: Complete CRUD flow via API"""
        # 1. CREATE
        response = self.client.post('/api/v1/mahasiswa/', {
            'nim': 'API001',
            'nama': 'API Test Student',
            'ipk': 3.5
        }, format='json')
        self.assertEqual(response.status_code, 201)
        nim = response.data['nim']

        # 2. READ
        response = self.client.get(f'/api/v1/mahasiswa/{nim}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['nim'], 'API001')

        # 3. UPDATE
        response = self.client.patch(f'/api/v1/mahasiswa/{nim}/', {
            'ipk': 3.8
        }, format='json')
        self.assertEqual(response.status_code, 200)

        # 4. Verify update
        response = self.client.get(f'/api/v1/mahasiswa/{nim}/')
        self.assertEqual(response.data['ipk'], 3.8)

        # 5. DELETE
        response = self.client.delete(f'/api/v1/mahasiswa/{nim}/')
        self.assertEqual(response.status_code, 204)

        # 6. Verify deleted (should be soft delete)
        from apps.feeder.models.mahasiswa import RiwayatPendidikan
        mhs = RiwayatPendidikan.objects.get(nim=nim)
        self.assertTrue(mhs.deleted)

        print(f"✓ Complete CRUD flow via API")
```

---

## 6. Snapshot Testing

### **6.1 API Response Snapshot**

```python
from django.test import TestCase
from rest_framework.test import APIClient
import json
import hashlib


class SnapshotTest(TestCase):
    """Test API response consistency"""

    def setUp(self):
        self.client = APIClient()
        # Create predictable test data
        MahasiswaFactory(nim='SNAP001', ipk=3.5)

    def test_api_response_snapshot(self):
        """Test: API response should match snapshot"""
        response = self.client.get('/api/v1/mahasiswa/SNAP001/')

        # Calculate response hash
        response_hash = hashlib.md5(
            json.dumps(response.data, sort_keys=True).encode()
        ).hexdigest()

        # Expected hash (update when intentional changes)
        expected_hash = 'your-expected-hash-here'

        self.assertEqual(response_hash, expected_hash,
                        "API response structure changed!")
```

---

## 7. Test Helpers & Utilities

### **7.1 Test Mixins**

```python
# apps/academic/tests/mixins.py
from apps.academic.tests.factories import MahasiswaFactory


class MahasiswaTestMixin:
    """Reusable mahasiswa test setup"""

    def setUp_mahasiswa(self, count=1):
        """Create test mahasiswa"""
        if count == 1:
            self.mahasiswa = MahasiswaFactory()
        else:
            self.mahasiswa_list = MahasiswaFactory.create_batch(count)

    def assert_mahasiswa_valid(self, mhs):
        """Assert mahasiswa is valid"""
        self.assertIsNotNone(mhs.nim)
        self.assertIsNotNone(mhs.id_mahasiswa)
        self.assertGreaterEqual(mhs.ipk, 0.0)
        self.assertLessEqual(mhs.ipk, 4.0)


class APITestMixin:
    """Reusable API test setup"""

    def setUp_api(self):
        """Setup API client"""
        from rest_framework.test import APIClient
        from apps.users.models import User

        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def assert_api_success(self, response, status_code=200):
        """Assert API response is successful"""
        self.assertEqual(response.status_code, status_code)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])


# Usage
class MyTest(TestCase, MahasiswaTestMixin, APITestMixin):
    def setUp(self):
        self.setUp_mahasiswa(count=5)
        self.setUp_api()

    def test_something(self):
        self.assert_mahasiswa_valid(self.mahasiswa_list[0])
        # ...
```

---

## 8. Test Documentation

### **8.1 Docstring Best Practices**

```python
class WellDocumentedTest(TestCase):
    """
    Test suite for Mahasiswa model

    Tests cover:
    - Model creation and validation
    - Relationships with Biodata
    - IPK calculations
    - Status transitions

    Setup:
    - Creates 10 test mahasiswa with various status
    - Creates associated biodata records
    - Sets up prodi relationships
    """

    def test_mahasiswa_creation(self):
        """
        Test: Mahasiswa can be created with valid data

        Given:
            - Valid NIM, nama, and IPK
        When:
            - Creating new RiwayatPendidikan instance
        Then:
            - Instance should be saved successfully
            - All fields should match input
            - Associated biodata should be created
        """
        # Test implementation...
        pass
```

---

## Summary

**Advanced Testing Patterns:**

1. ✅ **Factory Boy**: Flexible test data generation
2. ✅ **Parameterized Tests**: Test multiple inputs efficiently
3. ✅ **Data-Driven**: Use external data sources (CSV, JSON)
4. ✅ **Performance Tests**: Query optimization & load testing
5. ✅ **Integration Tests**: Multi-component workflows
6. ✅ **Test Mixins**: Reusable test utilities
7. ✅ **Snapshot Testing**: API response consistency
8. ✅ **Good Documentation**: Clear test intent

**Benefits:**
- 🚀 Faster test creation
- 🔄 More maintainable tests
- 📊 Better coverage
- 🎯 Clear test intent
- ⚡ Performance insights

---

**Next:** Apply these patterns to your graph database testing! 🧪
