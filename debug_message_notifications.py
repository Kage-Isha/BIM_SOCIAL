#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from notifications.models import Notification
from django.contrib.auth.models import User

print("=== Message Notifications Debug ===")
print(f"Total notifications: {Notification.objects.count()}")
print(f"Message notifications: {Notification.objects.filter(notification_type='message').count()}")

try:
    ram = User.objects.get(username='ramm')
    shyam = User.objects.get(username='shyam')
    
    print(f"\nRam's notifications: {Notification.objects.filter(recipient=ram).count()}")
    print(f"Shyam's notifications: {Notification.objects.filter(recipient=shyam).count()}")
    
    # Show recent message notifications
    message_notifications = Notification.objects.filter(
        notification_type='message'
    ).order_by('-created_at')[:5]
    
    print(f"\nRecent message notifications:")
    for notif in message_notifications:
        print(f"- {notif.sender.username} -> {notif.recipient.username}: {notif.message}")
        
except User.DoesNotExist as e:
    print(f"User not found: {e}")
