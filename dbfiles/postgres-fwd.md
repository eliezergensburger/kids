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