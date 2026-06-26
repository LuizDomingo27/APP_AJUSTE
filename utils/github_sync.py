# -*- coding: utf-8 -*-
"""
Sincronização do banco SQLite com o repositório GitHub.

Após cada upload, o arquivo ajustes.db é commitado via API do GitHub para
garantir persistência no Streamlit Cloud (onde o filesystem é efêmero).

Configuração necessária em Settings > Secrets no Streamlit Cloud:
    GITHUB_TOKEN = "ghp_seu_personal_access_token"
    GITHUB_REPO  = "seu-usuario/nome-do-repositorio"

O token precisa da permissão: Contents (read and write).
"""
from __future__ import annotations

import base64
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ajustes.db"
DB_REPO_PATH = "ajustes.db"


def sync_to_github() -> bool:
    """
    Commita o arquivo ajustes.db local de volta ao repositório GitHub.
    Retorna True em caso de sucesso, False se não configurado ou em erro.
    """
    try:
        import requests
        import streamlit as st

        token = st.secrets.get("GITHUB_TOKEN", "")
        repo = st.secrets.get("GITHUB_REPO", "")
        if not token or not repo:
            return False

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = f"https://api.github.com/repos/{repo}/contents/{DB_REPO_PATH}"

        # Obtém o SHA atual do arquivo no repo (necessário para atualizar)
        resp = requests.get(url, headers=headers, timeout=10)
        sha = resp.json().get("sha") if resp.status_code == 200 else None

        with open(DB_PATH, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        payload: dict = {
            "message": "chore: atualiza banco de dados via upload",
            "content": content,
        }
        if sha:
            payload["sha"] = sha

        put = requests.put(url, headers=headers, json=payload, timeout=30)
        return put.status_code in (200, 201)
    except Exception:
        return False
