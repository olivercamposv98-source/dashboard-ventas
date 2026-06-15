# =============================================================================
#  DASHBOARD DE VENTAS — BD_VENTAS_DIARIAS
#  Columnas: FECHA | SUCURSAL | VENTA PROYECTADA | VENTA REAL | DESVIACIÓN | % CUMPLIMIENTO
#  Moneda: Bolivianos (Bs)  |  Versión: 2.0
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_gsheets import GSheetsConnection
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

  /* ── Header ── */
  .dash-header {{
    background:linear-gradient(135deg,{C['slate_dark']} 0%,{C['slate']} 100%);
    padding:1.3rem 2rem; border-radius:14px;
    border-left:7px solid {C['yellow']}; margin-bottom:1.3rem;
  }}
  .dash-header h1 {{ color:{C['yellow']}; font-size:1.7rem; font-weight:800; margin:0; }}
  .dash-header p  {{ color:#D1D5DB; margin:.2rem 0 0; font-size:.82rem; }}

  /* ── KPI Cards ── */
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
  .kpi-red .kpi-value   {{ color:#FCA5A5;       font-size:1.65rem; }}
  .badge {{ display:inline-block; font-size:.7rem; font-weight:600;
            padding:.16rem .55rem; border-radius:20px; margin-top:.3rem; }}
  .bp  {{ background:{C['green_pale']}; color:#065F46; }}
  .bn  {{ background:{C['red_pale']};   color:#991B1B; }}
  .bnu {{ background:#F3F4F6;           color:{C['slate']}; }}
  .bw  {{ background:#FEF3C7;           color:#92400E; }}

  /* ── Section title ── */
  .sec {{ font-size:.92rem; font-weight:700; color:{C['slate_dark']};
          border-bottom:2px solid {C['yellow']};
          padding-bottom:.3rem; margin:1.1rem 0 .65rem; }}

  /* ── Alert rows ── */
  .alert-r {{
    background:#FEF2F2; border:1px solid #FECACA;
    border-left:4px solid {C['red']}; padding:.65rem 1rem;
    border-radius:8px; margin:.3rem 0; font-size:.83rem;
  }}
  .alert-w {{
    background:#FFFBEB; border:1px solid {C['yellow_lt']};
    border-left:4px solid {C['yellow']}; padding:.65rem 1rem;
    border-radius:8px; margin:.3rem 0; font-size:.83rem;
  }}
  .alert-g {{
    background:{C['green_pale']}; border:1px solid #6EE7B7;
    border-left:4px solid {C['green']}; padding:.65rem 1rem;
    border-radius:8px; margin:.3rem 0; font-size:.83rem;
  }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
    gap:.4rem; background:{C['bg']}; padding:.32rem; border-radius:10px;
  }}
  .stTabs [data-baseweb="tab"] {{
    border-radius:8px; padding:.42rem .85rem;
    font-weight:600; font-size:.8rem;
  }}
  .stTabs [aria-selected="true"] {{
    background:{C['yellow']} !important; color:{C['slate_dark']} !important;
  }}

  /* ── Progress bar cumplimiento ── */
  .prog-wrap {{ background:#E5E7EB; border-radius:8px; height:10px; margin:.25rem 0; }}
  .prog-bar  {{ height:10px; border-radius:8px; transition:width .4s ease; }}

  /* ── Footer ── */
  .footer {{
    text-align:center; color:{C['slate_lt']}; font-size:.7rem;
    padding:.85rem; border-top:1px solid {C['border']}; margin-top:1.8rem;
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
WORKSHEET_NAME   = "BD_VENTAS_DIARIAS"   # ← nombre exacto de la pestaña en Google Sheets
SYM              = "Bs"                  # Símbolo de moneda
UMBRAL_CRITICO   = 70.0                  # % cumplimiento crítico
UMBRAL_ALERTA    = 90.0                  # % cumplimiento de alerta
PLOTLY_TMPL      = "plotly_white"
_TP              = "rgba(0,0,0,0)"       # fondo transparente

# ─────────────────────────────────────────────────────────────────────────────
# PARSERS DE VALORES CON FORMATO "Bs" Y "%"
# ─────────────────────────────────────────────────────────────────────────────
def parse_bs(val) -> float:
    """'Bs4,725' | '-Bs2,205' | '' → float (0 si vacío)"""
    if pd.isna(val) or str(val).strip() in ("", "-", "—"):
        return np.nan
    s = str(val).strip()
    neg = s.startswith("-")
    s   = s.replace("-", "").replace("Bs", "").replace(",", "").replace(" ", "")
    try:
        return -float(s) if neg else float(s)
    except ValueError:
        return np.nan


def parse_pct(val) -> float:
    """'53.33%' → 53.33 | '' → nan"""
    if pd.isna(val) or str(val).strip() in ("", "-", "—"):
        return np.nan
    try:
        return float(str(val).replace("%", "").replace(",", ".").strip())
    except ValueError:
        return np.nan


# ─────────────────────────────────────────────────────────────────────────────
# AGRUPACIÓN AUTOMÁTICA DE SUCURSALES
# ─────────────────────────────────────────────────────────────────────────────
def get_grupo(suc: str) -> str:
    s = str(suc).strip().upper()
    if s.startswith("CF "):
        return "Cafeterías CF"
    if "HAPPY" in s:
        return "La Happy Hour"
    if "SANTO DOMINGO" in s:
        return "Santo Domingo Urubo"
    return "Otras"


# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS  (caché 60 s)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner="⏳ Sincronizando con Google Sheets…")
def load_data() -> pd.DataFrame:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df   = conn.read(worksheet=WORKSHEET_NAME, ttl=60)

        df = df.dropna(how="all")
        df.columns = df.columns.str.strip()

        # Renombrar a nombres limpios
        rename = {
            "FECHA":             "Fecha",
            "SUCURSAL":          "Sucursal",
            "VENTA PROYECTADA":  "V_Proyectada",
            "VENTA REAL":        "V_Real",
            "DESVIACIÓN":        "Desviacion",
            "% CUMPLIMIENTO":    "Pct_Cump",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

        # Tipos
        df["Fecha"]        = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
        df["V_Proyectada"] = df["V_Proyectada"].apply(parse_bs)
        df["V_Real"]       = df["V_Real"].apply(parse_bs)
        df["Desviacion"]   = df["Desviacion"].apply(parse_bs)
        df["Pct_Cump"]     = df["Pct_Cump"].apply(parse_pct)

        # Recalcular % cuando venga vacío (robustez)
        mask = df["Pct_Cump"].isna() & df["V_Proyectada"].notna() & df["V_Proyectada"] != 0
        df.loc[mask, "Pct_Cump"] = df.loc[mask, "V_Real"] / df.loc[mask, "V_Proyectada"] * 100

        # Columnas derivadas
        df["Grupo"]     = df["Sucursal"].apply(get_grupo)
        df["Mes"]       = df["Fecha"].dt.to_period("M").astype(str)
        df["Dia_Sem"]   = df["Fecha"].dt.day_name()
        df["Dia_Num"]   = df["Fecha"].dt.dayofweek   # 0=Lun
        df["Semana"]    = df["Fecha"].dt.isocalendar().week.astype(int)
        df["Sobre_Meta"]= df["Pct_Cump"] >= 100

        return df.dropna(subset=["Fecha"])

    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DE RUN RATE
# ─────────────────────────────────────────────────────────────────────────────
def calcular_run_rate(df_mes: pd.DataFrame, df_full: pd.DataFrame) -> dict:
    """
    df_mes  = datos filtrados SOLO del mes actual
    df_full = datos de todas las sucursales seleccionadas (todos los meses)
    """
    hoy    = date.today()
    d_cur  = hoy.day
    d_mes  = calendar.monthrange(hoy.year, hoy.month)[1]

    venta_acum = df_mes["V_Real"].sum(min_count=1) or 0
    proy_acum  = df_mes["V_Proyectada"].sum(min_count=1) or 0
    run_rate   = (venta_acum / d_cur * d_mes) if d_cur > 0 else 0

    # Proyectada total del mes (si existen todos los días en la hoja)
    proy_total_mes = df_mes["V_Proyectada"].sum()

    # Mes anterior para delta
    primer = hoy.replace(day=1)
    ant    = primer - timedelta(days=1)
    mask_ant = (
        (df_full["Fecha"].dt.year  == ant.year) &
        (df_full["Fecha"].dt.month == ant.month)
    )
    venta_ant = df_full[mask_ant]["V_Real"].sum()

    # Run Rate por sucursal
    rr_suc = (
        df_mes.groupby("Sucursal")["V_Real"].sum()
        .reset_index().rename(columns={"V_Real": "Acumulado"})
    )
    rr_suc["Run_Rate"] = (rr_suc["Acumulado"] / d_cur * d_mes)
    proy_suc = (
        df_mes.groupby("Sucursal")["V_Proyectada"].sum()
        .reset_index().rename(columns={"V_Proyectada": "Proy_Total"})
    )
    rr_suc = rr_suc.merge(proy_suc, on="Sucursal", how="left")
    rr_suc["Delta_vs_Proy"] = rr_suc["Run_Rate"] - rr_suc["Proy_Total"]

    return {
        "run_rate":       run_rate,
        "venta_acum":     venta_acum,
        "proy_acum":      proy_acum,
        "proy_total_mes": proy_total_mes,
        "venta_ant":      venta_ant,
        "d_cur":          d_cur,
        "d_mes":          d_mes,
        "rr_suc":         rr_suc.sort_values("Run_Rate", ascending=False),
        "mes_label":      hoy.strftime("%B %Y").title(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS UI
# ─────────────────────────────────────────────────────────────────────────────
def fmt(v, sym=SYM):
    if pd.isna(v): return f"{sym} 0"
    return f"{sym} {v:,.0f}"

def fmt_pct(v):
    if pd.isna(v): return "—"
    return f"{v:.1f}%"

def fmt_num(v):
    if abs(v) >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if abs(v) >= 1_000:     return f"{v/1_000:.1f}K"
    return f"{v:,.0f}"

def kpi(title, value, badge="", bt="bnu", variant=""):
    cls  = f"kpi{'-' + variant if variant else ''}"
    bh   = f'<span class="badge {bt}">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="{cls}">
      <div class="kpi-title">{title}</div>
      <div class="kpi-value">{value}</div>
      {bh}
    </div>""", unsafe_allow_html=True)

def sec(label):
    st.markdown(f'<div class="sec">{label}</div>', unsafe_allow_html=True)

def barra_cump(pct, mostrar_label=True):
    """Mini barra horizontal de cumplimiento con color semáforo."""
    pct_clip = min(max(pct or 0, 0), 150)
    color = (C["red"] if pct < UMBRAL_CRITICO
             else C["yellow"] if pct < UMBRAL_ALERTA
             else C["green"])
    label = f"{pct:.1f}%" if mostrar_label else ""
    return (
        f'<div style="font-size:.78rem;color:{C["slate_lt"]};margin-bottom:.1rem">{label}</div>'
        f'<div class="prog-wrap"><div class="prog-bar" '
        f'style="width:{min(pct_clip,100):.1f}%;background:{color}"></div></div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE GRÁFICOS
# ─────────────────────────────────────────────────────────────────────────────
def _lay(fig, h=340, **kw):
    fig.update_layout(
        template=PLOTLY_TMPL, height=h,
        plot_bgcolor=_TP, paper_bgcolor=_TP,
        margin=dict(l=20, r=30, t=30, b=20), **kw
    )
    return fig


def chart_real_vs_proy_sucursal(df):
    g = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum")
    ).reset_index().sort_values("Real", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=g["Proy"], y=g["Sucursal"], orientation="h",
                         name="Proyectada", marker_color=C["slate"], opacity=.6,
                         text=[fmt(v) for v in g["Proy"]], textposition="outside"))
    fig.add_trace(go.Bar(x=g["Real"], y=g["Sucursal"], orientation="h",
                         name="Real", marker_color=C["yellow"], opacity=.9,
                         text=[fmt(v) for v in g["Real"]], textposition="outside"))
    return _lay(fig, barmode="overlay", showlegend=True,
                legend=dict(orientation="h", y=1.1),
                xaxis_tickformat=f",", h=max(280, len(g)*52),
                margin=dict(l=20, r=140, t=35, b=20))


def chart_cump_sucursal(df):
    g = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum")
    ).reset_index()
    g["Cump"] = (g["Real"] / g["Proy"].replace(0, np.nan) * 100).round(1)
    g = g.sort_values("Cump", ascending=True)
    colors = [C["red"] if c < UMBRAL_CRITICO
              else C["yellow"] if c < UMBRAL_ALERTA
              else C["green"] for c in g["Cump"]]
    fig = go.Figure(go.Bar(
        x=g["Cump"], y=g["Sucursal"], orientation="h",
        marker_color=colors,
        text=[f"{c:.1f}%" for c in g["Cump"]], textposition="outside",
    ))
    fig.add_vline(x=100, line_dash="dash", line_color=C["slate_lt"], line_width=2)
    fig.add_annotation(x=100, y=-0.5, text="Meta 100%", showarrow=False,
                       font=dict(size=10, color=C["slate_lt"]))
    return _lay(fig, showlegend=False, h=max(280, len(g)*52),
                xaxis_title="% Cumplimiento",
                margin=dict(l=20, r=80, t=20, b=30))


def chart_tendencia_diaria(df):
    g = df.groupby("Fecha").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum")
    ).reset_index().sort_values("Fecha")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=g["Fecha"], y=g["Proy"], name="Proyectada",
        line=dict(color=C["slate_lt"], width=2, dash="dot"),
        fill="tozeroy", fillcolor="rgba(107,114,128,.07)"
    ))
    fig.add_trace(go.Scatter(
        x=g["Fecha"], y=g["Real"], name="Real",
        line=dict(color=C["yellow"], width=3),
        fill="tozeroy", fillcolor=C["yellow_pale"]
    ))
    return _lay(fig, h=310, legend=dict(orientation="h", y=1.12))


def chart_tendencia_sucursal(df):
    g = df.groupby(["Fecha","Sucursal"])["V_Real"].sum().reset_index()
    fig = px.line(
        g, x="Fecha", y="V_Real", color="Sucursal",
        labels={"V_Real":"Venta Real (Bs)", "Fecha":""},
        color_discrete_sequence=[
            C["yellow"],C["green"],C["blue"],C["purple"],
            C["orange"],"#EC4899","#14B8A6","#F43F5E","#A78BFA"]
    )
    fig.update_traces(mode="lines+markers", marker=dict(size=5))
    return _lay(fig, h=360, legend=dict(orientation="h", y=1.12))


def chart_heatmap(df):
    orden_dias  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    nombres_dia = {"Monday":"Lun","Tuesday":"Mar","Wednesday":"Mié",
                   "Thursday":"Jue","Friday":"Vie","Saturday":"Sáb","Sunday":"Dom"}
    g = (df.groupby(["Sucursal","Dia_Sem"])
           .agg(Cump=("Pct_Cump","mean"))
           .reset_index())
    g["Dia_ES"] = g["Dia_Sem"].map(nombres_dia)
    pivot = (g.pivot(index="Sucursal", columns="Dia_ES", values="Cump")
              .reindex(columns=[nombres_dia[d] for d in orden_dias if d in
                                 g["Dia_Sem"].unique()])
              .fillna(0))
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#FEE2E2"],[0.5,"#FEF3C7"],[1,"#D1FAE5"]],
        zmin=0, zmax=150,
        text=np.round(pivot.values, 1),
        texttemplate="%{text}%",
        hovertemplate="Sucursal: %{y}<br>Día: %{x}<br>Cumpl.: %{z:.1f}%<extra></extra>",
    ))
    return _lay(fig, h=max(280, len(pivot)*44),
                xaxis_title="", yaxis_title="",
                margin=dict(l=20,r=20,t=20,b=20))


def chart_dia_semana(df):
    orden  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    es_map = {"Monday":"Lun","Tuesday":"Mar","Wednesday":"Mié",
              "Thursday":"Jue","Friday":"Vie","Saturday":"Sáb","Sunday":"Dom"}
    g = (df.groupby("Dia_Sem")
           .agg(Real=("V_Real","sum"), Cump=("Pct_Cump","mean"), N=("Fecha","count"))
           .reindex(orden).reset_index().fillna(0))
    g["Dia"] = g["Dia_Sem"].map(es_map)
    colors  = [C["red"] if c<UMBRAL_CRITICO
               else C["yellow"] if c<UMBRAL_ALERTA
               else C["green"] for c in g["Cump"]]
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=g["Dia"], y=g["Real"], name=f"Venta Real",
                         marker_color=colors, opacity=.85,
                         text=[fmt(v) for v in g["Real"]], textposition="outside"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=g["Dia"], y=g["Cump"], name="Cumpl. %",
                             mode="lines+markers",
                             line=dict(color=C["slate_dark"], width=2.5),
                             marker=dict(size=9)),
                  secondary_y=True)
    fig.update_yaxes(secondary_y=True, range=[0,160], ticksuffix="%")
    fig.add_hline(y=100, secondary_y=True, line_dash="dash",
                  line_color=C["slate_lt"], line_width=1.5)
    return _lay(fig, h=340, legend=dict(orientation="h", y=1.12))


def chart_gauge(value, title="Cumplimiento Global"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=min(value, 150),
        title={"text": title, "font":{"size":13}},
        delta={"reference":100,"suffix":"%"},
        number={"suffix":"%","font":{"size":28}},
        gauge={
            "axis":{"range":[0,150],"ticksuffix":"%"},
            "bar":{"color":C["yellow"]},
            "steps":[
                {"range":[0,UMBRAL_CRITICO],  "color":"#FEE2E2"},
                {"range":[UMBRAL_CRITICO,100],"color":"#FEF3C7"},
                {"range":[100,150],            "color":"#D1FAE5"},
            ],
            "threshold":{"line":{"color":C["green"],"width":4},
                          "thickness":.75,"value":100},
        }
    ))
    fig.update_layout(height=230, margin=dict(l=30,r=30,t=40,b=10),
                      paper_bgcolor=_TP)
    return fig


def chart_desviacion_acum(df):
    g = (df.groupby("Fecha")
           .agg(Desv=("Desviacion","sum"))
           .reset_index().sort_values("Fecha"))
    g["Desv_Acum"] = g["Desv"].cumsum()
    colors = [C["green"] if v >= 0 else C["red"] for v in g["Desv"]]
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.add_trace(go.Bar(x=g["Fecha"], y=g["Desv"], name="Desv. Diaria",
                         marker_color=colors, opacity=.8), secondary_y=False)
    fig.add_trace(go.Scatter(x=g["Fecha"], y=g["Desv_Acum"],
                             name="Desv. Acumulada", mode="lines",
                             line=dict(color=C["slate_dark"], width=2.5,
                                       dash="solid")), secondary_y=True)
    fig.add_hline(y=0, secondary_y=False, line_color=C["slate_lt"],
                  line_width=1, line_dash="solid")
    fig.update_layout(legend=dict(orientation="h",y=1.12))
    return _lay(fig, h=300)


def chart_scatter_real_vs_proy(df):
    g = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum"),
        Cump=("Pct_Cump","mean")
    ).reset_index()
    fig = px.scatter(
        g, x="Proy", y="Real", text="Sucursal",
        size="Real", color="Cump",
        color_continuous_scale=[[0,"#EF4444"],[.5,"#F59E0B"],[1,"#10B981"]],
        labels={"Proy":"Venta Proyectada","Real":"Venta Real","Cump":"Cumpl. %"},
    )
    max_v = max(g["Real"].max(), g["Proy"].max()) * 1.05
    fig.add_trace(go.Scatter(x=[0, max_v], y=[0, max_v],
                             mode="lines", name="Meta 100%",
                             line=dict(color=C["slate_lt"], dash="dash", width=1.5)))
    fig.update_traces(textposition="top center", selector=dict(mode="markers+text"))
    return _lay(fig, h=360, showlegend=False, coloraxis_showscale=True,
                margin=dict(l=20,r=20,t=20,b=20))


# ─────────────────────────────────────────────────────────────────────────────
# CARGA INICIAL
# ─────────────────────────────────────────────────────────────────────────────
df_raw = load_data()

if df_raw.empty:
    st.markdown("""
    <div style="text-align:center;padding:4rem">
      <h2>📭 Sin datos</h2>
      <p>Verifica que el Google Sheet esté publicado y que la pestaña
         se llame <strong>BD_VENTAS_DIARIAS</strong>.</p>
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
        Auto-actualización: 60 s</p>
    </div>""", unsafe_allow_html=True)

    # Rango de fechas
    st.markdown("**📅 Rango de Fechas**")
    min_d = df_raw["Fecha"].min().date()
    max_d = df_raw["Fecha"].max().date()
    rango = st.date_input("Rango", value=(min_d, max_d),
                          min_value=min_d, max_value=max_d,
                          label_visibility="collapsed")
    fi = rango[0] if isinstance(rango,(list,tuple)) and len(rango)==2 else min_d
    ff = rango[1] if isinstance(rango,(list,tuple)) and len(rango)==2 else max_d

    st.divider()

    # Grupo → Sucursales (cascada)
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

    # Umbral editable
    st.markdown("**⚠️ Umbral Alerta (%)**")
    u_alerta  = st.slider("Alerta",  50, 100, int(UMBRAL_ALERTA),  5,
                           label_visibility="collapsed")
    st.markdown("**🔴 Umbral Crítico (%)**")
    u_critico = st.slider("Crítico", 0,   80, int(UMBRAL_CRITICO), 5,
                           label_visibility="collapsed")

    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}  |  {len(df_raw):,} filas")

# ─────────────────────────────────────────────────────────────────────────────
# APLICAR FILTROS
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
venta_real   = df["V_Real"].sum()
venta_proy   = df["V_Proyectada"].sum()
desv_total   = df["Desviacion"].sum()
cump_global  = (venta_real / venta_proy * 100) if venta_proy > 0 else 0
dias_analiz  = df["Fecha"].nunique()
dias_sobre   = df[df["Sobre_Meta"] == True]["Fecha"].nunique()

# Run Rate — mes actual
hoy = date.today()
mask_mes = (df["Fecha"].dt.year == hoy.year) & (df["Fecha"].dt.month == hoy.month)
rr = calcular_run_rate(df[mask_mes], df)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <h1>📊 Dashboard de Ventas — Panel Ejecutivo</h1>
  <p>
    📅 {fi.strftime('%d/%m/%Y')} → {ff.strftime('%d/%m/%Y')}
    &nbsp;|&nbsp; 🏪 {len(sel_suc) if sel_suc else len(pool_suc)} sucursales
    &nbsp;|&nbsp; 📋 {len(df):,} registros
    &nbsp;|&nbsp; ⏱️ {datetime.now().strftime('%H:%M')}
  </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑAS
# ─────────────────────────────────────────────────────────────────────────────
t_ger, t_com, t_tend, t_ope, t_meta = st.tabs([
    "📊 Gerencia",
    "💰 Comercial",
    "📈 Tendencias",
    "⚙️ Operaciones",
    "🎯 Metas y Alertas",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 ── GERENCIA
# ══════════════════════════════════════════════════════════════════════════════
with t_ger:
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        kpi("💵 Venta Real Total", fmt(venta_real))
    with c2:
        kpi("🎯 Venta Proyectada", fmt(venta_proy))
    with c3:
        btype = "bp" if cump_global >= 100 else ("bw" if cump_global >= u_alerta else "bn")
        kpi("📈 Cumplimiento Global", fmt_pct(cump_global),
            badge=f"{'▲' if cump_global>=100 else '▼'} {abs(cump_global-100):.1f}% vs meta",
            bt=btype)
    with c4:
        kpi("📊 Desviación Total",
            fmt(desv_total),
            badge="▲ Superávit" if desv_total >= 0 else "▼ Déficit",
            bt="bp" if desv_total >= 0 else "bn")

    st.markdown("<br>", unsafe_allow_html=True)

    # Run Rate + Gauge
    col_rr, col_g = st.columns([1, 2])
    with col_rr:
        delta_rr = ((rr["run_rate"] - rr["venta_ant"]) / rr["venta_ant"] * 100
                    if rr["venta_ant"] > 0 else 0)
        proy_rr_pct = (rr["run_rate"] / rr["proy_total_mes"] * 100
                       if rr["proy_total_mes"] > 0 else 0)
        st.markdown(f"""
        <div class="kpi-dark">
          <div class="kpi-title">🚀 RUN RATE — {rr['mes_label'].upper()}</div>
          <div class="kpi-value">{fmt(rr['run_rate'])}</div>
          <span class="badge {'bp' if delta_rr>=0 else 'bn'}">
            {'▲' if delta_rr>=0 else '▼'} {abs(delta_rr):.1f}% vs mes anterior
          </span><br>
          <span class="badge bnu">🎯 {proy_rr_pct:.1f}% de meta proyectada</span>
          <br><br>
          <small style="color:#9CA3AF">
            Acumulado: {fmt(rr['venta_acum'])}<br>
            Día {rr['d_cur']} de {rr['d_mes']} &nbsp;|&nbsp;
            Meta mes: {fmt(rr['proy_total_mes'])}
          </small>
        </div>""", unsafe_allow_html=True)

    with col_g:
        st.plotly_chart(chart_gauge(cump_global), use_container_width=True)

    # Tendencia diaria global
    sec("📅 Venta Real vs Proyectada — Evolución Diaria")
    st.plotly_chart(chart_tendencia_diaria(df), use_container_width=True)

    # Mini resumen por grupo
    sec("🏢 Resumen por Grupo de Sucursales")
    g_grp = df.groupby("Grupo").agg(
        Real=("V_Real","sum"),
        Proy=("V_Proyectada","sum"),
        Desv=("Desviacion","sum"),
    ).reset_index()
    g_grp["Cumpl_%"] = (g_grp["Real"] / g_grp["Proy"].replace(0,np.nan)*100).round(1)
    g_grp["Real"] = g_grp["Real"].apply(fmt)
    g_grp["Proy"] = g_grp["Proy"].apply(fmt)
    g_grp["Desv"] = g_grp["Desv"].apply(fmt)
    g_grp["Cumpl_%"] = g_grp["Cumpl_%"].apply(fmt_pct)
    st.dataframe(g_grp, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 ── COMERCIAL
# ══════════════════════════════════════════════════════════════════════════════
with t_com:
    # KPIs de sucursales
    g_suc_kpi = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum")
    ).reset_index()
    g_suc_kpi["Cump"] = (g_suc_kpi["Real"]/g_suc_kpi["Proy"].replace(0,np.nan)*100)
    mejor = g_suc_kpi.loc[g_suc_kpi["Cump"].idxmax()]
    peor  = g_suc_kpi.loc[g_suc_kpi["Cump"].idxmin()]

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("🏪 Sucursales Activas", str(df["Sucursal"].nunique()))
    with c2: kpi("🥇 Mayor Cumplimiento",
                 mejor["Sucursal"].title(),
                 badge=fmt_pct(mejor["Cump"]), bt="bp",
                 variant="green")
    with c3: kpi("⚠️ Menor Cumplimiento",
                 peor["Sucursal"].title(),
                 badge=fmt_pct(peor["Cump"]), bt="bn",
                 variant="red")
    with c4: kpi("📅 Días Analizados", str(dias_analiz))

    st.markdown("<br>", unsafe_allow_html=True)

    # Barras Real vs Proyectada
    col_b, col_c = st.columns([3, 2])
    with col_b:
        sec("🏪 Venta Real vs Proyectada por Sucursal")
        st.plotly_chart(chart_real_vs_proy_sucursal(df), use_container_width=True)
    with col_c:
        sec("📊 % Cumplimiento por Sucursal")
        st.plotly_chart(chart_cump_sucursal(df), use_container_width=True)

    # Scatter proyectada vs real
    sec("🎯 Dispersión: Real vs Proyectada (diagonal = 100%)")
    st.plotly_chart(chart_scatter_real_vs_proy(df), use_container_width=True)

    # Tabla detallada
    sec("📋 Detalle por Sucursal")
    det = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"),
        Proy=("V_Proyectada","sum"),
        Desv=("Desviacion","sum"),
        Cump_Prom=("Pct_Cump","mean"),
        Dias=("Fecha","nunique"),
        Dias_Sobre=("Sobre_Meta","sum"),
    ).reset_index().sort_values("Cump_Prom", ascending=False)
    det["Bajo_Meta"]    = det["Dias"] - det["Dias_Sobre"]
    det["Real"]         = det["Real"].apply(fmt)
    det["Proy"]         = det["Proy"].apply(fmt)
    det["Desv"]         = det["Desv"].apply(fmt)
    det["Cump_Prom"]    = det["Cump_Prom"].apply(fmt_pct)
    det["Dias_Sobre"]   = det["Dias_Sobre"].astype(int)
    det["Bajo_Meta"]    = det["Bajo_Meta"].astype(int)
    st.dataframe(det.rename(columns={
        "Dias":"Días","Dias_Sobre":"✅ Sobre Meta","Bajo_Meta":"❌ Bajo Meta"
    }), use_container_width=True, hide_index=True)

    # Run Rate por sucursal
    if not rr["rr_suc"].empty:
        sec(f"🚀 Run Rate del Mes ({rr['mes_label']}) por Sucursal")
        rr_d = rr["rr_suc"].copy()
        rr_d["Acumulado"]   = rr_d["Acumulado"].apply(fmt)
        rr_d["Run_Rate"]    = rr_d["Run_Rate"].apply(fmt)
        rr_d["Proy_Total"]  = rr_d["Proy_Total"].apply(fmt)
        rr_d["Delta_vs_Proy"] = rr_d["Delta_vs_Proy"].apply(fmt)
        st.dataframe(rr_d.rename(columns={
            "Acumulado":"Acumulado Mes",
            "Run_Rate":"Proyección Cierre",
            "Proy_Total":"Meta Proyectada",
            "Delta_vs_Proy":"Diferencia"
        }), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 ── TENDENCIAS
# ══════════════════════════════════════════════════════════════════════════════
with t_tend:
    sec("📈 Venta Real por Sucursal — Evolución Diaria")
    st.plotly_chart(chart_tendencia_sucursal(df), use_container_width=True)

    sec("🗓️ Mapa de Calor: % Cumplimiento por Sucursal y Día de Semana")
    st.plotly_chart(chart_heatmap(df), use_container_width=True)

    # Desviación acumulada
    sec("📉 Desviación Diaria y Acumulada")
    st.plotly_chart(chart_desviacion_acum(df), use_container_width=True)

    # Tabla pivote por semana
    sec("📋 Venta Real por Semana y Sucursal")
    piv = (df.groupby(["Semana","Sucursal"])["V_Real"]
             .sum().reset_index()
             .pivot(index="Sucursal", columns="Semana", values="V_Real")
             .fillna(0).applymap(lambda x: fmt(x)))
    piv.columns = [f"Sem {c}" for c in piv.columns]
    st.dataframe(piv, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 ── OPERACIONES
# ══════════════════════════════════════════════════════════════════════════════
with t_ope:
    # KPIs
    mejor_dia_idx = (df.groupby("Dia_Sem")["V_Real"].sum()
                       .reindex(["Monday","Tuesday","Wednesday","Thursday",
                                  "Friday","Saturday","Sunday"])
                       .idxmax())
    dia_es = {"Monday":"Lunes","Tuesday":"Martes","Wednesday":"Miércoles",
              "Thursday":"Jueves","Friday":"Viernes","Saturday":"Sábado","Sunday":"Domingo"}

    prom_diario_real = df.groupby("Fecha")["V_Real"].sum().mean()
    prom_diario_proy = df.groupby("Fecha")["V_Proyectada"].sum().mean()

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("📅 Días con Datos",   str(dias_analiz))
    with c2: kpi("✅ Días Sobre Meta",  str(dias_sobre),
                 badge=f"{dias_sobre/dias_analiz*100:.0f}% de los días" if dias_analiz>0 else "",
                 bt="bp" if dias_sobre/max(dias_analiz,1)>=.5 else "bn")
    with c3: kpi("⚡ Mejor Día Semana", dia_es.get(mejor_dia_idx,"—"))
    with c4: kpi("📊 Promedio Diario",  fmt(prom_diario_real),
                 badge=f"Meta: {fmt(prom_diario_proy)}", bt="bnu")

    st.markdown("<br>", unsafe_allow_html=True)

    sec("📅 Rendimiento por Día de la Semana")
    st.plotly_chart(chart_dia_semana(df), use_container_width=True)

    # Top y bottom días por cumplimiento
    col_top, col_bot = st.columns(2)
    g_dias = (df.groupby("Fecha").agg(
        Real=("V_Real","sum"), Proy=("V_Proyectada","sum")
    ).reset_index())
    g_dias["Cump"] = (g_dias["Real"]/g_dias["Proy"].replace(0,np.nan)*100).round(1)
    g_dias["Fecha_str"] = g_dias["Fecha"].dt.strftime("%a %d/%m")

    with col_top:
        sec("🏆 Top 5 Mejores Días")
        top5 = g_dias.nlargest(5,"Cump")[["Fecha_str","Real","Cump"]].copy()
        top5["Real"] = top5["Real"].apply(fmt)
        top5["Cump"] = top5["Cump"].apply(fmt_pct)
        st.dataframe(top5.rename(columns={"Fecha_str":"Fecha","Cump":"Cumpl."}),
                     use_container_width=True, hide_index=True)
    with col_bot:
        sec("⚠️ Top 5 Peores Días")
        bot5 = g_dias.nsmallest(5,"Cump")[["Fecha_str","Real","Cump"]].copy()
        bot5["Real"] = bot5["Real"].apply(fmt)
        bot5["Cump"] = bot5["Cump"].apply(fmt_pct)
        st.dataframe(bot5.rename(columns={"Fecha_str":"Fecha","Cump":"Cumpl."}),
                     use_container_width=True, hide_index=True)

    # Variabilidad por sucursal
    sec("📐 Variabilidad del Cumplimiento por Sucursal")
    g_var = df.groupby("Sucursal")["Pct_Cump"].agg(
        Media="mean", Minimo="min", Maximo="max", Desv_Std="std"
    ).round(1).reset_index().sort_values("Media", ascending=False)
    g_var_disp = g_var.copy()
    for col in ["Media","Minimo","Maximo","Desv_Std"]:
        g_var_disp[col] = g_var_disp[col].apply(fmt_pct)
    st.dataframe(g_var_disp, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 ── METAS Y ALERTAS
# ══════════════════════════════════════════════════════════════════════════════
with t_meta:
    # Cálculo estado por sucursal
    g_est = df.groupby("Sucursal").agg(
        Real=("V_Real","sum"),
        Proy=("V_Proyectada","sum"),
        Desv=("Desviacion","sum"),
        Dias=("Fecha","nunique"),
        Dias_Sobre=("Sobre_Meta","sum"),
    ).reset_index()
    g_est["Cump"] = (g_est["Real"] / g_est["Proy"].replace(0,np.nan)*100).round(1)
    g_est["Estado"] = g_est["Cump"].apply(
        lambda c: ("🔴 Crítico"  if c < u_critico
                   else "🟡 Alerta" if c < u_alerta
                   else "🟢 En Meta")
    )

    crit_n  = (g_est["Cump"] < u_critico).sum()
    alert_n = ((g_est["Cump"] >= u_critico) & (g_est["Cump"] < u_alerta)).sum()
    meta_n  = (g_est["Cump"] >= u_alerta).sum()

    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi("🔴 Crítico",    str(crit_n),
                 badge=f"< {u_critico}% cumpl.", bt="bn", variant="red")
    with c2: kpi("🟡 En Alerta",  str(alert_n),
                 badge=f"{u_critico}–{u_alerta}%", bt="bw")
    with c3: kpi("🟢 En Meta",    str(meta_n),
                 badge=f"≥ {u_alerta}%", bt="bp", variant="green")
    with c4: kpi("📊 Cumpl. Global", fmt_pct(cump_global),
                 badge=f"{'▲' if cump_global>=100 else '▼'} {abs(cump_global-100):.1f}%",
                 bt="bp" if cump_global>=100 else "bn")

    st.markdown("<br>", unsafe_allow_html=True)

    # Alertas individuales con barra de progreso
    sec("🚨 Estado de Cumplimiento por Sucursal")
    for _, r in g_est.sort_values("Cump").iterrows():
        alerta_cls = ("alert-r" if r["Cump"] < u_critico
                      else "alert-w" if r["Cump"] < u_alerta
                      else "alert-g")
        dias_txt = f"{int(r['Dias_Sobre'])}/{int(r['Dias'])} días sobre meta"
        st.markdown(f"""
        <div class="{alerta_cls}">
          {r['Estado']} &nbsp;<strong>{r['Sucursal']}</strong>
          &nbsp;|&nbsp; Real: <strong>{fmt(r['Real'])}</strong>
          &nbsp;|&nbsp; Meta: <strong>{fmt(r['Proy'])}</strong>
          &nbsp;|&nbsp; Desv: <strong>{fmt(r['Desv'])}</strong>
          &nbsp;|&nbsp; {dias_txt}
          {barra_cump(r['Cump'])}
        </div>""", unsafe_allow_html=True)

    # Proyección de cierre de mes
    if not rr["rr_suc"].empty:
        sec(f"📅 Proyección de Cierre — {rr['mes_label']}")
        st.info(
            f"📌 **Run Rate General:** {fmt(rr['run_rate'])}  "
            f"(Acumulado: {fmt(rr['venta_acum'])} en {rr['d_cur']} días "
            f"de {rr['d_mes']})"
        )
        rr_proj = rr["rr_suc"].copy()
        rr_proj["Cumpl_Proyectado"] = (
            rr_proj["Run_Rate"] / rr_proj["Proy_Total"].replace(0,np.nan)*100
        ).round(1)
        rr_proj["Estado_Proy"] = rr_proj["Cumpl_Proyectado"].apply(
            lambda c: ("🔴 Crítico" if c<u_critico
                       else "🟡 Alerta" if c<u_alerta
                       else "🟢 En Meta")
        )

        fig_proy = go.Figure()
        fig_proy.add_trace(go.Bar(
            x=rr_proj["Run_Rate"], y=rr_proj["Sucursal"], orientation="h",
            name="Proyección", marker_color=C["yellow"], opacity=.85,
            text=[fmt(v) for v in rr_proj["Run_Rate"]], textposition="outside"
        ))
        fig_proy.add_trace(go.Bar(
            x=rr_proj["Proy_Total"], y=rr_proj["Sucursal"], orientation="h",
            name="Meta Mes", marker_color=C["slate"], opacity=.5,
            text=[fmt(v) for v in rr_proj["Proy_Total"]], textposition="outside"
        ))
        fig_proy.update_layout(
            barmode="overlay", template=PLOTLY_TMPL,
            height=max(280, len(rr_proj)*52),
            plot_bgcolor=_TP, paper_bgcolor=_TP,
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=20, r=140, t=35, b=20)
        )
        st.plotly_chart(fig_proy, use_container_width=True)

        # Tabla
        rr_disp = rr_proj.copy()
        rr_disp["Acumulado"]          = rr_disp["Acumulado"].apply(fmt)
        rr_disp["Run_Rate"]           = rr_disp["Run_Rate"].apply(fmt)
        rr_disp["Proy_Total"]         = rr_disp["Proy_Total"].apply(fmt)
        rr_disp["Delta_vs_Proy"]      = rr_disp["Delta_vs_Proy"].apply(fmt)
        rr_disp["Cumpl_Proyectado"]   = rr_disp["Cumpl_Proyectado"].apply(fmt_pct)
        st.dataframe(rr_disp[[
            "Sucursal","Acumulado","Run_Rate","Proy_Total",
            "Delta_vs_Proy","Cumpl_Proyectado","Estado_Proy"
        ]].rename(columns={
            "Acumulado":"Acumulado Mes",
            "Run_Rate":"Proyec. Cierre",
            "Proy_Total":"Meta Proyectada",
            "Delta_vs_Proy":"Diferencia",
            "Cumpl_Proyectado":"Cumpl. Proy.",
            "Estado_Proy":"Estado",
        }), use_container_width=True, hide_index=True)

    # Histórico diario detallado
    sec("📋 Histórico Completo de Cumplimiento")
    hist = df[["Fecha","Sucursal","V_Proyectada","V_Real","Desviacion","Pct_Cump"]].copy()
    hist = hist.sort_values(["Fecha","Sucursal"], ascending=[False, True])
    hist["Estado"] = hist["Pct_Cump"].apply(
        lambda c: ("🔴" if (c or 0) < u_critico
                   else "🟡" if (c or 0) < u_alerta
                   else "🟢")
    )
    hist["Fecha"]        = hist["Fecha"].dt.strftime("%a %d/%m/%Y")
    hist["V_Proyectada"] = hist["V_Proyectada"].apply(fmt)
    hist["V_Real"]       = hist["V_Real"].apply(fmt)
    hist["Desviacion"]   = hist["Desviacion"].apply(fmt)
    hist["Pct_Cump"]     = hist["Pct_Cump"].apply(fmt_pct)
    st.dataframe(
        hist.rename(columns={
            "Fecha":"Fecha","Sucursal":"Sucursal",
            "V_Proyectada":"Proyectada","V_Real":"Real",
            "Desviacion":"Desviación","Pct_Cump":"% Cumpl.","Estado":"🚦"
        }),
        use_container_width=True, hide_index=True, height=430
    )

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  📊 Dashboard de Ventas &nbsp;|&nbsp;
  Fuente: Google Sheets · BD_VENTAS_DIARIAS &nbsp;|&nbsp;
  Caché: 60 s &nbsp;|&nbsp;
  {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""", unsafe_allow_html=True)
