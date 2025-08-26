#!/usr/bin/env python
"""
Force clear browser cache by adding timestamp to all static resources
"""
import os
import sys
import django
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from django.conf import settings

# Create a cache-busting timestamp
cache_bust = str(int(datetime.now().timestamp()))

print(f"Cache-busting timestamp: {cache_bust}")

# Update settings to include cache busting
cache_bust_file = os.path.join(settings.BASE_DIR, 'cache_bust.txt')
with open(cache_bust_file, 'w') as f:
    f.write(cache_bust)

print(f"Cache-busting file created: {cache_bust_file}")
print("Restart your Django server to apply changes.")
