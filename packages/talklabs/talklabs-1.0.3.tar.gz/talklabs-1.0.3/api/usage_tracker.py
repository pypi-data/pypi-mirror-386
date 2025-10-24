import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List
import os

DB_PATH = "/home/francisco/talklabs/data/usage.db"

class UsageTracker:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT NOT NULL,
                client_name TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                voice_id TEXT NOT NULL,
                text_length INTEGER NOT NULL,
                characters INTEGER NOT NULL,
                tokens INTEGER NOT NULL,
                audio_duration_seconds REAL NOT NULL,
                model_id TEXT DEFAULT 'eleven_multilingual_v2',
                language_code TEXT DEFAULT 'pt',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_summary (
                api_key TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                total_requests INTEGER DEFAULT 0,
                total_characters INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_audio_seconds REAL DEFAULT 0,
                first_use DATETIME,
                last_use DATETIME
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_key ON usage_log(api_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_log(timestamp)")
        conn.commit()
        conn.close()
    
    def log_usage(self, api_key: str, client_name: str, endpoint: str, voice_id: str, 
                  text: str, audio_duration: float, model_id: str = "eleven_multilingual_v2",
                  language_code: str = "pt", metadata: Optional[Dict] = None):
        characters = len(text)
        tokens = max(1, len(text) // 4)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO usage_log 
            (api_key, client_name, endpoint, voice_id, text_length, 
             characters, tokens, audio_duration_seconds, model_id, 
             language_code, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (api_key, client_name, endpoint, voice_id, len(text),
              characters, tokens, audio_duration, model_id, 
              language_code, json.dumps(metadata) if metadata else None))
        
        cursor.execute("""
            INSERT INTO usage_summary 
            (api_key, client_name, total_requests, total_characters, 
             total_tokens, total_audio_seconds, first_use, last_use)
            VALUES (?, ?, 1, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(api_key) DO UPDATE SET
                total_requests = total_requests + 1,
                total_characters = total_characters + ?,
                total_tokens = total_tokens + ?,
                total_audio_seconds = total_audio_seconds + ?,
                last_use = CURRENT_TIMESTAMP
        """, (api_key, client_name, characters, tokens, audio_duration,
              characters, tokens, audio_duration))
        
        conn.commit()
        conn.close()
    
    def get_usage_by_key(self, api_key: str) -> Dict:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usage_summary WHERE api_key = ?", (api_key,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                "api_key": api_key,
                "total_requests": 0,
                "total_characters": 0,
                "total_tokens": 0,
                "total_audio_seconds": 0,
                "total_audio_minutes": 0,
                "first_use": None,
                "last_use": None
            }
        
        return {
            "api_key": row[0],
            "client_name": row[1],
            "total_requests": row[2],
            "total_characters": row[3],
            "total_tokens": row[4],
            "total_audio_seconds": round(row[5], 2),
            "total_audio_minutes": round(row[5] / 60, 2),
            "first_use": row[6],
            "last_use": row[7]
        }
    
    def get_usage_history(self, api_key: str, limit: int = 100,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = """
            SELECT id, endpoint, voice_id, text_length, characters, 
                   tokens, audio_duration_seconds, model_id, 
                   language_code, timestamp
            FROM usage_log WHERE api_key = ?
        """
        params = [api_key]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "endpoint": row[1],
                "voice_id": row[2],
                "text_length": row[3],
                "characters": row[4],
                "tokens": row[5],
                "audio_duration_seconds": round(row[6], 2),
                "model_id": row[7],
                "language_code": row[8],
                "timestamp": row[9]
            }
            for row in rows
        ]
    
    def get_all_clients_usage(self) -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT api_key, client_name, total_requests, 
                   total_characters, total_tokens, 
                   total_audio_seconds, first_use, last_use
            FROM usage_summary
            ORDER BY total_requests DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "api_key": row[0],
                "client_name": row[1],
                "total_requests": row[2],
                "total_characters": row[3],
                "total_tokens": row[4],
                "total_audio_seconds": round(row[5], 2),
                "total_audio_minutes": round(row[5] / 60, 2),
                "first_use": row[6],
                "last_use": row[7]
            }
            for row in rows
        ]
    
    def get_usage_stats_by_period(self, api_key: str, period: str = "day") -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if period == "day":
            group_by = "DATE(timestamp)"
        elif period == "week":
            group_by = "strftime('%Y-%W', timestamp)"
        else:
            group_by = "strftime('%Y-%m', timestamp)"
        
        cursor.execute(f"""
            SELECT {group_by} as period,
                   COUNT(*) as requests,
                   SUM(characters) as characters,
                   SUM(tokens) as tokens,
                   SUM(audio_duration_seconds) as audio_seconds
            FROM usage_log
            WHERE api_key = ?
            GROUP BY period
            ORDER BY period DESC
            LIMIT 30
        """, (api_key,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "period": row[0],
                "requests": row[1],
                "characters": row[2],
                "tokens": row[3],
                "audio_seconds": round(row[4], 2),
                "audio_minutes": round(row[4] / 60, 2)
            }
            for row in rows
        ]

usage_tracker = UsageTracker()
