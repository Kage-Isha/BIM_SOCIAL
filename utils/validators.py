"""
Custom validators for BIM Social application
"""
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re


def validate_username(value):
    """Validate username format"""
    if len(value) < 3:
        raise ValidationError('Username must be at least 3 characters long.')
    if len(value) > 30:
        raise ValidationError('Username must be less than 30 characters.')
    if not re.match(r'^[a-zA-Z0-9_]+$', value):
        raise ValidationError('Username can only contain letters, numbers, and underscores.')


def validate_phone_number(value):
    """Validate phone number format"""
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_regex(value)


def validate_file_size(value):
    """Validate file size (max 10MB)"""
    filesize = value.size
    if filesize > 10485760:  # 10MB
        raise ValidationError("The maximum file size that can be uploaded is 10MB")


def validate_image_file(value):
    """Validate image file type and size"""
    validate_file_size(value)
    
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    extension = value.name.split('.')[-1].lower()
    
    if extension not in valid_extensions:
        raise ValidationError(f'Unsupported file extension. Allowed: {", ".join(valid_extensions)}')


def validate_video_file(value):
    """Validate video file type and size"""
    # Max 50MB for videos
    filesize = value.size
    if filesize > 52428800:  # 50MB
        raise ValidationError("The maximum video file size that can be uploaded is 50MB")
    
    valid_extensions = ['mp4', 'avi', 'mov', 'wmv', 'webm']
    extension = value.name.split('.')[-1].lower()
    
    if extension not in valid_extensions:
        raise ValidationError(f'Unsupported video format. Allowed: {", ".join(valid_extensions)}')
