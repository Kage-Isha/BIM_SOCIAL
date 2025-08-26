#!/usr/bin/env python3
"""
BIM Social Setup Script
Automated setup and deployment script for production environment
"""

import os
import sys
import subprocess
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from django.db import connection
from django.core.management.color import color_style

User = get_user_model()
style = color_style()


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{style.HTTP_INFO('→')} {description}...")
    try:
        if isinstance(command, list):
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(f"{style.SUCCESS('✓')} {description} completed successfully")
            if result.stdout.strip():
                print(f"  Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{style.ERROR('✗')} {description} failed")
        print(f"  Error: {e.stderr}")
        return False


def check_dependencies():
    """Check if all required dependencies are installed"""
    print(f"\n{style.HTTP_INFO('='*50)}")
    print(f"{style.HTTP_INFO('CHECKING DEPENDENCIES')}")
    print(f"{style.HTTP_INFO('='*50)}")
    
    required_packages = [
        'django', 'djangorestframework', 'channels', 'redis',
        'pillow', 'python-decouple', 'dj-database-url',
        'django-cors-headers', 'django-redis', 'psycopg2-binary'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"{style.SUCCESS('✓')} {package}")
        except ImportError:
            print(f"{style.ERROR('✗')} {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n{style.ERROR('Missing packages detected!')}")
        print(f"Install them with: pip install {' '.join(missing_packages)}")
        return False
    
    print(f"\n{style.SUCCESS('All dependencies are installed!')}")
    return True


def setup_database():
    """Setup database and run migrations"""
    print(f"\n{style.HTTP_INFO('='*50)}")
    print(f"{style.HTTP_INFO('DATABASE SETUP')}")
    print(f"{style.HTTP_INFO('='*50)}")
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print(f"{style.SUCCESS('✓')} Database connection successful")
    except Exception as e:
        print(f"{style.ERROR('✗')} Database connection failed: {e}")
        return False
    
    # Make migrations
    print(f"\n{style.HTTP_INFO('Creating migrations...')}")
    apps = ['accounts', 'social', 'chat', 'notifications']
    
    for app in apps:
        if not run_command(f'python manage.py makemigrations {app}', f'Making migrations for {app}'):
            return False
    
    # Run migrations
    if not run_command('python manage.py migrate', 'Applying migrations'):
        return False
    
    return True


def collect_static():
    """Collect static files"""
    print(f"\n{style.HTTP_INFO('='*50)}")
    print(f"{style.HTTP_INFO('STATIC FILES')}")
    print(f"{style.HTTP_INFO('='*50)}")
    
    return run_command('python manage.py collectstatic --noinput', 'Collecting static files')


def create_superuser():
    """Create superuser if it doesn't exist"""
    print(f"\n{style.HTTP_INFO('='*50)}")
    print(f"{style.HTTP_INFO('SUPERUSER SETUP')}")
    print(f"{style.HTTP_INFO('='*50)}")
    
    if User.objects.filter(is_superuser=True).exists():
        print(f"{style.SUCCESS('✓')} Superuser already exists")
        return True
    
    print(f"{style.HTTP_INFO('Creating superuser...')}")
    
    # Try to create superuser from environment variables
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@bimsocial.com')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if admin_password:
        try:
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            print(f"{style.SUCCESS('✓')} Superuser created successfully")
            print(f"  Username: {admin_username}")
            print(f"  Email: {admin_email}")
            return True
        except Exception as e:
            print(f"{style.ERROR('✗')} Failed to create superuser: {e}")
            return False
    else:
        print(f"{style.WARNING('!')} No ADMIN_PASSWORD environment variable set")
        print(f"  Run 'python manage.py createsuperuser' manually after setup")
        return True


def setup_cache():
    """Setup and test cache"""
    print(f"\n{style.HTTP_INFO('='*50)}")
    print(f"{style.HTTP_INFO('CACHE SETUP')}")
    print(f"{style.HTTP_INFO('='*50)}")
    
    try:
        from django.core.cache import cache
        
        # Test cache
        cache.set('test_key', 'test_value', 30)
        if cache.get('test_key') == 'test_value':
            print(f"{style.SUCCESS('✓')} Cache is working properly")
            cache.delete('test_key')
            return True
        else:
            print(f"{style.ERROR('✗')} Cache test failed")
            return False
    except Exception as e:
        print(f"{style.ERROR('✗')} Cache setup failed: {e}")
        return False


def setup_channels():
    """Setup Django Channels"""
    print(f"\n{style.HTTP_INFO('='*50)}")
    print(f"{style.HTTP_INFO('CHANNELS SETUP')}")
    print(f"{style.HTTP_INFO('='*50)}")
    
    try:
        import channels
        from channels.layers import get_channel_layer
        
        # Test channel layer
        channel_layer = get_channel_layer()
        if channel_layer is None:
            print(f"{style.ERROR('✗')} Channel layer not configured")
            return False
        
        print(f"{style.SUCCESS('✓')} Django Channels configured properly")
        return True
    except Exception as e:
        print(f"{style.ERROR('✗')} Channels setup failed: {e}")
        return False


def run_tests():
    """Run basic tests"""
    print(f"\n{style.HTTP_INFO('='*50)}")
    print(f"{style.HTTP_INFO('RUNNING TESTS')}")
    print(f"{style.HTTP_INFO('='*50)}")
    
    return run_command('python manage.py test --verbosity=1', 'Running tests')


def main():
    """Main setup function"""
    print(f"{style.SUCCESS('='*60)}")
    print(f"{style.SUCCESS('BIM SOCIAL - PRODUCTION SETUP')}")
    print(f"{style.SUCCESS('='*60)}")
    
    steps = [
        ("Dependencies", check_dependencies),
        ("Database", setup_database),
        ("Static Files", collect_static),
        ("Superuser", create_superuser),
        ("Cache", setup_cache),
        ("Channels", setup_channels),
    ]
    
    # Add tests if not in production
    if not os.getenv('SKIP_TESTS', '').lower() in ['true', '1', 'yes']:
        steps.append(("Tests", run_tests))
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"{style.ERROR('✗')} {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    # Summary
    print(f"\n{style.HTTP_INFO('='*60)}")
    print(f"{style.HTTP_INFO('SETUP SUMMARY')}")
    print(f"{style.HTTP_INFO('='*60)}")
    
    if failed_steps:
        print(f"{style.ERROR('Setup completed with errors!')}")
        print(f"{style.ERROR('Failed steps:')} {', '.join(failed_steps)}")
        print(f"\n{style.WARNING('Please fix the issues above before deploying to production.')}")
        return 1
    else:
        print(f"{style.SUCCESS('✓ Setup completed successfully!')}")
        print(f"\n{style.SUCCESS('Your BIM Social application is ready for production!')}")
        print(f"\nNext steps:")
        print(f"  1. Configure your web server (Nginx/Apache)")
        print(f"  2. Set up process manager (Gunicorn + Daphne)")
        print(f"  3. Configure SSL certificates")
        print(f"  4. Set up monitoring and logging")
        print(f"  5. Configure backups")
        return 0


if __name__ == '__main__':
    sys.exit(main())
