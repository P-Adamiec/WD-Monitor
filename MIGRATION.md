# Database Migration Guide (PostgreSQL to SQLite)

In the latest update, WD-Monitor has transitioned its architecture to use a unified SQLite database, replacing the dual-container setup that required a dedicated PostgreSQL instance. This change significantly reduces memory usage, simplifies the deployment process, and ensures better stability across systems.

This guide will walk you through the process of migrating your existing PostgreSQL data (tracked products, price history, logs, and settings) to the new SQLite format safely without losing any data.

> **⚠️ IMPORTANT:** Do not run `docker-compose down` on your existing setup until you have completed the migration steps below, otherwise your PostgreSQL container and data might be permanently removed.

## Migration Steps

Follow these instructions to safely migrate your database:

### 1. Update the Repository
Pull the latest changes from the repository. This will fetch the new SQLite configuration and the migration script.
```bash
git pull origin dev
```

### 2. Copy the Migration Script
Before stopping your current containers, you need to copy the migration script into the running `wd-monitor` backend container. 
*Note: If you run the development environment, substitute `wd-monitor` with `wd-monitor-dev` in the commands below.*

```bash
docker cp tools/migrate_pg_to_sqlite.py wd-monitor:/app/migrate_pg.py
```

### 3. Run the Migration Script
Execute the script inside the running container. This script will connect to your active PostgreSQL database, extract all targets, settings, and historical logs, and convert them into the new SQLite format (`monitor.db`).

```bash
docker exec wd-monitor python /app/migrate_pg.py
```

### 4. Extract the SQLite Database
Once the script completes successfully, extract the newly created `monitor.db` file from the container to your host machine.

```bash
# Create the local data directory if it doesn't exist
mkdir data

# Copy the database from the container to the local data directory
docker cp wd-monitor:/data/monitor.db ./data/monitor.db
```

### 5. Rebuild the Containers
Now that your data is safely stored in `./data/monitor.db`, you can safely take down the old architecture. The `--remove-orphans` flag ensures that the old PostgreSQL container is automatically cleaned up and removed.

```bash
# Bring down the old environment and clean up orphaned containers
docker-compose down --remove-orphans

# Build and start the new, lightweight SQLite-based environment
docker-compose up -d --build
```

### Verification
Once the new container starts, navigate to your WD-Monitor dashboard. All your previously tracked products, custom settings, and price history graphs should be available exactly as you left them. Moving forward, the application will read from and write to the `./data/monitor.db` file automatically.
