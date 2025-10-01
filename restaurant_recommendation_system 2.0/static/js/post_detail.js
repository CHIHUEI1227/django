// 切換回覆表單的顯示和隱藏
function toggleReplyForm(formId) {
    const form = document.getElementById(formId);
    if (form.style.display === 'none') {
        form.style.display = 'block';
    } else {
        form.style.display = 'none';
    }
}

// 添加表情符號反應
function addReaction(reactionType, postId, csrfToken) {
    fetch(`/post/${postId}/reaction/add/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `reaction_type=${reactionType}`
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            updateReactionsUI(data.reactions_count, data.total_reactions, reactionType);
        }
    })
    .catch(error => {
        console.error('添加表情符號反應失敗:', error);
    });
}

// 移除表情符號反應
function removeReaction(postId, csrfToken) {
    fetch(`/post/${postId}/reaction/remove/`, { // 修正路徑
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            updateReactionsUI(data.reactions_count, data.total_reactions, null);
        }
    })
    .catch(error => {
        console.error('移除表情符號反應失敗:', error);
    });
}

// 更新UI中的表情符號反應
function updateReactionsUI(reactionsCount, totalReactions, userReaction) {
    console.log(reactionsCount, totalReactions, userReaction);
    
    // 更新總反應數量
    const reactionsSummary = document.getElementById('reactions-summary');
    if (totalReactions > 0) {
        reactionsSummary.querySelector('.text-muted').textContent = `${totalReactions} 人反應`;
        reactionsSummary.style.display = 'block';
        
        // 更新各表情符號數量標籤
        const reactionIcons = {
            'like': '👍',
            'love': '❤️',
            'haha': '😄',
            'wow': '😲',
            'sad': '😢',
            'angry': '😠'
        };

        for (const type in reactionsCount) {
            let badge = reactionsSummary.querySelector(`[title="${type}"]`);
            if (reactionsCount[type] > 0) {
                if (badge) {
                    badge.querySelector('.reaction-count').textContent = reactionsCount[type];
                } else {
                    // 自動建立新的反應標籤（加上表情符號）
                    badge = document.createElement('span');
                    badge.setAttribute('title', type);
                    badge.innerHTML = `${reactionIcons[type]} <span class="reaction-count">${reactionsCount[type]}</span>`;
                    reactionsSummary.appendChild(badge);
                }
            } else if (badge) {
                badge.remove();
            }
        }
    } else {
        reactionsSummary.style.display = 'none';
    }
    
    // 更新反應按鈕顯示
    const reactionButton = document.getElementById('reaction-button');
    
    // 更新下拉選單中的數量
    const dropdownItems = document.querySelectorAll('.reaction-btn');
    dropdownItems.forEach(item => {
        const type = item.getAttribute('data-reaction');
        const countBadge = item.querySelector('.badge');
        if (countBadge) {
            countBadge.textContent = reactionsCount[type] || '0';
        }
    });
    
    // 更新用戶的反應按鈕
    if (userReaction) {
        const reactionIcons = {
            'like': '👍 讚',
            'love': '❤️ 愛心',
            'haha': '😄 哈哈',
            'wow': '😲 哇',
            'sad': '😢 傷心',
            'angry': '😠 怒'
        };
        reactionButton.innerHTML = reactionIcons[userReaction];
        
        // 顯示移除反應選項
        document.querySelectorAll('#remove-reaction-option').forEach(el => {
            el.style.display = 'block';
        });
    } else {
        reactionButton.innerHTML = '<i class="far fa-smile me-1"></i> 表情';
        
        // 隱藏移除反應選項
        document.querySelectorAll('#remove-reaction-option').forEach(el => {
            el.style.display = 'none';
        });
    }
}

// 收藏/取消收藏貼文
function toggleFavorite(postId, csrfToken) {
    const icon = document.getElementById('favorite-icon');
    const isFavorite = icon.classList.contains('fas'); // fas = 填滿, far = 空心
    const url = isFavorite
        ? `/post/${postId}/favorite/remove/`
        : `/post/${postId}/favorite/add/`;
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 切換 icon 樣式
            if (isFavorite) {
                icon.classList.remove('fas');
                icon.classList.add('far');
            } else {
                icon.classList.remove('far');
                icon.classList.add('fas');
            }
        }
    });
}

// 分享貼文
function sharePost(postTitle) {
    const shareUrl = window.location.href;
    
    if (navigator.share) {
        navigator.share({
            title: postTitle,
            url: shareUrl
        }).catch(error => {
            console.error('分享失敗:', error);
            fallbackShare(shareUrl);
        });
    } else {
        fallbackShare(shareUrl);
    }
}

// 後備分享方法
function fallbackShare(url) {
    // 創建一個臨時輸入框
    const input = document.createElement('input');
    input.value = url;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
    
    alert('連結已複製到剪貼簿！');
}

// 初始化地圖
function initMap(lat, lng, locationName) {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;
    
    const position = { lat, lng };
    const map = new google.maps.Map(mapElement, {
        zoom: 15,
        center: position,
    });
    
    const marker = new google.maps.Marker({
        position: position,
        map: map,
        title: locationName
    });
    
    const infowindow = new google.maps.InfoWindow({
        content: `<div><strong>${locationName}</strong></div>`
    });
    
    marker.addListener('click', function() {
        infowindow.open(map, marker);
    });
}

// 頁面載入後的互動邏輯

document.addEventListener('DOMContentLoaded', function() {
    console.log('[post_detail.js] DOMContentLoaded 觸發');
    // 取得全域變數
    const postId = window.postId;
    const csrfToken = window.csrfToken;
    const postTitle = window.postTitle;
    const postLat = window.postLat;
    const postLng = window.postLng;
    const locationName = window.locationName;

    // 表情符號下拉選單
    const reactionButton = document.getElementById('reaction-button');
    if (reactionButton) {
        const dropdown = new bootstrap.Dropdown(reactionButton, {
            autoClose: true,
            boundary: 'viewport'
        });
        const menu = document.querySelector('.reaction-menu');
        if (menu) {
            menu.style.zIndex = '9999';
        }
    }
    document.querySelectorAll('.reaction-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            const reactionType = this.getAttribute('data-reaction');
            addReaction(reactionType, postId, csrfToken);
            if (reactionButton) {
                bootstrap.Dropdown.getInstance(reactionButton).hide();
            }
        });
    });
    // 移除反應
    const removeReactionBtn = document.querySelector('.dropdown-item.text-danger');
    if (removeReactionBtn) {
        removeReactionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            removeReaction(postId, csrfToken);
            if (reactionButton) {
                bootstrap.Dropdown.getInstance(reactionButton).hide();
            }
        });
    }
    // 收藏
    const favoriteBtn = document.getElementById('favorite-button');
    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleFavorite(postId, csrfToken);
        });
    }
    // 分享
    const shareBtn = document.getElementById('share-button');
    if (shareBtn) {
        shareBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sharePost(postTitle);
        });
    }
    // Google Maps
    if (typeof postLat !== 'undefined' && typeof postLng !== 'undefined' && postLat && postLng) {
        window.initMap = function() {
            const lat = parseFloat(postLat);
            const lng = parseFloat(postLng);
            initMap(lat, lng, locationName);
        };
    }
    // 多圖 carousel 點擊切換
    var imgs = document.querySelectorAll('.post-detail-img');
    var imageModal = document.getElementById('imageModal');
    var carousel = document.getElementById('imageCarousel');
    var targetCarouselIndex = 0;

    imgs.forEach(function(img) {
        img.addEventListener('click', function(e) {
            e.preventDefault();
            targetCarouselIndex = parseInt(this.getAttribute('data-img-index')) || 0;
            var carouselInstance = bootstrap.Carousel.getOrCreateInstance(carousel);
            carouselInstance.to(targetCarouselIndex);
            // 主動開啟 Modal
            var modalInstance = bootstrap.Modal.getOrCreateInstance(imageModal);
            modalInstance.show();
        });
    });
});
