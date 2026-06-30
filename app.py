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

from utils.database import get_db_info, load_from_db
from utils.registro_manual import render_pagina_editar_registro, render_pagina_novo_registro
from utils.style import COLORS, flush_html, inject_global_css
from utils.view_dashboard import render_dashboard
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

if "show_upload" not in st.session_state:
    # Abre a tela de upload automaticamente se o banco ainda não existe.
    st.session_state.show_upload = get_db_info() is None
if "show_novo_registro" not in st.session_state:
    st.session_state.show_novo_registro = False
if "show_editar_registro" not in st.session_state:
    st.session_state.show_editar_registro = False

# --------------------------------------------------------------------------- #
# Sidebar — logo (exibido em todas as rotas)
# --------------------------------------------------------------------------- #

#_SIDEBAR_LOGO = f"""
#<div style="display:flex; align-items:center; gap:10px; margin-bottom:1.4rem;">
#    <div style="width:36px; height:36px; border-radius:10px;
#                background:rgba(31,231,184,0.12); display:flex;
#                align-items:center; justify-content:center; font-size:1.1rem;">📊</div>
#    <div>
#        <div style="font-weight:800; color:{COLORS['text']}; font-size:0.95rem;">AJUSTES &amp;</div>
#        <div style="font-weight:800; color:{COLORS['aqua']}; font-size:0.95rem;">OCORRÊNCIAS</div>
#    </div>
#</div>
#"""
#
# --------------------------------------------------------------------------- #
# Rota: tela de upload
# --------------------------------------------------------------------------- #

if st.session_state.show_upload:
    with st.sidebar:
        #_md(_SIDEBAR_LOGO)
        if get_db_info() is not None:
            if st.button("← Voltar ao dashboard", use_container_width=True):
                st.session_state.show_upload = False
                st.rerun()

    if render_pagina_upload():
        st.session_state.show_upload = False
        st.rerun()

    st.stop()

# --------------------------------------------------------------------------- #
# Guarda de segurança — banco vazio redireciona para upload
# --------------------------------------------------------------------------- #

df = load_from_db()
if df is None or df.empty:
    st.session_state.show_upload = True
    st.rerun()

# --------------------------------------------------------------------------- #
# Rota: formulário de novo registro
# --------------------------------------------------------------------------- #

if st.session_state.show_novo_registro:
    with st.sidebar:
        #_md(_SIDEBAR_LOGO)
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
        #_md(_SIDEBAR_LOGO)
        if st.button("← Voltar ao dashboard", use_container_width=True):
            st.session_state.show_editar_registro = False
            st.rerun()
    render_pagina_editar_registro()
    st.stop()

# --------------------------------------------------------------------------- #
# Rota: dashboard principal (padrão)
# --------------------------------------------------------------------------- #

with st.sidebar:
    #_md(_SIDEBAR_LOGO)
    if st.button("➕  Novo registro", use_container_width=True, type="primary"):
        st.session_state.show_novo_registro = True
        st.rerun()
    if st.button("✏️  Atualizar registro", use_container_width=True):
        st.session_state.show_editar_registro = True
        st.rerun()
    if st.button("🔄  Atualizar dados", use_container_width=True):
        st.session_state.show_upload = True
        st.rerun()

render_dashboard(df)
