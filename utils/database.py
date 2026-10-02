"""Database operations for NewsFindr"""

import sqlite3
import os
from typing import List
from langchain_community.utilities.sql_database import SQLDatabase
from core.config import DB_PATH

def get_db_path():
    """Get database path, auto-detect and copy if missing"""
    if os.path.exists(DB_PATH):
        return DB_PATH
    
    possible_paths = [
        "customer.db",
        "../customer.db",
        "../../customer.db",
        os.path.expanduser("~/customer.db"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            os.makedirs("data", exist_ok=True)
            import shutil
            shutil.copy(path, DB_PATH)
            print(f"Copied database from {path} to {DB_PATH}")
            return DB_PATH
    
    raise FileNotFoundError(f"customer.db not found. Checked: {possible_paths}")

def initialize_db():
    """Initialize database connection"""
    db_path = get_db_path()
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    tables = db.get_usable_table_names()
    
    if not tables:
        raise ValueError("Database has no tables")
    
    return db

def fetch_interests_direct(email: str) -> List[str]:
    """Direct SQL query to fetch user interests"""
    db_path = get_db_path()

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT interests FROM customers WHERE email = ?",
                (email,)
            )
            rows = cursor.fetchall()
        
        interests = []
        for (val,) in rows:
            try:
                import json
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    interests.extend(str(i).strip() for i in parsed if str(i).strip())
            except (json.JSONDecodeError, TypeError):
                interests.extend(i.strip() for i in str(val).split(",") if i.strip())

        return interests
    except Exception as e:
        print(f"Database error: {e}")
        return []

def get_all_emails() -> List[str]:
    """Get all email addresses from database"""
    db_path = get_db_path()

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM customers")
            rows = cursor.fetchall()
        
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Database error: {e}")
        return []

def parse_interests(text: str) -> List[str]:
    """Parse interests from LLM response or raw text"""
    import re
    import json
    
    if not text:
        return []
    
    if re.search(r"\b(sorry|cannot|can't|fail|unable to|no interests?)\b", text, re.IGNORECASE):
        return []
    
    match = re.search(r"\[.*?\]", text, re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return [str(i).strip().strip("'\"") for i in parsed if str(i).strip()]
        except json.JSONDecodeError:
            pass
    
    text = re.sub(r"^[^:]{0,60}:", "", text.strip(), count=1)
    parts = re.split(r"[,;\n]|\s\|\s", text.strip(" []"))
    return [p.strip(" -*\"'") for p in parts if 1 < len(p.strip(" -*\"'")) < 60]

def fetch_interests(email: str, use_agent: bool = False) -> List[str]:
    """Fetch user interests from database"""
    interests = fetch_interests_direct(email)
    
    seen, cleaned = set(), []
    for i in interests:
        k = i.lower()
        if k not in seen:
            seen.add(k)
            cleaned.append(i)
    
    return cleaned[:2]
