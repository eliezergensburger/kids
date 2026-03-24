This is a comprehensive guide to integrating two PostgreSQL databases in a Docker environment using the `postgres_fdw` (Foreign Data Wrapper) method.

Save the following content as a single `.md` file (e.g., `postgres-integration-guide.md`).

---

# PostgreSQL Multi-Database Integration Guide (Docker + pgAdmin)

This guide explains how to link two independent PostgreSQL databases (`db1` and `db2`) running in Docker so that `db1` can query tables from `db2` selectively.

## 1. Environment Configuration (`.env`)
Create a `.env` file to manage credentials and ports. This keeps your configuration clean and portable.

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

---

## 2. Docker Orchestration (`docker-compose.yml`)
This setup uses a shared internal network (`backend`) allowing containers to communicate using their service names.

```yaml
services:
  db1:
    image: postgres:16-alpine
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
      - ./db1_init:/docker-entrypoint-initdb.d # Auto-setup folder
    networks:
      - backend

  db2:
    image: postgres:16-alpine
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
    restart: always
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "${PGADMIN_PORT}:80"
    depends_on:
      - db1
      - db2
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  db1_data:
  db2_data:
```

---

## 3. Connecting via pgAdmin
1. Open `http://localhost:8080`.
2. **Register db1**: Host name: `db1`, Port: `5432`.
3. **Register db2**: Host name: `db2`, Port: `5432`.
   * *Note: Inside the Docker network, all Postgres containers listen on 5432.*

---

## 4. Setting up the Integration (Foreign Data Wrapper)
To allow `db1` to "see" `db2`, execute these SQL commands in the **db1 Query Tool** in pgAdmin.

### Step A: Enable Extension and Create Server
```sql
-- Enable the FDW extension
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- Create the connection link to the second container
CREATE SERVER remote_db2_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'db2', port '5432', dbname 'inventory_db');
```

### Step B: Map Users
Tell `db1` which credentials to use when it knocks on `db2`'s door.
```sql
CREATE USER MAPPING FOR admin
SERVER remote_db2_server
OPTIONS (user 'admin', password 'secret_pass_2');
```

### Step C: Selective Table Import (Recommended)
You do **not** have to import the entire database. You can choose exactly which tables you want.

**Option 1: Import only specific tables**
```sql
CREATE SCHEMA remote_inventory;

IMPORT FOREIGN SCHEMA public 
LIMIT TO (products, stock_levels) -- Only these tables will be linked
FROM SERVER remote_db2_server 
INTO remote_inventory;
```

**Option 2: Import everything EXCEPT specific tables**
```sql
IMPORT FOREIGN SCHEMA public 
EXCEPT (sensitive_user_data, internal_logs) 
FROM SERVER remote_db2_server 
INTO remote_inventory;
```

**Option 3: Manual definition (Maximum Control)**
If you only want specific columns from a remote table:
```sql
CREATE FOREIGN TABLE remote_inventory.product_titles (
    id int NOT NULL,
    product_name text
)
SERVER remote_db2_server
OPTIONS (schema_name 'public', table_name 'products');
```

---

## 5. Performance & Maintenance Tips

### Materialized Views for Speed
Cross-database queries can be slower than local ones. If the data doesn't change every second, cache it:
```sql
CREATE MATERIALIZED VIEW cached_products AS
SELECT * FROM remote_inventory.products;

-- Refresh when needed
REFRESH MATERIALIZED VIEW cached_products;
```

### Updating Schema Changes
If you add a column to a table in `db2`, it won't appear in `db1` automatically. You must refresh the link:
```sql
DROP SCHEMA remote_inventory CASCADE;
-- Then re-run the IMPORT FOREIGN SCHEMA command from Step 4C.
```

### Automation via Antigravity/Startup
If you want this setup to be ready every time you run `docker-compose up`, place the SQL from Step 4 into a file named `./db1_init/01_init_fdw.sql`. Docker will execute this script automatically during the first container creation.