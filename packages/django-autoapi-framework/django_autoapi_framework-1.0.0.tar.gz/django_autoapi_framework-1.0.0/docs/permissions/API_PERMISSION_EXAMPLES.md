# 🔗 **Contoh Implementasi Permission di API**

Panduan praktis menggunakan sistem permission di API endpoints dengan berbagai skenario.

## 📋 **Table of Contents**

1. [Basic API Permission](#basic-api-permission)
2. [Role-based API Access](#role-based-api-access)
3. [Object-level Permission](#object-level-permission)
4. [Dynamic Permission Checking](#dynamic-permission-checking)
5. [Permission untuk Data Export](#permission-untuk-data-export)
6. [Bulk Operations Permission](#bulk-operations-permission)
7. [Real-world API Examples](#real-world-api-examples)

## 🚀 **Basic API Permission**

### **1. Simple Permission Check**
```python
# api/v1/academic/dosen/views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from core.decorators.permission_decorators import require_academic_role

class DosenViewSet(ModelViewSet):
    queryset = Dosen.objects.all()
    serializer_class = DosenSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Dynamic permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Write operations require admin level
            permission_classes = [AdminFakultasPermission]
        elif self.action in ['list', 'retrieve']:
            # Read operations for dosen and above
            permission_classes = [DosenPermission]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter data based on user access"""
        return Dosen.objects.accessible_by_user(self.request.user)
```

### **2. Function-based API with Permission**
```python
# api/v1/academic/dosen/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dosen_list(request):
    """Get dosen list filtered by user access"""

    # Check role
    if not check_user_academic_role(request.user, ['dosen', 'kaprodi', 'admin_fakultas']):
        return Response({'error': 'Akses ditolak'}, status=403)

    # Get filtered queryset
    dosen_qs = Dosen.objects.accessible_by_user(request.user)

    # Apply additional filters
    search = request.GET.get('search')
    if search:
        dosen_qs = dosen_qs.filter(nama_dosen__icontains=search)

    # Serialize data
    serializer = DosenSerializer(dosen_qs, many=True)

    return Response({
        'results': serializer.data,
        'count': dosen_qs.count(),
        'user_role': get_profile_role(request.user)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_dosen(request):
    """Create new dosen - admin only"""

    if not check_user_academic_role(request.user, ['admin_fakultas', 'superuser']):
        return Response({'error': 'Hanya admin yang dapat menambah dosen'}, status=403)

    serializer = DosenSerializer(data=request.data)
    if serializer.is_valid():
        # Check prodi access if specified
        prodi_id = serializer.validated_data.get('id_prodi')
        if prodi_id and not check_prodi_access(request.user, prodi_id):
            return Response({'error': 'Tidak punya akses ke prodi ini'}, status=403)

        dosen = serializer.save()
        return Response(DosenSerializer(dosen).data, status=201)

    return Response(serializer.errors, status=400)
```

## 🎯 **Role-based API Access**

### **1. Endpoint Berbeda untuk Role Berbeda**
```python
# api/v1/dashboard/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """Dashboard data sesuai role user"""

    profile = get_user_profile(request.user)
    if not profile:
        return Response({'error': 'Profile tidak ditemukan'}, status=404)

    role = profile.academic_role

    if role == 'mahasiswa':
        return get_mahasiswa_dashboard(request, profile)
    elif role == 'dosen':
        return get_dosen_dashboard(request, profile)
    elif role == 'kaprodi':
        return get_kaprodi_dashboard(request, profile)
    elif role in ['admin_fakultas', 'dekan']:
        return get_admin_dashboard(request, profile)
    else:
        return get_guest_dashboard(request, profile)

def get_mahasiswa_dashboard(request, profile):
    """Dashboard data untuk mahasiswa"""
    try:
        # Get mahasiswa data
        mahasiswa = RiwayatPendidikan.objects.get(nim=request.user.username)

        # Get current semester data
        current_krs = KRS.objects.filter(
            id_registrasi_mahasiswa=mahasiswa,
            id_semester=get_current_semester()
        ).first()

        # Get recent grades
        recent_grades = Nilai.objects.filter(
            id_registrasi_mahasiswa=mahasiswa
        ).order_by('-created_at')[:5]

        return Response({
            'role': 'mahasiswa',
            'mahasiswa_info': {
                'nim': mahasiswa.nim,
                'nama': mahasiswa.nama_mahasiswa,
                'prodi': mahasiswa.id_prodi.nama_program_studi if mahasiswa.id_prodi else None,
            },
            'current_krs': KRSSerializer(current_krs).data if current_krs else None,
            'recent_grades': NilaiSerializer(recent_grades, many=True).data,
            'notifications': get_mahasiswa_notifications(mahasiswa)
        })

    except RiwayatPendidikan.DoesNotExist:
        return Response({'error': 'Data mahasiswa tidak ditemukan'}, status=404)

def get_dosen_dashboard(request, profile):
    """Dashboard data untuk dosen"""
    if not profile.id_dosen:
        return Response({'error': 'Data dosen tidak ditemukan'}, status=404)

    # Get teaching classes
    current_semester = get_current_semester()
    teaching_classes = Kelas.objects.filter(
        pengajar__id_dosen=profile.id_dosen,
        id_semester=current_semester
    )

    # Get pending grading tasks
    pending_grades = get_pending_grades_for_dosen(profile.id_dosen)

    # Get recent activities
    recent_activities = get_dosen_recent_activities(profile.id_dosen)

    return Response({
        'role': 'dosen',
        'dosen_info': {
            'nip': profile.id_dosen.nip,
            'nama': profile.id_dosen.nama_dosen,
            'nidn': profile.id_dosen.nidn,
        },
        'teaching_classes': KelasSerializer(teaching_classes, many=True).data,
        'pending_grades_count': pending_grades.count(),
        'recent_activities': recent_activities,
        'schedule_today': get_dosen_schedule_today(profile.id_dosen)
    })

def get_kaprodi_dashboard(request, profile):
    """Dashboard data untuk kaprodi"""
    if not profile.id_prodi:
        return Response({'error': 'Data prodi tidak ditemukan'}, status=404)

    # Statistics for prodi
    prodi_stats = {
        'total_mahasiswa': RiwayatPendidikan.objects.filter(
            id_prodi=profile.id_prodi,
            id_jenis_keluar__isnull=True
        ).count(),
        'total_dosen': Dosen.objects.filter(
            penugasan__id_prodi=profile.id_prodi
        ).distinct().count(),
        'total_matkul': MatkulKurikulum.objects.filter(
            id_kurikulum__id_prodi=profile.id_prodi
        ).count(),
    }

    # Pending approvals
    pending_approvals = get_pending_approvals_for_kaprodi(profile.id_prodi)

    return Response({
        'role': 'kaprodi',
        'prodi_info': {
            'id_prodi': profile.id_prodi.id_prodi,
            'nama_prodi': profile.id_prodi.nama_program_studi,
            'kode_prodi': profile.id_prodi.kode_program_studi,
        },
        'statistics': prodi_stats,
        'pending_approvals': pending_approvals,
        'recent_reports': get_prodi_recent_reports(profile.id_prodi)
    })
```

### **2. Multi-role Endpoint Access**
```python
# api/v1/academic/nilai/views.py
class NilaiViewSet(ModelViewSet):
    queryset = Nilai.objects.all()
    serializer_class = NilaiSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter nilai based on user role"""
        user = self.request.user
        profile = get_user_profile(user)

        if not profile:
            return self.queryset.none()

        role = profile.academic_role

        if role == 'mahasiswa':
            # Mahasiswa hanya lihat nilai sendiri
            try:
                mahasiswa = RiwayatPendidikan.objects.get(nim=user.username)
                return self.queryset.filter(id_registrasi_mahasiswa=mahasiswa)
            except RiwayatPendidikan.DoesNotExist:
                return self.queryset.none()

        elif role == 'dosen':
            # Dosen lihat nilai dari kelas yang diajar
            if profile.id_dosen:
                teaching_classes = Kelas.objects.filter(
                    pengajar__id_dosen=profile.id_dosen
                )
                return self.queryset.filter(id_kelas_kuliah__in=teaching_classes)
            return self.queryset.none()

        elif role == 'kaprodi':
            # Kaprodi lihat nilai di prodi
            if profile.id_prodi:
                return self.queryset.filter(
                    id_kelas_kuliah__id_prodi=profile.id_prodi
                )
            return self.queryset.none()

        elif role in ['admin_fakultas', 'dekan']:
            # Admin fakultas lihat semua di fakultas
            if profile.id_fakultas:
                return self.queryset.filter(
                    id_kelas_kuliah__id_prodi__id_fakultas=profile.id_fakultas
                )
            return self.queryset.all()

        elif user.is_superuser:
            return self.queryset.all()

        return self.queryset.none()

    @action(detail=False, methods=['post'])
    def input_nilai_bulk(self, request):
        """Bulk input nilai - hanya dosen"""
        if not check_user_academic_role(request.user, ['dosen', 'kaprodi']):
            return Response({'error': 'Hanya dosen yang dapat input nilai'}, status=403)

        kelas_id = request.data.get('kelas_id')
        nilai_data = request.data.get('nilai_list', [])

        # Validate kelas access
        profile = get_user_profile(request.user)
        if profile.academic_role == 'dosen':
            if not Kelas.objects.filter(
                id=kelas_id,
                pengajar__id_dosen=profile.id_dosen
            ).exists():
                return Response({'error': 'Anda tidak mengajar di kelas ini'}, status=403)

        # Process bulk input
        results = []
        for item in nilai_data:
            # Validate and save each nilai
            serializer = NilaiInputSerializer(data=item)
            if serializer.is_valid():
                nilai = serializer.save(
                    id_kelas_kuliah_id=kelas_id,
                    created_by=request.user
                )
                results.append({'id': nilai.id, 'status': 'success'})
            else:
                results.append({'errors': serializer.errors, 'status': 'error'})

        return Response({
            'results': results,
            'total': len(nilai_data),
            'success_count': len([r for r in results if r['status'] == 'success'])
        })
```

## 🔒 **Object-level Permission**

### **1. Detailed Object Access Control**
```python
# api/v1/academic/kelas/views.py
class KelasViewSet(ModelViewSet):
    queryset = Kelas.objects.all()
    serializer_class = KelasSerializer
    permission_classes = [IsAuthenticated]

    def check_object_permissions(self, request, obj):
        """Custom object-level permission check"""
        super().check_object_permissions(request, obj)

        user = request.user
        if user.is_superuser:
            return

        profile = get_user_profile(user)
        if not profile:
            self.permission_denied(request, 'Profile tidak ditemukan')

        role = profile.academic_role

        # Check access based on role and object
        if role == 'mahasiswa':
            # Mahasiswa hanya akses kelas yang diikuti
            try:
                mahasiswa = RiwayatPendidikan.objects.get(nim=user.username)
                if not KRS.objects.filter(
                    id_registrasi_mahasiswa=mahasiswa,
                    id_kelas_kuliah=obj
                ).exists():
                    self.permission_denied(request, 'Anda tidak terdaftar di kelas ini')
            except RiwayatPendidikan.DoesNotExist:
                self.permission_denied(request, 'Data mahasiswa tidak ditemukan')

        elif role == 'dosen':
            # Dosen hanya akses kelas yang diajar
            if profile.id_dosen and not obj.pengajar.filter(
                id_dosen=profile.id_dosen
            ).exists():
                self.permission_denied(request, 'Anda tidak mengajar di kelas ini')

        elif role == 'kaprodi':
            # Kaprodi akses kelas di prodi
            if profile.id_prodi and obj.id_prodi != profile.id_prodi:
                self.permission_denied(request, 'Kelas tidak berada di prodi Anda')

        elif role in ['admin_fakultas', 'dekan']:
            # Admin fakultas akses kelas di fakultas
            if profile.id_fakultas and obj.id_prodi.id_fakultas != profile.id_fakultas:
                self.permission_denied(request, 'Kelas tidak berada di fakultas Anda')

    @action(detail=True, methods=['get'])
    def peserta(self, request, pk=None):
        """Get peserta kelas with permission check"""
        kelas = self.get_object()  # This will trigger object permission check

        # Get peserta list
        peserta = KRS.objects.filter(id_kelas_kuliah=kelas).select_related(
            'id_registrasi_mahasiswa'
        )

        # Serialize based on role
        user_role = get_profile_role(request.user)
        if user_role == 'mahasiswa':
            # Mahasiswa hanya lihat diri sendiri dalam list
            mahasiswa = RiwayatPendidikan.objects.get(nim=request.user.username)
            peserta = peserta.filter(id_registrasi_mahasiswa=mahasiswa)

        serializer = KRSSerializer(peserta, many=True)
        return Response({
            'peserta': serializer.data,
            'total': peserta.count(),
            'kelas_info': KelasSerializer(kelas).data
        })

    @action(detail=True, methods=['post'])
    def input_presensi(self, request, pk=None):
        """Input presensi - hanya dosen pengajar"""
        kelas = self.get_object()

        # Additional check for dosen
        profile = get_user_profile(request.user)
        if profile.academic_role == 'dosen':
            if not kelas.pengajar.filter(id_dosen=profile.id_dosen).exists():
                return Response({'error': 'Anda tidak mengajar di kelas ini'}, status=403)
        elif not check_user_academic_role(request.user, ['kaprodi', 'admin_fakultas']):
            return Response({'error': 'Hanya dosen pengajar yang dapat input presensi'}, status=403)

        # Process presensi data
        presensi_data = request.data.get('presensi_list', [])
        tanggal = request.data.get('tanggal')

        if not tanggal:
            return Response({'error': 'Tanggal pertemuan harus diisi'}, status=400)

        # Create pertemuan record
        pertemuan = Pertemuan.objects.create(
            id_kelas_kuliah=kelas,
            tanggal=tanggal,
            created_by=request.user
        )

        # Process each presensi
        results = []
        for item in presensi_data:
            mahasiswa_id = item.get('mahasiswa_id')
            status = item.get('status', '0')  # Default hadir

            try:
                mahasiswa = RiwayatPendidikan.objects.get(id=mahasiswa_id)

                # Check if mahasiswa in this class
                if not KRS.objects.filter(
                    id_registrasi_mahasiswa=mahasiswa,
                    id_kelas_kuliah=kelas
                ).exists():
                    results.append({
                        'mahasiswa_id': mahasiswa_id,
                        'status': 'error',
                        'message': 'Mahasiswa tidak terdaftar di kelas ini'
                    })
                    continue

                # Create or update presensi
                presensi, created = PertemuanMahasiswa.objects.get_or_create(
                    id_pertemuan=pertemuan,
                    id_mahasiswa=mahasiswa,
                    defaults={'status_kehadiran': status}
                )

                if not created:
                    presensi.status_kehadiran = status
                    presensi.save()

                results.append({
                    'mahasiswa_id': mahasiswa_id,
                    'status': 'success',
                    'presensi_id': presensi.id
                })

            except RiwayatPendidikan.DoesNotExist:
                results.append({
                    'mahasiswa_id': mahasiswa_id,
                    'status': 'error',
                    'message': 'Mahasiswa tidak ditemukan'
                })

        return Response({
            'pertemuan_id': pertemuan.id,
            'results': results,
            'summary': {
                'total': len(presensi_data),
                'success': len([r for r in results if r['status'] == 'success']),
                'error': len([r for r in results if r['status'] == 'error'])
            }
        })
```

### **2. Conditional Field Access**
```python
# serializers.py with conditional fields
class MahasiswaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiwayatPendidikan
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        user = self.context['request'].user
        profile = get_user_profile(user)

        if not profile:
            return {}

        role = profile.academic_role

        # Remove sensitive fields based on role
        if role == 'mahasiswa':
            # Mahasiswa hanya lihat data diri sendiri dan hanya field tertentu
            if instance.nim != user.username:
                return {}  # Can't view other student's data

            # Remove administrative fields
            sensitive_fields = ['created_at', 'updated_at', 'sync', 'status']
            for field in sensitive_fields:
                data.pop(field, None)

        elif role == 'dosen':
            # Dosen lihat mahasiswa di kelas yang diajar, tapi field terbatas
            teaching_classes = get_dosen_teaching_classes(profile.id_dosen)
            mahasiswa_in_classes = KRS.objects.filter(
                id_kelas_kuliah__in=teaching_classes,
                id_registrasi_mahasiswa=instance
            ).exists()

            if not mahasiswa_in_classes:
                return {}

            # Limit fields for dosen
            allowed_fields = ['nim', 'nama_mahasiswa', 'id_prodi', 'angkatan']
            data = {k: v for k, v in data.items() if k in allowed_fields}

        elif role in ['kaprodi']:
            # Kaprodi lihat mahasiswa di prodi
            if instance.id_prodi != profile.id_prodi:
                return {}

        elif role in ['admin_fakultas', 'dekan']:
            # Admin fakultas lihat mahasiswa di fakultas
            if instance.id_prodi.id_fakultas != profile.id_fakultas:
                return {}

        return data

# Usage in ViewSet
class MahasiswaViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MahasiswaDetailSerializer
        elif self.action == 'list':
            return MahasiswaListSerializer
        return MahasiswaSerializer
```

## ⚡ **Dynamic Permission Checking**

### **1. Runtime Permission Evaluation**
```python
# api/v1/academic/utils/dynamic_permissions.py
class DynamicPermissionChecker:
    """Dynamic permission checker for complex scenarios"""

    def __init__(self, user):
        self.user = user
        self.profile = get_user_profile(user)

    def can_access_mahasiswa_data(self, mahasiswa_instance, access_type='view'):
        """Check if user can access specific mahasiswa data"""
        if self.user.is_superuser:
            return True

        if not self.profile:
            return False

        role = self.profile.academic_role

        if role == 'mahasiswa':
            # Only own data
            return mahasiswa_instance.nim == self.user.username

        elif role == 'dosen':
            # Students in taught classes
            if access_type == 'view':
                return self._mahasiswa_in_taught_classes(mahasiswa_instance)
            elif access_type == 'grade':
                return self._can_grade_mahasiswa(mahasiswa_instance)
            return False

        elif role == 'kaprodi':
            # Students in same prodi
            return mahasiswa_instance.id_prodi == self.profile.id_prodi

        elif role in ['admin_fakultas', 'dekan']:
            # Students in same fakultas
            return mahasiswa_instance.id_prodi.id_fakultas == self.profile.id_fakultas

        return False

    def can_modify_kelas_data(self, kelas_instance, modification_type):
        """Check if user can modify kelas data"""
        if self.user.is_superuser:
            return True

        if not self.profile:
            return False

        role = self.profile.academic_role

        if modification_type == 'schedule':
            # Only kaprodi and admin can modify schedule
            if role in ['kaprodi', 'admin_fakultas']:
                return self._has_prodi_access(kelas_instance.id_prodi)
            return False

        elif modification_type == 'attendance':
            # Dosen can input attendance for their classes
            if role == 'dosen':
                return kelas_instance.pengajar.filter(id_dosen=self.profile.id_dosen).exists()
            elif role in ['kaprodi', 'admin_fakultas']:
                return self._has_prodi_access(kelas_instance.id_prodi)
            return False

        elif modification_type == 'grades':
            # Similar to attendance
            return self.can_modify_kelas_data(kelas_instance, 'attendance')

        return False

    def get_accessible_prodi_for_reports(self):
        """Get prodi list accessible for reporting"""
        if self.user.is_superuser:
            return ProgramStudi.objects.all()

        if not self.profile:
            return ProgramStudi.objects.none()

        role = self.profile.academic_role

        if role in ['kaprodi']:
            return ProgramStudi.objects.filter(id_prodi=self.profile.id_prodi.id_prodi)
        elif role in ['admin_fakultas', 'dekan']:
            return ProgramStudi.objects.filter(id_fakultas=self.profile.id_fakultas)
        elif role == 'dosen':
            # Prodi where dosen teaches
            return ProgramStudi.objects.filter(
                kelas__pengajar__id_dosen=self.profile.id_dosen
            ).distinct()

        return ProgramStudi.objects.none()

    def _mahasiswa_in_taught_classes(self, mahasiswa_instance):
        """Check if mahasiswa is in dosen's taught classes"""
        if not self.profile.id_dosen:
            return False

        return KRS.objects.filter(
            id_registrasi_mahasiswa=mahasiswa_instance,
            id_kelas_kuliah__pengajar__id_dosen=self.profile.id_dosen
        ).exists()

    def _can_grade_mahasiswa(self, mahasiswa_instance):
        """Check if dosen can grade this mahasiswa"""
        # Additional check: only in current semester
        current_semester = get_current_semester()
        return KRS.objects.filter(
            id_registrasi_mahasiswa=mahasiswa_instance,
            id_kelas_kuliah__pengajar__id_dosen=self.profile.id_dosen,
            id_kelas_kuliah__id_semester=current_semester
        ).exists()

    def _has_prodi_access(self, prodi_instance):
        """Check if user has access to prodi"""
        role = self.profile.academic_role

        if role == 'kaprodi':
            return prodi_instance == self.profile.id_prodi
        elif role in ['admin_fakultas', 'dekan']:
            return prodi_instance.id_fakultas == self.profile.id_fakultas

        return False

# Usage in API views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mahasiswa_grades(request, mahasiswa_id):
    """Get grades for specific mahasiswa with dynamic permission"""
    try:
        mahasiswa = RiwayatPendidikan.objects.get(id=mahasiswa_id)
    except RiwayatPendidikan.DoesNotExist:
        return Response({'error': 'Mahasiswa tidak ditemukan'}, status=404)

    # Dynamic permission check
    permission_checker = DynamicPermissionChecker(request.user)
    if not permission_checker.can_access_mahasiswa_data(mahasiswa, 'view'):
        return Response({'error': 'Akses ditolak'}, status=403)

    # Get grades based on access level
    grades_qs = Nilai.objects.filter(id_registrasi_mahasiswa=mahasiswa)

    # Further filter based on role
    if permission_checker.profile.academic_role == 'dosen':
        # Dosen only see grades from their classes
        taught_classes = Kelas.objects.filter(
            pengajar__id_dosen=permission_checker.profile.id_dosen
        )
        grades_qs = grades_qs.filter(id_kelas_kuliah__in=taught_classes)

    serializer = NilaiSerializer(grades_qs, many=True)
    return Response({
        'mahasiswa': MahasiswaSerializer(mahasiswa).data,
        'grades': serializer.data,
        'access_level': permission_checker.profile.academic_role
    })
```

## 📊 **Permission untuk Data Export**

### **1. Export dengan Permission Filter**
```python
# api/v1/reports/views.py
import csv
from django.http import HttpResponse
from django.utils import timezone

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_dosen_data(request):
    """Export dosen data with permission filtering"""

    # Check export permission
    if not check_user_academic_role(request.user, ['kaprodi', 'admin_fakultas', 'superuser']):
        return Response({'error': 'Tidak memiliki akses untuk export data'}, status=403)

    # Get filtered data
    dosen_qs = Dosen.objects.accessible_by_user(request.user)

    # Apply additional filters from query params
    prodi_filter = request.GET.get('prodi')
    if prodi_filter:
        if not check_prodi_access(request.user, prodi_filter):
            return Response({'error': 'Tidak memiliki akses ke prodi tersebut'}, status=403)
        dosen_qs = dosen_qs.filter(penugasan__id_prodi__id_prodi=prodi_filter)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dosen_export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)

    # Header based on user access level
    profile = get_user_profile(request.user)
    if profile.academic_role in ['admin_fakultas', 'superuser']:
        headers = ['NIP', 'NIDN', 'Nama', 'Email', 'Prodi', 'Fakultas', 'Status', 'Jabatan Fungsional']
    else:
        headers = ['NIP', 'NIDN', 'Nama', 'Prodi']  # Limited for kaprodi

    writer.writerow(headers)

    # Write data
    for dosen in dosen_qs:
        if profile.academic_role in ['admin_fakultas', 'superuser']:
            row = [
                dosen.nip,
                dosen.nidn,
                dosen.nama_dosen,
                dosen.email,
                dosen.get_primary_prodi(),
                dosen.get_primary_fakultas(),
                dosen.status,
                dosen.id_jabatan_fungsional.nama_jabatan_fungsional if dosen.id_jabatan_fungsional else ''
            ]
        else:
            row = [
                dosen.nip,
                dosen.nidn,
                dosen.nama_dosen,
                dosen.get_primary_prodi()
            ]
        writer.writerow(row)

    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_report(request):
    """Generate custom report with permission validation"""

    report_type = request.data.get('report_type')
    filters = request.data.get('filters', {})

    # Validate report access
    allowed_reports = get_allowed_reports_for_user(request.user)
    if report_type not in allowed_reports:
        return Response({'error': f'Tidak memiliki akses untuk report {report_type}'}, status=403)

    # Validate filters
    permission_checker = DynamicPermissionChecker(request.user)

    if 'prodi_ids' in filters:
        accessible_prodi = permission_checker.get_accessible_prodi_for_reports()
        requested_prodi = filters['prodi_ids']

        # Check if all requested prodi are accessible
        if not all(accessible_prodi.filter(id_prodi=pid).exists() for pid in requested_prodi):
            return Response({'error': 'Beberapa prodi tidak dapat diakses'}, status=403)

    # Generate report based on type
    if report_type == 'mahasiswa_summary':
        return generate_mahasiswa_summary_report(request, filters)
    elif report_type == 'dosen_workload':
        return generate_dosen_workload_report(request, filters)
    elif report_type == 'grade_analysis':
        return generate_grade_analysis_report(request, filters)
    else:
        return Response({'error': 'Report type tidak dikenal'}, status=400)

def get_allowed_reports_for_user(user):
    """Get list of reports user can access"""
    profile = get_user_profile(user)
    if not profile:
        return []

    role = profile.academic_role

    if role == 'mahasiswa':
        return ['personal_transcript']
    elif role == 'dosen':
        return ['teaching_schedule', 'class_roster', 'grade_input']
    elif role == 'kaprodi':
        return ['mahasiswa_summary', 'dosen_workload', 'grade_analysis', 'prodi_statistics']
    elif role in ['admin_fakultas', 'dekan']:
        return ['mahasiswa_summary', 'dosen_workload', 'grade_analysis', 'prodi_statistics', 'fakultas_overview']
    elif user.is_superuser:
        return ['all']  # Special marker for all reports

    return []
```

## 🔄 **Bulk Operations Permission**

### **1. Bulk Operations dengan Validation**
```python
# api/v1/academic/bulk/views.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_mahasiswa_status(request):
    """Bulk update mahasiswa status with individual permission check"""

    # Check bulk operation permission
    if not check_user_academic_role(request.user, ['admin_fakultas', 'kaprodi']):
        return Response({'error': 'Tidak memiliki akses untuk bulk update'}, status=403)

    mahasiswa_updates = request.data.get('updates', [])
    if not mahasiswa_updates:
        return Response({'error': 'Data update kosong'}, status=400)

    permission_checker = DynamicPermissionChecker(request.user)
    results = []

    for update_item in mahasiswa_updates:
        mahasiswa_id = update_item.get('mahasiswa_id')
        new_status = update_item.get('status')

        try:
            mahasiswa = RiwayatPendidikan.objects.get(id=mahasiswa_id)

            # Check individual access
            if not permission_checker.can_access_mahasiswa_data(mahasiswa, 'modify'):
                results.append({
                    'mahasiswa_id': mahasiswa_id,
                    'status': 'error',
                    'message': 'Tidak memiliki akses untuk mengubah data mahasiswa ini'
                })
                continue

            # Validate status transition
            if not is_valid_status_transition(mahasiswa.id_jenis_keluar, new_status):
                results.append({
                    'mahasiswa_id': mahasiswa_id,
                    'status': 'error',
                    'message': f'Transisi status tidak valid: {mahasiswa.id_jenis_keluar} -> {new_status}'
                })
                continue

            # Update status
            old_status = mahasiswa.id_jenis_keluar
            mahasiswa.id_jenis_keluar = new_status
            mahasiswa.save()

            # Log change
            logger.info(f"Mahasiswa status updated by {request.user.username}: {mahasiswa.nim} {old_status} -> {new_status}")

            results.append({
                'mahasiswa_id': mahasiswa_id,
                'status': 'success',
                'old_status': old_status,
                'new_status': new_status
            })

        except RiwayatPendidikan.DoesNotExist:
            results.append({
                'mahasiswa_id': mahasiswa_id,
                'status': 'error',
                'message': 'Mahasiswa tidak ditemukan'
            })
        except Exception as e:
            results.append({
                'mahasiswa_id': mahasiswa_id,
                'status': 'error',
                'message': f'Error: {str(e)}'
            })

    # Summary
    success_count = len([r for r in results if r['status'] == 'success'])
    error_count = len([r for r in results if r['status'] == 'error'])

    return Response({
        'results': results,
        'summary': {
            'total': len(mahasiswa_updates),
            'success': success_count,
            'error': error_count
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_assign_dosen_to_kelas(request):
    """Bulk assign dosen to kelas with permission validation"""

    if not check_user_academic_role(request.user, ['kaprodi', 'admin_fakultas']):
        return Response({'error': 'Tidak memiliki akses untuk assign dosen'}, status=403)

    assignments = request.data.get('assignments', [])
    force_reassign = request.data.get('force_reassign', False)

    results = []
    profile = get_user_profile(request.user)

    for assignment in assignments:
        kelas_id = assignment.get('kelas_id')
        dosen_id = assignment.get('dosen_id')

        try:
            kelas = Kelas.objects.get(id=kelas_id)
            dosen = Dosen.objects.get(id_dosen=dosen_id)

            # Check kelas access
            if profile.academic_role == 'kaprodi':
                if kelas.id_prodi != profile.id_prodi:
                    results.append({
                        'kelas_id': kelas_id,
                        'dosen_id': dosen_id,
                        'status': 'error',
                        'message': 'Kelas tidak berada di prodi Anda'
                    })
                    continue

            # Check if dosen can teach in this prodi
            dosen_prodi_assignments = Penugasan.objects.filter(
                id_dosen=dosen,
                id_prodi=kelas.id_prodi,
                deleted=False
            )

            if not dosen_prodi_assignments.exists():
                results.append({
                    'kelas_id': kelas_id,
                    'dosen_id': dosen_id,
                    'status': 'error',
                    'message': f'Dosen {dosen.nama_dosen} tidak memiliki penugasan di prodi ini'
                })
                continue

            # Check existing assignment
            existing_assignment = Pengajar.objects.filter(
                id_kelas_kuliah=kelas,
                id_dosen=dosen
            ).first()

            if existing_assignment and not force_reassign:
                results.append({
                    'kelas_id': kelas_id,
                    'dosen_id': dosen_id,
                    'status': 'warning',
                    'message': f'Dosen sudah mengajar di kelas ini',
                    'pengajar_id': existing_assignment.id
                })
                continue

            # Create or update assignment
            pengajar, created = Pengajar.objects.get_or_create(
                id_kelas_kuliah=kelas,
                id_dosen=dosen,
                defaults={
                    'id_registrasi_dosen': dosen_prodi_assignments.first(),
                    'urutan': Pengajar.objects.filter(id_kelas_kuliah=kelas).count() + 1
                }
            )

            results.append({
                'kelas_id': kelas_id,
                'dosen_id': dosen_id,
                'status': 'success',
                'message': 'Dosen berhasil ditugaskan' if created else 'Assignment sudah ada',
                'pengajar_id': pengajar.id,
                'created': created
            })

        except Kelas.DoesNotExist:
            results.append({
                'kelas_id': kelas_id,
                'dosen_id': dosen_id,
                'status': 'error',
                'message': 'Kelas tidak ditemukan'
            })
        except Dosen.DoesNotExist:
            results.append({
                'kelas_id': kelas_id,
                'dosen_id': dosen_id,
                'status': 'error',
                'message': 'Dosen tidak ditemukan'
            })

    return Response({
        'results': results,
        'summary': {
            'total': len(assignments),
            'success': len([r for r in results if r['status'] == 'success']),
            'error': len([r for r in results if r['status'] == 'error']),
            'warning': len([r for r in results if r['status'] == 'warning'])
        }
    })
```

## 🎯 **Real-world API Examples**

### **1. Student Information System API**
```python
# api/v1/siadin/mahasiswa/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_dashboard(request):
    """Student dashboard API"""

    profile = get_user_profile(request.user)
    if not profile or profile.academic_role != 'mahasiswa':
        return Response({'error': 'Akses hanya untuk mahasiswa'}, status=403)

    try:
        mahasiswa = RiwayatPendidikan.objects.get(nim=request.user.username)
    except RiwayatPendidikan.DoesNotExist:
        return Response({'error': 'Data mahasiswa tidak ditemukan'}, status=404)

    current_semester = get_current_semester()

    # KRS current semester
    current_krs = KRS.objects.filter(
        id_registrasi_mahasiswa=mahasiswa,
        id_semester=current_semester
    ).select_related('id_kelas_kuliah', 'id_matkul')

    # Recent grades
    recent_grades = Nilai.objects.filter(
        id_registrasi_mahasiswa=mahasiswa
    ).select_related('id_kelas_kuliah', 'id_matkul').order_by('-created_at')[:10]

    # Schedule today
    today = timezone.now().date()
    today_schedule = []
    for krs in current_krs:
        jadwal = Jadwal.objects.filter(id_kelas=krs.id_kelas_kuliah).first()
        if jadwal and is_today_schedule(jadwal, today):
            today_schedule.append({
                'kelas': krs.id_kelas_kuliah.nama_kelas_kuliah,
                'matkul': krs.id_matkul.nama_mata_kuliah,
                'jadwal': f"{jadwal.hari.nama_hari}, {jadwal.sesi.jam}",
                'ruang': jadwal.ruang.nama if jadwal.ruang else None
            })

    # Academic progress
    total_sks = sum([krs.id_matkul.sks_mata_kuliah for krs in current_krs])
    ipk = calculate_ipk(mahasiswa)

    return Response({
        'mahasiswa_info': {
            'nim': mahasiswa.nim,
            'nama': mahasiswa.nama_mahasiswa,
            'prodi': mahasiswa.id_prodi.nama_program_studi if mahasiswa.id_prodi else None,
            'angkatan': mahasiswa.angkatan,
        },
        'current_semester': {
            'semester': current_semester.nama_semester if current_semester else None,
            'total_sks': total_sks,
            'jumlah_matkul': current_krs.count()
        },
        'today_schedule': today_schedule,
        'recent_grades': NilaiSerializer(recent_grades, many=True).data,
        'academic_progress': {
            'ipk': ipk,
            'total_sks_lulus': get_total_sks_lulus(mahasiswa),
            'semester_aktif': get_semester_aktif(mahasiswa)
        },
        'notifications': get_student_notifications(mahasiswa)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_transcript(request):
    """Get student transcript"""

    profile = get_user_profile(request.user)
    if profile.academic_role == 'mahasiswa':
        # Student can only access own transcript
        try:
            mahasiswa = RiwayatPendidikan.objects.get(nim=request.user.username)
        except RiwayatPendidikan.DoesNotExist:
            return Response({'error': 'Data mahasiswa tidak ditemukan'}, status=404)
    else:
        # Other roles need mahasiswa_id parameter and permission check
        mahasiswa_id = request.GET.get('mahasiswa_id')
        if not mahasiswa_id:
            return Response({'error': 'mahasiswa_id diperlukan'}, status=400)

        try:
            mahasiswa = RiwayatPendidikan.objects.get(id=mahasiswa_id)
        except RiwayatPendidikan.DoesNotExist:
            return Response({'error': 'Mahasiswa tidak ditemukan'}, status=404)

        # Check access permission
        permission_checker = DynamicPermissionChecker(request.user)
        if not permission_checker.can_access_mahasiswa_data(mahasiswa, 'view'):
            return Response({'error': 'Tidak memiliki akses ke data mahasiswa ini'}, status=403)

    # Get all grades grouped by semester
    grades = Nilai.objects.filter(
        id_registrasi_mahasiswa=mahasiswa
    ).select_related('id_kelas_kuliah', 'id_matkul', 'id_semester').order_by('id_semester__id_semester')

    # Group by semester
    transcript_data = {}
    for grade in grades:
        semester_id = grade.id_semester.id_semester
        if semester_id not in transcript_data:
            transcript_data[semester_id] = {
                'semester_info': {
                    'id': semester_id,
                    'nama': grade.id_semester.nama_semester,
                    'tahun': grade.id_semester.tahun
                },
                'grades': [],
                'ips': 0,
                'total_sks': 0
            }

        transcript_data[semester_id]['grades'].append({
            'kode_matkul': grade.id_matkul.kode_mata_kuliah,
            'nama_matkul': grade.id_matkul.nama_mata_kuliah,
            'sks': grade.id_matkul.sks_mata_kuliah,
            'nilai_huruf': grade.nilai_huruf,
            'nilai_indeks': grade.nilai_indeks,
            'kelas': grade.id_kelas_kuliah.nama_kelas_kuliah
        })

    # Calculate IPS for each semester
    for semester_data in transcript_data.values():
        ips, total_sks = calculate_ips_semester(semester_data['grades'])
        semester_data['ips'] = ips
        semester_data['total_sks'] = total_sks

    # Calculate overall statistics
    overall_stats = {
        'ipk': calculate_ipk(mahasiswa),
        'total_sks_lulus': get_total_sks_lulus(mahasiswa),
        'total_sks_diambil': get_total_sks_diambil(mahasiswa),
        'total_semester': len(transcript_data)
    }

    return Response({
        'mahasiswa_info': MahasiswaSerializer(mahasiswa).data,
        'transcript': list(transcript_data.values()),
        'overall_stats': overall_stats,
        'generated_at': timezone.now(),
        'generated_by': request.user.username
    })
```

### **2. Faculty Management API**
```python
# api/v1/faculty/management/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_faculty_overview(request):
    """Faculty overview for admin"""

    if not check_user_academic_role(request.user, ['admin_fakultas', 'dekan']):
        return Response({'error': 'Akses hanya untuk admin fakultas'}, status=403)

    profile = get_user_profile(request.user)
    if not profile.id_fakultas:
        return Response({'error': 'Fakultas tidak ditemukan'}, status=404)

    fakultas = profile.id_fakultas

    # Get all prodi in fakultas
    prodi_list = ProgramStudi.objects.filter(id_fakultas=fakultas)

    # Statistics
    stats = {
        'total_prodi': prodi_list.count(),
        'total_dosen': Dosen.objects.filter(
            penugasan__id_prodi__id_fakultas=fakultas,
            deleted=False
        ).distinct().count(),
        'total_mahasiswa_aktif': RiwayatPendidikan.objects.filter(
            id_prodi__id_fakultas=fakultas,
            id_jenis_keluar__isnull=True
        ).count(),
        'total_kelas_semester_ini': Kelas.objects.filter(
            id_prodi__id_fakultas=fakultas,
            id_semester=get_current_semester()
        ).count()
    }

    # Prodi breakdown
    prodi_breakdown = []
    for prodi in prodi_list:
        prodi_stats = {
            'prodi_info': {
                'id_prodi': prodi.id_prodi,
                'nama_prodi': prodi.nama_program_studi,
                'kode_prodi': prodi.kode_program_studi
            },
            'mahasiswa_aktif': RiwayatPendidikan.objects.filter(
                id_prodi=prodi,
                id_jenis_keluar__isnull=True
            ).count(),
            'dosen_aktif': Dosen.objects.filter(
                penugasan__id_prodi=prodi,
                deleted=False
            ).distinct().count(),
            'kelas_semester_ini': Kelas.objects.filter(
                id_prodi=prodi,
                id_semester=get_current_semester()
            ).count()
        }
        prodi_breakdown.append(prodi_stats)

    # Recent activities
    recent_activities = get_recent_faculty_activities(fakultas)

    # Pending approvals
    pending_approvals = get_pending_faculty_approvals(fakultas)

    return Response({
        'fakultas_info': {
            'id_fakultas': fakultas.id,
            'nama_fakultas': getattr(fakultas, 'nama_fakultas', 'Unknown'),
        },
        'overview_stats': stats,
        'prodi_breakdown': prodi_breakdown,
        'recent_activities': recent_activities,
        'pending_approvals': pending_approvals,
        'generated_at': timezone.now()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_faculty_action(request):
    """Approve various faculty-level actions"""

    if not check_user_academic_role(request.user, ['admin_fakultas', 'dekan']):
        return Response({'error': 'Akses hanya untuk admin fakultas'}, status=403)

    action_type = request.data.get('action_type')
    action_id = request.data.get('action_id')
    approval_status = request.data.get('status')  # 'approved' or 'rejected'
    notes = request.data.get('notes', '')

    if action_type not in ['dosen_promotion', 'curriculum_change', 'new_course']:
        return Response({'error': 'Action type tidak valid'}, status=400)

    try:
        # Process based on action type
        if action_type == 'dosen_promotion':
            result = process_dosen_promotion_approval(
                request.user, action_id, approval_status, notes
            )
        elif action_type == 'curriculum_change':
            result = process_curriculum_approval(
                request.user, action_id, approval_status, notes
            )
        elif action_type == 'new_course':
            result = process_new_course_approval(
                request.user, action_id, approval_status, notes
            )

        if result['success']:
            return Response({
                'status': 'success',
                'message': result['message'],
                'action_id': action_id,
                'approved_by': request.user.username,
                'approved_at': timezone.now()
            })
        else:
            return Response({'error': result['error']}, status=400)

    except Exception as e:
        logger.error(f"Faculty approval error: {e}")
        return Response({'error': 'Terjadi kesalahan sistem'}, status=500)
```

Dokumentasi ini memberikan contoh-contoh praktis penggunaan sistem permission di berbagai skenario API yang umum dalam sistem akademik. 🚀