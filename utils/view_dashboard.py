# -*- coding: utf-8 -*-
"""
Renderização do dashboard principal — Análise de Retrabalho por Oficina.

Responsabilidade única: dado um DataFrame de ocorrências (carregado do
banco pelo app.py), renderizar os controles de filtro na sidebar, aplicar
os filtros, calcular as métricas e exibir todas as seções do dashboard.

Seções do dashboard (em ordem):
    1. Header: título + cartão de período analisado
    2. KPIs: 5 cards principais (total, causa 1/2, financeiro, reincidência)
    3. Oficinas + Rosca: tabela de ranking + donut de causas
    4. Ranking + Causas: barras horizontais + colunas verticais
    5. Pareto: concentração de ocorrências por oficina
    6. Qualidade de classificação: percentual da causa "Outros"
    7. Sazonalidade: linha diária com média móvel de 3 dias
    8. Rodapé: conclusão gerencial + tabela de dados + botão de exportação

Não faz roteamento — mudanças de página (novo registro, editar, upload)
são responsabilidade de app.py, que gerencia session_state.

Dependências:
    utils.charts        → builders de opções ECharts
    utils.data_processor → DashboardMetrics, build_metrics, export_excel
    utils.style         → componentes HTML/CSS e render_echart
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.charts import build_causas, build_linha, build_pareto, build_ranking, build_rosca
from utils.data_processor import DashboardMetrics, build_metrics, export_excel
from utils.style import (
    CHART_PALETTE,
    COLORS,
    flush_html,
    kpi_card,
    render_dados_table,
    render_echart,
    render_oficinas_table,
    render_outros_descricoes_table,
)


def _md(html: str) -> None:
    st.markdown(flush_html(html), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Sidebar — filtros de período e oficina
# --------------------------------------------------------------------------- #

def _render_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona os filtros à sidebar e retorna o DataFrame filtrado.

    Usa st.sidebar como context manager — pode ser chamado DEPOIS de
    app.py já ter escrito o logo e os botões de navegação na sidebar,
    pois blocos `with st.sidebar:` são simplesmente acrescidos em ordem.
    """
    with st.sidebar:
        st.markdown("---")
        st.markdown("**🗓️ Período**")
        min_date = df["DATA"].min().date()
        max_date = df["DATA"].max().date()
        date_range = st.date_input(
            "Período analisado",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            label_visibility="collapsed",
        )

        st.markdown("**Oficinas**")
        todas_oficinas = sorted(df["OFICINA"].unique())
        oficinas_sel = st.multiselect(
            "Filtrar oficinas",
            options=todas_oficinas,
            default=[],
            placeholder="Todas as oficinas",
            label_visibility="collapsed",
        )

    df_f = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        ini, fim = date_range
        df_f = df_f[(df_f["DATA"].dt.date >= ini) & (df_f["DATA"].dt.date <= fim)]
    if oficinas_sel:
        df_f = df_f[df_f["OFICINA"].isin(oficinas_sel)]

    return df_f


# --------------------------------------------------------------------------- #
# Seção 1 — Header
# --------------------------------------------------------------------------- #

def _render_header(m: DashboardMetrics) -> None:
    h1, h2 = st.columns([3, 1.1])
    with h1:
        _md('<div class="app-title">AJUSTE NO <span>VALOR UNITÁRIO</span></div>')
        _md('<H5 class="app-title">INTEGRAÇÃO <span>GERFAC</span></H5>')
    #with h2:
    #    _md(
    #        f"""
    #        <div class="panel" style="padding: 0.7rem 1rem; margin-top:4px; margin-bottom: 0.5rem; align-items:center; display:flex; flex-direction:column; gap:0.2rem; border-radius:0.5rem;width:50%; min-width:160px; align:right;">
    #            <div class="kpi-label" style="text-align: right;">📅 Período analisado</div>
    #            <div style="color:{COLORS['text']}; font-weight:700; font-size:0.92rem;">
    #                {m.periodo_inicio} a {m.periodo_fim}
    #            </div>
    #        </div>
    #        """
    #    )


# --------------------------------------------------------------------------- #
# Seção 2 — KPIs principais
# --------------------------------------------------------------------------- #

def _render_kpis(m: DashboardMetrics) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        _md(kpi_card(
            label="Total de Ocorrências",
            value=str(m.total_ocorrencias),
            caption=f"ajustes registrados · média de {m.media_diaria}/dia",
            icon="📋",
        ))
    with c2:
        _md(kpi_card(
            label="Principal Causa",
            value=m.causa_principal,
            caption=f"{m.causa_principal_qtd} ocorrências",
            icon="🏷️",
            icon_bg="rgba(31,231,184,0.14)",
            icon_color=COLORS["aqua"],
            pill_text=f"{m.causa_principal_pct}% do total",
            pill_bg="rgba(31,231,184,0.14)",
            pill_color=COLORS["aqua"],
        ))
    with c3:
        _md(kpi_card(
            label="2ª Maior Causa",
            value=m.segunda_causa,
            caption=f"{m.segunda_causa_qtd} ocorrências",
            icon="⚖️",
            icon_bg="rgba(140,233,154,0.14)",
            icon_color=COLORS["green"],
            pill_text=f"{m.segunda_causa_pct}% do total",
            pill_bg="rgba(140,233,154,0.14)",
            pill_color=COLORS["green"],
        ))
    with c4:
        _md(kpi_card(
            label="Causas Financeiras",
            value=f"{m.pct_financeiro}%",
            caption="Descontos, Balanceamento, Valor Unitário e Reembolso",
            icon="💲",
            icon_bg="rgba(233,196,106,0.14)",
            icon_color=COLORS["amber"],
        ))
    with c5:
        _md(kpi_card(
            label="Oficinas com Reincidência",
            value=str(m.qtd_oficinas_reincidentes),
            caption=f"de {m.qtd_oficinas_total} oficinas no período",
            icon="🔁",
            icon_bg="rgba(224,102,122,0.14)",
            icon_color=COLORS["red"],
        ))


# --------------------------------------------------------------------------- #
# Seção 3 — Tabela de oficinas + rosca de causas
# --------------------------------------------------------------------------- #

def _render_oficinas_e_rosca(m: DashboardMetrics) -> None:
    _md('<div class="section-label">Principais oficinas com problema</div>')
    col_tabela, col_rosca = st.columns([1.2, 1.1])

    with col_tabela:
        _md('<div class="panel">')
        _md(render_oficinas_table(m.oficinas_resumo, top_n=8))
        _md("</div>")

    with col_rosca:
        _md('<div class="panel">')
        option, fmts = build_rosca(m.causas_resumo)
        render_echart(option, height=440, js_formatters=fmts)
        _md("</div>")


# --------------------------------------------------------------------------- #
# Seção 4 — Ranking horizontal + colunas de causas
# --------------------------------------------------------------------------- #

def _render_ranking_e_causas(m: DashboardMetrics) -> None:
    _md('<div class="section-label">Ranking de ajustes e distribuição de causas</div>')
    col_rank, col_causas = st.columns(2)

    with col_rank:
        _md('<div class="panel">')
        option, fmts = build_ranking(m.oficinas_resumo)
        render_echart(option, height=360, js_formatters=fmts)
        _md("</div>")

    with col_causas:
        _md('<div class="panel">')
        option, fmts = build_causas(m.causas_resumo)
        render_echart(option, height=360, js_formatters=fmts)
        _md(
            f"""
            <div class="insight-box">
            💡 As causas financeiras (Descontos, Balanceamento, Valor Unitário e Reembolso)
            concentram <b style="color:{COLORS['aqua']};">{m.pct_financeiro}%</b> de todas as
            ocorrências do período — oportunidade clara de revisão de processo de cadastro de
            preços e regras de fechamento.
            </div>
            """
        )
        _md("</div>")


# --------------------------------------------------------------------------- #
# Seção 5 — Pareto de oficinas
# --------------------------------------------------------------------------- #

def _render_pareto(m: DashboardMetrics) -> None:
    _md('<div class="section-label">Concentração de ocorrências — análise de Pareto</div>')
    _md('<div class="panel">')

    pareto_label = f"{m.pareto_80pct_count} oficina{'s' if m.pareto_80pct_count != 1 else ''}"
    option, fmts = build_pareto(m.pareto_oficinas)
    render_echart(option, height=400, js_formatters=fmts)

    _md(
        f"""
        <div class="insight-box">
        📊 <b style="color:{COLORS['aqua']};">{pareto_label}</b>
        ({m.pareto_80pct_pct_oficinas}% do total de {m.qtd_oficinas_total})
        respondem por <b style="color:{COLORS['amber']};">80% de todas as ocorrências</b> —
        foco de ação imediata para reduzir o volume de ajustes.
        </div>
        """
    )
    _md("</div>")


# --------------------------------------------------------------------------- #
# Seção 6 — Qualidade de classificação ("Outros")
# --------------------------------------------------------------------------- #

def _render_outros(m: DashboardMetrics) -> None:
    """Exibe o KPI de cobertura das CAUSE_RULES e orienta a ação corretiva.

    Thresholds de alerta:
        >= 20%  → vermelho  (CAUSE_RULES precisa de revisão urgente)
        >= 10%  → âmbar    (monitorar, avaliar novas palavras-chave)
        <  10%  → aqua     (classificação sob controle)
    """
    _md('<div class="section-label">Qualidade da classificação de causas</div>')

    if m.outros_pct >= 20:
        icon_bg    = "rgba(224,102,122,0.14)"
        icon_color = COLORS["red"]
        pill_bg    = "rgba(224,102,122,0.14)"
        pill_color = COLORS["red"]
        pill       = "⚠ Requer atenção"
        border     = COLORS["red"]
        status     = (
            "acima de 20% — alto! Muitas ocorrências sem categoria indicam que "
            "<b>CAUSE_RULES</b> precisa de revisão urgente."
        )
    elif m.outros_pct >= 10:
        icon_bg    = "rgba(233,196,106,0.14)"
        icon_color = COLORS["amber"]
        pill_bg    = "rgba(233,196,106,0.14)"
        pill_color = COLORS["amber"]
        pill       = "△ Monitorar"
        border     = COLORS["amber"]
        status     = (
            "entre 10% e 20% — monitorar; avalie se novas palavras-chave "
            "são necessárias em <b>CAUSE_RULES</b>."
        )
    else:
        icon_bg    = "rgba(31,231,184,0.12)"
        icon_color = COLORS["aqua"]
        pill_bg    = "rgba(31,231,184,0.14)"
        pill_color = COLORS["aqua"]
        pill       = "✓ Sob controle"
        border     = COLORS["aqua"]
        status     = "abaixo de 10% — as regras de classificação cobrem bem as ocorrências."

    col_kpi, col_info = st.columns([1, 2.5])
    with col_kpi:
        _md(kpi_card(
            label='Ocorrências "Outros"',
            value=f"{m.outros_pct}%",
            caption=f"{m.outros_qtd} de {m.total_ocorrencias} registros sem categoria",
            icon="🔎",
            icon_bg=icon_bg,
            icon_color=icon_color,
            pill_text=pill,
            pill_bg=pill_bg,
            pill_color=pill_color,
        ))
    with col_info:
        _md(
            f"""
            <div class="panel">
            <div class="panel-title">🔎 O que é a causa "Outros"?</div>
            <div style="color:{COLORS['text_dim']}; font-size:0.86rem; line-height:1.6;">
            Toda ocorrência que não corresponde a nenhuma palavra-chave em
            <b style="color:{COLORS['text']};">CAUSE_RULES</b> (data_processor.py)
            recebe automaticamente a causa <b style="color:{COLORS['text']};">Outros</b>.
            Um percentual alto indica que muitas ocorrências ficaram sem categoria definida.
            </div>
            <div class="insight-box" style="margin-top:0.7rem; border-left-color:{border};">
            O percentual atual de <b style="color:{border};">{m.outros_pct}%</b> está {status}
            </div>
            </div>
            """
        )

    if not m.outros_top_descricoes.empty:
        with st.expander(
            "📋 Descrições mais frequentes dentro de 'Outros' (candidatas a novas regras)"
        ):
            _md(render_outros_descricoes_table(m.outros_top_descricoes))


# --------------------------------------------------------------------------- #
# Seção 7 — Sazonalidade diária
# --------------------------------------------------------------------------- #

def _render_sazonalidade(m: DashboardMetrics) -> None:
    _md('<div class="section-label">Sazonalidade — tendência diária</div>')
    _md('<div class="panel">')

    option, fmts = build_linha(m.serie_diaria)
    render_echart(option, height=360, js_formatters=fmts)

    pico = m.serie_diaria.loc[m.serie_diaria["QTD"].idxmax()]
    _md(
        f"""
        <div class="insight-box">
        📌 Pico de <b style="color:{COLORS['aqua']};">{int(pico['QTD'])} ocorrências</b> em
        <b>{pd.to_datetime(pico['DIA']).strftime('%d/%m/%Y')}</b>. A linha pontilhada mostra a
        tendência (média móvel de 3 dias) para identificar se o retrabalho está em alta ou queda.
        </div>
        """
    )
    _md("</div>")


# --------------------------------------------------------------------------- #
# Seção 8 — Rodapé: conclusão gerencial + tabela + exportação
# --------------------------------------------------------------------------- #

def _render_rodape(m: DashboardMetrics, df_filtrado: pd.DataFrame) -> None:
    top3 = m.causas_resumo.head(3)
    top3_pct = round(top3["PERCENTUAL"].sum(), 0)
    top3_nomes = ", ".join(top3["CAUSA"].tolist())

    _md(
        f"""
        <div class="panel" style="margin-top:1.4rem; display:flex; align-items:center; gap:18px;">
            <div style="font-size:1.8rem;">🏆</div>
            <div>
                <div style="font-weight:800; color:{COLORS['text']}; font-size:0.95rem;
                            text-transform:uppercase; letter-spacing:0.04em;">
                    Conclusão Gerencial
                </div>
                <div style="color:{COLORS['text_dim']}; font-size:0.86rem; margin-top:4px;">
                    Os retrabalhos estão concentrados em poucos tipos de erro:
                    <b style="color:{COLORS['aqua']};">{top3_nomes}</b>
                    respondem por aproximadamente
                    <b style="color:{COLORS['aqua']};">{top3_pct:.0f}%</b> das ocorrências do período.
                    Atuar sobre essas causas e sobre as
                    <b>{m.qtd_oficinas_reincidentes} oficinas reincidentes</b> pode reduzir
                    significativamente o volume de ajustes futuros.
                </div>
            </div>
        </div>
        """
    )

    causa_color_map = {
        causa: CHART_PALETTE[i % len(CHART_PALETTE)]
        for i, causa in enumerate(m.causas_resumo["CAUSA"])
    }

    with st.expander("🔍 Ver dados tratados (base completa após classificação)"):
        _md(render_dados_table(
            df_filtrado[["OM", "OFICINA", "DATA", "CAUSA", "DESCRICAO"]].sort_values(
                "DATA", ascending=False
            ),
            causa_colors=causa_color_map,
        ))

    xlsx_bytes = export_excel(df_filtrado, m.periodo_inicio, m.periodo_fim)
    nome_arquivo = (
        f"ajustes_ocorrencias_"
        f"{m.periodo_inicio.replace('/', '-')}_a_{m.periodo_fim.replace('/', '-')}.xlsx"
    )
    st.download_button(
        label="⬇️ Exportar planilha executiva (.xlsx)",
        data=xlsx_bytes,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Gera uma planilha Excel com layout executivo contendo todos os registros filtrados.",
    )


# --------------------------------------------------------------------------- #
# Ponto de entrada público
# --------------------------------------------------------------------------- #

def render_dashboard(df: pd.DataFrame) -> None:
    """Renderiza o dashboard completo: filtros, métricas e todas as seções.

    Parâmetros
    ----------
    df : DataFrame completo carregado do banco (sem filtros aplicados).
        Colunas obrigatórias: OM, OFICINA, DATA, DESCRICAO, CAUSA, DIA.

    O DataFrame filtrado e as métricas são computados internamente —
    quem chama não precisa saber nada sobre filtros ou cálculos.
    """
    df_f = _render_filtros(df)

    if df_f.empty:
        st.warning("Nenhuma ocorrência encontrada para os filtros selecionados.")
        return

    m = build_metrics(df_f)

    _render_header(m)
    _render_kpis(m)
    _render_oficinas_e_rosca(m)
    _render_ranking_e_causas(m)
    _render_pareto(m)
    _render_outros(m)
    _render_sazonalidade(m)
    _render_rodape(m, df_f)
