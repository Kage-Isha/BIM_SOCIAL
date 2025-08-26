"""
Custom exceptions for BIM Social application
"""


class BIMSocialException(Exception):
    """Base exception for BIM Social application"""
    pass


class UserNotAuthenticatedException(BIMSocialException):
    """Raised when user is not authenticated"""
    pass


class PermissionDeniedException(BIMSocialException):
    """Raised when user doesn't have permission"""
    pass


class InvalidDataException(BIMSocialException):
    """Raised when invalid data is provided"""
    pass


class PostNotFoundException(BIMSocialException):
    """Raised when post is not found"""
    pass


class UserNotFoundException(BIMSocialException):
    """Raised when user is not found"""
    pass


class RateLimitExceededException(BIMSocialException):
    """Raised when rate limit is exceeded"""
    pass


class FileUploadException(BIMSocialException):
    """Raised when file upload fails"""
    pass
