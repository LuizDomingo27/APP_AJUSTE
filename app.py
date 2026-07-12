# -*- coding: utf-8 -*-
"""
Sistema de Ajustes & Ocorrências — ponto de entrada da aplicação.

Responsabilidade única: configurar a página, inicializar session_state
e rotear para a view correta de acordo com o estado da navegação.

Rotas disponíveis (controladas por session_state):
    show_upload=True          → view_upload.render_pagina_upload()
    show_novo_registro=True   → registro_manual.render_pagina_novo_registro()
    show_editar_registro=True → registro_manual.render_pagina_editar_registro()
    (padrão)                  → view_dashboard.render_dashboard(df)

Toda lógica de negócio, persistência e renderização de UI está isolada
nos módulos de utils/ — este arquivo não contém nenhuma dessas
responsabilidades.

Para adicionar uma nova página:
    1. Crie utils/view_nova_pagina.py com render_nova_pagina().
    2. Adicione uma chave em session_state aqui.
    3. Acrescente o botão na sidebar e o bloco de rota abaixo.
"""

import streamlit as st

from utils.database import get_db_info, load_from_db, get_db_info_gerfac, load_gerfac_from_db
from utils.registro_manual import render_pagina_editar_registro, render_pagina_novo_registro
from utils.style import COLORS, flush_html, inject_global_css
from utils.view_dashboard import render_dashboard
from utils.view_dashboard_gerfac import render_dashboard_gerfac
from utils.view_upload import render_pagina_upload

st.set_page_config(
    page_title="Ajustes & Ocorrências",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()


def _md(html: str) -> None:
    st.markdown(flush_html(html), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Session state — inicialização única na primeira execução
# --------------------------------------------------------------------------- #

if "analise_ativa" not in st.session_state:
    st.session_state.analise_ativa = "retrabalho"

if "show_upload" not in st.session_state:
    # Abre a tela de upload automaticamente se o banco ainda não existe.
    if st.session_state.analise_ativa == "gerfac":
        st.session_state.show_upload = get_db_info_gerfac() is None
    else:
        st.session_state.show_upload = get_db_info() is None

if "show_novo_registro" not in st.session_state:
    st.session_state.show_novo_registro = False
if "show_editar_registro" not in st.session_state:
    st.session_state.show_editar_registro = False


# --------------------------------------------------------------------------- #
# Sidebar — Seletor de Análise (topo)
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.markdown("**Selecione a Análise**")
    analise_opcoes = {
        "retrabalho": "Análise de Retrabalho",
        "gerfac": "Análise GERFAC"
    }
    
    nova_analise = st.radio(
        "Selecione a Análise",
        options=list(analise_opcoes.keys()),
        format_func=lambda x: analise_opcoes[x],
        label_visibility="collapsed",
        key="analise_ativa_radio"
    )
    
    if nova_analise != st.session_state.analise_ativa:
        st.session_state.analise_ativa = nova_analise
        # Reseta os estados de página ao alternar análises
        st.session_state.show_upload = False
        st.session_state.show_novo_registro = False
        st.session_state.show_editar_registro = False
        st.rerun()

# --------------------------------------------------------------------------- #
# Rota: tela de upload
# --------------------------------------------------------------------------- #

if st.session_state.show_upload:
    with st.sidebar:
        db_info_check = get_db_info_gerfac() if st.session_state.analise_ativa == "gerfac" else get_db_info()
        if db_info_check is not None:
            if st.button("← Voltar ao dashboard", use_container_width=True):
                st.session_state.show_upload = False
                st.rerun()

    if render_pagina_upload(st.session_state.analise_ativa):
        st.session_state.show_upload = False
        st.rerun()

    st.stop()

# --------------------------------------------------------------------------- #
# Guarda de segurança — banco vazio redireciona para upload
# --------------------------------------------------------------------------- #

if st.session_state.analise_ativa == "gerfac":
    df = load_gerfac_from_db()
else:
    df = load_from_db()

if df is None or df.empty:
    st.session_state.show_upload = True
    st.rerun()

# --------------------------------------------------------------------------- #
# Rota: formulário de novo registro
# --------------------------------------------------------------------------- #

if st.session_state.show_novo_registro:
    with st.sidebar:
        if st.button("← Voltar ao dashboard", use_container_width=True):
            st.session_state.show_novo_registro = False
            st.rerun()
    render_pagina_novo_registro()
    st.stop()

# --------------------------------------------------------------------------- #
# Rota: formulário de edição de registro
# --------------------------------------------------------------------------- #

if st.session_state.show_editar_registro:
    with st.sidebar:
        if st.button("← Voltar ao dashboard", use_container_width=True):
            st.session_state.show_editar_registro = False
            st.rerun()
    render_pagina_editar_registro()
    st.stop()

# --------------------------------------------------------------------------- #
# Rota: dashboard principal (padrão)
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.markdown("---")
    if st.session_state.analise_ativa == "gerfac":
        if st.button("Atualizar dados", use_container_width=True):
            st.session_state.show_upload = True
            st.rerun()
    else:
        if st.button("➕  Novo registro", use_container_width=True, type="primary"):
            st.session_state.show_novo_registro = True
            st.rerun()
        if st.button("✏️  Atualizar registro", use_container_width=True):
            st.session_state.show_editar_registro = True
            st.rerun()
        if st.button("🔄  Atualizar dados", use_container_width=True):
            st.session_state.show_upload = True
            st.rerun()

if st.session_state.analise_ativa == "gerfac":
    render_dashboard_gerfac(df)
else:
    render_dashboard(df)
