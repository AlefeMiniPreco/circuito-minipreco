# -*- coding: utf-8 -*-
# circuito_lojas_app.py — versão com novas regras de cálculo e ícone animado

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from io import BytesIO

# ----------------------------------------------------------------------
# Configuração inicial do Streamlit
# ----------------------------------------------------------------------
st.set_page_config(page_title="Circuito MiniPreço", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------------------------------------------------
# Fonte de dados: GitHub (raw)
# ----------------------------------------------------------------------
GITHUB_FILE_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/BaseCircuito.xlsx"

def get_data_from_github():
    """Baixa o arquivo BaseCircuito.xlsx direto do GitHub e retorna como dict de DataFrames."""
    try:
        df = pd.read_excel(GITHUB_FILE_URL, sheet_name=None, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados do GitHub: {e}")
        return {}

# ----------------------------------------------------------------------
# Constantes do arquivo
# ----------------------------------------------------------------------
ETAPA_SHEETS = [
    "PlanoVoo", "ProjetoFast", "PontoPartida", "AcoesComerciais", "PainelVendas",
    "Engajamento", "VisualMerchandising", "ModeloAtendimento", "EvolucaoComercial",
    "Qualidade", "Meta"
]
# Etapas com score mensal (baseado no ciclo)
MONTHLY_ETAPAS = ["Engajamento", "VisualMerchandising", "Meta"]
# Etapas "coringa" que não contam para o total de minutos do circuito
JOKER_ETAPAS = ["Meta"]

PREMIO_TOP1 = "Bônus Ouro + Folga"
PREMIO_TOP3 = "Bônus Prata"
PREMIO_TOP5 = "Bônus Bronze"
PREMIO_DEMAIS = "Reconhecimento + Plano de Ação"

# ----------------------------------------------------------------------
# CSS (visuais)
# ----------------------------------------------------------------------
st.markdown("""
<style>
.app-header { text-align: center; margin-top: -18px; margin-bottom: 6px; }
.app-header h1 { font-size: 34px !important; margin: 0; letter-spacing: 0.6px; color: #ffffff; font-weight: 800; text-shadow: 0 3px 10px rgba(0,0,0,0.6); }
.app-header p { margin: 4px 0 0 0; color: rgba(255,255,255,0.85); font-size: 14px; }
.podio-track { width: 100%; border-collapse: collapse; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; margin-bottom: 16px; }
.podio-track thead th { background: linear-gradient(90deg,#0b1220 0%, #131a25 100%); color: #fff; padding: 12px; text-align: left; font-size: 14px; border-bottom: 3px solid rgba(255,255,255,0.06); }
.podio-track tbody tr { transition: transform 0.18s ease, box-shadow 0.18s ease; height: 56px; }
.podio-track tbody tr:hover { transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.45); }
.podio-lane { width: 80px; font-weight: 700; font-size: 16px; color: #111827; text-align: center; background: linear-gradient(180deg,#f7fafc,#e6edf3); border-right: 2px solid rgba(0,0,0,0.04); }
.podio-row { background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); color: inherit; }
.podio-col-loja { padding: 12px; font-weight: 800; font-size: 15px; color: #0f172a; background: linear-gradient(90deg, rgba(255,255,255,0.88), rgba(255,255,255,0.95)); border-radius: 6px; display: inline-block; padding-left: 14px; padding-right: 14px; }
.podio-col-points { padding: 12px; font-size: 14px; text-align: center; color: #e6edf3; font-weight:700; }
.podio-finish { min-width: 140px; text-align: center; padding: 8px; font-weight: 700; color: #0f172a; background: linear-gradient(90deg,#fff 0%, #e6f4ea 100%); border-radius: 8px; display: inline-block; }
.checkered { background-image: linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000), linear-gradient(45deg, #000 25%, transparent 25%, transparent 75%, #000 75%, #000); background-size: 12px 12px; background-position: 0 0, 6px 6px; width: 28px; height: 28px; display:inline-block; margin-right:8px; vertical-align: middle; border-radius:4px; box-shadow: 0 4px 12px rgba(0,0,0,0.25); }
.podio-prize { padding: 8px 10px; border-radius: 8px; display:inline-block; font-weight:700; color: #111827; }
.gold { background: linear-gradient(90deg,#ffd54a,#f1c40f); }
.silver { background: linear-gradient(90deg,#cfd8dc,#b0bec5); }
.bronze { background: linear-gradient(90deg,#d7a77a,#c07a47); }
.other { background: linear-gradient(90deg,#edf2f7,#e2e8f0); color:#0f172a; }
.metric-card { background: linear-gradient(135deg, #2c3e50, #4a6580); border-radius: 16px; padding: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.15); text-align: center; transition: all 0.3s ease; height: 100%; color: white; }
.metric-card:hover { transform: translateY(-5px); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }
.metric-value { font-size: 32px; font-weight: 800; margin: 10px 0; color: white; text-shadow: 0 2px 8px rgba(0,0,0,0.3); }
.metric-label { font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 5px; }
@media (max-width: 900px) { .podio-lane { display:none; } .podio-track thead th:nth-child(1), .podio-track tbody td:nth-child(1) { display:none; } }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Utilitários
# ----------------------------------------------------------------------
def get_period_range(ciclo: str, selected_periods: list, periodos_df: pd.DataFrame):
    if not ciclo or periodos_df is None or periodos_df.empty:
        return None, None
    ciclo_df = periodos_df[periodos_df["Ciclo"].astype(str) == str(ciclo)].reset_index(drop=True)
    if ciclo_df.empty:
        return None, None
    ordered_periods = ciclo_df["Periodo"].astype(str).tolist()
    if not selected_periods or "Todos" in selected_periods:
        return ordered_periods[0], ordered_periods[-1]
    selected_in_order = [p for p in ordered_periods if p in selected_periods]
    if not selected_in_order:
        return None, None
    return selected_in_order[0], selected_in_order[-1]

# ----------------------------------------------------------------------
# Render do pódio
# ----------------------------------------------------------------------
def render_podio_table(df_final: pd.DataFrame):
    if df_final is None or df_final.empty:
        st.info("Sem dados para exibir no pódio.")
        return

    winners = df_final[df_final["Progresso"] >= 100.0].sort_values("Rank").reset_index(drop=True)

    if winners.empty:
        st.markdown("Nenhuma loja cruzou a linha de chegada. Top 3 do ranking atual:")
        top3 = df_final.head(3).reset_index(drop=True)
        cols = st.columns(3)
        for i in range(3):
            if i < len(top3):
                row = top3.loc[i]
                nome = row["Nome_Exibicao"]; pontos = row["Pontos_Totais"]; progresso = row["Progresso"]; rank = row["Rank"]
                with cols[i]:
                    st.markdown(
                        f"<div style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0f172a,#111827);color:white; text-align:center;'>"
                        f"<h3 style='margin:0'>{i+1}º — {nome}</h3>"
                        f"<p style='margin:6px 0 0 0; opacity:0.85'>Rank: #{rank}</p>"
                        f"<h2 style='margin:8px 0 0 0'>{pontos:.1f} min</h2>"
                        f"<p style='margin:6px 0 0 0; font-size:14px; opacity:0.85'>Progresso: {progresso:.1f}%</p>"
                        f"</div>", unsafe_allow_html=True
                    )
            else:
                with cols[i]:
                    st.markdown(
                        "<div style='padding:18px; border-radius:12px; background:rgba(255,255,255,0.03);color:#fff; text-align:center; opacity:0.5;'>"
                        f"<h3 style='margin:0'>{i+1}º</h3><p style='margin:6px 0 0 0; opacity:0.7'>—</p></div>",
                        unsafe_allow_html=True
                    )
        return

    html_table = []
    html_table.append("<table class='podio-track' role='table'>")
    html_table.append("<thead><tr>")
    html_table.append("<th style='width:80px;'>#</th>")
    html_table.append("<th>Loja</th>")
    html_table.append("<th style='width:120px; text-align:center;'>Minutos</th>")
    html_table.append("<th style='width:140px; text-align:center;'>Progresso</th>")
    html_table.append("<th style='width:220px; text-align:center;'>Premiação</th>")
    html_table.append("</tr></thead><tbody>")

    for _, row in winners.iterrows():
        pos = int(row["Rank"]); nome = row["Nome_Exibicao"]; pontos = row["Pontos_Totais"]; progresso = row["Progresso"]
        if pos == 1:
            premio = PREMIO_TOP1; premio_class = "gold"
        elif pos in (2, 3):
            premio = PREMIO_TOP3; premio_class = "silver"
        elif pos in (4, 5):
            premio = PREMIO_TOP5; premio_class = "bronze"
        else:
            premio = PREMIO_DEMAIS; premio_class = "other"

        lane_html = f"<td class='podio-lane'>{pos}º</td>"
        loja_html = f"<td><span class='podio-col-loja'>{nome}</span></td>"
        pontos_html = f"<td class='podio-col-points'>{pontos:.1f} min</td>"
        progresso_html = f"<td style='text-align:center; padding:12px;'><div class='podio-finish'><span class='checkered'></span> {progresso:.1f}%</div></td>"
        premio_html = f"<td style='text-align:center;'><span class='podio-prize {premio_class}'>{premio}</span></td>"

        html_table.append(f"<tr class='podio-row'>{lane_html}{loja_html}{pontos_html}{progresso_html}{premio_html}</tr>")

    html_table.append("</tbody></table>")
    st.markdown("### Pódio — Lojas que cruzaram a linha de chegada", unsafe_allow_html=True)
    st.markdown("".join(html_table), unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Carregamento & preparação de dados
# ----------------------------------------------------------------------
def load_and_prepare_data(all_sheets: dict):
    """
    Processa o dicionário de DataFrames obtido do Excel e
    retorna os DataFrames necessários para o app.
    """
    all_data = []
    etapas_info_total = {}
    periodos_pesos_records = []
    etapas_pesos_records = []

    for sheet_name in ETAPA_SHEETS:
        if sheet_name in all_sheets:
            try:
                df_etapa = all_sheets[sheet_name]
                df_etapa.columns = [c.strip() for c in df_etapa.columns]

                # Valida se as colunas essenciais estão presentes.
                if not all(col in df_etapa.columns for col in ['NomeLoja','loja_key','Nota','Ciclo','Período']):
                    continue

                # Normaliza tipos
                df_etapa['Ciclo'] = df_etapa['Ciclo'].astype(str)
                df_etapa['Período'] = df_etapa['Período'].astype(str)

                df_etapa = df_etapa.rename(columns={'loja_key': 'Loja', 'NomeLoja': 'Nome_Exibicao', 'Período': 'Periodo'})
                # Converte Nota para numérico, mantendo NaNs para notas nulas
                df_etapa['Score_Etapa'] = pd.to_numeric(df_etapa['Nota'], errors='coerce')

                # Consolida os dados da etapa.
                df_consolidado = df_etapa[['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo', 'Score_Etapa']].copy()
                df_consolidado.rename(columns={'Score_Etapa': f'{sheet_name}_Score'}, inplace=True)
                all_data.append(df_consolidado)

                # Coleta informações de peso para cada etapa e período.
                if 'PesoDaEtapa' in df_etapa.columns:
                    total_peso_sheet = pd.to_numeric(df_etapa['PesoDaEtapa'], errors='coerce').fillna(0.0).sum()
                    etapas_info_total[f'{sheet_name}_Score'] = float(total_peso_sheet)

                    pesos_gp = df_etapa.groupby(['Ciclo','Periodo'])['PesoDaEtapa'].sum().reset_index()
                    pesos_gp['Etapa'] = f'{sheet_name}_Score'
                    for _, r in pesos_gp.iterrows():
                        etapas_pesos_records.append({'Etapa': r['Etapa'], 'Ciclo': str(r['Ciclo']), 'Periodo': str(r['Periodo']), 'PesoDaEtapa': float(r['PesoDaEtapa'])})

                    # **NOVA REGRA**: Etapas "coringa" não contam para o total de minutos.
                    if sheet_name not in JOKER_ETAPAS:
                        for _, r in df_etapa.groupby(['Ciclo','Periodo'])['PesoDaEtapa'].sum().reset_index().iterrows():
                            periodos_pesos_records.append({'Ciclo': str(r['Ciclo']), 'Periodo': str(r['Periodo']), 'PesoDaEtapa': float(r['PesoDaEtapa'])})

            except Exception:
                continue

    if not all_data:
        return pd.DataFrame(), [], {}, pd.DataFrame(), [], pd.DataFrame(), pd.DataFrame()

    # Combina todos os DataFrames de etapa em um único DataFrame.
    combined_df = all_data[0]
    for i in range(1, len(all_data)):
        combined_df = pd.merge(combined_df, all_data[i], on=['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo'], how='outer')

    # Ordena o DataFrame combinado.
    month_order = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    combined_df['Ciclo'] = combined_df['Ciclo'].astype(str)
    combined_df['Periodo'] = combined_df['Periodo'].astype(str)
    combined_df['Ciclo_Cat'] = pd.Categorical(combined_df['Ciclo'], categories=month_order, ordered=True)
    combined_df = combined_df.sort_values(['Ciclo_Cat','Periodo','Nome_Exibicao']).reset_index(drop=True)

    # **NOVA REGRA**: Propaga scores de etapas mensais para todos os períodos do ciclo.
    for etapa in MONTHLY_ETAPAS:
        score_col = f"{etapa}_Score"
        if score_col in combined_df.columns:
            # Usa a nota máxima da loja no ciclo e aplica a todos os períodos.
            combined_df[score_col] = combined_df.groupby(['Loja', 'Ciclo'])[score_col].transform('max')

    etapas_scores = [c for c in combined_df.columns if c.endswith('_Score')]

    # Prepara os DataFrames de pesos.
    periodos_df = combined_df[["Ciclo","Periodo","Ciclo_Cat"]].drop_duplicates().sort_values(["Ciclo_Cat","Periodo"]).reset_index(drop=True)
    periodos_formatados = [f"{row['Ciclo']} - {row['Periodo']}" for _, row in periodos_df.iterrows()]

    if periodos_pesos_records:
        periodos_pesos_df = pd.DataFrame(periodos_pesos_records).groupby(['Ciclo','Periodo'], as_index=False)['PesoDaEtapa'].sum()
    else:
        periodos_pesos_df = pd.DataFrame(columns=['Ciclo','Periodo','PesoDaEtapa'])

    if etapas_pesos_records:
        etapas_pesos_df = pd.DataFrame(etapas_pesos_records).groupby(['Etapa','Ciclo','Periodo'], as_index=False)['PesoDaEtapa'].sum()
    else:
        etapas_pesos_df = pd.DataFrame(columns=['Etapa','Ciclo','Periodo','PesoDaEtapa'])

    return combined_df, etapas_scores, etapas_info_total, periodos_df, periodos_formatados, periodos_pesos_df, etapas_pesos_df

# ----------------------------------------------------------------------
# Cálculo de pontuação final
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas: list, max_minutos_total: float):
    df = df.copy()
    for e in etapas:
        if e not in df.columns:
            df[e] = 0.0
    # Na soma total, NaNs são tratados como 0, o que está correto para o cálculo.
    df["Pontos_Totais"] = df[etapas].sum(axis=1)
    max_p = max_minutos_total if max_minutos_total and max_minutos_total > 0 else (df["Pontos_Totais"].max() if not df.empty else 0)
    df["Progresso"] = (df["Pontos_Totais"] / max_p) * 100.0 if max_p > 0 else 0.0
    df["Rank"] = df["Pontos_Totais"].rank(method="dense", ascending=False).astype(int)
    df.sort_values(["Pontos_Totais","Nome_Exibicao"], ascending=[False,True], inplace=True)
    df = df.reset_index(drop=True)
    return df

# ----------------------------------------------------------------------
# Helpers para somar pesos
# ----------------------------------------------------------------------
def get_circuit_total(periodos_pesos_df: pd.DataFrame, ciclo: str, selected_periodos: list | None):
    if periodos_pesos_df is None or periodos_pesos_df.empty or ciclo is None:
        return 0.0
    df = periodos_pesos_df[periodos_pesos_df["Ciclo"].astype(str) == str(ciclo)].copy()
    if df.empty:
        return 0.0
    if not selected_periodos or "Todos" in selected_periodos:
        return float(df["PesoDaEtapa"].sum())
    df = df[df["Periodo"].astype(str).isin([str(p) for p in selected_periodos])]
    return float(df["PesoDaEtapa"].sum())

def get_etapa_pesos_for_selection(etapas_pesos_df: pd.DataFrame, ciclo: str, selected_periodos: list | None):
    if etapas_pesos_df is None or etapas_pesos_df.empty or ciclo is None:
        return {}
    df = etapas_pesos_df[etapas_pesos_df["Ciclo"].astype(str) == str(ciclo)].copy()
    if df.empty:
        return {}
    if not selected_periodos or "Todos" in selected_periodos:
        gp = df.groupby("Etapa", as_index=False)["PesoDaEtapa"].sum()
    else:
        gp = df[df["Periodo"].astype(str).isin([str(p) for p in selected_periodos])].groupby("Etapa", as_index=False)["PesoDaEtapa"].sum()
    return {row["Etapa"]: float(row["PesoDaEtapa"]) for _, row in gp.iterrows()}

# ----------------------------------------------------------------------
# Filtragem e agregação
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def filter_and_score_multi(data_original: pd.DataFrame, etapas: list, periodos_pesos_df: pd.DataFrame, etapas_pesos_df: pd.DataFrame, ciclo: str | None, periodos: list | None):
    if ciclo is None or periodos is None:
        return pd.DataFrame()
    df = data_original[data_original["Ciclo"].astype(str) == str(ciclo)].copy()
    if df.empty:
        return pd.DataFrame()
    if "Todos" not in periodos:
        df = df[df["Periodo"].astype(str).isin([str(p) for p in periodos])]
    if df.empty:
        return pd.DataFrame()
    score_cols = [c for c in df.columns if c.endswith('_Score')]
    if not score_cols:
        return pd.DataFrame()
    max_minutos = get_circuit_total(periodos_pesos_df, ciclo, periodos)
    
    # **NOVA REGRA**: Agrega com sum(min_count=1) para preservar NaNs se todas as notas de um grupo forem nulas
    aggregated = df.groupby(['Loja','Nome_Exibicao'], as_index=False)[score_cols].sum(min_count=1)
    
    aggregated['Ciclo'] = ciclo
    final = calculate_final_scores(aggregated, score_cols, max_minutos)
    return final

@st.cache_data(show_spinner=False)
def warm_cache_all_periods(data_original: pd.DataFrame, etapas: list, periodos_pesos_df: pd.DataFrame, periodos_df: pd.DataFrame):
    if periodos_df.empty:
        _ = calculate_final_scores(data_original, etapas, 0.0)
        return 1
    count = 0
    for _, row in periodos_df.iterrows():
        _ = filter_and_score_multi(data_original, etapas, periodos_pesos_df, None, str(row["Ciclo"]), [str(row["Periodo"])])
        count += 1
    return count

# ----------------------------------------------------------------------
# Visual: pista (COM ÍCONE ANIMADO)
# ----------------------------------------------------------------------
def build_pista_fig(data: pd.DataFrame, max_minutos: float = None) -> go.Figure:
    if data is None or data.empty:
        return go.Figure()

    # --- IMPORTANTE: COLE AQUI A URL "RAW" DO SEU GIF ---
    # Substitua 'SeuUsuario' e 'seu-repositorio' pelos dados corretos do seu GitHub.
    CAR_ICON_URL = "https://github.com/AlefeMiniPreco/circuito-minipreco/blob/692666deadc68d3338c03a8e1e17426245a7a72e/assets/carro-corrida.gif"

    fig = go.Figure()
    num_lojas = len(data)
    y_positions = np.arange(num_lojas)

    if max_minutos is None or max_minutos == 0:
        max_minutos = data["Pontos_Totais"].max() if not data.empty else 100

    def escala_visual(x):
        return np.sqrt(x)

    max_vis = escala_visual(max_minutos)

    # Pista
    for y in y_positions:
        fig.add_shape(type="rect", x0=0, y0=y-0.45, x1=max_vis, y1=y+0.45,
                      line=dict(width=0), fillcolor="#2C3E50", layer="below")

    # Linha e bandeira de chegada
    fig.add_shape(type="line", x0=max_vis, y0=-1, x1=max_vis, y1=num_lojas,
                  line=dict(color="black", width=4, dash="solid"))
    for y in range(num_lojas + 2):
        if y % 2 == 0:
            fig.add_shape(type="rect", x0=max_vis-0.5, y0=y-1, x1=max_vis+0.5, y1=y,
                          line=dict(width=0), fillcolor="black", layer="below")
        else:
            fig.add_shape(type="rect", x0=max_vis-0.5, y0=y-1, x1=max_vis+0.5, y1=y,
                          line=dict(width=0), fillcolor="white", layer="below")

    # LÓGICA PARA INSERIR ÍCONE ANIMADO E RÓTULOS
    for y, row in zip(y_positions, data.itertuples()):
        x_carro = escala_visual(row.Pontos_Totais)
        
        # Adiciona a imagem animada do carro na posição correta
        fig.add_layout_image(
            dict(
                source=CAR_ICON_URL,
                xref="x",
                yref="y",
                x=x_carro,
                y=y,
                sizex=max_vis * 0.08,  # Ajuste o tamanho do carro conforme necessário
                sizey=0.8,             # Ajuste o tamanho do carro conforme necessário
                xanchor="center",
                yanchor="middle",
                layer="above"
            )
        )

        # Adiciona o rótulo com o nome da loja
        fig.add_trace(go.Scatter(
            x=[x_carro], 
            y=[y-0.5], 
            mode="text", 
            text=[row.Nome_Exibicao],
            textfont=dict(size=9, color="rgba(255,255,255,0.9)"), 
            hoverinfo="skip", 
            showlegend=False
        ))
        
        # Adiciona um ponto invisível para criar o hovertext (caixa de informações)
        hover = f"<b>{row.Nome_Exibicao}</b><br>Minutos: {row.Pontos_Totais:.1f}<br>Progresso: {row.Progresso:.1f}%<br>Rank: #{int(row.Rank)}"
        fig.add_trace(go.Scatter(
            x=[x_carro],
            y=[y],
            mode='markers',
            marker=dict(color='rgba(0,0,0,0)', size=25), # Marcador invisível
            hoverinfo='text',
            hovertext=hover,
            showlegend=False
        ))

    fig.update_yaxes(showgrid=False, zeroline=False, tickmode="array", tickvals=y_positions, ticktext=[])
    fig.update_xaxes(range=[0, max_vis * 1.05], title_text="Minutos percorridos (escala visual compactada) →")
    fig.update_layout(
        height=250 + 70*num_lojas, margin=dict(l=10, r=10, t=80, b=40),
        plot_bgcolor="#1A2A3A", paper_bgcolor="rgba(26,42,58,0.7)"
    )
    return fig


# ----------------------------------------------------------------------
# Lógica Principal do Aplicativo (renders)
# ----------------------------------------------------------------------
def render_header_and_periodo(campaign_name: str, periodo_inicio: str | None, periodo_fim: str | None):
    st.markdown("<div class='app-header'>", unsafe_allow_html=True)
    st.markdown(f"<h1>{campaign_name}</h1>", unsafe_allow_html=True)
    if periodo_inicio and periodo_fim:
        if periodo_inicio == periodo_fim:
            st.markdown(f"<p>{periodo_inicio} — Painel de acompanhamento do Circuito</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p>{periodo_inicio} → {periodo_fim} — Painel de acompanhamento do Circuito</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p>Período não definido — Painel de acompanhamento do Circuito</p>", unsafe_allow_html=True)
    st.markdown("---")

def render_geral_page():
    st.header("Visão Geral")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Sem dados para exibir com a seleção atual.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Lojas", len(df_final))
    with col2:
        top1 = df_final[df_final["Progresso"] >= 100.0]
        if not top1.empty:
            st.metric("Ganhador(es) do Bônus Ouro + Folga", f"{top1['Nome_Exibicao'].iloc[0]}")
        else:
            st.metric("Líder Atual", f"{df_final['Nome_Exibicao'].iloc[0]}")

    render_podio_table(df_final)

    st.markdown("### Pista de Corrida do Circuito")
    max_minutos = get_circuit_total(st.session_state.periodos_pesos_df, st.session_state.ciclo, st.session_state.periodos)
    fig_pista = build_pista_fig(df_final, max_minutos=max_minutos)
    st.plotly_chart(fig_pista, use_container_width=True)

    st.markdown("### Classificação Completa")
    df_classificacao = df_final.copy()
    etapa_columns = [col for col in df_classificacao.columns if col.endswith('_Score')]

    rename_dict = {col: f"{col.replace('_Score', '')} (min)" for col in etapa_columns}
    df_classificacao.rename(columns=rename_dict, inplace=True)

    final_columns = ['Rank', 'Nome_Exibicao'] + list(rename_dict.values()) + ['Pontos_Totais', 'Progresso']
    df_display = df_classificacao[final_columns].copy()

    # **NOVA REGRA**: Formata as colunas de score para exibir mensagem para notas nulas
    for col in list(rename_dict.values()):
        df_display[col] = df_display[col].apply(lambda x: f"{x:.1f} min" if pd.notna(x) else "Ainda sem nota imputada")

    df_display['Pontos_Totais'] = df_display['Pontos_Totais'].apply(lambda x: f"{x:.1f} min")
    df_display['Progresso'] = df_display['Progresso'].apply(lambda x: f"{x:.1f}%")

    st.dataframe(df_display, use_container_width=True, hide_index=True)

def render_loja_page():
    st.header("Visão por Loja")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Selecione um Ciclo e Período no menu lateral.")
        return

    loja_options = df_final["Nome_Exibicao"].unique().tolist()
    loja_sel = st.selectbox("Selecione a Loja:", sorted(loja_options))
    st.session_state.loja_sb_ui = loja_sel

    loja_row = df_final[df_final["Nome_Exibicao"] == loja_sel].iloc[0]
    st.markdown(f"**Loja Selecionada:** {loja_row['Nome_Exibicao']}")
    st.metric("Pontos Totais", f"{loja_row['Pontos_Totais']:.1f} min")
    st.metric("Progresso Total", f"{loja_row['Progresso']:.1f}%")
    st.metric("Rank", f"#{int(loja_row['Rank'])}")

    st.markdown("### Pontuação por Etapa")
    etapa_scores_df = loja_row.filter(regex='_Score').to_frame().T
    etapa_scores_df.columns = [c.replace('_Score','') for c in etapa_scores_df.columns]
    
    # **NOVA REGRA**: Formata para exibir mensagem para notas nulas também na visão por loja
    etapa_scores_df_display = etapa_scores_df.copy()
    for col in etapa_scores_df_display.columns:
        etapa_scores_df_display[col] = etapa_scores_df_display[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "Ainda sem nota imputada")
    
    st.dataframe(etapa_scores_df_display, use_container_width=True, hide_index=True)

def render_etapa_page():
    st.header("Visão por Etapa")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Selecione um Ciclo e Período no menu lateral.")
        return

    etapa_options = [c.replace('_Score', '') for c in st.session_state.etapas_scores]
    etapa_sel = st.selectbox("Selecione a Etapa:", sorted(etapa_options))
    st.session_state.etapa_selected = etapa_sel

    col_name = f"{etapa_sel}_Score"

    if col_name not in df_final.columns:
        st.warning(f"Dados para a etapa '{etapa_sel}' não encontrados.")
        return

    df_etapa = df_final[['Nome_Exibicao', col_name]].copy().rename(columns={col_name:"Pontuação"}).sort_values("Pontuação", ascending=False)
    # Remove lojas sem pontuação (NaN) da visão de top 10
    df_etapa.dropna(subset=['Pontuação'], inplace=True)
    
    top10 = df_etapa.head(10)
    st.subheader(f"Top 10 da Etapa '{etapa_sel}'")
    st.dataframe(top10, use_container_width=True, hide_index=True)

    st.markdown("---")

# ----------------------------------------------------------------------
# Inicializações de sessão
# ----------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state.page = "Geral"
if 'ciclo' not in st.session_state: st.session_state.ciclo = None
if 'periodos' not in st.session_state: st.session_state.periodos = []
if 'data_original' not in st.session_state: st.session_state.data_original = pd.DataFrame()
if 'etapas_scores' not in st.session_state: st.session_state.etapas_scores = []
if 'etapas_info' not in st.session_state: st.session_state.etapas_info = {}
if 'periodos_df' not in st.session_state: st.session_state.periodos_df = pd.DataFrame()
if 'periodos_formatados' not in st.session_state: st.session_state.periodos_formatados = []
if 'df_final' not in st.session_state: st.session_state.df_final = pd.DataFrame()
if 'etapa_selected' not in st.session_state: st.session_state.etapa_selected = None
if 'loja_sb_ui' not in st.session_state: st.session_state.loja_sb_ui = None
if 'periodos_pesos_df' not in st.session_state: st.session_state.periodos_pesos_df = pd.DataFrame()
if 'etapas_pesos_df' not in st.session_state: st.session_state.etapas_pesos_df = pd.DataFrame()

# ----------------------------------------------------------------------
# Carregar dados (GitHub) e processar
# ----------------------------------------------------------------------
with st.spinner("Carregando dados do GitHub..."):
    all_sheets = get_data_from_github()
if not all_sheets:
    st.error("Não foi possível carregar os dados do GitHub.")
    st.stop()

with st.spinner("Processando dados..."):
    data, etapas_scores, etapas_info, periodos_df, periodos_formatados, periodos_pesos_df, etapas_pesos_df = load_and_prepare_data(all_sheets)

st.session_state.data_original = data
st.session_state.etapas_scores = etapas_scores
st.session_state.etapas_info = etapas_info
st.session_state.periodos_df = periodos_df
st.session_state.periodos_formatados = periodos_formatados
st.session_state.periodos_pesos_df = periodos_pesos_df
st.session_state.etapas_pesos_df = etapas_pesos_df
_ = warm_cache_all_periods(data, etapas_scores, periodos_pesos_df, periodos_df)

# ----------------------------------------------------------------------
# Sidebar (filtros e navegação)
# ----------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-retailhub.com/minipreco/096c9b29-4ac3-425f-8322-be76b794f040.webp", use_container_width=True)
    st.markdown("---")
    st.markdown("### Seleção de Ciclo e Período")
    periodos_df = st.session_state.get('periodos_df', pd.DataFrame())
    ciclos_unicos = periodos_df["Ciclo"].dropna().astype(str).unique().tolist() if not periodos_df.empty else []
    if not ciclos_unicos:
        st.error("Nenhum ciclo disponível nos dados.")
    else:
        ciclo_selecionado = st.selectbox("Selecione o Ciclo", sorted(ciclos_unicos), index=len(ciclos_unicos)-1)
        periodos_ciclo = periodos_df[periodos_df["Ciclo"].astype(str) == str(ciclo_selecionado)]["Periodo"].dropna().astype(str).unique().tolist()
        periodos_opcoes = ["Todos"] + list(periodos_ciclo)
        periodos_selecionados = st.multiselect("Selecione os Períodos", options=periodos_opcoes, default=["Todos"])
        st.session_state.ciclo = ciclo_selecionado
        st.session_state.periodos = periodos_selecionados

    st.markdown("---")
    st.markdown("### Navegação")
    if st.button("Visão Geral", use_container_width=True): st.session_state.page = "Geral"
    if st.button("Visão por Loja", use_container_width=True): st.session_state.page = "Loja"
    if st.button("Visão por Etapa", use_container_width=True): st.session_state.page = "Etapa"

# ----------------------------------------------------------------------
# Cálculo conforme seleção
# ----------------------------------------------------------------------
if st.session_state.ciclo and st.session_state.periodos is not None:
    df_to_render = filter_and_score_multi(
        st.session_state.data_original,
        st.session_state.etapas_scores,
        st.session_state.periodos_pesos_df,
        st.session_state.etapas_pesos_df,
        st.session_state.ciclo,
        st.session_state.periodos
    )
    st.session_state.df_final = pd.DataFrame() if (df_to_render is None or df_to_render.empty) else df_to_render
else:
    st.session_state.df_final = pd.DataFrame()

# ----------------------------------------------------------------------
# Header & Render de páginas
# ----------------------------------------------------------------------
periodo_inicio, periodo_fim = get_period_range(st.session_state.get('ciclo'), st.session_state.get('periodos', []), st.session_state.get('periodos_df', pd.DataFrame()))
render_header_and_periodo("Circuito MiniPreço", periodo_inicio, periodo_fim)

if st.session_state.page == "Geral":
    render_geral_page()
elif st.session_state.page == "Loja":
    render_loja_page()
elif st.session_state.page == "Etapa":
    render_etapa_page()
