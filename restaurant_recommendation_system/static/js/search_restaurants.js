document.addEventListener("DOMContentLoaded", function() {
    const input = document.getElementById('restaurant-search-input');
    const form = document.getElementById('searchForm');

    // 即時搜尋（輸入後0.5秒自動送出表單）
    let timer = null;
    input.addEventListener('input', function() {
        clearTimeout(timer);
        timer = setTimeout(() => {
            form.submit();
        }, 500);
    });
});