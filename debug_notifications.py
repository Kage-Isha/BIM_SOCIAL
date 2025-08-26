#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from notifications.models import Notification
from django.contrib.auth.models import User

print("=== NOTIFICATION DEBUG ===")
print(f"Total notifications: {Notification.objects.count()}")

print("\n=== ALL NOTIFICATIONS ===")
for n in Notification.objects.all().order_by('-created_at'):
    print(f"{n.sender.username} -> {n.recipient.username}: {n.title}")
    print(f"  Message: {n.message}")
    print(f"  Read: {n.is_read}")
    print(f"  Created: {n.created_at}")
    print("---")

print("\n=== USERS AND THEIR UNREAD NOTIFICATIONS ===")
for user in User.objects.all():
    unread = Notification.objects.filter(recipient=user, is_read=False).count()
    total = Notification.objects.filter(recipient=user).count()
    print(f"{user.username}: {unread} unread / {total} total")
