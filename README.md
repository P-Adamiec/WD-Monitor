# 🔴 WD Monitor

A real-time, beautifully designed Western Digital product availability tracker with price history, Discord alerts, and multi-locale support. Never miss a restock on high-capacity hard drives again.

## ✨ Features

- **Live Product Monitoring** — Track any WD HDD by SKU with automatic, background availability checking.
- **High-Performance Batching** — Checks up to 20 products in a single API request, eliminating lag even when tracking hundreds of hard drives.
- **Adjustable Polling Interval** — Configure check intervals on the fly directly from the UI (from 10 seconds up to 10 minutes).
- **Price History Charts** — Visual price tracking over time with green/red segments for in-stock/out-of-stock periods.
- **Smart Status Badges** — Distinct statuses for "In Stock", "Out of Stock", "Pending", and "Inquiry Only" products.
- **Stock Level Tracking** — Warns you exactly how many items are left in stock (e.g., "1 left" / "1 szt.").
- **Full Internationalization (i18n)** — UI fully translated into Polish (🇵🇱), English (🇺🇸), and German (🇩🇪) with instant, synchronous switching using SVG flags.
- **Multi-Region Store Support** — Switch your monitoring target context dynamically between PL, DE, US, UK, FR, IT, ES, and NL stores.
- **Discord Notifications** — Ping your Discord server via Webhook whenever a tracked product comes back in stock or changes price. Includes the full product name and precise price drops/increases.
- **Bulk Actions & Filtering** — Filter your catalog by capacity, drive series, or clearance status. Select multiple products for batch deletion or notification toggling.
- **Mobile Responsive** — Glassmorphism UI that looks stunning on desktop, tablet, and mobile browsers.

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python (Flask), Background Threads |
| **Database** | PostgreSQL |
| **Frontend** | Vanilla JS, CSS Glassmorphism, Chart.js, Flag-Icons |
| **API Client** | `curl_cffi` (Browser Impersonation to bypass blocks) |
| **Deployment** | Docker & Docker Compose |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose

### Launch

```bash
# Clone the repository
git clone https://github.com/yourusername/wd-monitor.git
cd wd-monitor

# Start the application in detached mode
docker-compose up -d --build
```

Once running, open your browser and navigate to:
**http://localhost:5000**

### Environment Variables

You can customize the deployment by copying `.env.example` to `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://monitor_user:monitor_password@db:5432/monitor_db` | PostgreSQL connection string |
| `CHECK_INTERVAL_SECONDS` | `60` | Fallback polling interval. (Can be overridden dynamically in the UI). |
| `WD_LOCALE` | `pl-pl` | Default starting locale for the WD store API. |

## 🧠 How It Works

1. **Catalog Parsing** — Products are loaded intuitively from `catalog.json` (providing SKUs, names, categories, capacities, and URLs).
2. **Monitoring Engine** — A resilient background thread chunks your tracked targets by locale into batches of up to 20 items. This allows the tool to query the WD GraphQL API lightning-fast without triggering rate limits.
3. **Price History** — Prices are recorded internally into PostgreSQL on a daily basis and instantly if any state changes (e.g., goes in-stock at a new price).
4. **Alerts** — Discord webhooks fire immediately using the saved settings when a product becomes available again or shifts in price.
5. **UI Instant-Translation** — No page reloads needed. The entire JS-rendered product catalog and your tracked targets instantly recreate themselves in your chosen language upon clicking a flag.

## 📁 Project Structure

```text
├── backend/
│   ├── routes.py          # Flask API Endpoints
│   ├── monitor.py         # Threaded Monitoring Engine & Batch API calls
│   ├── database.py        # PostgreSQL Connection & Setup
│   ├── config.py          # Environment configuration
│   └── notifications.py   # Discord Webhook integration
├── static/
│   ├── js/                # Modular Frontend Javascript (i18n, charts, settings, etc.)
│   └── style.css          # Core Styling & Glassmorphism themes
├── templates/
│   └── index.html         # Single-page App (SPA) base layout
├── docker-compose.yml     # Container Orchestration
├── Dockerfile             # Python Image setup
├── run.py                 # Application Bootstrap
└── catalog.json           # Known SKUs dictionary
```

## 📝 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
