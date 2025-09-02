# -*- coding: utf-8 -*-
# circuito_lojas_app.py
# Versão ajustada: notas -> minutos; circuito total = soma dos pesos dos períodos selecionados
import os
from io import BytesIO
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import time

# reportlab para PDFs
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.units import mm

st.set_page_config(page_title="Circuito MiniPreço", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

DATA_FILE_PATH = "BaseCircuito.xlsx"
ETAPA_SHEETS = [
    "PlanoVoo", "ProjetoFast", "PontoPartida", "AcoesComerciais", "PainelVendas",
    "Engajamento", "VisualMerchandising", "ModeloAtendimento", "EvolucaoComercial",
    "Qualidade", "Meta"
]
PREMIO_TOP1 = "Bônus Ouro + Folga"
PREMIO_TOP3 = "Bônus Prata"
PREMIO_TOP5 = "Bônus Bronze"
PREMIO_DEMAIS = "Reconhecimento + Plano de Ação"

# CSS (mantive estilo de pista/pódio)
# CSS (mantive estilo de pista/pódio)
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

# ---------- Utils: PDF & image helpers ----------
def fig_to_png_bytes(fig: go.Figure) -> BytesIO:
    try:
        img_bytes = fig.to_image(format="png")
        return BytesIO(img_bytes)
    except Exception as exc:
        st.error(
            "Falha ao gerar imagem do gráfico para o PDF. "
            "Verifique se 'kaleido' e 'plotly' estão instalados corretamente.\n\n"
            "Tente executar: pip install -U kaleido plotly"
        )
        raise

def _build_doc_buffer(elements) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------- Render do pódio (mantive) ----------
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

# ---------- Data loading & preparation (NOTA -> minutos) ----------
@st.cache_data(show_spinner=False)
def _read_excel_safe(path: str, sheet: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return pd.read_excel(path, sheet_name=sheet)

@st.cache_data(show_spinner=False)
def load_and_prepare_data(data_path: str, sheets: list):
    """
    Carrega todas as sheets, transforma Nota -> minutos (Score_Etapa = Nota),
    e constrói:
      - combined_df: linha per loja/ciclo/periodo com colunas <Sheet>_Score (minutos)
      - etapas_scores: lista de colunas <Sheet>_Score
      - etapas_info_total: soma dos pesos por sheet em todo o arquivo (útil como referência)
      - periodos_df: df com Ciclo/Periodo listados
      - periodos_formatados: lista string "Ciclo - Periodo"
      - periodos_pesos_df: df com soma de PesoDaEtapa por Ciclo/Periodo (somando todas as etapas)
      - etapas_pesos_df: df com soma de PesoDaEtapa por Etapa/Ciclo/Periodo (para cálculo por etapa)
    """
    all_data = []
    etapas_info_total = {}
    periodos_pesos_records = []
    etapas_pesos_records = []

    for sheet_name in sheets:
        try:
            df_etapa = _read_excel_safe(data_path, sheet_name)
            df_etapa.columns = [c.strip() for c in df_etapa.columns]
            required_cols = ['NomeLoja', 'loja_key', 'Nota', 'NotaMaxima', 'PesoDaEtapa', 'Ciclo', 'Período']
            # aceitar se colunas essenciais existirem (Пode haver sheets sem todas)
            if not all(col in df_etapa.columns for col in ['NomeLoja','loja_key','Nota','Ciclo','Período']):
                continue

            # padroniza nomes
            df_etapa = df_etapa.rename(columns={'loja_key': 'Loja', 'NomeLoja': 'Nome_Exibicao', 'Período': 'Periodo'})

            # Agora: Nota = minutos ganhos (não dividir por NotaMaxima)
            # Se Nota for nulo, tratar como 0
            df_etapa['Score_Etapa'] = pd.to_numeric(df_etapa['Nota'], errors='coerce').fillna(0.0)

            # Coluna consolidada
            df_consolidado = df_etapa[['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo', 'Score_Etapa']].copy()
            df_consolidado.rename(columns={'Score_Etapa': f'{sheet_name}_Score'}, inplace=True)
            all_data.append(df_consolidado)

            # Etapas info total (soma de PesoDaEtapa por sheet em todo o arquivo) - referência
            if 'PesoDaEtapa' in df_etapa.columns:
                total_peso_sheet = pd.to_numeric(df_etapa['PesoDaEtapa'], errors='coerce').fillna(0.0).sum()
                etapas_info_total[f'{sheet_name}_Score'] = float(total_peso_sheet)

                # registrar pesos por Ciclo/Periodo para esta etapa
                pesos_gp = df_etapa.groupby(['Ciclo','Periodo'])['PesoDaEtapa'].sum().reset_index()
                pesos_gp['Etapa'] = f'{sheet_name}_Score'
                for _, r in pesos_gp.iterrows():
                    etapas_pesos_records.append({'Etapa': r['Etapa'], 'Ciclo': r['Ciclo'], 'Periodo': r['Periodo'], 'PesoDaEtapa': float(r['PesoDaEtapa'])})

                # registrar para soma total por periodo (somando todas as etapas)
                for _, r in df_etapa.groupby(['Ciclo','Periodo'])['PesoDaEtapa'].sum().reset_index().iterrows():
                    periodos_pesos_records.append({'Ciclo': r['Ciclo'], 'Periodo': r['Periodo'], 'PesoDaEtapa': float(r['PesoDaEtapa'])})
        except Exception:
            # se uma sheet falhar, ignora e segue
            continue

    if not all_data:
        return pd.DataFrame(), [], {}, pd.DataFrame(), [], pd.DataFrame(), pd.DataFrame()

    # merge lateral por loja/ciclo/periodo
    combined_df = all_data[0]
    for i in range(1, len(all_data)):
        combined_df = pd.merge(combined_df, all_data[i], on=['Loja', 'Nome_Exibicao', 'Ciclo', 'Periodo'], how='outer')

    # ordenação amigável de meses (se aplicável)
    month_order = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    combined_df['Ciclo_Cat'] = pd.Categorical(combined_df['Ciclo'], categories=month_order, ordered=True)
    combined_df = combined_df.sort_values(['Ciclo_Cat','Periodo','Nome_Exibicao']).reset_index(drop=True)

    etapas_scores = [c for c in combined_df.columns if c.endswith('_Score')]
    if etapas_scores:
        combined_df[etapas_scores] = combined_df[etapas_scores].fillna(0.0)

    # periodos_df único
    periodos_df = combined_df[["Ciclo","Periodo","Ciclo_Cat"]].drop_duplicates().sort_values(["Ciclo_Cat","Periodo"]).reset_index(drop=True)
    periodos_formatados = [f"{row['Ciclo']} - {row['Periodo']}" for _, row in periodos_df.iterrows()]

    # criar dataframes de pesos por periodo e por etapa
    if periodos_pesos_records:
        periodos_pesos_df = pd.DataFrame(periodos_pesos_records).groupby(['Ciclo','Periodo'], as_index=False)['PesoDaEtapa'].sum()
    else:
        periodos_pesos_df = pd.DataFrame(columns=['Ciclo','Periodo','PesoDaEtapa'])

    if etapas_pesos_records:
        etapas_pesos_df = pd.DataFrame(etapas_pesos_records).groupby(['Etapa','Ciclo','Periodo'], as_index=False)['PesoDaEtapa'].sum()
    else:
        etapas_pesos_df = pd.DataFrame(columns=['Etapa','Ciclo','Periodo','PesoDaEtapa'])

    return combined_df, etapas_scores, etapas_info_total, periodos_df, periodos_formatados, periodos_pesos_df, etapas_pesos_df

# ---------- Cálculo de pontuação final (minutos) ----------
@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas: list, max_minutos_total: float):
    """
    df: agregado por Loja/Name com colunas <etapa>_Score contendo minutos acumulados
    max_minutos_total: valor do circuito (soma de pesos dos períodos selecionados)
    """
    df = df.copy()
    for e in etapas:
        if e not in df.columns:
            df[e] = 0.0
    df["Pontos_Totais"] = df[etapas].sum(axis=1)  # minutos acumulados
    max_p = max_minutos_total if max_minutos_total and max_minutos_total > 0 else (df["Pontos_Totais"].max() if not df.empty else 0)
    df["Progresso"] = (df["Pontos_Totais"] / max_p) * 100.0 if max_p > 0 else 0.0
    df["Rank"] = df["Pontos_Totais"].rank(method="dense", ascending=False).astype(int)
    df.sort_values(["Pontos_Totais","Nome_Exibicao"], ascending=[False,True], inplace=True)
    df = df.reset_index(drop=True)
    return df

# ---------- Helpers para somar pesos do circuito e pesos por etapa ----------
def get_circuit_total(periodos_pesos_df: pd.DataFrame, ciclo: str, selected_periodos: list | None):
    """
    Retorna a soma dos PesoDaEtapa para o (ciclo, periodos selecionados).
    If selected_periodos contains "Todos" or is None -> soma todos os períodos do ciclo.
    """
    if periodos_pesos_df is None or periodos_pesos_df.empty or ciclo is None:
        return 0.0
    df = periodos_pesos_df[periodos_pesos_df["Ciclo"] == ciclo].copy()
    if df.empty:
        return 0.0
    if not selected_periodos or "Todos" in selected_periodos:
        return float(df["PesoDaEtapa"].sum())
    df = df[df["Periodo"].isin(selected_periodos)]
    return float(df["PesoDaEtapa"].sum())

def get_etapa_pesos_for_selection(etapas_pesos_df: pd.DataFrame, ciclo: str, selected_periodos: list | None):
    """
    Retorna dict {etapa_col: peso_total_na_selecao} útil para calcular % por etapa
    """
    if etapas_pesos_df is None or etapas_pesos_df.empty or ciclo is None:
        return {}
    df = etapas_pesos_df[etapas_pesos_df["Ciclo"] == ciclo].copy()
    if df.empty:
        return {}
    if not selected_periodos or "Todos" in selected_periodos:
        gp = df.groupby("Etapa", as_index=False)["PesoDaEtapa"].sum()
    else:
        gp = df[df["Periodo"].isin(selected_periodos)].groupby("Etapa", as_index=False)["PesoDaEtapa"].sum()
    return {row["Etapa"]: float(row["PesoDaEtapa"]) for _, row in gp.iterrows()}

# ---------- Filtragem e agregação ----------
@st.cache_data(show_spinner=False)
def filter_and_score_multi(data_original: pd.DataFrame, etapas: list, periodos_pesos_df: pd.DataFrame, etapas_pesos_df: pd.DataFrame, ciclo: str | None, periodos: list | None):
    if ciclo is None or periodos is None:
        return pd.DataFrame()
    df = data_original[data_original["Ciclo"] == ciclo].copy()
    if df.empty:
        return pd.DataFrame()
    if "Todos" not in periodos:
        df = df[df["Periodo"].isin(periodos)]
    if df.empty:
        return pd.DataFrame()
    score_cols = [c for c in df.columns if c.endswith('_Score')]
    if not score_cols:
        return pd.DataFrame()

    # calcular total de minutos do circuito para essa seleção
    max_minutos = get_circuit_total(periodos_pesos_df, ciclo, periodos)
    # agregação por loja
    aggregated = df.groupby(['Loja','Nome_Exibicao'], as_index=False)[score_cols].sum()
    aggregated['Ciclo'] = ciclo

    final = calculate_final_scores(aggregated, score_cols, max_minutos)
    return final

@st.cache_data(show_spinner=False)
def warm_cache_all_periods(data_original: pd.DataFrame, etapas: list, periodos_pesos_df: pd.DataFrame, periodos_df: pd.DataFrame):
    """
    Pré-calcula filter_and_score_multi para todos os períodos (aquecimento).
    """
    if periodos_df.empty:
        _ = calculate_final_scores(data_original, etapas, 0.0)
        return 1
    count = 0
    for _, row in periodos_df.iterrows():
        _ = filter_and_score_multi(data_original, etapas, periodos_pesos_df, None, row["Ciclo"], [row["Periodo"]])  # etapas_pesos_df não necessário aqui
        count += 1
    return count

# ---------- Visual: pista (agora com escala em minutos) ----------
# ---------- Visual: pista (agora com escala em minutos) ----------
def build_pista_fig(data: pd.DataFrame, max_minutos: float = None) -> go.Figure:
    if data is None or data.empty:
        return go.Figure()
    fig = go.Figure()
    num_lojas = len(data)
    y_positions = np.arange(num_lojas)
    
    if max_minutos is None:
        max_minutos = data["Pontos_Totais"].max()

    # função de compressão para exibição
    def escala_visual(x):
        return np.sqrt(x)

    max_vis = escala_visual(max_minutos)

    # fundo da pista (reta total)
    for y in y_positions:
        fig.add_shape(type="rect", x0=0, y0=y-0.45, x1=max_vis, y1=y+0.45,
                      line=dict(width=0), fillcolor="#2C3E50", layer="below")

    # Linha de chegada (bandeira quadriculada)
    fig.add_shape(type="line", x0=max_vis, y0=-1, x1=max_vis, y1=num_lojas,
                  line=dict(color="black", width=4, dash="solid"))
    
    # Adicionar bandeira quadriculada no final da pista
    for y in range(num_lojas + 2):
        if y % 2 == 0:
            fig.add_shape(type="rect", x0=max_vis-0.5, y0=y-1, x1=max_vis+0.5, y1=y,
                          line=dict(width=0), fillcolor="black", layer="below")
        else:
            fig.add_shape(type="rect", x0=max_vis-0.5, y0=y-1, x1=max_vis+0.5, y1=y,
                          line=dict(width=0), fillcolor="white", layer="below")

    # carros 🚗 e bandeira 🏁
    for y, row in zip(y_positions, data.itertuples()):
        x_carro = escala_visual(row.Pontos_Totais)
        x_fim = escala_visual(max_minutos)
        
        # Determinar se cruzou a linha de chegada
        cruzou_linha = row.Pontos_Totais >= max_minutos
        
        # Escolher emoji e tamanho com base se cruzou a linha
        car_text = "🏁🚗" if cruzou_linha else "🚗"
        text_size = 35 if cruzou_linha else 30  # Maior para os que completaram
        text_color = "gold" if cruzou_linha else None  # Cor dourada para os que completaram
        
        hover = f"<b>{row.Nome_Exibicao}</b><br>Minutos: {row.Pontos_Totais:.1f}<br>Progresso: {row.Progresso:.1f}%<br>Rank: #{int(row.Rank)}"

        # carro
        fig.add_trace(go.Scatter(
            x=[x_carro], y=[y], mode="text", text=[car_text],
            textfont=dict(size=text_size, color=text_color), 
            hoverinfo="text", hovertext=hover, showlegend=False
        ))
        # nome da loja
        fig.add_trace(go.Scatter(
            x=[x_carro], y=[y-0.5], mode="text", text=[row.Nome_Exibicao],
            textfont=dict(size=9, color="rgba(255,255,255,0.9)"), hoverinfo="skip", showlegend=False
        ))

    # ajustes dos eixos
    fig.update_yaxes(showgrid=False, zeroline=False, tickmode="array", tickvals=y_positions, ticktext=[])
    fig.update_xaxes(range=[0, max_vis * 1.05], title_text="Minutos percorridos (escala visual compactada) →")

    fig.update_layout(
        height=250 + 70*num_lojas, margin=dict(l=10, r=10, t=80, b=40),
        plot_bgcolor="#1A2A3A", paper_bgcolor="rgba(26,42,58,0.7)"
    )
    
    return fig
# ---------- Inicializações de sessão ----------
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

@st.cache_resource
def load_data_and_warm_cache():
    data, etapas_scores, etapas_info, periodos_df, periodos_formatados, periodos_pesos_df, etapas_pesos_df = load_and_prepare_data(DATA_FILE_PATH, ETAPA_SHEETS)
    st.session_state.data_original = data
    st.session_state.etapas_scores = etapas_scores
    st.session_state.etapas_info = etapas_info
    st.session_state.periodos_df = periodos_df
    st.session_state.periodos_formatados = periodos_formatados
    st.session_state.periodos_pesos_df = periodos_pesos_df
    st.session_state.etapas_pesos_df = etapas_pesos_df
    _ = warm_cache_all_periods(data, etapas_scores, periodos_pesos_df, periodos_df)
    return True

try:
    load_data_and_warm_cache()
except Exception:
    pass

# ---------- Sidebar ----------
with st.sidebar:
    st.image("https://cdn-retailhub.com/minipreco/096c9b29-4ac3-425f-8322-be76b794f040.webp", use_container_width=True)
    st.markdown("---")
    st.markdown("### Seleção de Ciclo e Período")
    periodos_df = st.session_state.get('periodos_df', pd.DataFrame())
    ciclos_unicos = periodos_df["Ciclo"].dropna().unique().tolist() if not periodos_df.empty else []
    if not ciclos_unicos:
        st.error("Nenhum ciclo disponível nos dados.")
    else:
        ciclo_selecionado = st.selectbox("Selecione o Ciclo", ciclos_unicos, index=len(ciclos_unicos)-1)
        periodos_ciclo = periodos_df.query("Ciclo == @ciclo_selecionado")["Periodo"].dropna().unique().tolist()
        periodos_opcoes = ["Todos"] + list(periodos_ciclo)
        periodos_selecionados = st.multiselect("Selecione os Períodos", options=periodos_opcoes, default=["Todos"])
        st.session_state.ciclo = ciclo_selecionado
        st.session_state.periodos = periodos_selecionados

    st.markdown("---")
    st.markdown("### Navegação")
    if st.button("Visão Geral", use_container_width=True): st.session_state.page = "Geral"
    if st.button("Visão por Loja", use_container_width=True): st.session_state.page = "Loja"
    if st.button("Visão por Etapa", use_container_width=True): st.session_state.page = "Etapa"

# ---------- Validação / cálculo ----------
if st.session_state.data_original is None or st.session_state.data_original.empty:
    st.warning("Dados ainda não carregados ou arquivo vazio. Verifique DATA_FILE_PATH.")
else:
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

# ---------- Header & render pages ----------
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
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

def get_period_range(ciclo: str, selected_periods: list, periodos_df: pd.DataFrame):
    if not ciclo or periodos_df is None or periodos_df.empty:
        return None, None
    ciclo_df = periodos_df[periodos_df["Ciclo"] == ciclo].reset_index(drop=True)
    if ciclo_df.empty:
        return None, None
    ordered_periods = ciclo_df["Periodo"].tolist()
    if not selected_periods or "Todos" in selected_periods:
        return ordered_periods[0], ordered_periods[-1]
    selected_in_order = [p for p in ordered_periods if p in selected_periods]
    if not selected_in_order:
        return None, None
    return selected_in_order[0], selected_in_order[-1]

# ---------- PDFs (mantive lógica, mas usa minutos) ----------
def gerar_pdf_pagina_geral(include_plots: bool = True) -> BytesIO:
    styles = getSampleStyleSheet()
    title = styles["Title"]; h2 = styles["Heading2"]; normal = styles["Normal"]
    elements = []

    elements.append(Paragraph("Circuito MiniPreço — Visão Geral", title))
    elements.append(Spacer(1, 6))
    ciclo = st.session_state.get("ciclo", "Não definido"); periodos = st.session_state.get("periodos", [])
    elements.append(Paragraph(f"Ciclo: <b>{ciclo}</b>", normal))
    elements.append(Paragraph(f"Períodos: <b>{', '.join(periodos) if periodos else 'Não definido'}</b>", normal))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ParagraphStyle("small", parent=normal, fontSize=8)))
    elements.append(Spacer(1, 8))

    df_final = st.session_state.get("df_final", pd.DataFrame())

    elements.append(Paragraph("Pódio — Lojas que cruzaram a linha de chegada", h2))
    if df_final is None or df_final.empty:
        elements.append(Paragraph("Nenhum dado disponível.", normal))
        return _build_doc_buffer(elements)

    podium = df_final[df_final["Progresso"] >= 100.0].sort_values("Rank")
    if podium.empty:
        elements.append(Paragraph("Nenhuma loja cruzou a linha de chegada.", normal))
    else:
        table_data = [["Rank", "Loja", "Minutos", "Progresso (%)", "Prêmio"]]
        for _, r in podium.iterrows():
            pos = int(r["Rank"])
            premio = PREMIO_TOP1 if pos == 1 else PREMIO_TOP3 if pos in (2,3) else PREMIO_TOP5 if pos in (4,5) else PREMIO_DEMAIS
            table_data.append([pos, r["Nome_Exibicao"], f"{r['Pontos_Totais']:.1f}", f"{r['Progresso']:.1f}", premio])
        t = Table(table_data, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.grey), ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke), ("GRID",(0,0),(-1,-1),0.25,colors.black)]))
        elements.append(t)
    elements.append(Spacer(1, 8))

    if include_plots:
        elements.append(Paragraph("Pista — Progresso das Lojas", h2))
        fig_pista = build_pista_fig(df_final, max_minutos=get_circuit_total(st.session_state.get('periodos_pesos_df', pd.DataFrame()), st.session_state.get('ciclo'), st.session_state.get('periodos')))
        img_bytes = fig_to_png_bytes(fig_pista)
        if img_bytes.getbuffer().nbytes:
            elements.append(RLImage(img_bytes, width=170*mm))
            elements.append(Spacer(1, 8))

    elements.append(Paragraph("Classificação Detalhada (Top 50 exibidas)", styles["Heading3"]))
    etapa_cols = [c for c in df_final.columns if c.endswith('_Score')]
    header = ["Rank", "Loja", "Minutos", "Progresso (%)"] + [c.replace("_Score","") for c in etapa_cols]
    rows = [header]
    for _, r in df_final.head(50).iterrows():
        row = [int(r["Rank"]), r["Nome_Exibicao"], f"{r['Pontos_Totais']:.1f}", f"{r['Progresso']:.1f}"]
        for c in etapa_cols:
            row.append(f"{r.get(c,0.0):.1f}")
        rows.append(row)
    t2 = Table(rows, hAlign="LEFT")
    t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightgrey), ("GRID",(0,0),(-1,-1),0.25,colors.black), ("FONTSIZE",(0,0),(-1,-1),8)]))
    elements.append(t2)

    return _build_doc_buffer(elements)

def gerar_pdf_pagina_loja(loja_name: str | None = None, include_plots: bool = True) -> BytesIO:
    styles = getSampleStyleSheet(); normal = styles["Normal"]; h2 = styles["Heading2"]
    elements = []
    elements.append(Paragraph("Circuito MiniPreço — Visão por Loja", styles["Title"]))
    elements.append(Spacer(1,6))
    ciclo = st.session_state.get("ciclo", "Não definido"); periodos = st.session_state.get("periodos", [])
    elements.append(Paragraph(f"Ciclo: <b>{ciclo}</b>", normal)); elements.append(Paragraph(f"Períodos: <b>{', '.join(periodos) if periodos else 'Não definido'}</b>", normal))
    elements.append(Spacer(1,8))

    df_final = st.session_state.get("df_final", pd.DataFrame())
    if loja_name is None:
        loja_name = st.session_state.get("loja_sb_ui", None)
    if df_final is None or df_final.empty or not loja_name:
        elements.append(Paragraph("Nenhum dado de loja disponível para exportar.", normal))
        return _build_doc_buffer(elements)

    loja_row = df_final[df_final["Nome_Exibicao"] == loja_name]
    if loja_row.empty:
        elements.append(Paragraph("Loja selecionada não possui dados no período.", normal))
        return _build_doc_buffer(elements)

    lr = loja_row.iloc[0]
    elements.append(Paragraph(f"Loja: <b>{loja_name}</b>", h2))
    elements.append(Paragraph(f"Rank: {int(lr['Rank'])} — Minutos: {lr['Pontos_Totais']:.1f} — Progresso: {lr['Progresso']:.1f}%", normal))
    elements.append(Spacer(1,6))

    cards = [["Posição no Rank", f"#{int(lr['Rank'])}"], ["Minutos Totais", f"{lr['Pontos_Totais']:.1f}"], ["Progresso", f"{lr['Progresso']:.1f}%"]]
    tcard = Table(cards, hAlign="LEFT")
    tcard.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.black), ("BACKGROUND",(0,0),(0,-1),colors.lightgrey), ("FONTSIZE",(0,0),(-1,-1),9)]))
    elements.append(tcard)
    elements.append(Spacer(1,8))

    etapas_keys = st.session_state.get("etapas_scores", []) or []
    # calcula pesos por etapa para seleção atual
    etapa_pesos_sel = get_etapa_pesos_for_selection(st.session_state.get('etapas_pesos_df', pd.DataFrame()), st.session_state.get('ciclo'), st.session_state.get('periodos'))

    if include_plots and etapas_keys:
        oportunidades = []
        for e in etapas_keys:
            peso = etapa_pesos_sel.get(e, 0)
            pont = float(lr.get(e, 0.0))
            percentual = (pont / peso) * 100 if peso > 0 else 0
            potencial = max(peso - pont, 0)
            oportunidades.append({"Etapa": e.replace("_Score",""), "Percentual": percentual, "Potencial": potencial})
        df_opp = pd.DataFrame(oportunidades).sort_values("Percentual").head(5)
        if not df_opp.empty:
            fig_opp = go.Figure(go.Bar(y=df_opp["Etapa"], x=df_opp["Percentual"], orientation="h"))
            img_opp = fig_to_png_bytes(fig_opp)
            if img_opp.getbuffer().nbytes:
                elements.append(RLImage(img_opp, width=150*mm))
                elements.append(Spacer(1,6))

    if include_plots and etapas_keys:
        r = [float(lr.get(e,0.0)) for e in etapas_keys]
        pesos = [etapa_pesos_sel.get(e,0) for e in etapas_keys]
        percentual = [(ri/pi*100) if (pi and pi>0) else 0 for ri,pi in zip(r,pesos)]
        theta = [e.replace("_Score","") for e in etapas_keys]
        fig_radar = go.Figure(go.Scatterpolar(r=percentual, theta=theta, fill="toself"))
        img_radar = fig_to_png_bytes(fig_radar)
        if img_radar.getbuffer().nbytes:
            elements.append(RLImage(img_radar, width=150*mm))
            elements.append(Spacer(1,6))

    tabel_et = [["Etapa", "Minutos", "Peso da Etapa (seleção)", "Desempenho (%)"]]
    for e in etapas_keys:
        nome = e.replace("_Score",""); pont = float(lr.get(e,0.0)); peso = float(get_etapa_pesos_for_selection(st.session_state.get('etapas_pesos_df', pd.DataFrame()), st.session_state.get('ciclo'), st.session_state.get('periodos')).get(e, 0)); perc = (pont / peso * 100) if (peso and peso > 0) else 0
        tabel_et.append([nome, f"{pont:.1f}", f"{peso:.1f}", f"{perc:.1f}"])
    t_et = Table(tabel_et, hAlign="LEFT")
    t_et.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.black), ("BACKGROUND",(0,0),(-1,0),colors.grey), ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke), ("FONTSIZE",(0,0),(-1,-1),8)]))
    elements.append(t_et)

    return _build_doc_buffer(elements)

def gerar_pdf_pagina_etapa(etapa_name: str | None = None, include_plots: bool = True) -> BytesIO:
    styles = getSampleStyleSheet(); normal = styles["Normal"]
    elements = []
    elements.append(Paragraph("Circuito MiniPreço — Visão por Etapa", styles["Title"]))
    elements.append(Spacer(1,6))
    ciclo = st.session_state.get("ciclo", "Não definido"); periodos = st.session_state.get("periodos", [])
    elements.append(Paragraph(f"Ciclo: <b>{ciclo}</b>", normal)); elements.append(Paragraph(f"Períodos: <b>{', '.join(periodos) if periodos else 'Não definido'}</b>", normal))
    elements.append(Spacer(1,8))

    etapas_keys = st.session_state.get('etapas_scores', []) or []
    if etapa_name is None:
        etapa_name = st.session_state.get("etapa_selected", None)
    if etapa_name is None and etapas_keys:
        etapa_name = etapas_keys[0].replace("_Score","")

    col_key = f"{etapa_name}_Score"
    df_final = st.session_state.get("df_final", pd.DataFrame())
    if df_final is None or df_final.empty or col_key not in df_final.columns:
        elements.append(Paragraph("Nenhum dado para a etapa selecionada.", normal))
        return _build_doc_buffer(elements)

    etapa_df = df_final[["Nome_Exibicao", col_key]].copy().rename(columns={col_key:"Minutos"}).sort_values("Minutos", ascending=False)
    elements.append(Paragraph(f"Etapa: {etapa_name} — Top 5", styles["Heading2"]))
    top5 = etapa_df.head(5)
    tab = [["Pos","Loja","Minutos"]]
    for i,row in top5.reset_index(drop=True).iterrows():
        tab.append([i+1, row["Nome_Exibicao"], f"{row['Minutos']:.1f}"])
    ttop = Table(tab, hAlign="LEFT"); ttop.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.black), ("BACKGROUND",(0,0),(-1,0),colors.grey), ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke)]))
    elements.append(ttop); elements.append(Spacer(1,8))

    if include_plots:
        fig_hist = px.histogram(etapa_df, x="Minutos", nbins=20)
        imgh = fig_to_png_bytes(fig_hist)
        if imgh.getbuffer().nbytes:
            elements.append(RLImage(imgh, width=160*mm))
            elements.append(Spacer(1,8))

    if not etapa_df["Minutos"].empty:
        mins = etapa_df["Minutos"].astype(float)
        elements.append(Paragraph(f"Média: {mins.mean():.2f} min — Mediana: {mins.median():.2f} min — Min: {mins.min():.2f} — Max: {mins.max():.2f}", normal))

    return _build_doc_buffer(elements)

# ---------- Renderização das páginas ----------
def render_visao_geral():
    periodo_inicio, periodo_fim = get_period_range(st.session_state.get('ciclo'), st.session_state.get('periodos', []), st.session_state.get('periodos_df', pd.DataFrame()))
    render_header_and_periodo("Circuito MiniPreço", periodo_inicio, periodo_fim)

    render_podio_table(st.session_state.get('df_final', pd.DataFrame()))
    # calcular max_minutos do circuito para seleção atual
    max_minutos = get_circuit_total(st.session_state.get('periodos_pesos_df', pd.DataFrame()), st.session_state.get('ciclo'), st.session_state.get('periodos'))
    fig = build_pista_fig(st.session_state.get('df_final', pd.DataFrame()), max_minutos=max_minutos)
    st.plotly_chart(fig, use_container_width=True, key="pista_chart_ui")

    st.markdown("---")
    st.markdown("### Classificação Detalhada")
    mostrar_etapas = st.checkbox("Mostrar minutos por etapa", value=True, key="cb_geral_etapas")
    df_rank = st.session_state.get('df_final', pd.DataFrame())[["Rank","Nome_Exibicao","Pontos_Totais","Progresso"]].copy() if not st.session_state.get('df_final', pd.DataFrame()).empty else pd.DataFrame()
    etapa_cols = [c for c in st.session_state.get('df_final', pd.DataFrame()).columns if c.endswith('_Score')]
    if mostrar_etapas and etapa_cols and not df_rank.empty:
        for c in etapa_cols:
            friendly = c.replace('_Score','')
            df_rank[friendly] = st.session_state.df_final[c].round(1)
    if not df_rank.empty:
        df_rank["Prêmio"] = df_rank["Rank"].apply(lambda p: PREMIO_TOP1 if p==1 else PREMIO_TOP3 if p in (2,3) else PREMIO_TOP5 if p in (4,5) else PREMIO_DEMAIS)
        df_rank.rename(columns={"Nome_Exibicao":"Loja","Pontos_Totais":"Minutos","Progresso":"Progresso (%)"}, inplace=True)
        st.dataframe(df_rank, use_container_width=True, hide_index=True)

    st.markdown("---")
    buf = gerar_pdf_pagina_geral(include_plots=True)
    st.download_button("📥 Baixar PDF — Visão Geral (página atual)", data=buf.getvalue(), file_name="Visao_Geral_Circuito.pdf", mime="application/pdf", key="dl_pdf_geral_direct")

def render_visao_loja():
    periodo_inicio, periodo_fim = get_period_range(st.session_state.get('ciclo'), st.session_state.get('periodos', []), st.session_state.get('periodos_df', pd.DataFrame()))
    render_header_and_periodo("Circuito MiniPreço — Visão por Loja", periodo_inicio, periodo_fim)
    st.markdown("### Visão Detalhada por Loja")
    df_final = st.session_state.get('df_final', pd.DataFrame())
    lojas = df_final["Nome_Exibicao"].unique().tolist() if not df_final.empty else []
    if not lojas:
        st.info("Sem lojas para exibir.")
        return

    loja_selecionada = st.selectbox("Selecione uma Loja", lojas, key="loja_sb_ui")
    loja_row = df_final[df_final["Nome_Exibicao"] == loja_selecionada]
    if loja_row.empty:
        st.info("Loja sem dados.")
        return
    loja_series = loja_row.iloc[0]

    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Posição no Rank</div><div class='metric-value'>#{int(loja_series['Rank'])}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Minutos Totais</div><div class='metric-value'>{loja_series['Pontos_Totais']:.1f} min</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Progresso</div><div class='metric-value'>{loja_series['Progresso']:.1f}%</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    if loja_series['Progresso'] < 100:
        etapas_keys = st.session_state.get('etapas_scores', []) or []
        etapa_pesos_sel = get_etapa_pesos_for_selection(st.session_state.get('etapas_pesos_df', pd.DataFrame()), st.session_state.get('ciclo'), st.session_state.get('periodos'))
        oportunidades = []
        for e in etapas_keys:
            peso = etapa_pesos_sel.get(e, 0)
            pont = float(loja_series.get(e, 0.0))
            percentual = (pont / peso) * 100 if peso>0 else 0
            oportunidades.append({'Etapa': e.replace("_Score",""), 'Percentual': percentual})
        df_opp = pd.DataFrame(oportunidades).sort_values("Percentual").head(5)
        fig_opp = go.Figure()
        if not df_opp.empty:
            fig_opp.add_trace(go.Bar(y=df_opp["Etapa"], x=df_opp["Percentual"], orientation="h"))
        st.plotly_chart(fig_opp, use_container_width=True, key="oportunidades_chart_ui")

    etapas_keys = st.session_state.get('etapas_scores', []) or []
    if etapas_keys:
        etapa_pesos_sel = get_etapa_pesos_for_selection(st.session_state.get('etapas_pesos_df', pd.DataFrame()), st.session_state.get('ciclo'), st.session_state.get('periodos'))
        r = [float(loja_series.get(e,0.0)) for e in etapas_keys]
        pesos = [etapa_pesos_sel.get(e,0) for e in etapas_keys]
        percentual = [(ri/pi*100) if (pi and pi>0) else 0 for ri,pi in zip(r,pesos)]
        theta = [e.replace("_Score","") for e in etapas_keys]
        fig_radar = go.Figure(go.Scatterpolar(r=percentual, theta=theta, fill="toself"))
        st.plotly_chart(fig_radar, use_container_width=True, key="radar_chart_ui")

    st.markdown("---")
    buf_loja = gerar_pdf_pagina_loja(loja_name=loja_selecionada, include_plots=True)
    st.download_button(f"📥 Baixar PDF — Visão por Loja ({loja_selecionada})", data=buf_loja.getvalue(), file_name=f"Visao_Loja_{loja_selecionada}.pdf", mime="application/pdf", key=f"dl_pdf_loja_{loja_selecionada}")

def render_visao_etapa():
    periodo_inicio, periodo_fim = get_period_range(st.session_state.get('ciclo'), st.session_state.get('periodos', []), st.session_state.get('periodos_df', pd.DataFrame()))
    render_header_and_periodo("Circuito MiniPreço — Visão por Etapa", periodo_inicio, periodo_fim)
    etapas_keys = st.session_state.get('etapas_scores', []) or []
    friendly_etapas = [e.replace("_Score","") for e in etapas_keys]
    if not friendly_etapas:
        st.info("Sem etapas detectadas nos dados.")
        return
    etapa_sel = st.selectbox("Selecione uma Etapa", friendly_etapas, key="etapa_sel_ui")
    st.session_state.etapa_selected = etapa_sel
    col_key = f"{etapa_sel}_Score"
    df_final = st.session_state.get('df_final', pd.DataFrame())
    if df_final.empty or col_key not in df_final.columns:
        st.info("Sem dados para a etapa selecionada.")
        return
    etapa_df = df_final[["Nome_Exibicao", col_key]].copy().rename(columns={col_key:"Minutos"}).sort_values("Minutos", ascending=False)
    top5 = etapa_df.head(5)
    st.dataframe(top5, use_container_width=True, hide_index=True)
    fig_hist = px.histogram(etapa_df, x="Minutos", nbins=20)
    st.plotly_chart(fig_hist, use_container_width=True, key="histograma_chart_ui")

    st.markdown("---")
    buf_etapa = gerar_pdf_pagina_etapa(etapa_name=etapa_sel, include_plots=True)
    st.download_button(f"📥 Baixar PDF — Visão por Etapa ({etapa_sel})", data=buf_etapa.getvalue(), file_name=f"Visao_Etapa_{etapa_sel}.pdf", mime="application/pdf", key=f"dl_pdf_etapa_{etapa_sel}")

# ---------- Render main ----------
if st.session_state.df_final is None or st.session_state.df_final.empty:
    periodo_inicio, periodo_fim = get_period_range(st.session_state.get('ciclo'), st.session_state.get('periodos', []), st.session_state.get('periodos_df', pd.DataFrame()))
    render_header_and_periodo("Circuito MiniPreço", periodo_inicio, periodo_fim)
    st.warning("Sem dados para exibir com a seleção atual. Verifique o ciclo/períodos selecionados ou o arquivo de origem.")
else:
    if st.session_state.page == "Geral":
        render_visao_geral()
    elif st.session_state.page == "Loja":
        render_visao_loja()
    elif st.session_state.page == "Etapa":
        render_visao_etapa()

st.caption("**Circuito MiniPreço** - Dashboard para acompanhamento entre lojas. Notas agora representam minutos percorridos na pista.")
