# aiogram-telemetry

**aiogram-telemetry** is a lightweight observability layer for [aiogram 3.x](https://docs.aiogram.dev) bots.  
It automatically tracks handler performance, errors, and custom metrics across Redis, Prometheus, and optional PostgreSQL backends.

---

## 🚀 Features

- 📊 **Automatic Metrics Collection** — track message/update counts, handler execution times, and errors.  
- ⚙️ **Zero-Boilerplate Setup** — plug it in once; no code changes to your existing handlers.  
- 🔌 **Pluggable Backends** — supports Redis (for aggregation), Prometheus (for export), and optional PostgreSQL (for persistence).  
- 🧩 **Async & Non-Blocking** — built fully on asyncio to integrate seamlessly with aiogram 3.x.  
- 🪶 **Lightweight** — minimal overhead and no extra dependencies beyond aiogram and redis.

---

## 🧠 Installation

```bash
pip install aiogram-telemetry
# optional PostgreSQL support
pip install aiogram-telemetry[postgres]
