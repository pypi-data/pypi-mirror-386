"""
Utility functions untuk AutoAPI
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied


class EndpointResponse:
    """
    Helper class untuk consistent response formatting
    
    Usage:
        # Success response
        return EndpointResponse.success(data={'status': 'ok'})
        
        # Error response
        return EndpointResponse.error('Invalid data', status=400)
        
        # Success with serializer
        return EndpointResponse.success_with_serializer(instance, serializer)
    """
    
    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        """
        Create success response
        
        Args:
            data: Response data
            message: Optional success message
            status_code: HTTP status code
        
        Returns:
            Response object
        """
        response_data = {}
        
        if message:
            response_data['message'] = message
        
        if data is not None:
            response_data['data'] = data
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Create error response
        
        Args:
            message: Error message
            errors: Optional detailed errors
            status_code: HTTP status code
        
        Returns:
            Response object
        """
        response_data = {
            'error': message
        }
        
        if errors:
            response_data['details'] = errors
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def success_with_serializer(instance, serializer_class):
        """
        Create success response dengan serialized data
        
        Args:
            instance: Model instance
            serializer_class: Serializer class
        
        Returns:
            Response object
        """
        serializer = serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @staticmethod
    def created(data=None, message='Created successfully'):
        """
        Create 201 Created response
        
        Args:
            data: Response data
            message: Success message
        
        Returns:
            Response object
        """
        return EndpointResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED
        )
    
    @staticmethod
    def no_content():
        """
        Create 204 No Content response
        
        Returns:
            Response object
        """
        return Response(status=status.HTTP_204_NO_CONTENT)


class EndpointValidation:
    """
    Helper class untuk validation di custom endpoints
    
    Usage:
        @endpoint(methods=['POST'], detail=True)
        def graduate(self, request, instance):
            # Validate
            EndpointValidation.require_fields(request.data, ['date', 'certificate'])
            EndpointValidation.validate_status(instance, 'active', 'Can only graduate active students')
            
            instance.graduate()
            return Response({'status': 'graduated'})
    """
    
    @staticmethod
    def require_fields(data, required_fields):
        """
        Validate required fields in request data
        
        Args:
            data: Request data
            required_fields: List of required field names
        
        Raises:
            ValidationError: If required fields missing
        """
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            raise ValidationError({
                'error': 'Missing required fields',
                'missing_fields': missing
            })
    
    @staticmethod
    def validate_status(instance, expected_status, error_message=None):
        """
        Validate instance status
        
        Args:
            instance: Model instance
            expected_status: Expected status value
            error_message: Custom error message
        
        Raises:
            ValidationError: If status doesn't match
        """
        if not hasattr(instance, 'status'):
            return
        
        if instance.status != expected_status:
            message = error_message or f"Expected status '{expected_status}', got '{instance.status}'"
            raise ValidationError(message)
    
    @staticmethod
    def validate_not_status(instance, forbidden_status, error_message=None):
        """
        Validate instance is NOT in certain status
        
        Args:
            instance: Model instance
            forbidden_status: Forbidden status value
            error_message: Custom error message
        
        Raises:
            ValidationError: If status matches forbidden
        """
        if not hasattr(instance, 'status'):
            return
        
        if instance.status == forbidden_status:
            message = error_message or f"Cannot perform action when status is '{forbidden_status}'"
            raise ValidationError(message)
    
    @staticmethod
    def validate_condition(condition, error_message):
        """
        Generic condition validator
        
        Args:
            condition: Boolean condition
            error_message: Error message if condition is False
        
        Raises:
            ValidationError: If condition is False
        """
        if not condition:
            raise ValidationError(error_message)
    
    @staticmethod
    def check_permission(user, permission, error_message=None):
        """
        Check user permission
        
        Args:
            user: User object
            permission: Permission string (e.g., 'app.permission_name')
            error_message: Custom error message
        
        Raises:
            PermissionDenied: If user doesn't have permission
        """
        if not user.has_perm(permission):
            message = error_message or f"Permission denied: {permission}"
            raise PermissionDenied(message)


def handle_endpoint_errors(func):
    """
    Decorator untuk handle common errors di custom endpoints
    
    Usage:
        @endpoint(methods=['POST'], detail=True)
        @handle_endpoint_errors
        def graduate(self, request, instance):
            instance.graduate()  # May raise ValueError, etc
            return Response({'status': 'graduated'})
    
    Automatically handles:
    - ValidationError -> 400 Bad Request
    - PermissionDenied -> 403 Forbidden
    - ValueError -> 400 Bad Request
    - Exception -> 500 Internal Server Error
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return EndpointResponse.error(
                message=str(e),
                errors=e.detail if hasattr(e, 'detail') else None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return EndpointResponse.error(
                message=str(e),
                status_code=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return EndpointResponse.error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Log the error (in production)
            # logger.exception("Unexpected error in endpoint")
            
            return EndpointResponse.error(
                message='An unexpected error occurred',
                errors={'detail': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper

