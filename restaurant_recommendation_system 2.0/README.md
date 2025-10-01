# 餐廳推薦系統

一個基於Django的智能餐廳推薦系統，結合AI和地理位置服務，提供個性化餐廳推薦，並支援使用者社交互動功能。

## 系統功能一覽

### 核心功能
- **智能聊天推薦**：基於自然語言處理，理解用戶需求並推薦餐廳
- **AI模型支持**：採用Google Gemini模型提供智能回應
- **地理位置感知**：支援基於城市、區域的搜索功能
- **價格篩選**：可根據"平價"($$及以下)、"高級"等價格描述準確推薦餐廳
- **餐廳卡片展示**：顯示餐廳評分、價格、照片、營業時間等完整信息
- **顧客評價摘要**：展示用戶評論，幫助快速了解餐廳特色
- **一鍵導航**：內建地圖查看和導航功能，方便用戶前往餐廳
- **個人化偏好系統**：從用戶對話、發文和收藏中自動學習偏好，提供個性化推薦

### 用戶帳號系統
- **用戶註冊與登入**：支援一般使用者和商家兩種帳號類型
- **個人資料管理**：用戶可更新頭像、自我介紹和食物偏好
- **商家申請與驗證**：商家可提交資料申請認證，經管理員審核
- **多層級帳號體系**：一般用戶、商家用戶（經認證後顯示商家標識）和管理員權限分級

### 社交互動功能
- **發布貼文**：用戶可分享美食體驗和推薦，支援地點選擇功能
- **互動系統**：支援貼文收藏和用戶關注功能
- **個人動態牆**：顯示關注用戶的最新貼文
- **探索頁面**：展示平台熱門和精選內容
  - 精選推薦：平台推薦的優質貼文
  - 熱門貼文：按收藏數量排序的熱門內容
  - 最新貼文：最近發布的內容
- **評論與回覆系統**：支援對貼文進行評論和回覆
- **表情符號反應**：用戶可使用多種表情符號對貼文表達反應

### 商家功能
- **商家驗證流程**：上傳營業登記證明文件進行身份驗證
- **商家標識顯示**：經過驗證的商家在名字旁顯示商家標籤
- **商家資料管理**：更新商家名稱、地址、聯絡方式等基本資訊

### 地圖集成功能
- **地點選擇**：發布貼文時可通過Google Maps搜索並選擇餐廳位置
- **位置顯示**：貼文中顯示餐廳名稱、地址和互動式地圖
- **一鍵導航**：直接獲取前往餐廳的導航路線

### 管理功能
- **商家認證管理**：審核商家驗證申請，批准或拒絕
- **內容管理**：管理員可刪除不適當的貼文
- **平台推薦設置**：管理員可設置精選貼文，在探索頁面推廣
- **舉報處理**：管理員處理用戶舉報的內容

### 個人化功能
- **偏好學習**：自動學習用戶飲食偏好
- **收藏管理**：用戶可收藏喜愛的貼文以便日後瀏覽
- **貼文置頂**：用戶可將自己的特定貼文置頂於個人頁面
- **關注與粉絲**：查看關注者和粉絲列表

### 通知系統
- **互動通知**：收到評論、回覆、關注、收藏等互動時獲得通知
- **系統通知**：接收系統重要更新和公告

## 技術架構

- **後端**：Python Django框架
- **前端**：HTML, CSS, JavaScript, Bootstrap 5
- **數據庫**：SQLite (開發環境)，支持PostgreSQL(生產環境)
- **API集成**：
  - Google Places API：餐廳搜索和詳細信息獲取
  - Google Search API：網頁信息檢索
  - Google Gemini API：提供AI模型服務

## 特色亮點

- **Google Gemini 模型**：採用Google提供的高效AI模型
- **台灣地區精確定位**：內建台灣縣市鄉鎮區經緯度數據，精確處理台灣各地區搜索請求
- **價格智能映射**：準確理解"平價"、"高級"等描述詞並對應至適當價格級別
- **響應式設計**：適配桌面和移動設備的現代化UI
- **豐富的餐廳資訊**：包含評分、評論、照片、營業時間和聯絡方式等全方位信息
- **簡潔回應格式**：AI回應精準簡潔，突出重要信息
- **多管道偏好學習**：從對話、貼文、收藏等多種用戶行為中自動學習偏好
- **偏好時間衰減**：偏好系統支持基于時間的偏好強度衰減，確保推薦的時效性
- **社交互動**：用戶可互相關注、分享美食體驗，建立美食社群
- **商家電子名片**：驗證商家擁有專業標識，提升可信度

## API 認證使用說明

系統現已支持通過Token認證方式進行API存取。以下是使用方法：

### 獲取Token

```
POST /api/token/
Content-Type: application/json

{
    "username": "你的用戶名",
    "password": "你的密碼"
}
```

成功響應：

```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "username": "用戶名"
}
```

### 使用Token存取API

在後續所有API請求中，添加以下請求頭：

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 登出（使Token失效）

```
POST /api/logout/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### 可用的API端點

- `GET /api/profile/` - 獲取當前用戶資料
- `GET /api/posts/` - 獲取所有帖子
- `POST /api/posts/` - 創建新帖子
- `GET /api/posts/{id}/` - 獲取特定帖子
- `PUT /api/posts/{id}/` - 更新帖子
- `DELETE /api/posts/{id}/` - 刪除帖子
- `GET /api/comments/?post_id={post_id}` - 獲取特定帖子的評論
- `POST /api/comments/` - 創建評論

## 系統需求

- Python 3.8+
- Django 4.0+
- 必要的API金鑰：
  - Google Places API
  - Google Search API (選用)
  - Google Gemini API

## 安裝與設置

1. 克隆存儲庫：

```bash
git clone https://github.com/yourusername/restaurant_recommendation_system.git
cd restaurant_recommendation_system
```

2. 創建虛擬環境並激活：

```bash
python -m venv venv
source venv/bin/activate  # 在Linux/Mac上
venv\Scripts\activate  # 在Windows上
```

3. 安裝依賴：

```bash
pip install -r requirements.txt
```

4. 設置環境變數（API金鑰）：

```bash
# Linux/Mac
export GOOGLE_PLACES_API_KEY="your_key_here"
export GOOGLE_SEARCH_API_KEY="your_key_here"
export GOOGLE_CX_ID="your_cx_id_here"
export GEMINI_API_KEY="your_gemini_key_here"

# Windows
set GOOGLE_PLACES_API_KEY=your_key_here
set GOOGLE_SEARCH_API_KEY=your_key_here
set GOOGLE_CX_ID=your_cx_id_here
set GEMINI_API_KEY=your_gemini_key_here
```

5. 運行數據庫遷移：

```bash
python manage.py makemigrations
python manage.py migrate
```

6. 創建超級用戶（可選）：

```bash
python manage.py createsuperuser
```

7. 啟動開發服務器：

```bash
python manage.py runserver
```

應用將在 http://127.0.0.1:8000/ 上運行。

## 項目結構

- `restaurant_recommendation_system/`: 主要Django項目設置
- `chat/`: 聊天和餐廳推薦功能核心應用
  - `tools/`: API工具類目錄
    - `places_api.py`: Google Places API工具類
    - `gemini_api.py`: Google Gemini API工具類
    - `search_api.py`: Google搜索API工具類
    - `menu_scraper.py`: 菜單抓取工具
    - `llm_factory.py`: LLM工廠類，用於創建大型語言模型的實例
  - `restaurant_controller.py`: 控制層，協調用戶查詢處理和回應生成
  - `preference_service.py`: 用戶偏好服務，處理偏好學習和應用
- `user/`: 用戶管理和個人資料功能
  - `models.py`: 定義用戶資料、貼文、收藏、關注等資料模型
  - `views.py`: 處理用戶相關請求和頁面渲染
  - `forms.py`: 定義用戶註冊、資料更新、貼文創建等表單
- `templates/`: HTML模板文件
  - `chat/`: 聊天界面模板
  - `user/`: 用戶相關頁面模板
  - `post/`: 貼文相關頁面模板
  - `social/`: 社交互動相關頁面模板
  - `notification/`: 通知系統相關頁面模板
  - `report/`: 舉報系統相關頁面模板
  - `business/`: 商家功能相關頁面模板
  - `admin/`: 管理員功能相關頁面模板
- `static/`: 靜態文件
  - `json/town.json`: 台灣縣市鄉鎮區地理數據
  - `images/`: 圖片資源
  - `css/`: 樣式表
  - `js/`: JavaScript文件
- `media/`: 用戶上傳的媒體文件
  - `profile_pics/`: 用戶頭像
  - `post_images/`: 貼文圖片
  - `verification_documents/`: 商家認證文件

## 使用指南

### 聊天推薦
1. 註冊/登入系統
2. 進入聊天室與美食推薦助手互動
3. 詢問特定地區、類型或價格的餐廳推薦
   - 示例：「推薦基隆的平價燒烤店」
   - 示例：「台北市有什麼好吃的日本料理？」
4. 查看餐廳推薦卡片，獲取詳細信息
5. 點擊「查看地圖」或「導航前往」前往餐廳

### 社交功能
1. 發布美食體驗貼文，分享照片和心得
   - 可通過Google地圖搜索並添加餐廳位置
   - 添加照片豐富貼文內容
2. 關注其他用戶，在動態牆查看他們的最新貼文
3. 收藏喜愛的貼文
4. 瀏覽探索頁面發現熱門內容

### 商家功能
1. 註冊商家帳號
2. 提交商家認證資料
3. 審核通過後獲得商家標識
4. 管理商家資料和展示信息

## 目前支援的查詢類型

- 地區餐廳查詢：「高雄有什麼好吃的？」
- 特定料理類型：「推薦台中的義式餐廳」
- 價格範圍篩選：「平價的台南小吃」、「台北高級日料」
- 混合查詢：「台中西區有沒有平價的韓式烤肉？」

## AI模型配置

系統採用 Google Gemini 作為AI引擎，此模型提供高效的自然語言處理能力，為系統默認選項。

## 未來計劃

- 擴展餐廳標籤系統，支援更多特色標籤
- 優化偏好系統的權重計算，提高推薦準確度
- 加入餐廳評分功能
- 增加餐廳預訂功能
- 支援更多AI功能
- 改進貼文內容檢索能力

## 貢獻

歡迎貢獻！請隨時提交問題或拉取請求。 