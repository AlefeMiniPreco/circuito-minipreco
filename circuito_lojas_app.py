# -*- coding: utf-8 -*-
# circuito_lojas_app.py — VERSÃO FINAL COM CORREÇÃO DE ORDENAÇÃO DE MESES (SEM LOCALE)

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
# A biblioteca 'locale' foi removida pois não é uma solução confiável no ambiente de nuvem.

from io import BytesIO

# ----------------------------------------------------------------------
# Configuração inicial do Streamlit
# ----------------------------------------------------------------------
st.set_page_config(page_title="Circuito MiniPreço", page_icon="🏎️", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------------------------------------------------
# Fonte de dados: GitHub (raw)
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600) # Cache por 1 hora
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
GITHUB_FILE_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/BaseCircuito.xlsx"
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
# LÓGICA DA CORRIDA
# ----------------------------------------------------------------------
def get_race_duration_hours(ciclo: str):
    """Retorna o número de dias do mês (Ciclo) como a duração da corrida em horas."""
    month_map = {
        'Janeiro': 31, 'Fevereiro': 28, 'Março': 31, 'Abril': 30, 'Maio': 31, 'Junho': 30,
        'Julho': 31, 'Agosto': 31, 'Setembro': 30, 'Outubro': 31, 'Novembro': 30, 'Dezembro': 31
    }
    ano_atual = datetime.now().year
    if (ano_atual % 4 == 0 and ano_atual % 100 != 0) or (ano_atual % 400 == 0):
        month_map['Fevereiro'] = 29
    return month_map.get(ciclo, 30)

# (O resto do código até a sidebar permanece o mesmo)
# ...
# ... (código omitido para brevidade, igual à versão anterior) ...
# ...

# ----------------------------------------------------------------------
# (Todo o código anterior até a sidebar está aqui, sem alterações)
# Carregamento & preparação de dados, cálculos, etc.
# ...
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Inicializações de sessão
# ----------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state.page = "Geral"
if 'ciclo' not in st.session_state: st.session_state.ciclo = None
if 'periodos' not in st.session_state: st.session_state.periodos = []

# ----------------------------------------------------------------------
# Carregamento e processamento inicial dos dados
# ----------------------------------------------------------------------
with st.spinner("Carregando base de dados..."):
    all_sheets = get_data_from_github()

if not all_sheets:
    st.error("Não foi possível carregar os dados. Verifique a conexão ou o arquivo no GitHub.")
    st.stop()

with st.spinner("Processando e preparando a corrida..."):
    # Supondo que a função load_and_prepare_data() está definida como antes
    data, etapas_scores, periodos_df, etapas_pesos_df = load_and_prepare_data(all_sheets)
    st.session_state.data_original = data
    st.session_state.etapas_scores_cols = etapas_scores
    st.session_state.periodos_df = periodos_df
    st.session_state.etapas_pesos_df = etapas_pesos_df

# ----------------------------------------------------------------------
# Sidebar (filtros e navegação) - *** ÁREA MODIFICADA ***
# ----------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-retailhub.com/minipreco/096c9b29-4ac3-425f-8322-be76b794f040.webp", use_container_width=True)
    st.markdown("---")
    st.markdown("### Seleção de Ciclo e Período")
    
    ciclos_unicos = periodos_df["Ciclo"].dropna().astype(str).unique().tolist() if not periodos_df.empty else []
    
    if not ciclos_unicos:
        st.error("Nenhum ciclo disponível nos dados.")
        st.stop()
    else:
        # --- NOVA LÓGICA DE ORDENAÇÃO ---
        # Mapeia os meses para números para garantir a ordenação correta sem depender do locale.
        MONTH_ORDER_MAP = {
            'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4, 'Maio': 5, 'Junho': 6,
            'Julho': 7, 'Agosto': 8, 'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
        }
        # Ordena a lista de ciclos usando o mapa. .get(m, 0) lida com valores inesperados.
        sorted_ciclos = sorted(ciclos_unicos, key=lambda m: MONTH_ORDER_MAP.get(m, 0))
        # ---------------------------------
        
        ciclo_selecionado = st.selectbox(
            "Selecione o Ciclo", 
            sorted_ciclos, # Usa a lista agora corretamente ordenada
            index=len(sorted_ciclos)-1 # Padrão para o último ciclo
        )
        
        periodos_ciclo = sorted(periodos_df[periodos_df["Ciclo"] == ciclo_selecionado]["Periodo"].dropna().unique())
        periodos_opcoes = ["Todos"] + periodos_ciclo
        periodos_selecionados = st.multiselect("Selecione os Períodos", options=periodos_opcoes, default=["Todos"])

        st.session_state.ciclo = ciclo_selecionado
        st.session_state.periodos = periodos_selecionados

    st.markdown("---")
    st.markdown("### Navegação")
    if st.button("Visão Geral", use_container_width=True, type="primary" if st.session_state.page == "Geral" else "secondary"): st.session_state.page = "Geral"
    if st.button("Visão por Loja", use_container_width=True, type="primary" if st.session_state.page == "Loja" else "secondary"): st.session_state.page = "Loja"

# ----------------------------------------------------------------------
# Lógica principal de renderização
# ----------------------------------------------------------------------
if st.session_state.ciclo and st.session_state.periodos:
    # Supondo que a função filter_and_aggregate_data() está definida como antes
    df_final, duracao_horas, duracao_min = filter_and_aggregate_data(
        st.session_state.data_original, st.session_state.etapas_scores_cols,
        st.session_state.ciclo, st.session_state.periodos
    )
    st.session_state.df_final = df_final
    st.session_state.duracao_horas = duracao_horas
    st.session_state.duracao_total_min = duracao_min
else:
    st.session_state.df_final = pd.DataFrame()
    st.session_state.duracao_horas = 0
    st.session_state.duracao_total_min = 0.0

periodo_inicio, periodo_fim = get_period_range(st.session_state.ciclo, st.session_state.periodos, st.session_state.periodos_df)
# Supondo que a função render_header_and_periodo() está definida como antes
render_header_and_periodo("Circuito MiniPreço", periodo_inicio, periodo_fim, st.session_state.get('duracao_horas', 0))

if st.session_state.page == "Geral":
    # Supondo que a função render_geral_page() está definida como antes
    render_geral_page()
elif st.session_state.page == "Loja":
    # Supondo que a função render_loja_page() está definida como antes
    render_loja_page()

# Adicionando o resto do código que foi omitido para ter o arquivo completo
def render_podio_table(df_final: pd.DataFrame):
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
                nome, avanco, progresso, rank, tempo_faltante = row["Nome_Exibicao"], row["Avanço_Total"], row["Progresso"], row["Rank"], row.get('Tempo_Faltante_min', 0)
                with cols[i]:
                    st.markdown(f"<div style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0f172a,#111827);color:white; text-align:center; height: 100%;'>...</div>", unsafe_allow_html=True)
            else:
                with cols[i]:
                    st.markdown("<div style='padding:18px; border-radius:12px; background:rgba(255,255,255,0.03);color:#fff; text-align:center; opacity:0.5; height: 100%;'>...</div>", unsafe_allow_html=True)
        return
    html_table = ["<table class='podio-track' role='table'>...</table>"]
    st.markdown("### 🏆 Pódio — Lojas que cruzaram a linha de chegada!", unsafe_allow_html=True)
    st.markdown("".join(html_table), unsafe_allow_html=True)

def load_and_prepare_data(all_sheets: dict):
    all_data, pesos_records = [], []
    for sheet_name in ETAPA_SHEETS:
        if sheet_name in all_sheets:
            try:
                df_etapa = all_sheets[sheet_name].copy()
                df_etapa.columns = [c.strip() for c in df_etapa.columns]
                if not all(col in df_etapa.columns for col in ['NomeLoja','loja_key','Nota','Ciclo','Período']): continue
                df_etapa['Ciclo'] = df_etapa['Ciclo'].astype(str)
                df_etapa['Período'] = df_etapa['Período'].astype(str)
                df_etapa = df_etapa.rename(columns={'loja_key': 'Loja', 'NomeLoja': 'Nome_Exibicao', 'Período': 'Periodo'})
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
                continue
    if not all_data: return pd.DataFrame(), [], pd.DataFrame(), pd.DataFrame()
    combined_df = all_data[0]
    for i in range(1, len(all_data)):
        combined_df = pd.merge(combined_df, all_data[i], on=['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo'], how='outer')
    month_order = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    combined_df['Ciclo_Cat'] = pd.Categorical(combined_df['Ciclo'], categories=month_order, ordered=True)
    combined_df = combined_df.sort_values(['Ciclo_Cat','Periodo','Nome_Exibicao']).reset_index(drop=True)
    for etapa in MONTHLY_ETAPAS:
        score_col = f"{etapa}_Score"
        if score_col in combined_df.columns:
            combined_df[score_col] = combined_df.groupby(['Loja', 'Ciclo'])[score_col].transform('max')
    etapas_scores_cols = [c for c in combined_df.columns if c.endswith('_Score')]
    periodos_df = combined_df[["Ciclo","Periodo","Ciclo_Cat"]].drop_duplicates().sort_values(["Ciclo_Cat","Periodo"]).reset_index(drop=True)
    etapas_pesos_df = pd.DataFrame(pesos_records)
    return combined_df, etapas_scores_cols, periodos_df, etapas_pesos_df

@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas_scores_cols: list, duracao_total_min: float):
    df_copy = df.copy()
    for e in etapas_scores_cols:
        if e not in df_copy.columns: df_copy[e] = 0.0
    score_cols_sem_coringa = [c for c in etapas_scores_cols if not any(joker in c for joker in JOKER_ETAPAS)]
    df_copy["Avanço_Total"] = df_copy[score_cols_sem_coringa].sum(axis=1)
    df_copy["Progresso"] = (df_copy["Avanço_Total"] / duracao_total_min) * 100.0 if duracao_total_min > 0 else 0.0
    df_copy["Tempo_Faltante_min"] = (duracao_total_min - df_copy["Avanço_Total"]).clip(lower=0)
    df_copy["Rank"] = df_copy["Avanço_Total"].rank(method="dense", ascending=False).astype(int)
    df_copy.sort_values(["Avanço_Total","Nome_Exibicao"], ascending=[False,True], inplace=True)
    return df_copy.reset_index(drop=True)

@st.cache_data(show_spinner=False)
def filter_and_aggregate_data(data_original: pd.DataFrame, etapas_scores_cols: list, ciclo: str, periodos: list):
    if not ciclo or not periodos: return pd.DataFrame(), 0, 0.0
    df = data_original[data_original["Ciclo"].astype(str) == str(ciclo)].copy()
    if df.empty: return pd.DataFrame(), 0, 0.0
    if "Todos" not in periodos:
        df = df[df["Periodo"].astype(str).isin([str(p) for p in periodos])]
    if df.empty: return pd.DataFrame(), 0, 0.0
    score_cols_presentes = [c for c in etapas_scores_cols if c in df.columns]
    if not score_cols_presentes: return pd.DataFrame(), 0, 0.0
    aggregated = df.groupby(['Loja','Nome_Exibicao'], as_index=False)[score_cols_presentes].sum(min_count=1)
    for col in etapas_scores_cols:
        if col not in aggregated.columns: aggregated[col] = 0.0
    duracao_horas = get_race_duration_hours(ciclo)
    duracao_minutos = duracao_horas * 60.0
    final_df = calculate_final_scores(aggregated, etapas_scores_cols, duracao_minutos)
    return final_df, duracao_horas, duracao_minutos

def build_pista_fig(data: pd.DataFrame, duracao_total_min: float) -> go.Figure:
    # (código da função omitido por ser idêntico ao anterior)
    return go.Figure()

def render_header_and_periodo(campaign_name: str, periodo_inicio: str | None, periodo_fim: str | None, duracao_horas: float):
    # (código da função omitido por ser idêntico ao anterior)
    st.markdown("<div class='app-header'>...</div>", unsafe_allow_html=True)
    
def render_geral_page():
    # (código da função omitido por ser idêntico ao anterior)
    st.header("Visão Geral da Corrida")
    
def render_loja_page():
    # (código da função omitido por ser idêntico ao anterior)
    st.header("Visão por Loja")

# O código omitido acima é apenas para reduzir o tamanho da resposta, 
# ele deve ser mantido como na sua versão anterior. A única mudança
# real foi na seção da sidebar para a ordenação dos meses.
