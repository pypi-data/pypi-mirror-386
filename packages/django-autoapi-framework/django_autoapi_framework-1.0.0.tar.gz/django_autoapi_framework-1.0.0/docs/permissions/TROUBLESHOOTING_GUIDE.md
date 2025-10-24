# 🔧 **Troubleshooting Guide - Sistem Permission**

Panduan lengkap untuk mendiagnosis dan memperbaiki masalah pada sistem permission.

## 📋 **Daftar Masalah Umum**

1. [User Tidak Bisa Login](#user-tidak-bisa-login)
2. [Permission Denied Errors](#permission-denied-errors)
3. [Profile Tidak Ter-sync](#profile-tidak-ter-sync)
4. [Migration Issues](#migration-issues)
5. [API Permission Errors](#api-permission-errors)
6. [Performance Issues](#performance-issues)
7. [Group Assignment Problems](#group-assignment-problems)
8. [Admin Interface Issues](#admin-interface-issues)

## 🚨 **User Tidak Bisa Login**

### **Gejala:**
- User tidak bisa login ke sistem
- Error "Invalid credentials" meskipun password benar
- User ter-redirect ke halaman unauthorized

### **Diagnosis:**

**1. Check User Status:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
username = 'username_disini'
try:
    user = User.objects.get(username=username)
    print(f'User found: {user.username}')
    print(f'Is active: {user.is_active}')
    print(f'Is staff: {user.is_staff}')
    print(f'Last login: {user.last_login}')
    print(f'Date joined: {user.date_joined}')
except User.DoesNotExist:
    print('User tidak ditemukan')
"
```

**2. Check Profile:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from core.utils.profile_utils import get_user_profile
username = 'username_disini'
user = User.objects.get(username=username)
profile = get_user_profile(user)
if profile:
    print(f'Profile found: {profile.academic_role}')
    print(f'Is verified: {profile.is_verified}')
    print(f'Verification date: {profile.verification_date}')
else:
    print('Profile tidak ditemukan')
"
```

### **Solusi:**

**1. Activate User:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='username_disini')
user.is_active = True
user.save()
print('User activated')
"
```

**2. Create Missing Profile:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from apps.academic.models import Profile
user = User.objects.get(username='username_disini')
if not hasattr(user, 'academic_profile'):
    profile = Profile.objects.create(
        user=user,
        academic_role='guest',
        is_verified=True
    )
    print('Profile created')
else:
    print('Profile already exists')
"
```

**3. Reset Password:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='username_disini')
user.set_password('password_baru')
user.save()
print('Password reset')
"
```

## ❌ **Permission Denied Errors**

### **Gejala:**
- Error 403 Forbidden saat akses endpoint/page
- "Akses ditolak" messages
- API returns permission errors

### **Diagnosis:**

**1. Check User Groups:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='username_disini')
groups = list(user.groups.values_list('name', flat=True))
print(f'User groups: {groups}')
expected_groups = ['Dosen', 'Kaprodi', 'AdminFakultas', 'Mahasiswa', 'Superuser']
missing_groups = [g for g in expected_groups if g not in groups]
print(f'Available groups in system: {expected_groups}')
if missing_groups:
    print(f'User missing groups: {missing_groups}')
"
```

**2. Check Permissions:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='username_disini')
user_perms = list(user.user_permissions.values_list('codename', flat=True))
group_perms = []
for group in user.groups.all():
    group_perms.extend(list(group.permissions.values_list('codename', flat=True)))
print(f'Direct permissions: {user_perms}')
print(f'Group permissions: {group_perms}')
print(f'Total permissions: {len(set(user_perms + group_perms))}')
"
```

**3. Check Profile Access:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from core.utils.profile_utils import get_profile_context_for_api
user = User.objects.get(username='username_disini')
context = get_profile_context_for_api(user)
print('Profile context:')
import json
print(json.dumps(context, indent=2, default=str))
"
```

### **Solusi:**

**1. Sync Profile Permissions:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from core.utils.profile_utils import sync_profile_with_permissions
user = User.objects.get(username='username_disini')
result = sync_profile_with_permissions(user)
print('Sync result:', result)
if result['changes_made']:
    print('Changes made:', result['changes_made'])
if result['errors']:
    print('Errors:', result['errors'])
"
```

**2. Manual Group Assignment:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User, Group
user = User.objects.get(username='username_disini')
group = Group.objects.get(name='Dosen')  # atau group lain
user.groups.add(group)
print(f'Added user to group: {group.name}')
"
```

**3. Reset All Permissions:**
```bash
# Run permission setup script
python scripts/auto_permission_setup.py

# Or manual reset
python manage.py shell -c "
from django.contrib.auth.models import User
from core.utils.profile_utils import bulk_sync_profiles_with_permissions
users = User.objects.filter(is_active=True)
result = bulk_sync_profiles_with_permissions(users)
print(f'Synced: {result[\"successful_syncs\"]} users')
print(f'Failed: {result[\"failed_syncs\"]} users')
"
```

## 🔄 **Profile Tidak Ter-sync**

### **Gejala:**
- Profile ada tapi permissions tidak sesuai
- Group assignments tidak match dengan academic role
- Profile changes tidak ter-reflect di permissions

### **Diagnosis:**

**1. Check Profile-Group Mismatch:**
```bash
python manage.py shell -c "
from apps.academic.models import Profile
from django.contrib.auth.models import Group

mismatches = []
for profile in Profile.objects.all():
    expected_groups = {
        'dosen': 'Dosen',
        'kaprodi': 'Kaprodi',
        'admin_fakultas': 'AdminFakultas',
        'dekan': 'AdminFakultas',
        'mahasiswa': 'Mahasiswa',
        'staff': 'Dosen',
        'guest': None
    }

    expected_group = expected_groups.get(profile.academic_role)
    current_groups = list(profile.user.groups.values_list('name', flat=True))

    if expected_group and expected_group not in current_groups:
        mismatches.append({
            'user': profile.user.username,
            'role': profile.academic_role,
            'expected': expected_group,
            'current': current_groups
        })

print(f'Found {len(mismatches)} mismatches:')
for mismatch in mismatches:
    print(f'- {mismatch}')
"
```

**2. Check Django Signals:**
```bash
python manage.py shell -c "
from apps.academic.models import Profile
from django.db.models.signals import post_save

# Check if signals are connected
receivers = post_save._live_receivers(sender=Profile)
print(f'Profile post_save receivers: {len(receivers)}')
for receiver in receivers:
    print(f'- {receiver}')
"
```

### **Solusi:**

**1. Manual Profile Sync:**
```bash
python manage.py shell -c "
from apps.academic.models import Profile
from core.utils.profile_utils import sync_profile_with_permissions

for profile in Profile.objects.all():
    result = sync_profile_with_permissions(profile.user)
    if result['changes_made']:
        print(f'{profile.user.username}: {result[\"changes_made\"]}')
    if result['errors']:
        print(f'{profile.user.username} ERRORS: {result[\"errors\"]}')
"
```

**2. Fix Specific Profile:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from core.utils.profile_utils import sync_profile_with_permissions
user = User.objects.get(username='username_disini')
result = sync_profile_with_permissions(user)
print('Result:', result)
"
```

**3. Recreate Profile:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from apps.academic.models import Profile

user = User.objects.get(username='username_disini')

# Backup old profile data
old_profile = user.academic_profile
old_data = {
    'academic_role': old_profile.academic_role,
    'id_dosen': old_profile.id_dosen,
    'id_prodi': old_profile.id_prodi,
    'id_fakultas': old_profile.id_fakultas,
    'email_dsn': old_profile.email_dsn,
    'npp': old_profile.npp,
}

# Delete old profile
old_profile.delete()

# Create new profile
new_profile = Profile.objects.create(user=user, **old_data)
print(f'Profile recreated for {user.username}')
"
```

## 🗄️ **Migration Issues**

### **Gejala:**
- Migration fails dengan dependency errors
- "already exists" errors saat migrate
- Inconsistent migration history

### **Diagnosis:**

**1. Check Migration Status:**
```bash
python manage.py showmigrations academic
python manage.py showmigrations feeder
```

**2. Check Migration Dependencies:**
```bash
python manage.py shell -c "
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None)
for app, migrations in loader.graph.nodes.items():
    if app[0] in ['academic', 'feeder']:
        print(f'{app}: dependencies={loader.graph.node_map[app].dependencies}')
"
```

### **Solusi:**

**1. Fake Apply Missing Migrations:**
```bash
# If feeder migration is missing
python manage.py migrate --fake feeder 0004_remove_dosen_email_dsn

# Then run normal migration
python manage.py migrate
```

**2. Reset Specific App Migrations:**
```bash
# DANGER: Will lose data! Backup first!

# Reset academic migrations
python manage.py migrate academic zero

# Remove migration files
rm apps/academic/migrations/0*.py

# Recreate initial migration
python manage.py makemigrations academic

# Apply migrations
python manage.py migrate academic
```

**3. Manual Migration Fix:**
```bash
# If specific migration fails, edit the migration file to fix issues
# Then run:
python manage.py migrate --fake-initial academic
python manage.py migrate
```

## 🔌 **API Permission Errors**

### **Gejala:**
- API returns 403 errors
- Inconsistent API access
- Permission checks failing in views

### **Diagnosis:**

**1. Test API Permissions:**
```bash
python manage.py shell -c "
from django.test import RequestFactory
from django.contrib.auth.models import User
from core.utils.permission_utils import check_user_academic_role, check_prodi_access

user = User.objects.get(username='username_disini')
print(f'Role check (dosen): {check_user_academic_role(user, [\"dosen\"])}')
print(f'Role check (kaprodi): {check_user_academic_role(user, [\"kaprodi\"])}')
print(f'Prodi access test: {check_prodi_access(user, \"prodi_id_disini\")}')
"
```

**2. Check API Authentication:**
```bash
# Test API endpoint
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/academic/dosen/

# Check token validity
python manage.py shell -c "
from rest_framework_simplejwt.tokens import AccessToken
token = 'your_token_here'
try:
    access_token = AccessToken(token)
    print(f'Token valid. User ID: {access_token[\"user_id\"]}')
except Exception as e:
    print(f'Token invalid: {e}')
"
```

### **Solusi:**

**1. Check Permission Decorators:**
```python
# In your view, add debugging
from core.utils.permission_utils import check_user_academic_role

@api_view(['GET'])
def my_view(request):
    print(f"User: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"Role check: {check_user_academic_role(request.user, ['dosen'])}")
    # ... rest of view
```

**2. Refresh Authentication:**
```bash
# Generate new token
python manage.py shell -c "
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

user = User.objects.get(username='username_disini')
refresh = RefreshToken.for_user(user)
print(f'Access token: {refresh.access_token}')
print(f'Refresh token: {refresh}')
"
```

## ⚡ **Performance Issues**

### **Gejala:**
- Slow permission checks
- N+1 query problems
- High database load

### **Diagnosis:**

**1. Enable Query Logging:**
```python
# In settings/development.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

**2. Check Query Count:**
```bash
python manage.py shell -c "
from django.db import connection
from django.contrib.auth.models import User
from core.utils.profile_utils import get_user_profile

# Reset query count
connection.queries_log.clear()

# Perform operation
user = User.objects.get(username='username_disini')
profile = get_user_profile(user)

print(f'Query count: {len(connection.queries)}')
for query in connection.queries:
    print(f'- {query[\"sql\"]}')
"
```

### **Solusi:**

**1. Optimize Queries:**
```python
# BAD - N+1 queries
for user in User.objects.all():
    profile = get_user_profile(user)

# GOOD - Use select_related
users = User.objects.select_related('academic_profile').all()
for user in users:
    profile = user.academic_profile
```

**2. Add Database Indexes:**
```python
# In models.py
class Profile(BaseTable):
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['academic_role']),
            models.Index(fields=['id_prodi']),
            models.Index(fields=['is_verified']),
        ]
```

**3. Cache Permission Results:**
```python
from django.core.cache import cache

def cached_permission_check(user, permission_key):
    cache_key = f"perm_{user.id}_{permission_key}"
    result = cache.get(cache_key)

    if result is None:
        result = check_user_permission(user, permission_key)
        cache.set(cache_key, result, 300)  # 5 minutes

    return result
```

## 👥 **Group Assignment Problems**

### **Gejala:**
- Users tidak ter-assign ke group yang benar
- Group permissions tidak konsisten
- Manual group assignments ter-override

### **Diagnosis:**

**1. Check Group Consistency:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import Group, User
from apps.academic.models import Profile

print('=== GROUP ANALYSIS ===')
for group in Group.objects.all():
    user_count = group.user_set.count()
    perm_count = group.permissions.count()
    print(f'{group.name}: {user_count} users, {perm_count} permissions')

print('\n=== USERS WITHOUT GROUPS ===')
users_no_groups = User.objects.filter(groups__isnull=True, is_active=True)
for user in users_no_groups:
    profile = getattr(user, 'academic_profile', None)
    role = profile.academic_role if profile else 'No profile'
    print(f'{user.username}: {role}')
"
```

**2. Check Group Permissions:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import Group

for group in Group.objects.all():
    perms = list(group.permissions.values_list('codename', flat=True))
    print(f'{group.name}: {len(perms)} permissions')
    if perms:
        print(f'  Sample: {perms[:5]}')
"
```

### **Solusi:**

**1. Reset All Group Assignments:**
```bash
python scripts/auto_permission_setup.py --reset
```

**2. Manual Group Fix:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User, Group
from apps.academic.models import Profile

# Fix specific role
dosen_group = Group.objects.get(name='Dosen')
dosen_profiles = Profile.objects.filter(academic_role='dosen')

for profile in dosen_profiles:
    user = profile.user
    if dosen_group not in user.groups.all():
        user.groups.add(dosen_group)
        print(f'Added {user.username} to Dosen group')
"
```

**3. Validate Group Structure:**
```bash
python scripts/permission_validator.py --groups
```

## 🎛️ **Admin Interface Issues**

### **Gejala:**
- Admin interface tidak bisa diakses
- Profile inline tidak muncul
- Admin actions error

### **Diagnosis:**

**1. Check Admin Registration:**
```bash
python manage.py shell -c "
from django.contrib import admin
from apps.academic.models import Profile

print('Registered models:')
for model, admin_class in admin.site._registry.items():
    if 'academic' in str(model):
        print(f'  {model}: {admin_class}')

print(f'Profile registered: {Profile in admin.site._registry}')
"
```

**2. Check Admin Permissions:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='admin_username')
print(f'Is staff: {user.is_staff}')
print(f'Is superuser: {user.is_superuser}')
print(f'Has admin perms: {user.has_perm(\"academic.view_profile\")}')
"
```

### **Solusi:**

**1. Create Admin User:**
```bash
python manage.py createsuperuser
```

**2. Fix Admin Registration:**
```python
# In admin.py
from django.contrib import admin
from .models import Profile

# Re-register if needed
if Profile in admin.site._registry:
    admin.site.unregister(Profile)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'academic_role', 'is_verified']
```

**3. Check Admin URLs:**
```bash
python manage.py shell -c "
from django.urls import reverse
try:
    admin_url = reverse('admin:index')
    print(f'Admin URL: {admin_url}')
except Exception as e:
    print(f'Admin URL error: {e}')
"
```

## 🔍 **Diagnostic Scripts**

### **1. Complete System Check:**
```bash
# Create file: scripts/system_diagnosis.py
python manage.py shell -c "
print('=== SYSTEM DIAGNOSIS ===')

# Users
from django.contrib.auth.models import User
total_users = User.objects.count()
active_users = User.objects.filter(is_active=True).count()
print(f'Users: {active_users}/{total_users} active')

# Profiles
from apps.academic.models import Profile
total_profiles = Profile.objects.count()
verified_profiles = Profile.objects.filter(is_verified=True).count()
print(f'Profiles: {verified_profiles}/{total_profiles} verified')

# Groups
from django.contrib.auth.models import Group
groups = Group.objects.all()
print(f'Groups: {groups.count()}')
for group in groups:
    print(f'  {group.name}: {group.user_set.count()} users')

# Permissions
from django.contrib.auth.models import Permission
perms = Permission.objects.filter(content_type__app_label__in=['academic', 'feeder'])
print(f'Permissions: {perms.count()}')

print('=== DIAGNOSIS COMPLETE ===')
"
```

### **2. Permission Audit:**
```bash
# Create file: scripts/permission_audit.py
python manage.py shell -c "
from django.contrib.auth.models import User, Group, Permission
from apps.academic.models import Profile

print('=== PERMISSION AUDIT ===')

# Check for common issues
issues = []

# 1. Users without profiles
users_no_profile = User.objects.filter(academic_profile__isnull=True, is_active=True)
if users_no_profile.exists():
    issues.append(f'{users_no_profile.count()} active users without profiles')

# 2. Profiles without groups
for profile in Profile.objects.all():
    if not profile.user.groups.exists() and profile.academic_role != 'guest':
        issues.append(f'User {profile.user.username} ({profile.academic_role}) has no groups')

# 3. Missing groups
required_groups = ['Dosen', 'Kaprodi', 'AdminFakultas', 'Mahasiswa', 'Superuser']
existing_groups = list(Group.objects.values_list('name', flat=True))
missing_groups = [g for g in required_groups if g not in existing_groups]
if missing_groups:
    issues.append(f'Missing groups: {missing_groups}')

if issues:
    print('ISSUES FOUND:')
    for issue in issues:
        print(f'  - {issue}')
else:
    print('No issues found!')

print('=== AUDIT COMPLETE ===')
"
```

Gunakan panduan ini untuk mendiagnosis dan memperbaiki masalah pada sistem permission! 🔧