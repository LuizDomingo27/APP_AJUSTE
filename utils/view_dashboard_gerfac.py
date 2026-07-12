# -*- coding: utf-8 -*-
"""
Renderização do dashboard GERFAC — Análise de chamados e setores.

Responsabilidade única: dado um DataFrame da tbGerfac, renderizar os filtros na sidebar,
calcular métricas e exibir o dashboard corporativo (sem emojis, padrão premium).
"""

from __future__ import annotations

import html
import pandas as pd
import streamlit as st

from utils.charts import build_gerfac_setores, build_gerfac_oficinas, build_gerfac_evolucao
from utils.data_processor import GerfacMetrics, build_gerfac_metrics, export_gerfac_excel
from utils.style import COLORS, flush_html, kpi_card, render_echart


def _md(html_str: str) -> None:
    st.markdown(flush_html(html_str), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Sidebar — filtros de data, semana, prestador e dias do gráfico
# --------------------------------------------------------------------------- #

def _render_filtros(df: pd.DataFrame) -> tuple[pd.DataFrame, int | str]:
    with st.sidebar:
        st.markdown("---")
        st.markdown("**Período**")
        min_date = df["Dt. Problema"].min().date()
        max_date = df["Dt. Problema"].max().date()
        date_range = st.date_input(
            "Período analisado",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            label_visibility="collapsed",
        )

        df_period = df.copy()
        if isinstance(date_range, tuple) and len(date_range) == 2:
            ini, fim = date_range
            df_period = df_period[
                (df_period["Dt. Problema"].dt.date >= ini) & 
                (df_period["Dt. Problema"].dt.date <= fim)
            ]

        st.markdown("**Semana**")
        if not df_period.empty:
            semanas_ordenadas = sorted(df_period["Dt. Problema"].dt.isocalendar().week.unique())
            semanas_opcoes = ["Todas"] + [f"W-{w}" for w in semanas_ordenadas]
        else:
            semanas_opcoes = ["Todas"]

        semana_sel = st.selectbox(
            "Filtrar por semana",
            options=semanas_opcoes,
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("**Prestadores**")
        todos_prestadores = sorted(df["Prest. Serviço"].unique())
        prestadores_sel = st.multiselect(
            "Filtrar prestadores",
            options=todos_prestadores,
            default=[],
            placeholder="Todos os prestadores",
            label_visibility="collapsed",
        )

        st.markdown("**Exibição do Gráfico Temporal**")
        dias_exibir = st.selectbox(
            "Quantidade de dias a exibir",
            options=[7, 15, 30, 60, "Todos"],
            index=2,
            label_visibility="collapsed",
        )

    # Filtragem efetiva
    df_f = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        ini, fim = date_range
        df_f = df_f[
            (df_f["Dt. Problema"].dt.date >= ini) & 
            (df_f["Dt. Problema"].dt.date <= fim)
        ]

    if semana_sel != "Todas":
        try:
            week_num = int(semana_sel.split("-")[1])
            df_f = df_f[df_f["Dt. Problema"].dt.isocalendar().week == week_num]
        except (IndexError, ValueError):
            pass

    if prestadores_sel:
        df_f = df_f[df_f["Prest. Serviço"].isin(prestadores_sel)]

    return df_f, dias_exibir


# --------------------------------------------------------------------------- #
# Seções do Dashboard
# --------------------------------------------------------------------------- #

def _render_header(m: GerfacMetrics) -> None:
    _md(
        f"""
        <div class="page-hero" style="margin-top:0.8rem; margin-bottom:1.5rem; text-align: left;">
            <div class="page-hero-title">ANÁLISE DE CONTROLE <span>GERFAC</span></div>
            <div class="page-hero-subtitle">Monitoramento de chamados por setor e prestador</div>
        </div>
        """
    )


def _render_kpis(m: GerfacMetrics) -> None:
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        _md(kpi_card(
            label="Total de Chamados",
            value=str(m.total_chamados),
            caption=f"Período: {m.periodo_inicio} a {m.periodo_fim}",
            icon="",
            pill_text=f"{m.total_chamados} registros",
            pill_bg="rgba(31,231,184,0.12)",
            pill_color="#1FE7B8",
        ))
    with c2:
        _md(kpi_card(
            label="Media por Dia",
            value=str(m.media_diaria),
            caption="Chamados por dia util no periodo",
            icon="",
            pill_text="solicitacoes/dia",
            pill_bg="rgba(91,239,209,0.12)",
            pill_color="#5BEFD1",
        ))
    with c3:
        _md(kpi_card(
            label="Principal Motivo",
            value=m.motivo_principal,
            caption=f"{m.motivo_principal_qtd} chamados — {m.motivo_principal_pct}% do total",
            icon="",
            pill_text=f"#{1} mais frequente",
            pill_bg="rgba(233,196,106,0.12)",
            pill_color="#E9C46A",
        ))
    with c4:
        _md(kpi_card(
            label="Setor com Mais Problema",
            value=m.setor_principal,
            caption=f"{m.setor_principal_qtd} chamados — {m.setor_principal_pct}% do total",
            icon="",
            pill_text="setor lider",
            pill_bg="rgba(224,102,122,0.12)",
            pill_color="#E0667A",
        ))



def _render_setores_e_oficinas(m: GerfacMetrics) -> None:
    col_setores, col_oficinas = st.columns([1.1, 1.1])

    with col_setores:
        _md('<div class="section-label">Distribuição por Setor Responsável</div>')
        _md('<div class="panel">')
        if not m.setores_resumo.empty:
            option, fmts = build_gerfac_setores(m.setores_resumo)
            render_echart(option, height=380, js_formatters=fmts)
        else:
            st.info("Sem dados de setores no período.")
        _md("</div>")

    with col_oficinas:
        _md('<div class="section-label">Prestadores com Mais Chamados (Top 10)</div>')
        _md('<div class="panel">')
        if not m.oficinas_resumo.empty:
            option, fmts = build_gerfac_oficinas(m.oficinas_resumo)
            render_echart(option, height=380, js_formatters=fmts)
        else:
            st.info("Sem dados de prestadores no período.")
        _md("</div>")


def _render_evolucao_temporal(m: GerfacMetrics, dias_exibir: int | str) -> None:
    _md('<div class="section-label">Evolução Temporal dos Chamados</div>')
    _md('<div class="panel">')

    serie = m.serie_diaria.copy()
    if not serie.empty:
        if isinstance(dias_exibir, int):
            serie = serie.tail(dias_exibir)
        
        option, fmts = build_gerfac_evolucao(serie)
        render_echart(option, height=340, js_formatters=fmts)
    else:
        st.info("Sem dados temporais disponíveis.")

    _md("</div>")


def render_gerfac_dados_table(df: pd.DataFrame) -> str:
    """Monta a tabela HTML personalizada para a base de dados GERFAC."""
    rows = []
    for _, row in df.iterrows():
        dt_fmt = pd.to_datetime(row["Dt. Problema"]).strftime("%d/%m/%Y")
        prest = html.escape(str(row["Prest. Serviço"]))
        ind = html.escape(str(row["INDICADORES"]))
        op = html.escape(str(row.get("OP", "")))
        art = html.escape(str(row.get("Artigo", "")))
        fase = html.escape(str(row.get("Fase", "")))
        inf_comp = html.escape(str(row["Inf. Complementar (P. Serviço)"]))
        
        rows.append(
            f"""<tr>
<td style="color:{COLORS['text_dim']}; white-space:nowrap;">{dt_fmt}</td>
<td>{prest}</td>
<td><span class="tag" style="background:rgba(31,231,184,0.08); color:{COLORS['aqua']};">{ind}</span></td>
<td style="color:{COLORS['text_dim']}; text-align:center;">{op}</td>
<td style="color:{COLORS['text_dim']}; text-align:center;">{art}</td>
<td style="color:{COLORS['text_dim']}; text-align:center;">{fase}</td>
<td style="color:{COLORS['text_dim']}; max-width:380px;">{inf_comp}</td>
</tr>"""
        )
    rows_html = "\n".join(rows)

    table_html = f"""
<div class="scrollable-table-wrap">
<table class="custom-table">
<thead>
<tr>
<th>Data</th>
<th>Prestador</th>
<th>Setor/Indicador</th>
<th style="text-align:center;">OP</th>
<th style="text-align:center;">Artigo</th>
<th style="text-align:center;">Fase</th>
<th>Informações Complementares</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
"""
    return flush_html(table_html)


def _render_rodape(m: GerfacMetrics, df_filtrado: pd.DataFrame) -> None:
    with st.expander("Ver dados tratados (base completa após classificação)"):
        _md(render_gerfac_dados_table(
            df_filtrado.sort_values("Dt. Problema", ascending=False)
        ))

    xlsx_bytes = export_gerfac_excel(df_filtrado, m.periodo_inicio, m.periodo_fim)
    nome_arquivo = (
        f"analise_gerfac_"
        f"{m.periodo_inicio.replace('/', '-')}_a_{m.periodo_fim.replace('/', '-')}.xlsx"
    )
    st.download_button(
        label="Exportar planilha executiva (.xlsx)",
        data=xlsx_bytes,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Gera uma planilha Excel com layout executivo contendo todos os registros filtrados.",
    )


# --------------------------------------------------------------------------- #
# Ponto de entrada público
# --------------------------------------------------------------------------- #

def render_dashboard_gerfac(df: pd.DataFrame) -> None:
    """Renderiza o dashboard do GERFAC completo."""
    df_f, dias_exibir = _render_filtros(df)

    if df_f.empty:
        st.warning("Nenhum chamado encontrado para os filtros selecionados.")
        return

    m = build_gerfac_metrics(df_f)

    _render_header(m)
    _render_kpis(m)
    _render_setores_e_oficinas(m)
    _render_evolucao_temporal(m, dias_exibir)
    _render_rodape(m, df_f)
