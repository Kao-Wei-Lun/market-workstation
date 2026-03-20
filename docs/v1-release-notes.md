# V1 Release Notes

## 版本定位

本版本為 V1 release-candidate，本質上是一套可在本機或家用伺服器運行的盤後研究工作站。目標不是 production SaaS，而是提供單一使用者可實際操作、可驗證、可 demo 的完整交付物。

## V1 已交付內容

- FastAPI + PostgreSQL + SQLAlchemy + Alembic 後端基礎
- API / scheduler / analysis worker 架構
- config-driven universe bootstrap
- 台股 / 美股 / 指數 / 原物料 / macro 的 V1 universe 配置基礎
- 日線 ETL、指標計算、候選生成、報表生成、台灣法人衍生性商品分析
- 回測、參數搜尋、walk-forward 基礎
- 前端 zh-TW 儀表板與本機任務中心
- smoke-test / verify-v1 / release-check 驗證流程

## V1 建議使用方式

1. 啟動 `db`、`api`、`scheduler`、`analysis`、`frontend`
2. 執行 migration、load-universe、demo-data
3. 用總覽頁確認資料日期與核心摘要
4. 用任務中心頁手動觸發示範資料、ETL、指標、候選、報表
5. 用 Candidates / Reports / Backtests / Derivatives 做盤後研究

## 驗收重點

- API health 與 frontend 可正常啟動
- universe / coverage / system status / tasks API 可檢查資料與任務狀態
- demo data 可讓主要前端頁面看到實際內容
- zh-TW UI 可作為日常本機使用介面

## 已知限制

- 不含 realtime market data
- 不含 alerting / 推播
- 不含多使用者、auth、RBAC
- 不含 production-grade universe auto-sync
- 不含 production deployment hardening

## V2 預計延伸

- realtime worker 與即時資料模型
- 即時 watchlist / group / alerting
- 更完整的 broker / market API connector
- 更細緻的 health / lag / reconnect observability
