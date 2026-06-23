"""
Dashboard de Ventas Diarias — Dark BI Edition
==============================================
Fuente: Google Sheets  BD_VENTAS_DIARIAS
Moneda: Bolivianos (Bs)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ─────────────────────────────────────────────
#  CONFIG DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Intelligence · BD_VENTAS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  PALETA DARK BI
# ─────────────────────────────────────────────
BG       = "#0A0E1A"
BG2      = "#111827"
BG3      = "#1C2537"
BG4      = "#243044"
CYAN     = "#00F5D4"
CYAN_D   = "rgba(0,245,212,0.12)"
BLUE     = "#4CC9F0"
BLUE_D   = "rgba(76,201,240,0.12)"
RED      = "#FF4757"
RED_D    = "rgba(255,71,87,0.15)"
YELLOW   = "#FFB800"
YELLOW_D = "rgba(255,184,0,0.15)"
GREEN    = "#06D6A0"
GREEN_D  = "rgba(6,214,160,0.15)"
TEXT     = "#E2E8F0"
TEXT_DIM = "#8892B0"
BORDER   = "#1E3A4A"

# ─────────────────────────────────────────────
#  GOOGLE SHEETS
# ─────────────────────────────────────────────
SHEET_ID   = "1kbG1uvxDx5qF6g-ucGgqsTHRqV9IfRHM5J2nj-kQyjA"
SHEET_NAME = "BD_VENTAS_DIARIAS"
CSV_URL    = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
)
SYM          = "Bs"
UMBRAL_CRIT  = 70.0
UMBRAL_ALERT = 90.0
UMBRAL_FC    = 35.0   # Food Cost máximo aceptable %

COMPRAS_URL  = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    f"/gviz/tq?tqx=out:csv&sheet=COMPRAS"
)

# ─────────────────────────────────────────────
#  CSS GLOBAL
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {{
    background:{BG} !important;
    color:{TEXT} !important;
}}
[data-testid="stSidebar"] {{
    background:{BG2} !important;
    border-right:1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] * {{ color:{TEXT} !important; }}
h1,h2,h3,h4 {{ color:{TEXT} !important; }}
.block-container {{ padding-top:1rem !important; }}

.kpi-card {{
    background:{BG3};
    border:1px solid {BORDER};
    border-radius:12px;
    padding:18px 20px;
    text-align:center;
    position:relative;
    overflow:hidden;
}}
.kpi-card::before {{
    content:"";
    position:absolute;
    top:0; left:0; right:0;
    height:3px;
    background:var(--accent);
}}
.kpi-label {{
    font-size:10px;
    letter-spacing:1.5px;
    text-transform:uppercase;
    color:{TEXT_DIM};
    margin-bottom:8px;
}}
.kpi-value {{
    font-size:26px;
    font-weight:800;
    color:var(--accent);
    line-height:1.1;
    margin-bottom:4px;
    word-break:break-word;
}}
.kpi-sub {{
    font-size:11px;
    color:{TEXT_DIM};
}}
.sec-title {{
    font-size:11px;
    letter-spacing:2px;
    text-transform:uppercase;
    color:{CYAN};
    font-weight:600;
    margin-bottom:12px;
    padding-bottom:6px;
    border-bottom:1px solid {BG4};
}}
.alert-r {{background:{RED_D};border-left:3px solid {RED};border-radius:6px;padding:8px 12px;margin:4px 0;color:{TEXT} !important;}}
.alert-w {{background:{YELLOW_D};border-left:3px solid {YELLOW};border-radius:6px;padding:8px 12px;margin:4px 0;color:{TEXT} !important;}}
.alert-g {{background:{GREEN_D};border-left:3px solid {GREEN};border-radius:6px;padding:8px 12px;margin:4px 0;color:{TEXT} !important;}}
.alert-r strong,.alert-w strong,.alert-g strong {{ color:{TEXT} !important; }}
.dark-div {{ border:none;border-top:1px solid {BG4};margin:18px 0; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PARSERS
# ─────────────────────────────────────────────
def parse_bs(val) -> float:
    if pd.isna(val) or str(val).strip() in ("", "-", "—"):
        return np.nan
    s = str(val).strip()
    neg = s.startswith("-")
    s = s.replace("-", "").replace("Bs", "").replace(",", "").replace(" ", "")
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
    if s.startswith("CF "):      return "Chico Fresa"
    if "HAPPY"         in s:     return "La Happy Hour"
    if "SANTO DOMINGO" in s:     return "Santo Domingo Urubo"
    return "Otras"

# ─────────────────────────────────────────────
#  CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_URL, header=0)
    df.columns = [c.strip().upper() for c in df.columns]
    col_map = {}
    for c in df.columns:
        cu = c.upper()
        if "FECHA"       in cu:               col_map[c] = "FECHA"
        elif "SUCURSAL"  in cu:               col_map[c] = "SUCURSAL"
        elif "PROYECTADA" in cu:              col_map[c] = "PROYECTADA"
        elif "REAL"      in cu:               col_map[c] = "REAL"
        elif "DESVIACI"  in cu:               col_map[c] = "DESVIACION"
        elif "CUMPL"     in cu or "%" in cu:  col_map[c] = "CUMPLIMIENTO"
    df = df.rename(columns=col_map)
    for col in ["PROYECTADA", "REAL", "DESVIACION"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_bs)
    if "CUMPLIMIENTO" in df.columns:
        df["CUMPLIMIENTO"] = df["CUMPLIMIENTO"].apply(parse_pct)
    if "FECHA" in df.columns:
        df["FECHA"] = pd.to_datetime(df["FECHA"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["FECHA", "REAL"])
    df = df.sort_values("FECHA")
    if "SUCURSAL" in df.columns:
        df["GRUPO"] = df["SUCURSAL"].apply(get_grupo)
    if "CUMPLIMIENTO" not in df.columns or df["CUMPLIMIENTO"].isna().all():
        df["CUMPLIMIENTO"] = np.where(
            df["PROYECTADA"].notna() & (df["PROYECTADA"] != 0),
            df["REAL"] / df["PROYECTADA"] * 100,
            np.nan
        )
    DIAS = {0:"Lunes",1:"Martes",2:"Miércoles",3:"Jueves",
            4:"Viernes",5:"Sábado",6:"Domingo"}
    df["DIA_SEMANA"] = df["FECHA"].dt.dayofweek.map(DIAS)
    df["DIA_NUM"]    = df["FECHA"].dt.dayofweek
    df["SEMANA_ISO"] = df["FECHA"].dt.isocalendar().week.astype(int)
    df["MES"]        = df["FECHA"].dt.to_period("M").astype(str)
    return df

@st.cache_data(ttl=60)
def load_compras() -> pd.DataFrame:
    try:
        df = pd.read_csv(COMPRAS_URL, header=0)
    except Exception:
        return pd.DataFrame()
    df.columns = [c.strip().upper() for c in df.columns]
    col_map = {}
    for c in df.columns:
        cu = c.upper()
        if   "FECHA"   in cu: col_map[c] = "FECHA"
        elif "MARCA"   in cu: col_map[c] = "MARCA"
        elif "PROVEE"  in cu: col_map[c] = "PROVEEDOR"
        elif "PRODUC"  in cu: col_map[c] = "PRODUCTO"
        elif "MONTO"   in cu: col_map[c] = "MONTO_COMPRA"
    df = df.rename(columns=col_map)
    if "MONTO_COMPRA" in df.columns:
        df["MONTO_COMPRA"] = df["MONTO_COMPRA"].apply(parse_bs)
    if "FECHA" in df.columns:
        df["FECHA"] = pd.to_datetime(df["FECHA"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["FECHA", "MONTO_COMPRA"])
    df = df.sort_values("FECHA")
    if "MARCA" in df.columns:
        df["MARCA"] = df["MARCA"].str.strip().str.upper()
    df["MES"]        = df["FECHA"].dt.to_period("M").astype(str)
    df["SEMANA_ISO"] = df["FECHA"].dt.isocalendar().week.astype(int)
    return df

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
DARK_BASE = dict(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter,sans-serif", color=TEXT, size=12),
    hoverlabel=dict(bgcolor=BG3, font_color=TEXT, bordercolor=BORDER),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_DIM, size=10),
                orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)

def dark_layout(**kw):
    """Returns a layout dict merged with DARK_BASE, without duplicates."""
    base = dict(DARK_BASE)
    base.update(kw)
    return base

def fmt_bs(v, d=0):
    if pd.isna(v): return "—"
    return f"Bs {int(v):,}" if d == 0 else f"Bs {v:,.{d}f}"

def fmt_pct(v):
    if pd.isna(v): return "—"
    return f"{v:.1f}%"

def pct_color(v):
    if pd.isna(v):         return TEXT_DIM
    if v < UMBRAL_CRIT:    return RED
    if v < UMBRAL_ALERT:   return YELLOW
    return GREEN

def kpi(label, value, sub="", accent=CYAN):
    st.markdown(f"""<div class="kpi-card" style="--accent:{accent};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def sec(icon, text):
    st.markdown(f'<div class="sec-title">{icon}&nbsp;&nbsp;{text}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="dark-div"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CARGA
# ─────────────────────────────────────────────
try:
    df_all = load_data()
except Exception as e:
    st.error(f"❌ Error al cargar datos: {e}")
    st.stop()

if df_all.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""<div style="text-align:center;padding:16px 0 24px 0;">
        <div style="font-size:22px;font-weight:900;color:{CYAN};letter-spacing:1px;">⚡ VENTAS BI</div>
        <div style="font-size:10px;color:{TEXT_DIM};letter-spacing:2px;margin-top:4px;">DASHBOARD DIARIO</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:10px;letter-spacing:1px;color:{TEXT_DIM};text-transform:uppercase;margin-bottom:4px;">📅 Período</div>', unsafe_allow_html=True)
    fecha_min = df_all["FECHA"].min().date()
    fecha_max = df_all["FECHA"].max().date()
    rango = st.date_input("Rango", value=(fecha_min, fecha_max),
                          min_value=fecha_min, max_value=fecha_max,
                          label_visibility="collapsed")
    f_ini, f_fin = (rango[0], rango[1]) if len(rango) == 2 else (fecha_min, fecha_max)

    st.markdown("<hr style='border-color:#1E3A4A;margin:12px 0;'>", unsafe_allow_html=True)

    grupos_disp = sorted(df_all["GRUPO"].dropna().unique())
    st.markdown(f'<div style="font-size:10px;letter-spacing:1px;color:{TEXT_DIM};text-transform:uppercase;margin-bottom:4px;">🏷 Marca / Grupo</div>', unsafe_allow_html=True)
    grupos_sel = st.multiselect("Grupos", grupos_disp, default=grupos_disp, label_visibility="collapsed")

    suc_pool = sorted(
        df_all.loc[df_all["GRUPO"].isin(grupos_sel), "SUCURSAL"].dropna().unique()
    ) if grupos_sel else sorted(df_all["SUCURSAL"].dropna().unique())
    st.markdown(f'<div style="font-size:10px;letter-spacing:1px;color:{TEXT_DIM};text-transform:uppercase;margin-bottom:4px;">🏪 Sucursales</div>', unsafe_allow_html=True)
    suc_sel = st.multiselect("Sucursales", suc_pool, default=suc_pool, label_visibility="collapsed")

    st.markdown("<hr style='border-color:#1E3A4A;margin:12px 0;'>", unsafe_allow_html=True)
    from datetime import datetime
    st.markdown(f'<div style="font-size:10px;color:{TEXT_DIM};text-align:center;">Actualizado: {datetime.now().strftime("%d/%m %H:%M")}<br>Auto-refresh cada 60s</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FILTRADO
# ─────────────────────────────────────────────
mask = (
    (df_all["FECHA"].dt.date >= f_ini) &
    (df_all["FECHA"].dt.date <= f_fin)
)
if grupos_sel:
    mask &= df_all["GRUPO"].isin(grupos_sel)
if suc_sel:
    mask &= df_all["SUCURSAL"].isin(suc_sel)

df = df_all[mask].copy()

if df.empty:
    st.warning("Sin datos para los filtros seleccionados.")
    st.stop()

# ─────────────────────────────────────────────
#  CARGA Y FILTRO DE COMPRAS
# ─────────────────────────────────────────────
cp_all = load_compras()
if not cp_all.empty:
    cp_mask = (
        (cp_all["FECHA"].dt.date >= f_ini) &
        (cp_all["FECHA"].dt.date <= f_fin)
    )
    if grupos_sel and "MARCA" in cp_all.columns:
        cp_mask &= cp_all["MARCA"].isin([g.upper() for g in grupos_sel])
    cp = cp_all[cp_mask].copy()
else:
    cp = pd.DataFrame()

# ─────────────────────────────────────────────
#  MÉTRICAS
# ─────────────────────────────────────────────
total_real = df["REAL"].sum()
total_proy = df["PROYECTADA"].sum() if "PROYECTADA" in df.columns else np.nan
cump_global = (total_real / total_proy * 100) if (not np.isnan(total_proy) and total_proy > 0) else np.nan
dias_total  = df["FECHA"].dt.date.nunique()

# Run rate
hoy        = df["FECHA"].max()
dias_mes   = pd.Period(f"{hoy.year}-{hoy.month}", "M").days_in_month
dias_trans  = hoy.day
df_mes      = df[df["FECHA"].dt.to_period("M") == hoy.to_period("M")]
venta_mes   = df_mes["REAL"].sum()
run_rate    = (venta_mes / dias_trans * dias_mes) if dias_trans > 0 else np.nan

# Días sobre meta
daily_sums = df.groupby(df["FECHA"].dt.date).agg(R=("REAL","sum"), P=("PROYECTADA","sum"))
dias_sobre = int((daily_sums["R"] >= daily_sums["P"]).sum()) if "PROYECTADA" in df.columns else 0

suc_agg = (
    df.groupby("SUCURSAL")
    .agg(REAL=("REAL","sum"), PROYECTADA=("PROYECTADA","sum"), GRUPO=("GRUPO","first"))
    .reset_index()
)
suc_agg["CUMPLIMIENTO"] = np.where(
    suc_agg["PROYECTADA"] > 0,
    suc_agg["REAL"] / suc_agg["PROYECTADA"] * 100,
    np.nan
)
suc_agg = suc_agg.sort_values("REAL", ascending=False)

# Food Cost
total_compras = cp["MONTO_COMPRA"].sum() if not cp.empty else np.nan
fc_global = (total_compras / total_real * 100) if (not cp.empty and total_real > 0) else np.nan

# FC por marca
if not cp.empty and "MARCA" in cp.columns:
    cp_marca = cp.groupby("MARCA")["MONTO_COMPRA"].sum().reset_index()
    vt_marca  = df.copy()
    vt_marca["GRUPO"] = vt_marca["GRUPO"].str.upper()
    vt_marca  = vt_marca.groupby("GRUPO")["REAL"].sum().reset_index().rename(
        columns={"GRUPO":"MARCA","REAL":"VENTAS"})
    fc_marca  = cp_marca.merge(vt_marca, on="MARCA", how="outer").fillna(0)
    fc_marca["FC_PCT"] = np.where(
        fc_marca["VENTAS"] > 0,
        fc_marca["MONTO_COMPRA"] / fc_marca["VENTAS"] * 100,
        np.nan
    )
    # FC mensual para tendencia
    cp_mes = cp.groupby(["MES","MARCA"])["MONTO_COMPRA"].sum().reset_index()
    vt_mes_tmp = df.copy()
    vt_mes_tmp["GRUPO"] = vt_mes_tmp["GRUPO"].str.upper()
    vt_mes  = vt_mes_tmp.groupby(["MES","GRUPO"])["REAL"].sum().reset_index().rename(
        columns={"GRUPO":"MARCA","REAL":"VENTAS"})
    fc_mes  = cp_mes.merge(vt_mes, on=["MES","MARCA"], how="outer").fillna(0)
    fc_mes["FC_PCT"] = np.where(
        fc_mes["VENTAS"] > 0,
        fc_mes["MONTO_COMPRA"] / fc_mes["VENTAS"] * 100,
        np.nan
    )
    # FC por proveedor
    if "PROVEEDOR" in cp.columns:
        cp_prov = cp.groupby("PROVEEDOR")["MONTO_COMPRA"].sum().reset_index().sort_values("MONTO_COMPRA", ascending=False)
    else:
        cp_prov = pd.DataFrame()
else:
    fc_marca  = pd.DataFrame()
    fc_mes    = pd.DataFrame()
    cp_prov   = pd.DataFrame()

# ════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════
periodo_str = f"{f_ini.strftime('%d %b')} – {f_fin.strftime('%d %b %Y')}"
cump_color  = pct_color(cump_global)
ch1, ch2 = st.columns([3,1])
with ch1:
    st.markdown(f"""<div style="padding:4px 0 14px 0;">
        <span style="font-size:22px;font-weight:900;color:{TEXT};">Sales Intelligence</span>
        <span style="font-size:13px;color:{TEXT_DIM};margin-left:10px;">{periodo_str}</span>
    </div>""", unsafe_allow_html=True)
with ch2:
    st.markdown(f"""<div style="text-align:right;padding:4px 0 14px 0;">
        <span style="font-size:24px;font-weight:900;color:{cump_color};">{fmt_pct(cump_global)}</span><br>
        <span style="font-size:10px;color:{TEXT_DIM};letter-spacing:1px;">CUMPLIMIENTO GLOBAL</span>
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════
#  KPI ROW
# ════════════════════════════════════════════
k1,k2,k3,k4,k5,k6 = st.columns(6)
with k1:
    kpi("⚡ VENTA REAL TOTAL", fmt_bs(total_real), f"{dias_total} días analizados", CYAN)
with k2:
    kpi("🎯 VENTA PROYECTADA", fmt_bs(total_proy), "meta acumulada", BLUE)
with k3:
    kpi("📈 RUN RATE MES", fmt_bs(run_rate), f"proyección {dias_mes} días", YELLOW)
with k4:
    best_suc = suc_agg.iloc[0]["SUCURSAL"] if not suc_agg.empty else "-"
    best_val = suc_agg.iloc[0]["REAL"] if not suc_agg.empty else np.nan
    label    = (best_suc[:16]+"…") if len(best_suc) > 16 else best_suc
    kpi("🏆 TOP SUCURSAL", label, fmt_bs(best_val), GREEN)
with k5:
    pct_dias = (dias_sobre / dias_total * 100) if dias_total > 0 else 0
    kpi("✅ DÍAS SOBRE META", f"{dias_sobre}/{dias_total}", f"{pct_dias:.0f}% del período",
        GREEN if pct_dias >= 50 else YELLOW)
with k6:
    fc_accent = (RED if (not np.isnan(fc_global) and fc_global > UMBRAL_FC)
                 else (YELLOW if (not np.isnan(fc_global) and fc_global > UMBRAL_FC * 0.8)
                       else GREEN))
    fc_sub    = f"meta ≤{UMBRAL_FC:.0f}%" if not np.isnan(fc_global) else "sin datos compras"
    kpi("🍽 FOOD COST", fmt_pct(fc_global), fc_sub, fc_accent)

divider()

# ════════════════════════════════════════════
#  SECCIÓN 1 — EVOLUCIÓN DIARIA
# ════════════════════════════════════════════
sec("📊", "EVOLUCIÓN DIARIA DE VENTAS")

daily = (
    df.groupby("FECHA")
    .agg(REAL=("REAL","sum"), PROYECTADA=("PROYECTADA","sum"))
    .reset_index()
    .sort_values("FECHA")
)
daily["CUMP"] = np.where(
    daily["PROYECTADA"] > 0,
    daily["REAL"] / daily["PROYECTADA"] * 100,
    np.nan
)
daily["DOT_COLOR"] = daily["CUMP"].apply(pct_color)

col_c, col_d = st.columns([3,1])
with col_c:
    fig = go.Figure()
    # Área Real
    fig.add_trace(go.Scatter(
        x=daily["FECHA"], y=daily["REAL"],
        name="Venta Real",
        mode="lines",
        line=dict(color=CYAN, width=2.5),
        fill="tozeroy", fillcolor=CYAN_D,
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Real: Bs %{y:,.0f}<extra></extra>",
    ))
    # Línea meta
    fig.add_trace(go.Scatter(
        x=daily["FECHA"], y=daily["PROYECTADA"],
        name="Meta",
        mode="lines",
        line=dict(color=BLUE, width=1.5, dash="dot"),
        hovertemplate="<b>%{x|%d %b}</b><br>Meta: Bs %{y:,.0f}<extra></extra>",
    ))
    # Puntos coloreados
    fig.add_trace(go.Scatter(
        x=daily["FECHA"], y=daily["REAL"],
        mode="markers",
        marker=dict(color=daily["DOT_COLOR"].tolist(), size=7,
                    line=dict(width=1, color=BG3)),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig.update_layout(**dark_layout(
        height=340,
        margin=dict(l=10,r=10,t=36,b=10),
        xaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM,size=11)),
        yaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM,size=11), zeroline=False),
    ))
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    top5 = daily.nlargest(5,"REAL")[["FECHA","REAL","CUMP"]].reset_index(drop=True)
    bot5 = daily.nsmallest(5,"REAL")[["FECHA","REAL","CUMP"]].reset_index(drop=True)

    st.markdown(f'<div style="font-size:10px;color:{GREEN};letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">🔥 Mejores días</div>', unsafe_allow_html=True)
    for _, r in top5.iterrows():
        c = pct_color(r["CUMP"])
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
            padding:5px 8px;background:{BG3};border-radius:5px;margin-bottom:3px;">
            <span style="color:{TEXT_DIM};font-size:11px;">{r['FECHA'].strftime('%a %d %b')}</span>
            <span style="color:{CYAN};font-size:12px;font-weight:700;">Bs {int(r['REAL']):,}</span>
            <span style="color:{c};font-size:10px;">{fmt_pct(r['CUMP'])}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:10px;color:{RED};letter-spacing:1px;text-transform:uppercase;margin:10px 0 6px 0;">📉 Días más bajos</div>', unsafe_allow_html=True)
    for _, r in bot5.iterrows():
        c = pct_color(r["CUMP"])
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
            padding:5px 8px;background:{BG3};border-radius:5px;margin-bottom:3px;">
            <span style="color:{TEXT_DIM};font-size:11px;">{r['FECHA'].strftime('%a %d %b')}</span>
            <span style="color:{TEXT};font-size:12px;font-weight:700;">Bs {int(r['REAL']):,}</span>
            <span style="color:{c};font-size:10px;">{fmt_pct(r['CUMP'])}</span>
        </div>""", unsafe_allow_html=True)

divider()

# ════════════════════════════════════════════
#  SECCIÓN 2 — SUCURSALES | SEMANA A SEMANA
# ════════════════════════════════════════════
col_suc, col_wow = st.columns(2)

with col_suc:
    sec("🏪", "RANKING POR SUCURSAL")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=suc_agg["SUCURSAL"], x=suc_agg["PROYECTADA"],
        name="Meta", orientation="h",
        marker_color=BG4,
        hovertemplate="%{y}<br>Meta: Bs %{x:,.0f}<extra></extra>",
    ))
    fig2.add_trace(go.Bar(
        y=suc_agg["SUCURSAL"], x=suc_agg["REAL"],
        name="Real", orientation="h",
        marker=dict(color=[pct_color(v) for v in suc_agg["CUMPLIMIENTO"]], opacity=0.85),
        text=[f"Bs {int(v):,}  {fmt_pct(c)}" for v,c in zip(suc_agg["REAL"],suc_agg["CUMPLIMIENTO"])],
        textposition="outside",
        textfont=dict(size=9, color=TEXT_DIM),
        hovertemplate="%{y}<br>Real: Bs %{x:,.0f}<extra></extra>",
    ))
    h_suc = max(260, len(suc_agg)*34 + 60)
    fig2.update_layout(**dark_layout(
        barmode="overlay", height=h_suc,
        margin=dict(l=10,r=110,t=36,b=10),
        xaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM,size=9), showticklabels=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT,size=10), autorange="reversed"),
        showlegend=False,
    ))
    st.plotly_chart(fig2, use_container_width=True)

with col_wow:
    sec("📆", "SEMANA VS SEMANA")
    semanas = sorted(df["SEMANA_ISO"].unique(), reverse=True)
    DIAS_ORD = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    if len(semanas) >= 2:
        sem_act, sem_ant = semanas[0], semanas[1]
        tot_act = df[df["SEMANA_ISO"]==sem_act]["REAL"].sum()
        tot_ant = df[df["SEMANA_ISO"]==sem_ant]["REAL"].sum()
        diff    = ((tot_act - tot_ant) / tot_ant * 100) if tot_ant > 0 else 0
        dc      = GREEN if diff >= 0 else RED
        arrow   = "▲" if diff >= 0 else "▼"

        st.markdown(f"""<div style="display:flex;gap:8px;margin-bottom:12px;">
            <div style="flex:1;background:{BG3};border:1px solid {BORDER};border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:9px;color:{TEXT_DIM};letter-spacing:1px;margin-bottom:3px;">SEM {sem_act} (actual)</div>
                <div style="font-size:18px;font-weight:800;color:{CYAN};">Bs {int(tot_act):,}</div>
            </div>
            <div style="flex:1;background:{BG3};border:1px solid {BORDER};border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:9px;color:{TEXT_DIM};letter-spacing:1px;margin-bottom:3px;">SEM {sem_ant} (anterior)</div>
                <div style="font-size:18px;font-weight:800;color:{TEXT};">Bs {int(tot_ant):,}</div>
            </div>
            <div style="background:{BG3};border:1px solid {dc};border-radius:8px;padding:12px;text-align:center;min-width:72px;">
                <div style="font-size:9px;color:{TEXT_DIM};letter-spacing:1px;margin-bottom:3px;">VARIACIÓN</div>
                <div style="font-size:18px;font-weight:800;color:{dc};">{arrow}{abs(diff):.1f}%</div>
            </div>
        </div>""", unsafe_allow_html=True)

        d_act = df[df["SEMANA_ISO"]==sem_act].groupby("DIA_SEMANA")["REAL"].sum().reindex(DIAS_ORD, fill_value=0)
        d_ant = df[df["SEMANA_ISO"]==sem_ant].groupby("DIA_SEMANA")["REAL"].sum().reindex(DIAS_ORD, fill_value=0)

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name=f"Sem {sem_ant}", x=DIAS_ORD, y=d_ant.values,
            marker_color=BG4,
            hovertemplate="%{x}<br>Bs %{y:,.0f}<extra></extra>",
        ))
        fig3.add_trace(go.Bar(
            name=f"Sem {sem_act}", x=DIAS_ORD, y=d_act.values,
            marker_color=CYAN, opacity=0.85,
            hovertemplate="%{x}<br>Bs %{y:,.0f}<extra></extra>",
        ))
        fig3.update_layout(**dark_layout(
            barmode="group", height=200,
            margin=dict(l=10,r=10,t=10,b=10),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT_DIM,size=10)),
            yaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM,size=10), zeroline=False),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_DIM,size=10),
                        orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
        ))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Se necesitan al menos 2 semanas de datos.")

divider()

# ════════════════════════════════════════════
#  SECCIÓN 3 — HISTÓRICO DÍAS | HEATMAP
# ════════════════════════════════════════════
col_h, col_hm = st.columns(2)
DIAS_ORD = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

with col_h:
    sec("📅", "HISTÓRICO: QUÉ DÍA SE VENDE MÁS")

    hist = (
        df.groupby("DIA_SEMANA")
        .agg(PROM=("REAL","mean"), TOTAL=("REAL","sum"), N=("REAL","count"))
        .reindex(DIAS_ORD)
        .reset_index()
    )
    max_p = hist["PROM"].max()

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=hist["DIA_SEMANA"],
        y=hist["PROM"].fillna(0),
        marker=dict(
            color=hist["PROM"].fillna(0).tolist(),
            colorscale=[[0,BG4],[0.5,BLUE],[1,CYAN]],
            showscale=False,
        ),
        text=[f"Bs {int(v):,}" if not np.isnan(v) else "" for v in hist["PROM"]],
        textposition="outside",
        textfont=dict(size=10, color=TEXT_DIM),
        hovertemplate="<b>%{x}</b><br>Promedio: Bs %{y:,.0f}<extra></extra>",
    ))
    fig4.update_layout(**dark_layout(
        height=280,
        margin=dict(l=10,r=10,t=36,b=10),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT,size=11)),
        yaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM,size=10),
                   zeroline=False, showticklabels=False),
        showlegend=False,
    ))
    st.plotly_chart(fig4, use_container_width=True)

    if not hist["PROM"].isna().all():
        best_d = hist.loc[hist["PROM"].idxmax(), "DIA_SEMANA"]
        low_d  = hist.loc[hist["PROM"].idxmin(), "DIA_SEMANA"]
        st.markdown(f"""<div style="display:flex;gap:8px;margin-top:4px;">
            <div style="flex:1;background:{GREEN_D};border-left:3px solid {GREEN};border-radius:6px;padding:8px 10px;">
                <div style="font-size:9px;color:{GREEN};letter-spacing:1px;">MEJOR DÍA</div>
                <div style="font-size:15px;font-weight:700;color:{TEXT};">{best_d}</div>
            </div>
            <div style="flex:1;background:{RED_D};border-left:3px solid {RED};border-radius:6px;padding:8px 10px;">
                <div style="font-size:9px;color:{RED};letter-spacing:1px;">DÍA MÁS BAJO</div>
                <div style="font-size:15px;font-weight:700;color:{TEXT};">{low_d}</div>
            </div>
        </div>""", unsafe_allow_html=True)

with col_hm:
    sec("🔥", "HEATMAP — CUMPLIMIENTO % SUCURSAL × DÍA")

    hm = (
        df.groupby(["SUCURSAL","DIA_SEMANA"])
        .agg(R=("REAL","sum"), P=("PROYECTADA","sum"))
        .reset_index()
    )
    hm["C"] = np.where(hm["P"]>0, hm["R"]/hm["P"]*100, np.nan)

    suc_list  = suc_agg["SUCURSAL"].tolist()
    dias_list = [d for d in DIAS_ORD if d in hm["DIA_SEMANA"].values]
    z_vals, txt_vals = [], []
    for s in suc_list:
        rz, rt = [], []
        for d in dias_list:
            sub = hm.loc[(hm["SUCURSAL"]==s)&(hm["DIA_SEMANA"]==d), "C"]
            v   = float(sub.values[0]) if len(sub)>0 and not np.isnan(sub.values[0]) else np.nan
            rz.append(v)
            rt.append(f"{s}<br>{d}: {fmt_pct(v)}" if not np.isnan(v) else f"{s}<br>{d}: —")
        z_vals.append(rz)
        txt_vals.append(rt)

    fig5 = go.Figure(go.Heatmap(
        z=z_vals, x=dias_list, y=suc_list,
        text=txt_vals,
        hovertemplate="%{text}<extra></extra>",
        colorscale=[[0,RED],[0.35,YELLOW],[0.65,"#2DD4BF"],[1,CYAN]],
        zmid=90, zmin=40, zmax=130,
        showscale=True,
        colorbar=dict(thickness=10, len=0.8,
                      tickfont=dict(color=TEXT_DIM,size=9), ticksuffix="%",
                      bgcolor="rgba(0,0,0,0)"),
    ))
    fig5.update_layout(**dark_layout(
        height=max(260, len(suc_list)*30 + 80),
        margin=dict(l=10,r=60,t=36,b=10),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT,size=10), side="top"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT,size=9), autorange="reversed"),
    ))
    st.plotly_chart(fig5, use_container_width=True)

divider()

# ════════════════════════════════════════════
#  SECCIÓN 4 — RUN RATE & GAUGE
# ════════════════════════════════════════════
sec("🚀", "RUN RATE & PROYECCIÓN MENSUAL")

rr1, rr2, rr3 = st.columns([1,2,1])

with rr1:
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=cump_global if not np.isnan(cump_global) else 0,
        number=dict(suffix="%", font=dict(size=28, color=CYAN)),
        delta=dict(reference=100, relative=False, valueformat=".1f", suffix="%",
                   increasing=dict(color=GREEN), decreasing=dict(color=RED)),
        gauge=dict(
            axis=dict(range=[0,130], tickwidth=1, tickcolor=TEXT_DIM,
                      tickfont=dict(color=TEXT_DIM,size=8)),
            bar=dict(color=CYAN, thickness=0.22),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[
                dict(range=[0,UMBRAL_CRIT], color="rgba(255,71,87,0.18)"),
                dict(range=[UMBRAL_CRIT,UMBRAL_ALERT], color="rgba(255,184,0,0.18)"),
                dict(range=[UMBRAL_ALERT,130], color="rgba(0,245,212,0.12)"),
            ],
            threshold=dict(line=dict(color=YELLOW,width=2), thickness=0.75, value=100),
        ),
        title=dict(text="Cumplimiento<br>Global", font=dict(size=11,color=TEXT_DIM)),
    ))
    fig_g.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT), height=230, margin=dict(l=20,r=20,t=40,b=10),
    )
    st.plotly_chart(fig_g, use_container_width=True)

with rr2:
    mes_data = (
        df.groupby("MES")
        .agg(REAL=("REAL","sum"), PROYECTADA=("PROYECTADA","sum"))
        .reset_index().sort_values("MES")
    )
    mes_data["C"] = np.where(mes_data["PROYECTADA"]>0,
                              mes_data["REAL"]/mes_data["PROYECTADA"]*100, np.nan)
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        name="Proyectada", x=mes_data["MES"], y=mes_data["PROYECTADA"],
        marker_color=BG4,
        hovertemplate="%{x}<br>Meta: Bs %{y:,.0f}<extra></extra>",
    ))
    fig6.add_trace(go.Bar(
        name="Real", x=mes_data["MES"], y=mes_data["REAL"],
        marker=dict(color=[pct_color(v) for v in mes_data["C"]], opacity=0.85),
        text=[fmt_pct(v) for v in mes_data["C"]],
        textposition="outside",
        textfont=dict(size=10, color=TEXT_DIM),
        hovertemplate="%{x}<br>Real: Bs %{y:,.0f}<extra></extra>",
    ))
    fig6.update_layout(**dark_layout(
        barmode="overlay", height=230,
        margin=dict(l=10,r=10,t=36,b=10),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT,size=11)),
        yaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM,size=10), zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_DIM,size=10),
                    orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
    ))
    st.plotly_chart(fig6, use_container_width=True)

with rr3:
    proy_pct = (venta_mes / run_rate * 100) if (not np.isnan(run_rate) and run_rate > 0) else np.nan
    rr_c     = pct_color(proy_pct)
    st.markdown(f"""<div style="display:flex;flex-direction:column;gap:8px;padding:8px 0;">
        <div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {YELLOW};border-radius:8px;padding:12px;">
            <div style="font-size:9px;color:{TEXT_DIM};letter-spacing:1px;margin-bottom:3px;">RUN RATE MES</div>
            <div style="font-size:18px;font-weight:800;color:{YELLOW};">{fmt_bs(run_rate)}</div>
            <div style="font-size:10px;color:{TEXT_DIM};">proyección {dias_mes} días</div>
        </div>
        <div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {CYAN};border-radius:8px;padding:12px;">
            <div style="font-size:9px;color:{TEXT_DIM};letter-spacing:1px;margin-bottom:3px;">ACUMULADO MES</div>
            <div style="font-size:18px;font-weight:800;color:{CYAN};">{fmt_bs(venta_mes)}</div>
            <div style="font-size:10px;color:{TEXT_DIM};">día {dias_trans} de {dias_mes}</div>
        </div>
        <div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {rr_c};border-radius:8px;padding:12px;">
            <div style="font-size:9px;color:{TEXT_DIM};letter-spacing:1px;margin-bottom:3px;">AVANCE DEL MES</div>
            <div style="font-size:18px;font-weight:800;color:{rr_c};">{fmt_pct(proy_pct)}</div>
            <div style="font-size:10px;color:{TEXT_DIM};">vs run rate</div>
        </div>
    </div>""", unsafe_allow_html=True)

divider()

# ════════════════════════════════════════════
#  SECCIÓN 5 — FOOD COST TEÓRICO
# ════════════════════════════════════════════
sec("🍽", "FOOD COST TEÓRICO — COMPRAS VS VENTAS")

if cp.empty:
    st.info("Sin datos de compras para el período seleccionado. Verifica que la hoja **COMPRAS** tenga datos y esté pública.")
else:
    fc_col1, fc_col2, fc_col3 = st.columns([1, 1, 1])

    # ── Gauge FC Global ────────────────────────
    with fc_col1:
        fc_val = fc_global if not np.isnan(fc_global) else 0
        fig_fc_g = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=fc_val,
            number=dict(suffix="%", font=dict(size=28, color=RED if fc_val > UMBRAL_FC else GREEN)),
            delta=dict(reference=UMBRAL_FC, relative=False, valueformat=".1f", suffix="%",
                       increasing=dict(color=RED), decreasing=dict(color=GREEN)),
            gauge=dict(
                axis=dict(range=[0, 60], tickwidth=1, tickcolor=TEXT_DIM,
                          tickfont=dict(color=TEXT_DIM, size=8)),
                bar=dict(color=RED if fc_val > UMBRAL_FC else GREEN, thickness=0.22),
                bgcolor="rgba(0,0,0,0)", borderwidth=0,
                steps=[
                    dict(range=[0, UMBRAL_FC * 0.8], color="rgba(6,214,160,0.15)"),
                    dict(range=[UMBRAL_FC * 0.8, UMBRAL_FC], color="rgba(255,184,0,0.18)"),
                    dict(range=[UMBRAL_FC, 60], color="rgba(255,71,87,0.18)"),
                ],
                threshold=dict(line=dict(color=YELLOW, width=2), thickness=0.75, value=UMBRAL_FC),
            ),
            title=dict(text=f"Food Cost Global<br><span style='font-size:11px'>meta ≤{UMBRAL_FC:.0f}%</span>",
                       font=dict(size=11, color=TEXT_DIM)),
        ))
        fig_fc_g.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT), height=230, margin=dict(l=20, r=20, t=40, b=10),
        )
        st.plotly_chart(fig_fc_g, use_container_width=True)

        # Resumen Ventas vs Compras
        fc_resumen_color = RED if fc_val > UMBRAL_FC else GREEN
        st.markdown(f"""<div style="display:flex;flex-direction:column;gap:6px;margin-top:4px;">
            <div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {CYAN};
                        border-radius:7px;padding:10px 12px;display:flex;justify-content:space-between;">
                <span style="font-size:10px;color:{TEXT_DIM};">VENTAS PERÍODO</span>
                <span style="font-size:13px;font-weight:700;color:{CYAN};">{fmt_bs(total_real)}</span>
            </div>
            <div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {YELLOW};
                        border-radius:7px;padding:10px 12px;display:flex;justify-content:space-between;">
                <span style="font-size:10px;color:{TEXT_DIM};">COMPRAS PERÍODO</span>
                <span style="font-size:13px;font-weight:700;color:{YELLOW};">{fmt_bs(total_compras)}</span>
            </div>
            <div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {fc_resumen_color};
                        border-radius:7px;padding:10px 12px;display:flex;justify-content:space-between;">
                <span style="font-size:10px;color:{TEXT_DIM};">FOOD COST %</span>
                <span style="font-size:13px;font-weight:700;color:{fc_resumen_color};">{fmt_pct(fc_global)}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── FC por Marca (barras) ──────────────────
    with fc_col2:
        if not fc_marca.empty and not fc_marca["FC_PCT"].isna().all():
            fig_fc_m = go.Figure()
            fc_colors = [RED if v > UMBRAL_FC else (YELLOW if v > UMBRAL_FC * 0.85 else GREEN)
                         for v in fc_marca["FC_PCT"].fillna(0)]
            fig_fc_m.add_trace(go.Bar(
                y=fc_marca["MARCA"],
                x=fc_marca["FC_PCT"].fillna(0),
                orientation="h",
                marker=dict(color=fc_colors, opacity=0.85),
                text=[f"{fmt_pct(v)}  (Compras: {fmt_bs(c)})"
                      for v, c in zip(fc_marca["FC_PCT"], fc_marca["MONTO_COMPRA"])],
                textposition="outside",
                textfont=dict(size=10, color=TEXT_DIM),
                hovertemplate="<b>%{y}</b><br>FC: %{x:.1f}%<extra></extra>",
            ))
            # Línea de meta
            fig_fc_m.add_vline(
                x=UMBRAL_FC, line_dash="dot", line_color=YELLOW, line_width=1.5,
                annotation_text=f"Meta {UMBRAL_FC:.0f}%",
                annotation_font_color=YELLOW, annotation_font_size=10,
            )
            fig_fc_m.update_layout(**dark_layout(
                height=260,
                margin=dict(l=10, r=140, t=36, b=10),
                title=dict(text="Food Cost % por Marca", font=dict(size=11, color=TEXT_DIM), x=0),
                xaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM, size=10),
                           ticksuffix="%", range=[0, max(fc_marca["FC_PCT"].fillna(0).max() * 1.3, UMBRAL_FC * 1.5)]),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT, size=11), autorange="reversed"),
                showlegend=False,
            ))
            st.plotly_chart(fig_fc_m, use_container_width=True)

            # Tabla marca
            st.markdown(f'<div style="font-size:10px;color:{TEXT_DIM};letter-spacing:1px;margin-bottom:6px;">DETALLE POR MARCA</div>', unsafe_allow_html=True)
            for _, r in fc_marca.sort_values("FC_PCT", ascending=False).iterrows():
                fc_c = RED if r["FC_PCT"] > UMBRAL_FC else (YELLOW if r["FC_PCT"] > UMBRAL_FC * 0.85 else GREEN)
                st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                    padding:5px 8px;background:{BG3};border-radius:5px;margin-bottom:3px;">
                    <span style="color:{TEXT};font-size:11px;font-weight:600;">{r['MARCA']}</span>
                    <span style="color:{TEXT_DIM};font-size:11px;">Compras: {fmt_bs(r['MONTO_COMPRA'])}</span>
                    <span style="color:{TEXT_DIM};font-size:11px;">Ventas: {fmt_bs(r['VENTAS'])}</span>
                    <span style="color:{fc_c};font-size:12px;font-weight:700;">{fmt_pct(r['FC_PCT'])}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No hay datos suficientes para calcular FC por marca.")

    # ── Tendencia FC mensual + Top proveedores ──
    with fc_col3:
        if not fc_mes.empty and not fc_mes["FC_PCT"].isna().all():
            fig_fc_t = go.Figure()
            for marca in fc_mes["MARCA"].unique():
                sub = fc_mes[fc_mes["MARCA"] == marca].sort_values("MES")
                fig_fc_t.add_trace(go.Scatter(
                    x=sub["MES"], y=sub["FC_PCT"],
                    name=marca, mode="lines+markers",
                    line=dict(width=2),
                    marker=dict(size=6),
                    hovertemplate=f"<b>{marca}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
                ))
            fig_fc_t.add_hline(
                y=UMBRAL_FC, line_dash="dot", line_color=YELLOW, line_width=1.5,
                annotation_text=f"Meta {UMBRAL_FC:.0f}%",
                annotation_font_color=YELLOW, annotation_font_size=10,
            )
            fig_fc_t.update_layout(**dark_layout(
                height=200,
                margin=dict(l=10, r=10, t=36, b=10),
                title=dict(text="Tendencia FC % mensual", font=dict(size=11, color=TEXT_DIM), x=0),
                xaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM, size=10)),
                yaxis=dict(gridcolor=BG4, tickfont=dict(color=TEXT_DIM, size=10),
                           zeroline=False, ticksuffix="%"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_DIM, size=9),
                            orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
            ))
            st.plotly_chart(fig_fc_t, use_container_width=True)

        if not cp_prov.empty:
            st.markdown(f'<div style="font-size:10px;color:{TEXT_DIM};letter-spacing:1px;margin:8px 0 6px 0;">TOP PROVEEDORES POR COMPRA</div>', unsafe_allow_html=True)
            max_prov = cp_prov["MONTO_COMPRA"].max()
            for _, r in cp_prov.head(6).iterrows():
                bar_pct = int(r["MONTO_COMPRA"] / max_prov * 100) if max_prov > 0 else 0
                st.markdown(f"""<div style="margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                        <span style="font-size:11px;color:{TEXT};">{r['PROVEEDOR']}</span>
                        <span style="font-size:11px;font-weight:700;color:{YELLOW};">{fmt_bs(r['MONTO_COMPRA'])}</span>
                    </div>
                    <div style="background:{BG4};border-radius:3px;height:5px;">
                        <div style="background:{YELLOW};width:{bar_pct}%;height:100%;border-radius:3px;opacity:0.8;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

divider()

# ════════════════════════════════════════════
#  SECCIÓN 6 — ALERTAS DE CUMPLIMIENTO
# ════════════════════════════════════════════
sec("🚨", "ALERTAS DE CUMPLIMIENTO")

crit = suc_agg[suc_agg["CUMPLIMIENTO"] < UMBRAL_CRIT].sort_values("CUMPLIMIENTO")
warn = suc_agg[(suc_agg["CUMPLIMIENTO"] >= UMBRAL_CRIT) & (suc_agg["CUMPLIMIENTO"] < UMBRAL_ALERT)].sort_values("CUMPLIMIENTO")
ok   = suc_agg[suc_agg["CUMPLIMIENTO"] >= UMBRAL_ALERT].sort_values("CUMPLIMIENTO", ascending=False)

ca, cb, cc = st.columns(3)
with ca:
    st.markdown(f'<div style="font-size:10px;color:{RED};letter-spacing:1px;margin-bottom:6px;">⛔ CRÍTICO (&lt;{UMBRAL_CRIT:.0f}%)</div>', unsafe_allow_html=True)
    if crit.empty:
        st.markdown(f'<div style="color:{TEXT_DIM};font-size:12px;">Ninguna ✓</div>', unsafe_allow_html=True)
    for _, r in crit.iterrows():
        st.markdown(f'<div class="alert-r"><strong>{r["SUCURSAL"]}</strong><br>{fmt_pct(r["CUMPLIMIENTO"])} · {fmt_bs(r["REAL"])}</div>', unsafe_allow_html=True)

with cb:
    st.markdown(f'<div style="font-size:10px;color:{YELLOW};letter-spacing:1px;margin-bottom:6px;">⚠️ ALERTA ({UMBRAL_CRIT:.0f}–{UMBRAL_ALERT:.0f}%)</div>', unsafe_allow_html=True)
    if warn.empty:
        st.markdown(f'<div style="color:{TEXT_DIM};font-size:12px;">Ninguna ✓</div>', unsafe_allow_html=True)
    for _, r in warn.iterrows():
        st.markdown(f'<div class="alert-w"><strong>{r["SUCURSAL"]}</strong><br>{fmt_pct(r["CUMPLIMIENTO"])} · {fmt_bs(r["REAL"])}</div>', unsafe_allow_html=True)

with cc:
    st.markdown(f'<div style="font-size:10px;color:{GREEN};letter-spacing:1px;margin-bottom:6px;">✅ EN META (≥{UMBRAL_ALERT:.0f}%)</div>', unsafe_allow_html=True)
    if ok.empty:
        st.markdown(f'<div style="color:{TEXT_DIM};font-size:12px;">Ninguna</div>', unsafe_allow_html=True)
    for _, r in ok.iterrows():
        st.markdown(f'<div class="alert-g"><strong>{r["SUCURSAL"]}</strong><br>{fmt_pct(r["CUMPLIMIENTO"])} · {fmt_bs(r["REAL"])}</div>', unsafe_allow_html=True)

divider()

# ════════════════════════════════════════════
#  SECCIÓN 6 — TABLA DETALLADA
# ════════════════════════════════════════════
with st.expander("📋  TABLA DETALLADA — todos los registros", expanded=False):
    cols_show = [c for c in ["FECHA","SUCURSAL","GRUPO","REAL","PROYECTADA","DESVIACION","CUMPLIMIENTO"]
                 if c in df.columns]
    tbl = df[cols_show].sort_values(["FECHA","SUCURSAL"], ascending=[False,True]).copy()

    fmt = {
        "FECHA":        lambda v: v.strftime("%d/%m/%Y") if pd.notna(v) else "-",
        "REAL":         lambda v: fmt_bs(v) if not pd.isna(v) else "-",
        "PROYECTADA":   lambda v: fmt_bs(v) if not pd.isna(v) else "-",
        "DESVIACION":   lambda v: fmt_bs(v) if not pd.isna(v) else "-",
        "CUMPLIMIENTO": lambda v: fmt_pct(v) if not pd.isna(v) else "-",
    }
    for col, fn in fmt.items():
        if col in tbl.columns:
            tbl[col] = tbl[col].map(fn)

    st.dataframe(tbl, use_container_width=True, hide_index=True)
