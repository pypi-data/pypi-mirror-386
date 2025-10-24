# 🧪 Django Testing Guide - Unit Test dengan Data Dummy

## 📋 Overview

Panduan lengkap untuk membuat unit test di Django dengan:
- Setup/teardown data dummy otomatis
- Test database terpisah
- Clean up otomatis setelah test
- Best practices testing

---

## 1. Konsep Django Testing

### **1.1 Test Database**

Django otomatis membuat **test database** terpisah:

```
Development Database: nakula_db
Testing Database: test_nakula_db  ← Created automatically
```

**Karakteristik:**
- ✅ Dibuat otomatis sebelum test
- ✅ Dihapus otomatis setelah test
- ✅ Isolated dari data production
- ✅ Fresh database setiap run
- ✅ Rollback otomatis setelah setiap test

### **1.2 Test Lifecycle**

```python
1. setUpClass()           # Run ONCE before all tests in class
   ├── Create test database
   └── Run migrations

2. setUp()                # Run BEFORE each test method
   ├── Start transaction
   └── Create test data

3. test_something()       # Your test method
   └── Assertions

4. tearDown()             # Run AFTER each test method
   ├── Rollback transaction
   └── Clean data automatically

5. tearDownClass()        # Run ONCE after all tests
   └── Drop test database
```

**Key Point:** Data otomatis di-clean setelah setiap test method!

---

## 2. Basic Test Structure

### **2.1 Simple Test Example**

```python
# apps/academic/tests/test_models.py
from django.test import TestCase
from apps.feeder.models.mahasiswa import RiwayatPendidikan, Biodata


class MahasiswaModelTest(TestCase):
    """Test Mahasiswa models"""

    def setUp(self):
        """
        Create test data BEFORE each test method
        This runs before EVERY test_* method
        """
        # Create dummy biodata
        self.biodata = Biodata.objects.create(
            nama_mahasiswa='John Doe Test',
            jenis_kelamin='L',
            tanggal_lahir='2000-01-01',
            deleted=False
        )

        # Create dummy riwayat pendidikan
        self.riwayat = RiwayatPendidikan.objects.create(
            nim='TEST001',
            id_mahasiswa=self.biodata,
            nama_status_mahasiswa='Aktif',
            ipk=3.5,
            deleted=False
        )

        print(f"✓ Created test data: {self.riwayat.nim}")

    def tearDown(self):
        """
        Clean up AFTER each test method
        Actually, Django does this automatically via transaction rollback
        But you can add custom cleanup here if needed
        """
        print(f"✓ Test finished, data will be rolled back")

    def test_mahasiswa_creation(self):
        """Test: Can create mahasiswa"""
        self.assertEqual(self.riwayat.nim, 'TEST001')
        self.assertEqual(self.riwayat.id_mahasiswa.nama_mahasiswa, 'John Doe Test')
        print("✓ test_mahasiswa_creation passed")

    def test_mahasiswa_ipk(self):
        """Test: IPK is correctly stored"""
        self.assertEqual(self.riwayat.ipk, 3.5)
        self.assertIsInstance(self.riwayat.ipk, float)
        print("✓ test_mahasiswa_ipk passed")

    def test_mahasiswa_query(self):
        """Test: Can query mahasiswa"""
        found = RiwayatPendidikan.objects.get(nim='TEST001')
        self.assertEqual(found.nim, self.riwayat.nim)
        print("✓ test_mahasiswa_query passed")
```

**Run Test:**
```bash
# Run specific test file
python manage.py test apps.academic.tests.test_models

# Run specific test class
python manage.py test apps.academic.tests.test_models.MahasiswaModelTest

# Run specific test method
python manage.py test apps.academic.tests.test_models.MahasiswaModelTest.test_mahasiswa_creation
```

**Output:**
```
Creating test database for alias 'default'...
✓ Created test data: TEST001
✓ test_mahasiswa_creation passed
✓ Test finished, data will be rolled back

✓ Created test data: TEST001
✓ test_mahasiswa_ipk passed
✓ Test finished, data will be rolled back

✓ Created test data: TEST001
✓ test_mahasiswa_query passed
✓ Test finished, data will be rolled back

----------------------------------------------------------------------
Ran 3 tests in 0.150s

OK
Destroying test database for alias 'default'...
```

---

## 3. Test Fixtures (Reusable Test Data)

### **3.1 Using Fixtures Class**

```python
# apps/academic/tests/fixtures.py
"""
Reusable test data fixtures
"""
from apps.feeder.models.mahasiswa import RiwayatPendidikan, Biodata
from apps.feeder.models.dosen import Dosen
from apps.feeder.models.master import Prodi


class TestDataFixtures:
    """Factory untuk membuat test data"""

    @staticmethod
    def create_biodata(**kwargs):
        """Create test biodata"""
        defaults = {
            'nama_mahasiswa': 'Test Student',
            'jenis_kelamin': 'L',
            'tanggal_lahir': '2000-01-01',
            'deleted': False
        }
        defaults.update(kwargs)
        return Biodata.objects.create(**defaults)

    @staticmethod
    def create_mahasiswa(nim='TEST001', **kwargs):
        """Create test mahasiswa with biodata"""
        biodata = kwargs.pop('biodata', None)
        if not biodata:
            biodata = TestDataFixtures.create_biodata(
                nama_mahasiswa=kwargs.get('nama', 'Test Student')
            )

        defaults = {
            'nim': nim,
            'id_mahasiswa': biodata,
            'nama_status_mahasiswa': 'Aktif',
            'ipk': 3.5,
            'deleted': False
        }
        defaults.update(kwargs)
        return RiwayatPendidikan.objects.create(**defaults)

    @staticmethod
    def create_dosen(nip='TEST_DOSEN_001', **kwargs):
        """Create test dosen"""
        defaults = {
            'nip': nip,
            'nama_dosen': 'Dr. Test Dosen',
            'nidn': 'NIDN001',
            'jenis_kelamin': 'L',
            'deleted': False
        }
        defaults.update(kwargs)
        return Dosen.objects.create(**defaults)

    @staticmethod
    def create_prodi(kode='TIF', **kwargs):
        """Create test prodi"""
        defaults = {
            'kode_program_studi': kode,
            'nama_program_studi': 'Teknik Informatika Test',
            'nama_jenjang_pendidikan': 'S1',
            'deleted': False
        }
        defaults.update(kwargs)
        return Prodi.objects.create(**defaults)

    @staticmethod
    def create_bulk_mahasiswa(count=10, prefix='TEST'):
        """Create multiple mahasiswa for bulk testing"""
        mahasiswa_list = []
        for i in range(1, count + 1):
            nim = f"{prefix}{i:03d}"
            mhs = TestDataFixtures.create_mahasiswa(
                nim=nim,
                nama=f"Student {i}",
                ipk=3.0 + (i * 0.05)
            )
            mahasiswa_list.append(mhs)
        return mahasiswa_list
```

### **3.2 Using Fixtures in Tests**

```python
# apps/academic/tests/test_with_fixtures.py
from django.test import TestCase
from apps.academic.tests.fixtures import TestDataFixtures


class MahasiswaWithFixturesTest(TestCase):
    """Test using reusable fixtures"""

    def setUp(self):
        """Create test data using fixtures"""
        # Single mahasiswa
        self.mahasiswa = TestDataFixtures.create_mahasiswa(
            nim='TEST001',
            nama='John Doe',
            ipk=3.8
        )

        # Bulk mahasiswa
        self.mahasiswa_list = TestDataFixtures.create_bulk_mahasiswa(
            count=5,
            prefix='BULK'
        )

        print(f"✓ Created 1 + {len(self.mahasiswa_list)} test mahasiswa")

    def test_single_mahasiswa(self):
        """Test single mahasiswa creation"""
        self.assertEqual(self.mahasiswa.nim, 'TEST001')
        self.assertEqual(self.mahasiswa.ipk, 3.8)

    def test_bulk_mahasiswa(self):
        """Test bulk mahasiswa creation"""
        self.assertEqual(len(self.mahasiswa_list), 5)

        # Check NIMs
        nims = [m.nim for m in self.mahasiswa_list]
        self.assertIn('BULK001', nims)
        self.assertIn('BULK005', nims)

    def test_mahasiswa_query(self):
        """Test querying mahasiswa"""
        from apps.feeder.models.mahasiswa import RiwayatPendidikan

        # Should find all 6 mahasiswa (1 single + 5 bulk)
        all_mhs = RiwayatPendidikan.objects.filter(nim__startswith='TEST')
        self.assertEqual(all_mhs.count(), 6)
```

---

## 4. API Testing

### **4.1 Test REST API Endpoints**

```python
# apps/academic/tests/test_api.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.academic.tests.fixtures import TestDataFixtures
from apps.users.models import User


class MahasiswaAPITest(TestCase):
    """Test Mahasiswa API endpoints"""

    def setUp(self):
        """Setup for each test"""
        # Create API client
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

        # Create test data
        self.mahasiswa = TestDataFixtures.create_mahasiswa(
            nim='TEST001',
            nama='Test Student'
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

        print("✓ API test setup complete")

    def test_get_mahasiswa_list(self):
        """Test: GET /api/v1/mahasiswa/"""
        url = reverse('mahasiswa-list')  # assuming you have this URL name
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        print(f"✓ GET mahasiswa list: {response.status_code}")

    def test_get_mahasiswa_detail(self):
        """Test: GET /api/v1/mahasiswa/{nim}/"""
        url = reverse('mahasiswa-detail', kwargs={'nim': 'TEST001'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nim'], 'TEST001')
        print(f"✓ GET mahasiswa detail: {response.status_code}")

    def test_create_mahasiswa(self):
        """Test: POST /api/v1/mahasiswa/"""
        url = reverse('mahasiswa-list')
        data = {
            'nim': 'TEST002',
            'nama_mahasiswa': 'New Student',
            'jenis_kelamin': 'P',
            'tanggal_lahir': '2001-01-01',
            'ipk': 3.7
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nim'], 'TEST002')

        # Verify in database
        from apps.feeder.models.mahasiswa import RiwayatPendidikan
        exists = RiwayatPendidikan.objects.filter(nim='TEST002').exists()
        self.assertTrue(exists)

        print(f"✓ POST create mahasiswa: {response.status_code}")

    def test_update_mahasiswa(self):
        """Test: PUT /api/v1/mahasiswa/{nim}/"""
        url = reverse('mahasiswa-detail', kwargs={'nim': 'TEST001'})
        data = {
            'ipk': 3.9
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify update
        self.mahasiswa.refresh_from_db()
        self.assertEqual(self.mahasiswa.ipk, 3.9)

        print(f"✓ PATCH update mahasiswa: {response.status_code}")

    def test_delete_mahasiswa(self):
        """Test: DELETE /api/v1/mahasiswa/{nim}/"""
        url = reverse('mahasiswa-detail', kwargs={'nim': 'TEST001'})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft delete
        self.mahasiswa.refresh_from_db()
        self.assertTrue(self.mahasiswa.deleted)

        print(f"✓ DELETE mahasiswa: {response.status_code}")

    def test_unauthorized_access(self):
        """Test: Unauthorized access should fail"""
        # Logout
        self.client.force_authenticate(user=None)

        url = reverse('mahasiswa-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print(f"✓ Unauthorized access blocked: {response.status_code}")
```

---

## 5. Graph Database Testing

### **5.1 Test Neo4j Integration**

```python
# apps/academic/tests/test_graph_service.py
from django.test import TestCase, skipIf
from apps.academic.tests.fixtures import TestDataFixtures
from apps.academic.services.graph_service import AcademicGraphService
from apps.academic.graph_sync import GraphSyncManager
import os


# Skip if Neo4j not available
NEO4J_AVAILABLE = os.getenv('NEO4J_URI') is not None


@skipIf(not NEO4J_AVAILABLE, "Neo4j not configured")
class GraphServiceTest(TestCase):
    """Test Graph Database features"""

    @classmethod
    def setUpClass(cls):
        """Setup once for all tests"""
        super().setUpClass()
        cls.graph_manager = GraphSyncManager()

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        super().tearDownClass()
        # Clear Neo4j test data
        cls.graph_manager.clear_all_data()
        cls.graph_manager.close()

    def setUp(self):
        """Setup for each test"""
        # Create test mahasiswa
        self.mahasiswa1 = TestDataFixtures.create_mahasiswa(
            nim='GRAPH001',
            nama='Graph Student 1'
        )
        self.mahasiswa2 = TestDataFixtures.create_mahasiswa(
            nim='GRAPH002',
            nama='Graph Student 2'
        )

        # Sync to Neo4j
        self.graph_manager.sync_mahasiswa_node(self.mahasiswa1)
        self.graph_manager.sync_mahasiswa_node(self.mahasiswa2)

        print("✓ Graph test data synced")

    def test_get_classmates(self):
        """Test: Get classmates query"""
        classmates = AcademicGraphService.get_classmates('GRAPH001')

        self.assertIsInstance(classmates, list)
        print(f"✓ Found {len(classmates)} classmates")

    def test_recommend_courses(self):
        """Test: Course recommendation"""
        recommendations = AcademicGraphService.recommend_courses('GRAPH001')

        self.assertIsInstance(recommendations, list)
        print(f"✓ Got {len(recommendations)} recommendations")

    def test_sync_mahasiswa(self):
        """Test: Sync mahasiswa to Neo4j"""
        from apps.academic.graph_models import MahasiswaNode

        # Check if synced
        try:
            node = MahasiswaNode.nodes.get(nim='GRAPH001')
            self.assertEqual(node.nim, 'GRAPH001')
            print(f"✓ Mahasiswa synced to Neo4j: {node.nim}")
        except MahasiswaNode.DoesNotExist:
            self.fail("Mahasiswa not found in Neo4j")
```

---

## 6. Advanced Testing Patterns

### **6.1 Test with Multiple Databases**

```python
# apps/academic/tests/test_multi_db.py
from django.test import TestCase
from apps.academic.tests.fixtures import TestDataFixtures


class MultiDatabaseTest(TestCase):
    """Test with multiple database connections"""

    databases = ['default', 'secondary']  # if you have multiple DBs

    def test_data_in_multiple_dbs(self):
        """Test data across multiple databases"""
        # Create in default DB
        mhs = TestDataFixtures.create_mahasiswa(nim='MULTI001')
        self.assertEqual(mhs.nim, 'MULTI001')

        # Query from different DB connection (if configured)
        # ...
```

### **6.2 Test with Transactions**

```python
from django.test import TransactionTestCase


class TransactionTest(TransactionTestCase):
    """
    Use TransactionTestCase when you need to test:
    - Transactions
    - Multiple database connections
    - Threading
    """

    def test_transaction_rollback(self):
        """Test transaction rollback behavior"""
        from django.db import transaction

        try:
            with transaction.atomic():
                mhs = TestDataFixtures.create_mahasiswa(nim='TRANS001')
                # Force error to rollback
                raise Exception("Rollback!")
        except Exception:
            pass

        # Should not exist (rolled back)
        from apps.feeder.models.mahasiswa import RiwayatPendidikan
        exists = RiwayatPendidikan.objects.filter(nim='TRANS001').exists()
        self.assertFalse(exists)
```

### **6.3 Test with Mock Data**

```python
# apps/academic/tests/test_with_mocks.py
from django.test import TestCase
from unittest.mock import patch, MagicMock


class MockTest(TestCase):
    """Test with mocked external services"""

    @patch('apps.academic.services.external_api.fetch_data')
    def test_with_mocked_api(self, mock_fetch):
        """Test with mocked external API"""
        # Setup mock
        mock_fetch.return_value = {
            'status': 'success',
            'data': {'nim': 'MOCK001'}
        }

        # Test your code
        from apps.academic.services.external_api import get_student_data
        result = get_student_data('MOCK001')

        # Assertions
        self.assertEqual(result['nim'], 'MOCK001')
        mock_fetch.assert_called_once_with('MOCK001')
```

---

## 7. Test Coverage

### **7.1 Run with Coverage**

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='apps' manage.py test

# Generate report
coverage report

# Generate HTML report
coverage html

# View report
open htmlcov/index.html
```

**Output:**
```
Name                                       Stmts   Miss  Cover
--------------------------------------------------------------
apps/academic/__init__.py                      0      0   100%
apps/academic/models.py                      150     10    93%
apps/academic/views.py                       200     30    85%
apps/academic/services/graph_service.py      180     25    86%
--------------------------------------------------------------
TOTAL                                       1500    150    90%
```

### **7.2 Coverage Configuration**

```ini
# .coveragerc
[run]
source = apps
omit =
    */tests/*
    */migrations/*
    */admin.py
    */apps.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## 8. Test Organization

### **8.1 Directory Structure**

```
apps/academic/
├── tests/
│   ├── __init__.py
│   ├── fixtures.py              # Reusable test data
│   ├── test_models.py           # Model tests
│   ├── test_views.py            # View tests
│   ├── test_api.py              # API tests
│   ├── test_services.py         # Service layer tests
│   ├── test_graph_service.py    # Graph DB tests
│   ├── test_sync_manager.py     # Sync tests
│   └── test_integration.py      # Integration tests
```

### **8.2 Test Naming Convention**

```python
class TestClassName(TestCase):
    """Test [What is being tested]"""

    def test_feature_behavior(self):
        """Test: [Expected behavior]"""
        pass

    def test_feature_edge_case(self):
        """Test: [Edge case scenario]"""
        pass

    def test_feature_failure(self):
        """Test: [Failure scenario]"""
        pass
```

---

## 9. Running Tests

### **9.1 Basic Commands**

```bash
# Run all tests
python manage.py test

# Run specific app
python manage.py test apps.academic

# Run specific test file
python manage.py test apps.academic.tests.test_models

# Run specific test class
python manage.py test apps.academic.tests.test_models.MahasiswaModelTest

# Run specific test method
python manage.py test apps.academic.tests.test_models.MahasiswaModelTest.test_mahasiswa_creation

# Run with verbosity
python manage.py test --verbosity=2

# Run parallel (faster)
python manage.py test --parallel=4

# Keep test database (for debugging)
python manage.py test --keepdb
```

### **9.2 Pytest Alternative**

```bash
# Install pytest-django
pip install pytest pytest-django

# Create pytest.ini
cat > pytest.ini <<EOF
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
EOF

# Run with pytest (better output)
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test
pytest apps/academic/tests/test_models.py::MahasiswaModelTest::test_mahasiswa_creation
```

---

## 10. Best Practices

### ✅ **DO:**

1. **Use setUp and tearDown**
   ```python
   def setUp(self):
       """Create test data before each test"""
       self.data = create_test_data()
   ```

2. **Use fixtures for reusability**
   ```python
   from .fixtures import TestDataFixtures
   self.mhs = TestDataFixtures.create_mahasiswa()
   ```

3. **Test one thing per test method**
   ```python
   def test_creation(self): # Good - tests only creation
   def test_all_features(self): # Bad - too broad
   ```

4. **Use descriptive test names**
   ```python
   def test_mahasiswa_with_valid_ipk_should_save()  # Good
   def test_1()  # Bad
   ```

5. **Assert meaningfully**
   ```python
   self.assertEqual(result, expected, "IPK should be 3.5")
   ```

6. **Clean up external resources**
   ```python
   def tearDown(self):
       self.api_client.close()
       self.cache.clear()
   ```

### ❌ **DON'T:**

1. **Don't rely on test order**
   ```python
   # Bad - tests should be independent
   def test_1_create(self):
       self.id = create()
   def test_2_update(self):
       update(self.id)  # Depends on test_1
   ```

2. **Don't use production database**
   ```python
   # Django handles this automatically
   # But make sure your settings are correct
   ```

3. **Don't test Django's functionality**
   ```python
   # Bad - testing Django's ORM
   def test_objects_filter_works(self):
       objects = Model.objects.filter(id=1)
       self.assertIsNotNone(objects)
   ```

4. **Don't ignore test failures**
   ```python
   # Fix or skip explicitly
   @skip("Known issue #123")
   def test_broken_feature(self):
       pass
   ```

---

## 11. Debugging Tests

### **11.1 Print Debugging**

```python
def test_something(self):
    print(f"✓ Created: {self.data}")
    print(f"✓ Query result: {result}")
    self.assertEqual(result, expected)
```

### **11.2 Interactive Debugging**

```python
def test_something(self):
    import pdb; pdb.set_trace()  # Breakpoint
    result = do_something()
    self.assertEqual(result, expected)
```

### **11.3 Verbose Output**

```bash
python manage.py test --verbosity=2
python manage.py test --debug-mode
```

---

## 12. CI/CD Integration

### **12.1 GitHub Actions Example**

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        python manage.py test --verbosity=2

    - name: Generate coverage
      run: |
        coverage run manage.py test
        coverage report
```

---

## Summary

**Django Testing Key Points:**

1. ✅ Test database otomatis dibuat dan dihapus
2. ✅ Data dummy dibuat di `setUp()`, otomatis di-clean di `tearDown()`
3. ✅ Setiap test method isolated (tidak saling mempengaruhi)
4. ✅ Use fixtures untuk reusable test data
5. ✅ Test API dengan `APIClient`
6. ✅ Test dengan mock untuk external dependencies
7. ✅ Run coverage untuk track test completeness
8. ✅ Organize tests dalam structure yang jelas

**Test automatically cleans up! No manual deletion needed.** 🧹✨
