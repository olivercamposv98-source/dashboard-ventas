# =============================================================================
#  DASHBOARD DE VENTAS — BD_VENTAS_DIARIAS
#  Conexión: Google Sheets público vía CSV (sin paquetes externos)
#  Columnas: FECHA | SUCURSAL | VENTA PROYECTADA | VENTA REAL | DESVIACIÓN | % CUMPLIMIENTO
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
import calendar

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️  CONFIGURACIÓN — solo cambia estas 2 líneas si es necesario
# ─────────────────────────────────────────────────────────────────────────────
SHEET_ID    = "1kbG1uvxDx5qF6g-ucGgqsTHRqV9IfRHM5J2nj-kQyjA"
SHEET_NAME  = "BD_VENTAS_DIARIAS"   # nombre exacto de la pestaña

# URL pública de exportación CSV (funciona si el Sheet es "Cualquiera con el enlace")
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
)

# ─────────────────────────────────────────────────────────────────────────────
# PALETA CORPORATIVA
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "yellow":      "#F59E0B",
    "yellow_lt":   "#FDE68A",
    "yellow_pale": "rgba(245,158,11,0.12)",
    "slate_dark":  "#1F2937",
    "slate":       "#374151",
    "slate_lt":    "#6B7280",
    "green":       "#10B981",
    "green_pale":  "#D1FAE5",
    "red":         "#EF4444",
    "red_pale":    "#FEE2E2",
    "blue":        "#3B82F6",
    "purple":      "#8B5CF6",
    "orange":      "#F97316",
    "bg":          "#F8FAFC",
    "white":       "#FFFFFF",
    "border":      "#E5E7EB",
}

st.markdown(f"""
<style>
  .main .block-container {{ padding-top:.9rem; padding-bottom:2rem; }}

  .dash-header {{
    background:linear-gradient(135deg,{C['slate_dark']} 0%,{C['slate']} 100%);
    padding:1.3rem 2rem; border-radius:14px;
    border-left:7px solid {C['yellow']}; margin-bottom:1.3rem;
  }}
  .dash-header h1 {{ color:{C['yellow']}; font-size:1.7rem; font-weight:800; margin:0; }}
  .dash-header p  {{ color:#D1D5DB; margin:.2rem 0 0; font-size:.82rem; }}

  .kpi {{
    background:{C['white']}; padding:1rem 1.2rem;
    border-radius:12px; border:1px solid {C['border']};
    border-top:4px solid {C['yellow']};
    box-shadow:0 1px 4px rgba(0,0,0,.07);
    text-align:center; height:100%;
  }}
  .kpi-dark {{
    background:linear-gradient(135deg,{C['slate_dark']},{C['slate']});
    padding:1.3rem 1.5rem; border-radius:14px;
    border-left:6px solid {C['yellow']};
    box-shadow:0 4px 14px rgba(0,0,0,.18); text-align:center;
  }}
  .kpi-green {{
    background:linear-gradient(135deg,#064E3B,#065F46);
    padding:1rem 1.2rem; border-radius:12px;
    border-left:5px solid {C['green']};
    box-shadow:0 2px 8px rgba(0,0,0,.12); text-align:center;
  }}
  .kpi-red {{
    background:linear-gradient(135deg,#7F1D1D,#991B1B);
    padding:1rem 1.2rem; border-radius:12px;
    border-left:5px solid {C['red']};
    box-shadow:0 2px 8px rgba(0,0,0,.12); text-align:center;
  }}
  .kpi-title  {{ font-size:.68rem; font-weight:700; text-transform:uppercase;
                 letter-spacing:.06em; color:{C['slate_lt']}; margin-bottom:.35rem; }}
  .kpi-dark .kpi-title, .kpi-green .kpi-title, .kpi-red .kpi-title
                {{ color:rgba(255,255,255,.65); }}
  .kpi-value  {{ font-size:1.65rem; font-weight:800; color:{C['slate_dark']}; line-height:1.15; }}
  .kpi-dark .kpi-value  {{ color:{C['yellow']}; font-size:2rem; }}
  .kpi-green .kpi-value {{ color:{C['green']}; font-size:1.65rem; }}
  .kpi-red .kpi-value   {{ color:#FCA5A5; font-size:1.65rem; }}
  .badge {{ display:inline-block; font-size:.7rem; font-weight:600;
            padding:.16rem .55rem; border-radius:20px; margin-top:.3rem; }}
  .bp  {{ background:{C['green_pale']}; color:#065F46; }}
  .bn  {{ background:{C['red_pale']};   color:#991B1B; }}
  .bnu {{ background:#F3F4F6;           color:{C['slate']}; }}
  .bw  {{ background:#FEF3C7;           color:#92400E; }}

  .sec {{ font-size:.92rem; font-weight:700; color:{C['slate_dark']};
          border-bottom:2px solid {C['yellow']};
          padding-bottom:.3rem; margin:1.1rem 0 .65rem; }}

  .alert-r {{
    background:#FEF2F2 !important; border:1px solid #FECACA;
    border-left:4px solid {C['red']}; padding:.65rem 1rem;
    border-radius:8px; margin:.3rem 0; font-size:.83rem;
    color:#7F1D1D !important;
  }}
  .alert-r strong {{ color:#991B1B !important; }}
  .alert-w {{
    background:#FFFBEB !important; border:1px solid {C['yellow_lt']};
    border-left:4px solid {C['yellow']}; padding:.65rem 1rem;
    border-radius:8px; margin:.3rem 0; font-size:.83rem;
    color:#78350F !important;
  }}
  .alert-w strong {{ color:#92400E !important; }}
  .alert-g {{
    background:{C['green_pale']} !important; border:1px solid #6EE7B7;
    border-left:4px solid {C['green']}; padding:.65rem 1rem;
    border-radius:8px; margin:.3rem 0; font-size:.83rem;
    color:#064E3B !important;
  }}
  .alert-g strong {{ color:#065F46 !important; }}

  .stTabs [data-baseweb="tab-list"] {{
    gap:.4rem; background:{C['bg']}; padding:.32rem; border-radius:10px;
  }}
  .stTabs [data-baseweb="tab"] {{
    border-radius:8px; padding:.42rem .85rem; font-weight:600; font-size:.8rem;
  }}
  .stTabs [aria-selected="true"] {{
    background:{C['yellow']} !important; color:{C['slate_dark']} !important;
  }}

  .prog-wrap {{ background:#E5E7EB; border-radius:8px; height:10px; margin:.25rem 0; }}
  .prog-bar  {{ height:10px; border-radius:8px; }}

  .footer {{
    text-align:center; color:{C['slate_lt']}; font-size:.7rem;
    padding:.85rem; border-top:1px solid {C['border']}; margin-top:1.8rem;
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
SYM           = "Bs"
UMBRAL_CRIT   = 70.0
UMBRAL_ALERT  = 90.0
_TP           = "rgba(0,0,0,0)"
PLOTLY_TMPL   = "plotly_white"

# ─────────────────────────────────────────────────────────────────────────────
# PARSERS
# ─────────────────────────────────────────────────────────────────────────────
def parse_bs(val) -> float:
    if pd.isna(val) or str(val).strip() in ("", "-", "—"):
        return np.nan
    s   = str(val).strip()
    neg = s.startswith("-")
    s   = s.replace("-", "").replace("Bs", "").replace(",", "").replace(" ", "")
    try:
        return -float(s) if neg else float(s)
    except ValueError:
        return np.nan

def parse_pct(val) -> float:
    if pd.isna(val) or str(val).strip() in ("", "-", "—"):
        return np.nan
    try:
        return float(str(val).replace("%", "").replace(",", ".").strip())
    except ValueError:
        return np.nan

def get_grupo(suc: str) -> str:
    s = str(suc).strip().upper()
    if s.startswith("CF "):    return "Chico Fresa"
    if "HAPPY"        in s:    return "La Happy Hour"
    if "SANTO DOMINGO" in s:   return "Santo Domingo Urubo"
    return "Otras"

# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS — pd.read_csv directo desde Google Sheets público
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner="⏳ Actualizando datos desde Google Sheets…")
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(CSV_URL)
        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()

        rename = {
            "FECHA":            "Fecha",
            "SUCURSAL":         "Sucursal",
            "VENTA PROYECTADA": "V_Proyectada",
            "VENTA REAL":       "V_Real",
            "DESVIACIÓN":       "Desviacion",
            "% CUMPLIMIENTO":   "Pct_Cump",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

        df["Fecha"]        = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
        df["V_Proyectada"] = df["V_Proyectada"].apply(parse_bs)
        df["V_Real"]       = df["V_Real"].apply(parse_bs)
        df["Desviacion"]   = df["Desviacion"].apply(parse_bs)
        df["Pct_Cump"]     = df["Pct_Cump"].apply(parse_pct)

        mask = df["Pct_Cump"].isna() & df["V_Proyectada"].notna() & (df["V_Proyectada"] != 0)
        df.loc[mask, "Pct_Cump"] = df.loc[mask, "V_Real"] / df.loc[mask, "V_Proyectada"] * 100

        df["Grupo"]     = df["Sucursal"].apply(get_grupo)
        df["Mes"]       = df["Fecha"].dt.to_period("M").astype(str)
        df["Dia_Sem"]   = df["Fecha"].dt.day_name()
        df["Semana"]    = df["Fecha"].dt.isocalendar().week.astype(int)
        df["Sobre_Meta"]= df["Pct_Cump"] >= 100

        return df.dropna(subset=["Fecha"])

    except Exception as e:
        st.error(f"⚠️ Error al leer Google Sheets: {e}")
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# RUN RATE
# ─────────────────────────────────────────────────────────────────────────────
def calcular_run_rate(df_mes: pd.DataFrame, df_full: pd.DataFrame) -> dict:
    hoy   = date.today()
    d_cur = hoy.day
    d_mes = calendar.monthrange(hoy.year, hoy.month)[1]

    venta_acum    = df_mes["V_Real"].sum() if not df_mes.empty else 0
    proy_total    = df_mes["V_Proyectada"].sum() if not df_mes.empty else 0
    run_rate      = (venta_acum / d_cur * d_mes) if d_cur > 0 else 0

    primer = hoy.replace(day=1)
    ant    = primer - timedelta(days=1)
    mask_ant = (df_full["Fecha"].dt.year == ant.year) & (df_full["Fecha"].dt.month == ant.month)
    venta_ant = df_full[mask_ant]["V_Real"].sum()

    rr_suc = (
        df_mes.groupby("Sucursal")["V_Real"].sum()
        .reset_index().rename(columns={"V_Real": "Acumulado"})
    ) if not df_mes.empty else pd.DataFrame(columns=["Sucursal","Acumulado"])
    rr_suc["Run_Rate"] = (rr_suc["Acumulado"] / d_cur * d_mes)

    proy_suc = (
        df_mes.groupby("Sucursal")["V_Proyectada"].sum()
        .reset_index().rename(columns={"V_Proyectada":"Proy_Total"})
    ) if not df_mes.empty else pd.DataFrame(columns=["Sucursal","Proy_Total"])
    rr_suc = rr_suc.merge(proy_suc, on="Sucursal", how="left")
    rr_suc["Delta"] = rr_suc["Run_Rate"] - rr_suc["Proy_Total"]

    return {
        "run_rate":    run_rate,
        "venta_acum":  venta_acum,
        "proy_total":  proy_total,
        "venta_ant":   venta_ant,
        "d_cur":       d_cur,
        "d_mes":       d_mes,
        "rr_suc":      rr_suc.sort_values("Run_Rate", ascending=False),
        "mes_label":   hoy.strftime("%B %Y").title(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS UI
# ─────────────────────────────────────────────────────────────────────────────
def fmt(v):
    if pd.isna(v): return f"{SYM} 0"
    return f"{SYM} {v:,.0f}"

def fmt_pct(v):
    if pd.isna(v): return "—"
    return f"{v:.1f}%"

def kpi(title, value, badge="", bt="bnu", variant=""):
    cls = f"kpi{'-'+variant if variant else ''}"
    bh  = f'<span class="badge {bt}">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="{cls}">
      <div class="kpi-title">{title}</div>
      <div class="kpi-value">{value}</div>
      {bh}
    </div>""", unsafe_allow_html=True)

def sec(label):
    st.markdown(f'<div class="sec">{label}</div>', unsafe_allow_html=True)

def barra(pct):
    pct   = min(max(pct or 0, 0), 100)
    color = (C["red"] if pct < UMBRAL_CRIT else
             C["yellow"] if pct < UMBRAL_ALERT else C["green"])
    return (
        f'<div style="font-size:.75rem;color:{C["slate_lt"]}">{pct:.1f}%</div>'
        f'<div class="prog-wrap"><div class="prog-bar" '
        f'style="width:{pct:.1f}%;background:{color}"></div></div>'
    )

# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICOS
# ─────────────────────────────────────────────────────────────────────────────
def _lay(fig, h=340, **kw):
    kw.setdefault("margin", dict(l=20, r=30, t=30, b=20))
    fig.update_layout(
        template=PLOTLY_TMPL, height=h,
        plot_bgcolor=_TP, paper_bgcolor=_TP,
        **kw)
    return fig

def chart_real_vs_proy(df):
    g = df.groupby("Sucursal").agg(Real=("V_Real","sum"),Proy=("V_Proyectada","sum")).reset_index().sort_values("Real")
    g["Cump"] = (g["Real"]/g["Proy"].replace(0,np.nan)*100).round(1)
    fig = go.Figure()
    # Barra proyectada — sin texto para evitar superposición
    fig.add_trace(go.Bar(x=g["Proy"],y=g["Sucursal"],orientation="h",name="Proyectada",
                         marker_color=C["slate"],opacity=.35,
                         hovertemplate="<b>%{y}</b><br>Proyectada: %{x:,.0f}<extra></extra>"))
    # Barra real — texto con % cumplimiento al final
    fig.add_trace(go.Bar(x=g["Real"],y=g["Sucursal"],orientation="h",name="Real",
                         marker_color=C["yellow"],opacity=.92,
                         text=[f"{fmt(r)}  ({c:.0f}%)" for r,c in zip(g["Real"],g["Cump"])],
                         textposition="outside",
                         hovertemplate="<b>%{y}</b><br>Real: %{x:,.0f}<extra></extra>"))
    return _lay(fig,barmode="overlay",h=max(300,len(g)*58),
                legend=dict(orientation="h",y=1.1),
                margin=dict(l=20,r=200,t=35,b=20))

def chart_cump(df):
    g = df.groupby("Sucursal").agg(Real=("V_Real","sum"),Proy=("V_Proyectada","sum")).reset_index()
    g["Cump"] = (g["Real"]/g["Proy"].replace(0,np.nan)*100).round(1)
    g = g.sort_values("Cump")
    colors = [C["red"] if c<UMBRAL_CRIT else C["yellow"] if c<UMBRAL_ALERT else C["green"]
              for c in g["Cump"]]
    fig = go.Figure(go.Bar(x=g["Cump"],y=g["Sucursal"],orientation="h",
                           marker_color=colors,
                           text=[f"{c:.1f}%" for c in g["Cump"]],textposition="outside"))
    fig.add_vline(x=100,line_dash="dash",line_color=C["slate_lt"],line_width=2)
    return _lay(fig,h=max(280,len(g)*52),showlegend=False,
                xaxis_title="% Cumplimiento",margin=dict(l=20,r=80,t=20,b=30))

def chart_tendencia(df):
    g = df.groupby("Fecha").agg(Real=("V_Real","sum"),Proy=("V_Proyectada","sum")).reset_index().sort_values("Fecha")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g["Fecha"],y=g["Proy"],name="Proyectada",
                             line=dict(color=C["slate_lt"],width=2,dash="dot"),
                             fill="tozeroy",fillcolor="rgba(107,114,128,.07)"))
    fig.add_trace(go.Scatter(x=g["Fecha"],y=g["Real"],name="Real",
                             line=dict(color=C["yellow"],width=3),
                             fill="tozeroy",fillcolor=C["yellow_pale"]))
    return _lay(fig,h=310,legend=dict(orientation="h",y=1.12))

def chart_por_sucursal(df):
    g = df.groupby(["Fecha","Sucursal"])["V_Real"].sum().reset_index()
    fig = px.line(g,x="Fecha",y="V_Real",color="Sucursal",
                  labels={"V_Real":f"Venta Real ({SYM})","Fecha":""},
                  color_discrete_sequence=[C["yellow"],C["green"],C["blue"],C["purple"],
                                           C["orange"],"#EC4899","#14B8A6","#F43F5E","#A78BFA"])
    fig.update_traces(mode="lines+markers",marker=dict(size=5))
    return _lay(fig,h=360,legend=dict(orientation="h",y=1.12))

def chart_heatmap(df):
    orden = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    es    = {"Monday":"Lun","Tuesday":"Mar","Wednesday":"Mié",
             "Thursday":"Jue","Friday":"Vie","Saturday":"Sáb","Sunday":"Dom"}
    g = df.groupby(["Sucursal","Dia_Sem"])["Pct_Cump"].mean().reset_index()
    g["Dia"] = g["Dia_Sem"].map(es)
    dias_disp = [es[d] for d in orden if d in g["Dia_Sem"].unique()]
    pivot = (g.pivot(index="Sucursal",columns="Dia",values="Pct_Cump")
              .reindex(columns=dias_disp).fillna(0))
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#FEE2E2"],[0.5,"#FEF3C7"],[1,"#D1FAE5"]],
        zmin=0, zmax=150,
        text=np.round(pivot.values,1), texttemplate="%{text}%",
    ))
    return _lay(fig,h=max(280,len(pivot)*44),margin=dict(l=20,r=20,t=20,b=20))

def chart_dia_semana(df):
    orden = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    es    = {"Monday":"Lun","Tuesday":"Mar","Wednesday":"Mié",
             "Thursday":"Jue","Friday":"Vie","Saturday":"Sáb","Sunday":"Dom"}
    g = (df.groupby("Dia_Sem").agg(Real=("V_Real","sum"),Cump=("Pct_Cump","mean"))
           .reindex(orden).reset_index().fillna(0))
    g["Dia"] = g["Dia_Sem"].map(es)
    colors = [C["red"] if c<UMBRAL_CRIT else C["yellow"] if c<UMBRAL_ALERT else C["green"]
              for c in g["Cump"]]
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=g["Dia"],y=g["Real"],name="Venta Real",
                         marker_color=colors,opacity=.85), secondary_y=False)
    fig.add_trace(go.Scatter(x=g["Dia"],y=g["Cump"],name="Cumpl. %",
                             mode="lines+markers",
                             line=dict(color=C["slate_dark"],width=2.5),
                             marker=dict(size=9)), secondary_y=True)
    fig.update_yaxes(secondary_y=True,range=[0,160],ticksuffix="%")
    fig.add_hline(y=100,secondary_y=True,line_dash="dash",
                  line_color=C["slate_lt"],line_width=1.5)
    return _lay(fig,h=340,legend=dict(orientation="h",y=1.12))

def chart_gauge(value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=min(value,150),
        title={"text":"Cumplimiento Global","font":{"size":13}},
        delta={"reference":100,"suffix":"%"},
        number={"suffix":"%","font":{"size":28}},
        gauge={
            "axis":{"range":[0,150],"ticksuffix":"%"},
            "bar":{"color":C["yellow"]},
            "steps":[{"range":[0,UMBRAL_CRIT],"color":"#FEE2E2"},
                     {"range":[UMBRAL_CRIT,100],"color":"#FEF3C7"},
                     {"range":[100,150],"color":"#D1FAE5"}],
            "threshold":{"line":{"color":C["green"],"width":4},"thickness":.75,"value":100},
        }
    ))
    fig.update_layout(height=230,margin=dict(l=30,r=30,t=40,b=10),paper_bgcolor=_TP)
    return fig

def get_wow_data(df):
    """
    Retorna dict con datos de las 2 últimas semanas del período filtrado.
    Semanas según ISO (lunes-domingo).
    """
    semanas = sorted(df["Semana"].unique())
    if len(semanas) < 2:
        return None
    sem_act = semanas[-1]
    sem_ant = semanas[-2]

    g = (df[df["Semana"].isin([sem_ant, sem_act])]
           .groupby(["Sucursal","Semana"])
           .agg(Real=("V_Real","sum"), Proy=("V_Proyectada","sum"))
           .reset_index())

    pivot_r = g.pivot(index="Sucursal", columns="Semana", values="Real").fillna(0)
    pivot_p = g.pivot(index="Sucursal", columns="Semana", values="Proy").fillna(0)

    # Asegurar que ambas semanas existan como columnas
    for s in [sem_ant, sem_act]:
        if s not in pivot_r.columns: pivot_r[s] = 0
        if s not in pivot_p.columns: pivot_p[s] = 0

    tbl = pd.DataFrame({
        "Sucursal":   pivot_r.index,
        "Sem_Ant":    pivot_r[sem_ant].values,
        "Sem_Act":    pivot_r[sem_act].values,
        "Proy_Ant":   pivot_p[sem_ant].values,
        "Proy_Act":   pivot_p[sem_act].values,
    })
    tbl["Cambio"]    = tbl["Sem_Act"] - tbl["Sem_Ant"]
    tbl["Cambio_Pct"]= np.where(
        tbl["Sem_Ant"] > 0,
        (tbl["Cambio"] / tbl["Sem_Ant"] * 100), 0
    ).round(1)
    tbl["Cump_Ant"]  = np.where(tbl["Proy_Ant"]>0, tbl["Sem_Ant"]/tbl["Proy_Ant"]*100, 0).round(1)
    tbl["Cump_Act"]  = np.where(tbl["Proy_Act"]>0, tbl["Sem_Act"]/tbl["Proy_Act"]*100, 0).round(1)
    tbl["Delta_Cump"]= (tbl["Cump_Act"] - tbl["Cump_Ant"]).round(1)

    return {
        "tbl":     tbl.sort_values("Cambio_Pct", ascending=False).reset_index(drop=True),
        "sem_act": sem_act,
        "sem_ant": sem_ant,
        "total_act": tbl["Sem_Act"].sum(),
        "total_ant": tbl["Sem_Ant"].sum(),
        "total_proy_act": tbl["Proy_Act"].sum(),
        "total_proy_ant": tbl["Proy_Ant"].sum(),
    }


def chart_wow_barras(wow):
    """Barras agrupadas: semana anterior vs actual por sucursal."""
    t = wow["tbl"].sort_values("Sem_Act", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=t["Sem_Ant"], y=t["Sucursal"], orientation="h",
        name=f"Sem {wow['sem_ant']} (Anterior)",
        marker_color=C["slate"], opacity=.6,
        hovertemplate="<b>%{y}</b><br>Anterior: Bs %{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=t["Sem_Act"], y=t["Sucursal"], orientation="h",
        name=f"Sem {wow['sem_act']} (Actual)",
        marker_color=C["yellow"], opacity=.92,
        text=[f"Bs {v:,.0f}" for v in t["Sem_Act"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Actual: Bs %{x:,.0f}<extra></extra>",
    ))
    return _lay(fig, h=max(300, len(t)*58), barmode="group",
                legend=dict(orientation="h", y=1.1),
                margin=dict(l=20, r=160, t=35, b=20))


def chart_wow_cambio(wow):
    """Barras horizontales del % cambio semana vs semana."""
    t = wow["tbl"].sort_values("Cambio_Pct", ascending=True)
    colors = [C["green"] if v >= 0 else C["red"] for v in t["Cambio_Pct"]]
    fig = go.Figure(go.Bar(
        x=t["Cambio_Pct"], y=t["Sucursal"], orientation="h",
        marker_color=colors,
        text=[f"{'▲' if v>=0 else '▼'} {abs(v):.1f}%" for v in t["Cambio_Pct"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Cambio: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=0, line_color=C["slate_lt"], line_width=1.5)
    return _lay(fig, h=max(280, len(t)*52), showlegend=False,
                xaxis_title="% Cambio vs semana anterior",
                margin=dict(l=20, r=100, t=20, b=20))


def chart_wow_cump(wow):
    """Líneas de cumplimiento semana anterior vs actual."""
    t   = wow["tbl"].sort_values("Cump_Act", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(t))), y=t["Cump_Ant"],
        mode="lines+markers", name=f"Sem {wow['sem_ant']} (Ant.)",
        line=dict(color=C["slate_lt"], width=2, dash="dot"),
        marker=dict(size=8),
        hovertemplate="<b>%{text}</b><br>Ant.: %{y:.1f}%<extra></extra>",
        text=t["Sucursal"].tolist(),
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(t))), y=t["Cump_Act"],
        mode="lines+markers", name=f"Sem {wow['sem_act']} (Act.)",
        line=dict(color=C["yellow"], width=3),
        marker=dict(size=10),
        hovertemplate="<b>%{text}</b><br>Act.: %{y:.1f}%<extra></extra>",
        text=t["Sucursal"].tolist(),
    ))
    fig.add_hline(y=100, line_dash="dash", line_color=C["green"], line_width=1.5)
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(t))),
        ticktext=[s.replace("CF ","") for s in t["Sucursal"]],
        tickangle=-20,
    )
    fig.update_yaxes(ticksuffix="%", range=[0, max(t["Cump_Ant"].max(), t["Cump_Act"].max())*1.15])
    return _lay(fig, h=330, legend=dict(orientation="h", y=1.1))


def chart_desviacion(df):
    g = df.groupby("Fecha").agg(Desv=("Desviacion","sum")).reset_index().sort_values("Fecha")
    g["Acum"] = g["Desv"].cumsum()
    colors = [C["green"] if v>=0 else C["red"] for v in g["Desv"]]
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=g["Fecha"],y=g["Desv"],name="Diaria",
                         marker_color=colors,opacity=.8), secondary_y=False)
    fig.add_trace(go.Scatter(x=g["Fecha"],y=g["Acum"],name="Acumulada",
                             mode="lines",line=dict(color=C["slate_dark"],width=2.5)),
                  secondary_y=True)
    fig.add_hline(y=0,secondary_y=False,line_color=C["slate_lt"],line_width=1)
    fig.update_layout(legend=dict(orientation="h",y=1.12))
    return _lay(fig,h=300)

# ─────────────────────────────────────────────────────────────────────────────
# CARGA
# ─────────────────────────────────────────────────────────────────────────────
df_raw = load_data()

if df_raw.empty:
    st.markdown("""
    <div style="text-align:center;padding:4rem">
      <h2>📭 Sin datos</h2>
      <p>Verifica que el Google Sheet esté compartido como
      <strong>"Cualquier persona con el enlace → Lector"</strong>
      y que la pestaña se llame <strong>BD_VENTAS_DIARIAS</strong>.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{C['slate_dark']},{C['slate']});
                padding:.9rem 1rem;border-radius:10px;
                border-left:4px solid {C['yellow']};margin-bottom:.9rem;">
      <h3 style="color:{C['yellow']};margin:0;font-size:.95rem;">🎛️ Filtros</h3>
      <p style="color:#9CA3AF;font-size:.7rem;margin:.12rem 0 0;">
        Auto-refresh: 60 s</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("**📅 Rango de Fechas**")
    min_d = df_raw["Fecha"].min().date()
    max_d = df_raw["Fecha"].max().date()
    rango = st.date_input("Rango", value=(min_d, max_d),
                          min_value=min_d, max_value=max_d,
                          label_visibility="collapsed")
    fi = rango[0] if isinstance(rango,(list,tuple)) and len(rango)==2 else min_d
    ff = rango[1] if isinstance(rango,(list,tuple)) and len(rango)==2 else max_d

    st.divider()

    st.markdown("**🏢 Grupo**")
    grupos = sorted(df_raw["Grupo"].unique())
    sel_gr = st.multiselect("Grupos", grupos, default=list(grupos),
                             label_visibility="collapsed")

    st.markdown("**🏪 Sucursales**")
    pool_suc = sorted(
        df_raw[df_raw["Grupo"].isin(sel_gr)]["Sucursal"].unique()
        if sel_gr else df_raw["Sucursal"].unique()
    )
    sel_suc = st.multiselect("Sucursales", pool_suc, default=pool_suc,
                              label_visibility="collapsed")

    st.divider()
    st.markdown("**⚠️ Umbral Alerta (%)**")
    u_alert = st.slider("Alerta",  50, 100, int(UMBRAL_ALERT),  5, label_visibility="collapsed")
    st.markdown("**🔴 Umbral Crítico (%)**")
    u_crit  = st.slider("Crítico",  0,  80, int(UMBRAL_CRIT),   5, label_visibility="collapsed")

    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}  |  {len(df_raw):,} filas")

# ─────────────────────────────────────────────────────────────────────────────
# FILTROS
# ─────────────────────────────────────────────────────────────────────────────
df = df_raw.copy()
df = df[(df["Fecha"].dt.date >= fi) & (df["Fecha"].dt.date <= ff)]
if sel_suc:
    df = df[df["Sucursal"].isin(sel_suc)]

if df.empty:
    st.warning("⚠️ Sin datos para la selección actual.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# MÉTRICAS GLOBALES
# ─────────────────────────────────────────────────────────────────────────────
venta_real  = df["V_Real"].sum()
venta_proy  = df["V_Proyectada"].sum()
desv_total  = df["Desviacion"].sum()
cump_global = (venta_real / venta_proy * 100) if venta_proy > 0 else 0
dias_analiz = df["Fecha"].nunique()
dias_sobre  = int(df[df["Sobre_Meta"]]["Fecha"].nunique())

hoy = date.today()
mask_mes = (df["Fecha"].dt.year == hoy.year) & (df["Fecha"].dt.month == hoy.month)
rr = calcular_run_rate(df[mask_mes], df)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <h1>📊 Dashboard de Ventas — Panel Ejecutivo</h1>
  <p>📅 {fi.strftime('%d/%m/%Y')} → {ff.strftime('%d/%m/%Y')}
     &nbsp;|&nbsp; 🏪 {len(sel_suc) if sel_suc else len(pool_suc)} sucursales
     &nbsp;|&nbsp; 📋 {len(df):,} registros
     &nbsp;|&nbsp; ⏱️ {datetime.now().strftime('%H:%M')}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5 = st.tabs([
    "📊 Gerencia","💰 Comercial","📈 Tendencias","⚙️ Operaciones","🎯 Metas y Alertas"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — GERENCIA
# ══════════════════════════════════════════════════════════════════════════════
with t1:
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("💵 Venta Real Total", fmt(venta_real))
    with c2: kpi("🎯 Venta Proyectada", fmt(venta_proy))
    with c3:
        bt = "bp" if cump_global>=100 else ("bw" if cump_global>=u_alert else "bn")
        kpi("📈 Cumplimiento Global", fmt_pct(cump_global),
            badge=f"{'▲' if cump_global>=100 else '▼'} {abs(cump_global-100):.1f}%", bt=bt)
    with c4:
        kpi("📊 Desviación Total", fmt(desv_total),
            badge="▲ Superávit" if desv_total>=0 else "▼ Déficit",
            bt="bp" if desv_total>=0 else "bn")

    st.markdown("<br>", unsafe_allow_html=True)

    col_rr, col_g = st.columns([1,2])
    with col_rr:
        delta_rr = ((rr["run_rate"]-rr["venta_ant"])/rr["venta_ant"]*100
                    if rr["venta_ant"]>0 else 0)
        proy_pct = (rr["run_rate"]/rr["proy_total"]*100 if rr["proy_total"]>0 else 0)
        st.markdown(f"""
        <div class="kpi-dark">
          <div class="kpi-title">🚀 RUN RATE — {rr['mes_label'].upper()}</div>
          <div class="kpi-value">{fmt(rr['run_rate'])}</div>
          <span class="badge {'bp' if delta_rr>=0 else 'bn'}">
            {'▲' if delta_rr>=0 else '▼'} {abs(delta_rr):.1f}% vs mes anterior
          </span><br>
          <span class="badge bnu">🎯 {proy_pct:.1f}% de meta proyectada</span>
          <br><br>
          <small style="color:#9CA3AF">
            Acumulado: {fmt(rr['venta_acum'])}<br>
            Día {rr['d_cur']} de {rr['d_mes']} &nbsp;|&nbsp; Meta: {fmt(rr['proy_total'])}
          </small>
        </div>""", unsafe_allow_html=True)
    with col_g:
        st.plotly_chart(chart_gauge(cump_global), use_container_width=True)

    sec("📅 Venta Real vs Proyectada — Evolución Diaria")
    st.plotly_chart(chart_tendencia(df), use_container_width=True)

    sec("🏢 Resumen por Grupo")
    g_grp = df.groupby("Grupo").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum"), Desv=("Desviacion","sum")
    ).reset_index()
    g_grp["Cumpl_%"] = (g_grp["Real"]/g_grp["Proy"].replace(0,np.nan)*100).round(1)
    g_grp["Real"]     = g_grp["Real"].apply(fmt)
    g_grp["Proy"]     = g_grp["Proy"].apply(fmt)
    g_grp["Desv"]     = g_grp["Desv"].apply(fmt)
    g_grp["Cumpl_%"]  = g_grp["Cumpl_%"].apply(fmt_pct)
    st.dataframe(g_grp, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMERCIAL
# ══════════════════════════════════════════════════════════════════════════════
with t2:
    g_suc = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum")
    ).reset_index()
    g_suc["Cump"] = (g_suc["Real"]/g_suc["Proy"].replace(0,np.nan)*100)
    mejor = g_suc.loc[g_suc["Cump"].idxmax()]
    peor  = g_suc.loc[g_suc["Cump"].idxmin()]

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("🏪 Sucursales", str(df["Sucursal"].nunique()))
    with c2: kpi("🥇 Mayor Cumpl.", mejor["Sucursal"].title(),
                 badge=fmt_pct(mejor["Cump"]), bt="bp", variant="green")
    with c3: kpi("⚠️ Menor Cumpl.", peor["Sucursal"].title(),
                 badge=fmt_pct(peor["Cump"]), bt="bn", variant="red")
    with c4: kpi("📅 Días Analizados", str(dias_analiz))

    st.markdown("<br>", unsafe_allow_html=True)

    col_b, col_c = st.columns([3,2])
    with col_b:
        sec("🏪 Real vs Proyectada por Sucursal")
        st.plotly_chart(chart_real_vs_proy(df), use_container_width=True)
    with col_c:
        sec("📊 % Cumplimiento")
        st.plotly_chart(chart_cump(df), use_container_width=True)

    sec("📋 Detalle por Sucursal")
    det = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum"),
        Desv=("Desviacion","sum"), Cump=("Pct_Cump","mean"),
        Dias=("Fecha","nunique"), Sobre=("Sobre_Meta","sum")
    ).reset_index().sort_values("Cump", ascending=False)
    det["Bajo_Meta"] = det["Dias"] - det["Sobre"]
    det["Real"]  = det["Real"].apply(fmt)
    det["Proy"]  = det["Proy"].apply(fmt)
    det["Desv"]  = det["Desv"].apply(fmt)
    det["Cump"]  = det["Cump"].apply(fmt_pct)
    det["Sobre"] = det["Sobre"].astype(int)
    det["Bajo_Meta"] = det["Bajo_Meta"].astype(int)
    st.dataframe(det.rename(columns={
        "Dias":"Días","Sobre":"✅ Sobre","Bajo_Meta":"❌ Bajo"
    }), use_container_width=True, hide_index=True)

    if not rr["rr_suc"].empty:
        sec(f"🚀 Run Rate por Sucursal — {rr['mes_label']}")
        d = rr["rr_suc"].copy()
        d["Acumulado"]  = d["Acumulado"].apply(fmt)
        d["Run_Rate"]   = d["Run_Rate"].apply(fmt)
        d["Proy_Total"] = d["Proy_Total"].apply(fmt)
        d["Delta"]      = d["Delta"].apply(fmt)
        st.dataframe(d.rename(columns={
            "Acumulado":"Acumulado Mes","Run_Rate":"Proyec. Cierre",
            "Proy_Total":"Meta Proyectada","Delta":"Diferencia"
        }), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TENDENCIAS
# ══════════════════════════════════════════════════════════════════════════════
with t3:

    # ── COMPARACIÓN SEMANA A SEMANA ──────────────────────────────────────────
    wow = get_wow_data(df)

    if wow is None:
        st.info("ℹ️ Se necesitan al menos 2 semanas de datos para la comparación WoW.")
    else:
        cambio_total     = wow["total_act"] - wow["total_ant"]
        cambio_total_pct = (cambio_total / wow["total_ant"] * 100) if wow["total_ant"] > 0 else 0
        cump_act_tot     = (wow["total_act"] / wow["total_proy_act"] * 100) if wow["total_proy_act"] > 0 else 0
        cump_ant_tot     = (wow["total_ant"] / wow["total_proy_ant"] * 100) if wow["total_proy_ant"] > 0 else 0
        delta_cump       = cump_act_tot - cump_ant_tot

        mejor_wow  = wow["tbl"].loc[wow["tbl"]["Cambio_Pct"].idxmax()]
        peor_wow   = wow["tbl"].loc[wow["tbl"]["Cambio_Pct"].idxmin()]

        sec(f"📅 Comparación Semana a Semana  ·  Sem {wow['sem_ant']} vs Sem {wow['sem_act']}")

        c1,c2,c3,c4 = st.columns(4)
        with c1:
            kpi(f"📦 Sem {wow['sem_act']} (Actual)", fmt(wow["total_act"]),
                badge=fmt_pct(cump_act_tot) + " cumpl.", bt="bp" if cump_act_tot>=100 else "bw")
        with c2:
            kpi(f"📦 Sem {wow['sem_ant']} (Anterior)", fmt(wow["total_ant"]),
                badge=fmt_pct(cump_ant_tot) + " cumpl.", bt="bnu")
        with c3:
            kpi("📈 Cambio Semana", fmt(cambio_total),
                badge=f"{'▲' if cambio_total_pct>=0 else '▼'} {abs(cambio_total_pct):.1f}%",
                bt="bp" if cambio_total>=0 else "bn")
        with c4:
            kpi("🎯 Δ Cumplimiento", fmt_pct(delta_cump),
                badge=f"{'▲' if delta_cump>=0 else '▼'} puntos porcentuales",
                bt="bp" if delta_cump>=0 else "bn")

        st.markdown("<br>", unsafe_allow_html=True)

        # Barras agrupadas + cambio %
        col_bar, col_chg = st.columns([3, 2])
        with col_bar:
            st.plotly_chart(chart_wow_barras(wow), use_container_width=True)
        with col_chg:
            st.plotly_chart(chart_wow_cambio(wow), use_container_width=True)

        # Líneas de cumplimiento
        st.plotly_chart(chart_wow_cump(wow), use_container_width=True)

        # Tabla detallada WoW
        tbl_disp = wow["tbl"].copy()
        tbl_disp["Tendencia"] = tbl_disp["Cambio_Pct"].apply(
            lambda v: f"▲ {abs(v):.1f}%" if v >= 0 else f"▼ {abs(v):.1f}%"
        )
        tbl_disp["Δ Cumpl."] = tbl_disp["Delta_Cump"].apply(
            lambda v: f"▲ {abs(v):.1f}pp" if v >= 0 else f"▼ {abs(v):.1f}pp"
        )
        for col in ["Sem_Ant","Sem_Act","Cambio"]:
            tbl_disp[col] = tbl_disp[col].apply(fmt)
        tbl_disp["Cump_Ant"] = tbl_disp["Cump_Ant"].apply(fmt_pct)
        tbl_disp["Cump_Act"] = tbl_disp["Cump_Act"].apply(fmt_pct)

        st.dataframe(
            tbl_disp[["Sucursal","Sem_Ant","Cump_Ant","Sem_Act","Cump_Act","Cambio","Tendencia","Δ Cumpl."]].rename(columns={
                "Sem_Ant": f"Sem {wow['sem_ant']}",
                "Cump_Ant": f"Cumpl. {wow['sem_ant']}",
                "Sem_Act": f"Sem {wow['sem_act']}",
                "Cump_Act": f"Cumpl. {wow['sem_act']}",
                "Cambio": "Δ Venta",
            }),
            use_container_width=True, hide_index=True
        )

        # Ganadores y perdedores
        col_g, col_p = st.columns(2)
        with col_g:
            st.markdown(f"""
            <div class="alert-g">
              🏆 <strong>Mayor crecimiento:</strong> {mejor_wow['Sucursal']}
              &nbsp;|&nbsp; ▲ {mejor_wow['Cambio_Pct']:.1f}%
              &nbsp;|&nbsp; {fmt(mejor_wow['Sem_Ant'])} → {fmt(mejor_wow['Sem_Act'])}
            </div>""", unsafe_allow_html=True)
        with col_p:
            st.markdown(f"""
            <div class="alert-r">
              ⚠️ <strong>Mayor caída:</strong> {peor_wow['Sucursal']}
              &nbsp;|&nbsp; ▼ {abs(peor_wow['Cambio_Pct']):.1f}%
              &nbsp;|&nbsp; {fmt(peor_wow['Sem_Ant'])} → {fmt(peor_wow['Sem_Act'])}
            </div>""", unsafe_allow_html=True)

    st.divider()

    sec("📈 Venta Real por Sucursal — Evolución Diaria")
    st.plotly_chart(chart_por_sucursal(df), use_container_width=True)

    sec("🗓️ Mapa de Calor: % Cumplimiento por Sucursal y Día")
    st.plotly_chart(chart_heatmap(df), use_container_width=True)

    sec("📉 Desviación Diaria y Acumulada")
    st.plotly_chart(chart_desviacion(df), use_container_width=True)

    sec("📋 Pivot Semanal — Venta Real por Sucursal")
    piv = (df.groupby(["Semana","Sucursal"])["V_Real"].sum().reset_index()
             .pivot(index="Sucursal",columns="Semana",values="V_Real").fillna(0))
    piv.columns = [f"Sem {c}" for c in piv.columns]
    st.dataframe(piv.map(fmt), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — OPERACIONES
# ══════════════════════════════════════════════════════════════════════════════
with t4:
    orden_sem = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    es_dia = {"Monday":"Lunes","Tuesday":"Martes","Wednesday":"Miércoles",
              "Thursday":"Jueves","Friday":"Viernes","Saturday":"Sábado","Sunday":"Domingo"}
    g_dia_venta = df.groupby("Dia_Sem")["V_Real"].sum().reindex(orden_sem)
    mejor_dia   = es_dia.get(g_dia_venta.idxmax(), "—")
    prom_real   = df.groupby("Fecha")["V_Real"].sum().mean()
    prom_proy   = df.groupby("Fecha")["V_Proyectada"].sum().mean()

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("📅 Días con Datos", str(dias_analiz))
    with c2: kpi("✅ Días Sobre Meta", str(dias_sobre),
                 badge=f"{dias_sobre/max(dias_analiz,1)*100:.0f}% de los días",
                 bt="bp" if dias_sobre/max(dias_analiz,1)>=.5 else "bn")
    with c3: kpi("⚡ Mejor Día Sem.", mejor_dia)
    with c4: kpi("📊 Prom. Diario", fmt(prom_real),
                 badge=f"Meta: {fmt(prom_proy)}", bt="bnu")

    st.markdown("<br>", unsafe_allow_html=True)

    sec("📅 Rendimiento por Día de la Semana")
    st.plotly_chart(chart_dia_semana(df), use_container_width=True)

    g_dias = df.groupby("Fecha").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum")
    ).reset_index()
    g_dias["Cump"] = (g_dias["Real"]/g_dias["Proy"].replace(0,np.nan)*100).round(1)
    g_dias["Fecha_s"] = g_dias["Fecha"].dt.strftime("%a %d/%m")

    col_t, col_b = st.columns(2)
    with col_t:
        sec("🏆 Top 5 Mejores Días")
        t5d = g_dias.nlargest(5,"Cump")[["Fecha_s","Real","Cump"]].copy()
        t5d["Real"] = t5d["Real"].apply(fmt)
        t5d["Cump"] = t5d["Cump"].apply(fmt_pct)
        st.dataframe(t5d.rename(columns={"Fecha_s":"Fecha","Cump":"Cumpl."}),
                     use_container_width=True, hide_index=True)
    with col_b:
        sec("⚠️ Top 5 Peores Días")
        b5d = g_dias.nsmallest(5,"Cump")[["Fecha_s","Real","Cump"]].copy()
        b5d["Real"] = b5d["Real"].apply(fmt)
        b5d["Cump"] = b5d["Cump"].apply(fmt_pct)
        st.dataframe(b5d.rename(columns={"Fecha_s":"Fecha","Cump":"Cumpl."}),
                     use_container_width=True, hide_index=True)

    sec("📐 Variabilidad del Cumplimiento por Sucursal")
    g_var = df.groupby("Sucursal")["Pct_Cump"].agg(
        Media="mean", Min="min", Max="max", Desv_Std="std"
    ).round(1).reset_index().sort_values("Media", ascending=False)
    for col in ["Media","Min","Max","Desv_Std"]:
        g_var[col] = g_var[col].apply(fmt_pct)
    st.dataframe(g_var, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — METAS Y ALERTAS
# ══════════════════════════════════════════════════════════════════════════════
with t5:
    g_est = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum"),
        Desv=("Desviacion","sum"), Dias=("Fecha","nunique"),
        Sobre=("Sobre_Meta","sum")
    ).reset_index()
    g_est["Cump"] = (g_est["Real"]/g_est["Proy"].replace(0,np.nan)*100).round(1)
    g_est["Estado"] = g_est["Cump"].apply(
        lambda c: "🔴 Crítico" if c<u_crit else ("🟡 Alerta" if c<u_alert else "🟢 En Meta")
    )

    n_crit  = (g_est["Cump"]<u_crit).sum()
    n_alert = ((g_est["Cump"]>=u_crit) & (g_est["Cump"]<u_alert)).sum()
    n_meta  = (g_est["Cump"]>=u_alert).sum()

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("🔴 Crítico",   str(n_crit),  badge=f"< {u_crit}%",  bt="bn", variant="red")
    with c2: kpi("🟡 En Alerta", str(n_alert), badge=f"{u_crit}–{u_alert}%", bt="bw")
    with c3: kpi("🟢 En Meta",   str(n_meta),  badge=f"≥ {u_alert}%", bt="bp", variant="green")
    with c4:
        bt = "bp" if cump_global>=100 else ("bw" if cump_global>=u_alert else "bn")
        kpi("📊 Cumpl. Global", fmt_pct(cump_global), bt=bt)

    st.markdown("<br>", unsafe_allow_html=True)
    sec("🚨 Estado por Sucursal")

    for _, r in g_est.sort_values("Cump").iterrows():
        cls = ("alert-r" if r["Cump"]<u_crit else
               "alert-w" if r["Cump"]<u_alert else "alert-g")
        dias_txt = f"{int(r['Sobre'])}/{int(r['Dias'])} días sobre meta"
        st.markdown(f"""
        <div class="{cls}">
          {r['Estado']} &nbsp;<strong>{r['Sucursal']}</strong>
          &nbsp;|&nbsp; Real: <strong>{fmt(r['Real'])}</strong>
          &nbsp;|&nbsp; Meta: <strong>{fmt(r['Proy'])}</strong>
          &nbsp;|&nbsp; Desv: <strong>{fmt(r['Desv'])}</strong>
          &nbsp;|&nbsp; {dias_txt}
          {barra(r['Cump'])}
        </div>""", unsafe_allow_html=True)

    if not rr["rr_suc"].empty:
        sec(f"📅 Proyección de Cierre — {rr['mes_label']}")
        st.info(f"📌 Run Rate General: **{fmt(rr['run_rate'])}** "
                f"(Día {rr['d_cur']} de {rr['d_mes']})")
        d = rr["rr_suc"].copy()
        d["Cump_Proy"] = (d["Run_Rate"]/d["Proy_Total"].replace(0,np.nan)*100).round(1)
        d["Est"] = d["Cump_Proy"].apply(
            lambda c: "🔴 Crítico" if c<u_crit else ("🟡 Alerta" if c<u_alert else "🟢 En Meta")
        )
        d["Acumulado"]  = d["Acumulado"].apply(fmt)
        d["Run_Rate"]   = d["Run_Rate"].apply(fmt)
        d["Proy_Total"] = d["Proy_Total"].apply(fmt)
        d["Delta"]      = d["Delta"].apply(fmt)
        d["Cump_Proy"]  = d["Cump_Proy"].apply(fmt_pct)
        st.dataframe(d.rename(columns={
            "Acumulado":"Acum. Mes","Run_Rate":"Proyec. Cierre",
            "Proy_Total":"Meta","Delta":"Diferencia",
            "Cump_Proy":"Cumpl. Proy.","Est":"Estado"
        }), use_container_width=True, hide_index=True)

    sec("📋 Histórico de Cumplimiento")
    hist = df[["Fecha","Sucursal","V_Proyectada","V_Real","Desviacion","Pct_Cump"]].copy()
    hist = hist.sort_values(["Fecha","Sucursal"], ascending=[False,True])
    hist["🚦"] = hist["Pct_Cump"].apply(
        lambda c: "🔴" if (c or 0)<u_crit else ("🟡" if (c or 0)<u_alert else "🟢")
    )
    hist["Fecha"]        = hist["Fecha"].dt.strftime("%a %d/%m/%Y")
    hist["V_Proyectada"] = hist["V_Proyectada"].apply(fmt)
    hist["V_Real"]       = hist["V_Real"].apply(fmt)
    hist["Desviacion"]   = hist["Desviacion"].apply(fmt)
    hist["Pct_Cump"]     = hist["Pct_Cump"].apply(fmt_pct)
    st.dataframe(hist.rename(columns={
        "V_Proyectada":"Proyectada","V_Real":"Real",
        "Desviacion":"Desviación","Pct_Cump":"% Cumpl."
    }), use_container_width=True, hide_index=True, height=420)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  📊 Dashboard de Ventas &nbsp;|&nbsp;
  Fuente: Google Sheets (CSV público) &nbsp;|&nbsp;
  Caché 60 s &nbsp;|&nbsp;
  {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""", unsafe_allow_html=True)
