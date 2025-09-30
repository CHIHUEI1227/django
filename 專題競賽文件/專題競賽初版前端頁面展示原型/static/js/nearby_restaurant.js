
// 讀取 store_intros.json 的前三筆資料

window.demoStores = [
  {
    編號: "ChIJG-ssCcupQjQREy2mh1fvk_E",
    店名: "涮樂和牛鍋物 西門旗艦店",
    地址: "108台灣台北市萬華區峨眉街37號3樓",
    店家簡述: "氛圍愜意的休閒火鍋店，提供自助式服務，並附設燒烤桌。",
    店家googleMap: "https://maps.google.com/?cid=17407520143934106899",
    經緯度: "25.0436036,121.5071821"
  },
  {
    編號: "ChIJF45D7h-pQjQRo5SS_f8tmfo",
    店名: "尚品屋精緻鍋物-萬大店",
    地址: "108台灣台北市萬華區萬大路423巷54號",
    店家簡述: "氣氛悠閒的繽紛工業風餐廳，供應搭配肉品、海鮮和蔬菜的火鍋。",
    店家googleMap: "https://maps.google.com/?cid=18057514758412866723",
    經緯度: "25.02187259999999,121.5015647"
  },
  {
    編號: "ChIJI8A3Hu6pQjQR_hz5DGcLYbI",
    店名: "前鎮水產-海霸王 昆明店",
    地址: "108台灣台北市萬華區昆明街46號",
    店家簡述: "溫馨的餐館，供應粄條和豬肚等台式美食，並設有戶外座位。",
    店家googleMap: "https://maps.google.com/?cid=12853567348719295742",
    經緯度: "25.0465721,121.5056705"
  }
];

function searchNearbyRestaurants() {
    const listDiv = document.getElementById("restaurant-list");
    listDiv.innerHTML = "";
    demoStores.forEach(store => {
        const fakeIndicators = {
            food: Math.floor(Math.random() * 3) + 3,
            price: Math.floor(Math.random() * 3) + 3,
            service: Math.floor(Math.random() * 3) + 3,
            environment: Math.floor(Math.random() * 3) + 3
        };
        const card = document.createElement("div");
        card.className = "card mb-3 system-card";
    card.innerHTML = `
      <div class="card-body">
        <div class="mb-2 text-center">
          <img src="../../img/${store.編號}.jpg" alt="${store.店名}" style="max-width:100%;max-height:160px;border-radius:10px;object-fit:cover;">
        </div>
        <h5 class="card-title">${store.店名}</h5>
        <div class="mb-1"><strong>地址：</strong>${store.地址}</div>
        <p class="card-text">${store.店家簡述 || ''}</p>
        <ul class="list-inline mb-2">
          <li class="list-inline-item"><strong>食物：</strong>${fakeIndicators.food}/5</li>
          <li class="list-inline-item"><strong>價錢：</strong>${fakeIndicators.price}/5</li>
          <li class="list-inline-item"><strong>服務：</strong>${fakeIndicators.service}/5</li>
          <li class="list-inline-item"><strong>環境：</strong>${fakeIndicators.environment}/5</li>
        </ul>
        <a href="${store["店家googleMap"]}" target="_blank" class="btn btn-outline-primary detail-btn w-100 mt-2">詳細資料</a>
      </div>
    `;
        listDiv.appendChild(card);
    });
}
