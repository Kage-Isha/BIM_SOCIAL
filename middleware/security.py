"""
Production Security Middleware for BIM Social
Implements additional security layers beyond Django's built-in security features
"""

import logging
import time
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
User = get_user_model()


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent abuse
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip rate limiting for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
            
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Different rate limits for different endpoints
        rate_limits = {
            'login': (5, 300),  # 5 attempts per 5 minutes
            'register': (3, 3600),  # 3 attempts per hour
            'api': (100, 3600),  # 100 requests per hour for API
            'upload': (10, 3600),  # 10 uploads per hour
            'default': (200, 3600),  # 200 requests per hour default
        }
        
        # Determine rate limit type
        limit_type = 'default'
        if '/login/' in request.path:
            limit_type = 'login'
        elif '/register/' in request.path:
            limit_type = 'register'
        elif request.path.startswith('/api/'):
            limit_type = 'api'
        elif request.method == 'POST' and 'media' in str(request.FILES):
            limit_type = 'upload'
        
        max_requests, window = rate_limits[limit_type]
        
        # Check rate limit
        cache_key = f'rate_limit:{limit_type}:{ip}'
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= max_requests:
            logger.warning(f'Rate limit exceeded for IP {ip} on {limit_type}')
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': window
            }, status=429)
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, window)
        return None
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
            "img-src 'self' data: https: blob:",
            "media-src 'self' blob:",
            "connect-src 'self' ws: wss:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Remove server information
        if 'Server' in response:
            del response['Server']
        
        return response


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """
    Basic SQL injection detection and prevention
    """
    
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(--|#|/\*|\*/)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\b(CONCAT|CHAR|ASCII|SUBSTRING)\s*\()",
    ]
    
    def process_request(self, request):
        # Check GET parameters
        for key, value in request.GET.items():
            if self.contains_sql_injection(value):
                logger.critical(f'SQL injection attempt detected in GET parameter {key}: {value}')
                return HttpResponseForbidden('Malicious request detected')
        
        # Check POST parameters
        for key, value in request.POST.items():
            if isinstance(value, str) and self.contains_sql_injection(value):
                logger.critical(f'SQL injection attempt detected in POST parameter {key}: {value}')
                return HttpResponseForbidden('Malicious request detected')
        
        return None
    
    def contains_sql_injection(self, value):
        """Check if value contains potential SQL injection"""
        if not isinstance(value, str):
            return False
            
        value_upper = value.upper()
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False


class XSSProtectionMiddleware(MiddlewareMixin):
    """
    Basic XSS protection middleware
    """
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]
    
    def process_request(self, request):
        # Skip for file uploads
        if request.content_type and 'multipart/form-data' in request.content_type:
            return None
        
        # Check POST data for XSS
        for key, value in request.POST.items():
            if isinstance(value, str) and self.contains_xss(value):
                logger.warning(f'XSS attempt detected in POST parameter {key}')
                return HttpResponseForbidden('Malicious content detected')
        
        return None
    
    def contains_xss(self, value):
        """Check if value contains potential XSS"""
        if not isinstance(value, str):
            return False
            
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False


class LoginAttemptMiddleware(MiddlewareMixin):
    """
    Track and limit login attempts
    """
    
    def process_request(self, request):
        if request.path == '/login/' and request.method == 'POST':
            ip = self.get_client_ip(request)
            username = request.POST.get('username', '')
            
            # Track failed attempts by IP and username
            ip_key = f'login_attempts_ip:{ip}'
            user_key = f'login_attempts_user:{username}'
            
            ip_attempts = cache.get(ip_key, 0)
            user_attempts = cache.get(user_key, 0)
            
            # Block if too many attempts
            if ip_attempts >= 10 or user_attempts >= 5:
                logger.warning(f'Login blocked for IP {ip}, username {username}')
                return JsonResponse({
                    'error': 'Too many login attempts. Please try again later.',
                    'blocked': True
                }, status=429)
        
        return None
    
    def process_response(self, request, response):
        if request.path == '/login/' and request.method == 'POST':
            ip = self.get_client_ip(request)
            username = request.POST.get('username', '')
            
            # If login failed (status 400 or form errors)
            if response.status_code >= 400 or (hasattr(response, 'context_data') and 
                                               response.context_data and 
                                               'form' in response.context_data and 
                                               response.context_data['form'].errors):
                
                # Increment failed attempt counters
                ip_key = f'login_attempts_ip:{ip}'
                user_key = f'login_attempts_user:{username}'
                
                cache.set(ip_key, cache.get(ip_key, 0) + 1, 3600)  # 1 hour
                cache.set(user_key, cache.get(user_key, 0) + 1, 1800)  # 30 minutes
                
                logger.info(f'Failed login attempt from IP {ip} for username {username}')
            
            elif response.status_code == 200 or response.status_code == 302:
                # Successful login, clear counters
                ip_key = f'login_attempts_ip:{ip}'
                user_key = f'login_attempts_user:{username}'
                cache.delete(ip_key)
                cache.delete(user_key)
        
        return response
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FileUploadSecurityMiddleware(MiddlewareMixin):
    """
    Security checks for file uploads
    """
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.avi', '.mkv'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl', '.sh', '.ps1'
    }
    
    def process_request(self, request):
        if request.method == 'POST' and request.FILES:
            for field_name, uploaded_file in request.FILES.items():
                # Check file size
                if uploaded_file.size > self.MAX_FILE_SIZE:
                    logger.warning(f'File too large: {uploaded_file.name} ({uploaded_file.size} bytes)')
                    return JsonResponse({
                        'error': f'File too large. Maximum size is {self.MAX_FILE_SIZE // (1024*1024)}MB'
                    }, status=413)
                
                # Check file extension
                file_ext = self.get_file_extension(uploaded_file.name)
                
                if file_ext in self.DANGEROUS_EXTENSIONS:
                    logger.critical(f'Dangerous file upload attempt: {uploaded_file.name}')
                    return HttpResponseForbidden('File type not allowed')
                
                if file_ext not in self.ALLOWED_EXTENSIONS:
                    logger.warning(f'Disallowed file extension: {uploaded_file.name}')
                    return JsonResponse({
                        'error': f'File type not allowed. Allowed types: {", ".join(self.ALLOWED_EXTENSIONS)}'
                    }, status=400)
                
                # Check for embedded scripts in image files
                if file_ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
                    if self.contains_embedded_script(uploaded_file):
                        logger.critical(f'Malicious file detected: {uploaded_file.name}')
                        return HttpResponseForbidden('Malicious file detected')
        
        return None
    
    def get_file_extension(self, filename):
        """Get file extension in lowercase"""
        return '.' + filename.split('.')[-1].lower() if '.' in filename else ''
    
    def contains_embedded_script(self, uploaded_file):
        """Check for embedded scripts in image files"""
        try:
            # Read first 1KB to check for script tags
            uploaded_file.seek(0)
            content = uploaded_file.read(1024).decode('utf-8', errors='ignore')
            uploaded_file.seek(0)
            
            script_patterns = [
                r'<script[^>]*>',
                r'javascript:',
                r'on\w+\s*=',
                r'<?php',
                r'<%',
            ]
            
            for pattern in script_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
        except:
            # If we can't read the file, allow it but log
            logger.warning(f'Could not scan file for scripts: {uploaded_file.name}')
            return False


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log suspicious requests and security events
    """
    
    def process_request(self, request):
        # Log suspicious user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus', 'openvas',
            'burp', 'w3af', 'acunetix', 'appscan', 'webscarab'
        ]
        
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            logger.critical(f'Suspicious user agent detected: {user_agent} from IP {self.get_client_ip(request)}')
        
        # Log requests to sensitive paths
        sensitive_paths = [
            '/admin/', '/.env', '/config/', '/backup/', '/database/',
            '/phpMyAdmin/', '/wp-admin/', '/wp-config.php'
        ]
        
        if any(path in request.path for path in sensitive_paths):
            logger.warning(f'Access attempt to sensitive path: {request.path} from IP {self.get_client_ip(request)}')
        
        return None
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
