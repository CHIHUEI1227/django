document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.favorite-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const postId = btn.getAttribute('data-post-id');
            fetch(`/post/${postId}/favorite/add/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    btn.classList.add('active');
                    btn.innerHTML = '<i class="fas fa-heart"></i> 已收藏';
                }
            });
        });
    });
});