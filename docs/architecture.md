# 系統架構說明（architecture）

## 1. 系統定位
本系統為本地化、單一使用者、7x24 可持續運行之個人股票研究工作站。

版本規劃：
- V1：盤後資料研究系統
- V2：在 V1 基礎上增加台股即時資料

---

## 2. 架構原則
- 單一資料庫：PostgreSQL
- 模組化後端
- worker-based processing
- 本地 Docker Compose 部署
- 設定與 secrets 外部化
- V1 / V2 共享同一底層架構

---

## 3. 邏輯架構圖

```mermaid
flowchart LR
    subgraph Client
        UI[VS Code / Local UI / API Client]
    end

    subgraph App
        API[FastAPI API Service]
        SCH[Scheduler Worker]
        ANA[Analysis Worker]
        RT[Realtime Worker - V2]
    end

    subgraph Data
        DB[(PostgreSQL)]
        REDIS[(Redis - Optional)]
    end

    subgraph External
        TWSE[TWSE / 台股日資料]
        TAIFEX[TAIFEX / 法人期貨選擇權]
        USAPI[US EOD API]
        MACRO[Macro / Commodity / FRED / MM-like Sources]
        FUBON[Fubon API - V2]
    end

    UI --> API
    API --> DB
    API --> REDIS

    SCH --> DB
    SCH --> TWSE
    SCH --> TAIFEX
    SCH --> USAPI
    SCH --> MACRO
    SCH --> ANA

    ANA --> DB
    ANA --> REDIS

    RT --> FUBON
    RT --> DB
    RT --> REDIS
    API --> REDIS