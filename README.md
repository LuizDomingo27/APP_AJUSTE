# Sistema de Ajustes & Ocorrências — Resumo Executivo

Dashboard em Streamlit para análise de retrabalho por oficina. O usuário envia a
planilha (.xlsx/.xls/.csv) e o app trata os dados, classifica as causas e monta
o resumo executivo com os indicadores pedidos pela gestão.

## Como rodar

```bash
cd oficinas_dashboard
pip install -r requirements.txt
streamlit run app.py
```

O tema visual (verde neon aqua, fundo escuro, bordas suaves) já está aplicado via
`.streamlit/config.toml` e CSS customizado em `utils/style.py`.

## Estrutura

```
oficinas_dashboard/
├── app.py                  # App principal (upload, filtros, KPIs, gráficos)
├── requirements.txt
├── .streamlit/config.toml  # Tema dark + verde neon aqua
└── utils/
    ├── data_processor.py   # Leitura, normalização de colunas, classificação de causas, KPIs
    └── style.py            # CSS, cards e tabela HTML personalizada, paleta dos gráficos
```

## Colunas esperadas na planilha

| Coluna esperada | Variações reconhecidas automaticamente |
|---|---|
| OM | om, ordem, id |
| OFICINA | oficina, fornecedor, parceiro |
| DATA | data, dt |
| DESCRIÇÃO/OBS | descrição obs, obs, motivo, causa |

## Indicadores entregues (conforme solicitado)

1. **Total de ocorrências** — card no topo.
2. **Principal causa** — card com quantidade e % do total.
3. **Segunda maior causa** — card com quantidade e % do total.
4. **% de causas financeiras** (Descontos, Balanceamento, Valor Unitário, Reembolso) — card dedicado.
5. **Oficinas com reincidência** (≥ 2 ocorrências) — card dedicado.
6. **Tabela das principais oficinas** — HTML personalizado, com ranking, barra de proporção e status (Reincidente/Pontual).
7. **Gráfico de oficinas com maior quantidade de ajustes** — barra horizontal (Plotly).
8. **Gráfico de causas de retrabalho** — donut (Plotly), com legenda e destaque da causa líder.
9. **Gráfico de sazonalidade** — linha diária de ocorrências + média móvel de 3 dias (tendência), em Plotly.

Filtros de período e de oficina estão disponíveis na barra lateral, e a base
tratada (com a causa já classificada) pode ser inspecionada no expander no
final da página.

## Regra de classificação de causas

A causa é inferida a partir do texto da observação (`DESCRIÇÃO OBS`), em
`utils/data_processor.py`, função `classify_cause`. As regras são por palavra-chave
e podem ser ajustadas/expandidas facilmente nessa lista (`CAUSE_RULES`) conforme
o vocabulário real for evoluindo.
