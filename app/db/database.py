import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'claim_ledger.db')


def get_db_path():
    data_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return DB_PATH


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            contract_section TEXT,
            affected_area TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            responsible_party TEXT,
            supervision_notice_no TEXT,
            owner_order_no TEXT,
            description TEXT,
            visa_received INTEGER DEFAULT 0,
            resume_order_received INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            file_path TEXT NOT NULL,
            remark TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machinery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            machine_name TEXT NOT NULL,
            specification TEXT,
            quantity REAL DEFAULT 0,
            unit TEXT DEFAULT '台·天',
            remark TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS labor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            record_date TEXT NOT NULL,
            team_name TEXT NOT NULL,
            worker_count INTEGER DEFAULT 0,
            work_type TEXT,
            remark TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cost_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            version_name TEXT NOT NULL,
            version_desc TEXT,
            is_current INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            version_id INTEGER,
            cost_category TEXT NOT NULL,
            item_name TEXT NOT NULL,
            unit_price REAL DEFAULT 0,
            quantity REAL DEFAULT 0,
            unit TEXT,
            remark TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES cost_versions(id) ON DELETE SET NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL,
            doc_no TEXT,
            file_path TEXT,
            remark TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    ''')

    try:
        cursor.execute("ALTER TABLE cost_items ADD COLUMN version_id INTEGER REFERENCES cost_versions(id) ON DELETE SET NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("SELECT visa_received FROM events LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN visa_received INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN resume_order_received INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("SELECT follow_status FROM events LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN follow_status TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()
