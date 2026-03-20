# 本地化個人股票分析與監控系統需求規格書（V1）
## 版本名稱
V1：盤後日資料版（免費 API / 官方公開資料）

## 文件資訊
- 文件代號：SRS-V1
- 文件版本：1.0
- 文件狀態：正式版
- 適用階段：第一版開發
- 系統定位：本地化、單一使用者、7x24 常駐之個人股票研究工作站

---

# 1. 專案概述

## 1.1 專案目標
建立一套可在本機或家用伺服器上運行的股票分析與監控系統，供單一使用者研究台股、美股、全球主要指數、原物料與總經數據，並整合技術分析、回測、股票分類、台灣法人期貨/選擇權日資料分析與市場日報生成。

## 1.2 V1 範圍
V1 僅處理每日盤後資料，不納入即時行情資料流。

V1 功能重點：
- 台股盤後個股日資料
- 美股盤後個股日資料
- 全球主要指數、原物料、VIX 等日資料
- macromicro.me 類型之總經指標整合
- 股票手動與自動分類
- 技術指標計算
- 回測引擎
- 台灣三大法人期貨/選擇權日資料分析
- 每日摘要與報表
- 個股 / 大盤日線圖表
- 基本畫線工具
- 大盤 + 法人流向圖 foundation
- 7x24 常駐排程與本地部署

## 1.3 非範圍項目
V1 不包含：
- 台股即時行情
- 美股即時行情
- 券商下單
- 多使用者權限系統
- SaaS 雲端帳號服務
- 外部商業資料再散布
- 行動推播系統
- 企業級審批流程

## 1.4 V1 完成定義
V1 視為完成，需同時滿足以下條件：

- 可在本機以 Docker Compose 啟動 `db`、`api`、`scheduler`、`analysis`、`frontend`
- 可完成 migration、seed / universe bootstrap、demo-data、smoke-test、verify-v1
- 可透過總覽、任務中心、候選、報表、回測、衍生性商品頁面完成盤後研究基本流程
- 可透過個股圖表與大盤圖表進行日線複盤、基本畫線與法人流向對照
- 可檢查資料覆蓋、資料新鮮度、近期 ingest jobs、worker heartbeat 與手動任務結果
- 可從本機 API 與前端讀取核心資料，而不依賴即時資料流

V1 已包含：

- 盤後日資料研究流程
- 技術指標、候選、報表、回測、衍生性商品分析
- 日線圖表、畫線與市場／法人流向複盤
- 本機任務中心與系統狀態可視化
- 以示範資料與驗證命令支撐的交付流程

明確延後到 V2：

- realtime market data ingestion
- realtime watchlist / group refresh
- 即時 alerting / push
- broker / trading execution
- 多使用者、權限與雲端化能力

---

# 2. 使用者與使用情境

## 2.1 使用者角色
### Owner
唯一使用者，擁有完整讀寫權限，可設定資料來源、策略、報表與分類規則。

## 2.2 主要使用情境
### UC-01 每日更新資料
系統依排程自動抓取台股、美股、指數、原物料與總經數據之日資料，入庫後更新技術指標與報表。

### UC-02 檢視標的與族群
使用者可檢視個股、ETF、指數與自定義族群，觀察技術面、籌碼面與總經因子，並使用日線 K 線圖與基本畫線輔助盤後複盤。

### UC-03 執行回測
使用者可自由組合條件、指標與分類群組執行回測，檢視績效與風險。

### UC-04 觀察台灣法人衍生品部位
系統每日自動抓取台灣期貨/選擇權三大法人資料，分析外資偏多偏空與異常變化。

### UC-05 產生每日研究報表
系統在每日排程完成後產生市場摘要、分類群組觀察與隔日觀察重點。

---

# 3. 系統總體架構

## 3.1 架構原則
V1 與 V2 共用同一底層架構，V1 僅啟用盤後資料模組。

統一技術原則：
- PostgreSQL 為唯一資料庫
- 採服務模組化與 worker 架構
- 以 Docker Compose 進行本地部署
- 以外部設定檔與環境變數管理個人設定與 secrets
- 以 VS Code + Codex + Codex CLI 開發

## 3.2 邏輯架構
### API Service
提供本地查詢 API、回測 API、報表 API、分類 API。

### Scheduler Worker
依排程觸發 ETL、指標計算、特徵更新、報表生成。

### Analysis Worker
負責技術指標、分類規則、自動標籤、回測與衍生分析。

### Database
使用 PostgreSQL 儲存所有主資料、日線資料、指標、特徵、回測與報表。

### Optional Redis
V1 可不啟用；若後續任務排隊或快取需求增加，可作為快取與 job coordination 使用。

## 3.3 Docker Compose 服務規格
V1 必備服務：
- db
- api
- scheduler
- analysis

可選服務：
- redis

---

# 4. 功能需求

# 4.1 資料來源與主資料管理

## FR-001 資產主檔管理
系統需建立統一資產主檔，涵蓋：
- 台股個股
- 美股個股
- ETF
- 指數
- 原物料序列
- 總經序列

每個資產需至少包含：
- instrument_id
- symbol
- name
- market
- asset_type
- currency
- timezone
- source_route
- is_active

## FR-002 可配置資產清單
系統需支援以設定檔維護要追蹤的市場與資產清單，至少可配置：
- 台股股票列表
- 美股股票列表
- 主要指數列表
- 原物料列表
- 總經序列列表

## FR-003 資料來源路由
每個 instrument 需可配置資料來源，例如：
- twse_openapi
- taifex_open_data
- alpha_vantage
- fred
- manual_csv
- macromicro_adapter

---

# 4.2 日資料抓取與 ETL

## FR-010 台股盤後資料抓取
系統需每日抓取台股盤後個股資料，至少包含：
- trade_date
- symbol
- open
- high
- low
- close
- volume
- turnover_value
- transactions_count
- change
- change_percent

## FR-011 美股盤後資料抓取
系統需每日透過免費 API 抓取美股個股日資料，至少包含：
- trade_date
- symbol
- open
- high
- low
- close
- volume

## FR-012 指數與原物料日資料抓取
系統需支援指數與原物料序列日資料抓取，至少包含：
- trade_date
- instrument_id
- value 或 OHLC
- source

## FR-013 總經數據抓取
系統需支援整合總經與市場情緒序列，例如：
- VIX
- 恐懼貪婪類指標
- 站上 50 日均線比重
- 利率
- 匯率
- 景氣循環指標
- 其他由設定檔指定之宏觀序列

## FR-014 ETL 正規化
所有資料需經以下流程：
- 欄位映射
- 型別轉換
- 去重
- 空值檢查
- 主鍵檢查
- 異常資料標記
- 寫入 staging 後再載入正式表

## FR-015 ETL 失敗補跑
系統需支援：
- job log
- failure reason
- retry
- manual rerun
- 單日期補抓
- 單資料來源補抓

---

# 4.3 股票分類與群組觀察

## FR-020 手動分類
使用者可手動建立分類：
- 產業
- 子產業
- 族群
- 主題
- 自訂標籤
- 觀察清單

## FR-021 自動分類
系統需支援依規則自動分類，例如：
- 市值區間
- 交易市場
- 產業欄位映射
- 關鍵字匹配
- ETF 成分股映射
- 自訂條件規則

## FR-022 多標籤與多群組
同一檔股票可被指派到多個群組與標籤。

## FR-023 群組級觀察
使用者可直接觀察某一族群或群組的：
- 平均漲跌幅
- 成交量變化
- 強弱排序
- 技術指標概況
- 回測績效摘要

---

# 4.4 技術分析模組

## FR-030 技術指標計算
系統需至少提供以下指標：
- SMA
- EMA
- WMA
- MACD
- RSI
- Stochastic
- Bollinger Bands
- ATR
- ADX / DMI
- OBV
- VWAP（若日資料可定義為近似或延後）
- Ichimoku
- Supertrend
- Keltner Channel
- CCI
- ROC
- MFI
- Williams %R
- Donchian Channel
- Parabolic SAR

## FR-031 指標參數化
每個指標需可設定參數，並儲存成模板。

## FR-032 指標快取
指標結果需寫入資料庫，避免重複計算。

## FR-033 群組指標摘要
系統需支援計算群組層級的摘要指標，如：
- 站上月線比率
- RSI > 50 比率
- 創 20 日新高比率
- 成交量擴張比率

---

# 4.5 回測模組

## FR-040 回測引擎
回測引擎需支援日線回測，基於歷史 OHLCV 與指標條件執行。

## FR-041 策略條件
策略需支援：
- 技術指標條件
- 分類/群組條件
- 籌碼條件
- 事件條件
- 資金管理條件
- 風控條件

## FR-042 交易成本模型
需支援：
- 手續費
- 交易稅
- 滑價
- 固定成本
- 百分比成本

## FR-043 參數搜尋
需支援：
- Grid Search
- Random Search
- Walk-forward

## FR-044 回測結果輸出
需輸出：
- CAGR
- Sharpe
- Sortino
- Max Drawdown
- Win Rate
- Profit Factor
- Exposure
- Turnover
- 每筆交易明細
- 成本前後比較

---

# 4.6 台灣法人期貨與選擇權分析

## FR-050 每日法人資料抓取
系統需每日抓取台灣期貨/選擇權三大法人資料，重點關注外資。

## FR-051 資料欄位
至少需支援：
- trade_date
- product_code
- product_name
- investor_type
- long_volume
- short_volume
- net_volume
- long_value
- short_value
- net_value
- oi_long
- oi_short
- oi_net
- source_url
- fetched_at

## FR-052 自動分析
系統需自動產出：
- 1 日、5 日、20 日變化
- z-score
- 多空翻轉
- 異常旗標
- 偏多/偏空結論

## FR-053 與市場對照
系統需可將法人部位與：
- 台股加權指數
- 台指期
- 群組強弱
進行對照分析。

## FR-054 大盤 + 法人流圖基礎
系統需提供可疊合以下資料的盤後圖表基礎：
- 台灣大盤日線 K 線
- 外資期貨日未平倉 / 金額
- 外資選擇權日未平倉 / 金額
- 法人 bias / regime 摘要

V1 可先不含即時更新與現貨買賣超，但需保留後續擴充基礎。

---

# 4.7 報表與儀表板

## FR-060 每日市場報表
每日產出：
- 台股摘要
- 美股摘要
- 指數/原物料摘要
- 總經序列異動摘要
- 法人期貨/選擇權摘要
- 隔日觀察清單

## FR-061 群組觀察報表
依族群或分類輸出：
- 強弱排名
- 技術面概況
- 量價概況
- 關注名單

## FR-062 回測報表
回測完成後可輸出：
- 摘要指標
- 參數
- 圖表資料
- 交易明細

## FR-063 個股日線圖表
系統需提供個股 / ETF 日線圖表頁，至少包含：
- candlestick
- volume pane
- date range control
- 已保存技術指標 overlay

## FR-064 大盤日線圖表
系統需提供大盤 / 指數圖表頁，至少包含：
- candlestick
- volume pane
- date range control
- 與法人流向 foundation 併用之能力

## FR-065 基本畫線工具
系統需至少支援：
- trend line
- horizontal line
- clear / remove action

若實作可行，應支援依標的 / 視圖保存本機畫線注記。

---

# 5. 非功能需求

## NFR-001 本地化
所有核心資料、策略、模型與報表須保存在本地。

## NFR-002 單人使用
系統預設單一使用者，不實作多租戶與多人權限。

## NFR-003 7x24 運行
系統需可持續運行，排程任務在背景執行。

## NFR-004 可恢復性
系統重新啟動後需可恢復：
- 排程
- 資料庫連線
- 任務狀態
- 未完成任務重試

## NFR-005 可維護性
所有 schema 變更需透過 migration 管理。

## NFR-006 可測試性
所有核心模組需可單元測試與整合測試。

## NFR-007 安全性
所有 API key、帳號、憑證與 secrets 均不得硬編碼，必須來自 env 或外部設定。

---

# 6. 統一資料庫設計

## 6.1 核心資料表

### instruments
- instrument_id
- symbol
- name
- asset_type
- market
- currency
- timezone
- source_route
- is_active
- created_at
- updated_at

### instrument_tags
- id
- instrument_id
- tag_type
- tag_value
- source
- created_at

### daily_bars
- id
- instrument_id
- trade_date
- open
- high
- low
- close
- volume
- turnover_value
- transactions_count
- source
- fetched_at

### series_points
- id
- instrument_id
- trade_date
- value
- unit
- source
- fetched_at

### indicator_values
- id
- instrument_id
- trade_date
- indicator_key
- params_json
- value_1
- value_2
- value_3
- created_at

### strategies
- strategy_id
- name
- description
- dsl_json
- version
- created_at

### backtest_runs
- run_id
- strategy_id
- started_at
- finished_at
- status
- params_json
- metrics_json
- dataset_version

### backtest_trades
- id
- run_id
- instrument_id
- trade_ts
- side
- price
- qty
- fee
- tax
- pnl

### tw_derivatives_daily
- id
- trade_date
- product_code
- product_name
- investor_type
- long_volume
- short_volume
- net_volume
- long_value
- short_value
- net_value
- oi_long
- oi_short
- oi_net
- source_url
- fetched_at

### tw_derivatives_features
- id
- trade_date
- product_code
- investor_type
- delta_1d
- delta_5d
- delta_20d
- zscore_20d
- regime_label
- bias_score
- anomaly_flag

### reports_daily
- id
- report_date
- report_type
- title
- content_markdown
- metadata_json
- created_at

### ingest_jobs
- job_id
- job_type
- started_at
- finished_at
- status
- source
- metrics_json
- error_message

---

# 7. 排程需求

## SCH-001 每日盤後更新
每日收盤後依市場時區執行資料抓取。

## SCH-002 每日指標更新
ETL 完成後自動更新技術指標與群組統計。

## SCH-003 每日法人資料更新
固定時段抓取並分析台灣法人衍生品資料。

## SCH-004 每日報表生成
在所有日資料處理完成後自動生成每日報表。

## SCH-005 補跑任務
允許人工觸發指定日期與指定來源補跑。

---

# 8. Docker 與部署規格

## 8.1 部署方式
V1 採 Docker Compose。

## 8.2 服務
- db
- api
- scheduler
- analysis
- optional redis

## 8.3 Volume
- PostgreSQL data volume
- logs volume
- reports volume

## 8.4 設定外部化
所有個人設定與 secrets 不得寫入 image，必須透過：
- `.env`
- bind mount config
- docker secrets（可選）

---

# 9. 開發規格

## 9.1 開發工具
- VS Code
- Codex IDE extension
- Codex CLI
- GitHub
- Docker Desktop
- WSL Ubuntu

## 9.2 Python 技術棧
- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- pytest
- ruff
- mypy

## 9.3 工程要求
- 所有 schema 變更必須有 migration
- 所有 connector 必須集中在 `services/connectors/`
- 所有 worker 必須獨立模組化
- 所有新功能都要附測試

---

# 10. 驗收標準

## AC-001
系統可成功以 Docker Compose 啟動 db / api / scheduler / analysis。

## AC-002
系統可成功抓取並寫入至少一批台股日資料。

## AC-003
系統可成功抓取並寫入至少一批美股日資料。

## AC-004
系統可成功抓取並寫入至少一批指數/原物料/總經序列資料。

## AC-005
系統可成功計算指標並寫入 indicator_values。

## AC-006
系統可成功執行至少一組日線回測。

## AC-007
系統可成功抓取台灣法人期貨/選擇權日資料並輸出分析結果。

## AC-008
系統可成功生成每日報表。

---

# 11. 版本邊界

V1 為盤後資料版，未啟用即時行情模組。  
未來 V2 將在相同底層架構上新增台股即時行情與 WebSocket worker。
