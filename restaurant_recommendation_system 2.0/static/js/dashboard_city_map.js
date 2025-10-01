document.addEventListener("DOMContentLoaded", function() {
    var map = L.map('taiwanMap').setView([23.7, 121], 7.2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // 取得縣市統計資料
    var cityStats = JSON.parse(document.getElementById('city-stats-data').textContent);

    // 取得 GeoJSON 路徑
    var geojsonUrl = document.getElementById('taiwanMap').dataset.geojsonUrl;

    // 設定漸層顏色
    function getColor(d) {
        return d > 20 ? '#00441b' :
               d > 10 ? '#238b45' :
               d > 5  ? '#41ae76' :
               d > 0  ? '#66c2a4' :
                        '#ccece6';
    }

    // 載入台灣縣市GeoJSON
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
            }
        }).addTo(map);
    });
});