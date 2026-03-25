"""
db.py — MySQL database layer for Image Editor Login
Requires: pip install mysql-connector-python
"""

import mysql.connector
from mysql.connector import Error
import hashlib
import os

# ── Load .env file ───────────────────────────────────────────────────────────
_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# ── Connection config ────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("MYSQL_HOST",     "localhost"),
    "port":     int(os.environ.get("MYSQL_PORT", "3306")),
    "user":     os.environ.get("MYSQL_USER",     "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "image_editor"),
}

# ── Schema ───────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(64) NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50) NOT NULL,
    input_path  TEXT NOT NULL,
    output_path TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create database + tables if they don't exist."""
    cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    conn = mysql.connector.connect(**cfg)
    cur  = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cur.execute(f"USE {DB_CONFIG['database']}")
    for statement in SCHEMA.strip().split(";"):
        s = statement.strip()
        if s:
            cur.execute(s)
    conn.commit()

    cur.execute("SELECT id FROM users WHERE username = %s", ("admin",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", _hash("1234"))
        )
        conn.commit()

    cur.close()
    conn.close()


def validate_user(username: str, password: str) -> bool:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE username = %s AND password = %s",
            (username, _hash(password))
        )
        found = cur.fetchone() is not None
        cur.close()
        conn.close()
        return found
    except Error as e:
        raise ConnectionError(f"DB error: {e}")


def register_user(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password are required."
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, _hash(password))
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, "Account created successfully."
    except mysql.connector.IntegrityError:
        return False, "Username already exists."
    except Error as e:
        return False, f"DB error: {e}"


def add_history(username: str, input_path: str, output_path: str) -> None:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO history (username, input_path, output_path) VALUES (%s, %s, %s)",
            (username, input_path, output_path)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Error:
        pass


def get_history(username: str) -> list:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, input_path, output_path, created_at FROM history "
            "WHERE username = %s ORDER BY created_at DESC",
            (username,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Error:
        return []
