"""
Inverso — Motor de Inteligencia Inmobiliaria
Versión 2.0 · Arquitectura Freemium
"""

import streamlit as st
from datetime import datetime
import math

st.set_page_config(
    page_title="Inverso — Inteligencia Inmobiliaria",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── BENCHMARK DATA ─────────────────────────────────────────────────────────────
BENCHMARK = {
    "Barranquilla": {
        "Riomar / Alto Prado": {"p_min":6_500_000,"p_avg":8_400_000,"p_max":11_000_000,"r_avg":42_000,"cap_ref":0.058,"tier":"premium","desc":"Estrato 6 consolidado"},
        "El Poblado / Villa Campestre": {"p_min":5_800_000,"p_avg":7_200_000,"p_max":9_500_000,"r_avg":37_000,"cap_ref":0.062,"tier":"alto","desc":"Alta demanda ejecutiva"},
        "Buenavista / Villa Santos": {"p_min":3_800_000,"p_avg":4_900_000,"p_max":6_200_000,"r_avg":24_500,"cap_ref":0.060,"tier":"medio","desc":"Zona comercial-residencial mixta"},
        "Puerto Colombia / Pradomar": {"p_min":4_200_000,"p_avg":5_800_000,"p_max":7_800_000,"r_avg":29_000,"cap_ref":0.058,"tier":"alto","desc":"Perfil turístico y segunda vivienda"},
        "Ciudad Jardín / Las Delicias": {"p_min":2_800_000,"p_avg":3_500_000,"p_max":4_500_000,"r_avg":17_500,"cap_ref":0.060,"tier":"medio","desc":"Zona en consolidación"},
    },
    "Bogotá": {
        "Chico / Rosales": {"p_min":9_500_000,"p_avg":12_200_000,"p_max":16_000_000,"r_avg":56_000,"cap_ref":0.055,"tier":"premium","desc":"Top tier Bogotá"},
        "Cedritos / Santa Bárbara": {"p_min":5_500_000,"p_avg":7_100_000,"p_max":9_200_000,"r_avg":35_000,"cap_ref":0.059,"tier":"alto","desc":"Zona norte consolidada"},
        "Chapinero / Zona Rosa": {"p_min":6_000_000,"p_avg":8_000_000,"p_max":11_500_000,"r_avg":40_000,"cap_ref":0.060,"tier":"alto","desc":"Alta demanda joven y corporativa"},
    },
    "Medellín": {
        "El Poblado / Laureles": {"p_min":6_800_000,"p_avg":9_800_000,"p_max":13_500_000,"r_avg":55_000,"cap_ref":0.067,"tier":"premium","desc":"Mejor yield del país"},
        "Envigado / Sabaneta": {"p_min":4_200_000,"p_avg":5_900_000,"p_max":7_800_000,"r_avg":32_000,"cap_ref":0.065,"tier":"alto","desc":"Alta valorización proyectada"},
        "Robledo / Belén": {"p_min":2_500_000,"p_avg":3_800_000,"p_max":5_200_000,"r_avg":19_000,"cap_ref":0.060,"tier":"medio","desc":"Zona media en crecimiento"},
    },
    "Cartagena": {
        "Bocagrande / El Laguito": {"p_min":7_500_000,"p_avg":10_200_000,"p_max":14_000_000,"r_avg":65_000,"cap_ref":0.076,"tier":"premium","desc":"Alta demanda turística / Airbnb"},
        "Manga / Pie de la Popa": {"p_min":4_500_000,"p_avg":6_300_000,"p_max":9_000_000,"r_avg":35_000,"cap_ref":0.067,"tier":"alto","desc":"Zona histórica en valorización"},
    },
}

# ── SCORE ENGINE ───────────────────────────────────────────────────────────────
def calcular_score(precio_m2, bm, cap_rate_real, anos_entrega):
    """
    Score 0–100 ponderado:
    40% precio vs mercado
    35% cap rate vs referencia
    25% riesgo de entrega (planos)
    """
    # Precio (40pts) — penaliza sobreprecio, premia descuento
    desv = (precio_m2 - bm["p_avg"]) / bm["p_avg"]
    if desv <= -0.10:
        pts_precio = 40
    elif desv <= 0:
        pts_precio = 35
    elif desv <= 0.10:
        pts_precio = 28
    elif desv <= 0.20:
        pts_precio = 18
    else:
        pts_precio = max(0, 18 - (desv - 0.20) * 60)

    # Cap rate (35pts)
    ratio_cap = cap_rate_real / bm["cap_ref"]
    if ratio_cap >= 1.10:
        pts_cap = 35
    elif ratio_cap >= 0.95:
        pts_cap = 28
    elif ratio_cap >= 0.80:
        pts_cap = 18
    elif ratio_cap >= 0.65:
        pts_cap = 10
    else:
        pts_cap = 4

    # Riesgo entrega (25pts)
    if anos_entrega == 0:
        pts_entrega = 25
    elif anos_entrega == 1:
        pts_entrega = 22
    elif anos_entrega == 2:
        pts_entrega = 17
    elif anos_entrega == 3:
        pts_entrega = 11
    else:
        pts_entrega = 6

    total = pts_precio + pts_cap + pts_entrega
    return round(min(total, 100)), pts_precio, pts_cap, pts_entrega


def score_color(score):
    if score >= 70: return "#2E7D32", "#E8F5E9", "Buena oportunidad"
    if score >= 50: return "#F57F17", "#FFF8E1", "Riesgo moderado"
    return "#C62828", "#FFEBEE", "Alto riesgo"


def fmt(v): return f"${v/1_000_000:.1f}M" if v >= 1_000_000 else f"${v/1_000:.0f}K"
def fmt_full(v): return f"${v:,.0f}"
def fmtp(v): return f"{v*100:.1f}%"


# ── FISCAL ENGINE ──────────────────────────────────────────────────────────────
def tabla_imporrenta_pn(base):
    rangos = [
        (0, 38_004_000, 0.0),
        (38_004_000, 73_008_000, 0.19),
        (73_008_000, 115_200_000, 0.28),
        (115_200_000, 173_004_000, 0.33),
        (173_004_000, float('inf'), 0.39),
    ]
    imp = 0.0
    for lo, hi, t in rangos:
        if base <= lo: break
        imp += (min(base, hi) - lo) * t
    return imp


def fiscal_engine(valor, canon_mensual, fin_pct, tasa_hipo, ingresos_pn):
    renta_anual = canon_mensual * 12
    intereses = valor * fin_pct * tasa_hipo

    # PN
    costos_pn = renta_anual * 0.30
    neta_pn = max(renta_anual - costos_pn - intereses, 0)
    imp_total_pn = tabla_imporrenta_pn(ingresos_pn + neta_pn)
    imp_solo_pn = tabla_imporrenta_pn(ingresos_pn)
    imp_marginal_pn = imp_total_pn - imp_solo_pn
    neto_pn = neta_pn - imp_marginal_pn
    tasa_ef_pn = imp_marginal_pn / max(neta_pn, 1)

    # SAS
    depreciacion = valor / 45
    costos_sas = renta_anual * 0.12 + renta_anual * 0.005  # admin + ICA
    neta_sas = max(renta_anual - costos_sas - intereses - depreciacion, 0)
    imp_sas = neta_sas * 0.35
    dividendos = neta_sas - imp_sas
    imp_div = dividendos * 0.10
    neto_sas = dividendos - imp_div
    tasa_ef_sas = (imp_sas + imp_div) / max(renta_anual - costos_sas, 1)

    ahorro = neto_sas - neto_pn
    return {
        "renta_anual": renta_anual,
        "intereses": intereses,
        "depreciacion": depreciacion,
        # PN
        "costos_pn": costos_pn, "neta_pn": neta_pn,
        "imp_pn": imp_marginal_pn, "neto_pn": neto_pn,
        "tasa_pn": tasa_ef_pn, "cap_pn": neto_pn / valor,
        # SAS
        "costos_sas": costos_sas, "neta_sas": neta_sas,
        "imp_sas": imp_sas, "imp_div": imp_div,
        "neto_sas": neto_sas, "tasa_sas": tasa_ef_sas,
        "cap_sas": neto_sas / valor,
        # Delta
        "ahorro": ahorro, "ahorro_10": ahorro * 10,
        "ganador": "SAS" if ahorro > 0 else "Persona Natural",
    }


def salida_engine(valor_compra, valorizacion_pct, anos, es_pj):
    valor_venta = valor_compra * ((1 + valorizacion_pct) ** anos)
    costo_fiscal = valor_compra * ((1.04) ** anos)  # ajuste IGAC
    go = max(valor_venta - costo_fiscal, 0)
    tarifa = 0.10 if es_pj else 0.15
    imp_go = go * tarifa
    utilidad = (valor_venta - valor_compra) - imp_go
    roi_anual = ((valor_venta / valor_compra) ** (1/anos) - 1) if anos > 0 else 0
    return {
        "valor_venta": valor_venta, "go": go,
        "costo_fiscal": costo_fiscal, "tarifa": tarifa,
        "imp_go": imp_go, "utilidad": utilidad,
        "roi_total": (valor_venta - valor_compra) / valor_compra,
        "roi_anual": roi_anual,
    }


# ══════════════════════════════════════════════════════════════════════════════
# CSS — Editorial · Minimalista · Tipografía protagonista
# ══════════════════════════════════════════════════════════════════════════════
def css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@300;400;500&display=swap');

:root{
  --ink:#0A0A0A;--ink2:#3D3D3D;--ink3:#8A8A8A;--ink4:#C4C4C4;
  --paper:#FAFAF8;--surface:#F2F1EE;--surface2:#E8E7E3;
  --accent:#1A1A1A;--green:#2E7D32;--green-bg:#E8F5E9;
  --amber:#B45309;--amber-bg:#FEF3C7;
  --red:#B91C1C;--red-bg:#FEE2E2;
  --blue:#1D4ED8;--blue-bg:#EFF6FF;
  --r:10px;--r-sm:6px;
}

@media(prefers-color-scheme:dark){
  :root{
    --ink:#F5F5F0;--ink2:#C8C8C0;--ink3:#8A8A82;--ink4:#4A4A45;
    --paper:#111110;--surface:#1A1A18;--surface2:#242420;
    --accent:#F0EFE8;
    --green:#4ADE80;--green-bg:#052E16;
    --amber:#FCD34D;--amber-bg:#1C1400;
    --red:#F87171;--red-bg:#1A0505;
    --blue:#93C5FD;--blue-bg:#0C1A3A;
  }
}

html,body,[data-testid="stAppViewContainer"]{background:var(--paper)!important;color:var(--ink)!important}
[data-testid="stAppViewContainer"]>.main{background:var(--paper)!important}
.block-container{padding:2rem 2.5rem!important;max-width:1280px!important}
[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--surface2)!important}

h1,h2,h3{font-family:'Instrument Serif',serif!important;font-weight:400!important;letter-spacing:-0.02em}
p,label,span,div,input,select{font-family:'Geist Mono',monospace!important}

/* NAV */
.inv-nav{display:flex;align-items:center;justify-content:space-between;
  padding:1.25rem 0;border-bottom:1px solid var(--surface2);margin-bottom:2.5rem}
.inv-logo{font-family:'Instrument Serif',serif!important;font-size:1.5rem;
  color:var(--ink)!important;letter-spacing:-0.03em}
.inv-logo span{font-style:italic;color:var(--ink3)}
.inv-nav-links{display:flex;gap:1.5rem;align-items:center}
.inv-nav-link{font-size:12px;color:var(--ink3);letter-spacing:0.04em;text-transform:uppercase;
  text-decoration:none;font-family:'Geist Mono',monospace!important}
.inv-pro-badge{background:var(--ink);color:var(--paper);font-size:11px;
  padding:4px 12px;border-radius:4px;letter-spacing:0.06em;text-transform:uppercase;
  font-family:'Geist Mono',monospace!important}

/* SCORE HERO */
.score-hero{text-align:center;padding:3rem 2rem 2.5rem;
  border:1px solid var(--surface2);border-radius:var(--r);
  background:var(--surface);margin-bottom:1.5rem;position:relative;overflow:hidden}
.score-number{font-family:'Instrument Serif',serif!important;font-size:6rem;
  line-height:1;letter-spacing:-0.04em;color:var(--ink)}
.score-label{font-size:11px;letter-spacing:0.14em;text-transform:uppercase;
  color:var(--ink3);margin-top:0.5rem;font-family:'Geist Mono',monospace!important}
.score-verdict{font-size:13px;font-weight:500;margin-top:0.75rem;
  padding:5px 16px;border-radius:4px;display:inline-block;
  font-family:'Geist Mono',monospace!important}

/* INDICADORES */
.ind-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;
  background:var(--surface2);border:1px solid var(--surface2);
  border-radius:var(--r);overflow:hidden;margin-bottom:1.5rem}
.ind-cell{background:var(--paper);padding:1.25rem 1rem}
.ind-label{font-size:10px;letter-spacing:0.12em;text-transform:uppercase;
  color:var(--ink3);margin-bottom:0.4rem;font-family:'Geist Mono',monospace!important}
.ind-value{font-family:'Instrument Serif',serif!important;font-size:1.6rem;
  letter-spacing:-0.02em;color:var(--ink);line-height:1}
.ind-sub{font-size:11px;color:var(--ink3);margin-top:0.25rem;
  font-family:'Geist Mono',monospace!important}
.ind-tag{display:inline-block;font-size:10px;padding:2px 8px;border-radius:3px;
  margin-top:0.4rem;font-family:'Geist Mono',monospace!important;letter-spacing:0.04em}

/* SCORE BAR */
.score-bar-wrap{margin:1.5rem 0 0.25rem}
.score-bar-bg{height:6px;background:var(--surface2);border-radius:3px;
  position:relative;overflow:hidden}
.score-bar-fill{height:100%;border-radius:3px;transition:width 0.6s ease}
.score-ticks{display:flex;justify-content:space-between;
  margin-top:4px;font-size:10px;color:var(--ink4);
  font-family:'Geist Mono',monospace!important}

/* DESGLOSE SCORE */
.score-breakdown{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;
  margin:1.5rem 0}
.sb-item{background:var(--surface);border:1px solid var(--surface2);
  border-radius:var(--r-sm);padding:0.875rem}
.sb-label{font-size:10px;letter-spacing:0.1em;text-transform:uppercase;
  color:var(--ink3);font-family:'Geist Mono',monospace!important}
.sb-val{font-family:'Instrument Serif',serif!important;font-size:1.4rem;
  letter-spacing:-0.02em;margin:0.2rem 0}
.sb-max{font-size:10px;color:var(--ink4);font-family:'Geist Mono',monospace!important}

/* ALERTA */
.alerta{border-radius:var(--r-sm);padding:1rem 1.25rem;margin:1rem 0}
.alerta-title{font-size:12px;font-weight:500;letter-spacing:0.04em;
  font-family:'Geist Mono',monospace!important}
.alerta-body{font-size:12px;margin-top:0.35rem;line-height:1.6;
  font-family:'Geist Mono',monospace!important;opacity:0.85}

/* TABLA FISCAL */
.fiscal-table{width:100%;border-collapse:collapse;font-size:12px;
  font-family:'Geist Mono',monospace!important}
.fiscal-table th{font-size:10px;letter-spacing:0.1em;text-transform:uppercase;
  color:var(--ink3);border-bottom:1px solid var(--surface2);
  padding:0.5rem 0.75rem;text-align:left;font-weight:400}
.fiscal-table td{padding:0.6rem 0.75rem;border-bottom:1px solid var(--surface2);
  color:var(--ink2);vertical-align:top}
.fiscal-table tr:last-child td{border-bottom:none}
.fiscal-table tr.total td{color:var(--ink);font-weight:500;
  border-top:1px solid var(--surface2)}
.fiscal-table .neg{color:var(--red)!important}
.fiscal-table .pos{color:var(--green)!important}
.fiscal-table .hi{color:var(--ink)!important;font-weight:500}

/* PANELS */
.panel{border:1px solid var(--surface2);border-radius:var(--r);
  padding:1.5rem;margin-bottom:1.25rem;background:var(--paper)}
.panel-eyebrow{font-size:10px;letter-spacing:0.14em;text-transform:uppercase;
  color:var(--ink3);margin-bottom:0.5rem;font-family:'Geist Mono',monospace!important}
.panel-title{font-family:'Instrument Serif',serif!important;font-size:1.25rem;
  color:var(--ink);margin-bottom:1rem;letter-spacing:-0.02em}

/* PORTAFOLIO */
.prop-card{border:1px solid var(--surface2);border-radius:var(--r);
  padding:1rem 1.25rem;background:var(--paper);
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:0.5rem;transition:border-color 0.15s}
.prop-card:hover{border-color:var(--ink4)}
.prop-name{font-family:'Instrument Serif',serif!important;font-size:1.05rem;
  color:var(--ink);letter-spacing:-0.01em}
.prop-meta{font-size:11px;color:var(--ink3);margin-top:2px;
  font-family:'Geist Mono',monospace!important}
.prop-score-dot{width:36px;height:36px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-family:'Instrument Serif',serif!important;font-size:0.95rem}

/* WATERFALL */
.wf-row{display:flex;align-items:baseline;justify-content:space-between;
  padding:0.6rem 0;border-bottom:1px solid var(--surface2)}
.wf-row:last-child{border-bottom:none;font-weight:500}
.wf-label{font-size:12px;color:var(--ink2);font-family:'Geist Mono',monospace!important}
.wf-val{font-size:13px;font-family:'Geist Mono',monospace!important}

/* PAYWALL */
.paywall{border:1px solid var(--surface2);border-radius:var(--r);
  padding:2rem;text-align:center;background:var(--surface);margin:1.5rem 0}
.paywall h3{font-family:'Instrument Serif',serif!important;font-size:1.3rem;
  color:var(--ink);margin-bottom:0.5rem}
.paywall p{font-size:12px;color:var(--ink3);line-height:1.7;
  font-family:'Geist Mono',monospace!important;margin-bottom:1.25rem}

/* STREAMLIT OVERRIDES */
.stButton>button{background:var(--ink)!important;color:var(--paper)!important;
  border:none!important;border-radius:6px!important;
  font-family:'Geist Mono',monospace!important;font-size:12px!important;
  letter-spacing:0.06em!important;text-transform:uppercase!important;
  padding:0.6rem 1.5rem!important;width:100%!important}
.stButton>button:hover{opacity:0.85!important}
[data-testid="stNumberInput"]>div>div>input,
[data-testid="stTextInput"]>div>div>input,
.stSelectbox>div>div{
  background:var(--surface)!important;
  border:1px solid var(--surface2)!important;
  border-radius:6px!important;color:var(--ink)!important;
  font-family:'Geist Mono',monospace!important;font-size:13px!important}
label[data-testid="stWidgetLabel"]{
  color:var(--ink3)!important;font-family:'Geist Mono',monospace!important;
  font-size:11px!important;letter-spacing:0.08em!important;text-transform:uppercase!important}
[data-testid="stTabs"]>div:first-child{border-bottom:1px solid var(--surface2)!important}
[data-testid="stTab"]{font-family:'Geist Mono',monospace!important;
  font-size:12px!important;letter-spacing:0.06em!important;text-transform:uppercase!important}
button[data-testid="stTab"][aria-selected="true"]{
  color:var(--ink)!important;
  border-bottom:2px solid var(--ink)!important}
button[data-testid="stTab"]{color:var(--ink3)!important}
[data-testid="stSlider"]>div>div>div>div{background:var(--ink)!important}
.stMarkdown hr{border-color:var(--surface2)!important}
div[data-testid="stVerticalBlock"]{gap:0!important}
</style>
""", unsafe_allow_html=True)


# ── NAV ────────────────────────────────────────────────────────────────────────
def nav():
    st.markdown("""
<div class="inv-nav">
  <div class="inv-logo">inverso<span>.</span></div>
  <div class="inv-nav-links">
    <span class="inv-nav-link">Análisis</span>
    <span class="inv-nav-link">Portafolio</span>
    <span class="inv-nav-link">Fiscal</span>
    <span class="inv-pro-badge">Pro</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    css()
    nav()

    # Estado de sesión
    if "portafolio" not in st.session_state:
        st.session_state.portafolio = []
    if "pro" not in st.session_state:
        st.session_state.pro = False

    tab_analisis, tab_portafolio, tab_fiscal, tab_salida = st.tabs([
        "Analizar Inmueble",
        "Mi Portafolio",
        "Escudo Fiscal",
        "Estrategia de Salida",
    ])

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — ANÁLISIS
    # ══════════════════════════════════════════════════════════════
    with tab_analisis:
        col_form, col_score = st.columns([1, 1.2], gap="large")

        with col_form:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-eyebrow">Ingresa los datos</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">¿Qué inmueble quieres evaluar?</div>', unsafe_allow_html=True)

            nombre = st.text_input("Nombre del proyecto", value="Mi inmueble", key="n_nombre")
            ciudad = st.selectbox("Ciudad", list(BENCHMARK.keys()), key="n_ciudad")
            zona = st.selectbox("Zona / Barrio", list(BENCHMARK[ciudad].keys()), key="n_zona")

            c1, c2 = st.columns(2)
            with c1:
                area = st.number_input("Área m²", min_value=20.0, max_value=500.0, value=67.0, step=1.0, key="n_area")
            with c2:
                ano_entrega = st.number_input("Años hasta entrega", min_value=0, max_value=6, value=2, step=1, key="n_anos")

            precio = st.number_input("Precio total COP", min_value=50_000_000, max_value=5_000_000_000,
                                     value=451_000_000, step=5_000_000, key="n_precio",
                                     help="Si es en planos, usa el precio de lista del constructor")
            canon = st.number_input("Canon mensual esperado COP", min_value=300_000, max_value=20_000_000,
                                    value=1_950_000, step=50_000, key="n_canon",
                                    help="Renta mensual que esperas recibir. Usa el promedio de zona si no sabes.")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("Agregar al portafolio →", key="btn_add"):
                bm = BENCHMARK[ciudad][zona]
                pm2 = precio / area
                cap = (canon * 12) / precio
                sc, sp, sc2, se = calcular_score(pm2, bm, cap, ano_entrega)
                st.session_state.portafolio.append({
                    "nombre": nombre, "ciudad": ciudad, "zona": zona,
                    "area": area, "precio": precio, "canon": canon,
                    "pm2": pm2, "cap": cap, "score": sc,
                    "pts_precio": sp, "pts_cap": sc2, "pts_entrega": se,
                    "anos_entrega": ano_entrega,
                })
                st.success(f"'{nombre}' agregado al portafolio.")

        with col_score:
            bm = BENCHMARK[ciudad][zona]
            pm2 = precio / area if area > 0 else 0
            cap_real = (canon * 12) / precio if precio > 0 else 0
            score, pts_p, pts_c, pts_e = calcular_score(pm2, bm, cap_real, ano_entrega)
            sc_color, sc_bg, sc_veredicto = score_color(score)
            desv = (pm2 - bm["p_avg"]) / bm["p_avg"]

            # SCORE HERO
            st.markdown(f"""
<div class="score-hero">
  <div class="score-label">Puntaje de inversión</div>
  <div class="score-number" style="color:{sc_color}">{score}</div>
  <div class="score-label">sobre 100</div>
  <div class="score-verdict" style="background:{sc_bg};color:{sc_color}">{sc_veredicto}</div>
  <div class="score-bar-wrap">
    <div class="score-bar-bg">
      <div class="score-bar-fill" style="width:{score}%;background:{sc_color}"></div>
    </div>
    <div class="score-ticks"><span>0</span><span>50</span><span>100</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

            # 3 INDICADORES
            desv_label = f"+{desv*100:.0f}% sobre mercado" if desv > 0 else f"{desv*100:.0f}% bajo mercado"
            desv_color = "var(--red)" if desv > 0.15 else "var(--green)" if desv < -0.05 else "var(--amber)"
            cap_color = "var(--green)" if cap_real >= bm["cap_ref"] else "var(--amber)" if cap_real >= bm["cap_ref"]*0.8 else "var(--red)"

            st.markdown(f"""
<div class="ind-grid">
  <div class="ind-cell">
    <div class="ind-label">Precio / m²</div>
    <div class="ind-value">{fmt(pm2)}</div>
    <div class="ind-sub">Zona avg: {fmt(bm['p_avg'])}</div>
    <div class="ind-tag" style="background:{'var(--red-bg)' if desv>0.15 else 'var(--green-bg)'};color:{desv_color}">{desv_label}</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">Cap Rate</div>
    <div class="ind-value" style="color:{cap_color}">{fmtp(cap_real)}</div>
    <div class="ind-sub">Referencia zona: {fmtp(bm['cap_ref'])}</div>
    <div class="ind-tag" style="background:var(--surface);color:var(--ink3)">Renta anual / precio</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">Entrega</div>
    <div class="ind-value">{'Inmediata' if ano_entrega==0 else f'{ano_entrega} año{"s" if ano_entrega>1 else ""}'}</div>
    <div class="ind-sub">{'Sin riesgo de obra' if ano_entrega==0 else 'Riesgo constructora'}</div>
    <div class="ind-tag" style="background:{'var(--green-bg);color:var(--green)' if ano_entrega<=1 else 'var(--amber-bg);color:var(--amber)' if ano_entrega<=3 else 'var(--red-bg);color:var(--red)'}">{'Bajo' if ano_entrega<=1 else 'Moderado' if ano_entrega<=3 else 'Alto'} riesgo</div>
  </div>
</div>
""", unsafe_allow_html=True)

            # DESGLOSE SCORE
            st.markdown(f"""
<div class="score-breakdown">
  <div class="sb-item">
    <div class="sb-label">Precio vs mercado</div>
    <div class="sb-val" style="color:{sc_color}">{pts_p}</div>
    <div class="sb-max">de 40 pts</div>
  </div>
  <div class="sb-item">
    <div class="sb-label">Rentabilidad</div>
    <div class="sb-val" style="color:{sc_color}">{pts_c}</div>
    <div class="sb-max">de 35 pts</div>
  </div>
  <div class="sb-item">
    <div class="sb-label">Riesgo entrega</div>
    <div class="sb-val" style="color:{sc_color}">{pts_e}</div>
    <div class="sb-max">de 25 pts</div>
  </div>
</div>
""", unsafe_allow_html=True)

            # ALERTA CONTEXTUAL
            if desv > 0.15:
                diferencial = precio - bm["p_avg"] * area
                st.markdown(f"""
<div class="alerta" style="background:var(--red-bg);border:1px solid var(--red)">
  <div class="alerta-title" style="color:var(--red)">Precio {desv*100:.0f}% sobre el promedio de {zona}</div>
  <div class="alerta-body" style="color:var(--red)">
    Estás pagando {fmt(diferencial)} por encima del valor de mercado estimado ({fmt(bm['p_avg']*area)}).
    Verifica si el diferencial se justifica por acabados, vista o amenidades.
  </div>
</div>
""", unsafe_allow_html=True)
            elif cap_real < bm["cap_ref"] * 0.80:
                st.markdown(f"""
<div class="alerta" style="background:var(--amber-bg);border:1px solid var(--amber)">
  <div class="alerta-title" style="color:var(--amber)">Cap rate por debajo de la referencia de zona</div>
  <div class="alerta-body" style="color:var(--amber)">
    La rentabilidad esperada ({fmtp(cap_real)}) está {((bm['cap_ref']-cap_real)/bm['cap_ref']*100):.0f}% por debajo
    de la referencia de {zona} ({fmtp(bm['cap_ref'])}). Considera negociar el precio o el canon.
  </div>
</div>
""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div class="alerta" style="background:var(--green-bg);border:1px solid var(--green)">
  <div class="alerta-title" style="color:var(--green)">Indicadores dentro del rango esperado para {zona}</div>
  <div class="alerta-body" style="color:var(--green)">
    El precio/m² y cap rate son consistentes con el mercado. Avanza al análisis fiscal para optimizar la estructura.
  </div>
</div>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — PORTAFOLIO
    # ══════════════════════════════════════════════════════════════
    with tab_portafolio:
        if not st.session_state.portafolio:
            st.markdown("""
<div style="text-align:center;padding:3rem 1rem">
  <div style="font-family:'Instrument Serif',serif;font-size:1.5rem;color:var(--ink);margin-bottom:0.5rem">
    Tu portafolio está vacío
  </div>
  <div style="font-size:12px;color:var(--ink3);font-family:'Geist Mono',monospace;line-height:1.7">
    Analiza un inmueble en la pestaña anterior y agrégalo aquí.<br>
    Puedes comparar varios proyectos lado a lado.
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            # Resumen agregado
            total_inversion = sum(p["precio"] for p in st.session_state.portafolio)
            renta_total = sum(p["canon"] for p in st.session_state.portafolio) * 12
            cap_promedio = renta_total / total_inversion if total_inversion > 0 else 0
            score_promedio = sum(p["score"] for p in st.session_state.portafolio) / len(st.session_state.portafolio)

            st.markdown(f"""
<div class="ind-grid" style="margin-bottom:1.5rem">
  <div class="ind-cell">
    <div class="ind-label">Inversión total</div>
    <div class="ind-value">{fmt(total_inversion)}</div>
    <div class="ind-sub">{len(st.session_state.portafolio)} inmuebles</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">Renta anual estimada</div>
    <div class="ind-value">{fmt(renta_total)}</div>
    <div class="ind-sub">{fmt(renta_total/12)}/mes</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">Score promedio</div>
    <div class="ind-value" style="color:{score_color(score_promedio)[0]}">{score_promedio:.0f}</div>
    <div class="ind-sub">Cap rate: {fmtp(cap_promedio)}</div>
  </div>
</div>
""", unsafe_allow_html=True)

            for i, p in enumerate(st.session_state.portafolio):
                sc_col, sc_bg, _ = score_color(p["score"])
                col_card, col_del = st.columns([10, 1])
                with col_card:
                    st.markdown(f"""
<div class="prop-card">
  <div>
    <div class="prop-name">{p['nombre']}</div>
    <div class="prop-meta">{p['ciudad']} · {p['zona']} · {p['area']:.0f} m² · {fmt(p['precio'])}</div>
    <div class="prop-meta" style="margin-top:4px">
      Cap rate {fmtp(p['cap'])} · Precio/m² {fmt(p['pm2'])} · Canon {fmt(p['canon'])}/mes
    </div>
  </div>
  <div class="prop-score-dot" style="background:{sc_bg};color:{sc_col}">{p['score']}</div>
</div>
""", unsafe_allow_html=True)
                with col_del:
                    if st.button("✕", key=f"del_{i}"):
                        st.session_state.portafolio.pop(i)
                        st.rerun()

            if not st.session_state.pro:
                st.markdown("""
<div class="paywall">
  <h3>Exportar reporte del portafolio</h3>
  <p>Descarga un PDF con el análisis completo de todos tus inmuebles,<br>
  incluyendo benchmarks, scores y recomendaciones de estructuración.</p>
</div>
""", unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns([1,2,1])
                with col_b:
                    if st.button("Desbloquear Pro — $29 USD/mes", key="btn_pro_port"):
                        st.session_state.pro = True
                        st.success("Modo Pro activado (demo).")

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — FISCAL
    # ══════════════════════════════════════════════════════════════
    with tab_fiscal:
        col_fi, col_fr = st.columns([1, 1.3], gap="large")

        with col_fi:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-eyebrow">Parámetros</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">¿Cómo estructuras la compra?</div>', unsafe_allow_html=True)

            f_valor = st.number_input("Valor del inmueble", min_value=50_000_000,
                                       max_value=5_000_000_000, value=451_000_000,
                                       step=5_000_000, key="f_val")
            f_canon = st.number_input("Canon mensual COP", min_value=300_000,
                                       max_value=20_000_000, value=1_950_000,
                                       step=50_000, key="f_can")
            f_ingresos = st.number_input("Tus ingresos anuales PN (salario/honorarios)",
                                          min_value=0, max_value=1_000_000_000,
                                          value=120_000_000, step=5_000_000, key="f_ing",
                                          help="Necesario para calcular cuánto pagas de impuesto marginal como persona natural")
            f_fin = st.slider("% financiado con hipoteca", 0, 80, 50, 5, key="f_fin")
            f_tasa = st.slider("Tasa hipotecaria anual %", 8.0, 20.0, 14.5, 0.5, key="f_tasa")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_fr:
            if not st.session_state.pro:
                # Mostrar resultado PN gratis, SAS bloqueado
                r = fiscal_engine(f_valor, f_canon, f_fin/100, f_tasa/100, f_ingresos)

                st.markdown(f"""
<div class="panel">
  <div class="panel-eyebrow">Como Persona Natural</div>
  <div class="panel-title">Ingreso neto estimado</div>
  <table class="fiscal-table">
    <tr><td>Renta bruta anual</td><td class="hi">{fmt_full(r['renta_anual'])}</td></tr>
    <tr><td>Costos presuntos (30%)</td><td class="neg">({fmt_full(r['costos_pn'])})</td></tr>
    <tr><td>Intereses hipoteca</td><td class="neg">({fmt_full(r['intereses'])})</td></tr>
    <tr><td>Impuesto renta marginal</td><td class="neg">({fmt_full(r['imp_pn'])})</td></tr>
    <tr class="total"><td>Ingreso neto real / año</td><td class="hi">{fmt_full(r['neto_pn'])}</td></tr>
    <tr><td>Cap rate neto</td><td>{fmtp(r['cap_pn'])}</td></tr>
    <tr><td>Tasa efectiva</td><td>{fmtp(r['tasa_pn'])}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

                st.markdown(f"""
<div class="paywall">
  <h3>¿Cuánto ahorras estructurando como SAS?</h3>
  <p>
    La depreciación lineal de 45 años, el ICA deducible y la diferencia en<br>
    impuesto de dividendos pueden generarte un ahorro significativo.<br>
    Desbloquea Pro para ver la comparativa completa y el número exacto.
  </p>
</div>
""", unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns([1,2,1])
                with col_b:
                    if st.button("Ver análisis SAS completo →", key="btn_pro_fisc"):
                        st.session_state.pro = True
                        st.rerun()

            else:
                r = fiscal_engine(f_valor, f_canon, f_fin/100, f_tasa/100, f_ingresos)
                ganador_color = "var(--green)" if r["ganador"] == "SAS" else "var(--blue)"

                st.markdown(f"""
<div class="ind-grid" style="margin-bottom:1.25rem">
  <div class="ind-cell">
    <div class="ind-label">Cap rate neto PN</div>
    <div class="ind-value">{fmtp(r['cap_pn'])}</div>
    <div class="ind-sub">Tasa ef. {fmtp(r['tasa_pn'])}</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">Cap rate neto SAS</div>
    <div class="ind-value" style="color:var(--green)">{fmtp(r['cap_sas'])}</div>
    <div class="ind-sub">Tasa ef. {fmtp(r['tasa_sas'])}</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">Ahorro anual vía {r['ganador']}</div>
    <div class="ind-value" style="color:{ganador_color}">{fmt(abs(r['ahorro']))}</div>
    <div class="ind-sub">{fmt(abs(r['ahorro_10']))} en 10 años</div>
  </div>
</div>
""", unsafe_allow_html=True)

                col_pn, col_sas = st.columns(2, gap="medium")
                with col_pn:
                    st.markdown(f"""
<div class="panel">
  <div class="panel-eyebrow">Persona Natural</div>
  <table class="fiscal-table">
    <tr><th>Concepto</th><th>Valor</th></tr>
    <tr><td>Renta bruta</td><td>{fmt_full(r['renta_anual'])}</td></tr>
    <tr><td>Costos (30%)</td><td class="neg">({fmt_full(r['costos_pn'])})</td></tr>
    <tr><td>Intereses</td><td class="neg">({fmt_full(r['intereses'])})</td></tr>
    <tr><td>Impuesto marginal</td><td class="neg">({fmt_full(r['imp_pn'])})</td></tr>
    <tr class="total"><td>Neto real</td><td class="hi">{fmt_full(r['neto_pn'])}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

                with col_sas:
                    st.markdown(f"""
<div class="panel">
  <div class="panel-eyebrow">SAS · Persona Jurídica</div>
  <table class="fiscal-table">
    <tr><th>Concepto</th><th>Valor</th></tr>
    <tr><td>Renta bruta</td><td>{fmt_full(r['renta_anual'])}</td></tr>
    <tr><td>Depreciación 45a</td><td class="pos">({fmt_full(r['depreciacion'])})</td></tr>
    <tr><td>Admin + ICA</td><td class="neg">({fmt_full(r['costos_sas'])})</td></tr>
    <tr><td>Intereses</td><td class="neg">({fmt_full(r['intereses'])})</td></tr>
    <tr><td>Imporrenta 35%</td><td class="neg">({fmt_full(r['imp_sas'])})</td></tr>
    <tr><td>Imp. dividendos</td><td class="neg">({fmt_full(r['imp_div'])})</td></tr>
    <tr class="total"><td>Neto real</td><td class="hi pos">{fmt_full(r['neto_sas'])}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 4 — SALIDA
    # ══════════════════════════════════════════════════════════════
    with tab_salida:
        if not st.session_state.pro:
            st.markdown("""
<div style="padding:2rem 0">
  <div class="paywall">
    <h3>Proyecta tu estrategia de salida</h3>
    <p>
      Calcula la utilidad neta al vender, comparando Persona Natural (15% GO)<br>
      vs SAS (10% GO), con ajuste de costo fiscal por inflación IGAC.<br>
      Disponible en el plan Pro.
    </p>
  </div>
</div>
""", unsafe_allow_html=True)
            col_a, col_b, col_c = st.columns([1,2,1])
            with col_b:
                if st.button("Activar Pro →", key="btn_pro_sal"):
                    st.session_state.pro = True
                    st.rerun()
        else:
            col_si, col_sr = st.columns([1, 1.2], gap="large")

            with col_si:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-eyebrow">Proyección</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">¿Cuándo y cómo vendes?</div>', unsafe_allow_html=True)

                s_compra = st.number_input("Precio de compra", min_value=50_000_000,
                                            max_value=5_000_000_000, value=451_000_000,
                                            step=5_000_000, key="s_comp")
                s_val = st.slider("Valorización anual estimada %", 2.0, 15.0, 7.0, 0.5, key="s_val")
                s_anos = st.slider("Años de tenencia", 1, 25, 10, 1, key="s_anos")
                s_tipo = st.radio("Vehículo de venta", ["Persona Natural (GO 15%)", "SAS (GO 10%)"], key="s_tipo")
                es_pj = "SAS" in s_tipo
                st.markdown('</div>', unsafe_allow_html=True)

            with col_sr:
                sr = salida_engine(s_compra, s_val/100, s_anos, es_pj)
                sr_alt = salida_engine(s_compra, s_val/100, s_anos, not es_pj)
                ventaja = sr["utilidad_neta"] - sr_alt["utilidad_neta"]

                st.markdown(f"""
<div class="ind-grid" style="margin-bottom:1.25rem">
  <div class="ind-cell">
    <div class="ind-label">Valor de venta</div>
    <div class="ind-value">{fmt(sr['valor_venta'])}</div>
    <div class="ind-sub">en {s_anos} años</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">Utilidad neta</div>
    <div class="ind-value" style="color:var(--green)">{fmt(sr['utilidad_neta'])}</div>
    <div class="ind-sub">ROI total {fmtp(sr['roi_total'])}</div>
  </div>
  <div class="ind-cell">
    <div class="ind-label">ROI anual</div>
    <div class="ind-value">{fmtp(sr['roi_anual'])}</div>
    <div class="ind-sub">Impuesto GO {fmt(sr['imp_go'])}</div>
  </div>
</div>
""", unsafe_allow_html=True)

                st.markdown(f"""
<div class="panel">
  <div class="panel-eyebrow">Waterfall de salida</div>
  <div class="wf-row"><span class="wf-label">Precio de venta</span><span class="wf-val">{fmt_full(sr['valor_venta'])}</span></div>
  <div class="wf-row"><span class="wf-label">(−) Costo fiscal ajustado por IGAC</span><span class="wf-val" style="color:var(--red)">({fmt_full(sr['costo_fiscal'])})</span></div>
  <div class="wf-row"><span class="wf-label">= Ganancia Ocasional gravable</span><span class="wf-val">{fmt_full(sr['go'])}</span></div>
  <div class="wf-row"><span class="wf-label">(−) Impuesto GO ({fmtp(sr['tarifa'])})</span><span class="wf-val" style="color:var(--red)">({fmt_full(sr['imp_go'])})</span></div>
  <div class="wf-row"><span class="wf-label">(−) Precio de compra original</span><span class="wf-val" style="color:var(--red)">({fmt_full(s_compra)})</span></div>
  <div class="wf-row" style="border-top:1px solid var(--ink);padding-top:0.75rem"><span class="wf-label" style="color:var(--ink);font-weight:500">Utilidad neta final</span><span class="wf-val" style="color:var(--green);font-size:15px">{fmt_full(sr['utilidad_neta'])}</span></div>
</div>
""", unsafe_allow_html=True)

                if abs(ventaja) > 500_000:
                    label_mejor = "SAS" if ventaja > 0 else "Persona Natural"
                    st.markdown(f"""
<div class="alerta" style="background:var(--green-bg);border:1px solid var(--green)">
  <div class="alerta-title" style="color:var(--green)">Vender vía {label_mejor} te ahorra {fmt(abs(ventaja))} en impuestos</div>
  <div class="alerta-body" style="color:var(--green)">
    La diferencia de tarifa de Ganancia Ocasional (15% PN vs 10% SAS)
    representa {fmt(abs(ventaja))} adicionales en tu bolsillo al momento de vender.
  </div>
</div>
""", unsafe_allow_html=True)

    # FOOTER
    st.markdown(f"""
<div style="text-align:center;padding:2.5rem 0 1rem;margin-top:2rem;border-top:1px solid var(--surface2)">
  <div style="font-family:'Geist Mono',monospace;font-size:11px;color:var(--ink3);letter-spacing:0.08em">
    inverso · inteligencia inmobiliaria · colombia · {datetime.now().year}<br>
    <span style="opacity:0.6">los benchmarks son estimaciones de mercado. no constituyen asesoría profesional.</span>
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
