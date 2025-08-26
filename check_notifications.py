#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from notifications.models import Notification
from django.contrib.auth.models import User

print("=== NOTIFICATION DEBUG ===")
print(f"Total notifications: {Notification.objects.count()}")
print(f"Total users: {User.objects.count()}")

print("\n=== ALL NOTIFICATIONS ===")
for n in Notification.objects.all():
    print(f"  {n.sender.username} -> {n.recipient.username}: {n.message} (Read: {n.is_read})")

print("\n=== RECENT FOLLOW NOTIFICATIONS ===")
follow_notifications = Notification.objects.filter(notification_type='follow').order_by('-created_at')
for n in follow_notifications:
    print(f"  {n.created_at}: {n.sender.username} -> {n.recipient.username}: {n.title} - {n.message}")

print("\n=== USERS ===")
for user in User.objects.all():
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    print(f"  {user.username}: {unread_count} unread notifications")
