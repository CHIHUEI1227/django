// Google Map API 初始化範例，可供 demo 用
let map;
function initMap() {
    // 地圖中心設為涮樂和牛鍋物 西門旗艦店座標
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 25.04357, lng: 121.5064556 },
        zoom: 19,
        styles: [
            {
                featureType: "poi",
                elementType: "labels",
                stylers: [{ visibility: "off" }]
            }
        ]
    });

    // 只顯示涮樂和牛鍋物 西門旗艦店的 marker，座標精確設為 25.04357,121.5064556
    new google.maps.Marker({
        position: { lat: 25.0435946, lng: 121.5070705 },
        map: map,
        title: "涮樂和牛鍋物 西門旗艦店"
    });
}
// 這個檔案可供其他頁面引用
