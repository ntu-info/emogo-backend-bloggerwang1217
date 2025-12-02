# 情感追蹤應用 - API 上傳機制實現計劃

## 概述
將「I'm Emo Now」應用從完全本地儲存的 CSV 匯出方式改為實時 API 上傳機制。

---

## 用戶需求確認

| 需求 | 決策 |
|------|------|
| **用戶身份識別** | 無需註冊 - 每設備自動生成唯一 device_id |
| **影片存儲位置** | MongoDB GridFS（內置大檔案支持） |
| **離線支持** | 本地上傳隊列 + 自動重試機制 |
| **API 架構** | 分離式：先上傳元資料 → 再上傳影片 |

---

## 前端必須修改的檔案

### 1. 新增檔案
- `utils/device.ts` - Device ID 管理
- `utils/api.ts` - API 服務層
- `utils/uploadQueue.ts` - 上傳隊列管理

### 2. 修改檔案
- `utils/database.ts` - 新增 upload_queue 表格
- `app/(drawer)/index.tsx` - 修改提交流程
- `app/(drawer)/history.tsx` - 添加上傳狀態顯示
- `app/(drawer)/settings.tsx` - 隊列管理介面
- `app/_layout.tsx` - 上傳服務初始化
- `package.json` - 新增依賴

### 3. 資料庫修改
```sql
CREATE TABLE IF NOT EXISTS upload_queue (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  device_id TEXT NOT NULL,
  emotion_score INTEGER NOT NULL,
  latitude REAL,
  longitude REAL,
  timestamp TEXT NOT NULL,
  video_filename TEXT NOT NULL,
  video_uri TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  retry_count INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT
);

ALTER TABLE sessions ADD COLUMN device_id TEXT;
ALTER TABLE sessions ADD COLUMN upload_status TEXT DEFAULT 'pending';
ALTER TABLE sessions ADD COLUMN server_id TEXT;
```

---

## 後端實現架構

### 項目結構
```
backend/
├── main.py                 # 應用入口
├── models/
│   ├── __init__.py
│   └── session.py         # MongoDB 模型
├── routes/
│   ├── __init__.py
│   ├── sessions.py        # API 路由
│   └── health.py          # 健康檢查
├── config.py              # 設定管理
├── requirements.txt
└── .env                   # 環境變量
```

### API 端點
- `POST /api/sessions` - 建立會話
- `POST /api/sessions/{session_id}/video` - 上傳影片
- `GET /api/sessions/{device_id}` - 取得設備會話
- `GET /api/sessions/{session_id}/video` - 下載影片
- `GET /api/sessions/export` - 匯出 CSV
- `DELETE /api/sessions/{session_id}` - 刪除會話
- `GET /health` - 健康檢查

### Requirements
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pymongo==4.6.0
python-dotenv==1.0.0
python-multipart==0.0.6
pydantic==2.5.0
```

---

## MongoDB 設定

### Collections 設計

#### sessions 集合
```javascript
{
  "_id": ObjectId(),
  "device_id": "uuid",
  "emotion_score": 1-5,
  "latitude": number,
  "longitude": number,
  "timestamp": "ISO format",
  "video_id": ObjectId(),
  "created_at": "ISO format",
  "updated_at": "ISO format"
}
```

#### 索引建議
```javascript
db.sessions.createIndex({ "device_id": 1 })
db.sessions.createIndex({ "timestamp": -1 })
db.sessions.createIndex({ "device_id": 1, "timestamp": -1 })
db.sessions.createIndex({ "created_at": 1 }, { expireAfterSeconds: 7776000 })
```

#### GridFS（自動建立）
- fs.files - 影片元資料
- fs.chunks - 影片二進制資料

---

## MongoDB Atlas 快速設定

1. **建立帳戶**：https://www.mongodb.com/cloud/atlas
2. **創建免費叢集**：Shared (Free)
3. **創建用戶**：Database → Users → Add Database User
4. **設定網絡訪問**：Allow access from anywhere
5. **取得連接字符串**：Clusters → Connect → Drivers

連接字串格式：
```
mongodb+srv://emo_now:<password>@<cluster>.mongodb.net/emo_now
```

---

## 部署檢查清單

### MongoDB Atlas
- [ ] 帳戶已建立
- [ ] 免費叢集已建立
- [ ] 資料庫用戶已建立
- [ ] 網絡訪問已設定
- [ ] 連接字符串已保存

### 後端（Linode）
- [ ] 購買/設定伺服器
- [ ] 安裝 Python 3.10+
- [ ] 安裝依賴
- [ ] 設定防火牆（開啟 8000、443 端口）
- [ ] 使用 systemd 運行 FastAPI
- [ ] 設定 HTTPS (Let's Encrypt)
- [ ] 測試 MongoDB Atlas 連接

### 前端
- [ ] 設定 API 基礎 URL
- [ ] 測試上傳場景
- [ ] 測試離線重連
- [ ] 構建發佈版本

---

## 關鍵技術決策

### 為何分離元資料和影片上傳？
- 元資料快速上傳，影片在後台上傳
- 失敗時只需重試影片部分
- 用戶能立即看到數據

### 為何使用 GridFS？
- MongoDB 原生支持
- 不需額外文件服務
- 自動分塊處理大檔案

### 為何使用 device_id？
- 無需登錄，零摩擦體驗
- 適合研究應用
- 未來可升級為用戶認證

---

## 安全考慮

### 檔案驗證
- ✅ 限制檔案大小（50-100MB）
- ✅ 驗證檔案類型（MIME type）
- ✅ 檔案名稱消毒

### API 保護
- ✅ 配置 HTTPS
- ✅ 速率限制
- ⚠️ 無認證（研究用途）

### 資料隱私
- ✅ 使用 HTTPS 加密 GPS 資料
- ✅ 設定 TTL 索引（90 天自動刪除）
- ⚠️ 無認證機制

---

## 實現步驟

### Phase 1: 前端基礎（第 1-2 天）
1. Device ID 管理模組
2. API 服務層
3. 上傳隊列管理
4. 資料庫新增表格
5. 網絡監聽整合

### Phase 2: 前端 UI（第 2-3 天）
1. 修改提交流程
2. 修改歷史頁
3. 修改設定頁
4. 測試離線場景

### Phase 3: 後端開發（第 3-5 天）
1. FastAPI 專案初始化
2. MongoDB 連接
3. 會話路由
4. 影片上傳（GridFS）
5. Linode 部署

### Phase 4: 集成測試（第 5-6 天）
1. 前後端端對端測試
2. 離線/重連測試
3. 影片完整性驗證
4. 性能和安全檢查

---

## 下一步改進（Phase 2+）

1. **用戶認證** - 支持跨設備同步
2. **資料可視化** - 情感趨勢分析
3. **影片分享** - 社交媒體集成
4. **AI 分析** - 情感識別
5. **研究工具** - 批量匯出和統計
