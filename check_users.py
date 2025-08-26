#!/usr/bin/env python
"""
Quick script to check registered users in the database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

def check_users():
    print("=== USER REGISTRATION CHECK ===")
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Profiles: {Profile.objects.count()}")
    print("\n--- Recent Users ---")
    
    users = User.objects.all().order_by('-date_joined')[:5]
    for user in users:
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Date Joined: {user.date_joined}")
        print(f"Has Profile: {hasattr(user, 'profile')}")
        if hasattr(user, 'profile'):
            print(f"Profile ID: {user.profile.id}")
            print(f"Experience Level: {user.profile.experience_level}")
        print("-" * 30)

if __name__ == "__main__":
    check_users()
