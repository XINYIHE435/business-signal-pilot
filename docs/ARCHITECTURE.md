# SignalPilot Technical Architecture

**Version:** 2.0 (Phase 4 Complete)
**Last Updated:** 2026-07-18
**Status:** Production Ready

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Architecture Layers](#3-architecture-layers)
4. [LangGraph Workflow](#4-langgraph-workflow)
5. [Agent Responsibilities](#5-agent-responsibilities)
6. [ReportRequest Data Model](#6-reportrequest-data-model)

---

## 1. System Overview

SignalPilot is an AI-powered Business Intelligence Agent built on LangGraph.

Instead of writing SQL manually or switching between dashboards and spreadsheets, users interact with the system through natural language. The platform automatically:

- Understands business intent
- Generates SQL
- Executes analytics
- Performs root cause diagnosis
- Produces executive business reports
- Supports Markdown export

The system follows an **Agent-first Architecture**, where business logic is orchestrated by LangGraph rather than hardcoded controllers.
---

## 2. High-Level Architecture


```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Next.js 16 + TypeScript + Tailwind CSS + Recharts      │   │
│  │  - Dashboard (KPI + Trends + Anomalies)                 │   │
│  │  - Chat Interface (Natural Language Query)              │   │
│  │  - Report View (Executive Summary Display)              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI + Pydantic                                      │   │
│  │  - /api/v1/dashboard/* (Dashboard endpoints)            │   │
│  │  - /api/v1/chat/query (Chat endpoint)                   │   │
│  │  - /api/v1/diagnosis/analyze (Diagnosis endpoint)       │   │
│  │  - /api/v1/export/* (Export endpoints)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Orchestration Layer                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LangGraph Workflow Engine                               │   │
│  │  - Intent Classifier Node                                │   │
│  │  - Parameter Validation Node                             │   │
│  │  - SQL Agent Node                                        │   │
│  │  - Diagnosis Agent Node                                  │   │
│  │  - Report Agent Node                                     │   │
│  │  - Synthesizer Node                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         LLM Layer                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Claude Sonnet 4.5 (Anthropic API)                       │   │
│  │  - Intent Classification                                 │   │
│  │  - SQL Generation                                        │   │
│  │  - Root Cause Reasoning                                  │   │
│  │  - Executive Summary Generation                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Tool Layer                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  - SQL Tool                                              │   │
│  │  - Diagnosis Tool                                        │   │
│  │  - Export Tool                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  DuckDB (OLAP Engine)                                    │   │
│  │  - daily_agg table (KPI aggregates)                      │   │
│  │  - category_breakdown table (Category-level data)        │   │
│  │  - traffic_source table (Traffic analysis)               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 Design Principles

1. **Separation of Concerns**: Frontend (UI) / Backend (API) / Agent (Logic) / LLM (Intelligence) / Data (Storage)
2. **Agent-First Architecture**: Business logic orchestrated by LangGraph Agents, not hardcoded controllers
3. **Intent-based Routing**: Dynamic workflow routing based on user intent classification
4. **Tool Calling Pattern**: Agents dynamically select and invoke Tools based on reasoning needs
5. **Unified Response Format**: All agents return consistent response structure for frontend rendering

---

## 3. Architecture Layers

### 3.1 Frontend Layer

**Technology**: Next.js 16 (App Router) + TypeScript + Tailwind CSS

**Key Components**:

| Component | Path | Purpose |
|-----------|------|---------|
| `Dashboard` | `app/page.tsx` | KPI monitoring, trend visualization, anomaly alerts |
| `Chat` | `app/chat/page.tsx` | Natural language query interface |
| `ReportView` | `components/ReportView.tsx` | Executive Summary display (used in Chat & Dashboard) |
| `DiagnosisReport` | `components/DiagnosisReport.tsx` | Root cause analysis display |
| `KPICard` | `components/KPICard.tsx` | Metric card with delta indicator |
| `MultiTrendChart` | `components/MultiTrendChart.tsx` | Multi-metric trend line chart |

**State Management**: React hooks (`useState`, `useSWR` for data fetching)

**API Client**: `lib/api.ts` - Typed API wrappers for all backend endpoints

### 3.2 API Gateway Layer

**Technology**: FastAPI + Pydantic

**Core APIs**:

```
POST /api/v1/chat/query
POST /api/v1/dashboard/report
POST /api/v1/diagnosis/analyze
POST /api/v1/export/report
POST /api/v1/export/query-result
POST /api/v1/export/diagnosis
```

The frontend communicates exclusively through REST APIs.
Business logic resides entirely inside LangGraph.

## 4. LangGraph Workflow

SignalPilot uses a unified workflow for both Dashboard and Chat.

```text
START
    │
    ▼
Intent Classifier
    │
    ▼
Parameter Validation
    │
 ┌──┴─────────────┐
 │ Missing Params?│
 └─────┬──────────┘
 ┌─────┴────────────────────┐
 │                          │
 ▼                          ▼
 No                        Yes
 │                          │
 │                 Clarification Response
 │                          │
 │                         END
 ▼
Generate ReportRequest
       │
       ▼
Workflow Router
       │
 ┌─────┴────────────────────┐
 │                          │
 ▼                          ▼
SQL Agent             Diagnosis Agent
 │                          │
 └──────────────┬───────────┘
                ▼
          Report Agent
                │
                ▼
         Executive Summary
                │
                ▼
          Markdown Export
                │
                ▼
          Synthesizer
                │
               END
```

## 5. Agent Responsibilities

|         Agent        |              Responsibility                    |
|----------------------|------------------------------------------------|
| Intent Classifier    | Understand user intent and extract entities    |
| Parameter Validation | Verify required report parameters              |
| SQL Agent            | Convert natural language into executable SQL   |
| Diagnosis Agent      | Hypothesis-driven root cause analysis          |
| Report Agent         | Generate Executive Summary and business report |
| Synthesizer          | Assemble final response for frontend           |

---

## 6. ReportRequest Data Model

Dashboard and Chat both generate the same ReportRequest object.

```python
ReportRequest

{
    "site": "DE",
    "category": "Fashion",
    "marketplace": "eBay",
    "start_date": "2025-07-01",
    "end_date": "2025-07-31",
    "report_type": "monthly"
}
```

Every downstream Agent consumes this object.
No Agent is allowed to recompute:

- last week
- past month
- today

This guarantees Dashboard and Chat always produce identical reports.

---

