# -*- coding: utf-8 -*-
"""
Módulo de inserção/atualização manual de registros — "Novo Registro" e
"Atualizar Registro".

Hoje, para adicionar ou corrigir uma única ocorrência, era preciso reenviar
a planilha inteira (todos os registros do dia). Este módulo resolve isso
com dois formulários:

- Novo Registro: cadastra uma ocorrência por vez.
- Atualizar Registro: localiza um registro existente pela OM e corrige
  os dados (erro de cadastro), mantendo as mesmas regras de validação.

Em ambos os casos:
- OM: campo numérico, já vem pré-preenchido com "300" (toda ordem começa
  com esse prefixo).
- Oficina: combobox com as oficinas já existentes na base; se o nome
  digitado for novo, é cadastrado e passa a aparecer no combobox nas
  próximas inserções/edições.
- Data: calendário.
- Descrição/OBS: mesmo recurso de combobox da oficina, já que o mesmo
  tipo de chamado/observação costuma se repetir.

Mantém o mesmo padrão visual do restante do app (utils/style.py).
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.database import (
    atualizar_registro,
    buscar_registros_por_om,
    get_descricoes_unicas,
    get_oficinas_unicas,
    insert_registro_manual,
)
from utils.github_sync import sync_to_github
from utils.style import COLORS, flush_html

_NOVA_OFICINA = "➕ Cadastrar nova oficina..."
_NOVA_DESCRICAO = "➕ Escrever nova descrição/OBS..."


def _md(html: str) -> None:
    st.markdown(flush_html(html), unsafe_allow_html=True)


def _validar_om(valor: str) -> tuple[bool, str]:
    """Valida o campo OM: apenas dígitos, sempre iniciando em 300."""
    valor = (valor or "").strip()
    if not valor:
        return False, "Informe o número da OM."
    if not valor.isdigit():
        return False, "A OM deve conter apenas números."
    if not valor.startswith("300"):
        return False, "Toda OM deve começar com 300 (ex.: 300213456)."
    if len(valor) < 4:
        return False, "Número da OM incompleto."
    return True, ""


def _opcoes_combobox(
    valor_atual: str | None, opcoes_existentes: list[str], label_novo: str
) -> tuple[list[str], int | None]:
    """Monta a lista de opções de um combobox (oficina ou descrição)
    garantindo que o valor atual do registro — quando houver — sempre
    apareça na lista e já venha pré-selecionado."""
    opcoes = [label_novo] + list(opcoes_existentes)
    if valor_atual:
        if valor_atual not in opcoes_existentes:
            opcoes.insert(1, valor_atual)
        return opcoes, opcoes.index(valor_atual)
    return opcoes, None


def _renderizar_erros(erros: list[str]) -> None:
    _md(
        f"""
        <div class="insight-box" style="border-left-color:{COLORS['red']}; margin-top:0.9rem;">
        ⚠️ <b style="color:{COLORS['red']};">Corrija antes de salvar:</b><br>
        {'<br>'.join(f'• {e}' for e in erros)}
        </div>
        """
    )


def _validar_formulario(
    om_valor: str,
    oficina_escolhida: str | None,
    oficina_nova_valor: str,
    data_valor,
    descricao_escolhida: str | None,
    descricao_nova_valor: str,
) -> tuple[list[str], str, str]:
    """Aplica as mesmas regras de validação usadas no cadastro e na
    edição. Retorna (lista_de_erros, oficina_final, descricao_final)."""
    erros: list[str] = []

    om_ok, om_msg = _validar_om(om_valor)
    if not om_ok:
        erros.append(om_msg)

    oficina_final = (
        oficina_nova_valor.strip()
        if oficina_escolhida == _NOVA_OFICINA
        else (oficina_escolhida or "").strip()
    )
    if not oficina_final:
        erros.append("Informe ou selecione a oficina.")

    descricao_final = (
        descricao_nova_valor.strip()
        if descricao_escolhida == _NOVA_DESCRICAO
        else (descricao_escolhida or "").strip()
    )
    if not descricao_final:
        erros.append("Informe ou selecione a descrição/OBS.")

    if not data_valor:
        erros.append("Informe a data da ocorrência.")

    return erros, oficina_final, descricao_final


# --------------------------------------------------------------------------- #
# Novo registro
# --------------------------------------------------------------------------- #

def render_pagina_novo_registro() -> None:
    """Renderiza a página completa do formulário de novo registro."""

    _md(
        """
        <div class="page-hero">
            <div class="page-hero-icon">📝</div>
            <div class="page-hero-title">NOVO <span>REGISTRO</span></div>
            <div class="page-hero-subtitle">
                Cadastre uma ocorrência sem precisar reenviar a planilha completa
            </div>
        </div>
        """
    )

    oficinas_existentes = get_oficinas_unicas()
    descricoes_existentes = get_descricoes_unicas()

    _, col, _ = st.columns([0.3, 1.4, 0.3])
    with col:
        with st.form("form_novo_registro", clear_on_submit=False):

            _md('<div class="form-section-label">Identificação</div>')
            c_om, c_data = st.columns([2, 1])
            with c_om:
                om_valor = st.text_input(
                    "Nº da OM",
                    value="300",
                    help="Apenas números. Toda OM começa com 300 (ex.: 300213456).",
                )
            with c_data:
                data_valor = st.date_input(
                    "Data",
                    value=date.today(),
                    format="DD/MM/YYYY",
                )

            _md('<div class="form-section-label">Localização</div>')
            opcoes_oficina, idx_oficina = _opcoes_combobox(None, oficinas_existentes, _NOVA_OFICINA)
            oficina_escolhida = st.selectbox(
                "Oficina",
                options=opcoes_oficina,
                index=idx_oficina,
                placeholder="Selecione uma oficina já cadastrada...",
            )
            oficina_nova_valor = ""
            if oficina_escolhida == _NOVA_OFICINA:
                oficina_nova_valor = st.text_input("Nome da nova oficina")

            _md('<div class="form-section-label">Descrição da Ocorrência</div>')
            opcoes_descricao, idx_descricao = _opcoes_combobox(
                None, descricoes_existentes, _NOVA_DESCRICAO
            )
            descricao_escolhida = st.selectbox(
                "Descrição / OBS",
                options=opcoes_descricao,
                index=idx_descricao,
                placeholder="Selecione um motivo já usado anteriormente...",
                help="Tipos de chamado/observação repetidos podem ser reaproveitados aqui.",
            )
            descricao_nova_valor = ""
            if descricao_escolhida == _NOVA_DESCRICAO:
                descricao_nova_valor = st.text_area(
                    "Nova descrição / observação", height=90
                )

            _md('<div class="form-submit-spacer"></div>')
            enviado = st.form_submit_button(
                "💾  Salvar registro",
                use_container_width=True,
                type="primary",
            )

        if enviado:
            erros, oficina_final, descricao_final = _validar_formulario(
                om_valor,
                oficina_escolhida,
                oficina_nova_valor,
                data_valor,
                descricao_escolhida,
                descricao_nova_valor,
            )
            if erros:
                _renderizar_erros(erros)
                return

            insert_registro_manual(
                om=om_valor.strip(),
                oficina=oficina_final,
                data_valor=data_valor,
                descricao=descricao_final,
            )
            with st.spinner("Sincronizando..."):
                sync_to_github()

            st.toast("Registro salvo com sucesso!", icon="✅")
            _md(
                f"""
                <div class="insight-box" style="margin-top:0.9rem;">
                ✅ Ocorrência da OM <b style="color:{COLORS['aqua']};">{om_valor.strip()}</b>
                salva para a oficina <b style="color:{COLORS['aqua']};">{oficina_final}</b>.
                </div>
                """
            )


# --------------------------------------------------------------------------- #
# Atualizar registro (corrigir erro de cadastro)
# --------------------------------------------------------------------------- #

def render_pagina_editar_registro() -> None:
    """Renderiza a página de busca + edição de um registro existente,
    para corrigir erros de cadastro sem precisar reenviar a planilha."""

    if "er_resultados" not in st.session_state:
        st.session_state.er_resultados = None
    if "er_rowid_sel" not in st.session_state:
        st.session_state.er_rowid_sel = None

    _md(
        """
        <div class="page-hero">
            <div class="page-hero-icon">✏️</div>
            <div class="page-hero-title">ATUALIZAR <span>REGISTRO</span></div>
            <div class="page-hero-subtitle">
                Localize pela OM e corrija um registro com erro de cadastro
            </div>
        </div>
        """
    )

    _, col, _ = st.columns([0.3, 1.4, 0.3])
    with col:

        # ---- Busca pela OM (em formulário para aceitar Enter) -------------- #
        with st.form("form_busca_om", clear_on_submit=False):
            _md('<div class="form-section-label">Localizar Registro</div>')
            c_busca, c_botao = st.columns([3, 1])
            with c_busca:
                om_busca = st.text_input(
                    "OM",
                    key="er_om_busca",
                    placeholder="Digite a OM (ex.: 300213456)",
                    label_visibility="collapsed",
                )
            with c_botao:
                buscar_clicado = st.form_submit_button(
                    "🔎  Buscar",
                    use_container_width=True,
                    type="primary",
                )

        if buscar_clicado:
            om_limpo = (om_busca or "").strip()
            if not om_limpo:
                st.warning("Informe o número da OM para buscar.")
                st.session_state.er_resultados = None
                st.session_state.er_rowid_sel = None
            else:
                resultados = buscar_registros_por_om(om_limpo)
                st.session_state.er_resultados = resultados
                st.session_state.er_rowid_sel = None
                if resultados.empty:
                    st.warning(f"Nenhum registro encontrado para a OM '{om_limpo}'.")

        resultados = st.session_state.er_resultados

        if resultados is not None and not resultados.empty:
            # ---- Desambiguação, caso existam várias linhas com a mesma OM -- #
            if len(resultados) > 1 and st.session_state.er_rowid_sel is None:
                _md(
                    f"""
                    <div class="insight-box" style="margin-top:0.9rem;">
                    ⚠️ Foram encontrados <b style="color:{COLORS['aqua']};">{len(resultados)}</b>
                    registros com essa OM. Selecione qual deseja atualizar:
                    </div>
                    """
                )
                opcoes_rows = {}
                for _, row in resultados.iterrows():
                    data_fmt = pd.to_datetime(row["DATA"]).strftime("%d/%m/%Y")
                    rotulo = f"{row['OFICINA']} — {data_fmt} — {str(row['DESCRICAO'])[:50]}"
                    opcoes_rows[rotulo] = int(row["ROWID"])
                escolha_label = st.selectbox(
                    "Registro encontrado", options=list(opcoes_rows.keys())
                )
                st.session_state.er_rowid_sel = opcoes_rows[escolha_label]
            elif st.session_state.er_rowid_sel is None:
                st.session_state.er_rowid_sel = int(resultados.iloc[0]["ROWID"])

        rowid_sel = st.session_state.er_rowid_sel

        if rowid_sel is not None and resultados is not None and not resultados.empty:
            linha = resultados[resultados["ROWID"] == rowid_sel]
            if linha.empty:
                st.session_state.er_rowid_sel = None
                return
            registro = linha.iloc[0]

            oficinas_existentes = get_oficinas_unicas()
            descricoes_existentes = get_descricoes_unicas()

            _md('<div style="margin-top:1rem;"></div>')

            with st.form("form_editar_registro", clear_on_submit=False):

                _md('<div class="form-section-label">Identificação</div>')
                c_om, c_data = st.columns([2, 1])
                with c_om:
                    om_valor = st.text_input(
                        "Nº da OM",
                        value=str(registro["OM"]).strip(),
                        help="Apenas números. Toda OM começa com 300 (ex.: 300213456).",
                    )
                with c_data:
                    data_atual = pd.to_datetime(registro["DATA"]).date()
                    data_valor = st.date_input(
                        "Data", value=data_atual, format="DD/MM/YYYY"
                    )

                _md('<div class="form-section-label">Localização</div>')
                oficina_atual = str(registro["OFICINA"]).strip()
                opcoes_oficina, idx_oficina = _opcoes_combobox(
                    oficina_atual, oficinas_existentes, _NOVA_OFICINA
                )
                oficina_escolhida = st.selectbox(
                    "Oficina", options=opcoes_oficina, index=idx_oficina
                )
                oficina_nova_valor = ""
                if oficina_escolhida == _NOVA_OFICINA:
                    oficina_nova_valor = st.text_input("Nome da nova oficina")

                _md('<div class="form-section-label">Descrição da Ocorrência</div>')
                descricao_atual = str(registro["DESCRICAO"]).strip()
                opcoes_descricao, idx_descricao = _opcoes_combobox(
                    descricao_atual, descricoes_existentes, _NOVA_DESCRICAO
                )
                descricao_escolhida = st.selectbox(
                    "Descrição / OBS", options=opcoes_descricao, index=idx_descricao
                )
                descricao_nova_valor = ""
                if descricao_escolhida == _NOVA_DESCRICAO:
                    descricao_nova_valor = st.text_area(
                        "Nova descrição / observação", height=90
                    )

                _md('<div class="form-submit-spacer"></div>')
                col_salvar, col_cancelar = st.columns([3, 2])
                with col_salvar:
                    salvar = st.form_submit_button(
                        "💾  Salvar alterações",
                        use_container_width=True,
                        type="primary",
                    )
                with col_cancelar:
                    cancelar = st.form_submit_button(
                        "✖  Buscar outra OM",
                        use_container_width=True,
                    )

            if cancelar:
                st.session_state.er_resultados = None
                st.session_state.er_rowid_sel = None
                st.rerun()

            if salvar:
                erros, oficina_final, descricao_final = _validar_formulario(
                    om_valor,
                    oficina_escolhida,
                    oficina_nova_valor,
                    data_valor,
                    descricao_escolhida,
                    descricao_nova_valor,
                )
                if erros:
                    _renderizar_erros(erros)
                    return

                atualizar_registro(
                    rowid=rowid_sel,
                    om=om_valor.strip(),
                    oficina=oficina_final,
                    data_valor=data_valor,
                    descricao=descricao_final,
                )
                with st.spinner("Sincronizando..."):
                    sync_to_github()

                st.toast("Registro atualizado com sucesso!", icon="✅")
                _md(
                    f"""
                    <div class="insight-box" style="margin-top:0.9rem;">
                    ✅ Registro da OM <b style="color:{COLORS['aqua']};">{om_valor.strip()}</b>
                    atualizado para a oficina <b style="color:{COLORS['aqua']};">{oficina_final}</b>.
                    </div>
                    """
                )
                st.session_state.er_resultados = None
                st.session_state.er_rowid_sel = None
