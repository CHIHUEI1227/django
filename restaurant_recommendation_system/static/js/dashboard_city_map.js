document.addEventListener("DOMContentLoaded", function() {
    var map = L.map('taiwanMap').setView([23.7, 121], 7.2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    var cityStats = JSON.parse(document.getElementById('city-stats-data').textContent);
    var cityPosts = JSON.parse(document.getElementById('city-posts-data').textContent);
    var geojsonUrl = document.getElementById('taiwanMap').dataset.geojsonUrl;

    function getColor(d) {
        return d > 20 ? '#00441b' :
               d > 10 ? '#238b45' :
               d > 5  ? '#41ae76' :
               d > 0  ? '#66c2a4' :
                        '#ccece6';
    }

    // 切換分頁顯示
    function switchTab(tab) {
        const cityListBtn = document.getElementById('showCityListBtn');
        const cityPostsBtn = document.getElementById('showCityPostsBtn');
        const cityListBlock = document.getElementById('cityListBlock');
        const cityPostsBlock = document.getElementById('cityPostsBlock');
        if (tab === 'list') {
            cityListBtn.classList.add('active');
            cityPostsBtn.classList.remove('active');
            cityListBlock.style.display = '';
            cityPostsBlock.style.display = 'none';
        } else {
            cityListBtn.classList.remove('active');
            cityPostsBtn.classList.add('active');
            cityListBlock.style.display = 'none';
            cityPostsBlock.style.display = '';
        }
    }

    // 綁定分頁按鈕
    document.getElementById('showCityListBtn').onclick = function() {
        switchTab('list');
    };
    document.getElementById('showCityPostsBtn').onclick = function() {
        switchTab('posts');
    };

    function showCityPosts(city) {
        // 切換到貼文記錄分頁
        switchTab('posts');
        var posts = cityPosts[city] || [];
        var container = document.getElementById('cityPosts');
        var postsHtml = '';
        if (posts.length === 0) {
            postsHtml = `<div class="text-muted">尚無貼文</div>`;
        } else {
            postsHtml = `<h6 class="mb-2">${city} 貼文：</h6><ul class="list-group mb-2">` +
                posts.map(p => `<li class="list-group-item">${p}</li>`).join('') +
                `</ul>`;
        }
        container.innerHTML = postsHtml;
    }

    fetch(geojsonUrl)
    .then(response => response.json())
    .then(geojsonData => {
        L.geoJson(geojsonData, {
            style: function(feature) {
                var name = feature.properties.COUNTYNAME;
                var count = cityStats[name] || 0;
                return {
                    fillColor: getColor(count),
                    weight: 1,
                    opacity: 1,
                    color: '#fff',
                    fillOpacity: 0.7
                };
            },
            onEachFeature: function(feature, layer) {
                var name = feature.properties.COUNTYNAME;
                var count = cityStats[name] || 0;
                layer.bindPopup(name + "：" + count + " 筆");
                layer.on('click', function() {
                    showCityPosts(name);
                    layer.openPopup();
                });
            }
        }).addTo(map);
    });

    // 點選清單也能顯示貼文記錄
    document.querySelectorAll('.city-list-item').forEach(function(item) {
        item.addEventListener('click', function() {
            var city = this.dataset.city;
            showCityPosts(city);
        });
    });

    // 預設顯示縣市列表
    switchTab('list');
});