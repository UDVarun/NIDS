"""
backend/db/database.py
=======================
SQLite connection management + alert logging.
Uses thread-local connections for thread safety.
"""

import os
import json
import sqlite3
import threading
from datetime import datetime
from utils.logger import get_logger

logger      = get_logger('database')
DB_PATH     = os.environ.get('DB_PATH', 'db/nids.db')
_local      = threading.local()
_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_connection() -> sqlite3.Connection:
    if not hasattr(_local, 'conn') or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
        _init_schema(_local.conn)
    return _local.conn


def _init_schema(conn: sqlite3.Connection) -> None:
    try:
        with open(_SCHEMA_PATH, 'r') as f:
            schema = f.read()
        conn.executescript(schema)
        conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Schema init failed: {e}")
        raise


def log_alert(alert: dict) -> None:
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO alerts
            (timestamp, datetime_str, src_ip, dst_ip, protocol,
             prediction, attack_type, confidence, anomaly_score,
             is_attack, raw_features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.get('timestamp', 0),
            datetime.fromtimestamp(alert.get('timestamp', 0))
                    .strftime('%Y-%m-%d %H:%M:%S'),
            alert.get('src_ip', ''),
            alert.get('dst_ip', ''),
            alert.get('protocol', ''),
            alert.get('prediction', ''),
            alert.get('attack_type'),
            alert.get('confidence', 0.0),
            alert.get('anomaly_score', 0.0),
            1 if alert.get('is_attack') else 0,
            json.dumps(alert.get('features', {}))
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to log alert: {e}")


def get_recent_alerts(limit: int = 50, offset: int = 0,
                      attack_type: str = None) -> list:
    conn  = get_connection()
    query = "SELECT * FROM alerts"
    args  = []
    if attack_type:
        query += " WHERE attack_type = ?"
        args.append(attack_type)
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    args.extend([limit, offset])
    rows = conn.execute(query, args).fetchall()
    return [dict(row) for row in rows]


def get_attack_counts() -> dict:
    conn = get_connection()
    rows = conn.execute("""
        SELECT attack_type, COUNT(*) as cnt
        FROM alerts WHERE is_attack = 1
        GROUP BY attack_type
    """).fetchall()
    return {row['attack_type']: row['cnt'] for row in rows if row['attack_type']}
