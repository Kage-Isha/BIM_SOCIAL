from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class Profile(models.Model):
    """Extended user profile for BIM Social"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    location_verified = models.BooleanField(default=False)
    website = models.URLField(max_length=200, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        blank=True,
        null=True
    )
    cover_image = models.ImageField(
        upload_to='cover_images/', 
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # BIM-specific fields
    university = models.CharField(max_length=200, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    specialization = models.CharField(
        max_length=100, 
        choices=[
            ('architecture', 'Architecture'),
            ('civil_engineering', 'Civil Engineering'),
            ('mep', 'MEP Engineering'),
            ('structural', 'Structural Engineering'),
            ('project_management', 'Project Management'),
            ('quantity_surveying', 'Quantity Surveying'),
            ('other', 'Other'),
        ],
        blank=True,
        null=True
    )
    experience_level = models.CharField(
        max_length=50,
        choices=[
            ('student', 'Student'),
            ('entry', 'Entry Level'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='student'
    )
    
    # Social counts (denormalized for performance)
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_profile'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
    
    @property
    def profile_image_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return None  # Return None instead of broken default path


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Automatically create/update profile when user is created/updated"""
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        # Update existing profile if it exists
        if hasattr(instance, 'profile'):
            instance.profile.save()
