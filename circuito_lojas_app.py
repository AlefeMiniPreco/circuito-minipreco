# -*- coding: utf-8 -*-
# circuito_lojas_app.py — versão com melhorias de gamificação (Minutos_Ganhos, normalização, badges, milestones)
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
# (o restante do seu código original permanece - carregamento de dados, funções utilitárias, etc.)
# ----------------------------------------------------------------------
# OBS: mantive quase todas as funções originais intactas; adicionei/alterei as funções de cálculo e renderização
# para refletir as mudanças pedidas: Minutos_Ganhos, normalização, badges, milestones, labels atualizados.
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Novas/Alteradas: cálculo de pontuação final (Minutos_Ganhos), normalização, badges, milestones
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def calculate_final_scores(df: pd.DataFrame, etapas: list, max_minutos_total: float, normalize_by: str = None, milestones_pct=[25,50,75,100]):
    """
    Calcula pontuação final transformando pontos em 'Minutos_Ganhos' (mais intuitivo),
    adiciona normalização (por porte/fluxo), percentil, z-score, badges e milestones.
    Mantém colunas antigas 'Pontos_Totais' e 'Progresso' para compatibilidade com código legado.
    Params:
    - df: dataframe com colunas de score por etapa
    - etapas: lista de colunas *_Score (ou nome das etapas)
    - max_minutos_total: meta do circuito (p. ex. soma dos pesos)
    - normalize_by: coluna (str) para normalizar por porte/fluxo da loja (opcional)
    - milestones_pct: lista de percentuais que definem checkpoints
    """
    df = df.copy()
    for e in etapas:
        if e not in df.columns:
            df[e] = 0.0

    # Minutos ganhos = soma das etapas (métrica principal, mais intuitiva)
    df["Minutos_Ganhos"] = df[etapas].sum(axis=1)

    # Normalização por porte/fluxo (opcional) para fairness
    if normalize_by and normalize_by in df.columns:
        # evitar divisão por zero
        df["_norm_base"] = df[normalize_by].replace({0: np.nan})
        # opções de normalização: simples, sqrt, log - aqui usamos log(1+x)
        df["Minutos_Normalizados"] = df["Minutos_Ganhos"] / np.log1p(df["_norm_base"])
        df["Minutos_Normalizados"] = df["Minutos_Normalizados"].fillna(df["Minutos_Ganhos"])
        score_col_for_rank = "Minutos_Normalizados"
    else:
        df["Minutos_Normalizados"] = df["Minutos_Ganhos"]
        score_col_for_rank = "Minutos_Ganhos"

    # Meta e progresso (%)
    max_p = max_minutos_total if max_minutos_total and max_minutos_total > 0 else (df[score_col_for_rank].max() if not df.empty else 1)
    df["ProgressoPct"] = (df[score_col_for_rank] / max_p) * 100.0
    df["Minutos_Faltantes"] = (max_p - df[score_col_for_rank]).clip(lower=0.0)

    # Rank por score_col_for_rank (descendente)
    df["Rank"] = df[score_col_for_rank].rank(method="dense", ascending=False).astype(int)

    # Percentil e z-score (para análises e identificação de outliers)
    df["Percentil"] = df[score_col_for_rank].rank(pct=True) * 100.0
    # zscore manual (population)
    mean_val = df[score_col_for_rank].mean() if not df.empty else 0.0
    std_val = df[score_col_for_rank].std(ddof=0) if not df.empty else 0.0
    df["Zscore"] = ((df[score_col_for_rank] - mean_val) / (std_val if std_val != 0 else 1)).round(3)

    # Milestones (retorna maior checkpoint atingido e lista booleana de checkpoints)
    ms = sorted(set([int(m) for m in milestones_pct]))
    for m in ms:
        col = f"Reached_{m}pct"
        df[col] = df["ProgressoPct"] >= m
    # maior milestone atingida (rótulo)
    def _highest_milestone(r):
        achieved = [m for m in ms if r["ProgressoPct"] >= m]
        return f"{max(achieved)}%" if achieved else "Nenhum"
    df["Milestone_Atingida"] = df.apply(_highest_milestone, axis=1)

    # Badges/tiers simples (configuráveis)
    def assign_badge(pct):
        if pct >= 90: return "Ouro"
        if pct >= 60: return "Prata"
        if pct >= 30: return "Bronze"
        return "Participação"
    df["Badge"] = df["ProgressoPct"].round(1).apply(assign_badge)

    # compatibilidade com código antigo: expor colunas antigas
    df["Pontos_Totais"] = df["Minutos_Ganhos"]
    df["Progresso"] = df["ProgressoPct"]

    # ordenação e reset index
    df.sort_values([score_col_for_rank, "Nome_Exibicao"], ascending=[False, True], inplace=True)
    df = df.reset_index(drop=True)
    return df

# ----------------------------------------------------------------------
# Gamificação — configurações rápidas (sidebar)
# ----------------------------------------------------------------------
# preserva opções na session_state
if 'gamification_normalize_by' not in st.session_state:
    st.session_state.gamification_normalize_by = None
if 'gamification_milestones' not in st.session_state:
    st.session_state.gamification_milestones = [25,50,75,100]
if 'gamification_show_badges' not in st.session_state:
    st.session_state.gamification_show_badges = True
if 'gamification_show_percentil' not in st.session_state:
    st.session_state.gamification_show_percentil = False

with st.sidebar:
    st.markdown('### Gamificação — configurações')
    # detect numeric columns for normalization if data loaded
    data_orig = st.session_state.get('data_original', pd.DataFrame())
    numeric_cols = []
    if not data_orig.empty:
        numeric_cols = data_orig.select_dtypes(include=[np.number]).columns.tolist()
    norm_choice = st.selectbox("Normalizar por (porte/fluxo) — opcional", options=['Nenhum'] + numeric_cols, index=0)
    st.session_state.gamification_normalize_by = None if norm_choice == 'Nenhum' else norm_choice

    milestones_choice = st.multiselect("Milestones (%) — checkpoints", options=[10,25,30,50,60,75,90,100], default=st.session_state.gamification_milestones)
    st.session_state.gamification_milestones = sorted(list(set([int(x) for x in milestones_choice]))) if milestones_choice else [25,50,75,100]

    st.session_state.gamification_show_badges = st.checkbox("Mostrar badges/tiers", value=st.session_state.gamification_show_badges)
    st.session_state.gamification_show_percentil = st.checkbox("Mostrar percentil e z-score (debug)", value=st.session_state.gamification_show_percentil)

# ----------------------------------------------------------------------
# (Funções de suporte visual atualizadas)
# ----------------------------------------------------------------------
def build_pista_fig(data: pd.DataFrame, max_minutos: float = None) -> go.Figure:
    """
    Gera figura da pista usando 'Minutos_Ganhos' como métrica principal.
    Hover inclui Minutos_Ganhos, Minutos_Faltantes, ProgressoPct, Badge e Milestone.
    """
    if data is None or data.empty:
        return go.Figure()

    CAR_ICON_URL = "https://raw.githubusercontent.com/AlefeMiniPreco/circuito-minipreco/main/assets/carro-corrida_anim.webp"

    fig = go.Figure()
    num_lojas = len(data)
    y_positions = np.arange(num_lojas)

    # escolher coluna principal preferencialmente Minutos_Ganhos (compatível com versões antigas)
    value_col = "Minutos_Ganhos" if "Minutos_Ganhos" in data.columns else ("Pontos_Totais" if "Pontos_Totais" in data.columns else data.columns[0])

    if max_minutos is None or max_minutos == 0:
        max_minutos = data[value_col].max() if not data.empty else 100

    def escala_visual(x):
        return np.sqrt(max(x, 0))

    max_vis = escala_visual(max_minutos)

    for idx, y in enumerate(y_positions):
        row = data.iloc[idx]
        val = float(row.get(value_col, 0))
        vis_val = escala_visual(val)
        y0 = y - 0.35
        y1 = y + 0.35

        # barra de pista (fundo)
        fig.add_shape(type="rect", x0=0, y0=y0, x1=max_vis, y1=y1,
                      line=dict(width=0), fillcolor="#2C3E50", layer="below")

        # barra de progresso (visível)
        fig.add_shape(type="rect", x0=0, y0=y0, x1=vis_val, y1=y1,
                      line=dict(width=0), fillcolor="#10B981", layer="above")

        # marcador (carro) na posição proporcional
        car_x = min(vis_val, max_vis)
        fig.add_trace(go.Scatter(
            x=[car_x], y=[y], mode="markers", marker_symbol="car", marker_size=28,
            hoverinfo="text",
            hovertext=(
                f"<b>{row.get('Nome_Exibicao','-')}</b><br>"
                f"Minutos ganhos: {val:.1f} min<br>"
                f"Progresso: {row.get('ProgressoPct', row.get('Progresso',0)):.1f}%<br>"
                f"Faltam: {row.get('Minutos_Faltantes', max(0, max_minutos - val)):.1f} min<br>"
                + (f"Badge: {row.get('Badge')}<br>" if row.get('Badge') else "")
                + (f"Milestone: {row.get('Milestone_Atingida')}" if row.get('Milestone_Atingida') else "")
            ),
            showlegend=False
        ))

    # eixo e layout
    fig.update_yaxes(visible=False)
    fig.update_xaxes(title_text="Minutos ganhos (escala visual)", range=[0, max_vis*1.05])
    fig.update_layout(height=80 + 60 * num_lojas, margin=dict(l=40, r=40, t=30, b=40), template="plotly_dark")
    return fig

# ----------------------------------------------------------------------
# Render do pódio (atualizado para mostrar Badge e Milestone)
# ----------------------------------------------------------------------
def render_podio_table(df_final: pd.DataFrame):
    if df_final is None or df_final.empty:
        st.info("Sem dados para exibir no pódio.")
        return

    # use progresso compatível ou ProgressoPct se existir
    progresso_col = "Progresso" if "Progresso" in df_final.columns else "ProgressoPct"

    winners = df_final[df_final[progresso_col] >= 100.0].sort_values("Rank").reset_index(drop=True)

    # Helper to format extra badges/milestones
    def extras_text(row):
        parts = []
        if "Badge" in row and st.session_state.get('gamification_show_badges', True):
            parts.append(f"Badge: <b>{row['Badge']}</b>")
        if "Milestone_Atingida" in row:
            parts.append(f"Milestone: <b>{row['Milestone_Atingida']}</b>")
        if st.session_state.get('gamification_show_percentil', False):
            if "Percentil" in row:
                parts.append(f"Percentil: {row['Percentil']:.1f}º")
            if "Zscore" in row:
                parts.append(f"Z-score: {row['Zscore']:.2f}")
        return " • ".join(parts)

    if not winners.empty:
        st.markdown("### Parabéns ao(s) vencedor(es) que alcançaram 100% da meta")
        cols = st.columns(len(winners.head(3)))
        for i in range(min(3, len(winners))):
            row = winners.loc[i]
            nome = row["Nome_Exibicao"]
            pontos = row.get("Pontos_Totais", row.get("Minutos_Ganhos", 0))
            progresso = row.get(progresso_col, 0)
            rank = row.get("Rank", i+1)
            with cols[i]:
                st.markdown(
                    f"""<div style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0f172a,#111827);color:white; text-align:center;'>
                        <h3 style='margin:0'>{i+1}º — {nome}</h3>
                        <p style='margin:6px 0 0 0; opacity:0.95'>Rank: #{rank} • {pontos:.1f} min</p>
                        <p style='margin:6px 0 0 0; opacity:0.85'>Progresso: {progresso:.1f}%</p>
                        <p style='margin:6px 0 0 0; opacity:0.85'>{extras_text(row)}</p>
                    </div>""", unsafe_allow_html=True)
        return

    # se ninguém alcançou 100%, mostrar top3 do ranking atual
    st.markdown("Nenhuma loja cruzou a linha de chegada. Top 3 do ranking atual:")
    top3 = df_final.head(3).reset_index(drop=True)
    cols = st.columns(3)
    for i in range(3):
        if i < len(top3):
            row = top3.loc[i]
            nome = row["Nome_Exibicao"]
            pontos = row.get("Pontos_Totais", row.get("Minutos_Ganhos", 0))
            progresso = row.get(progresso_col, 0)
            rank = row.get("Rank", i+1)
            extras = extras_text(row)
            with cols[i]:
                st.markdown(
                    f"""<div style='padding:18px; border-radius:12px; background:linear-gradient(180deg,#0b1220,#111827);color:white; text-align:center;'>
                        <h3 style='margin:0'>{i+1}º — {nome}</h3>
                        <p style='margin:6px 0 0 0; opacity:0.95'>Rank: #{rank} • {pontos:.1f} min</p>
                        <p style='margin:6px 0 0 0; opacity:0.85'>Progresso: {progresso:.1f}%</p>
                        <p style='margin:6px 0 0 0; opacity:0.85'>{extras}</p>
                    </div>""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Ajuste nas renderizações principais (Visão Geral) para exibir novas colunas
# ----------------------------------------------------------------------
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
        # mostrar líder atual
        st.metric("Líder Atual", f"{df_final['Nome_Exibicao'].iloc[0]}")

    render_podio_table(df_final)

    st.markdown("### Pista de Corrida do Circuito")
    max_minutos = st.session_state.get('max_minutos_circuito', 0.0)
    fig_pista = build_pista_fig(df_final, max_minutos=max_minutos)
    st.plotly_chart(fig_pista, use_container_width=True)

    st.markdown("### Classificação Completa")
    df_classificacao = df_final.copy()

    # usar Minutos_Ganhos como principal (compatibilidade com Pontos_Totais)
    main_col = "Minutos_Ganhos" if "Minutos_Ganhos" in df_classificacao.columns else "Pontos_Totais"
    df_classificacao['Faltam (min)'] = (max_minutos - df_classificacao[main_col]).clip(lower=0)

    etapa_columns = [col for col in df_classificacao.columns if col.endswith('_Score')]

    rename_dict = {col: f"{col.replace('_Score', '')} (min)" for col in etapa_columns}
    df_classificacao.rename(columns=rename_dict, inplace=True)

    # montar colunas finais, incluindo badges/milestones opcionalmente
    final_columns = ['Rank', 'Nome_Exibicao'] + list(rename_dict.values()) + [main_col, 'ProgressoPct' if 'ProgressoPct' in df_classificacao.columns else 'Progresso', 'Faltam (min)']
    if 'Badge' in df_classificacao.columns and st.session_state.get('gamification_show_badges', True):
        final_columns.append('Badge')
    if 'Milestone_Atingida' in df_classificacao.columns:
        final_columns.append('Milestone_Atingida')
    if st.session_state.get('gamification_show_percentil', False):
        if 'Percentil' in df_classificacao.columns:
            final_columns.append('Percentil')
        if 'Zscore' in df_classificacao.columns:
            final_columns.append('Zscore')

    df_display = df_classificacao[final_columns].copy()

    for col in list(rename_dict.values()):
        df_display[col] = df_display[col].apply(lambda x: f"{x:.1f} min" if pd.notna(x) else "Ainda sem nota imputada")

    # format main columns
    df_display[main_col] = df_display[main_col].apply(lambda x: f"{x:.1f} min")
    prog_col = 'ProgressoPct' if 'ProgressoPct' in df_display.columns else 'Progresso'
    df_display[prog_col] = df_display[prog_col].apply(lambda x: f"{x:.1f}%")
    df_display['Faltam (min)'] = df_display['Faltam (min)'].apply(lambda x: f"{x:.1f} min")

    st.dataframe(df_display, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# Integração com pipeline existente
# ----------------------------------------------------------------------
# Substituí as chamadas principais para passar as configurações do sidebar
def filter_and_score_multi(data_original: pd.DataFrame, etapas: list, periodos_pesos_df: pd.DataFrame, ciclo: str | None, periodos: list | None):
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

    aggregated = df.groupby(['Loja','Nome_Exibicao'], as_index=False)[score_cols].sum(min_count=1)

    aggregated['Ciclo'] = ciclo
    final = calculate_final_scores(aggregated, score_cols, max_minutos, normalize_by=st.session_state.get('gamification_normalize_by', None), milestones_pct=st.session_state.get('gamification_milestones', [25,50,75,100]))
    return final

# ----------------------------------------------------------------------
# NOTE: O restante do seu arquivo original (upload, warming cache, outras pages) permanece.
# As funções principais foram adaptadas para manter compatibilidade e adicionar features.
# ----------------------------------------------------------------------

# (As funções e rotinas abaixo — carregamento de dados, warm_cache_all_periods, executors, etc. — 
#  permanecem do seu arquivo original e não foram explicitamente repetidas aqui para evitar duplicidade.
#  A versão salva em /mnt/data contém o arquivo completo e pronto.)
