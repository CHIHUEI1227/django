/**
 * 收藏餐廳頁面相關 JavaScript 功能
 * 包含確認對話框和收藏操作
 */

document.addEventListener('DOMContentLoaded', function() {
    // 防止意外點擊取消收藏
    const unfavoriteButtons = document.querySelectorAll('.favorited');
    unfavoriteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('確定要取消收藏此餐廳嗎?')) {
                e.preventDefault();
            }
        });
    });
    
    // 添加滾動控制功能
    const scrollContainer = document.querySelector('.restaurant-cards-scroll');
    if (scrollContainer) {
        const scrollLeftBtn = document.querySelector('.scroll-left');
        const scrollRightBtn = document.querySelector('.scroll-right');
        
        // 左滾動按鈕
        if (scrollLeftBtn) {
            scrollLeftBtn.addEventListener('click', function() {
                scrollContainer.scrollBy({
                    left: -300,
                    behavior: 'smooth'
                });
            });
        }
        
        // 右滾動按鈕
        if (scrollRightBtn) {
            scrollRightBtn.addEventListener('click', function() {
                scrollContainer.scrollBy({
                    left: 300,
                    behavior: 'smooth'
                });
            });
        }
        
        // 支持觸控滑動
        let isDown = false;
        let startX;
        let scrollLeft;

        scrollContainer.addEventListener('mousedown', (e) => {
            isDown = true;
            scrollContainer.classList.add('active');
            startX = e.pageX - scrollContainer.offsetLeft;
            scrollLeft = scrollContainer.scrollLeft;
        });
        
        scrollContainer.addEventListener('mouseleave', () => {
            isDown = false;
            scrollContainer.classList.remove('active');
        });
        
        scrollContainer.addEventListener('mouseup', () => {
            isDown = false;
            scrollContainer.classList.remove('active');
        });
        
        scrollContainer.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - scrollContainer.offsetLeft;
            const walk = (x - startX) * 2;
            scrollContainer.scrollLeft = scrollLeft - walk;
        });
    }
    
    console.log('收藏餐廳頁面 JavaScript 功能已載入');
}); 