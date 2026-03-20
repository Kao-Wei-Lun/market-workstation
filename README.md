# Market Workstation

本專案是 V1 本機日線研究工作站，目標是把收盤後研究流程整合成一套可啟動、可 demo、可檢查的單機系統。現階段重點是：

- 日線 ETL 與資料載入
- 技術指標計算與儲存
- 台灣法人期貨／選擇權日資料分析
- 觀察清單、群組、scanner 與候選清單
- 日線回測、參數搜尋、walk-forward
- 每日報表與 dashboard 聚合 API
- Vue 3 前端儀表板，預設介面語言為繁體中文

V1 不包含即時行情、即時警示、訂單執行或多使用者能力；這些會留給 V2。

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
- 系統狀態
- 觀察清單
- 標籤群組
- 候選清單
- 報表
- 回測
- 衍生性商品

前端特性：

- 預設介面語言為繁體中文
- 以 route query 保留頁面篩選狀態
- 以 dashboard aggregate API 減少前端自行重組資料
- 各頁面統一使用 loading / empty / error state
- 報表與候選頁提供較深的 drill-down
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

### 管理 / 可見性 APIs

```bash
curl "http://localhost:8000/api/system/coverage?preset_name=v1_market_expanded"
curl "http://localhost:8000/api/system/status?job_limit=20&worker_stale_minutes=30"
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

## Release / 驗收

建議閱讀：

- [V1 Release Checklist](docs/v1-release-checklist.md)

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

## 已知限制

V1 目前仍有以下限制：

- 不含 realtime market data
- 不含 alerting / push notification
- 不含 production auth / multi-user
- universe 仍以 config-driven preset 為主，尚未完成 full-market registry auto-sync
- 報表 markdown rendering 為 lightweight parser，不是完整 markdown engine
- 前端目前以本機單人研究使用為前提，未針對大型資料量做完整 pagination / caching

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
