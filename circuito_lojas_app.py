# -*- coding: utf-8 -*-
# circuito_lojas_app.py — VERSÃO COM NOVA LÓGICA DE CORRIDA (HORAS/MINUTOS)

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from io import BytesIO

# ----------------------------------------------------------------------
# Configuração inicial do Streamlit
# ----------------------------------------------------------------------
st.set_page_config(page_title="Circuito MiniPreço", page_icon="🏎️", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------------------------------------------------
# Fonte de dados: GitHub (raw)
# ----------------------------------------------------------------------
GITHUB_FILE_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/BaseCircuito.xlsx"

@st.cache_data(ttl=3600) # Cache por 1 hora
def get_data_from_github():
    """Baixa o arquivo BaseCircuito.xlsx direto do GitHub e retorna como dict de DataFrames."""
    try:
        # Usando BytesIO para ler o conteúdo da URL diretamente com pandas
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
MONTHLY_ETAPAS = ["Engajamento", "VisualMerchandising", "Meta"]
JOKER_ETAPAS = ["Meta"] # Etapa Coringa não conta para pontuação máxima

PREMIO_TOP1 = "Bônus Ouro + Folga"
PREMIO_TOP3 = "Bônus Prata"
PREMIO_TOP5 = "Bônus Bronze"
PREMIO_DEMAIS = "Reconhecimento + Plano de Ação"

# ----------------------------------------------------------------------
# CSS (visuais) - Mantido como no original para consistência
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
    # Checa se o ano atual é bissexto para Fevereiro
    ano_atual = datetime.now().year
    if (ano_atual % 4 == 0 and ano_atual % 100 != 0) or (ano_atual % 400 == 0):
        month_map['Fevereiro'] = 29
    return month_map.get(ciclo, 30) # Default para 30 se não encontrar

# ----------------------------------------------------------------------
# Render do pódio
# ----------------------------------------------------------------------
def render_podio_table(df_final: pd.DataFrame):
    if df_final is None or df_final.empty:
        st.info("Sem dados para exibir no pódio.")
        return

    # Ganhadores são os que completaram 100% ou mais
    winners = df_final[df_final["Progresso"] >= 100.0].sort_values("Rank").reset_index(drop=True)

    if winners.empty:
        st.markdown("🏁 **Nenhuma loja cruzou a linha de chegada ainda. A corrida continua!**")
        st.markdown("Confira o Top 3 atual:")
        top3 = df_final.head(3).reset_index(drop=True)
        cols = st.columns(3)
        for i in range(3):
            if i < len(top3):
                row = top3.loc[i]
                nome = row["Nome_Exibicao"]; avanco = row["Avanço_Total"]; progresso = row["Progresso"]; rank = row["Rank"]
                tempo_faltante = row.get('Tempo_Faltante_min', 0)
                
                with cols[i]:
                    st.markdown(
                        f"<div style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0f172a,#111827);color:white; text-align:center; height: 100%;'>"
                        f"<h3 style='margin:0'>{i+1}º — {nome}</h3>"
                        f"<p style='margin:6px 0 0 0; opacity:0.85'>Rank: #{rank}</p>"
                        f"<h2 style='margin:8px 0 0 0'>{avanco:.1f} min</h2>"
                        f"<p style='margin:6px 0 0 0; font-size:14px; opacity:0.85'>Progresso: {progresso:.1f}%</p>"
                        f"<p style='margin:4px 0 0 0; font-size:12px; opacity:0.7'>Faltam: {tempo_faltante:.1f} min</p>"
                        f"</div>", unsafe_allow_html=True
                    )
            else:
                with cols[i]:
                    st.markdown(
                        "<div style='padding:18px; border-radius:12px; background:rgba(255,255,255,0.03);color:#fff; text-align:center; opacity:0.5; height: 100%;'>"
                        f"<h3 style='margin:0'>{i+1}º</h3><p style='margin:6px 0 0 0; opacity:0.7'>—</p></div>",
                        unsafe_allow_html=True
                    )
        return

    html_table = []
    html_table.append("<table class='podio-track' role='table'>")
    html_table.append("<thead><tr>")
    html_table.append("<th style='width:80px;'>#</th>")
    html_table.append("<th>Loja</th>")
    html_table.append("<th style='width:120px; text-align:center;'>Avanço (min)</th>")
    html_table.append("<th style='width:140px; text-align:center;'>Progresso</th>")
    html_table.append("<th style='width:220px; text-align:center;'>Premiação</th>")
    html_table.append("</tr></thead><tbody>")

    for _, row in winners.iterrows():
        pos = int(row["Rank"]); nome = row["Nome_Exibicao"]; avanco = row["Avanço_Total"]; progresso = row["Progresso"]
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
        pontos_html = f"<td class='podio-col-points'>{avanco:.1f} min</td>"
        progresso_html = f"<td style='text-align:center; padding:12px;'><div class='podio-finish'><span class='checkered'></span> {progresso:.1f}%</div></td>"
        premio_html = f"<td style='text-align:center;'><span class='podio-prize {premio_class}'>{premio}</span></td>"

        html_table.append(f"<tr class='podio-row'>{lane_html}{loja_html}{pontos_html}{progresso_html}{premio_html}</tr>")

    html_table.append("</tbody></table>")
    st.markdown("### 🏆 Pódio — Lojas que cruzaram a linha de chegada!", unsafe_allow_html=True)
    st.markdown("".join(html_table), unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Carregamento & preparação de dados
# ----------------------------------------------------------------------
def load_and_prepare_data(all_sheets: dict):
    all_data = []
    pesos_records = []

    for sheet_name in ETAPA_SHEETS:
        if sheet_name in all_sheets:
            try:
                df_etapa = all_sheets[sheet_name].copy()
                df_etapa.columns = [c.strip() for c in df_etapa.columns]

                if not all(col in df_etapa.columns for col in ['NomeLoja','loja_key','Nota','Ciclo','Período']):
                    continue

                df_etapa['Ciclo'] = df_etapa['Ciclo'].astype(str)
                df_etapa['Período'] = df_etapa['Período'].astype(str)
                df_etapa = df_etapa.rename(columns={'loja_key': 'Loja', 'NomeLoja': 'Nome_Exibicao', 'Período': 'Periodo'})
                
                # O avanço (minutos) é o resultado da Nota * PesoDaEtapa
                if 'PesoDaEtapa' in df_etapa.columns:
                    nota_num = pd.to_numeric(df_etapa['Nota'], errors='coerce').fillna(0.0)
                    peso_num = pd.to_numeric(df_etapa['PesoDaEtapa'], errors='coerce').fillna(0.0)
                    df_etapa['Score_Etapa'] = nota_num * peso_num
                else: # Caso uma etapa não tenha peso, a nota vira o score
                    df_etapa['Score_Etapa'] = pd.to_numeric(df_etapa['Nota'], errors='coerce').fillna(0.0)

                df_consolidado = df_etapa[['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo', 'Score_Etapa']].copy()
                df_consolidado.rename(columns={'Score_Etapa': f'{sheet_name}_Score'}, inplace=True)
                all_data.append(df_consolidado)

                # Armazena os pesos máximos possíveis para cada etapa, ciclo e período
                if 'PesoDaEtapa' in df_etapa.columns and sheet_name not in JOKER_ETAPAS:
                    pesos_gp = df_etapa.groupby(['Ciclo','Periodo'])['PesoDaEtapa'].sum().reset_index()
                    pesos_gp['Etapa'] = f'{sheet_name}_Score'
                    for _, r in pesos_gp.iterrows():
                        pesos_records.append({'Etapa': r['Etapa'], 'Ciclo': str(r['Ciclo']), 'Periodo': str(r['Periodo']), 'PesoMaximo': float(r['PesoDaEtapa'])})

            except Exception as e:
                st.warning(f"Erro ao processar a aba '{sheet_name}': {e}")
                continue

    if not all_data:
        return pd.DataFrame(), [], pd.DataFrame(), pd.DataFrame()

    # Combina DFs de todas as etapas
    combined_df = all_data[0]
    for i in range(1, len(all_data)):
        combined_df = pd.merge(combined_df, all_data[i], on=['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo'], how='outer')

    # Ordena por Ciclo e Período
    month_order = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    combined_df['Ciclo_Cat'] = pd.Categorical(combined_df['Ciclo'], categories=month_order, ordered=True)
    combined_df = combined_df.sort_values(['Ciclo_Cat','Periodo','Nome_Exibicao']).reset_index(drop=True)

    # Propaga scores de etapas mensais para todos os períodos do mesmo ciclo
    for etapa in MONTHLY_ETAPAS:
        score_col = f"{etapa}_Score"
        if score_col in combined_df.columns:
            combined_df[score_col] = combined_df.groupby(['Loja', 'Ciclo'])[score_col].transform('max')

    etapas_scores_cols = [c for c in combined_df.columns if c.endswith('_Score')]
    periodos_df = combined_df[["Ciclo","Periodo","Ciclo_Cat"]].drop_duplicates().sort_values(["Ciclo_Cat","Periodo"]).reset_index(drop=True)
    etapas_pesos_df = pd.DataFrame(pesos_records)

    return combined_df, etapas_scores_cols, periodos_df, etapas_pesos_df

# ----------------------------------------------------------------------
# Cálculo de pontuação final
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas_scores_cols: list, duracao_total_min: float):
    df_copy = df.copy()
    
    # Garante que todas as colunas de etapa existem
    for e in etapas_scores_cols:
        if e not in df_copy.columns:
            df_copy[e] = 0.0

    # Calcula o avanço total em minutos e o progresso
    score_cols_sem_coringa = [c for c in etapas_scores_cols if not any(joker in c for joker in JOKER_ETAPAS)]
    df_copy["Avanço_Total"] = df_copy[score_cols_sem_coringa].sum(axis=1)
    
    if duracao_total_min > 0:
        df_copy["Progresso"] = (df_copy["Avanço_Total"] / duracao_total_min) * 100.0
    else:
        df_copy["Progresso"] = 0.0

    df_copy["Tempo_Faltante_min"] = (duracao_total_min - df_copy["Avanço_Total"]).clip(lower=0)
    df_copy["Rank"] = df_copy["Avanço_Total"].rank(method="dense", ascending=False).astype(int)
    
    df_copy.sort_values(["Avanço_Total","Nome_Exibicao"], ascending=[False,True], inplace=True)
    return df_copy.reset_index(drop=True)

# ----------------------------------------------------------------------
# Filtragem e agregação
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def filter_and_aggregate_data(data_original: pd.DataFrame, etapas_scores_cols: list, ciclo: str, periodos: list):
    if not ciclo or not periodos:
        return pd.DataFrame()

    df = data_original[data_original["Ciclo"].astype(str) == str(ciclo)].copy()
    if df.empty: return pd.DataFrame()

    if "Todos" not in periodos:
        df = df[df["Periodo"].astype(str).isin([str(p) for p in periodos])]
    if df.empty: return pd.DataFrame()

    score_cols_presentes = [c for c in etapas_scores_cols if c in df.columns]
    if not score_cols_presentes: return pd.DataFrame()
    
    # Agrega os scores (soma) para o período selecionado
    aggregated = df.groupby(['Loja','Nome_Exibicao'], as_index=False)[score_cols_presentes].sum(min_count=1)
    
    # Adiciona colunas de score faltantes com 0 para o cálculo final
    for col in etapas_scores_cols:
        if col not in aggregated.columns:
            aggregated[col] = 0.0

    # Calcula a duração da corrida para o ciclo
    duracao_horas = get_race_duration_hours(ciclo)
    duracao_minutos = duracao_horas * 60.0
    
    final_df = calculate_final_scores(aggregated, etapas_scores_cols, duracao_minutos)
    return final_df, duracao_horas, duracao_minutos

# ----------------------------------------------------------------------
# Visual: pista de corrida
# ----------------------------------------------------------------------
def build_pista_fig(data: pd.DataFrame, duracao_total_min: float) -> go.Figure:
    if data is None or data.empty:
        return go.Figure()

    CAR_ICON_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/afdcbb50f1132d94c34ae85bb5dee657bef4eac2/assets/carro-corrida_anim.webp"
    fig = go.Figure()
    num_lojas = len(data)
    y_positions = np.arange(num_lojas)
    
    max_minutos = duracao_total_min if duracao_total_min > 0 else (data["Avanço_Total"].max() if not data.empty else 100)

    # Adiciona as pistas de fundo
    for y in y_positions:
        fig.add_shape(type="rect", x0=0, y0=y-0.45, x1=max_minutos, y1=y+0.45,
                      line=dict(width=0), fillcolor="#2C3E50", layer="below")

    # Adiciona a linha de chegada quadriculada
    flag_width = max_minutos * 0.04
    num_cols_flag = 4
    square_size = flag_width / num_cols_flag
    y_steps = np.arange(-0.5, num_lojas, square_size)
    for i, y_start in enumerate(y_steps):
        for j in range(num_cols_flag):
            x_start = max_minutos
            color = "white" if (i + j) % 2 == 0 else "black"
            fig.add_shape(type="rect", x0=x_start + (j * square_size), y0=y_start,
                          x1=x_start + ((j+1) * square_size), y1=y_start + square_size,
                          line=dict(width=0.5, color="black"), fillcolor=color, layer="above")

    # Adiciona os carros
    for y, row in zip(y_positions, data.itertuples()):
        x_carro = row.Avanço_Total
        fig.add_layout_image(
            dict(source=CAR_ICON_URL, xref="x", yref="y", x=x_carro, y=y,
                 sizex=max_minutos * 0.08, sizey=0.8, xanchor="center", yanchor="middle", layer="above")
        )
        fig.add_trace(go.Scatter(
            x=[x_carro], y=[y-0.5], mode="text", text=[row.Nome_Exibicao],
            textfont=dict(size=9, color="rgba(255,255,255,0.9)"), hoverinfo="skip", showlegend=False
        ))
        
        hover = (f"<b>{row.Nome_Exibicao}</b><br>"
                 f"Avanço: {row.Avanço_Total:.1f} min<br>"
                 f"Progresso: {row.Progresso:.1f}%<br>"
                 f"Faltam: {row.Tempo_Faltante_min:.1f} min<br>"
                 f"Rank: #{int(row.Rank)}")
        fig.add_trace(go.Scatter(
            x=[x_carro], y=[y], mode='markers', marker=dict(color='rgba(0,0,0,0)', size=25),
            hoverinfo='text', hovertext=hover, showlegend=False
        ))

    fig.update_xaxes(range=[0, max_minutos * 1.05], title_text="Avanço na Pista (minutos) →", fixedrange=True)
    fig.update_yaxes(showgrid=False, zeroline=False, tickmode="array", tickvals=y_positions, ticktext=[], fixedrange=True)
    fig.update_layout(height=max(400, 200 + 40*num_lojas), margin=dict(l=10, r=10, t=80, b=40),
                      plot_bgcolor="#1A2A3A", paper_bgcolor="rgba(26,42,58,0.7)")
    return fig

# ----------------------------------------------------------------------
# Lógica Principal do Aplicativo (renders)
# ----------------------------------------------------------------------
def render_header_and_periodo(campaign_name: str, periodo_inicio: str | None, periodo_fim: str | None, duracao_horas: float):
    st.markdown("<div class='app-header'>", unsafe_allow_html=True)
    st.markdown(f"<h1>{campaign_name}</h1>", unsafe_allow_html=True)
    
    periodo_str = ""
    if periodo_inicio and periodo_fim:
        if periodo_inicio == periodo_fim:
            periodo_str = f"{periodo_inicio}"
        else:
            periodo_str = f"{periodo_inicio} → {periodo_fim}"
    
    duracao_str = f"Duração da corrida: **{duracao_horas:.0f} horas**"
    
    st.markdown(f"<p>{periodo_str} — {duracao_str}</p>", unsafe_allow_html=True)
    st.markdown("---")

def render_geral_page():
    st.header("Visão Geral da Corrida")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Sem dados para exibir com a seleção atual. Escolha um Ciclo e Período na barra lateral.")
        return

    render_podio_table(df_final)

    st.markdown("### Pista de Corrida do Circuito")
    duracao_total_min = st.session_state.get('duracao_total_min', 0.0)
    fig_pista = build_pista_fig(df_final, duracao_total_min)
    st.plotly_chart(fig_pista, use_container_width=True)

    st.markdown("### Classificação Completa")
    df_classificacao = df_final.copy()
    
    etapa_columns = [col for col in df_classificacao.columns if col.endswith('_Score')]
    rename_dict = {col: f"{col.replace('_Score', '')} (min)" for col in etapa_columns}
    df_classificacao.rename(columns=rename_dict, inplace=True)
    
    colunas_finais = ['Rank', 'Nome_Exibicao'] + list(rename_dict.values()) + ['Avanço_Total', 'Progresso', 'Tempo_Faltante_min']
    df_display = df_classificacao[colunas_finais].copy()
    df_display.rename(columns={'Avanço_Total': 'Avanço Total (min)', 'Tempo_Faltante_min': 'Faltam (min)'}, inplace=True)

    # Formatação para exibição
    for col in list(rename_dict.values()):
        df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    df_display['Avanço Total (min)'] = df_display['Avanço Total (min)'].apply(lambda x: f"{x:.1f}")
    df_display['Progresso'] = df_display['Progresso'].apply(lambda x: f"{x:.1f}%")
    df_display['Faltam (min)'] = df_display['Faltam (min)'].apply(lambda x: f"{x:.1f}")

    st.dataframe(df_display, use_container_width=True, hide_index=True)

def render_loja_page():
    st.header("Visão por Loja")
    df_final = st.session_state.get('df_final')
    if df_final is None or df_final.empty:
        st.warning("Selecione um Ciclo e Período no menu lateral.")
        return

    loja_options = sorted(df_final["Nome_Exibicao"].unique().tolist())
    loja_sel = st.selectbox("Selecione a Loja:", loja_options)

    loja_row = df_final[df_final["Nome_Exibicao"] == loja_sel].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avanço Total", f"{loja_row['Avanço_Total']:.1f} min")
    with col2:
        st.metric("Progresso na Corrida", f"{loja_row['Progresso']:.1f}%")
    with col3:
        st.metric("Rank Atual", f"#{int(loja_row['Rank'])}")
    with col4:
        st.metric("Tempo Faltante", f"{loja_row['Tempo_Faltante_min']:.1f} min")
    
    st.markdown("---")
    
    # Gráfico de Radar para pontos de melhoria
    ciclo = st.session_state.ciclo
    periodos = st.session_state.periodos
    etapas_pesos_df = st.session_state.get('etapas_pesos_df', pd.DataFrame())

    if not etapas_pesos_df.empty:
        df_pesos_ciclo = etapas_pesos_df[etapas_pesos_df['Ciclo'] == ciclo]
        if "Todos" not in periodos:
            df_pesos_ciclo = df_pesos_ciclo[df_pesos_ciclo['Periodo'].isin(periodos)]
        
        pesos_etapas = df_pesos_ciclo.groupby('Etapa')['PesoMaximo'].sum().to_dict()

        etapas_data = []
        for etapa_col, peso_max in pesos_etapas.items():
            if peso_max > 0:
                etapa_name = etapa_col.replace('_Score', '')
                score_atual = loja_row.get(etapa_col, 0)
                gap = peso_max - score_atual
                etapas_data.append({
                    'Etapa': etapa_name, 'Avanço Atual (min)': score_atual,
                    'Avanço Máximo (min)': peso_max, 'Gap (min)': gap
                })

        if etapas_data:
            df_melhoria = pd.DataFrame(etapas_data).sort_values('Gap (min)', ascending=False).reset_index(drop=True)
            
            col_insight, col_chart = st.columns([1, 2])
            with col_insight:
                st.subheader("Pontos de Melhoria")
                st.markdown("Oportunidades para ganhar minutos e avançar no circuito:")
                top_melhorias = df_melhoria[df_melhoria['Gap (min)'] > 0.1].head(3)
                if top_melhorias.empty:
                    st.success("🎉 Parabéns! A loja atingiu o avanço máximo em todas as etapas!")
                else:
                    for _, row in top_melhorias.iterrows():
                        st.info(f"**{row['Etapa']}**: Foque aqui para ganhar até **{row['Gap (min)']:.1f}** minutos.")

            with col_chart:
                st.subheader("Desempenho por Etapa")
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=df_melhoria['Avanço Máximo (min)'], theta=df_melhoria['Etapa'], mode='lines', line=dict(color='rgba(255, 255, 255, 0.4)'), name='Avanço Máximo'))
                fig.add_trace(go.Scatterpolar(r=df_melhoria['Avanço Atual (min)'], theta=df_melhoria['Etapa'], fill='toself', fillcolor='rgba(0, 176, 246, 0.4)', line=dict(color='rgba(0, 176, 246, 1)'), name='Avanço Atual'))
                fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, df_melhoria['Avanço Máximo (min)'].max() * 1.1])),
                                  showlegend=True, paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(l=40, r=40, t=80, b=40))
                st.plotly_chart(fig, use_container_width=True)

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
    data, etapas_scores, periodos_df, etapas_pesos_df = load_and_prepare_data(all_sheets)
    st.session_state.data_original = data
    st.session_state.etapas_scores_cols = etapas_scores
    st.session_state.periodos_df = periodos_df
    st.session_state.etapas_pesos_df = etapas_pesos_df

# ----------------------------------------------------------------------
# Sidebar (filtros e navegação)
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
        # Default para o último ciclo da lista
        ciclo_selecionado = st.selectbox("Selecione o Ciclo", sorted(ciclos_unicos, key=lambda m: datetime.strptime(m, "%B").month if m in ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'] else 0), index=len(ciclos_unicos)-1)
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
render_header_and_periodo("Circuito MiniPreço", periodo_inicio, periodo_fim, st.session_state.get('duracao_horas', 0))

if st.session_state.page == "Geral":
    render_geral_page()
elif st.session_state.page == "Loja":
    render_loja_page()
