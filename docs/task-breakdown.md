# 任務拆解（task-breakdown）

## Phase 0：專案初始化
- T000 建立 repo 結構
- T001 建立 docs 基礎文件
- T002 建立 .gitignore / .env.example / Makefile
- T003 建立 Docker Compose 最小版本
- T004 建立 auto_commit 腳本

## Phase 1：後端骨架
- T010 建立 FastAPI app skeleton
- T011 建立 settings/config system
- T012 建立 SQLAlchemy base / session / engine
- T013 建立 Alembic 初始化
- T014 建立健康檢查 API
- T015 建立基礎測試框架
- T016 建立 ruff / mypy / pytest 設定

## Phase 2：主資料與 schema
- T020 建立 instruments model
- T021 建立 instrument_tags model
- T022 建立 daily_bars model
- T023 建立 series_points model
- T024 建立 indicator_values model
- T025 建立 ingest_jobs model
- T026 建立 reports_daily model
- T027 建立對應 migrations
- T028 建立 ORM / schema / repository 測試

## Phase 3：V1 ETL - 台股 / 美股 / 指數 / 宏觀
- T030 建立 TWSE connector
- T031 建立 US EOD connector
- T032 建立 index / commodity connector
- T033 建立 macro series connector
- T034 建立 ETL normalization pipeline
- T035 建立 staging-to-core load flow
- T036 建立 ingest job logging
- T037 建立補跑機制
- T038 建立對應 tests

## Phase 4：股票分類與群組
- T040 建立分類資料模型
- T041 建立手動分類 service
- T042 建立自動分類規則引擎
- T043 建立群組查詢 API
- T044 建立群組摘要計算
- T045 建立分類與群組測試

## Phase 5：技術指標
- T050 建立 indicator engine
- T051 實作 MA/EMA/MACD/RSI
- T052 實作 Bollinger/ATR/ADX
- T053 實作 OBV/Stochastic/Ichimoku
- T054 實作其他指標
- T055 建立 indicator batch update flow
- T056 建立 indicator values persistence
- T057 建立技術指標測試

## Phase 6：回測引擎
- T060 建立 strategy model
- T061 建立 strategy DSL schema
- T062 建立 backtest_runs / backtest_trades model
- T063 建立日線回測引擎
- T064 建立交易成本模型
- T065 建立參數搜尋
- T066 建立 walk-forward
- T067 建立回測 API
- T068 建立回測測試

## Phase 7：台灣法人期貨/選擇權分析
- T070 建立 TAIFEX connector
- T071 建立 tw_derivatives_daily model
- T072 建立 tw_derivatives_features model
- T073 建立法人資料 ETL
- T074 建立變化/z-score/偏多偏空分析
- T075 建立對照分析與報表輸出
- T076 建立相關測試

## Phase 8：報表與 API
- T080 建立 daily report generator
- T081 建立 market summary report
- T082 建立 classification summary report
- T083 建立 derivatives summary report
- T084 建立 reports API
- T085 建立報表測試

## Phase 9：Scheduler / Analysis Worker
- T090 建立 scheduler worker skeleton
- T091 建立 analysis worker skeleton
- T092 建立 job dispatch flow
- T093 建立 retry/backoff 機制
- T094 建立 worker health metrics
- T095 建立 worker tests

## Phase 10：V1 驗收與部署
- T100 完成 V1 Docker Compose
- T101 完成 V1 環境設定檔
- T102 完成 V1 e2e flow
- T103 完成 V1 驗收測試
- T104 完成 V1 使用文件

## Phase 11：V2 即時資料基礎
- T110 建立 realtime worker skeleton
- T111 建立即時資料 model
- T112 建立 realtime_latest_state model
- T113 建立 realtime_subscriptions model
- T114 建立 worker_health model
- T115 建立 migrations

## Phase 12：富邦 API 串接
- T120 建立 Fubon connector abstraction
- T121 建立登入與初始化流程
- T122 建立 subscription manager
- T123 建立 tick normalization
- T124 建立 orderbook normalization
- T125 建立 reconnect / retry
- T126 建立 Fubon connector 測試

## Phase 13：即時資料服務
- T130 建立即時快取流程
- T131 建立 tick / snapshot 寫入策略
- T132 建立 realtime API
- T133 建立 watchlist/group realtime query
- T134 建立 lag/health metrics
- T135 建立即時資料測試

## Phase 14：即時警示
- T140 建立 alert rule model
- T141 建立 breakout / volume spike 規則
- T142 建立 cooldown / dedupe 機制
- T143 建立 alert API
- T144 建立即時警示測試

## Phase 15：V2 驗收與部署
- T150 完成 V2 Docker Compose 擴充
- T151 完成 realtime service healthcheck
- T152 完成 reconnect scenario test
- T153 完成 V2 驗收測試
- T154 完成 V2 使用文件

## 執行規則
- 每個 task 完成後必須：
  - 執行測試
  - 執行 lint
  - 執行 type check
  - 建立 commit
- 若 task 過大，應再細拆成子任務