# -*- coding: utf-8 -*-
# circuito_lojas_app.py — VERSÃO COM PISTA E CLASSIFICAÇÃO ESTILIZADAS

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
/* Estilos Gerais */
.app-header { text-align: center; margin-top: -18px; margin-bottom: 6px; }
.app-header h1 { font-size: 34px !important; margin: 0; letter-spacing: 0.6px; color: #ffffff; font-weight: 800; text-shadow: 0 3px 10px rgba(0,0,0,0.6); }
.app-header p { margin: 4px 0 0 0; color: rgba(255,255,255,0.85); font-size: 14px; }

/* Estilos da Tabela de Classificação de Corrida */
.race-table { width: 100%; border-collapse: collapse; font-family: "Segoe UI", Tahoma, sans-serif; margin-top: 10px; }
.race-table th { background: linear-gradient(90deg, #1f2937, #111827); color: #e5e7eb; padding: 12px 15px; text-align: left; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
.race-table td { padding: 14px 15px; color: #d1d5db; border-bottom: 1px solid #374151; }
.race-table tr.zebra { background-color: rgba(255, 255, 255, 0.02); }
.race-table tr:hover { background-color: #374151; }
.rank-cell { font-weight: 900; font-size: 1.1em; text-align: center; }
.rank-1 { color: #facc15; } /* Ouro */
.rank-2 { color: #d1d5db; } /* Prata */
.rank-3 { color: #f59e0b; } /* Bronze */
.loja-cell { font-weight: 700; color: #f9fafb; }
.progress-bar-container { background-color: #374151; border-radius: 10px; overflow: hidden; height: 18px; width: 100%; }
.progress-bar { background: linear-gradient(90deg, #38bdf8, #3b82f6); height: 100%; border-radius: 10px; text-align: center; color: white; font-size: 12px; line-height: 18px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Funções Utilitárias
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_data_from_github():
    try: return pd.read_excel(GITHUB_FILE_URL, sheet_name=None, engine="openpyxl")
    except Exception as e:
        st.error(f"Erro ao carregar os dados do GitHub: {e}")
        return {}

def format_minutes(minutes: float):
    if pd.isna(minutes) or minutes < 0: return "-"
    if minutes < 60: return f"{minutes:.1f} min"
    hours = math.floor(minutes / 60)
    rem_minutes = round(minutes % 60)
    return f"{hours}h {rem_minutes}min"

def get_period_range(ciclo: str, selected_periods: list, periodos_df: pd.DataFrame):
    if not ciclo or periodos_df is None or periodos_df.empty: return None, None
    ciclo_df = periodos_df[periodos_df["Ciclo"] == str(ciclo)]
    if ciclo_df.empty: return None, None
    ordered_periods = sorted(ciclo_df["Periodo"].astype(str).unique())
    if not selected_periods or "Todos" in selected_periods: return ordered_periods[0], ordered_periods[-1]
    selected_in_order = [p for p in ordered_periods if p in selected_periods]
    return (selected_in_order[0], selected_in_order[-1]) if selected_in_order else (None, None)

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
    # (Função mantida como na versão anterior, sem alterações)
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
    # A linha abaixo foi atualizada para usar o ano atual dinamicamente.
    if MONTH_MAP.get(ciclo) == hoje.month and datetime.now().year == 2025:
        baseline_horas = hoje.day
    duracao_horas = get_race_duration_hours(ciclo)
    final_df = calculate_final_scores(aggregated, etapas_scores_cols, duracao_horas, baseline_horas)
    return final_df, duracao_horas, baseline_horas

# ----------------------------------------------------------------------
# Funções de Renderização da Interface
# ----------------------------------------------------------------------
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
                tempo_faltante_min = row.Tempo_Faltante_Horas * 60
                with cols[i]:
                    st.markdown(
                        f"<div style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0f172a,#111827);color:white; text-align:center; height: 100%;'>"
                        f"<h3 style='margin:0'>{i+1}º — {row.Nome_Exibicao}</h3>"
                        f"<h2 style='margin:8px 0; font-size: 1.6em;'>Boost: +{format_minutes(row.Boost_Total_Min)}</h2>"
                        f"<p style='margin:4px 0; font-size:14px; opacity:0.85'>Progresso: {row.Progresso:.1f}%</p>"
                        f"<p style='margin:4px 0 0 0; font-size:12px; opacity:0.7'>Faltam: {format_minutes(tempo_faltante_min)}</p>"
                        f"</div>", unsafe_allow_html=True
                    )

def build_pista_fig(data: pd.DataFrame, duracao_total_horas: float, baseline_horas: float) -> go.Figure:
    if data is None or data.empty: return go.Figure()
    CAR_ICON_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/assets/carro-corrida_anim.webp"
    fig = go.Figure()
    max_horas = duracao_total_horas if duracao_total_horas > 0 else 1
    
    # Linhas de fundo da pista
    for i in range(len(data)):
        fig.add_shape(type="rect", x0=0, y0=i-0.5, x1=max_horas, y1=i+0.5, line=dict(width=0), fillcolor="#2C3E50", layer="below")
        
    # Linha de Partida
    fig.add_shape(type="line", x0=0, y0=-0.5, x1=0, y1=len(data)-0.5, line=dict(color="white", width=3, dash="solid"), layer="above")
    
    # Linha de Largada do Dia (se aplicável)
    if baseline_horas > 0:
        fig.add_shape(type="rect", x0=0, y0=-0.5, x1=baseline_horas, y1=len(data)-0.5, line=dict(width=0), fillcolor="rgba(113, 128, 150, 0.25)", layer="below")
        fig.add_vline(x=baseline_horas, line_width=1, line_dash="dash", line_color="yellow", annotation_text=f"Largada do Dia ({baseline_horas}h)", annotation_position="top left")
        
    # Linha de Chegada (largura reduzida)
    square_size = max_horas / 40
    num_cols = 2 # Reduzido de 4 para 2
    for i in range(math.ceil((len(data)+0.5) / square_size)):
        for j in range(num_cols):
            color = "white" if (i + j) % 2 == 0 else "black"
            fig.add_shape(type="rect", x0=max_horas + (j * square_size), y0=i*square_size - 0.5, x1=max_horas + ((j+1) * square_size), y1=(i+1)*square_size - 0.5, line=dict(width=0.5, color="black"), fillcolor=color, layer="above")
            
    # Carros e textos
    for i, row in data.iterrows():
        hover_text = (f"<b>{row.Nome_Exibicao}</b><br>Posição Final: {row.Posicao_Final_Horas:.2f}h<br>Progresso: {row.Progresso:.1f}%<br>Boost Acumulado: {format_minutes(row.Boost_Total_Min)}<br>Faltam: {format_minutes(row.Tempo_Faltante_Horas * 60)}<br>Rank: #{row.Rank}")
        fig.add_trace(go.Scatter(x=[row.Posicao_Final_Horas], y=[i], mode='markers', marker=dict(color='rgba(0,0,0,0)', size=25), hoverinfo='text', hovertext=hover_text, showlegend=False))
        fig.add_layout_image(dict(source=CAR_ICON_URL, xref="x", yref="y", x=row.Posicao_Final_Horas, y=i, sizex=max(2, max_horas / 12), sizey=0.85, xanchor="center", yanchor="middle", layer="above"))
        fig.add_trace(go.Scatter(x=[row.Posicao_Final_Horas], y=[i-0.55], mode="text", text=[row.Nome_Exibicao], textfont=dict(size=9, color="rgba(255,255,255,0.9)"), hoverinfo="skip", showlegend=False))
        
    fig.update_xaxes(range=[0, max_horas * 1.15], title_text="Avanço na Pista (horas) →", fixedrange=True)
    fig.update_yaxes(showgrid=False, zeroline=False, tickvals=list(range(len(data))), ticktext=[], fixedrange=True)
    fig.update_layout(height=max(600, 300 + 60*len(data)), margin=dict(l=10, r=10, t=80, b=40), plot_bgcolor="#1A2A3A", paper_bgcolor="rgba(26,42,58,0.7)")
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
        
    render_podio_table(df_final)
    
    st.markdown("### Pista de Corrida do Circuito")
    fig_pista = build_pista_fig(df_final, st.session_state.get('duracao_horas', 0), st.session_state.get('baseline_horas', 0))
    st.plotly_chart(fig_pista, use_container_width=True)

    st.markdown("### Classificação Completa")
    html = ["<table class='race-table'><thead><tr><th>Rank</th><th>Loja</th><th>Boost</th><th>Posição</th><th>Progresso</th><th>Faltam</th></tr></thead><tbody>"]
    for i, row in df_final.iterrows():
        rank = row['Rank']
        rank_class = f'rank-{rank}' if rank <= 3 else ''
        zebra_class = 'zebra' if i % 2 != 0 else ''
        
        progresso_percent = row['Progresso']
        progresso_bar = f"""
        <div class='progress-bar-container'>
            <div class='progress-bar' style='width: {min(progresso_percent, 100)}%;'>
                {progresso_percent:.1f}%
            </div>
        </div>
        """
        
        html.append(f"<tr class='{zebra_class}'>")
        html.append(f"<td class='rank-cell {rank_class}'>{rank}</td>")
        html.append(f"<td class='loja-cell'>{row['Nome_Exibicao']}</td>")
        html.append(f"<td>+{format_minutes(row['Boost_Total_Min'])}</td>")
        html.append(f"<td>{row['Posicao_Final_Horas']:.2f}h</td>")
        html.append(f"<td>{progresso_bar}</td>")
        html.append(f"<td>{format_minutes(row['Tempo_Faltante_Horas'] * 60)}</td>")
        html.append("</tr>")
        
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)

def render_loja_page():
    st.header("Visão por Loja")
    # (Função mantida como na versão anterior, sem alterações)
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty: return
    loja_sel = st.selectbox("Selecione a Loja:", sorted(df_final["Nome_Exibicao"].unique().tolist()))
    loja_row = df_final[df_final["Nome_Exibicao"] == loja_sel].iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Posição Final na Pista", f"{loja_row['Posicao_Final_Horas']:.2f}h")
    with col2: st.metric("Boost (Notas)", f"+ {format_minutes(loja_row['Boost_Total_Min'])}")
    with col3: st.metric("Progresso Total", f"{loja_row['Progresso']:.1f}%")
    with col4: st.metric("Rank Atual", f"#{loja_row['Rank']}")
    st.markdown("---")
    ciclo, periodos = st.session_state.ciclo, st.session_state.periodos
    etapas_pesos_df = st.session_state.get('etapas_pesos_df', pd.DataFrame())
    if not etapas_pesos_df.empty:
        df_pesos_ciclo = etapas_pesos_df[etapas_pesos_df['Ciclo'] == ciclo]
        if "Todos" not in periodos: df_pesos_ciclo = df_pesos_ciclo[df_pesos_ciclo['Periodo'].isin(periodos)]
        pesos_etapas = df_pesos_ciclo.groupby('Etapa')['PesoMaximo'].sum().to_dict()
        etapas_data = []
        score_cols = [c for c in loja_row.index if c.endswith('_Score')]
        for etapa_col, peso_max in pesos_etapas.items():
            if peso_max > 0:
                etapa_name, score_atual = etapa_col.replace('_Score', ''), loja_row.get(etapa_col, 0)
                etapas_data.append({'Etapa': etapa_name, 'Avanço Atual': score_atual, 'Avanço Máximo': peso_max, 'Gap': peso_max - score_atual})
        if etapas_data:
            df_melhoria = pd.DataFrame(etapas_data).sort_values('Gap', ascending=False, ignore_index=True)
            col_insight, col_chart = st.columns([1, 2])
            with col_insight:
                st.subheader("Pontos de Melhoria")
                st.markdown("Oportunidades para ganhar tempo e avançar no circuito:")
                top_melhorias = df_melhoria[df_melhoria['Gap'] > 0.1].head(3)
                if top_melhorias.empty: st.success("🎉 Parabéns! A loja atingiu o avanço máximo em todas as etapas!")
                else:
                    for _, row in top_melhorias.iterrows(): st.info(f"**{row['Etapa']}**: Foque aqui para ganhar até **{format_minutes(row['Gap'])}**.")
            with col_chart:
                st.subheader("Desempenho por Etapa")
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=df_melhoria['Avanço Máximo'], theta=df_melhoria['Etapa'], mode='lines', line=dict(color='rgba(255, 255, 255, 0.4)'), name='Avanço Máximo'))
                fig.add_trace(go.Scatterpolar(r=df_melhoria['Avanço Atual'], theta=df_melhoria['Etapa'], fill='toself', fillcolor='rgba(0, 176, 246, 0.4)', line=dict(color='rgba(0, 176, 246, 1)'), name='Avanço Atual'))
                fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, df_melhoria['Avanço Máximo'].max() * 1.1 if not df_melhoria.empty else 1])), showlegend=True, paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(l=40, r=40, t=80, b=40))
                st.plotly_chart(fig, use_container_width=True)

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
