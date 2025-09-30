// 側邊選單切換
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('wrapper').classList.toggle('toggled');
        });
    }
    
    // 為內容添加底部間距，避免被頁腳遮擋
    const footer = document.querySelector('.footer');
    if (footer) {
        const footerHeight = footer.offsetHeight;
        document.body.style.paddingBottom = footerHeight + 'px';
    }
});

$(document).ready(function() {
    // 側邊欄折疊控制
    $('#sidebarToggle').on('click', function() {
        const sidebar = $('#sidebar');
        const mainContent = $('.main-content');
        
        sidebar.toggleClass('collapsed');
        mainContent.toggleClass('expanded');
        
        // 保存側邊欄狀態到本地存儲
        const isSidebarCollapsed = sidebar.hasClass('collapsed');
        localStorage.setItem('sidebarCollapsed', isSidebarCollapsed);
    });
    
    // 頁面加載時檢查側邊欄狀態
    const storedSidebarState = localStorage.getItem('sidebarCollapsed');
    if (storedSidebarState === 'true') {
        $('#sidebar').addClass('collapsed');
        $('.main-content').addClass('expanded');
    }
    
    // 在小屏幕上點擊背景時收起側邊欄
    $(document).on('click', function(e) {
        if ($(window).width() <= 768) {
            if (!$(e.target).closest('#sidebar').length && !$(e.target).closest('#sidebarToggle').length) {
                $('#sidebar').removeClass('active');
            }
        }
    });
    
    // 返回按鈕功能
    $('#backButton').on('click', function(e) {
        e.preventDefault();
        // 這裡可以添加返回所有對話列表的功能
        console.log('返回所有對話列表');
    });
    
    // 新對話按鈕功能
    $('.new-conversation-btn button').on('click', function() {
        // 這裡可以添加創建新對話的功能
        console.log('創建新對話');
        window.location.href = '/chat/new/';
    });
    
    // 對話項目點擊功能
    $('.conversation-item').on('click', function() {
        const conversationId = $(this).data('id');
        if (conversationId) {
            window.location.href = '/chat/conversation/' + conversationId + '/';
        }
    });
    
    // 頂部導航標籤切換
    $('.nav-tab').on('click', function() {
        $('.nav-tab').removeClass('active');
        $(this).addClass('active');
        
        // 這裡可以添加標籤切換的相應功能
        const tabName = $(this).text().trim();
        console.log('切換到標籤:', tabName);
    });
    
    // 用戶頭像點擊事件
    $('.user-profile').on('click', function() {
        // 這裡可以添加用戶菜單或個人資料功能
        console.log('用戶頭像點擊');
    });
    
    // 調整聊天區域高度，確保在可視範圍內滾動
    function adjustChatHeight() {
        if ($('.chat-messages').length) {
            const viewportHeight = $(window).height();
            const chatHeaderHeight = $('.chat-header').outerHeight();
            const chatInputHeight = $('.chat-input-container').outerHeight();
            const topNavHeight = $('.top-nav').outerHeight();
            
            const chatMessagesHeight = viewportHeight - (chatHeaderHeight + chatInputHeight + topNavHeight) - 40; // 減去額外間距
            $('.chat-messages').css('height', chatMessagesHeight + 'px');
        }
    }
    
    // 調整應用容器高度
    function adjustAppHeight() {
        const viewportHeight = $(window).height();
        const containerHeight = viewportHeight - 40; // 留出上下間距
        $('.app-wrapper').css('height', containerHeight + 'px');
    }
    
    // 頁面加載和窗口大小改變時調整高度
    adjustChatHeight();
    adjustAppHeight();
    $(window).on('resize', function() {
        adjustChatHeight();
        adjustAppHeight();
    });
    
    // 添加聊天輸入框占位符動畫效果
    $('#userInput').on('focus', function() {
        $(this).attr('placeholder', '');
    }).on('blur', function() {
        if ($(this).val() === '') {
            $(this).attr('placeholder', '請輸入您的問題或要求...');
        }
    });
    
    // 初始化頁面時滾動到最新消息
    if ($('.chat-messages').length) {
        setTimeout(function() {
            $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);
        }, 100);
    }
    
    // 模擬文件上傳功能
    $('.chat-tools .fa-paperclip').on('click', function() {
        console.log('開啟文件上傳');
        // 這裡可以添加打開文件選擇對話框的功能
    });
    
    // 模擬語音輸入功能
    $('.chat-tools .fa-microphone').on('click', function() {
        console.log('開啟語音輸入');
        // 這裡可以添加語音輸入功能
    });
}); 