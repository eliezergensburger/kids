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

### In PostgreSQL, **standard Foreign Key constraints do not work across different databases** (even if they are on the same server/Docker network). 

A Foreign Key requires both tables to share the same system catalog to enforce referential integrity. When using `postgres_fdw`, the "Foreign Table" in `db1` is just a proxy; `db1` has no way to "lock" or "verify" a row in `db2` during a transaction.

Here are the four ways to resolve this "conflict" and maintain data integrity:

---

### 1. The Trigger Method (Simulated Foreign Key)
If you must ensure that a record in `db1.orders` only points to a `db2.products` ID that actually exists, you can use a trigger.

**Run this on DB1:**
```sql
CREATE OR REPLACE FUNCTION check_remote_product_exists() 
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the ID exists in the foreign table
    IF NOT EXISTS (SELECT 1 FROM remote_inventory.products WHERE id = NEW.product_id) THEN
        RAISE EXCEPTION 'Product ID % does not exist in the inventory database!', NEW.product_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_product_exists
BEFORE INSERT OR UPDATE ON local_orders
FOR EACH ROW EXECUTE FUNCTION check_remote_product_exists();
```
*   **Pros:** Enforces integrity at the database level.
*   **Cons:** Performance hit (every insert/update triggers a network call to DB2).

---

### 2. The "Soft Key" Method (Application Level)
This is the most common approach in microservices. You treat the `product_id` in `db1` as a **Logical Foreign Key**. 

*   **No physical constraint:** You remove the `REFERENCES` clause in your SQL.
*   **Application Logic:** Your backend code (Node, Python, Go, etc.) is responsible for validating the ID before saving.
*   **Cleanup:** You must decide what happens if a product is deleted in `db2`. Since there is no `ON DELETE CASCADE`, your app must handle the "orphaned" records or use a "Soft Delete" (setting a `deleted_at` flag) on `db2`.

---

### 3. The Materialized View Method (Local Validation)
If the data in `db2` (like a list of products) doesn't change every second, you can sync it locally to `db1`.

1.  **Create a Materialized View** in `db1` based on the foreign table.
2.  **Create a standard Foreign Key** pointing to that Materialized View.

```sql
-- 1. Sync the remote data locally
CREATE MATERIALIZED VIEW local_products_cache AS 
SELECT id, name FROM remote_inventory.products;

-- 2. Add a unique index (required for FK targets)
CREATE UNIQUE INDEX idx_products_cache_id ON local_products_cache(id);

-- 3. Now you can use it as a reference (only works with regular tables, 
-- so you may need a 'dummy' table or triggers to sync)
```
*Note: This is complex because Postgres doesn't allow FKs to point directly to Views. You would usually use a regular table and a background job (like Cron) to `INSERT INTO ... ON CONFLICT DO UPDATE` from the foreign table.*

---

### 4. The Architectural Solution: Schemas vs. Databases
If you find yourself struggling with foreign keys between two databases on the same Docker host, ask: **Do these actually need to be two separate databases?**

In PostgreSQL, a single **Database** can have multiple **Schemas**.
*   `db1` (Database)
    *   `sales` (Schema)
    *   `inventory` (Schema)

**Foreign Keys work perfectly across Schemas.** 

If you move the tables into two schemas within the same database:
1.  You can use standard `REFERENCES inventory.products(id)`.
2.  You still keep the data organized and separated.
3.  Performance is much higher (no network overhead).

---

### Summary: Which should you choose?
1.  **Use Triggers** if you have low-volume writes and high integrity requirements.
2.  **Use Soft Keys** if you are building a modern Microservices architecture.
3.  **Use Schemas** if you are still in the development phase and realized the two databases are tightly coupled (this is usually the "best" technical fix).
