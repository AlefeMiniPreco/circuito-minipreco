# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import math
import time

# ----------------------------------------------------------------------
# Configuração inicial do Streamlit
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Circuito MiniPreço F1", 
    page_icon="🏎️", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

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

# Cores da temática F1
F1_COLORS = {
    'red': '#FF1801',     # Ferrari
    'blue': '#006F62',    # Mercedes
    'yellow': '#F0D800',  # Renault
    'orange': '#FF8700',  # McLaren
    'pink': '#EB0EAD',    # Racing Point
    'white': '#FFFFFF',
    'black': '#000000',
    'gray': '#333333',
    'light_gray': '#888888',
    'track_green': '#2E8B57',
    'asphalt': '#36454F'
}

# ----------------------------------------------------------------------
# CSS (visuais com temática F1)
# ----------------------------------------------------------------------
st.markdown(f"""
<style>
/* Estilos Gerais com tema F1 */
body {{
    background-color: {F1_COLORS['black']};
    color: {F1_COLORS['white']};
    font-family: 'Titillium Web', sans-serif;
}}

.app-header {{ 
    text-align: center; 
    margin-top: -18px; 
    margin-bottom: 6px; 
    background: linear-gradient(90deg, {F1_COLORS['red']}, {F1_COLORS['yellow']});
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}}
.app-header h1 {{ 
    font-size: 42px !important; 
    margin: 0; 
    letter-spacing: 2px; 
    color: {F1_COLORS['white']}; 
    font-weight: 900; 
    text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    text-transform: uppercase;
}}
.app-header p {{ 
    margin: 4px 0 0 0; 
    color: rgba(255,255,255,0.9); 
    font-size: 16px; 
    font-weight: 600;
}}

/* Cards de Pódio */
.podio-card {{
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    height: 100%;
    box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    transition: transform 0.3s ease;
}}
.podio-card:hover {{
    transform: translateY(-5px);
}}
.podio-card h2 {{ 
    font-size: 2.2em; 
    margin: 8px 0 2px 0; 
    font-weight: 800;
}}
.podio-card h3 {{ 
    font-size: 1.3em; 
    margin: 0; 
    font-weight: 700;
}}
.podio-card p.breakdown-text {{ 
    margin: 0 0 8px 0; 
    font-size: 0.9em; 
    opacity: 0.8; 
}}
.podio-card p.progress-text {{ 
    margin: 4px 0 0 0; 
    font-size: 1em; 
    opacity: 0.9;
    font-weight: 600;
}}
.podio-card p.remaining-text {{ 
    margin: 2px 0 0 0; 
    font-size: 0.9em; 
    opacity: 0.7;
}}

/* Tabela de Classificação */
.race-table {{ 
    width: 100%; 
    border-collapse: collapse; 
    font-family: "Titillium Web", sans-serif; 
    margin-top: 10px; 
    font-size: 0.95em; 
    border: 1px solid {F1_COLORS['gray']};
    border-radius: 8px;
    overflow: hidden;
}}
.race-table th {{ 
    background: linear-gradient(90deg, {F1_COLORS['red']}, {F1_COLORS['yellow']});
    color: {F1_COLORS['white']}; 
    padding: 14px 15px; 
    text-align: left; 
    font-size: 14px; 
    text-transform: uppercase; 
    letter-spacing: 1px; 
    font-weight: 700;
}}
.race-table td {{ 
    padding: 14px 15px; 
    color: {F1_COLORS['white']}; 
    border-bottom: 1px solid {F1_COLORS['gray']}; 
    font-weight: 500;
}}
.race-table tr.zebra {{ 
    background-color: rgba(255, 255, 255, 0.05); 
}}
.race-table tr:hover {{ 
    background-color: {F1_COLORS['gray']}; 
}}
.rank-cell {{ 
    font-weight: 900; 
    font-size: 1.3em; 
    text-align: center; 
}}
.rank-1 {{ 
    color: {F1_COLORS['yellow']}; 
    text-shadow: 0 0 8px rgba(240, 216, 0, 0.7);
}}
.rank-2 {{ 
    color: {F1_COLORS['white']}; 
}}
.rank-3 {{ 
    color: {F1_COLORS['orange']}; 
}}
.loja-cell {{ 
    font-weight: 800; 
    color: {F1_COLORS['white']}; 
    font-size: 1.1em; 
}}

/* Barras de Progresso */
.progress-bar-container {{ 
    background-color: {F1_COLORS['gray']}; 
    border-radius: 10px; 
    overflow: hidden; 
    height: 20px; 
    width: 100%; 
    min-width: 100px; 
    border: 1px solid {F1_COLORS['light_gray']};
}}
.progress-bar {{ 
    background: linear-gradient(90deg, {F1_COLORS['red']}, {F1_COLORS['yellow']});
    height: 100%; 
    border-radius: 10px; 
    text-align: center; 
    color: {F1_COLORS['white']}; 
    font-size: 12px; 
    line-height: 20px; 
    font-weight: 700;
    box-shadow: 0 0 8px rgba(255, 24, 1, 0.6);
}}

/* Sidebar */
.css-1d391kg {{ 
    background-color: {F1_COLORS['black']};
    border-right: 2px solid {F1_COLORS['red']};
}}
.stButton > button {{
    background: linear-gradient(90deg, {F1_COLORS['red']}, {F1_COLORS['yellow']});
    color: {F1_COLORS['white']};
    border: none;
    border-radius: 6px;
    padding: 10px;
    font-weight: 700;
    transition: all 0.3s ease;
}}
.stButton > button:hover {{
    background: linear-gradient(90deg, {F1_COLORS['yellow']}, {F1_COLORS['red']});
    transform: scale(1.03);
}}

/* Cards de Métricas */
.metric-card {{
    background: rgba(30, 30, 30, 0.7);
    border-radius: 8px;
    padding: 15px;
    border-left: 4px solid {F1_COLORS['red']};
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}}

/* Responsividade */
@media (max-width: 640px) {{
    .app-header h1 {{ font-size: 28px !important; }}
    .app-header p {{ font-size: 12px; }}
    .podio-card h2 {{ font-size: 1.5em; }}
    .podio-card h3 {{ font-size: 1em; }}
    .race-table {{ font-size: 0.8em; }}
    .race-table th, .race-table td {{ padding: 8px 6px; }}
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Funções Utilitárias e de Processamento (com cache otimizado)
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Buscando dados do GitHub...")
def get_data_from_github():
    try: 
        return pd.read_excel(GITHUB_FILE_URL, sheet_name=None, engine="openpyxl")
    except Exception as e:
        st.error(f"Erro ao carregar os dados do GitHub: {e}")
        return {}

def set_page(page_name):
    st.session_state.page = page_name

def format_hours_and_minutes(hours_float: float):
    if pd.isna(hours_float) or hours_float < 0: return "0h 00min"
    hours = math.floor(hours_float)
    minutes = round((hours_float - hours) * 60)
    return f"{hours}h {minutes:02d}min"

def get_race_duration_hours(ciclo: str):
    local_month_map = MONTH_DAYS_MAP.copy()
    ano_atual = datetime.now().year
    if (ano_atual % 4 == 0 and ano_atual % 100 != 0) or (ano_atual % 400 == 0):
        local_month_map['Fevereiro'] = 29
    return local_month_map.get(ciclo, 30)

@st.cache_data(show_spinner="Processando dados das etapas...")
def load_and_prepare_data(all_sheets: dict):
    all_data, pesos_records = [], []
    for sheet_name in ETAPA_SHEETS:
        if sheet_name in all_sheets:
            try:
                df_etapa = all_sheets[sheet_name].copy()
                df_etapa.columns = [c.strip() for c in df_etapa.columns]
                if not all(col in df_etapa.columns for col in ['NomeLoja','loja_key','Nota','Ciclo','Período']): 
                    continue
                
                df_etapa.rename(columns={
                    'loja_key': 'Loja', 
                    'NomeLoja': 'Nome_Exibicao', 
                    'Período': 'Periodo'
                }, inplace=True)
                
                for col in ['Ciclo', 'Periodo']: 
                    df_etapa[col] = df_etapa[col].astype(str)
                
                if 'PesoDaEtapa' in df_etapa.columns:
                    nota_num = pd.to_numeric(df_etapa['Nota'], errors='coerce').fillna(0.0)
                    peso_num = pd.to_numeric(df_etapa['PesoDaEtapa'], errors='coerce').fillna(0.0)
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
                        pesos_records.append({
                            'Etapa': r['Etapa'], 
                            'Ciclo': str(r['Ciclo']), 
                            'Periodo': str(r['Periodo']), 
                            'PesoMaximo': float(r['PesoDaEtapa'])
                        })
            except Exception as e:
                st.warning(f"Erro ao processar a planilha {sheet_name}: {str(e)}")
                continue
    
    if not all_data: 
        return pd.DataFrame(), [], pd.DataFrame(), pd.DataFrame()
    
    # Merge otimizado dos dados
    df_merged = all_data[0]
    for df in all_data[1:]:
        df_merged = pd.merge(df_merged, df, on=['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo'], how='outer')
    
    # Ordenação por mês
    month_order = list(MONTH_MAP.keys())
    df_merged['Ciclo_Cat'] = pd.Categorical(df_merged['Ciclo'], categories=month_order, ordered=True)
    df_merged.sort_values(['Ciclo_Cat','Periodo','Nome_Exibicao'], inplace=True, ignore_index=True)
    
    # Para etapas mensais, usar o valor máximo do ciclo
    for etapa in MONTHLY_ETAPAS:
        score_col = f"{etapa}_Score"
        if score_col in df_merged.columns:
            df_merged[score_col] = df_merged.groupby(['Loja', 'Ciclo'])[score_col].transform('max')
    
    # Filtrar colunas de scores
    etapas_scores_cols = [c for c in df_merged.columns if c.endswith('_Score')]
    
    # Preparar dados de períodos e pesos
    periodos_df = df_merged[["Ciclo","Periodo","Ciclo_Cat"]].drop_duplicates().sort_values(["Ciclo_Cat","Periodo"]).reset_index(drop=True)
    etapas_pesos_df = pd.DataFrame(pesos_records)
    
    return df_merged, etapas_scores_cols, periodos_df, etapas_pesos_df

@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas_scores_cols: list, duracao_total_horas: float, baseline_horas: float):
    df_copy = df.copy()
    
    # Garantir que todas as colunas de score existem
    for e in etapas_scores_cols:
        if e not in df_copy.columns:
            df_copy[e] = 0.0
    
    # Calcular scores (excluindo jokers)
    score_cols_sem_coringa = [c for c in etapas_scores_cols if not any(joker in c for joker in JOKER_ETAPAS)]
    df_copy["Boost_Total_Min"] = df_copy[score_cols_sem_coringa].sum(axis=1)
    
    # Calcular posição (baseline + impulso convertido para horas)
    df_copy["Posicao_Horas"] = baseline_horas + (df_copy["Boost_Total_Min"] / 60.0)
    
    # Calcular progresso
    if duracao_total_horas > 0:
        df_copy["Progresso"] = (df_copy["Posicao_Horas"] / duracao_total_horas) * 100.0
    else:
        df_copy["Progresso"] = 0.0
    
    # Calcular tempo faltante
    df_copy["Tempo_Faltante_Horas"] = (duracao_total_horas - df_copy["Posicao_Horas"]).clip(lower=0)
    
    # Calcular ranking
    df_copy["Rank"] = df_copy["Posicao_Horas"].rank(method="dense", ascending=False).astype(int)
    df_copy.sort_values(["Posicao_Horas","Nome_Exibicao"], ascending=[False,True], inplace=True, ignore_index=True)
    
    return df_copy

@st.cache_data(show_spinner="Calculando ranking...")
def filter_and_aggregate_data(data_original: pd.DataFrame, etapas_scores_cols: list, ciclo: str):
    if not ciclo: 
        return pd.DataFrame(), 0, 0
    
    # Filtrar por ciclo
    df = data_original[data_original["Ciclo"] == str(ciclo)].copy()
    if df.empty: 
        return pd.DataFrame(), 0, 0
    
    # Verificar colunas de score disponíveis
    score_cols = [c for c in etapas_scores_cols if c in df.columns]
    if not score_cols: 
        return pd.DataFrame(), 0, 0
    
    # Agregar dados por loja
    id_vars = ['Loja', 'Nome_Exibicao']
    aggregated = df.groupby(id_vars, as_index=False)[score_cols].sum(min_count=0)
    
    # Calcular baseline (dia atual se for o mês atual)
    hoje = datetime.now()
    baseline_horas = 0
    if MONTH_MAP.get(ciclo) == hoje.month and hoje.year == datetime.now().year:
        baseline_horas = hoje.day * 24  # Converter dias em horas
    
    # Obter duração total
    duracao_horas = get_race_duration_hours(ciclo) * 24  # Converter dias em horas
    
    # Calcular scores finais
    final_df = calculate_final_scores(aggregated, etapas_scores_cols, duracao_horas, baseline_horas)
    
    return final_df, duracao_horas, baseline_horas

# ----------------------------------------------------------------------
# Funções de Renderização da Interface (com tema F1)
# ----------------------------------------------------------------------
def render_header_and_periodo(campaign_name: str, ciclo:str, duracao_horas: float, baseline_horas: float):
    st.markdown("<div class='app-header'>", unsafe_allow_html=True)
    st.markdown(f"<h1>🏎️ {campaign_name} 🏁</h1>", unsafe_allow_html=True)
    
    # Calcular informações da corrida
    dias_corrida = duracao_horas / 24
    dias_decorridos = baseline_horas / 24
    dias_restantes = dias_corrida - dias_decorridos
    
    st.markdown(f"""
    <p>
    Ciclo: <b>{ciclo}</b> | 
    Duração da Corrida: <b>{dias_corrida:.0f} dias</b> | 
    Voltas Completas: <b>{dias_decorridos:.0f}</b> | 
    Voltas Restantes: <b>{dias_restantes:.0f}</b>
    </p>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

def render_podio_table(df_final: pd.DataFrame, baseline_horas: float):
    st.markdown("### 🏆 Pódio Atual")
    
    # Configurar colunas com tamanhos diferentes para efeito de pódio
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    # Primeiro lugar (meio, mais alto)
    with col2:
        if len(df_final) > 0:
            row = df_final.iloc[0]
            st.markdown(
                f"""
                <div class='podio-card' style='background: linear-gradient(135deg, {F1_COLORS['yellow']}, {F1_COLORS['orange']}); color: {F1_COLORS['black']};'>
                <h3>🥇 {row['Rank']}º — {row['Nome_Exibicao']}</h3>
                <h2>{format_hours_and_minutes(row['Posicao_Horas'])}</h2>
                <p class='breakdown-text'>({baseline_horas/24:.0f}d de Base + {format_hours_and_minutes(row['Boost_Total_Min'] / 60)} de Impulso)</p>
                <p class='progress-text'>Progresso: {row['Progresso']:.1f}%</p>
                <p class='remaining-text'>Faltam: {format_hours_and_minutes(row['Tempo_Faltante_Horas'])}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Segundo lugar (esquerda)
    with col1:
        if len(df_final) > 1:
            row = df_final.iloc[1]
            st.markdown(
                f"""
                <div class='podio-card' style='background: linear-gradient(135deg, {F1_COLORS['white']}, {F1_COLORS['light_gray']}); color: {F1_COLORS['black']};'>
                <h3>🥈 {row['Rank']}º — {row['Nome_Exibicao']}</h3>
                <h2>{format_hours_and_minutes(row['Posicao_Horas'])}</h2>
                <p class='breakdown-text'>({baseline_horas/24:.0f}d de Base + {format_hours_and_minutes(row['Boost_Total_Min'] / 60)} de Impulso)</p>
                <p class='progress-text'>Progresso: {row['Progresso']:.1f}%</p>
                <p class='remaining-text'>Faltam: {format_hours_and_minutes(row['Tempo_Faltante_Horas'])}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Terceiro lugar (direita)
    with col3:
        if len(df_final) > 2:
            row = df_final.iloc[2]
            st.markdown(
                f"""
                <div class='podio-card' style='background: linear-gradient(135deg, {F1_COLORS['orange']}, #BF5B17); color: {F1_COLORS['white']};'>
                <h3>🥉 {row['Rank']}º — {row['Nome_Exibicao']}</h3>
                <h2>{format_hours_and_minutes(row['Posicao_Horas'])}</h2>
                <p class='breakdown-text'>({baseline_horas/24:.0f}d de Base + {format_hours_and_minutes(row['Boost_Total_Min'] / 60)} de Impulso)</p>
                <p class='progress-text'>Progresso: {row['Progresso']:.1f}%</p>
                <p class='remaining-text'>Faltam: {format_hours_and_minutes(row['Tempo_Faltante_Horas'])}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

def build_pista_fig(data: pd.DataFrame, duracao_total_horas: float) -> go.Figure:
    if data is None or data.empty: 
        return go.Figure()
    
    # Configuração da pista
    CAR_ICON_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/assets/carro-corrida_anim.webp"
    CHECKERED_FLAG_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/assets/checkered-flag.png"
    
    fig = go.Figure()
    
    # Calcular limites do eixo
    max_posicao_carro = data['Posicao_Horas'].max() if not data.empty else 0
    limite_eixo = max(duracao_total_horas, max_posicao_carro) * 1.05
    
    # Desenhar faixas da pista
    for i in range(len(data)):
        fig.add_shape(
            type="rect", 
            x0=0, 
            y0=i-0.4, 
            x1=limite_eixo, 
            y1=i+0.4, 
            line=dict(color=F1_COLORS['white'], width=1), 
            fillcolor=F1_COLORS['asphalt'], 
            layer="below"
        )
        
        # Adicionar linhas de divisão (faixas da pista)
        fig.add_shape(
            type="line", 
            x0=0, 
            y0=i, 
            x1=limite_eixo, 
            y1=i, 
            line=dict(color=F1_COLORS['white'], width=1, dash="dash"), 
            layer="below"
        )
    
    # Linha de partida
    fig.add_shape(
        type="line", 
        x0=0, 
        y0=-0.5, 
        x1=0, 
        y1=len(data)-0.5, 
        line=dict(color=F1_COLORS['red'], width=4, dash="solid"), 
        layer="above"
    )
    
    # Linha de chegada
    fig.add_shape(
        type="line", 
        x0=duracao_total_horas, 
        y0=-0.5, 
        x1=duracao_total_horas, 
        y1=len(data)-0.5, 
        line=dict(color=F1_COLORS['black'], width=6), 
        layer="above"
    )
    
    # Bandeira quadriculada no final
    fig.add_layout_image(
        dict(
            source=CHECKERED_FLAG_URL,
            xref="x", 
            yref="y", 
            x=duracao_total_horas, 
            y=len(data)/2,
            sizex=duracao_total_horas * 0.05,
            sizey=len(data) * 0.8,
            layer="above",
            xanchor="right",
            yanchor="middle"
        )
    )
    
    # Preparar textos para hover
    hover_texts = [
        f"<b>{row['Nome_Exibicao']}</b><br>"
        f"Posição: {row['Posicao_Horas']:.2f}h<br>"
        f"Progresso: {row['Progresso']:.1f}%<br>"
        f"Impulso: {format_hours_and_minutes(row['Boost_Total_Min'] / 60)}<br>"
        f"Faltam: {format_hours_and_minutes(row['Tempo_Faltante_Horas'])}<br>"
        f"Rank: #{row['Rank']}"
        for i, row in data.iterrows()
    ]
    
    # Adicionar ícones dos carros
    for i, row in data.iterrows():
        fig.add_layout_image(
            dict(
                source=CAR_ICON_URL,
                xref="x", 
                yref="y", 
                x=row['Posicao_Horas'], 
                y=i,
                sizex=max(1.8, duracao_total_horas / 20),
                sizey=0.8,
                layer="above",
                xanchor="center",
                yanchor="middle"
            )
        )
    
    # Adicionar nomes das lojas
    y_text = data.index - 0.35  # Desloca o texto para baixo
    fig.add_trace(go.Scatter(
        x=data['Posicao_Horas'],
        y=y_text,
        mode='text',
        text=data['Nome_Exibicao'],
        textposition="top center",
        textfont=dict(color=F1_COLORS['white'], size=10, family='Arial Black'),
        hoverinfo='text',
        hovertext=hover_texts,
        showlegend=False
    ))
    
    # Configurar layout do gráfico
    fig.update_xaxes(
        range=[-limite_eixo*0.02, limite_eixo * 1.05], 
        title_text="Avanço na Pista (horas) →", 
        fixedrange=True, 
        tick0=0, 
        dtick=24,  # Marcadores a cada 24 horas (1 dia)
        showgrid=True,
        gridcolor=F1_COLORS['gray'],
        zeroline=False
    )
    
    fig.update_yaxes(
        showgrid=False, 
        zeroline=False, 
        tickvals=list(range(len(data))), 
        ticktext=[], 
        fixedrange=True
    )
    
    fig.update_layout(
        height=max(600, 300 + 40*len(data)),
        margin=dict(l=10, r=10, t=80, b=40),
        plot_bgcolor=F1_COLORS['black'],
        paper_bgcolor=F1_COLORS['black'],
        title="Pista do Circuito MiniPreço F1",
        title_font=dict(size=20, color=F1_COLORS['white'], family='Arial Black'),
        xaxis_title_font=dict(color=F1_COLORS['white']),
        showlegend=False
    )
    
    return fig

def render_geral_page():
    st.header("🏁 Visão Geral da Corrida")
    
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Sem dados para exibir com a seleção atual.")
        return
    
    duracao_horas = st.session_state.get('duracao_horas', 0)
    baseline_horas = st.session_state.get('baseline_horas', 0)
    
    # Converter horas em dias para exibição
    dias_totais = duracao_horas / 24
    dias_decorridos = baseline_horas / 24
    dias_restantes = dias_totais - dias_decorridos
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>Voltas Restantes</h3><h2>{dias_restantes:.0f}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>Líder Atual</h3><h2>{df_final["Nome_Exibicao"].iloc[0] if not df_final.empty else "N/A"}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>Total de Equipes</h3><h2>{len(df_final)}</h2></div>', unsafe_allow_html=True)
    with col4:
        progresso_medio = df_final["Progresso"].mean() if not df_final.empty else 0
        st.markdown(f'<div class="metric-card"><h3>Progresso Médio</h3><h2>{progresso_medio:.1f}%</h2></div>', unsafe_allow_html=True)
    
    # Pódio
    render_podio_table(df_final, baseline_horas)
    
    # Pista de corrida
    st.markdown("### 🏎️ Pista de Corrida do Circuito")
    fig_pista = build_pista_fig(df_final, duracao_horas)
    st.plotly_chart(fig_pista, use_container_width=True)
    
    # Tabela de classificação
    st.markdown("### 📊 Classificação Completa")
    
    show_details = st.toggle("Mostrar detalhes por etapa", value=False, key="detalhes_etapa")
    score_cols = st.session_state.get('etapas_scores_cols', [])
    score_cols_with_data = [col for col in score_cols if col in df_final.columns and df_final[col].sum() > 0]
    
    # Preparar cabeçalhos da tabela
    headers = ["Pos", "Equipe", "Impulso Total", "Avanço", "Progresso"]
    if show_details:
        headers.extend([col.replace('_Score', '') for col in score_cols_with_data])
    
    # Construir tabela HTML
    html = [f"<table class='race-table'><thead><tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr></thead><tbody>"]
    
    for i, row in df_final.iterrows():
        rank, zebra_class = row['Rank'], 'zebra' if i % 2 != 0 else ''
        rank_class = f'rank-{rank}' if rank <= 3 else ''
        
        # Barra de progresso
        prog_bar = f"<div class='progress-bar-container'><div class='progress-bar' style='width: {min(row["Progresso"], 100)}%;'>{row["Progresso"]:.1f}%</div></div>"
        
        # Linha da tabela
        html.append(f"<tr class='{zebra_class}'>")
        html.append(f"<td class='rank-cell {rank_class}'>{rank}</td>")
        html.append(f"<td class='loja-cell'>{row['Nome_Exibicao']}</td>")
        html.append(f"<td>+{format_hours_and_minutes(row['Boost_Total_Min'] / 60)}</td>")
        html.append(f"<td>{row['Posicao_Horas']:.2f}h</td>")
        html.append(f"<td>{prog_bar}</td>")
        
        # Colunas detalhadas (se habilitado)
        if show_details:
            for col in score_cols_with_data:
                html.append(f"<td>{format_hours_and_minutes(row.get(col, 0) / 60)}</td>")
        
        html.append("</tr>")
    
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)

def render_loja_page():
    st.header("🏪 Visão por Loja")
    
    df_final = st.session_state.get('df_final')
    etapas_pesos_df = st.session_state.get('etapas_pesos_df', pd.DataFrame())
    
    if df_final is None or df_final.empty:
        st.warning("Selecione um Ciclo para ver os detalhes da loja.")
        return
    
    loja_options = sorted(df_final["Nome_Exibicao"].unique().tolist())
    loja_sel = st.selectbox("Selecione a Loja:", loja_options, key="loja_select")
    
    if loja_sel:
        loja_row = df_final[df_final["Nome_Exibicao"] == loja_sel].iloc[0]
        
        # Métricas da loja
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            st.markdown(f'<div class="metric-card"><h3>Avanço na Pista</h3><h2>{loja_row["Posicao_Horas"]:.2f}h</h2></div>', unsafe_allow_html=True)
        with col2: 
            st.markdown(f'<div class="metric-card"><h3>Impulso (Notas)</h3><h2>+{format_hours_and_minutes(loja_row["Boost_Total_Min"] / 60)}</h2></div>', unsafe_allow_html=True)
        with col3: 
            st.markdown(f'<div class="metric-card"><h3>Progresso Total</h3><h2>{loja_row["Progresso"]:.1f}%</h2></div>', unsafe_allow_html=True)
        with col4: 
            st.markdown(f'<div class="metric-card"><h3>Posição Atual</h3><h2>#{loja_row["Rank"]}</h2></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Análise de desempenho por etapa
        ciclo = st.session_state.ciclo
        if not etapas_pesos_df.empty:
            df_pesos_ciclo = etapas_pesos_df[etapas_pesos_df['Ciclo'] == ciclo]
            pesos_etapas = df_pesos_ciclo.groupby('Etapa')['PesoMaximo'].sum().to_dict()
            
            etapas_data = []
            for etapa_col in st.session_state.etapas_scores_cols:
                peso_max = pesos_etapas.get(etapa_col, 0)
                if peso_max > 0:
                    etapa_name = etapa_col.replace('_Score', '')
                    score_atual = loja_row.get(etapa_col, 0)
                    percentual = (score_atual / peso_max) * 100 if peso_max > 0 else 0
                    
                    etapas_data.append({
                        'Etapa': etapa_name, 
                        'Impulso Atual': score_atual, 
                        'Impulso Máximo': peso_max, 
                        'Gap': peso_max - score_atual,
                        'Percentual': percentual
                    })
            
            if etapas_data:
                df_melhoria = pd.DataFrame(etapas_data).sort_values('Gap', ascending=False, ignore_index=True)
                
                col_insight, col_chart = st.columns([1, 2])
                
                with col_insight:
                    st.subheader("📈 Pontos de Melhoria")
                    st.markdown("Oportunidades para ganhar impulso e avançar no circuito:")
                    
                    top_melhorias = df_melhoria[df_melhoria['Gap'] > 0.1].head(3)
                    if top_melhorias.empty: 
                        st.success("🎉 Parabéns! A loja atingiu o impulso máximo em todas as etapas!")
                    else:
                        for _, row in top_melhorias.iterrows(): 
                            st.info(f"**{row['Etapa']}**: Foque aqui para ganhar até **{format_hours_and_minutes(row['Gap'] / 60)}**.")
                
                with col_chart:
                    st.subheader("📊 Desempenho por Etapa")
                    
                    # Gráfico de radar
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatterpolar(
                        r=df_melhoria['Percentual'],
                        theta=df_melhoria['Etapa'],
                        fill='toself',
                        fillcolor='rgba(255, 24, 1, 0.4)',
                        line=dict(color=F1_COLORS['red'], width=2),
                        name='Desempenho Atual'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(
                                visible=True, 
                                range=[0, 100],
                                tickfont=dict(color=F1_COLORS['white']),
                                gridcolor=F1_COLORS['gray']
                            ),
                            angularaxis=dict(
                                gridcolor=F1_COLORS['gray'],
                                linecolor=F1_COLORS['gray'],
                                tickfont=dict(color=F1_COLORS['white'])
                            )
                        ),
                        showlegend=True,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color=F1_COLORS['white'],
                        margin=dict(l=40, r=40, t=80, b=40),
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

def render_etapa_page():
    st.header("📋 Visão por Etapa")
    
    df_final = st.session_state.get('df_final')
    etapas_scores_cols = st.session_state.get('etapas_scores_cols', [])
    
    if df_final is None or df_final.empty:
        st.warning("Selecione um Ciclo para ver os detalhes da etapa.")
        return
    
    etapa_options = [c.replace('_Score', '') for c in etapas_scores_cols 
                     if c in df_final.columns and df_final[c].sum() > 0]
    
    etapa_sel = st.selectbox("Selecione a Etapa:", sorted(etapa_options), key="etapa_select")
    
    if etapa_sel:
        col_name = f"{etapa_sel}_Score"
        
        # Dados da etapa selecionada
        df_etapa = df_final[['Nome_Exibicao', col_name]].copy()
        df_etapa.rename(columns={col_name: "Impulso na Etapa (min)"}, inplace=True)
        df_etapa.sort_values("Impulso na Etapa (min)", ascending=False, inplace=True)
        
        # Calcular estatísticas
        impulso_max = df_etapa["Impulso na Etapa (min)"].max()
        impulso_medio = df_etapa["Impulso na Etapa (min)"].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card"><h3>Maior Impulso</h3><h2>{format_hours_and_minutes(impulso_max / 60)}</h2></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><h3>Impulso Médio</h3><h2>{format_hours_and_minutes(impulso_medio / 60)}</h2></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><h3>Lojas Participantes</h3><h2>{len(df_etapa)}</h2></div>', unsafe_allow_html=True)
        
        st.subheader(f"🏅 Ranking da Etapa: {etapa_sel}")
        
        # Formatar tabela
        df_display = df_etapa.head(10).copy()
        df_display["Posição"] = range(1, len(df_display) + 1)
        df_display["Impulso na Etapa"] = df_display["Impulso na Etapa (min)"].apply(
            lambda x: format_hours_and_minutes(x / 60)
        )
        
        # Exibir tabela
        st.dataframe(
            df_display[["Posição", "Nome_Exibicao", "Impulso na Etapa"]], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Gráfico de barras
        if len(df_etapa) > 0:
            st.subheader("📈 Comparativo de Desempenho")
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df_etapa.head(10)["Nome_Exibicao"],
                y=df_etapa.head(10)["Impulso na Etapa (min)"] / 60,  # Converter para horas
                marker_color=F1_COLORS['red'],
                hovertemplate="<b>%{x}</b><br>Impulso: %{y:.2f}h<extra></extra>"
            ))
            
            fig.update_layout(
                xaxis_title="Lojas",
                yaxis_title="Impulso (horas)",
                plot_bgcolor=F1_COLORS['black'],
                paper_bgcolor=F1_COLORS['black'],
                font=dict(color=F1_COLORS['white']),
                xaxis=dict(tickangle=45),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# Estrutura Principal do App
# ----------------------------------------------------------------------
def main():
    # Inicializar estado da sessão
    if 'page' not in st.session_state:
        st.session_state.page = "Geral"
    
    # Carregar dados
    with st.spinner("Carregando base de dados..."):
        all_sheets = get_data_from_github()
    
    if not all_sheets:
        st.error("Não foi possível carregar os dados. Verifique a conexão e tente novamente.")
        st.stop()
    
    # Processar dados
    data, etapas_scores, periodos_df, etapas_pesos_df = load_and_prepare_data(all_sheets)
    
    # Armazenar dados na sessão
    st.session_state.update({
        'data_original': data, 
        'etapas_scores_cols': etapas_scores, 
        'periodos_df': periodos_df, 
        'etapas_pesos_df': etapas_pesos_df
    })
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-retailhub.com/minipreco/096c9b29-4ac3-425f-8322-be76b794f040.webp", use_container_width=True)
        st.markdown("---")
        st.markdown("<h3>Seleção de Ciclo</h3>", unsafe_allow_html=True)
        
        # Obter ciclos disponíveis
        ciclos_unicos = periodos_df["Ciclo"].dropna().unique().tolist() if not periodos_df.empty else []
        
        if not ciclos_unicos:
            st.warning("Nenhum ciclo encontrado nos dados.")
            st.stop()
        
        # Ordenar ciclos
        sort_order_map = {name: i for i, name in enumerate(MONTH_MAP.keys())}
        sorted_ciclos = sorted(ciclos_unicos, key=lambda m: sort_order_map.get(m, -1))
        
        # Selecionar ciclo
        ciclo_selecionado = st.selectbox(
            "Selecione o Ciclo", 
            sorted_ciclos, 
            index=len(sorted_ciclos)-1, 
            label_visibility="collapsed",
            key="ciclo_select"
        )
        
        st.session_state.ciclo = ciclo_selecionado
        
        st.markdown("---")
        st.markdown("<h3>Navegação</h3>", unsafe_allow_html=True)
        
        # Botões de navegação
        st.button(
            "🏁 Visão Geral", 
            on_click=set_page, 
            args=("Geral",), 
            use_container_width=True, 
            type="primary" if st.session_state.page == "Geral" else "secondary"
        )
        
        st.button(
            "🏪 Visão por Loja", 
            on_click=set_page, 
            args=("Loja",), 
            use_container_width=True, 
            type="primary" if st.session_state.page == "Loja" else "secondary"
        )
        
        st.button(
            "📋 Visão por Etapa", 
            on_click=set_page, 
            args=("Etapa",), 
            use_container_width=True, 
            type="primary" if st.session_state.page == "Etapa" else "secondary"
        )
    
    # Processar dados para o ciclo selecionado
    if st.session_state.get('ciclo'):
        df_final, duracao_horas, baseline_horas = filter_and_aggregate_data(
            st.session_state.data_original, 
            st.session_state.etapas_scores_cols, 
            st.session_state.ciclo
        )
        
        st.session_state.update({
            'df_final': df_final, 
            'duracao_horas': duracao_horas, 
            'baseline_horas': baseline_horas
        })
        
        # Renderizar cabeçalho
        render_header_and_periodo(
            "Circuito MiniPreço F1", 
            st.session_state.ciclo, 
            st.session_state.get('duracao_horas', 0), 
            st.session_state.get('baseline_horas', 0)
        )
        
        # Renderizar página selecionada
        page = st.session_state.page
        if page == "Geral":
            render_geral_page()
        elif page == "Loja":
            render_loja_page()
        elif page == "Etapa":
            render_etapa_page()

if __name__ == "__main__":
    main()
