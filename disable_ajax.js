// Disable all AJAX like calls by overriding jQuery and fetch
(function() {
    // Override jQuery post for like endpoints
    if (window.$ && $.post) {
        const originalPost = $.post;
        $.post = function(url, data, success, dataType) {
            if (url && url.includes('/ajax/like/')) {
                console.log('AJAX like call blocked - using Django forms instead');
                return;
            }
            return originalPost.apply(this, arguments);
        };
    }
    
    // Override fetch for like endpoints
    if (window.fetch) {
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (url && url.includes('/ajax/like/')) {
                console.log('Fetch like call blocked - using Django forms instead');
                return Promise.resolve(new Response('{}', {status: 200}));
            }
            return originalFetch.apply(this, arguments);
        };
    }
    
    // Remove any existing like button event listeners
    document.addEventListener('DOMContentLoaded', function() {
        const likeButtons = document.querySelectorAll('.like-btn, [data-post-id]');
        likeButtons.forEach(btn => {
            // Clone button to remove all event listeners
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
        });
    });
})();
