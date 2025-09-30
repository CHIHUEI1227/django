/**
 * 聊天系統JavaScript功能
 * 包含聊天界面、訊息處理、指南模態視窗等功能
 */

// 設置頁面類別為聊天頁面
$(document).ready(function() {
    // 設置聊天頁面的類別
    $('body').addClass('chat-page');
    
    // 聊天室界面元素
    const toggleHistoryBtn = $('#toggleHistoryBtn');
    const closeHistoryPanel = $('#closeHistoryPanel');
    const mobileToggleBtn = $('#mobileToggleBtn');
    const chatHistoryPanel = $('#chatHistoryPanel');
    const chatWindow = $('#chatWindow');
    const newChatBtn = $('#newChatBtn');
    const sendButton = $('#sendButton');
    
    // 用戶偏好和位置資訊
    let userPreferences = {};
    let userLocation = null;
                    
    // 獲取用戶偏好
    const favoriteFoods = $('#userFavoriteFoods').data('value');
    const foodRestrictions = $('#userFoodRestrictions').data('value');
    
    // 設置用戶偏好
    if (favoriteFoods && favoriteFoods !== 'None') {
        userPreferences.favorite_foods = favoriteFoods;
    }
    
    if (foodRestrictions && foodRestrictions !== 'None') {
        userPreferences.food_restrictions = foodRestrictions;
    }
    
    // 嘗試獲取用戶位置
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                userLocation = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };
                console.log('已獲取用戶位置');
                },
                function(error) {
                console.log('無法獲取用戶位置:', error.message);
            }
        );
    }
    
    // 設置初始狀態 - 默認顯示聊天記錄
    let isHistoryVisible = true;
    
    // 切換聊天記錄面板
    function toggleHistory() {
        if (isHistoryVisible) {
            chatHistoryPanel.addClass('hidden');
            toggleHistoryBtn.html('<i class="fas fa-history"></i>');
            // 不需要手動調整按鈕位置，CSS已經處理
        } else {
            chatHistoryPanel.removeClass('hidden');
            toggleHistoryBtn.html('<i class="fas fa-chevron-left"></i>');
            // 不需要手動調整按鈕位置，CSS已經處理
        }
        isHistoryVisible = !isHistoryVisible;
    }
    
    // 切換按鈕點擊事件
    toggleHistoryBtn.on('click', toggleHistory);
    
    // 關閉按鈕點擊事件
    closeHistoryPanel.on('click', function() {
        if (isHistoryVisible) {
            toggleHistory();
                }
    });
    
    // 移動端切換按鈕
    mobileToggleBtn.on('click', function() {
        chatHistoryPanel.toggleClass('active');
    });
    
    // 點擊歷史記錄項目
    $('.history-item').on('click', function(e) {
        // 如果點擊的是刪除按鈕，則不執行載入聊天記錄的操作
        if ($(e.target).closest('.delete-chat-btn').length) {
            return;
        }
        
        const chatId = $(this).data('chat-id');
        if (chatId) {
            loadChatHistory(chatId);
            }
            
        // 在移動端自動隱藏側欄
        if ($(window).width() <= 992) {
            chatHistoryPanel.removeClass('active');
        }
    });
    
    // 模態視窗顯示前事件處理
    $('#deleteChatModal').on('show.bs.modal', function(event) {
        // 獲取觸發按鈕
        const button = $(event.relatedTarget);
        // 獲取聊天記錄ID
        const chatId = button.data('chat-id');
        // 將ID保存到確認刪除按鈕
        $('#confirmDeleteBtn').data('chat-id', chatId);
    });
    
    // 點擊確認刪除按鈕
    $(document).on('click', '#confirmDeleteBtn', function() {
        const chatId = $(this).data('chat-id');
        
        if (!chatId) {
            return;
        }
        
        // 發送AJAX請求刪除聊天記錄
        $.ajax({
            url: `/chat/history/${chatId}/delete/`,
            type: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                // 關閉模態視窗
                $('#deleteChatModal').modal('hide');
                
                // 移除對應的聊天記錄項目
                $(`.history-item[data-chat-id="${chatId}"]`).fadeOut(300, function() {
                    $(this).remove();
                    
                    // 如果所有聊天記錄都已刪除，顯示空記錄提示
                    if ($('.history-item').length === 0) {
                        $('.history-content').html(`
                            <div class="history-empty">
                                <i class="fas fa-comment-slash"></i>
                                <p>暫無聊天記錄</p>
                                <p>開始新對話來獲取餐廳推薦吧！</p>
                            </div>
                        `);
                    }
                });
                
                // 如果刪除的是當前正在查看的聊天記錄，顯示新對話
                if ($('#chatMessages').data('current-chat-id') === chatId) {
                    newChatBtn.click();
                }
                
                // 顯示成功訊息
                if (typeof showGlobalToast === 'function') {
                    showGlobalToast('聊天記錄已成功刪除');
                }
            },
            error: function(error) {
                console.error('刪除聊天記錄失敗:', error);
                
                // 顯示錯誤訊息
                if (typeof showGlobalToast === 'function') {
                    showGlobalToast('刪除聊天記錄失敗');
                }
            }
        });
    });
                
    // 新對話按鈕
    newChatBtn.on('click', function() {
        // 清空聊天記錄，顯示歡迎訊息
        $('#chatMessages').html(`
            <div class="message bot-message">
                <img src="/static/images/bot_avatar.png" alt="Bot" class="avatar">
                <div class="content">
                    <div class="sender">
                        餐廳推薦小幫手
                        <span class="time">${new Date().toLocaleTimeString('zh-TW', {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <div class="text">
                        <p>您好！歡迎使用餐廳推薦小幫手。我可以：</p>
                        <ul>
                            <li>根據您的偏好推薦適合的餐廳</li>
                            <li>提供附近熱門餐廳的訊息</li>
                            <li>幫您尋找特定類型的美食</li>
                            <li>提供餐廳的營業時間、評價和菜單建議</li>
                        </ul>
                        <p style="margin-bottom: 0;">請告訴我您想要尋找什麼類型的餐廳或美食？</p>
                    </div>
                </div>
            </div>
        `);
        
        // 在移動端自動隱藏側欄
        if ($(window).width() <= 992) {
            chatHistoryPanel.removeClass('active');
        }
    });
    
    // 每當用戶發送訊息後，自動儲存聊天記錄
    sendButton.on('click', sendMessage);
    
    // 按下 Enter 鍵發送
    $('#userInput').keypress(function(e) {
        if (e.which === 13) {
            sendMessage();
            return false; // 阻止表單提交
    }
    });
    
    // 發送訊息
    function sendMessage() {
        const userInput = $('#userInput').val().trim();
        
        if (userInput !== '') {
            // 添加用戶訊息到聊天窗口
        appendMessage('user', userInput);
        
            // 清空輸入框並禁用
            $('#userInput').val('').prop('disabled', true);
            $('#sendBtn').prop('disabled', true);
        
            // 顯示加載中動畫
        const loadingId = showLoading();
        
            // 準備請求數據
            const requestData = {
                message: userInput,
                preferences: userPreferences,
                location: userLocation
            };
            
            // 發送AJAX請求
        $.ajax({
            url: '/chat/send_message/',
            type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(requestData),
            headers: {
                    'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                    // 移除加載中動畫
                removeLoading(loadingId);
                
                    // 添加機器人回應
                    const botResponse = response.bot_response.content;
                    const placeCards = response.bot_response.place_cards || [];
                
                    // 處理前置圖片加載
                    if (placeCards && placeCards.length > 0) {
                        // 檢查餐廳卡片中的圖片路徑是否正確
                        placeCards.forEach(place => {
                            // 確保photo屬性存在，不再使用photo_url
                            if (!place.photo && place.photo_url) {
                                place.photo = place.photo_url;
                                delete place.photo_url;
                            }
                            
                            // 如果沒有圖片，添加默認圖片
                            if (!place.photo || place.photo.trim() === '') {
                                place.photo = '/static/images/default_restaurant.jpg';
            }
        });
    }
    
                    appendMessage('assistant', botResponse, placeCards);
                    
                    // 啟用輸入框
                    $('#userInput').prop('disabled', false).focus();
                    $('#sendBtn').prop('disabled', false);
                    
                    // 保存聊天記錄
                    saveChatContent();
                },
                error: function(error) {
                    // 移除加載中動畫
                    removeLoading(loadingId);
                    
                    console.error('發送訊息失敗:', error);
                    
                    // 添加錯誤訊息
                    appendMessage('assistant', '很抱歉，無法處理您的訊息。請稍後再試。');
                    
                    // 啟用輸入框
                    $('#userInput').prop('disabled', false).focus();
                    $('#sendBtn').prop('disabled', false);
                }
            });
        }
    }
    
    // 添加訊息到聊天框
    function appendMessage(sender, content, placeCards = null) {
        const chatMessages = $('#chatMessages');
        const messageTime = new Date().toLocaleTimeString('zh-TW', {hour: '2-digit', minute:'2-digit'});
        
        let messageHTML = '';
        
        if (sender === 'user') {
            messageHTML = `
            <div class="message user-message">
                <div class="content">
                    <div class="sender">
                        您
                        <span class="time">${messageTime}</span>
                    </div>
                    <div class="text">
                        <p>${content}</p>
                    </div>
                </div>
                    <img src="/static/images/default_avatar.jpg" alt="User" class="avatar" style="display:none;">
            </div>
            `;
        } else if (sender === 'assistant') {
            // 處理餐廳卡片
            let cardsHTML = '';
            if (placeCards && placeCards.length > 0) {
                cardsHTML = generateRestaurantCards(placeCards);
            }
            
            messageHTML = `
            <div class="message bot-message">
                <img src="/static/images/bot_avatar.png" alt="Bot" class="avatar">
                <div class="content">
                    <div class="sender">
                        餐廳推薦小幫手
                        <span class="time">${messageTime}</span>
                    </div>
                    <div class="text">
                        <p>${content}</p>
                        ${cardsHTML}
                    </div>
                </div>
            </div>
            `;
        }
        
        chatMessages.append(messageHTML);
        scrollToBottom();
    }
    
    // 生成餐廳卡片
    function generateRestaurantCards(places) {
        let cardsHTML = `
            <div class="restaurant-cards-scroll">
        `;
        
        places.forEach(place => {
            // 確保獲取所有可能的資料
            let imageUrl = place.photo || place.photos?.[0]?.getUrl?.() || place.image_url || place.photos?.[0]?.photo_reference || '/static/images/default_restaurant.jpg';
            let rating = place.rating ? parseFloat(place.rating).toFixed(1) : "暫無評分";
            let userRatingsTotal = place.user_ratings_total || '0';
            let priceLevel = '';
            let address = place.vicinity || place.formatted_address || place.address || '地址未知';
            let phone = place.formatted_phone_number || place.phone || place.international_phone_number || '電話未知';
            
            // 處理營業狀態
            let isOpen = '營業中';
            let statusClass = 'status-open';
            if (place.opening_hours) {
                if (place.opening_hours.isOpen?.() === true || place.opening_hours.open_now === true) {
                    isOpen = '營業中';
                    statusClass = 'status-open';
                } else {
                    isOpen = '已打烊';
                    statusClass = 'status-closed';
                }
            }
            
            if (place.price_level) {
                for (let i = 0; i < parseInt(place.price_level); i++) {
                    priceLevel += '￥';
                }
            } else {
                priceLevel = "價格未知";
            }
            
            cardsHTML += `
            <div class="restaurant-card" data-place-id="${place.place_id || ''}">
                <div class="card-header">
                    <h5 class="restaurant-name">${place.name}</h5>
                </div>
                <div class="restaurant-image">
                    <img src="${imageUrl}" alt="${place.name}" onerror="this.src='/static/images/default_restaurant.jpg'">
                </div>
                <div class="status-badge ${statusClass}">${isOpen}</div>
                <div class="restaurant-info">
                    <div class="restaurant-meta">
                        <span class="restaurant-rating">
                            ${rating} ${generateStars(place.rating || 0)} (${userRatingsTotal})
                        </span>
                        <span class="restaurant-price">
                            ${priceLevel}
                        </span>
                    </div>
                    <p class="restaurant-address">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${address}</span>
                    </p>
                    <p class="restaurant-phone">
                        <i class="fas fa-phone"></i>
                        <span>${phone}</span>
                    </p>
                    <div class="action-buttons">
                        <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name)}&query_place_id=${place.place_id || ''}" 
                            target="_blank" class="btn btn-map">
                            <i class="fas fa-info-circle"></i> 餐廳詳細資訊
                        </a>
                        <button class="btn btn-favorite favorite-btn" 
                            data-place-id="${place.place_id || ''}"
                            data-name="${place.name}"
                            data-address="${address}"
                            data-image="${imageUrl}"
                            data-rating="${place.rating || ''}"
                            data-price="${place.price_level || ''}"
                            data-lat="${place.lat || place.geometry?.location.lat || ''}"
                            data-lng="${place.lng || place.geometry?.location.lng || ''}">
                            <i class="far fa-star"></i> 收藏/儲存餐廳
                        </button>
                        <a href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(place.name)}&destination_place_id=${place.place_id || ''}" 
                            target="_blank" class="btn btn-navigation">
                            <i class="fas fa-directions"></i> 導航前往
                        </a>
                        ${place.website ? `
                        <a href="${place.website}" target="_blank" class="btn btn-website">
                            <i class="fas fa-globe"></i> 官方網站
                        </a>
                        ` : ''}
                    </div>
                </div>
            </div>
            `;
        });
        
        cardsHTML += `
            </div>
            <div class="scroll-controls">
                <button class="scroll-btn scroll-left" aria-label="向左滾動">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <button class="scroll-btn scroll-right" aria-label="向右滾動">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        // 添加輔助函數來生成星星
        function generateStars(rating) {
            const fullStar = '<i class="fas fa-star text-warning"></i>';
            const halfStar = '<i class="fas fa-star-half-alt text-warning"></i>';
            const emptyStar = '<i class="far fa-star text-warning"></i>';
            
            let stars = '';
            const ratingNum = parseFloat(rating);
            
            for (let i = 1; i <= 5; i++) {
                if (i <= ratingNum) {
                    stars += fullStar;
                } else if (i - 0.5 <= ratingNum) {
                    stars += halfStar;
                } else {
                    stars += emptyStar;
                }
            }
            
            return stars;
        }
        
        // 添加事件監聽器，讓函數返回後執行
        setTimeout(function() {
            // 為所有收藏按鈕添加事件監聽器
            document.querySelectorAll('.favorite-btn').forEach(button => {
                button.addEventListener('click', function() {
                    toggleFavoriteRestaurant(this);
                });
                
                // 檢查餐廳是否已被收藏
                const placeId = button.getAttribute('data-place-id');
                if (placeId) {
                    checkIfRestaurantFavorited(placeId).then(isFavorited => {
                        if (isFavorited) {
                            button.innerHTML = '<i class="fas fa-star"></i> 已收藏';
                            button.classList.add('favorited');
                        } else {
                            button.innerHTML = '<i class="far fa-star"></i> 收藏餐廳';
                        }
                    });
                }
            });
            
            // 添加左右滾動按鈕事件監聽器
            const scrollContainer = document.querySelector('.restaurant-cards-scroll');
            if (scrollContainer) {
                const scrollLeftBtn = document.querySelector('.scroll-left');
                const scrollRightBtn = document.querySelector('.scroll-right');
                
                if (scrollLeftBtn) {
                    scrollLeftBtn.addEventListener('click', function() {
                        scrollContainer.scrollBy({
                            left: -300,
                            behavior: 'smooth'
                        });
                    });
                }
                
                if (scrollRightBtn) {
                    scrollRightBtn.addEventListener('click', function() {
                        scrollContainer.scrollBy({
                            left: 300,
                            behavior: 'smooth'
                        });
                    });
                }
            }
        }, 100);
        
        return cardsHTML;
    }
    
    // 顯示加載中動畫
    function showLoading() {
        const loadingId = 'loading-' + Date.now();
        const loadingHTML = `
            <div id="${loadingId}" class="message bot-message">
                <img src="/static/images/bot_avatar.png" alt="Bot" class="avatar">
                <div class="content">
                    <div class="sender">
                        餐廳推薦小幫手
                        <span class="time">${new Date().toLocaleTimeString('zh-TW', {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <div class="text">
                        <div class="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('#chatMessages').append(loadingHTML);
        scrollToBottom();
        return loadingId;
    }
    
    // 移除加載中動畫
    function removeLoading(loadingId) {
        $(`#${loadingId}`).remove();
    }
    
    // 儲存聊天記錄的函數
    function saveChat(title, content) {
        $.ajax({
            url: '/chat/save_chat/',
            type: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            data: JSON.stringify({
                'title': title,
                'content': content
            }),
            success: function(response) {
                console.log('聊天記錄已儲存');
            },
            error: function(error) {
                console.error('儲存聊天記錄失敗:', error);
            }
        });
    }
    
    // 保存聊天內容
    function saveChatContent() {
        // 將第一個用戶問題作為標題
        let firstUserMessage = $('.user-message .text p').first().text();
        let chatTitle = firstUserMessage.substring(0, 30) + (firstUserMessage.length > 30 ? '...' : '');
        
        // 獲取當前聊天內容
        let chatContent = $('#chatMessages').html();
        
        // 延遲保存，確保所有內容都已渲染完成
        setTimeout(function() {
            saveChat(chatTitle, chatContent);
        }, 1000);
    }
    
    // 載入聊天記錄
    function loadChatHistory(chatId) {
        $.ajax({
            url: `/chat/history/${chatId}/`,
            type: 'GET',
            success: function(response) {
                if (response.content) {
                    // 清空當前聊天區域
                    $('#chatMessages').html(response.content);
                    // 記錄當前聊天記錄ID
                    $('#chatMessages').data('current-chat-id', chatId);
                } else {
                    appendMessage('assistant', '無法載入該聊天記錄。');
                }
                scrollToBottom();
            },
            error: function(error) {
                console.error('載入聊天記錄失敗:', error);
                appendMessage('assistant', '載入聊天記錄時發生錯誤，請稍後再試。');
                scrollToBottom();
            }
        });
    }
    
    // 滾動到聊天區域底部
    function scrollToBottom() {
        const messagesContainer = document.querySelector('.chat-messages-container');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    // 響應窗口大小改變
    $(window).resize(function() {
        if ($(window).width() > 992) {
            chatHistoryPanel.removeClass('active');
        }
    });
});

// 使用指南步驟導航（僅在關於頁面執行）
document.addEventListener('DOMContentLoaded', function() {
    const totalSteps = 6;
    let currentStep = 1;
    const prevBtn = document.getElementById('prevStep');
    const nextBtn = document.getElementById('nextStep');
    const stepIndicator = document.getElementById('stepIndicator');
    
    // 如果不在關於頁面，則退出
    if (!prevBtn || !nextBtn || !stepIndicator) {
        return;
    }
    
    // 更新步驟狀態
    function updateStepState() {
        // 隱藏所有步驟
        document.querySelectorAll('.guide-step').forEach(step => {
            step.style.display = 'none';
        });
        
        // 顯示當前步驟
        document.querySelector(`.guide-step[data-step="${currentStep}"]`).style.display = 'block';
        
        // 更新步驟指示器
        stepIndicator.textContent = `步驟 ${currentStep}/${totalSteps}`;
        
        // 更新按鈕狀態
        prevBtn.disabled = (currentStep === 1);
        if (currentStep === totalSteps) {
            nextBtn.textContent = '完成';
            nextBtn.innerHTML = '完成<i class="fas fa-check ms-2"></i>';
        } else {
            nextBtn.textContent = '下一步';
            nextBtn.innerHTML = '下一步<i class="fas fa-arrow-right ms-2"></i>';
        }
    }
    
    // 下一步按鈕點擊事件
    nextBtn.addEventListener('click', function() {
        if (currentStep < totalSteps) {
            currentStep++;
            updateStepState();
        } else {
            // 如果在最後一步，關閉模態框
            bootstrap.Modal.getInstance(document.getElementById('guideModal')).hide();
        }
    });
    
    // 上一步按鈕點擊事件
    prevBtn.addEventListener('click', function() {
        if (currentStep > 1) {
            currentStep--;
            updateStepState();
        }
    });
    
    // 模態框打開時重置步驟
    const guideModal = document.getElementById('guideModal');
    if (guideModal) {
        guideModal.addEventListener('show.bs.modal', function () {
            currentStep = 1;
            updateStepState();
        });
    }
});

// 檢查餐廳是否已被收藏
async function checkIfRestaurantFavorited(placeId) {
    try {
        const response = await fetch(`/user/restaurant/check_favorite/?place_id=${placeId}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.is_favorited;
        }
        return false;
    } catch (error) {
        console.error('檢查餐廳收藏狀態失敗:', error);
        return false;
    }
}

// 切換餐廳收藏狀態
function toggleFavoriteRestaurant(button) {
    const placeId = button.getAttribute('data-place-id');
    const name = button.getAttribute('data-name');
    const address = button.getAttribute('data-address');
    const imageUrl = button.getAttribute('data-image');
    const rating = button.getAttribute('data-rating');
    const priceLevel = button.getAttribute('data-price');
    const lat = button.getAttribute('data-lat');
    const lng = button.getAttribute('data-lng');
    
    const csrfToken = getCookie('csrftoken');
    
    const formData = new FormData();
    formData.append('restaurant_place_id', placeId);
    formData.append('restaurant_name', name);
    formData.append('restaurant_address', address);
    formData.append('restaurant_image_url', imageUrl);
    formData.append('restaurant_rating', rating);
    formData.append('restaurant_price_level', priceLevel);
    formData.append('restaurant_lat', lat);
    formData.append('restaurant_lng', lng);
    
    fetch('/user/restaurant/favorite/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (data.is_favorite) {
                // 已收藏狀態
                button.innerHTML = '<i class="fas fa-star"></i> 已收藏';
                button.classList.add('favorited');
                
                // 顯示成功訊息
                if (typeof showGlobalToast === 'function') {
                    showGlobalToast('已成功收藏餐廳');
                }
            } else {
                // 未收藏狀態
                button.innerHTML = '<i class="far fa-star"></i> 收藏餐廳';
                button.classList.remove('favorited');
                
                // 顯示成功訊息
                if (typeof showGlobalToast === 'function') {
                    showGlobalToast('已取消收藏餐廳');
                }
            }
        } else {
            // 顯示錯誤訊息
            if (typeof showGlobalToast === 'function') {
                showGlobalToast('操作失敗: ' + data.message);
            }
        }
    })
    .catch(error => {
        console.error('收藏餐廳操作失敗:', error);
        
        // 顯示錯誤訊息
        if (typeof showGlobalToast === 'function') {
            showGlobalToast('操作失敗，請稍後再試');
        }
    });
}

// 獲取CSRF Cookie
function getCookie(name) {
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
}