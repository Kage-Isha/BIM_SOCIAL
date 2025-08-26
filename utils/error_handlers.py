"""
Error Handlers and Custom Exception Classes for BIM Social
Production-ready error handling with logging and user-friendly responses
"""

import logging
import traceback
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import DatabaseError, IntegrityError
# DRF imports removed - using Django views only
from channels.exceptions import DenyConnection

logger = logging.getLogger(__name__)


class BIMSocialException(Exception):
    """Base exception class for BIM Social application"""
    
    def __init__(self, message, error_code=None, status_code=400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(BIMSocialException):
    """Raised when validation fails"""
    
    def __init__(self, message, field=None):
        self.field = field
        super().__init__(message, error_code='VALIDATION_ERROR', status_code=400)


class AuthenticationException(BIMSocialException):
    """Raised when authentication fails"""
    
    def __init__(self, message="Authentication required"):
        super().__init__(message, error_code='AUTH_ERROR', status_code=401)


class AuthorizationException(BIMSocialException):
    """Raised when authorization fails"""
    
    def __init__(self, message="Permission denied"):
        super().__init__(message, error_code='PERMISSION_ERROR', status_code=403)


class ResourceNotFoundException(BIMSocialException):
    """Raised when a resource is not found"""
    
    def __init__(self, message="Resource not found", resource_type=None):
        self.resource_type = resource_type
        super().__init__(message, error_code='NOT_FOUND', status_code=404)


class RateLimitException(BIMSocialException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message="Rate limit exceeded", retry_after=None):
        self.retry_after = retry_after
        super().__init__(message, error_code='RATE_LIMIT', status_code=429)


class FileUploadException(BIMSocialException):
    """Raised when file upload fails"""
    
    def __init__(self, message="File upload failed", file_type=None):
        self.file_type = file_type
        super().__init__(message, error_code='UPLOAD_ERROR', status_code=400)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    request = context.get('request')
    user = getattr(request, 'user', None)
    
    logger.error(
        f"API Exception: {exc.__class__.__name__}: {str(exc)}",
        extra={
            'exception': exc,
            'request_path': getattr(request, 'path', 'Unknown'),
            'request_method': getattr(request, 'method', 'Unknown'),
            'user_id': getattr(user, 'id', None) if user and user.is_authenticated else None,
            'ip_address': get_client_ip(request) if request else None,
        },
        exc_info=True
    )
    
    # Handle custom exceptions
    if isinstance(exc, BIMSocialException):
        custom_response_data = {
            'error': {
                'message': exc.message,
                'code': exc.error_code,
                'type': exc.__class__.__name__
            }
        }
        
        if hasattr(exc, 'field') and exc.field:
            custom_response_data['error']['field'] = exc.field
        
        if hasattr(exc, 'retry_after') and exc.retry_after:
            custom_response_data['error']['retry_after'] = exc.retry_after
        
        return Response(custom_response_data, status=exc.status_code)
    
    # Handle Django exceptions
    if isinstance(exc, ValidationError):
        return Response({
            'error': {
                'message': 'Validation failed',
                'code': 'VALIDATION_ERROR',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if isinstance(exc, PermissionDenied):
        return Response({
            'error': {
                'message': 'Permission denied',
                'code': 'PERMISSION_DENIED'
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    if isinstance(exc, (DatabaseError, IntegrityError)):
        return Response({
            'error': {
                'message': 'Database error occurred',
                'code': 'DATABASE_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # If response is None, create a generic error response
    if response is None:
        return Response({
            'error': {
                'message': 'An unexpected error occurred',
                'code': 'INTERNAL_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Customize the response data
    if response.data:
        custom_response_data = {
            'error': {
                'message': 'Request failed',
                'code': 'REQUEST_ERROR',
                'details': response.data
            }
        }
        response.data = custom_response_data
    
    return response


def handle_404(request, exception=None):
    """Custom 404 error handler"""
    logger.warning(
        f"404 Error: {request.path}",
        extra={
            'request_path': request.path,
            'request_method': request.method,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': get_client_ip(request),
        }
    )
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': {
                'message': 'Endpoint not found',
                'code': 'NOT_FOUND'
            }
        }, status=404)
    
    return render(request, 'errors/404.html', status=404)


def handle_500(request):
    """Custom 500 error handler"""
    logger.error(
        f"500 Error: {request.path}",
        extra={
            'request_path': request.path,
            'request_method': request.method,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': get_client_ip(request),
        },
        exc_info=True
    )
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': {
                'message': 'Internal server error',
                'code': 'INTERNAL_ERROR'
            }
        }, status=500)
    
    return render(request, 'errors/500.html', status=500)


def handle_403(request, exception=None):
    """Custom 403 error handler"""
    logger.warning(
        f"403 Error: {request.path}",
        extra={
            'request_path': request.path,
            'request_method': request.method,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': get_client_ip(request),
        }
    )
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': {
                'message': 'Permission denied',
                'code': 'PERMISSION_DENIED'
            }
        }, status=403)
    
    return render(request, 'errors/403.html', status=403)


def handle_400(request, exception=None):
    """Custom 400 error handler"""
    logger.warning(
        f"400 Error: {request.path}",
        extra={
            'request_path': request.path,
            'request_method': request.method,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': get_client_ip(request),
        }
    )
    
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': {
                'message': 'Bad request',
                'code': 'BAD_REQUEST'
            }
        }, status=400)
    
    return render(request, 'errors/400.html', status=400)


def get_client_ip(request):
    """Get the real client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ErrorReportingMiddleware:
    """
    Middleware to catch and report unhandled exceptions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Process unhandled exceptions"""
        # Log the exception with context
        logger.error(
            f"Unhandled Exception: {exception.__class__.__name__}: {str(exception)}",
            extra={
                'exception': exception,
                'request_path': request.path,
                'request_method': request.method,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'ip_address': get_client_ip(request),
                'request_data': self._get_request_data(request),
            },
            exc_info=True
        )
        
        # Send error notification in production
        if not settings.DEBUG:
            self._send_error_notification(request, exception)
        
        return None  # Let Django handle the response
    
    def _get_request_data(self, request):
        """Get sanitized request data for logging"""
        data = {}
        
        # GET parameters
        if request.GET:
            data['GET'] = dict(request.GET)
        
        # POST parameters (sanitized)
        if request.POST:
            post_data = dict(request.POST)
            # Remove sensitive fields
            sensitive_fields = ['password', 'token', 'secret', 'key']
            for field in sensitive_fields:
                if field in post_data:
                    post_data[field] = '[REDACTED]'
            data['POST'] = post_data
        
        # Headers (sanitized)
        headers = {}
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                if 'authorization' in header_name.lower() or 'token' in header_name.lower():
                    headers[header_name] = '[REDACTED]'
                else:
                    headers[header_name] = value
        data['headers'] = headers
        
        return data
    
    def _send_error_notification(self, request, exception):
        """Send error notification to administrators"""
        try:
            # This could be extended to send emails, Slack notifications, etc.
            pass
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")


def log_security_event(event_type, message, request=None, user=None, severity='WARNING'):
    """
    Log security-related events
    """
    extra_data = {
        'event_type': event_type,
        'severity': severity,
    }
    
    if request:
        extra_data.update({
            'request_path': request.path,
            'request_method': request.method,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        })
    
    if user:
        extra_data['user_id'] = user.id
        extra_data['username'] = user.username
    
    security_logger = logging.getLogger('security')
    
    if severity == 'CRITICAL':
        security_logger.critical(message, extra=extra_data)
    elif severity == 'ERROR':
        security_logger.error(message, extra=extra_data)
    elif severity == 'WARNING':
        security_logger.warning(message, extra=extra_data)
    else:
        security_logger.info(message, extra=extra_data)


def handle_websocket_error(consumer, error):
    """
    Handle WebSocket errors in Channels consumers
    """
    logger.error(
        f"WebSocket Error in {consumer.__class__.__name__}: {str(error)}",
        extra={
            'consumer': consumer.__class__.__name__,
            'channel_name': getattr(consumer, 'channel_name', 'Unknown'),
            'user_id': getattr(consumer.scope.get('user'), 'id', None) if consumer.scope.get('user') else None,
        },
        exc_info=True
    )
    
    # Send error message to client
    try:
        consumer.send_json({
            'type': 'error',
            'message': 'An error occurred. Please try again.',
            'code': 'WEBSOCKET_ERROR'
        })
    except Exception as e:
        logger.error(f"Failed to send WebSocket error message: {e}")


class DatabaseErrorHandler:
    """
    Handle database-related errors
    """
    
    @staticmethod
    def handle_integrity_error(error, model_name=None):
        """Handle database integrity errors"""
        error_message = str(error)
        
        if 'UNIQUE constraint failed' in error_message or 'duplicate key' in error_message:
            field = DatabaseErrorHandler._extract_field_from_error(error_message)
            message = f"A record with this {field} already exists" if field else "This record already exists"
            raise ValidationException(message, field=field)
        
        elif 'NOT NULL constraint failed' in error_message:
            field = DatabaseErrorHandler._extract_field_from_error(error_message)
            message = f"The {field} field is required" if field else "Required field is missing"
            raise ValidationException(message, field=field)
        
        elif 'FOREIGN KEY constraint failed' in error_message:
            raise ValidationException("Referenced record does not exist")
        
        else:
            logger.error(f"Database integrity error: {error}", exc_info=True)
            raise BIMSocialException("Database constraint violation", status_code=400)
    
    @staticmethod
    def _extract_field_from_error(error_message):
        """Extract field name from database error message"""
        import re
        
        # Try to extract field name from common error patterns
        patterns = [
            r'UNIQUE constraint failed: \w+\.(\w+)',
            r'NOT NULL constraint failed: \w+\.(\w+)',
            r'duplicate key value violates unique constraint ".*_(\w+)_',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1)
        
        return None
