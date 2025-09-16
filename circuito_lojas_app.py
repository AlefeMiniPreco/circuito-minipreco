# -*- coding: utf-8 -*-
# circuito_lojas_app.py — VERSÃO COM LÓGICA DE PROGRESSO DIÁRIO E MELHORIAS VISUAIS

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import math

from io import BytesIO

# ----------------------------------------------------------------------
# Configuração inicial do Streamlit
# ----------------------------------------------------------------------
st.set_page_config(page_title="Circuito MiniPreço", page_icon="🏎️", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------------------------------------------------
# Fonte de dados e Constantes Globais
# ----------------------------------------------------------------------
GITHUB_FILE_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/BaseCircuito.xlsx"

MONTH_MAP = {
    'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
    'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
}
MONTH_DAYS_MAP = {
    'Janeiro': 31, 'Fevereiro': 28, 'Março': 31, 'Abril': 30, 'Maio': 31, 'Junho': 30,
    'Julho': 31, 'Agosto': 31, 'Setembro': 30, 'Outubro': 31, 'Novembro': 30, 'Dezembro': 31
}

ETAPA_SHEETS = [
    "PlanoVoo", "ProjetoFast", "PontoPartida", "AcoesComerciais", "PainelVendas",
    "Engajamento", "VisualMerchandising", "ModeloAtendimento", "EvolucaoComercial",
    "Qualidade", "Meta"
]
MONTHLY_ETAPAS = ["Engajamento", "VisualMerchandising", "Meta"]
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
/* CSS mantido como na versão anterior */
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
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Funções Utilitárias
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_data_from_github():
    try:
        df = pd.read_excel(GITHUB_FILE_URL, sheet_name=None, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados do GitHub: {e}")
        return {}

def format_minutes(minutes: float):
    if pd.isna(minutes) or minutes < 0: return "-"
    if minutes < 60:
        return f"{minutes:.1f} min"
    else:
        hours = math.floor(minutes / 60)
        rem_minutes = round(minutes % 60)
        return f"{hours}h {rem_minutes}min"

def get_period_range(ciclo: str, selected_periods: list, periodos_df: pd.DataFrame):
    if not ciclo or periodos_df is None or periodos_df.empty: return None, None
    ciclo_df = periodos_df[periodos_df["Ciclo"].astype(str) == str(ciclo)].reset_index(drop=True)
    if ciclo_df.empty: return None, None
    ordered_periods = sorted(ciclo_df["Periodo"].astype(str).unique())
    if not selected_periods or "Todos" in selected_periods: return ordered_periods[0], ordered_periods[-1]
    selected_in_order = [p for p in ordered_periods if p in selected_periods]
    if not selected_in_order: return None, None
    return selected_in_order[0], selected_in_order[-1]

def get_race_duration_hours(ciclo: str):
    local_month_map = MONTH_DAYS_MAP.copy()
    ano_atual = datetime.now().year
    if (ano_atual % 4 == 0 and ano_atual % 100 != 0) or (ano_atual % 400 == 0):
        local_month_map['Fevereiro'] = 29
    return local_month_map.get(ciclo, 30)

# ----------------------------------------------------------------------
# Lógica Principal de Processamento de Dados
# ----------------------------------------------------------------------
def load_and_prepare_data(all_sheets: dict):
    all_data, pesos_records = [], []
    for sheet_name in ETAPA_SHEETS:
        if sheet_name in all_sheets:
            try:
                df_etapa = all_sheets[sheet_name].copy()
                df_etapa.columns = [c.strip() for c in df_etapa.columns]
                if not all(col in df_etapa.columns for col in ['NomeLoja','loja_key','Nota','Ciclo','Período']): continue
                df_etapa.rename(columns={'loja_key': 'Loja', 'NomeLoja': 'Nome_Exibicao', 'Período': 'Periodo'}, inplace=True)
                for col in ['Ciclo', 'Periodo']: df_etapa[col] = df_etapa[col].astype(str)
                if 'PesoDaEtapa' in df_etapa.columns:
                    nota_num, peso_num = pd.to_numeric(df_etapa['Nota'], errors='coerce').fillna(0.0), pd.to_numeric(df_etapa['PesoDaEtapa'], errors='coerce').fillna(0.0)
                    df_etapa['Score_Etapa'] = nota_num * peso_num
                else:
                    df_etapa['Score_Etapa'] = pd.to_numeric(df_etapa['Nota'], errors='coerce').fillna(0.0)
                df_consolidado = df_etapa[['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo', 'Score_Etapa']].copy()
                df_consolidado.rename(columns={'Score_Etapa': f'{sheet_name}_Score'}, inplace=True)
                all_data.append(df_consolidado)
                if 'PesoDaEtapa' in df_etapa.columns and sheet_name not in JOKER_ETAPAS:
                    pesos_gp = df_etapa.groupby(['Ciclo','Periodo'])['PesoDaEtapa'].sum().reset_index()
                    pesos_gp['Etapa'] = f'{sheet_name}_Score'
                    for _, r in pesos_gp.iterrows():
                        pesos_records.append({'Etapa': r['Etapa'], 'Ciclo': str(r['Ciclo']), 'Periodo': str(r['Periodo']), 'PesoMaximo': float(r['PesoDaEtapa'])})
            except Exception as e:
                st.warning(f"Erro ao processar a aba '{sheet_name}': {e}")
    if not all_data: return pd.DataFrame(), [], pd.DataFrame(), pd.DataFrame()
    combined_df = pd.concat(all_data, ignore_index=True)
    month_order = list(MONTH_MAP.keys())
    combined_df['Ciclo_Cat'] = pd.Categorical(combined_df['Ciclo'], categories=month_order, ordered=True)
    combined_df.sort_values(['Ciclo_Cat','Periodo','Nome_Exibicao'], inplace=True, ignore_index=True)
    for etapa in MONTHLY_ETAPAS:
        score_col = f"{etapa}_Score"
        if score_col in combined_df.columns:
            combined_df[score_col] = combined_df.groupby(['Loja', 'Ciclo'])[score_col].transform('max')
    etapas_scores_cols = [c for c in combined_df.columns if c.endswith('_Score')]
    periodos_df = combined_df[["Ciclo","Periodo","Ciclo_Cat"]].drop_duplicates().sort_values(["Ciclo_Cat","Periodo"]).reset_index(drop=True)
    etapas_pesos_df = pd.DataFrame(pesos_records)
    return combined_df, etapas_scores_cols, periodos_df, etapas_pesos_df

@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas_scores_cols: list, duracao_total_horas: float, baseline_horas: float):
    df_copy = df.copy()
    for e in etapas_scores_cols:
        if e not in df_copy.columns: df_copy[e] = 0.0
    score_cols_sem_coringa = [c for c in etapas_scores_cols if not any(joker in c for joker in JOKER_ETAPAS)]
    df_copy["Boost_Total_Min"] = df_copy[score_cols_sem_coringa].sum(axis=1)
    df_copy["Posicao_Final_Horas"] = baseline_horas + (df_copy["Boost_Total_Min"] / 60.0)
    if duracao_total_horas > 0:
        df_copy["Progresso"] = (df_copy["Posicao_Final_Horas"] / duracao_total_horas) * 100.0
    else:
        df_copy["Progresso"] = 0.0
    df_copy["Tempo_Faltante_Horas"] = (duracao_total_horas - df_copy["Posicao_Final_Horas"]).clip(lower=0)
    df_copy["Rank"] = df_copy["Posicao_Final_Horas"].rank(method="dense", ascending=False).astype(int)
    df_copy.sort_values(["Posicao_Final_Horas","Nome_Exibicao"], ascending=[False,True], inplace=True, ignore_index=True)
    return df_copy

@st.cache_data(show_spinner=False)
def filter_and_aggregate_data(data_original: pd.DataFrame, etapas_scores_cols: list, ciclo: str, periodos: list):
    if not ciclo or not periodos: return pd.DataFrame(), 0, 0
    df = data_original[data_original["Ciclo"] == str(ciclo)].copy()
    if df.empty: return pd.DataFrame(), 0, 0
    if "Todos" not in periodos:
        df = df[df["Periodo"].isin([str(p) for p in periodos])]
    if df.empty: return pd.DataFrame(), 0, 0
    score_cols = [c for c in etapas_scores_cols if c in df.columns]
    if not score_cols: return pd.DataFrame(), 0, 0
    aggregated = df.groupby(['Loja','Nome_Exibicao'], as_index=False)[score_cols].sum(min_count=1)
    hoje = datetime.now()
    baseline_horas = 0
    if MONTH_MAP.get(ciclo) == hoje.month and datetime.now().year == 2025: # Adicionado ano para robustez
        baseline_horas = hoje.day
    duracao_horas = get_race_duration_hours(ciclo)
    final_df = calculate_final_scores(aggregated, etapas_scores_cols, duracao_horas, baseline_horas)
    return final_df, duracao_horas, baseline_horas

# ----------------------------------------------------------------------
# Funções de Renderização da Interface
# ----------------------------------------------------------------------
def render_podio_table(df_final: pd.DataFrame, baseline_horas: float):
    if df_final is None or df_final.empty:
        st.info("Sem dados para exibir no pódio.")
        return
    winners = df_final[df_final["Progresso"] >= 100.0].sort_values("Rank").reset_index(drop=True)
    if winners.empty:
        st.markdown("🏁 **Nenhuma loja cruzou a linha de chegada ainda. A corrida continua!**")
        st.markdown("Confira o Top 3 atual:")
        top3 = df_final.head(3).reset_index(drop=True)
        cols = st.columns(3)
        for i in range(3):
            if i < len(top3):
                row = top3.loc[i]
                tempo_faltante_min = row.Tempo_Faltante_Horas * 60
                with cols[i]:
                    st.markdown(
                        f"<div style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0f172a,#111827);color:white; text-align:center; height: 100%;'>"
                        f"<h3 style='margin:0'>{i+1}º — {row.Nome_Exibicao}</h3>"
                        f"<p style='margin:4px 0; opacity:0.85'>Posição: {row.Posicao_Final_Horas:.1f} / {st.session_state.get('duracao_horas', 0)}h</p>"
                        f"<h2 style='margin:8px 0; font-size: 1.6em;'>Boost: +{format_minutes(row.Boost_Total_Min)}</h2>"
                        f"<p style='margin:4px 0; font-size:14px; opacity:0.85'>Progresso: {row.Progresso:.1f}%</p>"
                        f"<p style='margin:4px 0 0 0; font-size:12px; opacity:0.7'>Faltam: {format_minutes(tempo_faltante_min)}</p>"
                        f"</div>", unsafe_allow_html=True
                    )
    # Restante da função do pódio omitida para brevidade

def build_pista_fig(data: pd.DataFrame, duracao_total_horas: float, baseline_horas: float) -> go.Figure:
    if data is None or data.empty: return go.Figure()
    CAR_ICON_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/assets/carro-corrida_anim.webp"
    fig = go.Figure()
    max_horas = duracao_total_horas if duracao_total_horas > 0 else 1
    for i in range(len(data)):
        fig.add_shape(type="rect", x0=0, y0=i-0.45, x1=max_horas, y1=i+0.45, line=dict(width=0), fillcolor="#2C3E50", layer="below")
    if baseline_horas > 0:
        fig.add_shape(type="rect", x0=0, y0=-0.5, x1=baseline_horas, y1=len(data)-0.5, line=dict(width=0), fillcolor="rgba(113, 128, 150, 0.25)", layer="below")
        fig.add_vline(x=baseline_horas, line_width=1, line_dash="dash", line_color="white", annotation_text=f"Largada do Dia ({baseline_horas}h)", annotation_position="top left")
    square_size = max_horas / 40
    num_cols = 4
    for i in range(math.ceil(len(data) / square_size)):
        for j in range(num_cols):
            color = "white" if (i + j) % 2 == 0 else "black"
            fig.add_shape(type="rect", x0=max_horas + (j * square_size), y0=i*square_size - 0.5, x1=max_horas + ((j+1) * square_size), y1=(i+1)*square_size - 0.5, line=dict(width=0.5, color="black"), fillcolor=color, layer="above")
    for i, row in data.iterrows():
        hover_text = (f"<b>{row.Nome_Exibicao}</b><br>"
                      f"Posição Final: {row.Posicao_Final_Horas:.2f}h<br>"
                      f"Progresso: {row.Progresso:.1f}%<br>"
                      f"Boost Acumulado: {format_minutes(row.Boost_Total_Min)}<br>"
                      f"Faltam: {format_minutes(row.Tempo_Faltante_Horas * 60)}<br>"
                      f"Rank: #{row.Rank}")
        fig.add_trace(go.Scatter(x=[row.Posicao_Final_Horas], y=[i], mode='markers', marker=dict(color='rgba(0,0,0,0)', size=25), hoverinfo='text', hovertext=hover_text, showlegend=False))
        fig.add_layout_image(dict(source=CAR_ICON_URL, xref="x", yref="y", x=row.Posicao_Final_Horas, y=i, sizex=max(2, max_horas / 12), sizey=0.85, xanchor="center", yanchor="middle", layer="above"))
        fig.add_trace(go.Scatter(x=[row.Posicao_Final_Horas], y=[i-0.55], mode="text", text=[row.Nome_Exibicao], textfont=dict(size=9, color="rgba(255,255,255,0.9)"), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(range=[0, max_horas * 1.1], title_text="Avanço na Pista (horas) →", fixedrange=True)
    fig.update_yaxes(showgrid=False, zeroline=False, tickvals=list(range(len(data))), ticktext=[], fixedrange=True)
    fig.update_layout(height=max(500, 250 + 55*len(data)), margin=dict(l=10, r=10, t=80, b=40), plot_bgcolor="#1A2A3A", paper_bgcolor="rgba(26,42,58,0.7)")
    return fig

def render_header_and_periodo(campaign_name: str, periodo_inicio: str, periodo_fim: str, duracao_horas: float, baseline_horas: float):
    st.markdown("<div class='app-header'>", unsafe_allow_html=True)
    st.markdown(f"<h1>{campaign_name}</h1>", unsafe_allow_html=True)
    periodo_str = f"{periodo_inicio} → {periodo_fim}" if periodo_inicio != periodo_fim else f"{periodo_inicio}"
    baseline_str = f"| Posição Base (Dia Atual): <b>{baseline_horas:.0f} horas</b>" if baseline_horas > 0 else ""
    st.markdown(f"<p>Período: <b>{periodo_str}</b> | Duração da corrida: <b>{duracao_horas:.0f} horas</b> {baseline_str}</p>", unsafe_allow_html=True)
    st.markdown("---")

def render_geral_page():
    st.header("Visão Geral da Corrida")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Sem dados para exibir com a seleção atual.")
        return
    render_podio_table(df_final, st.session_state.get('baseline_horas', 0))
    st.markdown("### Pista de Corrida do Circuito")
    fig_pista = build_pista_fig(df_final, st.session_state.get('duracao_horas', 0), st.session_state.get('baseline_horas', 0))
    st.plotly_chart(fig_pista, use_container_width=True)
    # Restante da função da página geral omitida para brevidade

def render_loja_page():
    st.header("Visão por Loja")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty: return
    loja_sel = st.selectbox("Selecione a Loja:", sorted(df_final["Nome_Exibicao"].unique().tolist()))
    loja_row = df_final[df_final["Nome_Exibicao"] == loja_sel].iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Posição Final na Pista", f"{loja_row['Posicao_Final_Horas']:.2f}h")
    with col2: st.metric("Boost (Notas)", f"+ {format_minutes(loja_row['Boost_Total_Min'])}")
    with col3: st.metric("Progresso Total", f"{loja_row['Progresso']:.1f}%")
    with col4: st.metric("Rank Atual", f"#{loja_row['Rank']}")
    # Restante da função da página da loja omitida para brevidade

# ----------------------------------------------------------------------
# Estrutura Principal do App
# ----------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state.page = "Geral"

with st.spinner("Carregando base de dados..."):
    all_sheets = get_data_from_github()
if not all_sheets: st.stop()

with st.spinner("Processando e preparando a corrida..."):
    data, etapas_scores, periodos_df, etapas_pesos_df = load_and_prepare_data(all_sheets)
    st.session_state.update({'data_original': data, 'etapas_scores_cols': etapas_scores, 'periodos_df': periodos_df, 'etapas_pesos_df': etapas_pesos_df})

with st.sidebar:
    st.image("https://cdn-retailhub.com/minipreco/096c9b29-4ac3-425f-8322-be76b794f040.webp", use_container_width=True)
    st.markdown("---<h3>Seleção de Ciclo e Período</h3>", unsafe_allow_html=True)
    ciclos_unicos = periodos_df["Ciclo"].dropna().unique().tolist() if not periodos_df.empty else []
    if not ciclos_unicos: st.stop()
    sort_order_map = {name: i for i, name in enumerate(MONTH_MAP.keys())}
    sorted_ciclos = sorted(ciclos_unicos, key=lambda m: sort_order_map.get(m, -1))
    ciclo_selecionado = st.selectbox("Selecione o Ciclo", sorted_ciclos, index=len(sorted_ciclos)-1)
    periodos_ciclo = sorted(periodos_df[periodos_df["Ciclo"] == ciclo_selecionado]["Periodo"].dropna().unique())
    periodos_selecionados = st.multiselect("Selecione os Períodos", ["Todos"] + periodos_ciclo, default=["Todos"])
    st.session_state.update({'ciclo': ciclo_selecionado, 'periodos': periodos_selecionados})
    st.markdown("---<h3>Navegação</h3>", unsafe_allow_html=True)
    if st.button("Visão Geral", use_container_width=True, type="primary" if st.session_state.page == "Geral" else "secondary"): st.session_state.page = "Geral"
    if st.button("Visão por Loja", use_container_width=True, type="primary" if st.session_state.page == "Loja" else "secondary"): st.session_state.page = "Loja"

if st.session_state.get('ciclo') and st.session_state.get('periodos'):
    df_final, duracao_horas, baseline_horas = filter_and_aggregate_data(st.session_state.data_original, st.session_state.etapas_scores_cols, st.session_state.ciclo, st.session_state.periodos)
    st.session_state.update({'df_final': df_final, 'duracao_horas': duracao_horas, 'baseline_horas': baseline_horas})

periodo_inicio, periodo_fim = get_period_range(st.session_state.get('ciclo'), st.session_state.get('periodos'), st.session_state.get('periodos_df'))
render_header_and_periodo("Circuito MiniPreço", periodo_inicio, periodo_fim, st.session_state.get('duracao_horas', 0), st.session_state.get('baseline_horas', 0))

if st.session_state.page == "Geral":
    render_geral_page()
elif st.session_state.page == "Loja":
    render_loja_page()
