import os
import asyncpg
from dotenv import load_dotenv

# Load variables from .env if running locally
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost") 
DB_USER = os.getenv("DB_USER") or os.getenv("DB_USER_SECRET")
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("DB_PASSWORD_SECRET")
DB_NAME = os.getenv("DB_NAME") or os.getenv("DB_NAME_SECRET")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# Global connection pool
pool = None

async def init_db_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

async def close_db_pool():
    global pool
    if pool:
        await pool.close()

# --- TEACHERS ---
async def get_teachers():
    async with pool.acquire() as conn:
        records = await conn.fetch("SELECT id, first_name, last_name, email, created_at FROM TEACHER ORDER BY id;")
        return [dict(r) for r in records]

async def add_teacher(first_name, last_name, email):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO TEACHER (first_name, last_name, email) VALUES ($1, $2, $3)",
            first_name, last_name, email
        )

async def update_teacher(teacher_id, first_name, last_name, email):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE TEACHER SET first_name=$1, last_name=$2, email=$3 WHERE id=$4",
            first_name, last_name, email, teacher_id
        )

async def delete_teacher(teacher_id):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM TEACHER WHERE id=$1", teacher_id)

# --- PLAYGROUPS ---
async def get_playgroups():
    async with pool.acquire() as conn:
        # Join to get teacher's name instead of just ID
        query = """
            SELECT p.id, p.groupName as group_name, p.teacherId as teacher_id, 
                   t.first_name || ' ' || t.last_name as teacher_name, p.created_at 
            FROM PLAYGROUP p
            LEFT JOIN TEACHER t ON p.teacherId = t.id
            ORDER BY p.id;
        """
        records = await conn.fetch(query)
        return [dict(r) for r in records]

async def add_playgroup(group_name, teacher_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO PLAYGROUP (groupName, teacherId) VALUES ($1, $2)",
            group_name, teacher_id
        )

async def update_playgroup(playgroup_id, group_name, teacher_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE PLAYGROUP SET groupName=$1, teacherId=$2 WHERE id=$3",
            group_name, teacher_id, playgroup_id
        )

async def delete_playgroup(playgroup_id):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM PLAYGROUP WHERE id=$1", playgroup_id)

# --- CHILDREN ---
async def get_children():
    async with pool.acquire() as conn:
        # Join to get playgroup name
        query = """
            SELECT c.id, c.first_name, c.last_name, c.age, c.email, c.groupId as group_id, 
                   p.groupName as group_name, c.created_at 
            FROM CHILD c
            LEFT JOIN PLAYGROUP p ON c.groupId = p.id
            ORDER BY c.id;
        """
        records = await conn.fetch(query)
        return [dict(r) for r in records]

async def add_child(first_name, last_name, age, email, group_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO CHILD (first_name, last_name, age, email, groupId) VALUES ($1, $2, $3, $4, $5)",
            first_name, last_name, age, email, group_id
        )

async def update_child(child_id, first_name, last_name, age, email, group_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE CHILD SET first_name=$1, last_name=$2, age=$3, email=$4, groupId=$5 WHERE id=$6",
            first_name, last_name, age, email, group_id, child_id
        )

async def delete_child(child_id):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM CHILD WHERE id=$1", child_id)
