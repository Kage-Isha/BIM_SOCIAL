from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from social.models import Post, Follow
from accounts.models import Profile
from notifications.models import Notification
from chat.models import Conversation, ConversationMember, Message, MessageRead
import logging

logger = logging.getLogger(__name__)
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone
from datetime import timedelta

def home_view(request):
    """Home page - show landing page for all users"""
    return render(request, 'home.html')

def about_view(request):
    """About Us page"""
    return render(request, 'about.html')

@login_required
def explore_view(request):
    """Explore/Discovery page for posts"""
    posts = Post.objects.filter(is_public=True).select_related('user', 'user__profile').prefetch_related(
        'likes', 'comments', 'comments__user'
    ).annotate(
        is_liked=Exists(
            Post.objects.filter(id=OuterRef('id'), likes__user=request.user)
        ),
        is_saved=Exists(
            Post.objects.filter(id=OuterRef('id'), saved_by__user=request.user)
        ),
        is_following_author=Exists(
            Follow.objects.filter(follower=request.user, following=OuterRef('user'))
        )
    ).order_by('-created_at')
    
    # Apply filters
    filter_type = request.GET.get('filter', 'trending')
    if filter_type == 'popular':
        posts = posts.order_by('-likes_count', '-created_at')
    elif filter_type == 'recent':
        posts = posts.order_by('-created_at')
    else:  # trending
        # Simple trending algorithm based on recent engagement
        week_ago = timezone.now() - timedelta(days=7)
        posts = posts.filter(created_at__gte=week_ago).order_by('-likes_count', '-comments_count', '-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        posts = posts.filter(
            Q(caption__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Add recent comments to each post without affecting like counts
    for post in posts:
        post.recent_comments = list(post.comments.select_related('user', 'user__profile').order_by('-created_at')[:2])
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    return render(request, 'social/explore.html', {'posts': posts})

@login_required
def notifications_view(request):
    """Notifications page"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'sender__profile').order_by('-created_at')
    
    # Mark all as read
    notifications.filter(is_read=False).update(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)
    
    return render(request, 'notifications/notifications.html', {'notifications': notifications})

@login_required
def profile_view(request, username):
    """User profile page"""
    user = get_object_or_404(User, username=username)
    profile = user.profile
    
    # Get user's posts
    posts = Post.objects.filter(user=user, is_public=True).order_by('-created_at')
    
    # Check if current user follows this user
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    
    # Get followers and following counts
    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    
    # Pagination for posts
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'profile_user': user,
        'profile': profile,
        'posts': posts,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_own_profile': request.user == user,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_post_view(request, post_id):
    """Edit post page"""
    post = get_object_or_404(Post, id=post_id, user=request.user)
    
    if request.method == 'POST':
        caption = request.POST.get('caption', '').strip()
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        
        # Update post
        post.caption = caption
        if image:
            post.image = image
            post.video = None  # Clear video if image is uploaded
        elif video:
            post.video = video
            post.image = None  # Clear image if video is uploaded
        
        post.save()
        messages.success(request, 'Post updated successfully!')
        return redirect('post_detail', post_id=post.id)
    
    return render(request, 'social/edit_post.html', {'post': post})

def login_view(request):
    """Login page and authentication"""
    # Allow access to login page even if authenticated (for debugging)
    # if request.user.is_authenticated:
    #     return redirect('feed')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')

def register_view(request):
    """Registration page and user creation"""
    if request.user.is_authenticated:
        return redirect('feed')
    
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Profile data
        bio = request.POST.get('bio', '')
        location = request.POST.get('location', '')
        university = request.POST.get('university', '')
        specialization = request.POST.get('specialization')
        experience_level = request.POST.get('experience_level')
        profile_image = request.FILES.get('profile_image')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'auth/register.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Get or create profile (signal should handle this, but ensure it exists)
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Update profile with additional data
            profile.bio = bio
            profile.location = location
            profile.university = university
            profile.specialization = specialization
            profile.experience_level = experience_level
            if profile_image:
                profile.profile_image = profile_image
            profile.save()
            
            # Login user
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to BIM Social!')
            return redirect('feed')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def feed_view(request):
    """Main feed page showing posts from followed users"""
    # Get posts from followed users and own posts
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    posts_query = Post.objects.filter(
        Q(user__in=following_users) | Q(user=request.user)
    ).select_related('user', 'user__profile').prefetch_related(
        'likes', 'comments', 'comments__user'
    ).annotate(
        is_liked=Exists(
            Post.objects.filter(id=OuterRef('id'), likes__user=request.user)
        ),
        is_saved=Exists(
            Post.objects.filter(id=OuterRef('id'), saved_by__user=request.user)
        ),
        is_following_author=Exists(
            Follow.objects.filter(follower=request.user, following=OuterRef('user'))
        )
    ).order_by('-created_at')
    
    # Add recent comments to each post
    for post in posts_query:
        post.recent_comments = post.comments.select_related('user', 'user__profile').order_by('-created_at')[:2]
    
    # Pagination
    paginator = Paginator(posts_query, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    return render(request, 'social/feed.html', {'posts': posts})




@login_required
def messages_view(request):
    """Messages/Chat page"""
    # Get user's conversations
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'participants__profile', 'messages').order_by('-updated_at')
    
    # Get mutual followers for new conversations
    from social.models import Follow
    
    # Users who follow current user
    user_followers = Follow.objects.filter(following=request.user).values_list('follower', flat=True)
    
    # Users current user follows who also follow back (mutual)
    mutual_followers = User.objects.filter(
        id__in=Follow.objects.filter(
            follower=request.user,
            following__in=user_followers
        ).values_list('following', flat=True)
    ).select_related('profile')
    
    context = {
        'conversations': conversations,
        'mutual_followers': mutual_followers,
    }
    
    return render(request, 'chat/messages.html', context)

@login_required
@require_http_methods(["POST"])
def start_conversation(request, username):
    """Start a new conversation with a user"""
    try:
        other_user = get_object_or_404(User, username=username)
        
        # Check if they are mutual followers
        is_mutual = (
            Follow.objects.filter(follower=request.user, following=other_user).exists() and
            Follow.objects.filter(follower=other_user, following=request.user).exists()
        )
        
        if not is_mutual:
            messages.error(request, 'You can only start conversations with mutual followers.')
            return redirect('messages')
        
        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if existing_conversation:
            messages.info(request, f'Conversation with {other_user.username} already exists.')
            return redirect('conversation_detail', conversation_id=existing_conversation.id)
        
        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        
        # Create conversation members
        ConversationMember.objects.create(conversation=conversation, user=request.user)
        ConversationMember.objects.create(conversation=conversation, user=other_user)
        
        messages.success(request, f'Started conversation with {other_user.username}!')
        return redirect('conversation_detail', conversation_id=conversation.id)
        
    except Exception as e:
        logger.error(f"Start conversation error: {str(e)}")
        messages.error(request, 'Failed to start conversation.')
        return redirect('messages')

@login_required
def conversation_detail_view(request, conversation_id):
    """View conversation details and messages"""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user).prefetch_related(
            'messages__read_by',
            'messages__sender',
            'messages__sender__profile'
        ),
        id=conversation_id
    )
    
    # Mark messages as read
    unread_messages = conversation.messages.exclude(sender=request.user).exclude(
        read_by__user=request.user
    )
    for message in unread_messages:
        MessageRead.objects.get_or_create(message=message, user=request.user)
    
    return render(request, 'chat/conversation_detail.html', {'conversation': conversation})

@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, 'Message cannot be empty.')
        return redirect('conversation_detail', conversation_id=conversation_id)
    
    # Verify mutual followers
    other_participant = conversation.participants.exclude(id=request.user.id).first()
    if other_participant:
        is_mutual = (
            Follow.objects.filter(follower=request.user, following=other_participant).exists() and
            Follow.objects.filter(follower=other_participant, following=request.user).exists()
        )
        if not is_mutual:
            messages.error(request, 'You can only message mutual followers.')
            return redirect('messages')
    
    # Create message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content
    )
    
    # Update conversation metadata
    conversation.last_message = content
    conversation.last_message_at = message.created_at
    conversation.last_message_by = request.user
    conversation.updated_at = timezone.now()
    conversation.save()
    
    # Mark as read for sender
    MessageRead.objects.get_or_create(message=message, user=request.user)
    
    # Create notification for recipient
    if other_participant:
        Notification.objects.create(
            recipient=other_participant,
            sender=request.user,
            notification_type='message',
            title='New Message',
            message=f'{request.user.username} sent you a message: {content[:50]}{"..." if len(content) > 50 else ""}'
        )
    
    return redirect('conversation_detail', conversation_id=conversation_id)

@login_required
def post_detail_view(request, post_id):
    """Individual post detail page"""
    post = get_object_or_404(Post, id=post_id)
    
    # Annotate post with user-specific data
    post.comments_count = post.comments.count()
    post.is_liked = post.likes.filter(user=request.user).exists()
    post.is_saved = post.saved_by.filter(user=request.user).exists()
    post.is_following_author = Follow.objects.filter(
        follower=request.user, following=post.user
    ).exists() if post.user != request.user else False
    
    # Get comments with pagination
    comments = post.comments.select_related('user', 'user__profile').order_by('-created_at')
    paginator = Paginator(comments, 20)
    page_number = request.GET.get('page')
    comments_page = paginator.get_page(page_number)
    
    context = {
        'post': post,
        'comments': comments_page,
    }
    
    return render(request, 'social/post_detail.html', context)

@login_required
def settings_view(request):
    """User settings page"""
    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update profile - ensure profile exists
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        profile.university = request.POST.get('university', '')
        profile.specialization = request.POST.get('specialization', '')
        profile.experience_level = request.POST.get('experience_level', '')
        
        # Handle profile image upload
        if request.FILES.get('profile_image'):
            profile.profile_image = request.FILES['profile_image']
            print(f"Profile image uploaded: {profile.profile_image.name}")  # Debug log
        
        profile.save()
        print(f"Profile saved. Image field: {profile.profile_image}")  # Debug log
        messages.success(request, 'Settings updated successfully!')
        return redirect('profile', username=request.user.username)
        
    return render(request, 'settings/profile.html')

# Django Form Views for social interactions
@login_required
@require_http_methods(["POST"])
def toggle_like_view(request, post_id):
    """Django form view to toggle like on a post"""
    try:
        from social.models import Like
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            like.delete()
            # Use F() to avoid race conditions
            Post.objects.filter(id=post_id).update(likes_count=models.F('likes_count') - 1)
            messages.success(request, 'Post unliked!')
        else:
            # Use F() to avoid race conditions
            Post.objects.filter(id=post_id).update(likes_count=models.F('likes_count') + 1)
            messages.success(request, 'Post liked!')
        
        # Refresh the post object to get the updated like count
        post.refresh_from_db()
        
        # Redirect back to the referring page
        return redirect(request.META.get('HTTP_REFERER', 'feed'))
        
    except Exception as e:
        messages.error(request, f'Error liking post: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'feed'))

@login_required
@require_http_methods(["POST"])
def toggle_follow_view(request, username):
    """Django form view to toggle follow for a user"""
    try:
        user_to_follow = get_object_or_404(User, username=username)
        
        if user_to_follow == request.user:
            messages.error(request, 'You cannot follow yourself.')
            return redirect(request.META.get('HTTP_REFERER', 'explore'))
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if not created:
            follow.delete()
            messages.success(request, f'You unfollowed {user_to_follow.username}.')
            # Create unfollow notification
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type='follow',
                title='Unfollowed',
                message=f'{request.user.username} unfollowed you'
            )
        else:
            messages.success(request, f'You are now following {user_to_follow.username}!')
            # Create follow notification
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type='follow',
                title='New Follower',
                message=f'{request.user.username} started following you'
            )
        
        # Regular form submission - redirect back
        return redirect(request.META.get('HTTP_REFERER', 'explore'))
            
    except Exception as e:
        messages.error(request, f'Error following user: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'explore'))

@login_required
@require_http_methods(["POST"])
def toggle_save_view(request, post_id):
    """Django form view to toggle save on a post"""
    try:
        from social.models import SavedPost
        post = get_object_or_404(Post, id=post_id)
        saved_post, created = SavedPost.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            saved_post.delete()
            messages.success(request, 'Post removed from saved!')
        else:
            messages.success(request, 'Post saved!')
        
        return redirect(request.META.get('HTTP_REFERER', 'feed'))
        
    except Exception as e:
        messages.error(request, f'Error saving post: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'feed'))

@login_required
@require_http_methods(["POST"])
def add_comment_view(request, post_id):
    """Django form view to add comment to a post"""
    try:
        from social.models import Comment
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get('content', '').strip()
        
        if not content:
            messages.error(request, 'Comment cannot be empty')
            return redirect(request.META.get('HTTP_REFERER', 'feed'))
        
        comment = Comment.objects.create(
            user=request.user,
            post=post,
            content=content
        )
        
        # Update post comment count
        post.comments_count += 1
        post.save()
        
        # Create notification for post author
        if post.user != request.user:
            Notification.objects.create(
                recipient=post.user,
                sender=request.user,
                notification_type='comment',
                title='New Comment',
                message=f'{request.user.username} commented on your post',
                related_post=post,
                related_comment=comment
            )
        
        messages.success(request, 'Comment added successfully!')
        return redirect(request.META.get('HTTP_REFERER', 'feed'))
        
    except Exception as e:
        messages.error(request, f'Error adding comment: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'feed'))

@login_required
@require_http_methods(["POST"])
def create_post_view(request):
    """Django form view to create a new post"""
    try:
        caption = request.POST.get('caption', '').strip()
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        
        if not caption and not image and not video:
            messages.error(request, 'Post must have content, image, or video')
            return redirect(request.META.get('HTTP_REFERER', 'feed'))
        
        # Create the post with initial like count of 0
        post = Post.objects.create(
            user=request.user,
            caption=caption,
            image=image,
            video=video,
            likes_count=0  # Explicitly set initial like count to 0
        )
        
        # No automatic like from creator
        # Users must explicitly like the post
        
        # Update user's post count
        profile = request.user.profile
        profile.posts_count += 1
        profile.save()
        
        messages.success(request, 'Post created successfully!')
        return redirect('feed')
        
    except Exception as e:
        messages.error(request, f'Error creating post: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'feed'))

# All AJAX functionality removed - using pure Django forms and views
