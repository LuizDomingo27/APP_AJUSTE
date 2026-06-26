# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent.parent / "ajustes.db"


def save_to_db(df: pd.DataFrame) -> None:
    """Substitui toda a tabela de ocorrências e registra metadados do upload."""
    df_save = df.copy()
    df_save["DATA"] = df_save["DATA"].astype(str)
    df_save["DIA"] = df_save["DIA"].astype(str)

    with sqlite3.connect(DB_PATH) as conn:
        df_save.to_sql("ocorrencias", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('upload_date', ?)",
            (datetime.now().strftime("%d/%m/%Y %H:%M"),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta VALUES ('record_count', ?)",
            (str(len(df)),),
        )


def load_from_db() -> pd.DataFrame | None:
    """Carrega ocorrências do SQLite. Retorna None se o banco não existir."""
    if not DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql("SELECT * FROM ocorrencias", conn)
        df["DATA"] = pd.to_datetime(df["DATA"])
        df["DIA"] = pd.to_datetime(df["DIA"]).dt.date
        return df if not df.empty else None
    except Exception:
        return None


def get_db_info() -> dict | None:
    """Retorna metadados do último upload (data e quantidade de registros)."""
    if not DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        return {
            "upload_date": rows.get("upload_date", ""),
            "count": int(rows.get("record_count", 0)),
        }
    except Exception:
        return None
