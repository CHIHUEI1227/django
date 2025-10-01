/**
 * 網站通用JavaScript功能
 * 包含導航欄、下拉選單和其他共用功能
 */

// 確保Bootstrap下拉選單正確運作
document.addEventListener('DOMContentLoaded', function() {
    // 使用Bootstrap原生下拉選單功能
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    
    // 為聊天頁面添加特殊處理
    if (document.body.classList.contains('chat-page')) {
        // 點擊導航項目後，確保下拉選單能正確顯示
        document.querySelectorAll('.nav-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                e.stopPropagation(); // 阻止事件冒泡
            });
        });
    }
    
    // 獲取CSRF令牌的共用函數
    window.getCookie = function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
    
    // 添加通用的訊息提示功能
    window.showMessage = function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // 添加到頁面
        const contentContainer = document.querySelector('.content-container');
        if (contentContainer) {
            contentContainer.prepend(alertDiv);
            
            // 5秒後自動消失
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }, 5000);
        }
    };
}); 