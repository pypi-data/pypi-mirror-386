"""
Example patterns untuk custom endpoints

This file contains production-ready patterns for implementing custom endpoints
in Django AutoAPI framework.
"""

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django_autoapi import AutoAPI
from django_autoapi.decorators import endpoint, detail_action, collection_action


# ============================================================================
# Pattern 1: Basic Detail Action
# ============================================================================

class Pattern1_BasicDetailAPI(AutoAPI):
    """
    Basic custom endpoint - detail action

    Example: Activate a single instance
    """
    # model = YourModel

    @endpoint(methods=['POST'], detail=True)
    def activate(self, request, instance):
        """
        Activate an instance

        Request:
            POST /api/items/{id}/activate/

        Response:
            {
                "id": 123,
                "status": "activated",
                "message": "Item activated successfully"
            }
        """
        instance.is_active = True
        instance.save()

        return Response({
            'id': instance.id,
            'status': 'activated',
            'message': 'Item activated successfully'
        })


# ============================================================================
# Pattern 2: Basic Collection Action
# ============================================================================

class Pattern2_BasicCollectionAPI(AutoAPI):
    """
    Basic collection endpoint - statistics

    Example: Get aggregate statistics
    """
    # model = YourModel

    @endpoint(methods=['GET'], detail=False)
    def statistics(self, request, queryset):
        """
        Get statistics

        Request:
            GET /api/items/statistics/
            GET /api/items/statistics/?category=electronics

        Response:
            {
                "total": 100,
                "active": 85,
                "inactive": 15
            }
        """
        return Response({
            'total': queryset.count(),
            'active': queryset.filter(is_active=True).count(),
            'inactive': queryset.filter(is_active=False).count()
        })


# ============================================================================
# Pattern 3: With Input Validation
# ============================================================================

class UpdateStatusSerializer(serializers.Serializer):
    """Input serializer for status update"""
    status = serializers.ChoiceField(choices=['active', 'inactive', 'pending'])
    notes = serializers.CharField(required=False, allow_blank=True)
    effective_date = serializers.DateField(required=False)


class Pattern3_WithValidationAPI(AutoAPI):
    """
    Endpoint with input validation

    Example: Update status with validated input
    """
    # model = YourModel

    @endpoint(methods=['POST'], detail=True)
    def update_status(self, request, instance):
        """
        Update instance status with validation

        Request:
            POST /api/items/{id}/update_status/
            {
                "status": "active",
                "notes": "Manually activated",
                "effective_date": "2025-01-15"
            }

        Response:
            {
                "id": 123,
                "status": "active",
                "message": "Status updated successfully"
            }
        """
        # Validate input
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get validated data
        data = serializer.validated_data
        instance.status = data['status']
        instance.status_notes = data.get('notes', '')
        if data.get('effective_date'):
            instance.status_date = data['effective_date']
        instance.save()

        return Response({
            'id': instance.id,
            'status': instance.status,
            'message': 'Status updated successfully'
        })


# ============================================================================
# Pattern 4: With Business Logic Validation
# ============================================================================

class Pattern4_WithBusinessValidationAPI(AutoAPI):
    """
    Endpoint with business logic validation

    Example: Graduate student with requirement checks
    """
    # model = Student

    @endpoint(methods=['POST'], detail=True)
    def graduate(self, request, instance):
        """
        Graduate student with validation

        Request:
            POST /api/students/{id}/graduate/

        Response:
            {
                "id": 123,
                "status": "graduated",
                "message": "Student graduated successfully"
            }
        """
        # Validate: not already graduated
        if instance.status == 'graduated':
            raise ValidationError({
                'status': 'Student already graduated'
            })

        # Validate: requirements met
        if hasattr(instance, 'can_graduate') and not instance.can_graduate():
            raise ValidationError({
                'requirements': 'Graduation requirements not met'
            })

        # Execute graduation
        instance.status = 'graduated'
        instance.save()

        # Optional: trigger side effects
        # send_graduation_notification(instance)

        return Response({
            'id': instance.id,
            'status': 'graduated',
            'message': 'Student graduated successfully'
        })


# ============================================================================
# Pattern 5: Returning Serialized Response
# ============================================================================

class Pattern5_SerializedResponseAPI(AutoAPI):
    """
    Endpoint returning serialized object

    Example: Complete task and return full object
    """
    # model = Task

    @endpoint(methods=['POST'], detail=True)
    def complete(self, request, instance):
        """
        Complete task and return serialized data

        Request:
            POST /api/tasks/{id}/complete/

        Response:
            {
                "status": "completed",
                "task": {
                    "id": 123,
                    "name": "Task name",
                    "status": "completed",
                    ...
                }
            }
        """
        # Execute business logic
        instance.status = 'completed'
        instance.completed_at = timezone.now()
        instance.save()

        # Return serialized instance using ViewSet's serializer
        serializer = self.get_serializer(instance)

        return Response({
            'status': 'completed',
            'task': serializer.data,
            'message': 'Task completed successfully'
        })


# ============================================================================
# Pattern 6: Collection with Aggregation
# ============================================================================

class Pattern6_CollectionAggregationAPI(AutoAPI):
    """
    Collection endpoint with database aggregation

    Example: Get sales summary
    """
    # model = Sale

    @endpoint(methods=['GET'], detail=False)
    def summary(self, request, queryset):
        """
        Get sales summary with aggregation

        Request:
            GET /api/sales/summary/
            GET /api/sales/summary/?month=2025-01

        Response:
            {
                "total_sales": 100,
                "total_amount": 50000.00,
                "average_amount": 500.00,
                "by_category": {
                    "electronics": 30,
                    "books": 70
                }
            }
        """
        # Aggregate statistics
        stats = queryset.aggregate(
            total_sales=Count('id'),
            total_amount=Sum('amount'),
            average_amount=Avg('amount')
        )

        # Group by category
        by_category = dict(
            queryset.values('category')
            .annotate(count=Count('id'))
            .values_list('category', 'count')
        )

        return Response({
            'total_sales': stats['total_sales'] or 0,
            'total_amount': stats['total_amount'] or 0,
            'average_amount': stats['average_amount'] or 0,
            'by_category': by_category
        })


# ============================================================================
# Pattern 7: Bulk Action
# ============================================================================

class BulkActionSerializer(serializers.Serializer):
    """Input serializer for bulk actions"""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )


class Pattern7_BulkActionAPI(AutoAPI):
    """
    Bulk action on multiple instances

    Example: Activate multiple items at once
    """
    # model = Product

    @endpoint(methods=['POST'], detail=False)
    def bulk_activate(self, request, queryset):
        """
        Activate multiple items

        Request:
            POST /api/products/bulk_activate/
            {
                "ids": [1, 2, 3, 4, 5]
            }

        Response:
            {
                "updated": 5,
                "message": "5 items activated"
            }
        """
        # Validate input
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data['ids']

        # Filter and update
        items = queryset.filter(id__in=ids)
        updated = items.update(is_active=True)

        return Response({
            'updated': updated,
            'message': f'{updated} items activated'
        })


# ============================================================================
# Pattern 8: With Custom Serializer per Endpoint
# ============================================================================

class MinimalProductSerializer(serializers.Serializer):
    """Minimal product serializer"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class DetailedProductSerializer(serializers.Serializer):
    """Detailed product serializer"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField()
    category = serializers.CharField()
    stock = serializers.IntegerField()
    is_active = serializers.BooleanField()


class Pattern8_CustomSerializerAPI(AutoAPI):
    """
    Different serializers for different endpoints

    Example: Minimal list, detailed individual
    """
    # model = Product

    @endpoint(
        methods=['GET'],
        detail=False,
        serializer_class=MinimalProductSerializer
    )
    def list_minimal(self, request, queryset):
        """
        List products with minimal data

        Request:
            GET /api/products/list_minimal/

        Response:
            [
                {"id": 1, "name": "Product 1", "price": "99.99"},
                {"id": 2, "name": "Product 2", "price": "149.99"}
            ]
        """
        # Use custom minimal serializer
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @endpoint(
        methods=['GET'],
        detail=True,
        serializer_class=DetailedProductSerializer
    )
    def detail_full(self, request, instance):
        """
        Get product with full details

        Request:
            GET /api/products/{id}/detail_full/

        Response:
            {
                "id": 1,
                "name": "Product 1",
                "price": "99.99",
                "description": "...",
                "category": "electronics",
                "stock": 50,
                "is_active": true
            }
        """
        # Use custom detailed serializer
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ============================================================================
# Pattern 9: Multiple HTTP Methods
# ============================================================================

class Pattern9_MultipleMethodsAPI(AutoAPI):
    """
    Single endpoint with multiple HTTP methods

    Example: Toggle status (GET to check, POST to toggle)
    """
    # model = Product

    @endpoint(methods=['GET', 'POST'], detail=True)
    def toggle_status(self, request, instance):
        """
        Check or toggle product status

        GET Request:
            GET /api/products/{id}/toggle_status/

        GET Response:
            {
                "current_status": "active",
                "can_toggle": true
            }

        POST Request:
            POST /api/products/{id}/toggle_status/

        POST Response:
            {
                "old_status": "active",
                "new_status": "inactive",
                "message": "Status toggled"
            }
        """
        if request.method == 'GET':
            # Check current status
            return Response({
                'current_status': instance.status,
                'can_toggle': True
            })
        else:
            # Toggle status
            old_status = instance.status
            instance.status = 'inactive' if instance.status == 'active' else 'active'
            instance.save()

            return Response({
                'old_status': old_status,
                'new_status': instance.status,
                'message': 'Status toggled'
            })


# ============================================================================
# Pattern 10: Complex Business Logic with Permissions
# ============================================================================

class Pattern10_ComplexBusinessLogicAPI(AutoAPI):
    """
    Endpoint with complex business logic and permissions

    Example: Approve request with multiple validations
    """
    # model = Request

    @endpoint(
        methods=['POST'],
        detail=True,
        permissions=['rest_framework.permissions.IsAuthenticated']
    )
    def approve(self, request, instance):
        """
        Approve request with validation

        Request:
            POST /api/requests/{id}/approve/
            {
                "notes": "Approved by manager"
            }

        Response:
            {
                "id": 123,
                "status": "approved",
                "approved_by": "john_doe",
                "message": "Request approved successfully"
            }
        """
        # Validate: only pending can be approved
        if instance.status != 'pending':
            raise ValidationError({
                'status': f'Cannot approve {instance.status} request'
            })

        # Validate: user has permission
        if not request.user.has_perm('app.approve_request'):
            raise ValidationError({
                'permission': 'You do not have permission to approve'
            })

        # Validate: custom business rules
        if hasattr(instance, 'can_be_approved'):
            can_approve, reason = instance.can_be_approved()
            if not can_approve:
                raise ValidationError({'validation': reason})

        # Execute approval
        instance.status = 'approved'
        instance.approved_by = request.user
        instance.approval_notes = request.data.get('notes', '')
        instance.save()

        # Optional: send notification
        # send_approval_notification(instance)

        # Return serialized response
        serializer = self.get_serializer(instance)

        return Response({
            'id': instance.id,
            'status': instance.status,
            'approved_by': request.user.username,
            'data': serializer.data,
            'message': 'Request approved successfully'
        })


# ============================================================================
# Pattern 11: Shorthand Decorators
# ============================================================================

class Pattern11_ShorthandDecoratorsAPI(AutoAPI):
    """
    Using shorthand decorators for common patterns

    Example: GET and POST shortcuts
    """
    # model = Product

    @detail_action(methods=['POST'])
    def activate(self, request, instance):
        """
        Activate product (shorthand for detail POST endpoint)

        Request:
            POST /api/products/{id}/activate/

        Response:
            {"status": "activated"}
        """
        instance.is_active = True
        instance.save()
        return Response({'status': 'activated'})

    @collection_action(methods=['GET'])
    def active_products(self, request, queryset):
        """
        Get active products (shorthand for collection GET endpoint)

        Request:
            GET /api/products/active_products/

        Response:
            {
                "count": 50,
                "results": [...]
            }
        """
        active = queryset.filter(is_active=True)

        # Use pagination
        page = self.paginate_queryset(active)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)


# ============================================================================
# Pattern 12: Export Data
# ============================================================================

class Pattern12_ExportDataAPI(AutoAPI):
    """
    Export data in different formats

    Example: Export as CSV or JSON
    """
    # model = Product

    @endpoint(methods=['GET'], detail=False)
    def export_csv(self, request, queryset):
        """
        Export data as CSV

        Request:
            GET /api/products/export_csv/
            GET /api/products/export_csv/?category=electronics

        Response:
            CSV file download
        """
        import csv
        from django.http import HttpResponse

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Price', 'Stock'])

        for product in queryset:
            writer.writerow([
                product.id,
                product.name,
                product.price,
                product.stock
            ])

        return response


# ============================================================================
# Pattern 13: Search and Filter
# ============================================================================

class SearchSerializer(serializers.Serializer):
    """Search parameters"""
    query = serializers.CharField(required=True)
    filters = serializers.DictField(required=False)


class Pattern13_SearchFilterAPI(AutoAPI):
    """
    Advanced search and filter

    Example: Search with multiple criteria
    """
    # model = Product

    @endpoint(methods=['POST'], detail=False)
    def advanced_search(self, request, queryset):
        """
        Advanced search with filters

        Request:
            POST /api/products/advanced_search/
            {
                "query": "laptop",
                "filters": {
                    "price_min": 500,
                    "price_max": 2000,
                    "category": "electronics"
                }
            }

        Response:
            {
                "count": 15,
                "results": [...]
            }
        """
        # Validate input
        serializer = SearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        filters = serializer.validated_data.get('filters', {})

        # Apply search
        results = queryset.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

        # Apply filters
        if 'price_min' in filters:
            results = results.filter(price__gte=filters['price_min'])
        if 'price_max' in filters:
            results = results.filter(price__lte=filters['price_max'])
        if 'category' in filters:
            results = results.filter(category=filters['category'])

        # Paginate
        page = self.paginate_queryset(results)
        data_serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(data_serializer.data)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
HOW TO USE THESE PATTERNS:

1. Copy the pattern you need
2. Replace 'model = YourModel' with your actual model
3. Customize the business logic
4. Add to your API class

EXAMPLE:

from django_autoapi import AutoAPI
from django_autoapi.decorators import endpoint
from myapp.models import Product

class ProductAPI(AutoAPI):
    model = Product

    filterable = ['category', 'is_active']
    searchable = ['name', 'description']
    orderable = ['name', 'price', 'created_at']

    # Pattern 1: Basic activation
    @endpoint(methods=['POST'], detail=True)
    def activate(self, request, instance):
        instance.is_active = True
        instance.save()
        return Response({'status': 'activated'})

    # Pattern 2: Statistics
    @endpoint(methods=['GET'], detail=False)
    def statistics(self, request, queryset):
        return Response({
            'total': queryset.count(),
            'active': queryset.filter(is_active=True).count()
        })

GENERATED URLS:

Standard CRUD:
    GET    /api/products/              - List
    POST   /api/products/              - Create
    GET    /api/products/{id}/         - Retrieve
    PUT    /api/products/{id}/         - Update
    PATCH  /api/products/{id}/         - Partial Update
    DELETE /api/products/{id}/         - Delete

Custom Endpoints:
    POST   /api/products/{id}/activate/     - Activate
    GET    /api/products/statistics/        - Statistics
"""
