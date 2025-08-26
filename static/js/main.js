// BIM Social - Main JavaScript File
// Real-time interactions, WebSocket connections, and UI enhancements

class BIMSocial {
    constructor() {
        this.chatSocket = null;
        this.notificationSocket = null;
        this.currentUser = null;
        this.isTyping = false;
        this.typingTimeout = null;
        this.init();
    }

    init() {
        this.setupCSRF();
        this.setupEventListeners();
        this.initializeWebSockets();
        this.setupInfiniteScroll();
        this.setupImagePreview();
        this.setupNotifications();
    }

    // CSRF Token Setup
    setupCSRF() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    }
                }
            });
        }
    }

    // Event Listeners
    setupEventListeners() {
        // Search functionality
        this.setupSearch();
        
        // Post interactions
        this.setupPostInteractions();
        
        // Chat functionality
        this.setupChat();
        
        // Navigation
        this.setupNavigation();
        
        // Form submissions
        this.setupForms();
    }

    // WebSocket Connections
    initializeWebSockets() {
        this.connectChatSocket();
        this.connectNotificationSocket();
    }

    connectChatSocket() {
        const conversationId = document.querySelector('[data-conversation-id]')?.dataset.conversationId;
        if (!conversationId) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${conversationId}/`;
        
        this.chatSocket = new WebSocket(wsUrl);
        
        this.chatSocket.onopen = () => {
            console.log('Chat WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.chatSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleChatMessage(data);
        };
        
        this.chatSocket.onclose = () => {
            console.log('Chat WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.connectChatSocket(), 3000);
        };
        
        this.chatSocket.onerror = (error) => {
            console.error('Chat WebSocket error:', error);
        };
    }

    connectNotificationSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        this.notificationSocket = new WebSocket(wsUrl);
        
        this.notificationSocket.onopen = () => {
            console.log('Notification WebSocket connected');
        };
        
        this.notificationSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleNotification(data);
        };
        
        this.notificationSocket.onclose = () => {
            console.log('Notification WebSocket disconnected');
            setTimeout(() => this.connectNotificationSocket(), 3000);
        };
    }

    // Chat Functionality
    setupChat() {
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        
        if (chatForm && messageInput) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
            
            messageInput.addEventListener('input', () => {
                this.handleTyping();
            });
            
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || !this.chatSocket) return;
        
        this.chatSocket.send(JSON.stringify({
            'type': 'chat_message',
            'message': message
        }));
        
        messageInput.value = '';
        this.stopTyping();
    }

    handleChatMessage(data) {
        switch (data.type) {
            case 'chat_message':
                this.displayMessage(data);
                break;
            case 'typing_indicator':
                this.showTypingIndicator(data);
                break;
            case 'user_online':
                this.updateUserStatus(data.user_id, true);
                break;
            case 'user_offline':
                this.updateUserStatus(data.user_id, false);
                break;
            case 'message_read':
                this.markMessageAsRead(data.message_id);
                break;
        }
    }

    displayMessage(data) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        const messageElement = this.createMessageElement(data);
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Remove typing indicator if it exists
        this.removeTypingIndicator();
        
        // Play notification sound for received messages
        if (data.user_id !== this.getCurrentUserId()) {
            this.playNotificationSound();
        }
    }

    createMessageElement(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.user_id === this.getCurrentUserId() ? 'own' : ''}`;
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-content">${this.escapeHtml(data.message)}</div>
                <div class="message-time">${this.formatTime(data.timestamp)}</div>
            </div>
        `;
        return messageDiv;
    }

    handleTyping() {
        if (!this.isTyping && this.chatSocket) {
            this.isTyping = true;
            this.chatSocket.send(JSON.stringify({
                'type': 'typing_start'
            }));
        }
        
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.stopTyping();
        }, 1000);
    }

    stopTyping() {
        if (this.isTyping && this.chatSocket) {
            this.isTyping = false;
            this.chatSocket.send(JSON.stringify({
                'type': 'typing_stop'
            }));
        }
    }

    showTypingIndicator(data) {
        if (data.user_id === this.getCurrentUserId()) return;
        
        this.removeTypingIndicator();
        
        const messagesContainer = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `${data.username} is typing...`;
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Search Functionality
    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        
        if (searchInput) {
            let searchTimeout;
            
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length < 2) {
                    if (searchResults) searchResults.innerHTML = '';
                    return;
                }
                
                searchTimeout = setTimeout(() => {
                    this.performSearch(query);
                }, 300);
            });
            
            // Hide search results when clicking outside
            document.addEventListener('click', (e) => {
                if (!searchInput.contains(e.target) && searchResults) {
                    searchResults.innerHTML = '';
                }
            });
        }
    }

    performSearch(query) {
        $.get('/ajax/search/', { q: query })
            .done((data) => {
                this.displaySearchResults(data);
            })
            .fail(() => {
                console.error('Search failed');
            });
    }

    displaySearchResults(results) {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="p-3 text-muted">No results found</div>';
            return;
        }
        
        const resultsHtml = results.map(user => `
            <a href="/profile/${user.username}/" class="d-flex align-items-center p-3 text-decoration-none border-bottom">
                <img src="${user.profile_image || '/static/images/default-avatar.png'}" 
                     alt="${user.username}" class="avatar me-3">
                <div>
                    <div class="fw-medium">${user.full_name || user.username}</div>
                    <div class="text-muted small">${user.specialization || 'BIM Professional'}</div>
                </div>
            </a>
        `).join('');
        
        searchResults.innerHTML = resultsHtml;
    }

    // Post Interactions
    setupPostInteractions() {
        // Like buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.like-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.like-btn');
                const postId = btn.dataset.postId;
                this.toggleLike(postId, btn);
            }
            
            if (e.target.closest('.save-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.save-btn');
                const postId = btn.dataset.postId;
                this.toggleSave(postId, btn);
            }
            
            if (e.target.closest('.follow-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.follow-btn');
                const username = btn.dataset.username;
                this.toggleFollow(username, btn);
            }
        });
    }

    toggleLike(postId, button) {
        const icon = button.querySelector('i');
        const countSpan = button.querySelector('.like-count');
        
        button.disabled = true;
        
        $.post(`/ajax/like/${postId}/`)
            .done((data) => {
                if (data.liked) {
                    icon.className = 'fas fa-heart text-danger';
                } else {
                    icon.className = 'far fa-heart';
                }
                countSpan.textContent = data.likes_count;
                
                // Add animation
                button.classList.add('animate__animated', 'animate__pulse');
                setTimeout(() => {
                    button.classList.remove('animate__animated', 'animate__pulse');
                }, 600);
            })
            .fail(() => {
                this.showToast('Error liking post', 'error');
            })
            .always(() => {
                button.disabled = false;
            });
    }

    toggleSave(postId, button) {
        const icon = button.querySelector('i');
        
        button.disabled = true;
        
        $.post(`/ajax/save/${postId}/`)
            .done((data) => {
                if (data.saved) {
                    icon.className = 'fas fa-bookmark text-warning';
                } else {
                    icon.className = 'far fa-bookmark';
                }
                
                this.showToast(data.saved ? 'Post saved' : 'Post unsaved', 'success');
            })
            .fail(() => {
                this.showToast('Error saving post', 'error');
            })
            .always(() => {
                button.disabled = false;
            });
    }

    toggleFollow(username, button) {
        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = 'Loading...';
        
        $.post(`/ajax/follow/${username}/`)
            .done((data) => {
                if (data.following) {
                    button.textContent = 'Following';
                    button.className = 'btn btn-sm btn-secondary follow-btn';
                } else {
                    button.textContent = 'Follow';
                    button.className = 'btn btn-sm btn-primary follow-btn';
                }
                
                this.showToast(data.following ? `Now following ${username}` : `Unfollowed ${username}`, 'success');
            })
            .fail(() => {
                button.textContent = originalText;
                this.showToast('Error updating follow status', 'error');
            })
            .always(() => {
                button.disabled = false;
            });
    }

    // Notifications
    setupNotifications() {
        this.requestNotificationPermission();
        this.loadNotifications();
    }

    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    handleNotification(data) {
        switch (data.type) {
            case 'new_notification':
                this.displayNotification(data);
                this.updateNotificationBadge();
                break;
            case 'notification_read':
                this.markNotificationAsRead(data.notification_id);
                break;
        }
    }

    displayNotification(data) {
        // Show browser notification
        if (Notification.permission === 'granted') {
            new Notification(data.title, {
                body: data.message,
                icon: '/static/images/logo.png',
                tag: data.notification_id
            });
        }
        
        // Show in-app notification
        this.showToast(data.message, 'info');
        
        // Add to notifications dropdown
        this.addNotificationToDropdown(data);
    }

    loadNotifications() {
        $.get('/ajax/notifications/')
            .done((data) => {
                this.updateNotificationBadge(data.unread_count);
                this.populateNotificationsDropdown(data.notifications);
            });
    }

    updateNotificationBadge(count = null) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            if (count === null) {
                // Increment current count
                const currentCount = parseInt(badge.textContent) || 0;
                count = currentCount + 1;
            }
            
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    // Infinite Scroll
    setupInfiniteScroll() {
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (!loadMoreBtn) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !loadMoreBtn.disabled) {
                    this.loadMorePosts();
                }
            });
        });
        
        observer.observe(loadMoreBtn);
    }

    loadMorePosts() {
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        const page = loadMoreBtn.dataset.page;
        
        loadMoreBtn.disabled = true;
        loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        
        $.get(window.location.pathname, { page: page })
            .done((data) => {
                // This would need backend support to return JSON with HTML fragments
                const postsContainer = document.getElementById('posts-container');
                postsContainer.insertAdjacentHTML('beforeend', data.posts_html);
                
                if (data.has_next) {
                    loadMoreBtn.dataset.page = data.next_page;
                    loadMoreBtn.disabled = false;
                    loadMoreBtn.innerHTML = 'Load More Posts';
                } else {
                    loadMoreBtn.style.display = 'none';
                }
            })
            .fail(() => {
                this.showToast('Error loading more posts', 'error');
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = 'Load More Posts';
            });
    }

    // Image Preview
    setupImagePreview() {
        document.addEventListener('change', (e) => {
            if (e.target.type === 'file' && e.target.accept?.includes('image')) {
                this.previewImage(e.target);
            }
        });
    }

    previewImage(input) {
        const file = input.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('imagePreview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
    }

    // Form Handling
    setupForms() {
        // Post creation form
        const createPostForm = document.getElementById('createPostForm');
        if (createPostForm) {
            createPostForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitPost(createPostForm);
            });
        }
        
        // Comment forms
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('comment-form')) {
                e.preventDefault();
                this.submitComment(e.target);
            }
        });
    }

    submitPost(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const formData = new FormData(form);
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Posting...';
        
        $.ajax({
            url: '/ajax/create-post/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: (data) => {
                form.reset();
                $('#createPostModal').modal('hide');
                this.showToast('Post created successfully!', 'success');
                
                // Add new post to feed
                const postsContainer = document.getElementById('posts-container');
                if (postsContainer) {
                    postsContainer.insertAdjacentHTML('afterbegin', data.post_html);
                }
            },
            error: () => {
                this.showToast('Error creating post', 'error');
            },
            complete: () => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Post';
            }
        });
    }

    submitComment(form) {
        const postId = form.dataset.postId;
        const formData = new FormData(form);
        
        $.ajax({
            url: `/ajax/comment/${postId}/`,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: (data) => {
                form.reset();
                // Add comment to post
                const commentsContainer = form.closest('.post-card').querySelector('.comments-container');
                if (commentsContainer) {
                    commentsContainer.insertAdjacentHTML('beforeend', data.comment_html);
                }
            },
            error: () => {
                this.showToast('Error adding comment', 'error');
            }
        });
    }

    // Navigation
    setupNavigation() {
        // Active nav link highlighting
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // Utility Functions
    getCurrentUserId() {
        return document.body.dataset.userId;
    }

    updateConnectionStatus(connected) {
        const statusIndicator = document.querySelector('.connection-status');
        if (statusIndicator) {
            statusIndicator.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            statusIndicator.title = connected ? 'Connected' : 'Disconnected';
        }
    }

    updateUserStatus(userId, online) {
        const userElements = document.querySelectorAll(`[data-user-id="${userId}"]`);
        userElements.forEach(element => {
            const statusDot = element.querySelector('.status-dot');
            if (statusDot) {
                statusDot.className = `status-dot ${online ? 'online' : 'offline'}`;
            }
        });
    }

    markMessageAsRead(messageId) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            messageElement.classList.add('read');
        }
    }

    playNotificationSound() {
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(() => {
            // Ignore errors if sound can't be played
        });
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.bimSocial = new BIMSocial();
});

// Global functions for backward compatibility
function toggleLike(postId, button) {
    window.bimSocial.toggleLike(postId, button);
}

function toggleSave(postId, button) {
    window.bimSocial.toggleSave(postId, button);
}

function toggleFollow(username, button) {
    window.bimSocial.toggleFollow(username, button);
}

function addComment(event, postId) {
    event.preventDefault();
    window.bimSocial.submitComment(event.target);
}
