# V1 Release Checklist

本文件用於本機 V1 release-candidate 驗收。目標不是 production deployment，而是確認目前的日線研究工作站已達到可安裝、可啟動、可 demo、可檢查、可操作的交付狀態。

## 1. 環境與依賴

- [ ] 已安裝 Python 3.12
- [ ] 已安裝 PostgreSQL 16，或使用 Docker Compose 提供的 `db`
- [ ] 已安裝 Docker / Docker Compose
- [ ] 已建立 `.env`
- [ ] `.env` 中 host 端命令使用 `POSTGRES_HOST=localhost`
- [ ] `make setup` 可成功完成

## 2. 基本啟動流程

- [ ] `make dev-up` 可成功啟動 `db`、`api`、`scheduler`、`analysis`、`frontend`
- [ ] `make migrate` 成功
- [ ] `make seed` 成功
- [ ] `make load-universe` 成功
- [ ] `make demo-data` 成功
- [ ] `make smoke-test` 成功

## 3. 後端健康與可見性

- [ ] `curl http://localhost:8000/health` 回傳 200
- [ ] `curl http://localhost:8000/healthz` 回傳 200
- [ ] `curl http://localhost:8000/api/system/coverage` 可看到 preset / scope / counts
- [ ] `curl http://localhost:8000/api/system/status` 可看到 datasets / recent_jobs / workers
- [ ] `python -m workers.scheduler.main --list-jobs` 可列出工作
- [ ] `python -m workers.analysis.main --list-jobs` 可列出工作

## 4. Demo / 資料可見性

- [ ] `curl http://localhost:8000/candidates/runs` 非空
- [ ] `curl http://localhost:8000/backtests/runs` 非空
- [ ] `curl http://localhost:8000/reports/latest` 非空
- [ ] `curl http://localhost:8000/derivatives/summary/latest` 非空
- [ ] `curl http://localhost:8000/api/dashboard/overview` 回傳非空 `summary_cards`
- [ ] `curl http://localhost:8000/api/dashboard/reports/latest` 回傳最近報表摘要

## 5. 前端頁面驗收

- [ ] `http://localhost:5173` 可開啟
- [ ] 總覽頁可作為每日入口，能看到資料日期、生成時間、候選摘要、報表摘要、觀察清單摘要、族群摘要、法人摘要、回測摘要
- [ ] 導覽列可看到：
  - [ ] 總覽
  - [ ] 資料覆蓋
  - [ ] 系統狀態
  - [ ] 觀察清單
  - [ ] 標籤群組
  - [ ] 候選清單
  - [ ] 報表
  - [ ] 回測
  - [ ] 衍生性商品
- [ ] 各頁面載入時顯示一致的載入中狀態
- [ ] 無資料時顯示一致的空狀態文案
- [ ] API 失敗時顯示一致的錯誤狀態文案

## 6. 報表 / 候選 / 回測 / 衍生性商品

- [ ] Reports 頁可依日期與類型切換
- [ ] Reports 頁可切換報表區塊並閱讀 markdown / structured payload
- [ ] Candidates 頁可依日期、代號、分數、名次篩選
- [ ] Candidates 頁可打開候選明細
- [ ] Backtests 頁可切換 run 並查看 trades
- [ ] Derivatives 頁可看到偏向摘要與重點

## 7. 匯出能力

- [ ] 報表 bundle 匯出可用
- [ ] 候選清單匯出可用
- [ ] 回測結果或交易匯出可用
- [ ] scanner summary 匯出可用

## 8. zh-TW UI 完整性

- [ ] 導覽列文案為繁體中文
- [ ] 頁面標題與描述為繁體中文
- [ ] 篩選欄位標籤為繁體中文
- [ ] 空狀態 / 錯誤 / 載入文案為繁體中文
- [ ] 無明顯殘留的英文操作文案（專有名詞如 API、ETL、SMA、MACD 可保留）

## 9. 驗證命令

建議最小驗證流程：

```bash
make migrate
make seed
make load-universe
make demo-data
make smoke-test
make release-check
```

若 `release-check` 失敗，優先檢查：

- API 是否已啟動於 `http://localhost:8000`
- `.env` 是否存在且 DB 連線資訊正確
- `make demo-data` 是否已成功產生可見資料
- scheduler / analysis 是否有正常心跳

## 10. 已知非目標

- 不含即時行情 / 訂閱 / alerting
- 不含 production auth / multi-user / RBAC
- 不含 production-grade market universe sync automation
- 不含 production deployment hardening
