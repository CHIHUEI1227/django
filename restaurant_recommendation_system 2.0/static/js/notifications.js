/**
 * 通知系統相關的JavaScript功能
 */

// 刪除單個通知
function deleteNotification(notificationId) {
    if (confirm('確定要刪除此通知嗎？')) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch(`/notification/${notificationId}/delete/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 移除通知元素
                document.getElementById(`notification-${notificationId}`).remove();
                
                // 如果沒有通知了，顯示空通知訊息
                const notificationItems = document.querySelectorAll('.notification-item');
                if (notificationItems.length === 0) {
                    const cardBody = document.querySelector('.card-body');
                    cardBody.innerHTML = `
                        <div class="text-center py-5">
                            <i class="far fa-bell-slash fa-4x text-muted mb-3"></i>
                            <p class="lead text-muted">您目前沒有任何通知</p>
                        </div>
                    `;
                    
                    // 隱藏頂部按鈕
                    hideActionButtons();
                }
                
                // 更新導航欄的通知計數
                updateNotificationCount();
            }
        });
    }
}

// 設置刪除通知按鈕的事件監聽
function setupDeleteButtons() {
    document.addEventListener('click', function(event) {
        const deleteButton = event.target.closest('.delete-notification-btn');
        if (deleteButton) {
            const notificationId = deleteButton.dataset.notificationId;
            if (notificationId) {
                deleteNotification(notificationId);
            }
        }
    });
}

// 標記所有通知為已讀
function setupMarkAllReadButton() {
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            if (confirm('確定要將所有通知標記為已讀嗎？')) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                fetch('/notifications/mark-all-read/', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // 移除所有未讀通知的背景色
                        document.querySelectorAll('.notification-item.bg-light').forEach(item => {
                            item.classList.remove('bg-light');
                        });
                        
                        // 更新導航欄的通知計數
                        updateNotificationCount();
                    }
                });
            }
        });
    }
}

// 刪除所有通知
function setupDeleteAllButton() {
    const deleteAllBtn = document.getElementById('deleteAllBtn');
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener('click', function() {
            if (confirm('確定要刪除所有通知嗎？此操作無法撤銷。')) {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                fetch('/notifications/delete-all/', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // 顯示空通知訊息
                        const cardBody = document.querySelector('.card-body');
                        cardBody.innerHTML = `
                            <div class="text-center py-5">
                                <i class="far fa-bell-slash fa-4x text-muted mb-3"></i>
                                <p class="lead text-muted">您目前沒有任何通知</p>
                            </div>
                        `;
                        
                        // 隱藏頂部按鈕
                        hideActionButtons();
                        
                        // 更新導航欄的通知計數
                        updateNotificationCount();
                    }
                });
            }
        });
    }
}

// 隱藏操作按鈕
function hideActionButtons() {
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    const deleteAllBtn = document.getElementById('deleteAllBtn');
    
    if (markAllReadBtn) markAllReadBtn.style.display = 'none';
    if (deleteAllBtn) deleteAllBtn.style.display = 'none';
}

// 更新導航欄的通知計數
function updateNotificationCount() {
    // 這個函數在標記已讀或刪除通知後調用，將導航欄的通知計數更新為0
    const navBadge = document.querySelector('.nav-item .badge');
    if (navBadge) {
        navBadge.style.display = 'none';
    }
}

// 初始化所有通知相關功能
document.addEventListener('DOMContentLoaded', function() {
    setupDeleteButtons();
    setupMarkAllReadButton();
    setupDeleteAllButton();
}); 