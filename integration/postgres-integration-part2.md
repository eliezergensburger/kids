## Integration from 'backupxxxx' file

To integrate a backup file into your Dockerized PostgreSQL setup, you need to follow a three-step process: **Upload**, **Restore**, and **Link**.

Since you have a backup file (let's call it `backup.sql` or `backup.dump`), we will restore it into **Database 2 (`db2`)** and then link it to **Database 1 (`db1`)**.

---

### Step 1: Move the Backup into Docker
Docker containers cannot "see" files on your Windows/Mac desktop unless you move them or mount them.

**Option A: The Command Line (Fastest)**
Open your terminal/command prompt in the folder where your backup file is located and run:
```bash
docker cp backupxxxx sales_container:/tmp/backupxxxx
```
*(Replace `sales_container` with the `container_name` from your docker-compose for db2).*

**Option B: The Volume Folder**
If your `docker-compose` has a volume like `./db2_init:/docker-entrypoint-initdb.d`, just move the file into that folder on your computer. If it is a `.sql` file, Postgres will try to run it automatically when the container starts for the first time.

---

### Step 2: Restore the Backup via pgAdmin
Once the file is "inside" the environment, use pgAdmin to restore it.

1.  Open **pgAdmin**.
2.  Right-click on your **Target Database** (e.g., `inventory_db` on `db2`).
3.  Select **Restore**.
4.  In the **Filename** field, click the folder icon.
    *   If you used `docker cp`, look in `/tmp/`.
    *   If you mapped a volume, look in the mapped path.
5.  Select your file and click **Restore**.

> **Note:** If the backup was created using the "Plain" format in pgAdmin, use the **Query Tool** to open the file and hit **Play**. If it was "Custom" or "Tar" format, use the **Restore** menu.

---

### Step 3: Create the Integration (The "Link")
Now that your data is living inside `db2`, you need to tell `db1` how to read it using the **Foreign Data Wrapper** method we discussed.

**Run this in the Query Tool of `db1`:**

```sql
-- 1. Enable the bridge tool
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- 2. Define the server (use the docker service name 'db2')
CREATE SERVER restored_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'db2', port '5432', dbname 'inventory_db');

-- 3. Map your credentials
CREATE USER MAPPING FOR sales_admin
SERVER restored_server
OPTIONS (user 'inventory_admin', password 'inventory_pass_456');

-- 4. Import the specific tables from the backup
-- IMPORTANT: Look at the restored database in pgAdmin. 
-- If the backup created a schema named 'public', use 'public'.
-- If it created a schema named 'client_data', use that.
CREATE SCHEMA restored_data;

IMPORT FOREIGN SCHEMA public 
LIMIT TO (table_name_from_backup) 
FROM SERVER restored_server 
INTO restored_data;
```

---

### Step 4: Resolve the Foreign Key (Soft Key)
Now that the backup data is visible in `db1`, you can link your local tables to it.

If your backup contains a table of `products` and you want your local `orders` table to point to them:

1.  **Check the ID type:** Look at the `id` column in `restored_data.products`. Is it an Integer? A UUID?
2.  **Create your local table:**
    ```sql
    CREATE TABLE local_orders (
        id SERIAL PRIMARY KEY,
        -- Redefine the product_id to match the backup's ID type
        backup_product_id INTEGER, 
        customer_name TEXT
    );
    ```
3.  **Perform the Integration Join:**
    ```sql
    SELECT 
        o.customer_name, 
        p.name as product_from_backup
    FROM local_orders o
    JOIN restored_data.products p ON o.backup_product_id = p.id;
    ```

---

### Troubleshooting Common Backup Integration Issues:

*   **Role Not Found:** If the backup was made from a database where the user was `boss_man`, and your Docker user is `admin`, the restore might show errors.
    *   *Fix:* In the pgAdmin Restore dialog, go to **Restore options** and check **Do not save owner**.
*   **Schema Confusion:** If your backup contains multiple schemas, you must run the `IMPORT FOREIGN SCHEMA` command for **each** schema you want to link.
*   **Search Path:** If you want to query the restored tables easily without typing `restored_data.`, run:
    ```sql
    SET search_path TO public, restored_data;
    ```

### Summary of the Workflow:
1.  **Restore** the backup into the second container (`db2`).
2.  **Link** the first container (`db1`) to the second using `postgres_fdw`.
3.  **Map** the foreign tables into a local schema.
4.  **Join** them using "Soft Keys" (Standard Integers) in your queries.