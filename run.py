"""WD Monitor — Entry Point.
Initializes database, loads catalog, starts background threads, runs Flask.
"""
import threading
from backend import create_app
from backend.database import init_db
from backend.catalog import load_catalog, start_catalog_refresh
from backend.monitor import monitor_thread

# Initialize database schema
init_db()

# Load product catalog
load_catalog()

# Start catalog auto-refresh thread
start_catalog_refresh()

# Create Flask application
app = create_app()

if __name__ == "__main__":
    t = threading.Thread(target=monitor_thread, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
