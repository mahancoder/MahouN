# گزارش بررسی وایرینگ پروژه HAJIX

**تاریخ**: 2025-01-XX  
**وضعیت**: ⚠️ مشکلات شناسایی شده - نیاز به رفع

---

## خلاصه اجرایی

پروژه HAJIX از پروژه اصلی X refactor شده است. بررسی وایرینگ نشان می‌دهد که چندین مشکل مهم در اتصالات و imports وجود دارد که باید رفع شوند.

### مشکلات کلیدی

1. ❌ **Router ها موجود نیستند** - `api/routers/` در HAJIX خالی است (6 router ضروری)
2. ❌ **دو لایه MCP گم شده‌اند** - `mahoun/api_router.py` و `mahoun/dashboard/router.py` برای اتصال MCP به API ضروری هستند
3. ❌ **logging_utils گم شده** - ماژول در HAJIX وجود ندارد
4. ⚠️ **Lifecycle hooks موجود نیست** - startup/shutdown برای database
5. ✅ **Core connections سالم** - Agent system و RAG services درست هستند

---

## 1. مشکلات Import و Router

### 1.1 مشکل Router ها

**مکان**: `api/main.py`

**مشکل**: 
- کد سعی می‌کند از `api.routers` import کند
- دایرکتوری `api/routes/` (singular) در HAJIX وجود دارد اما خالی است
- دایرکتوری `api/routers/` (plural) در HAJIX وجود ندارد
- در پروژه اصلی X، `api/routers/` با 29 فایل وجود دارد

**Router های مورد نیاز**:
```python
from api.routers import system as system_router      # ✅ موجود در X
from api.routers import search as search_router      # ✅ موجود در X
from api.routers import ingest as ingest_router      # ✅ موجود در X
from api.routers import mahoun as mahoun_router      # ✅ موجود در X
from api.routers import health_v2                    # ✅ موجود در X
from api.routers import metrics as metrics_router    # ✅ موجود در X
```

**راه حل**:
1. کپی کردن دایرکتوری `api/routers/` از پروژه X به HAJIX
2. یا تغییر imports از `api.routers` به `api.routes` و ایجاد router ها

**فایل‌های موجود در X/api/routers/**:
- `__init__.py`
- `system.py` ✅
- `search.py` ✅
- `ingest.py` ✅
- `mahoun.py` ✅
- `health_v2.py` ✅
- `metrics.py` ✅
- `admin.py`
- `analyze.py`
- `audit.py`
- `auth.py`
- `chunking.py`
- `data_management.py`
- `embedding.py`
- `explainability.py`
- `generate.py`
- `graph_health.py`
- `health.py`
- `legal_rag.py`
- `monitoring.py`
- `retrieval.py`
- `legal_rag/` (subdirectory)

### 1.2 مشکل logging_utils

**مکان**: `api/main.py:16`

**مشکل**:
```python
from logging_utils import get_logger  # ❌ ماژول وجود ندارد
```

**راه حل‌های موجود**:

**گزینه 1**: استفاده از `pipelines._logging`
```python
from pipelines._logging import get_logger  # ✅ موجود است
```

**گزینه 2**: کپی کردن `logging_utils.py` از X
- فایل در `/home/haji/Videos/X/logging_utils.py` موجود است
- ساده و مستقل است

**گزینه 3**: استفاده از logging استاندارد
```python
import logging
logger = logging.getLogger(__name__)
```

**توصیه**: گزینه 1 (استفاده از `pipelines._logging`) چون قبلاً در پروژه استفاده شده.

---

## 2. بررسی اتصالات Core

### 2.1 Database Connections ✅

**وضعیت**: سالم

**فایل**: `api/database.py`

**بررسی شده**:
- ✅ PostgreSQL connection pool (`init_postgres`, `get_postgres`)
- ✅ Neo4j driver (`init_neo4j`, `get_neo4j`)
- ✅ Redis client (`init_redis`, `get_redis`)
- ✅ Functions برای initialize و close همه databases

**مشکل**: 
- ⚠️ Lifecycle hooks در `api/main.py` موجود نیست
- باید `@app.on_event("startup")` و `@app.on_event("shutdown")` اضافه شود

**راه حل**:
```python
@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
```

### 2.2 RAG Services ✅

**وضعیت**: سالم

**بررسی شده**:
- ✅ `rag/hybrid_rag_service.py` - HybridRAGService موجود است
- ✅ `rag/citation_engine.py` - CitationEngine موجود است
- ✅ `create_hybrid_rag_service()` function موجود است
- ✅ Agents از RAG services استفاده می‌کنند

**اتصالات**:
- `agents/narrative_agent.py` → `rag.hybrid_rag_service` ✅
- `agents/contract_agent.py` → `rag.hybrid_rag_service` ✅
- `agents/legal_precedent_agent.py` → `rag.hybrid_rag_service` ✅
- `agents/risk_assessment_agent.py` → `rag.hybrid_rag_service` ✅

### 2.3 Agent System ✅

**وضعیت**: سالم

**بررسی شده**:
- ✅ `agents/base_agent.py` - BaseAgent class موجود است
- ✅ `agents/factory.py` - AgentFactory موجود است
- ✅ `agents/orchestrator.py` - AgentOrchestrator موجود است
- ✅ تمام agent classes موجود هستند:
  - `DocParserAgent` ✅
  - `DisputeAgent` ✅
  - `ClaimAgent` ✅
  - `TimelineAgent` ✅
  - `DelayAgent` ✅
  - `NarrativeAgent` ✅
  - `ContractAgent` ✅
  - `RiskAssessmentAgent` ✅
  - `LegalPrecedentAgent` ✅

**اتصالات**:
- Agents از `core.metrics` استفاده می‌کنند ✅
- Agents از `rag.hybrid_rag_service` استفاده می‌کنند ✅
- Factory pattern به درستی پیاده شده ✅

---

## 3. بررسی Dependencies

### 3.1 Circular Dependencies ⚠️

**بررسی شده**: هیچ circular dependency خطرناکی یافت نشد.

**Imports بررسی شده**:
- `api` → `agents`: ❌ (مستقیم import نمی‌کند)
- `api` → `rag`: ❌ (مستقیم import نمی‌کند)
- `agents` → `rag`: ✅ (یک طرفه)
- `agents` → `core`: ✅ (یک طرفه)
- `rag` → `core`: ✅ (یک طرفه)

### 3.2 Missing Modules

**ماژول‌های گم شده**:

1. ❌ `api.routers.*` - تمام router ها
2. ❌ `logging_utils` - در root level

**ماژول‌های موجود**:
- ✅ `api.config` - Settings موجود است
- ✅ `api.database` - Database connections موجود است
- ✅ `api.models` - Pydantic models موجود است
- ✅ `api.dependencies` - FastAPI dependencies موجود است
- ✅ `core.*` - تمام core modules موجود هستند
- ✅ `rag.*` - تمام RAG modules موجود هستند
- ✅ `agents.*` - تمام agent modules موجود هستند

---

## 4. پیشنهادات رفع مشکلات

### اولویت 1: رفع Router ها

**گام 1**: کپی کردن router ها از X
```bash
cp -r /home/haji/Videos/X/api/routers /home/haji/Desktop/Z/HAJIX/api/
```

**گام 2**: کپی کردن لایه‌های ضروری MCP از X
```bash
# کپی api_router و dashboard router
cp /home/haji/Videos/X/mahoun/api_router.py /home/haji/Desktop/Z/HAJIX/mahoun/
cp -r /home/haji/Videos/X/mahoun/dashboard /home/haji/Desktop/Z/HAJIX/mahoun/
```

**گام 3**: اضافه کردن MCP routers به `api/main.py`
```python
# بعد از import سایر router ها
try:
    from mahoun.api_router import router as mahoun_api_router
    app.include_router(mahoun_api_router)
    logger.info("✓ MAHOUN observability router registered at /internal")
except ImportError as e:
    logger.warning(f"MAHOUN observability router not available: {e}")

try:
    from mahoun.dashboard.router import router as mahoun_dashboard_router
    app.include_router(mahoun_dashboard_router)
    logger.info("✓ MAHOUN dashboard router registered at /internal/dashboard")
except ImportError as e:
    logger.warning(f"MAHOUN dashboard router not available: {e}")
```

**گام 4**: بررسی و تطبیق imports در router ها
- ممکن است برخی imports نیاز به تغییر داشته باشند
- بررسی paths و module names

**گام 5**: تست import ها
```python
from api.routers import system, search, ingest, mahoun, health_v2, metrics
from mahoun.api_router import router as mahoun_api_router
from mahoun.dashboard.router import router as mahoun_dashboard_router
```

### اولویت 2: رفع logging_utils

**گزینه پیشنهادی**: استفاده از `pipelines._logging`

**تغییر در `api/main.py`**:
```python
# قبل:
from logging_utils import get_logger

# بعد:
from pipelines._logging import get_logger
```

**یا** کپی کردن `logging_utils.py`:
```bash
cp /home/haji/Videos/X/logging_utils.py /home/haji/Desktop/Z/HAJIX/
```

### اولویت 3: اضافه کردن Lifecycle Hooks

**اضافه کردن به `api/main.py`**:
```python
from api.database import init_db, close_db

@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup"""
    try:
        await init_db()
        logger.info("✅ Database connections initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize databases: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing databases: {e}")
```

---

## 5. تست‌های وایرینگ پیشنهادی

### تست 1: Import Test
```python
def test_imports():
    """Test all critical imports"""
    from api.routers import system, search
    from api.database import init_db
    from agents.factory import AgentFactory
    from rag.hybrid_rag_service import HybridRAGService
    assert True
```

### تست 2: Router Registration Test
```python
def test_router_registration():
    """Test that all routers are registered"""
    from api.main import app
    routes = [r.path for r in app.routes]
    assert "/system/mode" in routes
    assert "/v1/search/verdicts" in routes
```

### تست 3: Database Connection Test
```python
async def test_database_connections():
    """Test database initialization"""
    from api.database import init_db, close_db
    await init_db()
    # Test connections
    await close_db()
```

### تست 4: Agent Factory Test
```python
async def test_agent_factory():
    """Test agent creation"""
    from agents.factory import AgentFactory
    agent = await AgentFactory.create_agent("doc_parser")
    assert agent is not None
```

---

## 6. چک‌لیست رفع مشکلات

- [ ] کپی کردن `api/routers/` از X به HAJIX (6 router ضروری)
- [ ] کپی کردن `mahoun/api_router.py` از X به HAJIX (**لایه MCP 1**)
- [ ] کپی کردن `mahoun/dashboard/` از X به HAJIX (**لایه MCP 2**)
- [ ] اضافه کردن MCP routers به `api/main.py`
- [ ] بررسی و تطبیق imports در router ها
- [ ] رفع `logging_utils` import (استفاده از `pipelines._logging`)
- [ ] اضافه کردن lifecycle hooks برای database
- [ ] تست import های router ها
- [ ] تست import های MCP routers
- [ ] تست اتصالات database
- [ ] تست agent factory
- [ ] تست RAG services
- [ ] تست MCP endpoints (`/internal/*`, `/internal/dashboard/*`)
- [ ] اجرای تست‌های وایرینگ

---

## 7. خلاصه مشکلات

| مشکل | اولویت | وضعیت | راه حل |
|------|--------|-------|--------|
| Router ها موجود نیستند | 🔴 بالا | ❌ | کپی از X (6 router) |
| **MCP api_router گم شده** | 🔴 **بالا** | ❌ | **کپی از X** |
| **MCP dashboard router گم شده** | 🔴 **بالا** | ❌ | **کپی از X** |
| logging_utils گم شده | 🔴 بالا | ❌ | استفاده از pipelines._logging |
| Lifecycle hooks موجود نیست | 🟡 متوسط | ⚠️ | اضافه کردن startup/shutdown |
| Database connections | 🟢 پایین | ✅ | فقط lifecycle hooks نیاز است |
| Agent system | 🟢 پایین | ✅ | سالم |
| RAG services | 🟢 پایین | ✅ | سالم |

---

## 8. تحلیل انتخاب‌ها و بهینه‌سازی

### 8.1 مقایسه logging_utils

**گزینه 1: استفاده از `logging_utils` (پروژه X)**
- ✅ ساده و مستقیم
- ✅ در root level - دسترسی آسان
- ❌ نیاز به کپی فایل
- ❌ وابستگی اضافی

**گزینه 2: استفاده از `pipelines._logging` (HAJIX)**
- ✅ قبلاً در پروژه استفاده شده
- ✅ در ماژول pipelines - منطقی‌تر
- ✅ Backward compatibility با `logging_utils`
- ⚠️ Path طولانی‌تر (`pipelines._logging` vs `logging_utils`)

**توصیه**: ✅ **گزینه 2 بهتر است** چون:
- قبلاً در پروژه استفاده شده
- ساختار بهتری دارد (در ماژول pipelines)
- Backward compatibility دارد

### 8.2 مقایسه Router ها

**وضعیت فعلی**:
- در X: 29 فایل router در `api/routers/`
- در HAJIX: دایرکتوری `api/routes/` خالی است

**Router های ضروری** (بر اساس استفاده در `api/main.py`):
1. ✅ `system.py` - ضروری (runtime config, health)
2. ✅ `search.py` - ضروری (legal search)
3. ✅ `ingest.py` - ضروری (document upload)
4. ✅ `mahoun.py` - ضروری (main MAHOUN endpoints)
5. ✅ `health_v2.py` - ضروری (enhanced health)
6. ✅ `metrics.py` - ضروری (metrics collection)

**⚠️ لایه‌های ضروری MCP که فراموش شده‌اند** (این دو لایه برای اتصال MCP به API اصلی ضروری هستند):
7. ❌ `mahoun/api_router.py` - **ضروری برای MCP** (observability endpoints: `/internal/health`, `/internal/metrics`)
8. ❌ `mahoun/dashboard/router.py` - **ضروری برای MCP** (dashboard interface: `/internal/dashboard/*`)

**نکته مهم**: این دو router در X وجود دارند اما در HAJIX موجود نیستند. آنها برای اتصال MCP server به FastAPI اصلی ضروری هستند.

**چرا این دو لایه ضروری هستند؟**
- `mahoun/api_router.py`: 
  - Endpoints: `/internal/health`, `/internal/metrics`, `/internal/metrics/json`
  - برای observability و monitoring سیستم
  - اتصال MCP tools به metrics و health checks
  
- `mahoun/dashboard/router.py`:
  - Endpoints: `/internal/dashboard/*`
  - Dashboard UI برای مشاهده metrics، traces، health
  - رابط کاربری برای observability

**بدون این دو لایه**: MCP server (`mahoun/mcp/server.py`) نمی‌تواند به درستی به FastAPI اصلی متصل شود و observability endpoints در دسترس نخواهند بود.

**Router های اختیاری** (در X موجود اما در HAJIX استفاده نمی‌شوند):
- `admin.py` - مدیریت
- `analyze.py` - تحلیل
- `audit.py` - audit logs
- `auth.py` - احراز هویت
- `chunking.py` - chunking
- `data_management.py` - مدیریت داده
- `embedding.py` - embeddings
- `explainability.py` - توضیح‌پذیری
- `generate.py` - تولید
- `graph_health.py` - سلامت graph
- `health.py` - health check قدیمی
- `legal_rag.py` - legal RAG
- `monitoring.py` - monitoring
- `retrieval.py` - retrieval

**توصیه**: ✅ **فقط router های ضروری را کپی کنید**:
- 6 router ضروری کافی هستند
- **⚠️ اما دو لایه MCP را فراموش نکنید**:
  - `mahoun/api_router.py` - برای observability
  - `mahoun/dashboard/router.py` - برای dashboard
- Router های دیگر را در صورت نیاز اضافه کنید
- این رویکرد سبک‌تر و قابل نگهداری‌تر است

### 8.3 مقایسه Lifecycle Hooks

**وضعیت**:
- ❌ در X: lifecycle hooks موجود نیست
- ❌ در HAJIX: lifecycle hooks موجود نیست

**توصیه**: ✅ **اضافه کردن lifecycle hooks**:
- برای initialize/close database connections
- برای startup/shutdown tasks
- Best practice در FastAPI

### 8.4 خلاصه انتخاب‌های بهینه

| مورد | انتخاب فعلی | انتخاب بهینه | دلیل |
|------|------------|--------------|------|
| logging | `logging_utils` ❌ | `pipelines._logging` ✅ | قبلاً استفاده شده، ساختار بهتر |
| Router ها | همه ❌ | فقط 6 تا ضروری ✅ | سبک‌تر، قابل نگهداری |
| **MCP Layers** | **فراموش شده** ❌ | **2 لایه ضروری** ✅ | **برای اتصال MCP به API** |
| Lifecycle | موجود نیست ❌ | اضافه شود ✅ | Best practice |

---

## 9. نتیجه‌گیری

پروژه HAJIX از نظر ساختار core (agents, RAG, database) سالم است، اما مشکلات مهمی در لایه API وجود دارد:

1. **Router ها**: باید از پروژه X کپی شوند (فقط 6 تا ضروری)
2. **logging_utils**: باید رفع شود (استفاده از `pipelines._logging` - انتخاب بهینه)
3. **Lifecycle hooks**: باید اضافه شوند (بهبود نسبت به X)

**انتخاب‌های انجام شده**: 
- ✅ **بهینه**: استفاده از `pipelines._logging` به جای `logging_utils`
- ✅ **بهینه**: کپی کردن فقط router های ضروری (6 تا)
- ⚠️ **فراموش شده**: دو لایه MCP (`api_router`, `dashboard/router`) - **باید اضافه شوند**
- ✅ **بهینه**: اضافه کردن lifecycle hooks (بهبود نسبت به X)

**⚠️ نکته مهم**: دو لایه MCP (`mahoun/api_router.py` و `mahoun/dashboard/router.py`) برای اتصال MCP server به FastAPI اصلی ضروری هستند و باید از X کپی شوند.

پس از رفع این مشکلات (شامل دو لایه MCP)، پروژه باید به درستی کار کند و حتی بهتر از X باشد.

---

**گزارش تهیه شده توسط**: AI Assistant  
**تاریخ**: 2025-01-XX

