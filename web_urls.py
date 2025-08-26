"""
URL configuration for web views (Django templates)
"""
from django.urls import path
import web_views

urlpatterns = [
    # Authentication
    path('', web_views.home_view, name='home'),
    path('about/', web_views.about_view, name='about'),
    path('login/', web_views.login_view, name='login'),
    path('register/', web_views.register_view, name='register'),
    path('logout/', web_views.logout_view, name='logout'),
    
    # Main pages
    path('feed/', web_views.feed_view, name='feed'),
    path('explore/', web_views.explore_view, name='explore'),
    path('notifications/', web_views.notifications_view, name='notifications'),
    path('messages/', web_views.messages_view, name='messages'),
    path('start-conversation/<str:username>/', web_views.start_conversation, name='start_conversation'),
    path('conversation/<uuid:conversation_id>/', web_views.conversation_detail_view, name='conversation_detail'),
    path('send-message/<uuid:conversation_id>/', web_views.send_message, name='send_message'),
    path('settings/', web_views.settings_view, name='settings'),
    
    # Profile and posts
    path('profile/<str:username>/', web_views.profile_view, name='profile'),
    path('post/<uuid:post_id>/', web_views.post_detail_view, name='post_detail'),
    path('edit-post/<uuid:post_id>/', web_views.edit_post_view, name='edit_post'),
    
    # Django form endpoints
    path('like/<uuid:post_id>/', web_views.toggle_like_view, name='toggle_like'),
    path('follow/<str:username>/', web_views.toggle_follow_view, name='toggle_follow'),
    path('comment/<uuid:post_id>/', web_views.add_comment_view, name='add_comment'),
    path('create-post/', web_views.create_post_view, name='create_post'),
    path('save/<uuid:post_id>/', web_views.toggle_save_view, name='toggle_save'),
]
