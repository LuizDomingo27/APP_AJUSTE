# -*- coding: utf-8 -*-
"""
Página de upload de planilha — tela inicial do app quando não há dados no
banco ou quando o usuário clica em "Atualizar dados".

Responsabilidade única: coletar o arquivo enviado pelo usuário, processá-lo
e persistir no banco. Não controla session_state nem chama st.rerun() —
isso é responsabilidade de app.py, que age sobre o valor de retorno.

Fluxo interno:
    1. Exibe o formulário de upload (file_uploader).
    2. Ao receber um arquivo, chama load_dataframe → process_data.
    3. Persiste via save_to_db e sincroniza com GitHub via sync_to_github.
    4. Retorna True → app.py redireciona para o dashboard.
    5. Em caso de erro no processamento, exibe mensagem e retorna False.
"""

from __future__ import annotations

import streamlit as st

from utils.data_processor import load_dataframe, process_data
from utils.database import save_to_db
from utils.github_sync import sync_to_github
from utils.style import flush_html


def _md(html: str) -> None:
    st.markdown(flush_html(html), unsafe_allow_html=True)


def render_pagina_upload() -> bool:
    """Renderiza a tela de upload e processa o arquivo enviado.

    Retorna True quando o arquivo foi processado e salvo com sucesso,
    sinalizando a app.py que deve redirecionar para o dashboard.
    Retorna False enquanto aguarda envio ou quando ocorre erro de leitura.
    """
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        _md(
            """
            <div style="text-align:center; margin:3rem 0 2rem;">
                <div class="app-title" style="justify-content:center;">
                    AJUSTES <span>&amp; OCORRÊNCIAS</span>
                </div>
                <div class="app-subtitle">Envie a planilha para carregar o dashboard</div>
            </div>
            """
        )
        _md('<div class="panel" style="padding:2rem 2rem 1.5rem;">')
        _md('<div style="text-align:center; font-size:2.5rem; margin-bottom:0.5rem;">📂</div>')
        _md(
            '<div class="panel-title" style="text-align:center; margin-bottom:1.2rem;">'
            "Planilha de ocorrências</div>"
        )

        uploaded_file = st.file_uploader(
            "Envie o arquivo (.xlsx, .xls ou .csv)",
            type=["xlsx", "xls", "csv"],
            label_visibility="collapsed",
        )
        st.caption(
            "Colunas esperadas: **OM**, **OFICINA**, **DATA** e **DESCRIÇÃO/OBS**. "
            "O app reconhece variações comuns de cabeçalho automaticamente."
        )
        _md("</div>")

    if uploaded_file is not None:
        try:
            with st.spinner("Processando planilha..."):
                raw_df = load_dataframe(uploaded_file)
                df_processado = process_data(raw_df)
        except Exception as e:
            st.error(f"⚠️ Não foi possível processar a planilha enviada: {e}")
            return False

        save_to_db(df_processado)
        with st.spinner("Sincronizando..."):
            sync_to_github()
        st.toast("Dados carregados com sucesso!", icon="✅")
        return True

    return False
