from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = [
        'bio', 'location', 'website', 'birth_date',
        'profile_image', 'cover_image', 'is_verified', 'is_private',
        'phone_number', 'university', 'graduation_year', 'specialization',
        'experience_level'
    ]


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'specialization', 'experience_level', 'followers_count', 'following_count', 'created_at']
    list_filter = ['specialization', 'experience_level', 'is_verified', 'is_private', 'created_at']
    search_fields = ['user__username', 'user__email', 'bio', 'university']
    readonly_fields = ['id', 'followers_count', 'following_count', 'posts_count', 'created_at', 'updated_at']


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
