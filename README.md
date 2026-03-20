# Market Workstation

本專案是 V1 本機日線研究工作站，目標是把收盤後研究流程整合成一套可啟動、可 demo、可檢查的單機系統。現階段重點是：

- 日線 ETL 與資料載入
- 技術指標計算與儲存
- 台灣法人期貨／選擇權日資料分析
- 觀察清單、群組、scanner 與候選清單
- 日線回測、參數搜尋、walk-forward
- 每日報表與 dashboard 聚合 API
- 個股 / 大盤日線圖表、持久化畫線與市場結構圖
- Vue 3 前端儀表板，預設介面語言為繁體中文

V1 不包含即時行情、即時警示、訂單執行或多使用者能力；這些會留給 V2。

本 README 同時作為目前 V1 交付文件，對應的 release 驗收補充文件請見：

- [V1 Release Checklist](docs/v1-release-checklist.md)
- [V1 Release Notes](docs/v1-release-notes.md)

## V1 範圍

V1 目前提供：

- FastAPI API 服務
- PostgreSQL + SQLAlchemy + Alembic
- scheduler / analysis worker 基礎
- provider-isolated connectors
- config-driven universe bootstrap
- demo data 產生流程
- 前端研究儀表板與管理頁面

V1 建議用途：

- 本機收盤後資料檢查
- 候選標的盤後複核
- 報表閱讀與隔日規劃
- 基礎日線策略研究與回測
- universe / ETL / worker 狀態檢查
- 日線 K 線圖與盤後複盤

## 系統需求

- Python 3.12
- PostgreSQL 16
- Docker / Docker Compose
- Node.js 18+（前端開發建議）

## 環境設定

1. 建立環境檔：

```bash
cp .env.example .env
```

2. 若在 host 端直接執行 `make migrate`、`make seed`、`make demo-data`，請保持：

```bash
POSTGRES_HOST=localhost
```

3. Docker Compose 內會覆寫 DB host 為 `db`，因此同一份 `.env` 可以同時支援 host 與 container。

4. 本機 demo flow 不需要填寫外部 provider key。

## 安裝

```bash
python3 -m venv .venv
make setup
make frontend-install
```

## 快速啟動

最短可見成果流程：

```bash
make dev-up
make migrate
make seed
make demo-data
make smoke-test
make run-frontend
```

啟動後可檢查：

- API: `http://localhost:8000/health`
- API: `http://localhost:8000/healthz`
- Frontend: `http://localhost:5173`

## Bootstrap / Seed / Demo / Smoke Flow

建議把初始化流程理解成五個層次：

1. `make load-universe`
用途：載入較完整的 V1 研究 universe、watchlists 與 tag 基礎。
2. `make seed`
用途：只建立最小參考資料，適合最小初始化與 smoke test。
3. `make demo-data`
用途：建立前端可見的示範日線、指標、候選、報表、衍生性商品與回測資料。
4. `make smoke-test`
用途：檢查 DB、API health、schema 與 sample instruments 是否可用。
5. `make verify-v1`
用途：跑 demo data、smoke 與核心資料可見性驗證，確認 V1 已達本機交付狀態。

`make release-check` 則是更完整的 RC 驗證，會串起後端/前端測試、lint、typecheck 與 `verify-v1`。

## Seed / Universe / Demo Data 的差異

### `make seed`

只建立最小參考資料：

- sample instruments
- sample watchlists
- sample tags

用途：

- smoke test
- 最小初始化
- 後續 demo-data 的基底

### `make list-universes`

列出可用 universe preset 與 scope。

### `make load-universe`

載入較完整的 V1 研究 universe。預設 preset 為 `v1_market_expanded`，目前涵蓋：

- 台灣股票 / ETF / 主要指數
- 精選美股 / ETF / 主要指數
- 全球主要指數
- 原物料
- macro series

也可只載入特定 scope，例如：

```bash
python scripts/manage.py load-universe --preset v1_market_expanded --scope macro_series_core
```

### `make demo-data`

建立前端可見的本機示範資料，內容包含：

- daily bars
- indicator values
- Taiwan derivatives demo rows / features
- candidate run / candidate items
- backtest run / trades
- daily reports / daily report bundle

`make demo-data` 針對同一 `TRADE_DATE` 設計為可重跑，不應不斷膨脹重複的 demo run。

注意：`demo-data` 的目的是前端展示與本機驗證，不是還原真實市場資料。若你要讓圖表與實際市場對齊，應改用真實資料 backfill 指令。

### 載入真實資料

目前 V1 已有可直接使用的真實資料路徑：

- `make real-twse-backfill START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD SYMBOL=2330`
- `make real-tw-index-backfill START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD SYMBOL=^TWII`
- `make real-taifex-backfill START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD`
- `make clear-demo-data`
- `make real-workspace TRADE_DATE=YYYY-MM-DD START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD`

用途：

- 將 TWSE 支援標的的真實日線載入 `daily_bars`
- 將台灣加權指數等已支援的大盤指數日線載入 `daily_bars`
- 將 TAIFEX 真實法人日資料載入 `tw_derivatives_daily`
- 重新計算對應法人特徵，供市場結構圖與衍生性商品頁使用
- 清除 sample/demo 來源與由其衍生出的候選、報表、示範回測
- 以真實資料重建指標、候選與報表輸出

補充：

- `demo-data` 現在會避開已存在的真實日線區間，不再直接覆蓋那些標的的既有資料
- `real-workspace` 會自動跳過未設定真實 provider 的 `us_eod_provider` 與 `macro_series_provider`
- 目前真實日資料 connector 已涵蓋 TWSE 個股 / ETF、`^TWII` 與 TAIFEX 法人資料；其餘台灣 / 全球指數仍需後續補更完整 connector

建議切換到真實資料模式時使用：

```bash
make clear-demo-data
make real-workspace TRADE_DATE=2026-03-20 START_DATE=2026-03-01 END_DATE=2026-03-20
```

這條流程的原則是：

- 先移除 sample/demo 基底與其衍生輸出
- 再回填目前已支援的真實資料來源
- 最後重新產生指標、候選與報表

若某些頁面在切換後變成空白，通常表示該資料 scope 目前尚未配置真實 provider，或該類型仍缺少正式 connector，而不是系統自動回退成 demo。

## V1.1 資料完整度策略

V1.1 的重點不是改架構，而是讓本機使用者更容易看出「哪些 universe 已準備好、哪些還缺資料、哪些資料過期需要補跑」。

目前策略：

- universe 仍以 `config/universes/` 下的 preset 與 scope 定義為準
- 每個 scope 會宣告 market、asset_type、source_route、coverage 類型與 `stale_after_days`
- coverage API 會比對：
  - 預設宣告標的數
  - 已 bootstrap 標的數
  - 已有資料標的數
  - 缺資料標的數
  - 過期標的數
  - scope / category 最新資料日期
- 前端的「資料覆蓋」與「任務中心」會直接顯示缺資料 / 過期 scope，作為補跑依據

換句話說，V1.1 的日常流程是：

1. `make load-universe`
2. 開前端看「資料覆蓋」
3. 找出缺資料或過期 scope
4. 到「任務中心」執行示範資料、ETL、指標、報表任務
5. 回到總覽、候選、報表確認結果

## 日常 demo flow

若要讓前端幾乎每一頁都有可看資料，建議流程：

```bash
make migrate
make seed
make load-universe
make demo-data
make smoke-test
make run-frontend
```

執行後，以下端點應有可見內容：

```bash
curl http://localhost:8000/candidates/runs
curl http://localhost:8000/backtests/runs
curl http://localhost:8000/reports/latest
curl http://localhost:8000/derivatives/summary/latest
curl "http://localhost:8000/api/system/coverage?preset_name=v1_market_expanded"
curl "http://localhost:8000/api/system/status?job_limit=20&worker_stale_minutes=30"
```

若要檢查缺資料或過期狀態，優先看：

```bash
curl "http://localhost:8000/api/system/coverage?preset_name=v1_market_expanded"
```

該 payload 會包含 scope 級與 category 級的：

- `latest_data_date`
- `missing_data_count`
- `stale_data_count`
- `status`

## 常用命令

### 啟動與管理

```bash
make dev-up
make dev-down
make run-api
make run-scheduler
make run-analysis
make run-frontend
```

### 初始化與資料

```bash
make migrate
make seed
make list-universes
make load-universe
make demo-data
make sample-etl
make indicator-update
make generate-reports
make smoke-test
make verify-v1
```

### 驗證與品質

```bash
make test
make lint
make typecheck
make verify-v1
make frontend-test
make frontend-build
make release-check
```

## `scripts/manage.py`

管理 CLI 提供：

```bash
python scripts/manage.py migrate
python scripts/manage.py seed
python scripts/manage.py list-universes
python scripts/manage.py load-universe --preset v1_market_expanded
python scripts/manage.py demo-data --trade-date 2026-03-20
python scripts/manage.py sample-etl --trade-date 2026-03-20
python scripts/manage.py indicator-update --trade-date 2026-03-20
python scripts/manage.py generate-reports --trade-date 2026-03-20
python scripts/manage.py smoke-test --api-base-url http://localhost:8000
python scripts/manage.py verify-v1 --api-base-url http://localhost:8000 --trade-date 2026-03-20
```

## Frontend 使用流程

前端目前主要頁面：

- 總覽
- 資料覆蓋
- 任務中心
- 觀察清單
- 標籤群組
- 候選清單
- 報表
- 回測
- 衍生性商品
- 個股圖表
- 市場結構圖

前端特性：

- 預設介面語言為繁體中文
- 總覽頁作為每日工作入口，整合資料新鮮度、候選、報表、觀察清單、群組、衍生性商品與回測摘要
- 任務中心頁可手動觸發示範資料、日線 ETL、技術指標、候選與報表任務，並查看最近執行結果
- 以 route query 保留頁面篩選狀態
- 以 dashboard aggregate API 減少前端自行重組資料
- 各頁面統一使用 loading / empty / error state
- 報表與候選頁提供較深的 drill-down
- 個股圖表頁提供日線 K 線、成交量、indicator overlay 與持久化畫線
- 市場結構圖頁提供台灣大盤日線、外資現貨／期貨／選擇權方向、bias interpretation 與持久化畫線
- 管理頁提供 universe coverage、資料新鮮度、ingest jobs、worker heartbeat 可視性

`VITE_API_BASE_URL` 可在 `.env` 或 `frontend/.env.example` 中設定，典型本機值為：

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## API 與可視化重點

### Dashboard APIs

```bash
curl "http://localhost:8000/api/dashboard/overview?trade_date=2026-03-20&watchlist_id=1&tag=semiconductor"
curl "http://localhost:8000/api/dashboard/candidates/latest?candidate_date=2026-03-20&limit=10"
curl "http://localhost:8000/api/dashboard/reports/latest?report_date=2026-03-20&limit=10"
curl "http://localhost:8000/api/dashboard/backtests/latest?limit=5"
curl "http://localhost:8000/api/dashboard/derivatives/latest?trade_date=2026-03-20"
```

建議的每日使用順序：

1. 先開「總覽」確認資料日期、最近成功匯入、最近報表生成與今日重點。
2. 若資料不完整，轉到「任務中心」與「資料覆蓋」檢查 worker、jobs、universe/bootstrap。
3. 在「任務中心」直接手動觸發示範資料、日線 ETL、技術指標、候選或報表任務。
4. 再從總覽或任務中心直接跳往「報表」、「候選清單」、「觀察清單」或「標籤群組」深入閱讀。
5. 若要做價位複盤或市場結構對照，前往「個股圖表」或「市場結構圖」查看 K 線、成交量、overlay、外資流向與畫線。

### 如何檢查缺資料 / 過期資料

1. 打開「資料覆蓋」頁
2. 先看「需補資料 / 補跑的區段」表格
3. 再看「市場統計」與「資料來源統計」中的最新日期、缺資料、過期數
4. 若需要補跑，前往「任務中心」執行對應任務
5. 補跑完成後回到「資料覆蓋」與「總覽」確認狀態是否改善

### 任務中心 / 系統狀態使用方式

「任務中心」頁是 V1 的本機操作頁，建議用法：

1. 先看摘要卡與 highlights，確認最近手動任務、失敗數與資料集狀態。
2. 若資料尚未準備好，手動執行：
   - `產生示範資料`
   - `載入示範日線`
   - `更新技術指標`
   - `產生候選清單`
   - `產生每日報表`
3. 檢查同頁的最近任務結果、最近資料更新、ETL / ingest jobs、worker 心跳。
4. 成功後直接跳去 Candidates、Reports 或 Overview 確認結果。

### 管理 / 可見性 APIs

```bash
curl "http://localhost:8000/api/system/coverage?preset_name=v1_market_expanded"
curl "http://localhost:8000/api/system/status?job_limit=20&worker_stale_minutes=30"
curl "http://localhost:8000/api/system/tasks?limit=20"
curl -X POST "http://localhost:8000/api/system/tasks/demo_data" \
  -H "Content-Type: application/json" \
  -d '{"trade_date":"2026-03-20"}'
curl -X POST "http://localhost:8000/api/system/tasks/candidate_generation" \
  -H "Content-Type: application/json" \
  -d '{"trade_date":"2026-03-20"}'
curl -X POST "http://localhost:8000/api/system/tasks/report_generation" \
  -H "Content-Type: application/json" \
  -d '{"trade_date":"2026-03-20"}'
```

### 報表 / 候選 / 匯出

```bash
curl http://localhost:8000/reports/latest
curl http://localhost:8000/reports/2026-03-20/bundle
curl "http://localhost:8000/reports/2026-03-20/bundle/export?export_format=csv"
curl "http://localhost:8000/candidates/runs?candidate_date=2026-03-20"
curl "http://localhost:8000/candidates/runs/<run_id>/export?export_format=csv"
curl http://localhost:8000/backtests/runs
curl "http://localhost:8000/backtests/runs/<run_id>/export?export_format=csv"
curl "http://localhost:8000/scanner/export?trade_date=2026-03-20&watchlist_id=1&export_format=csv"
```

### 圖表 APIs

```bash
curl "http://localhost:8000/api/charts/instruments?market=TW&limit=20"
curl "http://localhost:8000/api/charts/ohlcv/2330?indicator_name=sma&indicator_name=ema"
curl "http://localhost:8000/api/charts/institutional-flow/%5ETWII"
curl "http://localhost:8000/api/charts/market-structure/%5ETWII"
curl "http://localhost:8000/api/charts/annotations/2330?view_kind=instrument"
curl -X POST "http://localhost:8000/api/charts/annotations" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"2330","view_kind":"instrument","annotation_type":"horizontal_line","label":"壓力位","payload_json":{"price":950}}'
```

圖表頁目前支援：

- 個股 / ETF 日線 K 線圖
- 市場結構圖：大盤 / 指數日線 K 線 + 外資現貨／期貨／選擇權方向
- 成交量 pane
- 已保存 indicator_values overlay
- 趨勢線、水平線、垂直線、區間框、重點標記
- 本機持久化畫線注記，可依標的 / 視圖重新載入
- 市場結構 interpretation 與跨頁導覽

## Release / 驗收

建議閱讀：

- [V1 Release Checklist](docs/v1-release-checklist.md)
- [V1 Release Notes](docs/v1-release-notes.md)

最小 release-candidate 驗證流程：

```bash
make migrate
make seed
make load-universe
make demo-data
make smoke-test
make release-check
```

`make release-check` 會串起：

- `make demo-data`
- `make smoke-test`
- `make test`
- `make lint`
- `make typecheck`
- `make frontend-test`
- `make frontend-build`
- `make verify-v1`

其中 `make verify-v1` 會再確認：

- smoke test 成功
- candidate runs 可見
- backtest runs 可見
- reports 可見
- Taiwan derivatives 資料可見
- V1 demo flow 的核心資料已足夠支撐前端頁面閱讀

## 已知限制

V1 目前仍有以下限制：

- 不含 realtime market data
- 不含 alerting / push notification
- 不含 production auth / multi-user
- universe 仍以 config-driven preset 為主，尚未完成 full-market registry auto-sync
- 報表 markdown rendering 為 lightweight parser，不是完整 markdown engine
- 圖表目前僅支援日線 / 盤後資料，不含即時更新、縮放拖拉與進階繪圖工具
- 市場結構圖目前以 market-level 外資現貨 summary 與衍生性商品方向資料為主，不含更細的現貨分點或多法人拆解
- 前端目前以本機單人研究使用為前提，未針對大型資料量做完整 pagination / caching
- 任務中心目前以安全手動觸發為主，不含正式分散式 queue / RBAC / 審批流

## V2 方向

V2 預計延伸：

- realtime worker
- realtime data model / subscriptions
- 富邦等券商 / 行情 API connector
- 即時群組與 watchlist 查詢
- 即時警示
- 更完整的 health / lag / reconnect metrics

V1 與 V2 會維持同一套基礎架構：API + workers + PostgreSQL + connector isolation。

## 驗證

目前建議的完整檢查：

```bash
pytest -q
ruff check .
mypy .
npm --prefix frontend run test
npm --prefix frontend run build
```
