# -*- coding: utf-8 -*-
"""
Camada de persistência SQLite — Sistema de Ajustes & Ocorrências.

Responsabilidade única: ler e escrever dados no banco local (ajustes.db).
Nenhuma lógica de UI aqui — apenas operações de banco de dados.

Funções públicas:
    save_to_db(df)                    → substitui toda a tabela (upload)
    load_from_db()                    → carrega DataFrame do banco
    get_db_info()                     → metadados do último upload
    insert_registro_manual(...)       → INSERT de uma única linha
    buscar_registros_por_om(om)       → SELECT por OM normalizada
    atualizar_registro(rowid, ...)    → UPDATE por rowid
    get_oficinas_unicas()             → lista para o selectbox de oficina
    get_descricoes_unicas(limit)      → lista para o selectbox de descrição

Por que rowid e não OM como chave primária?
    A OM não é única na base — uploads antigos já trouxeram OMs repetidas.
    O rowid interno do SQLite identifica exatamente qual linha atualizar,
    mesmo quando várias linhas compartilham a mesma OM.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from utils.data_processor import classify_cause

DB_PATH = Path(__file__).parent.parent / "ajustes.db"


# --------------------------------------------------------------------------- #
# Helper interno — metadados
# --------------------------------------------------------------------------- #

def _update_meta(conn: sqlite3.Connection, record_count: int | None = None) -> None:
    """Atualiza os metadados de upload (data e contagem de registros).

    Chamado após qualquer operação que altera a tabela de ocorrências.
    Se record_count for None, consulta a tabela para obter a contagem atual
    (útil após INSERT, onde o total exato não é conhecido antes da query).
    """
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute(
        "INSERT OR REPLACE INTO meta VALUES ('upload_date', ?)",
        (datetime.now().strftime("%d/%m/%Y %H:%M"),),
    )
    if record_count is None:
        record_count = conn.execute("SELECT COUNT(*) FROM ocorrencias").fetchone()[0]
    conn.execute(
        "INSERT OR REPLACE INTO meta VALUES ('record_count', ?)",
        (str(record_count),),
    )


def save_to_db(df: pd.DataFrame) -> None:
    """Substitui toda a tabela de ocorrências e registra metadados do upload."""
    df_save = df.copy()
    df_save["DATA"] = df_save["DATA"].astype(str)
    df_save["DIA"] = df_save["DIA"].astype(str)

    with sqlite3.connect(DB_PATH) as conn:
        df_save.to_sql("ocorrencias", conn, if_exists="replace", index=False)
        _update_meta(conn, record_count=len(df))


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


# --------------------------------------------------------------------------- #
# Persistência GERFAC
# --------------------------------------------------------------------------- #

def _update_meta_gerfac(conn: sqlite3.Connection, record_count: int | None = None) -> None:
    """Atualiza os metadados de upload do GERFAC."""
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute(
        "INSERT OR REPLACE INTO meta VALUES ('upload_date_gerfac', ?)",
        (datetime.now().strftime("%d/%m/%Y %H:%M"),),
    )
    if record_count is None:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tbGerfac'")
        if cursor.fetchone():
            record_count = conn.execute("SELECT COUNT(*) FROM tbGerfac").fetchone()[0]
        else:
            record_count = 0
    conn.execute(
        "INSERT OR REPLACE INTO meta VALUES ('record_count_gerfac', ?)",
        (str(record_count),),
    )


def save_gerfac_to_db(df: pd.DataFrame) -> None:
    """Substitui toda a tabela tbGerfac e registra metadados do upload."""
    df_save = df.copy()
    if "Dt. Problema" in df_save.columns:
        df_save["Dt. Problema"] = df_save["Dt. Problema"].astype(str)
    if "Agrupador" in df_save.columns:
        df_save["Agrupador"] = df_save["Agrupador"].astype(str)
    if "Dt. Fim At." in df_save.columns:
        df_save["Dt. Fim At."] = df_save["Dt. Fim At."].astype(str)

    with sqlite3.connect(DB_PATH) as conn:
        df_save.to_sql("tbGerfac", conn, if_exists="replace", index=False)
        _update_meta_gerfac(conn, record_count=len(df))


def load_gerfac_from_db() -> pd.DataFrame | None:
    """Carrega dados da tbGerfac do SQLite. Retorna None se o banco ou a tabela não existirem."""
    if not DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Verifica se a tabela existe antes de fazer a consulta
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tbGerfac'")
            if not cursor.fetchone():
                return None
            df = pd.read_sql("SELECT * FROM tbGerfac", conn)
        
        if df.empty:
            return None
            
        if "Dt. Problema" in df.columns:
            df["Dt. Problema"] = pd.to_datetime(df["Dt. Problema"], errors="coerce")
        if "Agrupador" in df.columns:
            df["Agrupador"] = pd.to_datetime(df["Agrupador"], errors="coerce")
        return df
    except Exception:
        return None


def get_db_info_gerfac() -> dict | None:
    """Retorna metadados do último upload do GERFAC (data e quantidade)."""
    if not DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meta'")
            if not cursor.fetchone():
                return None
            rows = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        if "upload_date_gerfac" not in rows:
            return None
        return {
            "upload_date": rows.get("upload_date_gerfac", ""),
            "count": int(rows.get("record_count_gerfac", 0)),
        }
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Inserção individual de registros (formulário "Novo Registro")
# --------------------------------------------------------------------------- #
# Diferente de save_to_db (que substitui a tabela inteira a cada upload de
# planilha), as funções abaixo fazem um INSERT pontual de uma única linha,
# permitindo cadastrar uma ocorrência sem precisar reenviar a base completa.

def _garantir_tabela_ocorrencias(conn: sqlite3.Connection) -> None:
    """Cria a tabela 'ocorrencias' caso ainda não exista (primeiro uso do
    app sem nenhum upload de planilha prévio)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ocorrencias (
            OM TEXT,
            OFICINA TEXT,
            DATA TEXT,
            DESCRICAO TEXT,
            CAUSA TEXT,
            DIA TEXT
        )
        """
    )


def insert_registro_manual(om: str, oficina: str, data_valor: date, descricao: str) -> None:
    """Insere uma única ocorrência na tabela 'ocorrencias', classificando a
    causa automaticamente a partir da descrição (mesma regra usada no
    processamento da planilha) e atualiza os metadados de contagem."""
    om = str(om).strip()
    oficina = str(oficina).strip()
    descricao = str(descricao).strip()
    causa = classify_cause(descricao)
    data_str = str(data_valor)

    with sqlite3.connect(DB_PATH) as conn:
        _garantir_tabela_ocorrencias(conn)
        conn.execute(
            "INSERT INTO ocorrencias (OM, OFICINA, DATA, DESCRICAO, CAUSA, DIA) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (om, oficina, data_str, descricao, causa, data_str),
        )
        # record_count=None → _update_meta faz SELECT COUNT(*) após o INSERT
        _update_meta(conn)


def get_oficinas_unicas() -> list[str]:
    """Lista de oficinas já cadastradas na base, ordenada alfabeticamente —
    alimenta o selectbox de oficina do formulário de novo registro."""
    if not DB_PATH.exists():
        return []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT DISTINCT OFICINA FROM ocorrencias "
                "WHERE OFICINA IS NOT NULL AND TRIM(OFICINA) != '' "
                "ORDER BY OFICINA COLLATE NOCASE"
            ).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


def get_descricoes_unicas(limit: int = 60) -> list[str]:
    """Lista das descrições/OBS mais usadas na base (mais frequentes
    primeiro) — alimenta o selectbox de descrição do formulário de novo
    registro, já que o mesmo tipo de chamado costuma se repetir."""
    if not DB_PATH.exists():
        return []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT DESCRICAO, COUNT(*) AS qtd FROM ocorrencias "
                "WHERE DESCRICAO IS NOT NULL AND TRIM(DESCRICAO) != '' "
                "GROUP BY DESCRICAO ORDER BY qtd DESC, DESCRICAO COLLATE NOCASE "
                "LIMIT ?",
                (limit,),
            ).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


# --------------------------------------------------------------------------- #
# Atualização de registros (corrigir erro de cadastro)
# --------------------------------------------------------------------------- #
# A OM não é necessariamente única na base (uploads antigos já trouxeram OMs
# repetidas), então a busca usa o número da OM apenas para localizar o(s)
# candidato(s) e a atualização em si é feita pelo rowid interno do SQLite —
# assim o usuário sempre atualiza exatamente o registro que escolheu, mesmo
# quando há mais de um com a mesma OM.

def _normalizar_om(valor: str) -> str:
    """Mantém só os dígitos — protege contra espaços comuns e caracteres
    invisíveis (ex.: NBSP) que já apareceram em uploads antigos."""
    return "".join(ch for ch in str(valor) if ch.isdigit())


def buscar_registros_por_om(om: str) -> pd.DataFrame:
    """Busca todos os registros cuja OM (normalizada, ignorando espaços e
    caracteres invisíveis) corresponde exatamente à OM informada. Retorna
    um DataFrame com a coluna ROWID, necessária para identificar qual
    registro específico deve ser atualizado."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    om_busca = _normalizar_om(om)
    if not om_busca:
        return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql(
                "SELECT rowid AS ROWID, OM, OFICINA, DATA, DESCRICAO, CAUSA FROM ocorrencias",
                conn,
            )
        if df.empty:
            return df
        om_normalizado = df["OM"].astype(str).apply(_normalizar_om)
        return df[om_normalizado == om_busca].reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def atualizar_registro(rowid: int, om: str, oficina: str, data_valor: date, descricao: str) -> None:
    """Atualiza um registro existente (identificado pelo rowid do SQLite)
    com os novos valores, reclassificando a causa a partir da descrição —
    mesma regra de negócio usada na inserção e no upload da planilha."""
    om = str(om).strip()
    oficina = str(oficina).strip()
    descricao = str(descricao).strip()
    causa = classify_cause(descricao)
    data_str = str(data_valor)

    with sqlite3.connect(DB_PATH) as conn:
        _garantir_tabela_ocorrencias(conn)
        conn.execute(
            "UPDATE ocorrencias SET OM = ?, OFICINA = ?, DATA = ?, DESCRICAO = ?, "
            "CAUSA = ?, DIA = ? WHERE rowid = ?",
            (om, oficina, data_str, descricao, causa, data_str, rowid),
        )
        # UPDATE não muda a contagem — _update_meta consulta o total atual
        _update_meta(conn)
