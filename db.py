# db.py
import os
import json
import logging
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_POOL = None

def get_pool():
    global DB_POOL
    if DB_POOL is not None:
        return DB_POOL

    # Connection parameters from .env/environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME', 'teaching_staff_rating')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_pass = os.environ.get('DB_PASS', 'postgres')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    try:
        logging.info("Initializing PostgreSQL connection pool...")
        DB_POOL = SimpleConnectionPool(1, 10, db_url)
        return DB_POOL
    except Exception as e:
        logging.error(f"Error creating connection pool: {e}")
        return None

@contextmanager
def get_db_connection():
    pool = get_pool()
    if pool is None:
        raise RuntimeError("Database connection pool is not initialized. Please verify your connection settings in .env.")
    
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Database transaction error: {e}")
        raise e
    finally:
        pool.putconn(conn)

def init_db():
    query = """
    CREATE TABLE IF NOT EXISTS ratings (
        full_name VARCHAR(255) PRIMARY KEY,
        position VARCHAR(255) NOT NULL,
        institution_type VARCHAR(255),
        department VARCHAR(255),
        total_score NUMERIC(10, 2) NOT NULL,
        details JSONB NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                logging.info("Database tables initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}")
        # We do not crash the app setup immediately to allow loading, but log the failure.

def save_rating(full_name, position, institution_type, department, total_score, details):
    query = """
    INSERT INTO ratings (full_name, position, institution_type, department, total_score, details, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (full_name) DO UPDATE SET
        position = EXCLUDED.position,
        institution_type = EXCLUDED.institution_type,
        department = EXCLUDED.department,
        total_score = EXCLUDED.total_score,
        details = EXCLUDED.details,
        updated_at = CURRENT_TIMESTAMP;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (
                full_name,
                position,
                institution_type,
                department,
                total_score,
                json.dumps(details, ensure_ascii=False)
            ))
            logging.info(f"Saved rating for {full_name} (Score: {total_score})")

def get_leaderboard():
    query = """
    SELECT full_name, position, total_score
    FROM ratings;
    """
    leaderboard_data = {}
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                for row in rows:
                    name, pos, score = row
                    leaderboard_data[name] = {
                        'score': float(score),
                        'position': pos
                    }
    except Exception as e:
        logging.error(f"Error loading leaderboard from database: {e}")
    return leaderboard_data

def delete_rating(full_name):
    query = "DELETE FROM ratings WHERE full_name = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (full_name,))
            logging.info(f"Deleted rating for {full_name}")

def rename_rating(original_name, new_name, position, score):
    query = """
    UPDATE ratings
    SET full_name = %s, position = %s, total_score = %s, updated_at = CURRENT_TIMESTAMP
    WHERE full_name = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (new_name, position, score, original_name))
            logging.info(f"Renamed rating from '{original_name}' to '{new_name}'")

def get_rating_details(full_name):
    query = "SELECT details, institution_type, department, position FROM ratings WHERE full_name = %s;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (full_name,))
                row = cur.fetchone()
                if row:
                    details_json, inst_type, dept, pos = row
                    if isinstance(details_json, str):
                        return json.loads(details_json), inst_type, dept, pos
                    return details_json, inst_type, dept, pos
    except Exception as e:
        logging.error(f"Error fetching details for user '{full_name}': {e}")
    return None, None, None, None
