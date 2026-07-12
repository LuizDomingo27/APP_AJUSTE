# -*- coding: utf-8 -*-
"""
Módulo de estilo visual — paleta verde neon aqua / dark, bordas suaves,
cards e tabela 100% personalizados em HTML/CSS, no padrão do mock de
referência (Resumo Executivo).

IMPORTANTE: os blocos HTML retornados aqui são sempre "desindentados"
(flush à esquerda) antes de ir para st.markdown. O parser Markdown do
Streamlit trata blocos com 4+ espaços de indentação como código-fonte
literal — se isso não for respeitado, o HTML aparece como texto cru em
vez de ser renderizado.
"""

import html
import json
import textwrap

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --------------------------------------------------------------------------- #
# Paleta
# --------------------------------------------------------------------------- #

COLORS = {
    "bg": "#070B10",
    "bg_card": "#0E151B",
    "bg_card_alt": "#0B1117",
    "border": "rgba(31, 231, 184, 0.18)",
    "border_strong": "rgba(31, 231, 184, 0.45)",
    "aqua": "#1FE7B8",
    "aqua_soft": "#5BEFD1",
    "green": "#8CE99A",
    "amber": "#E9C46A",
    "red": "#E0667A",
    "text": "#E9F5F1",
    "text_dim": "#7F93A0",
    "text_muted": "#5A6B76",
}

CHART_PALETTE = ["#1FE7B8", "#8CE99A", "#E9C46A", "#5BEFD1", "#4D8FAC", "#2C3E46"]


def _flush(html: str) -> str:
    """Remove indentação comum e espaços de borda para evitar que o
    Markdown interprete o HTML como bloco de código."""
    return textwrap.dedent(html).strip()


# Alias público — usado também em app.py para qualquer bloco HTML solto,
# evitando o mesmo problema de indentação virar bloco de código Markdown.
flush_html = _flush


def inject_global_css() -> None:
    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');

html, body, [class*="css"] {{
font-family: 'Inter', sans-serif;
}}

.stApp {{
background: radial-gradient(circle at 10% -10%, rgba(31,231,184,0.06), transparent 45%),
            radial-gradient(circle at 90% 0%, rgba(91,239,209,0.05), transparent 40%),
            {COLORS['bg']};
}}

section[data-testid="stSidebar"] {{
background: #060A0E;
border-right: 1px solid {COLORS['border']};
}}

#MainMenu, footer {{visibility: hidden;}}
[data-testid="stHeader"] {{
height: 0rem !important;
min-height: 0rem !important;
background: transparent !important;
box-shadow: none !important;
overflow: visible !important;
}}
[data-testid="stDecoration"] {{
display: none !important;
}}
[data-testid="stToolbar"] {{
visibility: hidden !important;
}}

/* Botão de abrir a sidebar quando ela está colapsada */
[data-testid="stExpandSidebarButton"] {{
visibility: visible !important;
display: flex !important;
opacity: 1 !important;
position: fixed !important;
top: 0.8rem !important;
left: 0.8rem !important;
background: rgba(31,231,184,0.16) !important;
border: 1px solid {COLORS['border_strong']} !important;
border-radius: 10px !important;
z-index: 999999 !important;
}}
[data-testid="stExpandSidebarButton"] svg {{
fill: {COLORS['aqua']} !important;
color: {COLORS['aqua']} !important;
}}

/* Botão de fechar a sidebar quando ela está aberta */
[data-testid="stSidebarCollapseButton"] {{
visibility: visible !important;
opacity: 1 !important;
}}
[data-testid="stSidebarCollapseButton"] svg {{
fill: {COLORS['aqua']} !important;
color: {COLORS['aqua']} !important;
}}

.block-container {{
padding-top: 1.2rem;
padding-bottom: 2rem;
padding-left: 2.2rem;
padding-right: 2.2rem;
max-width: 100% !important;
}}

.app-title {{
font-family: 'Manrope', sans-serif;
font-weight: 800;
font-size: 2.05rem;
letter-spacing: -0.02em;
color: {COLORS['text']};
margin-bottom: 0;
}}
.app-title span {{
color: {COLORS['aqua']};
text-shadow: 0 0 18px rgba(31,231,184,0.35);
}}
.app-subtitle {{
color: {COLORS['text_dim']};
font-size: 0.85rem;
letter-spacing: 0.06em;
text-transform: uppercase;
margin-top: 2px;
}}

.section-label {{
color: {COLORS['aqua_soft']};
font-size: 0.78rem;
font-weight: 700;
letter-spacing: 0.08em;
text-transform: uppercase;
margin: 1.8rem 0 0.7rem 0;
display: flex;
align-items: center;
gap: 8px;
}}
.section-label::before {{
content: "";
width: 6px;
height: 6px;
border-radius: 50%;
background: {COLORS['aqua']};
box-shadow: 0 0 8px {COLORS['aqua']};
display: inline-block;
}}

.kpi-card {{
background: linear-gradient(165deg, {COLORS['bg_card']} 0%, {COLORS['bg_card_alt']} 100%);
border: 1px solid {COLORS['border']};
border-radius: 18px;
padding: 0.95rem 1.1rem;
height: 142px;
position: relative;
overflow: hidden;
transition: border-color 0.2s ease;
box-sizing: border-box;
}}
.kpi-card:hover {{
border-color: {COLORS['border_strong']};
}}
.kpi-card::after {{
content: "";
position: absolute;
top: -40%; right: -30%;
width: 140px; height: 140px;
background: radial-gradient(circle, rgba(31,231,184,0.10), transparent 70%);
pointer-events: none;
}}
.kpi-icon {{
width: 38px; height: 38px;
border-radius: 11px;
display: flex; align-items: center; justify-content: center;
font-size: 1.05rem;
margin-bottom: 0.6rem;
}}

.kpi-label {{
color: #A8BFBA;
font-size: 0.72rem;
font-weight: 600;
letter-spacing: 0.06em;
text-transform: uppercase;
margin-bottom: 0.15rem;
}}

.kpi-value {{
font-family: 'Manrope', sans-serif;
font-size: clamp(1.05rem, 1.7rem, 1.7rem);
font-weight: 800;
color: {COLORS['text']};
line-height: 1.2;
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
max-width: 100%;
margin-bottom: 0.25rem;
}}

.kpi-caption {{
color: #C8D8D4;
font-size: 0.76rem;
line-height: 1.35;
margin-bottom: 0.35rem;
}}

.kpi-pill {{
display: inline-block;
padding: 2px 8px;
border-radius: 999px;
font-size: 0.70rem;
font-weight: 700;
}}

/* ---------- Panel container ---------- */
.panel {{
background: linear-gradient(165deg, {COLORS['bg_card']} 0%, {COLORS['bg_card_alt']} 100%);
border: 1px solid {COLORS['border']};
border-radius: 18px;
padding: 1.2rem 1.35rem 1.35rem 1.35rem;
height: 100%;
}}
.panel-title {{
color: {COLORS['text']};
font-weight: 700;
font-size: 0.92rem;
letter-spacing: 0.03em;
text-transform: uppercase;
margin-bottom: 0.85rem;
}}

/* ---------- Custom HTML table ---------- */
.custom-table-wrap {{
border-radius: 14px;
overflow: hidden;
border: 1px solid {COLORS['border']};
}}
.scrollable-table-wrap {{
border-radius: 14px;
border: 1px solid {COLORS['border']};
max-height: 480px;
overflow-y: auto;
overflow-x: hidden;
}}
.scrollable-table-wrap::-webkit-scrollbar {{
width: 8px;
}}
.scrollable-table-wrap::-webkit-scrollbar-track {{
background: transparent;
}}
.scrollable-table-wrap::-webkit-scrollbar-thumb {{
background: rgba(31,231,184,0.25);
border-radius: 8px;
}}
.scrollable-table-wrap table.custom-table thead th {{
position: sticky;
top: 0;
z-index: 2;
}}
table.custom-table {{
width: 100%;
border-collapse: collapse;
font-size: 0.86rem;
}}
table.custom-table thead th {{
background: linear-gradient(180deg, rgba(31,231,184,0.16), rgba(31,231,184,0.07));
color: {COLORS['aqua']};
text-transform: uppercase;
font-size: 0.7rem;
letter-spacing: 0.07em;
font-weight: 800;
text-align: left;
padding: 11px 16px;
border-bottom: 1px solid {COLORS['border_strong']};
}}
table.custom-table tbody td {{
padding: 10px 16px;
color: {COLORS['text']};
border-bottom: 1px solid rgba(255,255,255,0.03);
}}
table.custom-table tbody tr {{
background: transparent;
transition: background 0.15s ease;
}}
table.custom-table tbody tr:nth-child(even) {{
background: rgba(31,231,184,0.045);
}}
table.custom-table tbody tr:hover {{
background: rgba(31,231,184,0.11);
}}
table.custom-table tbody tr:last-child td {{
border-bottom: none;
}}
.rank-badge {{
display: inline-flex;
align-items: center;
justify-content: center;
width: 22px; height: 22px;
border-radius: 50%;
font-size: 0.72rem;
font-weight: 800;
color: #04140F;
}}
.bar-track {{
width: 100%;
height: 6px;
border-radius: 4px;
background: rgba(255,255,255,0.06);
overflow: hidden;
}}
.bar-fill {{
height: 100%;
border-radius: 4px;
background: linear-gradient(90deg, {COLORS['aqua']}, {COLORS['aqua_soft']});
}}
.tag {{
display: inline-block;
padding: 2px 9px;
border-radius: 999px;
font-size: 0.72rem;
font-weight: 700;
}}

.insight-box {{
border: 1px solid {COLORS['border']};
border-left: 3px solid {COLORS['aqua']};
border-radius: 12px;
padding: 0.85rem 1rem;
background: rgba(31,231,184,0.04);
font-size: 0.86rem;
color: {COLORS['text']};
margin-top: 0.7rem;
}}

[data-testid="stMetricValue"] {{ color: {COLORS['text']}; }}

/* Oculta o nome do arquivo exibido pelo file_uploader na sidebar */
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {{
    display: none !important;
}}

/* ======================================================= */
/* FORMULÁRIOS — inputs, labels, selects, botões, cards    */
/* ======================================================= */

/* Labels dos campos */
[data-testid="stTextInput"] > label,
[data-testid="stTextArea"] > label,
[data-testid="stDateInput"] > label,
[data-testid="stSelectbox"] > label {{
    color: {COLORS['text_dim']} !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    margin-bottom: 2px !important;
}}

/* Text inputs */
[data-testid="stTextInput"] input {{
    background: rgba(4, 7, 10, 0.92) !important;
    border: 1px solid rgba(31,231,184,0.2) !important;
    border-radius: 10px !important;
    color: {COLORS['text']} !important;
    font-size: 0.92rem !important;
    transition: border-color 0.22s, box-shadow 0.22s !important;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: rgba(31,231,184,0.6) !important;
    box-shadow: 0 0 0 3px rgba(31,231,184,0.10) !important;
    outline: none !important;
}}

/* Textarea */
[data-testid="stTextArea"] textarea {{
    background: rgba(4, 7, 10, 0.92) !important;
    border: 1px solid rgba(31,231,184,0.2) !important;
    border-radius: 10px !important;
    color: {COLORS['text']} !important;
    font-size: 0.92rem !important;
    transition: border-color 0.22s, box-shadow 0.22s !important;
    resize: vertical !important;
}}
[data-testid="stTextArea"] textarea:focus {{
    border-color: rgba(31,231,184,0.6) !important;
    box-shadow: 0 0 0 3px rgba(31,231,184,0.10) !important;
}}

/* Date input */
[data-testid="stDateInput"] input {{
    background: rgba(4, 7, 10, 0.92) !important;
    border: 1px solid rgba(31,231,184,0.2) !important;
    border-radius: 10px !important;
    color: {COLORS['text']} !important;
    font-size: 0.92rem !important;
}}

/* Selectbox — trigger container */
[data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child {{
    background: rgba(4, 7, 10, 0.92) !important;
    border: 1px solid rgba(31,231,184,0.2) !important;
    border-radius: 10px !important;
    transition: border-color 0.22s !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] svg {{
    fill: {COLORS['aqua']} !important;
}}

/* Form container → card com tarja superior */
[data-testid="stForm"] {{
    background: linear-gradient(165deg, {COLORS['bg_card']} 0%, {COLORS['bg_card_alt']} 100%) !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 18px !important;
    padding: 1.5rem 1.8rem 1.7rem !important;
    position: relative !important;
    overflow: hidden !important;
    box-shadow: 0 8px 36px rgba(0,0,0,0.35) !important;
    margin-bottom: 0 !important;
}}
[data-testid="stForm"]::before {{
    content: "" !important;
    position: absolute !important;
    top: 0; left: 0; right: 0 !important;
    height: 3px !important;
    background: linear-gradient(90deg, {COLORS['aqua']}, {COLORS['aqua_soft']}, transparent) !important;
    pointer-events: none !important;
}}

/* Botões — base comum */
.stButton > button,
.stFormSubmitButton > button {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.025em !important;
    transition: all 0.2s ease !important;
    font-family: 'Inter', sans-serif !important;
}}

/* Botão primary */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primaryFormSubmit"] {{
    background: linear-gradient(135deg, {COLORS['aqua']} 0%, {COLORS['aqua_soft']} 100%) !important;
    color: #04140F !important;
    border: none !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 18px rgba(31,231,184,0.28) !important;
}}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover {{
    box-shadow: 0 6px 26px rgba(31,231,184,0.46) !important;
    filter: brightness(1.07) !important;
    transform: translateY(-1px) !important;
}}

/* Botão secondary / padrão */
.stButton > button:not([kind="primary"]),
.stFormSubmitButton > button[kind="secondaryFormSubmit"] {{
    background: rgba(31,231,184,0.07) !important;
    color: {COLORS['aqua']} !important;
    border: 1px solid rgba(31,231,184,0.28) !important;
}}
.stButton > button:not([kind="primary"]):hover,
.stFormSubmitButton > button[kind="secondaryFormSubmit"]:hover {{
    background: rgba(31,231,184,0.13) !important;
    border-color: rgba(31,231,184,0.52) !important;
    box-shadow: 0 2px 12px rgba(31,231,184,0.15) !important;
    transform: translateY(-1px) !important;
}}

/* Divisor de seção dentro do formulário */
.form-section-label {{
    color: {COLORS['text_muted']};
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 1.25rem 0 0.2rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid rgba(31,231,184,0.1);
    display: flex;
    align-items: center;
    gap: 6px;
}}
.form-section-label::before {{
    content: "";
    width: 4px; height: 4px;
    border-radius: 50%;
    background: {COLORS['aqua']};
    opacity: 0.55;
    display: inline-block;
    flex-shrink: 0;
}}
.form-section-label:first-child {{
    margin-top: 0;
}}

/* Hero header das páginas de formulário */
.page-hero {{
    text-align: center;
    margin: 1.8rem 0 1.5rem;
}}
.page-hero-icon {{
    width: 56px; height: 56px;
    border-radius: 16px;
    background: rgba(31,231,184,0.1);
    border: 1px solid rgba(31,231,184,0.22);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 0 28px rgba(31,231,184,0.12);
}}
.page-hero-title {{
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 1.72rem;
    letter-spacing: -0.02em;
    color: {COLORS['text']};
    margin-bottom: 0.2rem;
}}
.page-hero-title span {{
    color: {COLORS['aqua']};
    text-shadow: 0 0 18px rgba(31,231,184,0.38);
}}
.page-hero-subtitle {{
    color: {COLORS['text_muted']};
    font-size: 0.83rem;
    letter-spacing: 0.05em;
}}

/* Espaçador antes do botão de submit */
.form-submit-spacer {{
    margin-top: 1.4rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(31,231,184,0.08);
}}
</style>
"""
    st.markdown(_flush(css), unsafe_allow_html=True)


def _icon_chip(icon: str, bg: str, color: str) -> str:
    return f'<div class="kpi-icon" style="background:{bg}; color:{color};">{icon}</div>'


def kpi_card(
    label: str,
    value: str,
    caption: str = "",
    icon: str = "📌",
    icon_bg: str = "rgba(31,231,184,0.12)",
    icon_color: str = "#1FE7B8",
    pill_text: str = "",
    pill_bg: str = "rgba(31,231,184,0.14)",
    pill_color: str = "#1FE7B8",
) -> str:
    pill_html = (
        f'<div class="kpi-pill" style="background:{pill_bg}; color:{pill_color};">{pill_text}</div>'
        if pill_text
        else ""
    )
    icon_html = _icon_chip(icon, icon_bg, icon_color) if icon else ""
    
    html = f"""
<div class="kpi-card">
{icon_html}
<div class="kpi-label">{label}</div>
<div class="kpi-value">{value}</div>
<div class="kpi-caption">{caption}</div>
{pill_html}
</div>
"""
    return _flush(html)


def render_oficinas_table(df_oficinas: pd.DataFrame, top_n: int = 8) -> str:
    """Monta uma tabela HTML personalizada com as oficinas que mais geram
    ocorrências: cabeçalho verde, zebra-striping suave, barra de proporção
    e badge de ranking."""
    data = df_oficinas.head(top_n).reset_index(drop=True)
    max_qtd = data["QTD"].max() if len(data) else 1

    badge_colors = ["#1FE7B8", "#5BEFD1", "#8CE99A"] + ["#2C3E46"] * 10

    rows = []
    for i, row in data.iterrows():
        pct_bar = max(int(row["QTD"] / max_qtd * 100), 6)
        status_tag = (
            '<span class="tag" style="background:rgba(224,102,122,0.15); color:#E0667A;">Reincidente</span>'
            if row["QTD"] >= 2
            else '<span class="tag" style="background:rgba(140,233,154,0.15); color:#8CE99A;">Pontual</span>'
        )
        rows.append(
            f"""<tr>
<td><span class="rank-badge" style="background:{badge_colors[i]};">{i + 1}</span></td>
<td>{row['OFICINA']}</td>
<td>
<div style="display:flex; align-items:center; gap:10px;">
<div class="bar-track" style="max-width:140px;"><div class="bar-fill" style="width:{pct_bar}%;"></div></div>
<span style="color:#7F93A0; font-size:0.78rem;">{row['QTD']}</span>
</div>
</td>
<td>{status_tag}</td>
</tr>"""
        )
    rows_html = "\n".join(rows)

    html = f"""
<div class="custom-table-wrap">
<table class="custom-table">
<thead>
<tr>
<th>#</th>
<th>Oficina</th>
<th>Ocorrências</th>
<th>Status</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
"""
    return _flush(html)


def render_dados_table(df: pd.DataFrame, causa_colors: dict | None = None) -> str:
    """Monta a tabela HTML da base completa de dados tratados, no mesmo
    padrão visual das demais tabelas do dashboard (cabeçalho verde,
    zebra-striping, bordas arredondadas) — com cabeçalho fixo e rolagem,
    já que pode conter muitas linhas. Datas em formato pt-BR (dd/mm/yyyy)
    e a causa exibida como uma tag colorida (mesma cor do gráfico de
    colunas, quando o mapeamento é informado)."""
    causa_colors = causa_colors or {}

    rows = []
    for _, row in df.iterrows():
        data_fmt = pd.to_datetime(row["DATA"]).strftime("%d/%m/%Y")
        causa = str(row["CAUSA"])
        cor = causa_colors.get(causa, COLORS["aqua"])
        oficina_safe = html.escape(str(row["OFICINA"]))
        descricao_safe = html.escape(str(row["DESCRICAO"]))
        om_safe = html.escape(str(row["OM"]))
        rows.append(
            f"""<tr>
<td style="color:{COLORS['text_dim']}; white-space:nowrap;">{om_safe}</td>
<td style="white-space:nowrap;">{oficina_safe}</td>
<td style="color:{COLORS['text_dim']}; white-space:nowrap;">{data_fmt}</td>
<td><span class="tag" style="background:{cor}22; color:{cor};">{html.escape(causa)}</span></td>
<td style="color:{COLORS['text_dim']}; max-width:420px;">{descricao_safe}</td>
</tr>"""
        )
    rows_html = "\n".join(rows)

    table_html = f"""
<div class="scrollable-table-wrap">
<table class="custom-table">
<thead>
<tr>
<th>OM</th>
<th>Oficina</th>
<th>Data</th>
<th>Causa</th>
<th>Descrição</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
"""
    return _flush(table_html)


def render_outros_descricoes_table(df: pd.DataFrame) -> str:
    """Tabela com as descrições mais frequentes dentro da causa 'Outros',
    para identificar candidatas a novas palavras-chave em CAUSE_RULES."""
    rows = []
    for _, row in df.iterrows():
        descricao_safe = html.escape(str(row["DESCRICAO"]))
        rows.append(
            f"""<tr>
<td style="color:{COLORS['text']}; max-width:540px;">{descricao_safe}</td>
<td style="color:{COLORS['aqua']}; font-weight:700; text-align:right; white-space:nowrap;">{int(row['QTD'])}</td>
</tr>"""
        )
    rows_html = "\n".join(rows)
    table_html = f"""
<div class="custom-table-wrap">
<table class="custom-table">
<thead>
<tr>
<th>Descrição (sem categoria definida)</th>
<th style="text-align:right;">Qtd</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
"""
    return _flush(table_html)


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _interp_color(c_low: str, c_high: str, t: float) -> str:
    """Interpola linearmente entre duas cores hex (t entre 0 e 1)."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = _hex_to_rgb(c_low)
    r2, g2, b2 = _hex_to_rgb(c_high)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def value_color_scale(values, c_low: str = "#1A4A40", c_high: str = None) -> list:
    """Gera uma cor por valor, interpolando entre c_low e c_high de acordo
    com a posição do valor no intervalo [min, max] — usado para colorir
    barras de ranking proporcionalmente (igual ao colorscale do Plotly)."""
    c_high = c_high or COLORS["aqua"]
    values = list(values)
    if not values:
        return []
    v_min, v_max = min(values), max(values)
    span = (v_max - v_min) or 1
    return [_interp_color(c_low, c_high, (v - v_min) / span) for v in values]


def echarts_tooltip_style() -> dict:
    """Estilo padrão de tooltip — visual 'moderno' (cantos arredondados,
    leve blur/sombra, padding confortável) — reaproveitado em todos os
    gráficos ECharts para manter a mesma identidade visual dark/aqua."""
    return dict(
        backgroundColor="rgba(13,20,26,0.96)",
        borderColor=COLORS["border_strong"],
        borderWidth=1,
        borderRadius=10,
        padding=[10, 14],
        confine=True,
        textStyle=dict(color=COLORS["text"], fontSize=12, fontFamily="Inter, sans-serif"),
        extraCssText=(
            "box-shadow: 0 12px 28px rgba(0,0,0,0.45); "
            "backdrop-filter: blur(6px); line-height: 1.5;"
        ),
    )


def render_echart(option: dict, height: int = 380, js_formatters: dict | None = None) -> None:
    """Renderiza um gráfico Apache ECharts dentro de um componente HTML.

    Não depende de nenhum pacote Python extra (streamlit-echarts etc.) —
    apenas carrega a biblioteca echarts.js via CDN no navegador do usuário
    e desenha o gráfico a partir do dicionário de opções (mesmo formato
    usado pelo ECharts em JS).

    `js_formatters` permite injetar funções JS reais (ex.: tooltip.formatter
    com marcador colorido, percentual calculado etc.) — algo que o JSON puro
    não suporta. Basta colocar um placeholder string (ex. "__MEU_FORMATTER__")
    no dict de opções e passar aqui o código JS correspondente; a troca é
    feita no texto já serializado, antes de ir para o navegador.
    """
    option_json = json.dumps(option, ensure_ascii=False, default=str)
    if js_formatters:
        for placeholder, js_code in js_formatters.items():
            option_json = option_json.replace(f'"{placeholder}"', js_code)
    chart_id = f"echart_{abs(hash(option_json)) % (10 ** 9)}_{height}"
    html = f"""
<div id="{chart_id}" style="width:100%; height:{height}px;"></div>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>
(function() {{
    var el = document.getElementById("{chart_id}");
    if (!el || typeof echarts === "undefined") return;
    var chart = echarts.init(el, null, {{renderer: "svg"}});
    chart.setOption({option_json});
    var ro = new ResizeObserver(function() {{ chart.resize(); }});
    ro.observe(el);
    window.addEventListener("resize", function() {{ chart.resize(); }});
}})();
</script>
"""
    components.html(html, height=height + 12, scrolling=False)
