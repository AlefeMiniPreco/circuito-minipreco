# -*- coding: utf-8 -*-
# circuito_lojas_app.py — VERSÃO COM TABELA E VISÃO DE LOJA FOCADAS EM TEMPO RESTANTE

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import math

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

# ----------------------------------------------------------------------
# CSS (visuais com otimização para Mobile)
# ----------------------------------------------------------------------
st.markdown("""
<style>
/* Estilos Gerais */
.app-header { text-align: center; margin-top: -18px; margin-bottom: 6px; }
.app-header h1 { font-size: 34px !important; margin: 0; letter-spacing: 0.6px; color: #ffffff; font-weight: 800; text-shadow: 0 3px 10px rgba(0,0,0,0.6); }
.app-header p { margin: 4px 0 0 0; color: rgba(255,255,255,0.85); font-size: 14px; }
.podio-card h2 { font-size: 2em; margin: 8px 0 2px 0; color: #6EE7B7; }
.podio-card h3 { font-size: 1.1em; margin: 0; }
.podio-card p.metric-label { font-size: 0.8em; font-weight: 700; text-transform: uppercase; opacity: 0.7; margin: 8px 0 -5px 0; letter-spacing: 0.5px; }
.podio-card p.secondary-metric { margin: 0 0 8px 0; font-size: 0.9em; opacity: 0.8; }
.podio-card p.progress-text { margin: 4px 0 0 0; font-size:0.9em; opacity: 0.9;}
.race-table { width: 100%; border-collapse: collapse; font-family: "Segoe UI", Tahoma, sans-serif; margin-top: 10px; font-size: 0.9em; }
.race-table th { background: linear-gradient(90deg, #1f2937, #111827); color: #e5e7eb; padding: 12px 15px; text-align: left; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
.race-table td { padding: 14px 15px; color: #d1d5db; border-bottom: 1px solid #374151; }
.race-table tr.zebra { background-color: rgba(255, 255, 255, 0.05); }
.race-table tr:hover { background-color: #374151; }
.rank-cell { font-weight: 900; font-size: 1.2em; text-align: center; }
.rank-1 { color: #facc15; }
.rank-2 { color: #e5e7eb; }
.rank-3 { color: #f59e0b; }
.loja-cell { font-weight: 800; color: #FFFFFF; font-size: 1.1em; }
.progress-bar-container { background-color: #374151; border-radius: 10px; overflow: hidden; height: 18px; width: 100%; min-width: 100px; }
.progress-bar { background: linear-gradient(90deg, #6EE7B7, #10B981); height: 100%; border-radius: 10px; text-align: center; color: white; font-size: 12px; line-height: 18px; font-weight: 600;}
@media (max-width: 640px) {
    .app-header h1 { font-size: 28px !important; }
    .app-header p { font-size: 12px; }
    .podio-card h2 { font-size: 1.5em; }
    .podio-card h3 { font-size: 1em; }
    .race-table { font-size: 0.8em; }
    .race-table th, .race-table td { padding: 8px 6px; }
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Funções Utilitárias e de Processamento
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_data_from_github():
    try: return pd.read_excel(GITHUB_FILE_URL, sheet_name=None, engine="openpyxl")
    except Exception as e:
        st.error(f"Erro ao carregar os dados do GitHub: {e}")
        return {}

def set_page(page_name):
    st.session_state.page = page_name

def format_hours_and_minutes(hours_float: float):
    if pd.isna(hours_float): return "N/A"
    if hours_float < 0: return "Finalizou!"
    hours = math.floor(hours_float)
    minutes = round((hours_float - hours) * 60)
    return f"{hours}h {minutes:02d}min"

def get_race_duration_hours(ciclo: str):
    local_month_map = MONTH_DAYS_MAP.copy()
    ano_atual = datetime.now().year
    if (ano_atual % 4 == 0 and ano_atual % 100 != 0) or (ano_atual % 400 == 0):
        local_month_map['Fevereiro'] = 29
    return local_month_map.get(ciclo, 30)

@st.cache_data(show_spinner="Processando dados...")
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
            except Exception: continue
    if not all_data: return pd.DataFrame(), [], pd.DataFrame(), pd.DataFrame()
    df_merged = pd.DataFrame(columns=['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo'])
    unique_identifiers = ['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo']
    for df in all_data:
        df_merged = pd.merge(df_merged, df, on=unique_identifiers, how='outer')
    month_order = list(MONTH_MAP.keys())
    df_merged['Ciclo_Cat'] = pd.Categorical(df_merged['Ciclo'], categories=month_order, ordered=True)
    df_merged.sort_values(['Ciclo_Cat','Periodo','Nome_Exibicao'], inplace=True, ignore_index=True)
    for etapa in MONTHLY_ETAPAS:
        score_col = f"{etapa}_Score"
        if score_col in df_merged.columns:
            df_merged[score_col] = df_merged.groupby(['Loja', 'Ciclo'])[score_col].transform('max')
    etapas_scores_cols = [c for c in df_merged.columns if c.endswith('_Score')]
    periodos_df = df_merged[["Ciclo","Periodo","Ciclo_Cat"]].drop_duplicates().sort_values(["Ciclo_Cat","Periodo"]).reset_index(drop=True)
    etapas_pesos_df = pd.DataFrame(pesos_records)
    return df_merged, etapas_scores_cols, periodos_df, etapas_pesos_df

@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas_scores_cols: list, duracao_total_horas: float, baseline_horas: float):
    df_copy = df.copy()
    for e in etapas_scores_cols:
        if e not in df_copy.columns: df_copy[e] = 0.0
    score_cols_sem_coringa = [c for c in etapas_scores_cols if not any(joker in c for joker in JOKER_ETAPAS)]
    df_copy["Boost_Total_Min"] = df_copy[score_cols_sem_coringa].sum(axis=1)
    df_copy["Posicao_Horas"] = baseline_horas + (df_copy["Boost_Total_Min"] / 60.0)
    if duracao_total_horas > 0:
        df_copy["Progresso"] = (df_copy["Posicao_Horas"] / duracao_total_horas) * 100.0
    else:
        df_copy["Progresso"] = 0.0
    df_copy["Tempo_Faltante_Horas"] = duracao_total_horas - df_copy["Posicao_Horas"]
    df_copy["Rank"] = df_copy["Posicao_Horas"].rank(method="dense", ascending=False).astype(int)
    df_copy.sort_values(["Posicao_Horas","Nome_Exibicao"], ascending=[False,True], inplace=True, ignore_index=True)
    return df_copy

@st.cache_data(show_spinner="Calculando ranking...")
def filter_and_aggregate_data(data_original: pd.DataFrame, etapas_scores_cols: list, ciclo: str):
    if not ciclo: return pd.DataFrame(), 0, 0
    df = data_original[data_original["Ciclo"] == str(ciclo)].copy()
    if df.empty: return pd.DataFrame(), 0, 0
    score_cols = [c for c in etapas_scores_cols if c in df.columns]
    if not score_cols: return pd.DataFrame(), 0, 0
    id_vars = ['Loja', 'Nome_Exibicao']
    aggregated = df.groupby(id_vars, as_index=False)[score_cols].sum(min_count=0)
    hoje = datetime.now()
    baseline_horas = 0
    if MONTH_MAP.get(ciclo) == hoje.month and hoje.year == 2025:
        baseline_horas = hoje.day
    duracao_horas = get_race_duration_hours(ciclo)
    final_df = calculate_final_scores(aggregated, etapas_scores_cols, duracao_horas, baseline_horas)
    return final_df, duracao_horas, baseline_horas

# ----------------------------------------------------------------------
# Funções de Renderização da Interface
# ----------------------------------------------------------------------
def render_header_and_periodo(campaign_name: str, ciclo:str, duracao_horas: float, baseline_horas: float):
    st.markdown("<div class='app-header'>", unsafe_allow_html=True)
    st.markdown(f"<h1>{campaign_name}</h1>", unsafe_allow_html=True)
    baseline_str = f"| Avanço Base (Dia Atual): <b>{baseline_horas:.0f} horas</b>" if baseline_horas > 0 else ""
    st.markdown(f"<p>Ciclo: <b>{ciclo}</b> | Duração da corrida: <b>{duracao_horas:.0f} horas</b> {baseline_str}</p>", unsafe_allow_html=True)
    st.markdown("---")

def render_podio_table(df_final: pd.DataFrame, baseline_horas: float):
    st.markdown("### Pódio Atual")
    top3 = df_final.head(3)
    cols = st.columns(3)
    for i, row in top3.iterrows():
        with cols[i]:
            st.markdown(
                f"<div class='podio-card' style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0f172a,#111827);color:white; text-align:center; height: 100%; border: 1px solid #374151;'>"
                f"<h3>{row['Rank']}º — {row['Nome_Exibicao']}</h3>"
                f"<p class='metric-label'>Tempo Restante</p>"
                f"<h2>{format_hours_and_minutes(row['Tempo_Faltante_Horas'])}</h2>"
                f"<p class='secondary-metric'>Avanço: {format_hours_and_minutes(row['Posicao_Horas'])}</p>"
                f"<p class='progress-text'>Progresso: {row['Progresso']:.1f}%</p>"
                f"</div>", unsafe_allow_html=True
            )

def build_pista_fig(data: pd.DataFrame, duracao_total_horas: float) -> go.Figure:
    if data is None or data.empty: return go.Figure()
    CAR_ICON_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/assets/carro-corrida_anim.webp"
    fig = go.Figure()
    max_posicao_carro = data['Posicao_Horas'].max() if not data.empty else 0
    limite_eixo = max(duracao_total_horas, max_posicao_carro)
    for i in range(len(data)):
        fig.add_shape(type="rect", x0=0, y0=i-0.5, x1=limite_eixo, y1=i+0.5, line=dict(color='rgba(255, 255, 255, 0.1)', width=1.5), fillcolor="#2C3E50", layer="below")
    fig.add_shape(type="line", x0=0, y0=-0.5, x1=0, y1=len(data)-0.5, line=dict(color="#10B981", width=4, dash="solid"), layer="above")
    square_size = max(0.5, duracao_total_horas / 40)
    num_cols = 2 
    for i in range(math.ceil((len(data)+0.5) / square_size)):
        for j in range(num_cols):
            color = "white" if (i + j) % 2 == 0 else "black"
            fig.add_shape(type="rect", x0=duracao_total_horas + (j * square_size), y0=i*square_size - 0.5, x1=duracao_total_horas + ((j+1) * square_size), y1=(i+1)*square_size - 0.5, line=dict(width=0.5, color="black"), fillcolor=color, layer="above")
    hover_texts = [
        f"<b>{row['Nome_Exibicao']}</b><br>Avanço: {row['Posicao_Horas']:.2f}h<br>Progresso: {row['Progresso']:.1f}%<br>Impulso: {format_hours_and_minutes(row['Boost_Total_Min'] / 60)}<br>Faltam: {format_hours_and_minutes(row['Tempo_Faltante_Horas'])}<br>Rank: #{row['Rank']}"
        for i, row in data.iterrows()
    ]
    y_text = data.index - 0.35
    fig.add_trace(go.Scatter(x=data['Posicao_Horas'], y=y_text, mode='text', text=data['Nome_Exibicao'], textposition="top center", textfont=dict(color='white', size=10), hoverinfo='text', hovertext=hover_texts, showlegend=False))
    for i, row in data.iterrows():
        fig.add_layout_image(dict(source=CAR_ICON_URL, xref="x", yref="y", x=row['Posicao_Horas'], y=i, sizex=max(1.8, duracao_total_horas / 20), sizey=0.9, layer="below", xanchor="center", yanchor="middle"))
    fig.update_xaxes(range=[-limite_eixo*0.02, limite_eixo * 1.05], title_text="Avanço na Pista (dias/horas) →", fixedrange=True, tick0=0, dtick=1, showgrid=False)
    fig.update_yaxes(showgrid=False, zeroline=False, tickvals=list(range(len(data))), ticktext=[], fixedrange=True)
    fig.update_layout(height=max(600, 300 + 60*len(data)), margin=dict(l=10, r=10, t=80, b=40), plot_bgcolor="#1A2A3A", paper_bgcolor="rgba(26,42,58,0.7)")
    return fig

def render_geral_page():
    st.header("Visão Geral da Corrida")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Sem dados para exibir com a seleção atual.")
        return
    duracao_horas = st.session_state.get('duracao_horas', 0)
    baseline_horas = st.session_state.get('baseline_horas', 0)
    dias_restantes = duracao_horas - baseline_horas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Término da Corrida", f"{dias_restantes:.0f} dias" if dias_restantes >= 0 else "Finalizada")
    with col2:
        st.metric("Líder Atual", df_final['Nome_Exibicao'].iloc[0] if not df_final.empty else "N/A")
    with col3:
        st.metric("Total de Lojas", f"{len(df_final)}")
    render_podio_table(df_final, baseline_horas)
    st.markdown("### Pista de Corrida do Circuito")
    fig_pista = build_pista_fig(df_final, st.session_state.get('duracao_horas', 0))
    st.plotly_chart(fig_pista, use_container_width=True)
    st.markdown("### Classificação Completa")
    show_details = st.toggle("Mostrar detalhes por etapa", value=False)
    score_cols = st.session_state.get('etapas_scores_cols', [])
    score_cols_with_data = [col for col in score_cols if col in df_final.columns and df_final[col].sum() > 0]
    
    # MUDANÇA AQUI: Cabeçalho da tabela focado em Tempo Restante
    headers = ["Rank", "Loja", "Tempo Restante", "Progresso", "Impulso Total"]
    if show_details:
        headers.extend([col.replace('_Score', '') for col in score_cols_with_data])
    
    html = [f"<table class='race-table'><thead><tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr></thead><tbody>"]
    
    for i, row in df_final.iterrows():
        rank, zebra_class = row['Rank'], 'zebra' if i % 2 != 0 else ''
        rank_class = f'rank-{rank}' if rank <= 3 else ''
        prog_bar = f"<div class='progress-bar-container'><div class='progress-bar' style='width: {min(row['Progresso'], 100)}%;'>{row['Progresso']:.1f}%</div></div>"
        
        html.append(f"<tr class='{zebra_class}'>")
        html.append(f"<td class='rank-cell {rank_class}'>{rank}</td>")
        html.append(f"<td class='loja-cell'>{row['Nome_Exibicao']}</td>")
        # MUDANÇA AQUI: Coluna principal agora é Tempo Restante
        html.append(f"<td>{format_hours_and_minutes(row['Tempo_Faltante_Horas'])}</td>")
        html.append(f"<td>{prog_bar}</td>")
        html.append(f"<td>+{format_hours_and_minutes(row['Boost_Total_Min'] / 60)}</td>")

        if show_details:
            for col in score_cols_with_data:
                 html.append(f"<td>{format_hours_and_minutes(row.get(col, 0) / 60)}</td>")
        html.append("</tr>")
        
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)

def render_loja_page():
    st.header("Visão por Loja")
    df_final = st.session_state.get('df_final')
    etapas_pesos_df = st.session_state.get('etapas_pesos_df', pd.DataFrame())
    if df_final is None or df_final.empty:
        st.warning("Selecione um Ciclo para ver os detalhes da loja.")
        return
    loja_options = sorted(df_final["Nome_Exibicao"].unique().tolist())
    loja_sel = st.selectbox("Selecione a Loja:", loja_options)
    if loja_sel:
        loja_row = df_final[df_final["Nome_Exibicao"] == loja_sel].iloc[0]
        
        # MUDANÇA AQUI: Métricas focadas em Tempo Restante
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Tempo Restante", format_hours_and_minutes(loja_row['Tempo_Faltante_Horas']))
        with col2: st.metric("Avanço na Pista", format_hours_and_minutes(loja_row['Posicao_Horas']))
        with col3: st.metric("Progresso Total", f"{loja_row['Progresso']:.1f}%")
        with col4: st.metric("Rank Atual", f"#{loja_row['Rank']}")
        
        st.markdown("---")
        ciclo = st.session_state.ciclo
        if not etapas_pesos_df.empty:
            df_pesos_ciclo = etapas_pesos_df[etapas_pesos_df['Ciclo'] == ciclo]
            pesos_etapas = df_pesos_ciclo.groupby('Etapa')['PesoMaximo'].sum().to_dict()
            etapas_data = []
            for etapa_col in st.session_state.etapas_scores_cols:
                peso_max = pesos_etapas.get(etapa_col, 0)
                if peso_max > 0:
                    etapa_name, score_atual = etapa_col.replace('_Score', ''), loja_row.get(etapa_col, 0)
                    etapas_data.append({'Etapa': etapa_name, 'Impulso Atual': score_atual, 'Impulso Máximo': peso_max, 'Gap': peso_max - score_atual})
            if etapas_data:
                df_melhoria = pd.DataFrame(etapas_data).sort_values('Gap', ascending=False, ignore_index=True)
                col_insight, col_chart = st.columns([1, 2])
                with col_insight:
                    st.subheader("Pontos de Melhoria")
                    st.markdown("Oportunidades para ganhar impulso e avançar no circuito:")
                    top_melhorias = df_melhoria[df_melhoria['Gap'] > 0.1].head(3)
                    if top_melhorias.empty: st.success("🎉 Parabéns! A loja atingiu o impulso máximo em todas as etapas!")
                    else:
                        for _, row in top_melhorias.iterrows(): st.info(f"**{row['Etapa']}**: Foque aqui para ganhar até **{format_hours_and_minutes(row['Gap'] / 60)}**.")
                with col_chart:
                    st.subheader("Desempenho por Etapa")
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(r=df_melhoria['Impulso Máximo'], theta=df_melhoria['Etapa'], mode='lines', line=dict(color='rgba(255, 255, 255, 0.4)'), name='Impulso Máximo'))
                    fig.add_trace(go.Scatterpolar(r=df_melhoria['Impulso Atual'], theta=df_melhoria['Etapa'], fill='toself', fillcolor='rgba(0, 176, 246, 0.4)', line=dict(color='rgba(0, 176, 246, 1)'), name='Impulso Atual'))
                    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, df_melhoria['Impulso Máximo'].max() * 1.1 if not df_melhoria.empty else 1])), showlegend=True, paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(l=40, r=40, t=80, b=40))
                    st.plotly_chart(fig, use_container_width=True)

def render_etapa_page():
    st.header("Visão por Etapa")
    df_final = st.session_state.get('df_final')
    etapas_scores_cols = st.session_state.get('etapas_scores_cols', [])
    if df_final is None or df_final.empty:
        st.warning("Selecione um Ciclo para ver os detalhes da etapa.")
        return
    etapa_options = [c.replace('_Score', '') for c in etapas_scores_cols if c in df_final.columns and df_final[c].sum() > 0]
    etapa_sel = st.selectbox("Selecione a Etapa:", sorted(etapa_options))
    if etapa_sel:
        col_name = f"{etapa_sel}_Score"
        df_etapa = df_final[['Nome_Exibicao', col_name]].copy()
        df_etapa.rename(columns={col_name: "Impulso na Etapa (min)"}, inplace=True)
        df_etapa.sort_values("Impulso na Etapa (min)", ascending=False, inplace=True)
        st.subheader(f"Ranking da Etapa: {etapa_sel}")
        st.dataframe(df_etapa.head(10).reset_index(drop=True), use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# Estrutura Principal do App
# ----------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state.page = "Geral"

with st.spinner("Carregando base de dados..."):
    all_sheets = get_data_from_github()
if not all_sheets: st.stop()

data, etapas_scores, periodos_df, etapas_pesos_df = load_and_prepare_data(all_sheets)
st.session_state.update({'data_original': data, 'etapas_scores_cols': etapas_scores, 'periodos_df': periodos_df, 'etapas_pesos_df': etapas_pesos_df})

with st.sidebar:
    st.image("https://cdn-retailhub.com/minipreco/096c9b29-4ac3-425f-8322-be76b794f040.webp", use_container_width=True)
    st.markdown("---<h3>Seleção de Ciclo</h3>", unsafe_allow_html=True)
    ciclos_unicos = periodos_df["Ciclo"].dropna().unique().tolist() if not periodos_df.empty else []
    if not ciclos_unicos: st.stop()
    sort_order_map = {name: i for i, name in enumerate(MONTH_MAP.keys())}
    sorted_ciclos = sorted(ciclos_unicos, key=lambda m: sort_order_map.get(m, -1))
    ciclo_selecionado = st.selectbox("Selecione o Ciclo", sorted_ciclos, index=len(sorted_ciclos)-1, label_visibility="collapsed")
    st.session_state.ciclo = ciclo_selecionado
    st.markdown("---<h3>Navegação</h3>", unsafe_allow_html=True)
    st.button("Visão Geral", on_click=set_page, args=("Geral",), use_container_width=True, type="primary" if st.session_state.page == "Geral" else "secondary")
    st.button("Visão por Loja", on_click=set_page, args=("Loja",), use_container_width=True, type="primary" if st.session_state.page == "Loja" else "secondary")
    st.button("Visão por Etapa", on_click=set_page, args=("Etapa",), use_container_width=True, type="primary" if st.session_state.page == "Etapa" else "secondary")

if st.session_state.get('ciclo'):
    df_final, duracao_horas, baseline_horas = filter_and_aggregate_data(st.session_state.data_original, st.session_state.etapas_scores_cols, st.session_state.ciclo)
    st.session_state.update({'df_final': df_final, 'duracao_horas': duracao_horas, 'baseline_horas': baseline_horas})
    
    render_header_and_periodo("Circuito MiniPreço", st.session_state.ciclo, st.session_state.get('duracao_horas', 0), st.session_state.get('baseline_horas', 0))
    
    page = st.session_state.page
    if page == "Geral":
        render_geral_page()
    elif page == "Loja":
        render_loja_page()
    elif page == "Etapa":
        render_etapa_page()
