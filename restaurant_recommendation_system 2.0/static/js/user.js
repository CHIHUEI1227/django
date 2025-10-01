/**
 * 用戶相關頁面的JavaScript功能
 * 包含表單處理、個人資料管理等功能
 */

// 頁面加載完成後執行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化表單樣式
    initFormStyles();
    
    // 初始化圖片預覽功能
    initImagePreview();
    
    // 初始化追蹤功能
    initFollowButtons();
    
    // 初始化密碼強度檢查
    initPasswordStrengthChecker();
});

/**
 * 初始化表單樣式
 */
function initFormStyles() {
    // 為所有表單輸入添加Bootstrap樣式
    const formInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea');
    formInputs.forEach(input => {
        input.classList.add('form-control');
    });
    
    // 為所有提交按鈕添加樣式
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(button => {
        if (!button.classList.contains('btn')) {
            button.classList.add('btn', 'btn-primary');
        }
    });
}

/**
 * 初始化圖片預覽功能
 */
function initImagePreview() {
    const profilePicInput = document.querySelector('input[type="file"][name="profile_pic"]');
    
    if (profilePicInput) {
        profilePicInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // 尋找預覽元素或創建一個
                    let previewElement = document.getElementById('profile-pic-preview');
                    
                    if (!previewElement) {
                        previewElement = document.createElement('img');
                        previewElement.id = 'profile-pic-preview';
                        previewElement.className = 'img-thumbnail mt-2';
                        previewElement.style.maxHeight = '200px';
                        profilePicInput.parentNode.appendChild(previewElement);
                    }
                    
                    previewElement.src = e.target.result;
                };
                
                reader.readAsDataURL(file);
            }
        });
    }
}

/**
 * 初始化追蹤按鈕功能
 */
function initFollowButtons() {
    const followButtons = document.querySelectorAll('.follow-btn');
    
    followButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            if (userId) {
                toggleFollow(userId, this);
            }
        });
    });
}

/**
 * 切換追蹤狀態
 * @param {string} userId - 用戶ID
 * @param {Element} btn - 按鈕元素
 */
function toggleFollow(userId, btn) {
    fetch(`/follow/${userId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            const isFollowing = data.is_following;
            
            // 更新按鈕狀態
            if (isFollowing) {
                btn.textContent = '已追蹤';
                btn.classList.replace('btn-outline-primary', 'btn-primary');
            } else {
                btn.textContent = '追蹤';
                btn.classList.replace('btn-primary', 'btn-outline-primary');
            }
            
            // 更新計數（如果存在）
            const followersCountElement = document.getElementById('followers-count');
            if (followersCountElement && data.followers_count !== undefined) {
                followersCountElement.textContent = data.followers_count;
            }
            
            // 顯示通知
            showToast(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('操作失敗，請稍後再試');
    });
}

/**
 * 初始化密碼強度檢查
 */
function initPasswordStrengthChecker() {
    const passwordInput = document.querySelector('input[type="password"][name="password1"]');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            
            // 尋找或創建強度提示元素
            let strengthElement = document.getElementById('password-strength');
            
            if (!strengthElement) {
                strengthElement = document.createElement('div');
                strengthElement.id = 'password-strength';
                strengthElement.className = 'mt-2';
                passwordInput.parentNode.appendChild(strengthElement);
            }
            
            // 更新強度提示
            strengthElement.className = 'mt-2 text-' + strength.color;
            strengthElement.textContent = strength.message;
        });
    }
}

/**
 * 檢查密碼強度
 * @param {string} password - 密碼
 * @returns {Object} 強度評估結果
 */
function checkPasswordStrength(password) {
    // 長度檢查
    if (password.length < 8) {
        return { color: 'danger', message: '密碼太短（至少8個字符）' };
    }
    
    // 複雜度檢查
    let score = 0;
    
    // 包含數字
    if (/\d/.test(password)) {
        score += 1;
    }
    
    // 包含小寫字母
    if (/[a-z]/.test(password)) {
        score += 1;
    }
    
    // 包含大寫字母
    if (/[A-Z]/.test(password)) {
        score += 1;
    }
    
    // 包含特殊字符
    if (/[^A-Za-z0-9]/.test(password)) {
        score += 1;
    }
    
    // 根據分數判斷強度
    if (score === 1) {
        return { color: 'danger', message: '密碼強度：弱' };
    } else if (score === 2) {
        return { color: 'warning', message: '密碼強度：中' };
    } else if (score === 3) {
        return { color: 'info', message: '密碼強度：強' };
    } else if (score === 4) {
        return { color: 'success', message: '密碼強度：非常強' };
    }
    
    return { color: 'danger', message: '密碼強度：弱' };
}

/**
 * 顯示Toast通知
 * @param {string} message - 要顯示的消息
 */
function showToast(message) {
    // 創建toast元素
    const toastContainer = document.createElement('div');
    toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
    toastContainer.style.zIndex = '5';
    
    toastContainer.innerHTML = `
        <div class="toast align-items-center text-white bg-primary border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.body.appendChild(toastContainer);
    
    // 使用Bootstrap的Toast API
    const toastElement = new bootstrap.Toast(toastContainer.querySelector('.toast'), {
        delay: 3000
    });
    toastElement.show();
    
    // 自動移除元素
    toastContainer.querySelector('.toast').addEventListener('hidden.bs.toast', function() {
        toastContainer.remove();
    });
}

/**
 * 獲取CSRF Token
 * @returns {string} CSRF Token
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return '';
} 