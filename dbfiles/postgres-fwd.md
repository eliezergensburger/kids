To integrate two PostgreSQL databases running in Docker Desktop and manage them via pgAdmin, the most effective method is using the **PostgreSQL Foreign Data Wrapper (`postgres_fdw`)**. This allows you to query tables from one database while connected to the other as if they were local.

Since you are using **Antigravity** workflows, you likely want a clean, scaffolded approach. Below is the configuration for your `docker-compose.yml`, `.env`, and the SQL commands to link them.

### 1. Configure `.env`
Define the credentials for both databases and pgAdmin. This keeps your secrets out of the compose file.

```ini
# Database 1 (Primary/Source)
DB1_NAME=sales_db
DB1_USER=admin
DB1_PASSWORD=secret_pass_1
DB1_PORT=5432

# Database 2 (Secondary/Target)
DB2_NAME=inventory_db
DB2_USER=admin
DB2_PASSWORD=secret_pass_2
DB2_PORT=5433

# pgAdmin
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin_pass
PGADMIN_PORT=8080
```

### 2. Configure `docker-compose.yml`
This setup places all containers on a single internal network so they can "see" each other using their service names (`db1` and `db2`) instead of IP addresses.

```yaml
services:
  db1:
    image: postgres:17.1
    container_name: db1_postgres
    restart: always
    environment:
      POSTGRES_DB: ${DB1_NAME}
      POSTGRES_USER: ${DB1_USER}
      POSTGRES_PASSWORD: ${DB1_PASSWORD}
    ports:
      - "${DB1_PORT}:5432"
    volumes:
      - db1_data:/var/lib/postgresql/data

  db2:
    image: postgres:17.1
    container_name: db2_postgres
    restart: always
    environment:
      POSTGRES_DB: ${DB2_NAME}
      POSTGRES_USER: ${DB2_USER}
      POSTGRES_PASSWORD: ${DB2_PASSWORD}
    ports:
      - "${DB2_PORT}:5432"
    volumes:
      - db2_data:/var/lib/postgresql/data

  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin_container
    restart: always
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    ports:
      - "${PGADMIN_PORT}:80"
    depends_on:
      - db1
      - db2

volumes:
  db1_data:
  db2_data:
```

### 3. Access in pgAdmin
1. Open `http://localhost:8080` and log in.
2. **Register db1**: 
   - **Host name**: `db1` (Use the service name from docker-compose, not `localhost`).
   - **Port**: `5432`.
3. **Register db2**: 
   - **Host name**: `db2`.
   - **Port**: `5432`.

### 4. Perform the Integration (The "Bridge")
To make `db1` able to read data from `db2`, run these SQL commands **inside the `db1` query tool** in pgAdmin:

#### Step A: Enable the Extension
```sql
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
```

#### Step B: Create a Foreign Server
This tells `db1` how to reach `db2`. Note that we use the Docker service name `db2` as the host.
```sql
CREATE SERVER inventory_link
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'db2', port '5432', dbname 'inventory_db');
```

#### Step C: Map the User
This tells `db1` which credentials to use when logging into `db2`.
```sql
CREATE USER MAPPING FOR admin -- your db1 user
SERVER inventory_link
OPTIONS (user 'admin', password 'secret_pass_2'); -- db2 credentials
```

#### Step D: Import the Tables
You can now import the entire schema or specific tables from `db2` into `db1`.
```sql
-- This imports all tables from 'public' schema of db2 into db1's public schema
IMPORT FOREIGN SCHEMA public 
FROM SERVER inventory_link 
INTO public;
```

### How to use it
Now, even if you are only connected to `db1`, you can run a query like:
```sql
SELECT a.customer_name, b.item_name 
FROM local_sales_table a
JOIN foreign_inventory_table b ON a.product_id = b.id;
```

### Pro Tips for Antigravity Users:
*   **Networking**: When containers are in the same `docker-compose.yml`, they are on the same network by default. Always use the **service name** (e.g., `db1`) for internal links, and **localhost** only for external tools like DBeaver or a browser.
*   **Initialization**: If you want these steps to happen automatically on build, you can place the SQL scripts in a `./init` folder and map it to `/docker-entrypoint-initdb.d/` in your compose file.

To "enhance" this setup, we will move beyond a basic connection and focus on **automation, security, and performance**.

Instead of manually running SQL in pgAdmin, we will configure the integration to **self-assemble** the moment you run `docker-compose up`.

### 1. The Enhanced Folder Structure
Organizing your scripts allows Docker to initialize the integration automatically.
```text
.
├── .env
├── docker-compose.yml
├── db1_init/
│   └── 01_setup_fdw.sql   <-- This runs on DB1 startup
└── db2_init/
    └── 01_seed_data.sql    <-- This creates tables in DB2
```

### 2. Enhanced `docker-compose.yml`
We add **Healthchecks** and **Internal Networks**. Healthchecks ensure `db1` doesn't try to connect to `db2` before `db2` is fully ready.

```yaml
services:
  db1:
    image: postgres:16-alpine
    container_name: db1_postgres
    environment:
      POSTGRES_DB: ${DB1_NAME}
      POSTGRES_USER: ${DB1_USER}
      POSTGRES_PASSWORD: ${DB1_PASSWORD}
      DB2_NAME: ${DB2_NAME} # Pass these so SQL scripts can use them
      DB2_USER: ${DB2_USER}
      DB2_PASS: ${DB2_PASSWORD}
    ports:
      - "${DB1_PORT}:5432"
    volumes:
      - db1_data:/var/lib/postgresql/data
      - ./db1_init:/docker-entrypoint-initdb.d # Auto-run scripts
    depends_on:
      db2:
        condition: service_healthy
    networks:
      - backend

  db2:
    image: postgres:16-alpine
    container_name: db2_postgres
    environment:
      POSTGRES_DB: ${DB2_NAME}
      POSTGRES_USER: ${DB2_USER}
      POSTGRES_PASSWORD: ${DB2_PASSWORD}
    ports:
      - "${DB2_PORT}:5432"
    volumes:
      - db2_data:/var/lib/postgresql/data
      - ./db2_init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB2_USER} -d ${DB2_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin_container
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_CONFIG_SERVER_MODE: 'False' # Optimization for local use
    ports:
      - "${PGADMIN_PORT}:80"
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  db1_data:
  db2_data:
```

### 3. Automated SQL Initialization
Create `db1_init/01_setup_fdw.sql`. This script uses the environment variables passed in the compose file to link the databases automatically.

```sql
-- 1. Enable FDW
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- 2. Create the link to DB2
-- Use 'db2' as the host because they share the Docker network
CREATE SERVER remote_db2_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'db2', port '5432', dbname 'inventory_db');

-- 3. Map the local admin to the remote admin
-- Note: In production, use a dedicated read-only user for safety
CREATE USER MAPPING FOR admin
SERVER remote_db2_server
OPTIONS (user 'admin', password 'secret_pass_2');

-- 4. Create a specific schema to hold the foreign tables
-- This keeps your local and remote tables organized
CREATE SCHEMA remote_inventory;

-- 5. Import the remote schema
IMPORT FOREIGN SCHEMA public 
FROM SERVER remote_db2_server 
INTO remote_inventory;
```

### 4. Performance Enhancement: Materialized Views
Cross-database joins over a network (even a Docker network) can be slow for large datasets. To fix this, use a **Materialized View** on `db1` that caches data from `db2`.

In pgAdmin, you can run this on `db1`:
```sql
CREATE MATERIALIZED VIEW cached_inventory AS
SELECT id, item_name, stock_count
FROM remote_inventory.products;

-- Create an index on the cached data for lightning speed
CREATE INDEX idx_cached_item_name ON cached_inventory(item_name);

-- To refresh the data from DB2:
REFRESH MATERIALIZED VIEW cached_inventory;
```

### 5. Advanced Security (Read-Only Integration)
If `db1` should only **read** from `db2` (e.g., a Reporting DB reading from a Production DB), do this in your `db2_init` script:

1. Create a `readonly` user in `db2`.
2. Map `db1`'s server to that `readonly` user.
3. This prevents `db1` from accidentally deleting or updating data in `db2`.

### 6. Verification Checklist
1. **Network Check**: From inside the `db1` container, can you ping `db2`?
   - `docker exec -it db1_postgres ping db2`
2. **Postgres Logs**: Watch logs as the containers start to see if the FDW setup failed.
   - `docker-compose logs -f db1`
3. **pgAdmin Visuals**: In pgAdmin, under `db1` -> `Foreign Servers`, you should see `remote_db2_server` already created and ready to use.

### Why this is better:
*   **Infrastructure as Code**: If you delete your containers and run `docker-compose up` again, the integration is rebuilt instantly.
*   **Encapsulation**: Using a dedicated schema (`remote_inventory`) prevents table name collisions between the two databases.
*   **Health Awareness**: `db1` won't crash or throw errors on startup because it waits for `db2` to be healthy.