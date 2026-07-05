# -*- coding: utf-8 -*-
"""
Construtores de opções ECharts — Dashboard de Ajustes & Ocorrências.

Cada função retorna uma tupla (option, js_formatters) pronta para ser
passada diretamente a utils.style.render_echart():

    option, fmts = build_rosca(m.causas_resumo)
    render_echart(option, height=440, js_formatters=fmts)

Responsabilidade única: transformar DataFrames de métricas em dicionários
de configuração ECharts. Nenhuma função aqui chama st.* — renderização
é responsabilidade de quem chama.

Por que separar aqui?
- Cada gráfico pode ser alterado sem tocar na lógica de página.
- Os builders retornam dicts puros, fáceis de inspecionar e testar.
- Novos gráficos entram aqui sem poluir view_dashboard.py.

Gráficos disponíveis:
    build_rosca(causas_resumo)      → top 4 causas (donut)
    build_ranking(oficinas_resumo)  → top 10 oficinas (barras horizontais)
    build_causas(causas_resumo)     → todas as causas (colunas verticais)
    build_pareto(pareto_oficinas)   → pareto com linha de % acumulado
    build_linha(serie_diaria)       → sazonalidade diária com média móvel

Paleta e estilos compartilhados vêm de utils.style (COLORS, CHART_PALETTE,
echarts_tooltip_style) — ponto único de verdade visual.
"""

from __future__ import annotations

import pandas as pd

from utils.style import CHART_PALETTE, COLORS, echarts_tooltip_style, value_color_scale

# Atalho local — todos os gráficos usam o mesmo estilo de tooltip.
_tt = echarts_tooltip_style


# --------------------------------------------------------------------------- #
# Rosca — distribuição das causas de retrabalho
# --------------------------------------------------------------------------- #

def build_rosca(causas_resumo: pd.DataFrame) -> tuple[dict, dict]:
    """Gráfico de rosca com as top 4 causas de retrabalho.

    Causas além da 4ª são agrupadas em "Demais" para não poluir o visual.
    O total geral é exibido no centro do anel.

    Parâmetros
    ----------
    causas_resumo : DataFrame[CAUSA, QTD, PERCENTUAL]
        Saída de DashboardMetrics.causas_resumo (já ordenado por QTD desc).

    Retorna
    -------
    (option, js_formatters) prontos para render_echart().
    """
    top4 = causas_resumo.head(4).reset_index(drop=True)
    #outros_qtd = int(causas_resumo.iloc[5:]["QTD"].sum()) if len(causas_resumo) > 5 else 0

    rosca_data = [
        {"value": int(row["QTD"]), "name": row["CAUSA"]}
        for _, row in top4.iterrows()
    ]
    #if outros_qtd > 0:
    #    rosca_data.append({"value": outros_qtd, "name": "Demais"})

    palette = CHART_PALETTE[:4] + [COLORS["text_muted"]]
    total = sum(item["value"] for item in rosca_data)

    tooltip_js = f"""function(params) {{
        return '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:4px;">' +
               params.marker + params.name + '</div>' +
               '<div style="color:{COLORS['text']};font-size:12px;">' +
               '<span style="color:' + params.color + ';font-weight:800;">' + params.value + '</span>' +
               ' ocorrências &nbsp;<span style="color:{COLORS['aqua']};font-weight:800;">(' +
               params.percent.toFixed(1) + '%)</span></div>';
    }}"""

    label_js = f"""function(params) {{
        return '{{nome|' + params.name + '}}\\n{{valor|' + params.value +
               '}} {{pct|(' + params.percent.toFixed(1) + '%)}}';
    }}"""

    option = {
        "graphic": [
            {
                "type": "text",
                "left": "40%",
                "top": "48%",
                "style": {
                    "text": "{valor|" + str(total) + "}\n{rotulo|Total}",
                    "textAlign": "center",
                    "textVerticalAlign": "middle",
                    "fontFamily": "Inter, sans-serif",
                    "rich": {
                        "valor": {
                            "fill": COLORS["text"],
                            "fontSize": 28,
                            "fontWeight": "bold",
                            "lineHeight": 32,
                            "align": "center",
                        },
                        "rotulo": {
                            "fill": COLORS["text_dim"],
                            "fontSize": 12,
                            "lineHeight": 16,
                            "align": "center",
                        },
                    },
                },
            }
        ],
        "tooltip": {**_tt(), "trigger": "item", "formatter": "__ROSCA_TOOLTIP__"},
        "legend": {
            "orient": "vertical",
            "right": "1%",
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
                "radius": ["40%", "64%"],
                "center": ["42%", "51%"],
                "avoidLabelOverlap": True,
                "minShowLabelAngle": 8,
                "label": {
                    "show": True,
                    "position": "outside",
                    "formatter": "__ROSCA_LABEL__",
                    "color": COLORS["text"],
                    "fontSize": 11,
                    "fontFamily": "Inter, sans-serif",
                    "lineHeight": 15,
                    "rich": {
                        "nome": {
                            "color": COLORS["text"],
                            "fontWeight": 700,
                            "fontSize": 11,
                            "fontFamily": "Inter, sans-serif",
                        },
                        "valor": {
                            "color": COLORS["aqua"],
                            "fontWeight": 800,
                            "fontSize": 13,
                            "fontFamily": "Inter, sans-serif",
                        },
                        "pct": {
                            "color": COLORS["text_dim"],
                            "fontSize": 11,
                            "fontFamily": "Inter, sans-serif",
                        },
                    },
                },
                "labelLine": {
                    "show": True,
                    "length": 12,
                    "length2": 14,
                    "smooth": True,
                    "lineStyle": {"color": COLORS["text_muted"], "width": 1.2},
                },
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": 12,
                        "fontWeight": "bold",
                        "fontFamily": "Inter, sans-serif",
                    },
                    "itemStyle": {"shadowBlur": 14, "shadowColor": "rgba(31,231,184,0.35)"},
                },
                "data": [
                    {**item, "itemStyle": {"color": palette[i]}}
                    for i, item in enumerate(rosca_data)
                ],
            }
        ],
    }

    return option, {"__ROSCA_TOOLTIP__": tooltip_js, "__ROSCA_LABEL__": label_js}


# --------------------------------------------------------------------------- #
# Ranking horizontal — top 10 oficinas por volume
# --------------------------------------------------------------------------- #

def build_ranking(oficinas_resumo: pd.DataFrame) -> tuple[dict, dict]:
    """Barras horizontais com as top 10 oficinas por volume de ajustes.

    Cores interpoladas (escala de claro a aqua) proporcionais ao volume,
    para destacar visualmente as oficinas mais críticas.

    Parâmetros
    ----------
    oficinas_resumo : DataFrame[OFICINA, QTD]
        Saída de DashboardMetrics.oficinas_resumo (já ordenado desc).
    """
    top10 = oficinas_resumo.head(10).sort_values("QTD", ascending=True)
    bar_colors = value_color_scale(top10["QTD"])

    tooltip_js = f"""function(params) {{
        var p = params[0];
        return '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:4px;">' +
               p.marker + p.name + '</div>' +
               '<div style="color:{COLORS['text']};font-size:12px;">' +
               '<span style="color:' + p.color + ';font-weight:800;">' + p.value +
               '</span> ocorrências</div>';
    }}"""

    option = {
        "grid": {"left": 4, "right": 48, "top": 8, "bottom": 8, "containLabel": True},
        "tooltip": {
            **_tt(),
            "trigger": "axis",
            "axisPointer": {"type": "shadow", "shadowStyle": {"color": "rgba(31,231,184,0.06)"}},
            "formatter": "__RANKING_TOOLTIP__",
        },
        "xAxis": {"type": "value", "show": False},
        "yAxis": {
            "type": "category",
            "data": top10["OFICINA"].tolist(),
            "axisLine": {"show": False},
            "axisTick": {"show": False},
            "axisLabel": {
                "color": COLORS["text_dim"],
                "fontSize": 11,
                "fontFamily": "Inter, sans-serif",
            },
        },
        "series": [
            {
                "type": "bar",
                "data": [
                    {"value": int(v), "itemStyle": {"color": c, "borderRadius": [0, 5, 5, 0]}}
                    for v, c in zip(top10["QTD"], bar_colors)
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

    return option, {"__RANKING_TOOLTIP__": tooltip_js}


# --------------------------------------------------------------------------- #
# Colunas verticais — distribuição de todas as causas
# --------------------------------------------------------------------------- #

def build_causas(causas_resumo: pd.DataFrame) -> tuple[dict, dict]:
    """Colunas verticais com a distribuição de todas as causas de retrabalho.

    O tooltip inclui o percentual sobre o total, extraído do campo 'pct'
    injetado em cada ponto de dados (necessário porque o ECharts não calcula
    % por padrão em gráficos de barras).

    Parâmetros
    ----------
    causas_resumo : DataFrame[CAUSA, QTD, PERCENTUAL]
    """
    causas_df = causas_resumo.reset_index(drop=True)

    tooltip_js = f"""function(params) {{
        var pct = params.data.pct;
        return '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:4px;">' +
               params.marker + params.name + '</div>' +
               '<div style="color:{COLORS['text']};font-size:12px;">' +
               '<span style="color:' + params.color + ';font-weight:800;">' + params.value + '</span>' +
               ' ocorrências &nbsp;<span style="color:{COLORS['aqua']};font-weight:800;">(' +
               pct.toFixed(1) + '%)</span></div>';
    }}"""

    option = {
        "tooltip": {**_tt(), "trigger": "item", "formatter": "__CAUSAS_TOOLTIP__"},
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

    return option, {"__CAUSAS_TOOLTIP__": tooltip_js}


# --------------------------------------------------------------------------- #
# Pareto — barras de volume + linha de percentual acumulado
# --------------------------------------------------------------------------- #

def build_pareto(pareto_oficinas: pd.DataFrame) -> tuple[dict, dict]:
    """Pareto de oficinas: barras de volume (eixo Y esquerdo) e linha de
    percentual acumulado (eixo Y direito). Linha de referência a 80%.

    Parâmetros
    ----------
    pareto_oficinas : DataFrame[OFICINA, QTD, PCT, PCT_ACUM]
        Saída de DashboardMetrics.pareto_oficinas (já ordenado desc por QTD).
        Limitado internamente às 15 primeiras para não comprimir o eixo X.
    """
    pareto_df = pareto_oficinas.head(15)

    tooltip_js = f"""function(params) {{
        var html = '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:6px;">' +
                   params[0].axisValueLabel + '</div>';
        params.forEach(function(p) {{
            var val = p.seriesIndex === 0
                ? '<b style="color:' + p.color + ';font-weight:800;">' + p.value + '</b> ocorrências'
                : '<b style="color:' + p.color + ';font-weight:800;">' + (typeof p.value === 'number' ? p.value.toFixed(1) : p.value) +
                  '%</b> acumulado';
            html += '<div style="display:flex;align-items:center;justify-content:space-between;' +
                    'gap:16px;color:{COLORS['text']};font-size:12px;margin-top:3px;">' +
                    '<span>' + p.marker + p.seriesName + '</span>' +
                    '<span>' + val + '</span></div>';
        }});
        return html;
    }}"""

    option = {
        "tooltip": {
            **_tt(),
            "trigger": "axis",
            "formatter": "__PARETO_TOOLTIP__",
            "axisPointer": {"type": "shadow"},
        },
        "legend": {
            "data": ["Ocorrências", "% Acumulado"],
            "bottom": 0,
            "textStyle": {
                "color": COLORS["text_dim"],
                "fontSize": 11,
                "fontFamily": "Inter, sans-serif",
            },
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

    return option, {"__PARETO_TOOLTIP__": tooltip_js}


# --------------------------------------------------------------------------- #
# Linha — sazonalidade diária com média móvel
# --------------------------------------------------------------------------- #

def build_linha(serie_diaria: pd.DataFrame, granularity: str = "Dia") -> tuple[dict, dict]:
    """Linha com área — ocorrências por período, média móvel e variação percentual.

    Parâmetros
    ----------
    serie_diaria : DataFrame[PERIODO, QTD, VARIACAO, MEDIA_MOVEL]
        Saída de calculate_seasonality (ordenado por PERIODO asc).
    """
    if serie_diaria.empty:
        return {}, {}

    periods = pd.to_datetime(serie_diaria["PERIODO"])

    if granularity == "Dia":
        x_data = periods.dt.strftime("%d/%m").tolist()
        label_qtd = "Ocorrências/dia"
        label_media = "Média móvel (3d)"
    elif granularity == "Semana":
        x_data = [f"W-{dt.isocalendar().week}" for dt in periods]
        label_qtd = "Ocorrências/semana"
        label_media = "Média móvel (3s)"
    elif granularity == "Mês":
        PT_MONTHS = {
            1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
        }
        x_data = [f"{PT_MONTHS[dt.month]}/{str(dt.year)[2:]}" for dt in periods]
        label_qtd = "Ocorrências/mês"
        label_media = "Média móvel (3m)"
    else:
        x_data = periods.dt.strftime("%d/%m").tolist()
        label_qtd = "Ocorrências"
        label_media = "Média móvel"

    tooltip_js = f"""function(params) {{
        var html = '<div style="font-weight:700;color:{COLORS['text']};margin-bottom:6px;">' +
                    params[0].axisValueLabel + '</div>';
        params.forEach(function(p) {{
            var val_formatted = p.value;
            if (p.seriesName === "Variação (%)") {{
                if (p.value !== undefined && p.value !== null) {{
                    var numVal = Number(p.value);
                    val_formatted = (numVal >= 0 ? "+" : "") + numVal.toFixed(1) + "%";
                }} else {{
                    val_formatted = "0.0%";
                }}
            }}
            html += '<div style="display:flex;align-items:center;justify-content:space-between;' +
                    'gap:16px;color:{COLORS['text']};font-size:12px;margin-top:3px;">' +
                    '<span>' + p.marker + p.seriesName + '</span>' +
                    '<span style="font-weight:800;color:' + p.color + ';">' + val_formatted +
                    '</span></div>';
        }});
        return html;
    }}"""

    option = {
        "tooltip": {**_tt(), "trigger": "axis", "formatter": "__SAZONALIDADE_TOOLTIP__"},
        "legend": {
            "data": [label_qtd, label_media, "Variação (%)"],
            "bottom": 0,
            "textStyle": {
                "color": COLORS["text_dim"],
                "fontSize": 11,
                "fontFamily": "Inter, sans-serif",
            },
        },
        "grid": {"left": "1%", "right": "6%", "top": "12%", "bottom": "18%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": x_data,
            "boundaryGap": False,
            "axisLine": {"lineStyle": {"color": "rgba(255,255,255,0.12)"}},
            "axisTick": {"show": False},
            "axisLabel": {
                "color": COLORS["text_dim"],
                "fontSize": 10,
                "fontFamily": "Inter, sans-serif",
            },
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Ocorrências",
                "nameTextStyle": {"color": COLORS["text_dim"], "fontSize": 10},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
            },
            {
                "type": "value",
                "name": "Variação (%)",
                "nameTextStyle": {"color": COLORS["text_dim"], "fontSize": 10},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
            },
        ],
        "series": [
            {
                "name": label_qtd,
                "type": "line",
                "smooth": True,
                "symbolSize": 6,
                "data": [int(v) for v in serie_diaria["QTD"]],
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
                "name": label_media,
                "type": "line",
                "smooth": True,
                "showSymbol": False,
                "data": [float(v) for v in serie_diaria["MEDIA_MOVEL"]],
                "lineStyle": {"color": COLORS["amber"], "width": 2, "type": "dotted"},
            },
            {
                "name": "Variação (%)",
                "type": "line",
                "yAxisIndex": 1,
                "smooth": True,
                "symbolSize": 6,
                "data": [float(v) for v in serie_diaria["VARIACAO"]],
                "lineStyle": {"color": COLORS["green"], "width": 2},
                "itemStyle": {"color": COLORS["green"]},
            },
        ],
    }

    return option, {"__SAZONALIDADE_TOOLTIP__": tooltip_js}
