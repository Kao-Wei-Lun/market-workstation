# 開發規則（dev-rules）

## 1. 專案目標
本專案為本地化個人股票分析與監控系統。

版本規劃：
- V1：盤後日資料版
- V2：在 V1 基礎上新增台股即時行情

## 2. 統一技術棧
- Python 3.12
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2.x
- Alembic
- Pydantic
- pytest
- ruff
- mypy
- Docker Compose
- VS Code + Codex IDE extension + Codex CLI

## 3. 架構原則
- V1 與 V2 共用同一套底層架構
- PostgreSQL 是唯一正式資料庫
- 採 worker-based architecture
- 所有外部資料來源必須經 connector 層封裝
- 所有 secrets 必須由環境變數或外部設定檔提供
- 不允許硬編碼帳密、API key、憑證路徑

## 4. 目錄規範
- `apps/api/`：FastAPI app
- `services/connectors/`：外部資料來源接入
- `services/core/`：核心商業邏輯
- `services/db/`：DB session、base、repository
- `services/models/`：ORM models
- `services/schemas/`：Pydantic schemas
- `workers/scheduler/`：排程 worker
- `workers/analysis/`：分析 worker
- `workers/realtime/`：即時行情 worker
- `migrations/`：Alembic migrations
- `tests/`：測試
- `docs/`：規格與開發文檔

## 5. Schema 與 migration 規則
- 所有資料表變更都必須透過 Alembic migration
- 不可直接手改正式資料庫 schema
- migration 名稱需可辨識變更目的
- model 變更後必須同步更新 migration 與測試

## 6. Connector 規則
- 每個資料來源一個獨立 connector module
- connector 必須負責：
  - request / response handling
  - schema normalization
  - retry / timeout
  - rate-limit guard
- connector 不應直接耦合業務邏輯
- connector 必須可被 mock 測試

## 7. Worker 規則
- scheduler worker 只負責觸發任務
- analysis worker 只負責分析、特徵、報表、回測
- realtime worker 只負責即時資料流
- worker 之間不應直接共享隱式狀態
- 任務狀態必須可觀測、可記錄、可重試

## 8. API 規則
- API 使用 REST 風格
- 所有輸入輸出使用 Pydantic schema
- API 層不直接寫商業邏輯
- API 層僅調用 service layer

## 9. 測試規則
每個新功能至少應有：
- 單元測試
- 必要的整合測試

至少涵蓋：
- connector contract tests
- DB model tests
- migration smoke tests
- API route tests
- service logic tests

## 10. 代碼品質規則
- 所有新程式碼需通過：
  - `ruff check .`
  - `mypy .`
  - `pytest`
- 優先使用 typed Python
- 函式應保持小而可測
- 避免巨大單檔與巨大單類別

## 11. Git 規則
- 每完成一個 task 後：
  1. 執行測試
  2. 執行 lint
  3. 更新必要文件
  4. 建立 git commit
- commit message 建議採 conventional commits：
  - `feat: ...`
  - `fix: ...`
  - `refactor: ...`
  - `docs: ...`
  - `test: ...`
  - `chore: ...`

## 12. Docker 規則
- 本地開發以 Docker Compose 為主
- 所有服務應可單獨啟動與健康檢查
- image 不可內含 secrets
- `.env` 僅作本地開發用途，正式敏感值需改外部管理

## 13. V1/V2 邊界規則
### V1
- 不實作即時行情
- 不啟用 realtime worker
- 以日資料 ETL、分析、回測為主

### V2
- 在 V1 基礎上新增 realtime worker
- 接入富邦 API
- 支援台股即時行情與即時警示
- 不破壞 V1 資料結構相容性

## 14. Codex 使用規則
- 開始修改前先閱讀：
  - `docs/srs-v1.md`
  - `docs/srs-v2.md`
  - `docs/dev-rules.md`
  - `docs/task-breakdown.md`
  - `docs/architecture.md`
- 不可跳過 migration
- 不可跳過測試
- 不可自行更換核心技術棧
- 每完成 task 應使用：
  - `bash scripts/auto_commit.sh "<commit message>"`

## 15. 完成定義（Definition of Done）
任一 task 視為完成，需滿足：
- 功能已實作
- 測試通過
- lint 通過
- type check 通過
- 文件已更新
- git commit 已建立