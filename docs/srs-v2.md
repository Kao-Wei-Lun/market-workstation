# 本地化個人股票分析與監控系統需求規格書（V2）
## 版本名稱
V2：台股即時增強版（V1 + 富邦 API 即時資料）

## 文件資訊
- 文件代號：SRS-V2
- 文件版本：1.0
- 文件狀態：正式版
- 適用階段：第二版開發
- 系統定位：在 V1 本地化日資料系統基礎上，新增台股即時行情處理能力

---

# 1. 專案概述

## 1.1 專案目標
在 V1 盤後日資料版的完整基礎上，新增台股即時行情接收、即時監控、即時 UI 顯示與即時資料流處理能力，使系統同時支援：
- 每日盤後研究
- 台股盤中即時監控
- 即時警示與即時觀察面板

## 1.2 V2 範圍
V2 包含 V1 所有功能，並新增：
- 富邦 API 串接
- 台股即時報價
- 台股即時成交資訊
- 台股即時成交量
- 台股即時五檔/委買委賣（若 API 提供）
- 即時資料寫入流程
- WebSocket worker
- 即時監控頁面資料來源
- 即時警示基礎能力

## 1.3 非範圍項目
V2 仍不包含：
- 美股即時行情
- 自動下單
- 雲端多人即時分享
- 對外資料再散布 API
- 行動裝置推播系統
- 企業級帳號/權限/審批

---

# 2. 與 V1 的關係

## 2.1 延續性
V2 必須完全延續 V1 的底層架構：
- PostgreSQL 不更換
- 資料表設計只做向前擴充
- 不重做 ETL 核心
- 不重做 API service
- 不重做 worker 基礎框架

## 2.2 差異點
V2 相較 V1 的主要新增能力：
- 即時資料來源接入
- 即時資料流處理
- 即時監控 API
- 即時資料儲存與快取
- 即時警示規則引擎

---

# 3. 系統總體架構

## 3.1 共同底層架構
V2 與 V1 共用：
- db
- api
- scheduler
- analysis
- config 外部化
- Docker Compose
- 遷移機制
- VS Code + Codex 開發流程

## 3.2 新增元件
### Realtime Worker
負責：
- 富邦 API 登入
- WebSocket 建立
- 訂閱管理
- 斷線重連
- 訊息正規化
- 即時資料落地/快取
- 指標事件觸發
- 警示事件觸發

### Optional Redis
V2 建議啟用 Redis，作為：
- 即時最新狀態快取
- 訂閱狀態表
- 警示節流
- worker 協調
- UI 快速查詢層

## 3.3 Docker Compose 服務規格
V2 必備服務：
- db
- api
- scheduler
- analysis
- realtime
- optional redis

---

# 4. 功能需求

# 4.1 繼承 V1 功能
V2 必須完整保留 V1 所有功能，包括：
- 台股/美股/全球指數/原物料/總經日資料
- 股票分類
- 技術指標
- 回測
- 台灣法人期貨/選擇權分析
- 每日報表

---

# 4.2 台股即時行情接入

## FR-100 富邦 API 連線設定
系統需支援透過設定檔提供以下資訊：
- 帳號
- 密碼
- 憑證路徑
- 憑證密碼
- API 環境設定
- 訂閱列表
- 連線參數

## FR-101 即時登入與初始化
Realtime Worker 啟動後需：
- 載入設定
- 檢查憑證
- 建立登入 session
- 初始化 market data client
- 建立 WebSocket 連線
- 啟動訂閱流程

## FR-102 訂閱標的管理
系統需支援：
- 從 watchlist 載入訂閱標的
- 從群組計算訂閱標的
- 手動新增/移除訂閱
- 限額控制
- 多批次訂閱

## FR-103 訂閱資料類型
至少需支援：
- 最新成交
- 報價
- 成交量
- 指數
- 委買委賣/五檔（若來源支援）
- odd lot 參數（若來源支援）

## FR-104 即時資料正規化
接收後需轉換為內部統一格式，至少包含：
- instrument_id
- event_ts
- event_type
- last_price
- last_qty
- cumulative_volume
- bid_price_1~5
- bid_qty_1~5
- ask_price_1~5
- ask_qty_1~5
- source
- raw_payload_hash

## FR-105 即時狀態維護
系統需維護每檔股票的 latest snapshot，供 API 與 UI 快速查詢。

---

# 4.3 即時資料儲存與快取

## FR-110 即時 tick 儲存
系統需可將即時成交或快照資料寫入資料庫或分層儲存表。

## FR-111 即時最新狀態快取
系統需將每檔最新即時狀態保存在快取層，供毫秒級到秒級查詢。

## FR-112 分鐘聚合（可選）
V2 需預留 tick-to-bar 聚合能力，至少可在後續擴充成：
- 1m
- 5m
- 15m

## FR-113 寫入策略
為避免寫入壓力過高，需支援：
- tick 落地
- snapshot 落地
- micro-batch
- debounce
- flush interval

---

# 4.4 即時監控與警示

## FR-120 即時監控 API
API service 需提供：
- 單檔即時最新狀態
- watchlist 即時狀態
- 群組即時狀態
- 訂閱清單
- 連線健康度
- lag 指標

## FR-121 即時警示規則
需支援基本規則：
- 價格突破
- 漲跌幅超過門檻
- 成交量異常
- 委買委賣異常
- 分類群組同步異動
- 自訂條件警示

## FR-122 警示節流
系統需支援：
- cooldown
- 去重
- 同條件短時間不重複通知
- 日內最大觸發次數

## FR-123 即時群組觀察
對群組提供：
- 即時漲跌幅排序
- 成交量排行
- 漲停/跌停監控
- 異常股票列表

---

# 4.5 即時資料品質與穩定性

## FR-130 斷線重連
Realtime Worker 若斷線需：
- 自動重連
- 重建 session
- 重送訂閱
- 重建快取狀態

## FR-131 連線健康檢查
需監控：
- last_message_time
- connection_state
- reconnect_count
- lag_seconds
- dropped_events_count

## FR-132 限流與降級
若遇到資料來源限制、訂閱上限或內部壓力過高，系統需支援：
- 降低非必要訂閱
- 暫停低優先級群組
- 只保留核心 watchlist
- 降低落地頻率

---

# 4.6 即時與日資料整合

## FR-140 同步主檔
即時資料使用的台股標的主檔需與 V1 的 instruments 共用。

## FR-141 盤後回補
日終後需可將日內即時資訊與盤後正式資料對帳。

## FR-142 即時與日資料一致性
需可定義：
- intraday provisional state
- official end-of-day state

## FR-143 即時觀察與盤後研究連結
使用者可從即時異常事件直接跳到：
- 日線資料
- 技術指標
- 分類群組
- 歷史回測條件

---

# 5. 非功能需求

## NFR-100 7x24 持續運行
系統需支援持續常駐運行，並可在台股開盤時段穩定處理即時資料。

## NFR-101 穩定性
Realtime Worker 需支援：
- 自動重啟
- 心跳檢查
- 失敗重試
- reconnect backoff

## NFR-102 效能
在訂閱上限內，單一即時事件應可於可接受時間內完成：
- 正規化
- 快取更新
- 必要時落地

## NFR-103 可觀測性
需記錄：
- 錯誤日誌
- reconnect log
- lag metrics
- subscription metrics
- write throughput

## NFR-104 安全性
富邦 API 帳密與憑證資訊必須外部化，且不得寫入版本控制。

---

# 6. 統一資料庫設計（V2 擴充）

V2 延續 V1 全部 schema，新增以下表。

## 6.1 realtime_ticks
- id
- instrument_id
- event_ts
- event_type
- last_price
- last_qty
- cumulative_volume
- source
- raw_payload_json
- created_at

## 6.2 realtime_orderbook_snapshots
- id
- instrument_id
- event_ts
- bid_price_1
- bid_qty_1
- bid_price_2
- bid_qty_2
- bid_price_3
- bid_qty_3
- bid_price_4
- bid_qty_4
- bid_price_5
- bid_qty_5
- ask_price_1
- ask_qty_1
- ask_price_2
- ask_qty_2
- ask_price_3
- ask_qty_3
- ask_price_4
- ask_qty_4
- ask_price_5
- ask_qty_5
- source
- created_at

## 6.3 realtime_latest_state
- instrument_id
- last_event_ts
- last_price
- last_qty
- cumulative_volume
- bid_json
- ask_json
- connection_source
- updated_at

## 6.4 realtime_subscriptions
- id
- instrument_id
- channel_type
- is_active
- priority
- created_at
- updated_at

## 6.5 realtime_alert_events
- id
- instrument_id
- alert_type
- alert_key
- triggered_at
- payload_json
- cooldown_until

## 6.6 worker_health
- worker_name
- worker_type
- status
- heartbeat_at
- metrics_json
- updated_at

---

# 7. 排程與即時流程

## SCH-100 繼承 V1 排程
V2 保留所有 V1 日資料排程。

## SCH-101 啟動時即時載入
realtime worker 啟動時需：
- 讀取 watchlist
- 讀取群組高優先級清單
- 建立訂閱任務

## SCH-102 盤中監控
系統需在台股交易時段內維持即時連線，盤後可自動降載或停止非必要訂閱。

## SCH-103 日終封存
日終後需可執行：
- snapshot flush
- stats aggregation
- intraday cleanup
- 與盤後資料整合

---

# 8. Docker 與部署規格

## 8.1 V2 Compose 服務
- db
- api
- scheduler
- analysis
- realtime
- optional redis

## 8.2 Realtime 服務需求
realtime service 需具備：
- restart policy
- healthcheck
- log rotation
- env-based configuration

## 8.3 資源配置
需可透過環境變數調整：
- worker concurrency
- batch size
- flush interval
- subscription priority
- reconnect policy

---

# 9. API 需求

## 9.1 盤後查詢 API
延續 V1：
- instruments
- daily bars
- indicators
- reports
- backtests
- classifications

## 9.2 即時查詢 API
新增：
- `/api/realtime/latest`
- `/api/realtime/watchlist`
- `/api/realtime/group`
- `/api/realtime/subscriptions`
- `/api/realtime/health`
- `/api/realtime/alerts`

## 9.3 管理 API
新增：
- 啟用/停用訂閱
- 手動刷新 watchlist 訂閱
- worker health status
- alert rule 管理

---

# 10. 開發規格

## 10.1 技術棧
- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis（建議）
- pytest
- ruff
- mypy

## 10.2 工程規則
- V2 不得破壞 V1 schema 相容性
- 即時來源抽象化
- 所有外部即時 provider 封裝於 `services/connectors/`
- realtime worker 必須獨立於 scheduler 與 analysis
- 所有 alert 規則需具測試

## 10.3 開發方式
- VS Code + Codex IDE extension
- Codex CLI 執行 bootstrap、refactor、test-fix
- GitHub 版本控制
- Docker Compose 本地部署
- migration 驅動 schema 演進

---

# 11. 驗收標準

## AC-100
V2 必須保留 V1 全部驗收項目。

## AC-101
系統可成功登入即時資料來源並建立 WebSocket 連線。

## AC-102
系統可成功接收至少一檔台股即時資料並寫入 latest state。

## AC-103
系統可成功維護 watchlist 的即時快取狀態。

## AC-104
系統可成功執行斷線重連與重新訂閱。

## AC-105
系統可成功依規則產生至少一種即時警示事件。

## AC-106
系統可在 Docker Compose 中穩定啟動 realtime service 並通過 healthcheck。

---

# 12. 版本邊界

V2 是在 V1 基礎上增加台股即時行情能力的增強版。  
未來若擴充美股即時、期貨即時或多市場即時資料，應延續 V2 的 realtime worker 與 provider abstraction 設計，不另起新底層架構。