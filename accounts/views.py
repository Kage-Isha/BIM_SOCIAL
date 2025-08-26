# All API views removed - functionality moved to web_views.py
# This app now only contains Django models and admin configuration
from django.contrib.auth.models import User
from .models import Profile
import logging

logger = logging.getLogger(__name__)
