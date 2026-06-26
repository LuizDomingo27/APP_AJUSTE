# -*- coding: utf-8 -*-
"""
Sistema de Ajustes & Ocorrências — Dashboard Executivo
Upload da planilha → tratamento de dados → insights para a gestão.
"""

import streamlit as st
import pandas as pd

from utils.data_processor import load_dataframe, process_data, build_metrics, export_excel, FINANCIAL_CAUSES
from utils.database import save_to_db, load_from_db, get_db_info
from utils.github_sync import sync_to_github
from utils.style import (
    inject_global_css,
    kpi_card,
    render_oficinas_table,
    render_dados_table,
    render_outros_descricoes_table,
    render_echart,
    value_color_scale,
    echarts_tooltip_style,
    flush_html,
    COLORS,
    CHART_PALETTE,
)

st.set_page_config(
    page_title="Ajustes & Ocorrências | Resumo Executivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()


def md(html: str) -> None:
    """st.markdown com HTML, sempre desindentado para não virar bloco de código."""
    st.markdown(flush_html(html), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Sidebar — upload e filtros
# --------------------------------------------------------------------------- #

with st.sidebar:
    md(
        f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 1.4rem;">
            <div style="width:36px; height:36px; border-radius:10px;
                        background:rgba(31,231,184,0.12); display:flex;
                        align-items:center; justify-content:center; font-size:1.1rem;">📊</div>
            <div>
                <div style="font-weight:800; color:{COLORS['text']}; font-size:0.95rem;">AJUSTES &amp;</div>
                <div style="font-weight:800; color:{COLORS['aqua']}; font-size:0.95rem;">OCORRÊNCIAS</div>
            </div>
        </div>
        """
    )

    st.markdown("**📂 Planilha de ocorrências**")
    uploaded_file = st.file_uploader(
        "Envie o arquivo (.xlsx, .xls ou .csv)",
        type=["xlsx", "xls", "csv"],
        label_visibility="collapsed",
    )

    st.caption(
        "Colunas esperadas: **OM**, **OFICINA**, **DATA** e **DESCRIÇÃO/OBS**. "
        "O app reconhece variações comuns de cabeçalho automaticamente."
    )


# --------------------------------------------------------------------------- #
# Pipeline de dados
# --------------------------------------------------------------------------- #

if uploaded_file is not None:
    # Novo arquivo: processa, persiste no SQLite e sincroniza com o GitHub.
    try:
        raw_df = load_dataframe(uploaded_file)
        df = process_data(raw_df)
    except Exception as e:
        st.error(f"⚠️ Não foi possível processar a planilha enviada: {e}")
        st.stop()

    save_to_db(df)

    with st.spinner("Salvando..."):
        synced = sync_to_github()
    if synced:
        st.toast("Dados salvos e sincronizados!", icon="✅")
    else:
        st.toast("Dados salvos localmente.", icon="💾")

else:
    # Sem upload: tenta carregar do banco salvo.
    df = load_from_db()

    if df is not None:
        _db_info = get_db_info()
        if _db_info:
            st.toast(f"Base carregada · {_db_info['count']:,} registros · {_db_info['upload_date']}", icon="💾")

    if df is None:
        md(
            """
            <div class="app-title">RESUMO <span>EXECUTIVO</span></div>
            <div class="app-subtitle">Análise de retrabalho por oficina</div>
            """
        )
        md(
            """
            <div class="insight-box" style="margin-top:1.5rem;">
            👈 Envie a planilha de ocorrências na barra lateral para gerar o resumo executivo,
            com os indicadores, tabela de oficinas e gráficos de causas e sazonalidade.
            </div>
            """
        )
        st.stop()

if df.empty:
    st.warning("A planilha foi lida, porém nenhuma ocorrência válida (com data e oficina) foi encontrada.")
    st.stop()

# Filtros (sidebar)
with st.sidebar:
    st.markdown("---")
    st.markdown("**🗓️ Período**")
    min_date, max_date = df["DATA"].min().date(), df["DATA"].max().date()
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

# Aplica filtros
df_f = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    ini, fim = date_range
    df_f = df_f[(df_f["DATA"].dt.date >= ini) & (df_f["DATA"].dt.date <= fim)]
if oficinas_sel:
    df_f = df_f[df_f["OFICINA"].isin(oficinas_sel)]

if df_f.empty:
    st.warning("Nenhuma ocorrência encontrada para os filtros selecionados.")
    st.stop()

m = build_metrics(df_f)

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #

h1, h2 = st.columns([3, 1.1])
with h1:
    md(
        """
        <div class="app-title">ANÁLISE <span>DE RETRABALHO POR OFICINA</span></div>
        """
    )
with h2:
    md(
        f"""
        <div class="panel" style="padding: 0.7rem 1rem; margin-top:4px;">
            <div class="kpi-label">📅 Período analisado</div>
            <div style="color:{COLORS['text']}; font-weight:700; font-size:0.92rem;">
                {m.periodo_inicio} a {m.periodo_fim}
            </div>
        </div>
        """
    )

# --------------------------------------------------------------------------- #
# KPIs principais (cards solicitados pela gestão)
# --------------------------------------------------------------------------- #

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    md(
        kpi_card(
            label="Total de Ocorrências",
            value=str(m.total_ocorrencias),
            caption=f"ajustes registrados · média de {m.media_diaria}/dia",
            icon="📋",
        )
    )

with c2:
    md(
        kpi_card(
            label="Principal Causa",
            value=m.causa_principal,
            caption=f"{m.causa_principal_qtd} ocorrências",
            icon="🏷️",
            icon_bg="rgba(31,231,184,0.14)",
            icon_color=COLORS["aqua"],
            pill_text=f"{m.causa_principal_pct}% do total",
            pill_bg="rgba(31,231,184,0.14)",
            pill_color=COLORS["aqua"],
        )
    )

with c3:
    md(
        kpi_card(
            label="2ª Maior Causa",
            value=m.segunda_causa,
            caption=f"{m.segunda_causa_qtd} ocorrências",
            icon="⚖️",
            icon_bg="rgba(140,233,154,0.14)",
            icon_color=COLORS["green"],
            pill_text=f"{m.segunda_causa_pct}% do total",
            pill_bg="rgba(140,233,154,0.14)",
            pill_color=COLORS["green"],
        )
    )

with c4:
    md(
        kpi_card(
            label="Causas Financeiras",
            value=f"{m.pct_financeiro}%",
            caption="Descontos, Balanceamento, Valor Unitário e Reembolso",
            icon="💲",
            icon_bg="rgba(233,196,106,0.14)",
            icon_color=COLORS["amber"],
        )
    )

with c5:
    md(
        kpi_card(
            label="Oficinas com Reincidência",
            value=str(m.qtd_oficinas_reincidentes),
            caption=f"de {m.qtd_oficinas_total} oficinas no período",
            icon="🔁",
            icon_bg="rgba(224,102,122,0.14)",
            icon_color=COLORS["red"],
        )
    )

tooltip_style = echarts_tooltip_style()

# --------------------------------------------------------------------------- #
# Linha — Tabela de oficinas (largura cheia)
# --------------------------------------------------------------------------- #

md('<div class="section-label">Principais oficinas com problema</div>')

col_tabela, col_rosca = st.columns([1.6, 1])

with col_tabela:
    md('<div class="panel">')
    #md('<div class="panel-title">🏭 Ranking de oficinas por volume de ajustes</div>')
    md(render_oficinas_table(m.oficinas_resumo, top_n=8))
    md("</div>")

with col_rosca:
    md('<div class="panel">')
    #md('<div class="panel-title">🍩 Top 4 causas de retrabalho</div>')

    top4_causas = m.causas_resumo.head(4).reset_index(drop=True)
    outros_qtd = int(m.causas_resumo.iloc[4:]["QTD"].sum()) if len(m.causas_resumo) > 4 else 0
    rosca_data = [
        {"value": int(row["QTD"]), "name": row["CAUSA"]}
        for _, row in top4_causas.iterrows()
    ]
    if outros_qtd > 0:
        rosca_data.append({"value": outros_qtd, "name": "Demais"})

    rosca_palette = CHART_PALETTE[:4] + [COLORS["text_muted"]]

    rosca_tooltip_js = f"""function(params) {{
        return '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:4px;">' +
               params.marker + params.name + '</div>' +
               '<div style="color:{COLORS['text_dim']};font-size:12px;">' +
               '<span style="color:{COLORS['text']};font-weight:700;">' + params.value + '</span>' +
               ' ocorrências &nbsp;<span style="color:{COLORS['aqua']};font-weight:700;">(' +
               params.percent.toFixed(1) + '%)</span></div>';
    }}"""

    rosca_option = {
        "tooltip": {
            **tooltip_style,
            "trigger": "item",
            "formatter": "__ROSCA_TOOLTIP__",
        },
        "legend": {
            "orient": "vertical",
            "right": "2%",
            "top": "center",
            "textStyle": {
                "color": COLORS["text_dim"],
                "fontSize": 11,
                "fontFamily": "Inter, sans-serif",
            },
            "itemWidth": 10,
            "itemHeight": 10,
            "itemGap": 10,
        },
        "series": [
            {
                "type": "pie",
                "radius": ["38%", "64%"],
                "center": ["36%", "52%"],
                "avoidLabelOverlap": True,
                "label": {
                    "show": True,
                    "position": "outside",
                    "formatter": "{c}",
                    "color": COLORS["text"],
                    "fontSize": 11,
                    "fontWeight": 700,
                    "fontFamily": "Inter, sans-serif",
                },
                "labelLine": {
                    "show": True,
                    "length": 10,
                    "length2": 12,
                    "lineStyle": {"color": COLORS["text_muted"], "width": 1.2},
                },
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": 13,
                        "fontWeight": "bold",
                        "color": COLORS["aqua"],
                        "fontFamily": "Inter, sans-serif",
                    },
                    "itemStyle": {
                        "shadowBlur": 14,
                        "shadowColor": "rgba(31,231,184,0.35)",
                    },
                },
                "data": [
                    {**item, "itemStyle": {"color": rosca_palette[i]}}
                    for i, item in enumerate(rosca_data)
                ],
            }
        ],
    }

    render_echart(rosca_option, height=300, js_formatters={"__ROSCA_TOOLTIP__": rosca_tooltip_js})
    md("</div>")

# --------------------------------------------------------------------------- #
# Linha — Gráfico de oficinas com maior quantidade de ajustes (largura cheia)
# --------------------------------------------------------------------------- #

md('<div class="section-label">Ranking de ajustes e distribuição de causas</div>')

col_rank, col_causas = st.columns(2)

top_oficinas = m.oficinas_resumo.head(10).sort_values("QTD", ascending=True)
bar_colors = value_color_scale(top_oficinas["QTD"])

ranking_tooltip_js = f"""function(params) {{
    var p = params[0];
    return '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:4px;">' +
           p.marker + p.name + '</div>' +
           '<div style="color:{COLORS['text_dim']};font-size:12px;">' +
           '<span style="color:{COLORS['text']};font-weight:700;">' + p.value + '</span> ocorrências</div>';
}}"""

bar_option = {
    "grid": {"left": 4, "right": 48, "top": 8, "bottom": 8, "containLabel": True},
    "tooltip": {
        **tooltip_style,
        "trigger": "axis",
        "axisPointer": {"type": "shadow", "shadowStyle": {"color": "rgba(31,231,184,0.06)"}},
        "formatter": "__RANKING_TOOLTIP__",
    },
    "xAxis": {"type": "value", "show": False},
    "yAxis": {
        "type": "category",
        "data": top_oficinas["OFICINA"].tolist(),
        "axisLine": {"show": False},
        "axisTick": {"show": False},
        "axisLabel": {"color": COLORS["text_dim"], "fontSize": 11, "fontFamily": "Inter, sans-serif"},
    },
    "series": [
        {
            "type": "bar",
            "data": [
                {"value": int(v), "itemStyle": {"color": c, "borderRadius": [0, 5, 5, 0]}}
                for v, c in zip(top_oficinas["QTD"], bar_colors)
            ],
            "barWidth": "56%",
            "label": {
                "show": True,
                "position": "right",
                "color": COLORS["text"],
                "fontSize": 12,
                "fontWeight": 600,
            },
        }
    ],
}

causas_df = m.causas_resumo.reset_index(drop=True)

causas_tooltip_js = f"""function(params) {{
    var pct = params.data.pct;
    return '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:4px;">' +
           params.marker + params.name + '</div>' +
           '<div style="color:{COLORS['text_dim']};font-size:12px;">' +
           params.value + ' ocorrências &nbsp;<span style="color:{COLORS['aqua']};font-weight:700;">(' +
           pct.toFixed(1) + '%)</span></div>';
}}"""

column_option = {
    "tooltip": {
        **tooltip_style,
        "trigger": "item",
        "formatter": "__CAUSAS_TOOLTIP__",
    },
    "grid": {"left": "1%", "right": "2%", "top": "10%", "bottom": "18%", "containLabel": True},
    "xAxis": {
        "type": "category",
        "data": causas_df["CAUSA"].tolist(),
        "axisLine": {"lineStyle": {"color": "rgba(255,255,255,0.12)"}},
        "axisTick": {"show": False},
        "axisLabel": {
            "color": COLORS["text_dim"],
            "fontSize": 10,
            "fontFamily": "Inter, sans-serif",
            "interval": 0,
            "rotate": 22,
        },
    },
    "yAxis": {
        "type": "value",
        "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
        "axisLabel": {"color": COLORS["text_dim"], "fontFamily": "Inter, sans-serif"},
    },
    "series": [
        {
            "type": "bar",
            "barWidth": "52%",
            "data": [
                {
                    "value": int(row["QTD"]),
                    "pct": float(row["PERCENTUAL"]),
                    "itemStyle": {
                        "color": CHART_PALETTE[i % len(CHART_PALETTE)],
                        "borderRadius": [6, 6, 0, 0],
                    },
                }
                for i, row in causas_df.iterrows()
            ],
            "label": {
                "show": True,
                "position": "top",
                "color": COLORS["text"],
                "fontSize": 11,
                "fontWeight": 600,
            },
        }
    ],
}

with col_rank:
    md('<div class="panel">')
    #md('<div class="panel-title">📊 Ranking de ajustes por oficina</div>')
    render_echart(bar_option, height=360, js_formatters={"__RANKING_TOOLTIP__": ranking_tooltip_js})
    md("</div>")

with col_causas:
    md('<div class="panel">')
    #md('<div class="panel-title">🧭 Distribuição das causas de retrabalho</div>')
    render_echart(column_option, height=360, js_formatters={"__CAUSAS_TOOLTIP__": causas_tooltip_js})
    md(
        f"""
        <div class="insight-box">
        💡 As causas financeiras (Descontos, Balanceamento, Valor Unitário e Reembolso)
        concentram <b style="color:{COLORS['aqua']};">{m.pct_financeiro}%</b> de todas as ocorrências do período —
        oportunidade clara de revisão de processo de cadastro de preços e regras de fechamento.
        </div>
        """
    )
    md("</div>")

# --------------------------------------------------------------------------- #
# Linha — Pareto de oficinas (curva de concentração)
# --------------------------------------------------------------------------- #

md('<div class="section-label">Concentração de ocorrências — análise de Pareto</div>')
md('<div class="panel">')
#md('<div class="panel-title">📉 Pareto de oficinas — volume e % acumulado de ajustes</div>')

pareto_df = m.pareto_oficinas.head(15)
pareto_label = f"{m.pareto_80pct_count} oficina{'s' if m.pareto_80pct_count != 1 else ''}"

pareto_tooltip_js = f"""function(params) {{
    var html = '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:6px;">' +
               params[0].axisValueLabel + '</div>';
    params.forEach(function(p) {{
        var val = p.seriesIndex === 0
            ? '<b>' + p.value + '</b> ocorrências'
            : '<b>' + (typeof p.value === 'number' ? p.value.toFixed(1) : p.value) + '%</b> acumulado';
        html += '<div style="display:flex;align-items:center;justify-content:space-between;' +
                'gap:16px;color:{COLORS['text_dim']};font-size:12px;margin-top:3px;">' +
                '<span>' + p.marker + p.seriesName + '</span>' +
                '<span style="font-weight:700;color:{COLORS['text']};">' + val + '</span></div>';
    }});
    return html;
}}"""

pareto_option = {
    "tooltip": {
        **tooltip_style,
        "trigger": "axis",
        "formatter": "__PARETO_TOOLTIP__",
        "axisPointer": {"type": "shadow"},
    },
    "legend": {
        "data": ["Ocorrências", "% Acumulado"],
        "bottom": 0,
        "textStyle": {"color": COLORS["text_dim"], "fontSize": 11, "fontFamily": "Inter, sans-serif"},
    },
    "grid": {"left": "1%", "right": "6%", "top": "10%", "bottom": "20%", "containLabel": True},
    "xAxis": {
        "type": "category",
        "data": pareto_df["OFICINA"].tolist(),
        "axisLine": {"lineStyle": {"color": "rgba(255,255,255,0.12)"}},
        "axisTick": {"show": False},
        "axisLabel": {
            "color": COLORS["text_dim"],
            "fontSize": 10,
            "fontFamily": "Inter, sans-serif",
            "interval": 0,
            "rotate": 25,
        },
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Ocorrências",
            "nameTextStyle": {"color": COLORS["text_dim"], "fontSize": 10},
            "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
            "axisLabel": {"color": COLORS["text_dim"], "fontFamily": "Inter, sans-serif"},
        },
        {
            "type": "value",
            "name": "% Acum.",
            "nameTextStyle": {"color": COLORS["text_dim"], "fontSize": 10},
            "min": 0,
            "max": 100,
            "interval": 20,
            "splitLine": {"show": False},
            "axisLabel": {
                "color": COLORS["text_dim"],
                "fontFamily": "Inter, sans-serif",
                "formatter": "{value}%",
            },
        },
    ],
    "series": [
        {
            "name": "Ocorrências",
            "type": "bar",
            "barWidth": "52%",
            "data": pareto_df["QTD"].tolist(),
            "itemStyle": {"color": COLORS["aqua"], "borderRadius": [4, 4, 0, 0]},
            "label": {
                "show": True,
                "position": "top",
                "color": COLORS["text"],
                "fontSize": 10,
                "fontWeight": 600,
            },
        },
        {
            "name": "% Acumulado",
            "type": "line",
            "yAxisIndex": 1,
            "smooth": False,
            "data": pareto_df["PCT_ACUM"].tolist(),
            "lineStyle": {"color": COLORS["amber"], "width": 2.5},
            "itemStyle": {"color": COLORS["amber"]},
            "symbolSize": 7,
            "markLine": {
                "silent": True,
                "data": [{"yAxis": 80}],
                "lineStyle": {"color": COLORS["red"], "type": "dashed", "width": 1.5},
                "label": {
                    "show": True,
                    "formatter": "80%",
                    "color": COLORS["red"],
                    "fontSize": 11,
                    "fontWeight": 700,
                    "position": "insideEndTop",
                },
            },
        },
    ],
}

render_echart(pareto_option, height=400, js_formatters={"__PARETO_TOOLTIP__": pareto_tooltip_js})

md(
    f"""
    <div class="insight-box">
    📊 <b style="color:{COLORS['aqua']};">{pareto_label}</b>
    ({m.pareto_80pct_pct_oficinas}% do total de {m.qtd_oficinas_total})
    respondem por <b style="color:{COLORS['amber']};">80% de todas as ocorrências</b> —
    foco de ação imediata para reduzir o volume de ajustes.
    </div>
    """
)
md("</div>")

# --------------------------------------------------------------------------- #
# Linha — % de ocorrências "Outros" (qualidade das regras de classificação)
# --------------------------------------------------------------------------- #

md('<div class="section-label">Qualidade da classificação de causas</div>')

if m.outros_pct >= 20:
    _o_icon_bg = "rgba(224,102,122,0.14)"
    _o_icon_color = COLORS["red"]
    _o_pill_bg = "rgba(224,102,122,0.14)"
    _o_pill_color = COLORS["red"]
    _o_pill = "⚠ Requer atenção"
    _o_border = COLORS["red"]
    _o_status = "acima de 20% — alto! Muitas ocorrências sem categoria indicam que <b>CAUSE_RULES</b> precisa de revisão urgente."
elif m.outros_pct >= 10:
    _o_icon_bg = "rgba(233,196,106,0.14)"
    _o_icon_color = COLORS["amber"]
    _o_pill_bg = "rgba(233,196,106,0.14)"
    _o_pill_color = COLORS["amber"]
    _o_pill = "△ Monitorar"
    _o_border = COLORS["amber"]
    _o_status = "entre 10% e 20% — monitorar; avalie se novas palavras-chave são necessárias em <b>CAUSE_RULES</b>."
else:
    _o_icon_bg = "rgba(31,231,184,0.12)"
    _o_icon_color = COLORS["aqua"]
    _o_pill_bg = "rgba(31,231,184,0.14)"
    _o_pill_color = COLORS["aqua"]
    _o_pill = "✓ Sob controle"
    _o_border = COLORS["aqua"]
    _o_status = "abaixo de 10% — as regras de classificação cobrem bem as ocorrências."

col_o_kpi, col_o_info = st.columns([1, 2.5])
with col_o_kpi:
    md(
        kpi_card(
            label='Ocorrências "Outros"',
            value=f"{m.outros_pct}%",
            caption=f"{m.outros_qtd} de {m.total_ocorrencias} registros sem categoria",
            icon="🔎",
            icon_bg=_o_icon_bg,
            icon_color=_o_icon_color,
            pill_text=_o_pill,
            pill_bg=_o_pill_bg,
            pill_color=_o_pill_color,
        )
    )
with col_o_info:
    md(
        f"""
        <div class="panel">
        <div class="panel-title">🔎 O que é a causa "Outros"?</div>
        <div style="color:{COLORS['text_dim']}; font-size:0.86rem; line-height:1.6;">
        Toda ocorrência que não corresponde a nenhuma palavra-chave em
        <b style="color:{COLORS['text']};">CAUSE_RULES</b> (data_processor.py)
        recebe automaticamente a causa <b style="color:{COLORS['text']};">Outros</b>.
        Um percentual alto indica que muitas ocorrências ficaram sem categoria definida.
        </div>
        <div class="insight-box" style="margin-top:0.7rem; border-left-color:{_o_border};">
        O percentual atual de <b style="color:{_o_border};">{m.outros_pct}%</b> está {_o_status}
        </div>
        </div>
        """
    )

if not m.outros_top_descricoes.empty:
    with st.expander("📋 Descrições mais frequentes dentro de 'Outros' (candidatas a novas regras)"):
        md(render_outros_descricoes_table(m.outros_top_descricoes))

# --------------------------------------------------------------------------- #
# Linha — Sazonalidade / tendência diária (largura cheia)
# --------------------------------------------------------------------------- #

md('<div class="section-label">Sazonalidade — tendência diária</div>')
md('<div class="panel">')
#md('<div class="panel-title">📈 Ocorrências por dia e tendência (média móvel de 3 dias)</div>')

serie = m.serie_diaria
dias_fmt = pd.to_datetime(serie["DIA"]).dt.strftime("%d/%m").tolist()

sazonalidade_tooltip_js = f"""function(params) {{
    var html = '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:6px;">' +
                params[0].axisValueLabel + '</div>';
    params.forEach(function(p) {{
        html += '<div style="display:flex;align-items:center;justify-content:space-between;' +
                'gap:16px;color:{COLORS['text_dim']};font-size:12px;margin-top:3px;">' +
                '<span>' + p.marker + p.seriesName + '</span>' +
                '<span style="font-weight:700;color:{COLORS['text']};">' + p.value + '</span></div>';
    }});
    return html;
}}"""

line_option = {
    "tooltip": {
        **tooltip_style,
        "trigger": "axis",
        "formatter": "__SAZONALIDADE_TOOLTIP__",
    },
    "legend": {
        "data": ["Ocorrências/dia", "Média móvel (3d)"],
        "bottom": 0,
        "textStyle": {"color": COLORS["text_dim"], "fontSize": 11, "fontFamily": "Inter, sans-serif"},
    },
    "grid": {"left": "1%", "right": "2%", "top": "6%", "bottom": "16%", "containLabel": True},
    "xAxis": {
        "type": "category",
        "data": dias_fmt,
        "boundaryGap": False,
        "axisLine": {"lineStyle": {"color": "rgba(255,255,255,0.12)"}},
        "axisTick": {"show": False},
        "axisLabel": {"color": COLORS["text_dim"], "fontSize": 10, "fontFamily": "Inter, sans-serif"},
    },
    "yAxis": {
        "type": "value",
        "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}},
        "axisLabel": {"color": COLORS["text_dim"], "fontFamily": "Inter, sans-serif"},
    },
    "series": [
        {
            "name": "Ocorrências/dia",
            "type": "line",
            "smooth": True,
            "symbolSize": 6,
            "data": serie["QTD"].tolist(),
            "lineStyle": {"color": COLORS["aqua"], "width": 2.5},
            "itemStyle": {"color": COLORS["aqua"]},
            "areaStyle": {
                "color": {
                    "type": "linear",
                    "x": 0, "y": 0, "x2": 0, "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": "rgba(31,231,184,0.22)"},
                        {"offset": 1, "color": "rgba(31,231,184,0)"},
                    ],
                }
            },
        },
        {
            "name": "Média móvel (3d)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": serie["MEDIA_MOVEL"].tolist(),
            "lineStyle": {"color": COLORS["amber"], "width": 2, "type": "dotted"},
        },
    ],
}
render_echart(line_option, height=360, js_formatters={"__SAZONALIDADE_TOOLTIP__": sazonalidade_tooltip_js})

pico = serie.loc[serie["QTD"].idxmax()]
md(
    f"""
    <div class="insight-box">
    📌 Pico de <b style="color:{COLORS['aqua']};">{int(pico['QTD'])} ocorrências</b> em
    <b>{pd.to_datetime(pico['DIA']).strftime('%d/%m/%Y')}</b>. A linha pontilhada mostra a
    tendência (média móvel de 3 dias) para identificar se o retrabalho está em alta ou queda.
    </div>
    """
)
md("</div>")

# --------------------------------------------------------------------------- #
# Rodapé — conclusão gerencial
# --------------------------------------------------------------------------- #

top3 = m.causas_resumo.head(3)
top3_pct = round(top3["PERCENTUAL"].sum(), 0)
top3_nomes = ", ".join(top3["CAUSA"].tolist())

md(
    f"""
    <div class="panel" style="margin-top:1.4rem; display:flex; align-items:center; gap:18px;">
        <div style="font-size:1.8rem;">🏆</div>
        <div>
            <div style="font-weight:800; color:{COLORS['text']}; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.04em;">
                Conclusão Gerencial
            </div>
            <div style="color:{COLORS['text_dim']}; font-size:0.86rem; margin-top:4px;">
                Os retrabalhos estão concentrados em poucos tipos de erro: <b style="color:{COLORS['aqua']};">{top3_nomes}</b>
                respondem por aproximadamente <b style="color:{COLORS['aqua']};">{top3_pct:.0f}%</b> das ocorrências do período.
                Atuar sobre essas causas e sobre as <b>{m.qtd_oficinas_reincidentes} oficinas reincidentes</b> pode reduzir
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
    md(
        render_dados_table(
            df_f[["OM", "OFICINA", "DATA", "CAUSA", "DESCRICAO"]].sort_values("DATA", ascending=False),
            causa_colors=causa_color_map,
        )
    )

xlsx_bytes = export_excel(df_f, m.periodo_inicio, m.periodo_fim)
st.download_button(
    label="⬇️ Exportar planilha executiva (.xlsx)",
    data=xlsx_bytes,
    file_name=f"ajustes_ocorrencias_{m.periodo_inicio.replace('/', '-')}_a_{m.periodo_fim.replace('/', '-')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    help="Gera uma planilha Excel com layout executivo contendo todos os registros filtrados.",
)
