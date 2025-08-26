#!/usr/bin/env python
"""
Script to create superuser programmatically
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    username = 'admin'
    email = 'admin@bimsocial.com'
    password = 'admin123'
    
    if User.objects.filter(username=username).exists():
        print(f"Superuser '{username}' already exists!")
        return
    
    # Create user without triggering signals that might cause conflicts
    user = User(
        username=username,
        email=email,
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    user.set_password(password)
    user.save()
    
    # Ensure profile exists
    from accounts.models import Profile
    Profile.objects.get_or_create(user=user)
    
    print(f"Superuser created successfully!")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Login at: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    create_superuser()
