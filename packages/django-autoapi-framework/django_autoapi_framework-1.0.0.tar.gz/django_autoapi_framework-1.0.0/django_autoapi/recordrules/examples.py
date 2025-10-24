"""
Example usage patterns untuk Record Rules
"""

from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django_autoapi.recordrules.models import RecordRule, RecordRuleBypass
from django_autoapi.recordrules.engine import RecordRuleEngine


# ========================================
# Example 1: Kaprodi Can Only See Their Unit's Students
# ========================================

def example_kaprodi_rule(Mahasiswa):
    """
    Kaprodi hanya bisa lihat mahasiswa dari unit mereka
    """
    # Get or create group
    kaprodi_group = Group.objects.get_or_create(name='Kaprodi')[0]
    
    # Create rule
    ct = ContentType.objects.get_for_model(Mahasiswa)
    rule = RecordRule.objects.create(
        name='Kaprodi: Own Unit Students',
        content_type=ct,
        domain_filter={
            'unit_id': '${user.profile.unit_id}'
            # Assumes user has profile with unit_id
        },
        perm_read=True,
        perm_write=True,
    )
    rule.groups.add(kaprodi_group)
    
    # Usage:
    # kaprodi_user = User.objects.get(username='kaprodi_ti')
    # engine = RecordRuleEngine(kaprodi_user)
    # students = engine.apply_rules(Mahasiswa.objects.all())
    # Result: Only students from TI unit


# ========================================
# Example 2: Staff Can Only See Active Records
# ========================================

def example_active_only_rule(Mahasiswa):
    """
    Staff hanya bisa lihat mahasiswa yang active
    """
    staff_group = Group.objects.get_or_create(name='Staff')[0]
    
    ct = ContentType.objects.get_for_model(Mahasiswa)
    rule = RecordRule.objects.create(
        name='Staff: Active Students Only',
        content_type=ct,
        domain_filter={'status': 'active'},
        perm_read=True,
        global_rule=False  # Only for staff group
    )
    rule.groups.add(staff_group)


# ========================================
# Example 3: Dosen Can See Students They Teach
# ========================================

def example_dosen_rule(Mahasiswa):
    """
    Dosen bisa lihat mahasiswa yang mereka ajar
    """
    dosen_group = Group.objects.get_or_create(name='Dosen')[0]
    
    ct = ContentType.objects.get_for_model(Mahasiswa)
    rule = RecordRule.objects.create(
        name='Dosen: Students in Their Classes',
        content_type=ct,
        domain_filter={
            'kelas__dosen_id': '${user.id}'
            # Assumes Mahasiswa has kelas relation with dosen
        },
        perm_read=True,
    )
    rule.groups.add(dosen_group)


# ========================================
# Example 4: Multi-tenant SaaS Application
# ========================================

def example_tenant_isolation(Product):
    """
    Each tenant can only see their own products
    """
    ct = ContentType

    ct = ContentType.objects.get_for_model(Product)
    
    # Global rule for tenant isolation
    rule = RecordRule.objects.create(
        name='Tenant Isolation',
        content_type=ct,
        domain_filter={
            'tenant_id': '${user.tenant_id}'
            # Assumes Product has tenant_id field
        },
        perm_read=True,
        perm_write=True,
        perm_create=True,
        perm_delete=True,
        global_rule=True  # Applies to ALL users
    )
    
    # Superusers bypass automatically


# ========================================
# Example 5: Hierarchical Access (Dekan sees all)
# ========================================

def example_hierarchical_access(Mahasiswa):
    """
    Dekan can see all students, Kaprodi only their unit
    """
    # Kaprodi rule (restricted)
    kaprodi_group = Group.objects.get_or_create(name='Kaprodi')[0]
    ct = ContentType.objects.get_for_model(Mahasiswa)
    
    kaprodi_rule = RecordRule.objects.create(
        name='Kaprodi: Own Unit',
        content_type=ct,
        domain_filter={'unit_id': '${user.profile.unit_id}'},
        perm_read=True,
        priority=10  # Lower priority
    )
    kaprodi_rule.groups.add(kaprodi_group)
    
    # Dekan bypass (can see all)
    dekan_group = Group.objects.get_or_create(name='Dekan')[0]
    dekan_users = User.objects.filter(groups=dekan_group)
    
    for dekan in dekan_users:
        RecordRuleBypass.objects.get_or_create(
            user=dekan,
            content_type=ct,
            defaults={'reason': 'Dekan has full access'}
        )


# ========================================
# Example 6: Time-based Access
# ========================================

def example_time_based_access(Document):
    """
    Users can only see documents published in current year
    """
    from django.utils import timezone
    
    ct = ContentType.objects.get_for_model(Document)
    current_year = timezone.now().year
    
    rule = RecordRule.objects.create(
        name='Current Year Documents',
        content_type=ct,
        domain_filter={
            'published_date__year': current_year
        },
        perm_read=True,
        global_rule=True
    )


# ========================================
# Example 7: Owner-based Access
# ========================================

def example_owner_access(Task):
    """
    Users can only see tasks assigned to them
    """
    ct = ContentType.objects.get_for_model(Task)
    
    rule = RecordRule.objects.create(
        name='Own Tasks Only',
        content_type=ct,
        domain_filter={
            'assigned_to_id': '${user.id}'
        },
        perm_read=True,
        perm_write=True,
        global_rule=True
    )


# ========================================
# Example 8: Complex Multi-Condition
# ========================================

def example_complex_conditions(Order):
    """
    Sales team sees: their region AND (pending OR processing)
    """
    sales_group = Group.objects.get_or_create(name='Sales')[0]
    ct = ContentType.objects.get_for_model(Order)
    
    # Rule 1: Own region
    rule1 = RecordRule.objects.create(
        name='Sales: Own Region',
        content_type=ct,
        domain_filter={
            'region_id': '${user.profile.region_id}'
        },
        perm_read=True,
        priority=10
    )
    rule1.groups.add(sales_group)
    
    # Rule 2: Pending or Processing status
    rule2 = RecordRule.objects.create(
        name='Sales: Active Orders',
        content_type=ct,
        domain_filter={
            'status__in': ['pending', 'processing']
        },
        perm_read=True,
        priority=10
    )
    rule2.groups.add(sales_group)
    
    # Both rules will be combined with AND


# ========================================
# Example 9: Department-based with Lookups
# ========================================

def example_department_with_lookups(Employee):
    """
    HR can see employees with salary >= 50000 in their department
    """
    hr_group = Group.objects.get_or_create(name='HR')[0]
    ct = ContentType.objects.get_for_model(Employee)
    
    rule = RecordRule.objects.create(
        name='HR: Department with Salary Filter',
        content_type=ct,
        domain_filter={
            'department_id': '${user.profile.department_id}',
            'salary__gte': 50000
        },
        perm_read=True,
    )
    rule.groups.add(hr_group)


# ========================================
# Example 10: Public/Private Content
# ========================================

def example_public_private(Article):
    """
    Everyone sees public, authors see their own private
    """
    ct = ContentType.objects.get_for_model(Article)
    
    # Rule 1: Public articles (global)
    public_rule = RecordRule.objects.create(
        name='Public Articles',
        content_type=ct,
        domain_filter={'is_public': True},
        perm_read=True,
        global_rule=True,
        priority=5
    )
    
    # Rule 2: Own private articles
    author_group = Group.objects.get_or_create(name='Author')[0]
    private_rule = RecordRule.objects.create(
        name='Own Private Articles',
        content_type=ct,
        domain_filter={
            'author_id': '${user.id}',
            'is_public': False
        },
        perm_read=True,
        perm_write=True,
        priority=10  # Higher priority
    )
    private_rule.groups.add(author_group)


# ========================================
# Example 11: Usage in Views/APIs
# ========================================

def example_in_view(request, Mahasiswa):
    """
    How to use in Django views
    """
    from django_autoapi.recordrules.engine import RecordRuleEngine
    
    # Get user
    user = request.user
    
    # Create engine
    engine = RecordRuleEngine(user)
    
    # Apply to queryset
    all_students = Mahasiswa.objects.all()
    accessible_students = engine.apply_rules(all_students, operation='read')
    
    # Use filtered queryset
    return accessible_students


def example_check_single_instance(request, student):
    """
    Check access to single instance
    """
    from django_autoapi.recordrules.engine import RecordRuleChecker
    
    checker = RecordRuleChecker(request.user)
    
    # Check permissions
    if not checker.can_read(student):
        # User cannot read this student
        raise PermissionError('Access denied')
    
    if not checker.can_write(student):
        # User cannot modify this student
        raise PermissionError('Cannot modify')
    
    # Proceed with operation
    return student

