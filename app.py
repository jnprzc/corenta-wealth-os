"""
Corenta Wealth OS — MVP v1.0
Motor de Inteligencia Patrimonial Inmobiliaria para Colombia
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import math

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Corenta Wealth OS",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── BENCHMARK DATA ─────────────────────────────────────────────────────────────
BENCHMARK_DB = {
    "Barranquilla": {
        "El Poblado / Villa Campestre": {
            "precio_m2_min": 5_800_000,
            "precio_m2_max": 9_500_000,
            "precio_m2_avg": 7_200_000,
            "renta_m2_min": 28_000,
            "renta_m2_max": 48_000,
            "renta_m2_avg": 37_000,
            "cap_rate_ref": 0.062,
            "notas": "Zona premium residencial. Alta demanda ejecutiva.",
        },
        "Puerto Colombia / Pradomar": {
            "precio_m2_min": 4_200_000,
            "precio_m2_max": 7_800_000,
            "precio_m2_avg": 5_800_000,
            "renta_m2_min": 22_000,
            "renta_m2_max": 38_000,
            "renta_m2_avg": 29_000,
            "cap_rate_ref": 0.058,
            "notas": "Costa norte. Perfil turístico y segunda vivienda.",
        },
        "Riomar / Alto Prado": {
            "precio_m2_min": 6_500_000,
            "precio_m2_max": 11_000_000,
            "precio_m2_avg": 8_400_000,
            "renta_m2_min": 32_000,
            "renta_m2_max": 55_000,
            "renta_m2_avg": 42_000,
            "cap_rate_ref": 0.058,
            "notas": "Estrato 6 consolidado. Máxima valorización histórica.",
        },
        "Buenavista / Villa Santos": {
            "precio_m2_min": 3_800_000,
            "precio_m2_max": 6_200_000,
            "precio_m2_avg": 4_900_000,
            "renta_m2_min": 19_000,
            "renta_m2_max": 31_000,
            "renta_m2_avg": 24_500,
            "cap_rate_ref": 0.060,
            "notas": "Zona comercial-residencial mixta. Buena liquidez.",
        },
        "Ciudad Jardín / Las Delicias": {
            "precio_m2_min": 2_800_000,
            "precio_m2_max": 4_500_000,
            "precio_m2_avg": 3_500_000,
            "renta_m2_min": 14_000,
            "renta_m2_max": 22_000,
            "renta_m2_avg": 17_500,
            "cap_rate_ref": 0.060,
            "notas": "Zona media-alta en consolidación. Potencial de valorización.",
        },
    },
    "Bogotá": {
        "Chico / Rosales": {
            "precio_m2_min": 9_500_000,
            "precio_m2_max": 16_000_000,
            "precio_m2_avg": 12_200_000,
            "renta_m2_min": 42_000,
            "renta_m2_max": 72_000,
            "renta_m2_avg": 56_000,
            "cap_rate_ref": 0.055,
            "notas": "Top tier Bogotá. Máxima plusvalía y renta corporativa.",
        },
        "Cedritos / Santa Bárbara": {
            "precio_m2_min": 5_500_000,
            "precio_m2_max": 9_200_000,
            "precio_m2_avg": 7_100_000,
            "renta_m2_min": 28_000,
            "renta_m2_max": 45_000,
            "renta_m2_avg": 35_000,
            "cap_rate_ref": 0.059,
            "notas": "Zona norte consolidada. Perfil profesional y familiar.",
        },
    },
    "Medellín": {
        "El Poblado / Laureles": {
            "precio_m2_min": 6_800_000,
            "precio_m2_max": 13_500_000,
            "precio_m2_avg": 9_800_000,
            "renta_m2_min": 38_000,
            "renta_m2_max": 78_000,
            "renta_m2_avg": 55_000,
            "cap_rate_ref": 0.067,
            "notas": "Alta demanda Airbnb y ejecutiva. Mejor yield del país.",
        },
        "Envigado / Sabaneta": {
            "precio_m2_min": 4_200_000,
            "precio_m2_max": 7_800_000,
            "precio_m2_avg": 5_900_000,
            "renta_m2_min": 24_000,
            "renta_m2_max": 42_000,
            "renta_m2_avg": 32_000,
            "cap_rate_ref": 0.065,
            "notas": "Municipios satélite premium. Alta valorización proyectada.",
        },
    },
}

# ── FISCAL CONSTANTS (Colombia 2024-2025) ─────────────────────────────────────
FISCAL = {
    # Persona Natural
    "pn": {
        "rentas_capital_tarifa": 0.10,        # Rentas de capital (15% de renta pasiva, simplificado)
        "ganancia_ocasional": 0.15,            # Venta de inmueble
        "imporrenta_rango": [                  # Rangos simplificados tabla Art 241 ET
            (0, 38_004_000, 0.0),
            (38_004_000, 73_008_000, 0.19),
            (73_008_000, 115_200_000, 0.28),
            (115_200_000, 173_004_000, 0.33),
            (173_004_000, float('inf'), 0.39),
        ],
        "predial_deducible": True,
        "intereses_deducibles": True,
        "deduccion_costos_arrendamiento_pct": 0.30,  # 30% presunción costos
    },
    # Persona Jurídica (SAS)
    "pj": {
        "imporrenta_tarifa": 0.35,             # Renta ordinaria 2024
        "ganancia_ocasional": 0.10,            # 10% GO para PJ
        "depreciacion_anos": 45,               # Depreciación lineal inmuebles
        "depreciacion_tasa": 1 / 45,
        "intereses_deducibles": True,
        "costos_admin_deducibles": True,
        "ica_tasa": 0.005,                     # ICA Barranquilla aprox
        "industria_comercio": True,
    },
}

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

    :root {
        --gold: #C9A84C;
        --gold-dim: #8B6E2E;
        --obsidian: #080B0F;
        --surface: #0D1117;
        --surface-2: #141B24;
        --surface-3: #1C2633;
        --border: rgba(201,168,76,0.18);
        --border-subtle: rgba(255,255,255,0.06);
        --text-primary: #F0EDE6;
        --text-secondary: #8A9BB0;
        --text-muted: #4A5568;
        --danger: #E05C5C;
        --success: #4CAF82;
        --info: #5B9BD5;
        --radius: 10px;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--obsidian) !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stAppViewContainer"] > .main {
        background: var(--obsidian) !important;
    }

    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }

    .block-container {
        padding: 2rem 3rem !important;
        max-width: 1400px !important;
    }

    /* Typography */
    h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; color: var(--text-primary) !important; }
    p, label, span, div { font-family: 'DM Mono', monospace !important; }

    /* Header */
    .wealth-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem 2rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .wealth-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }
    .wealth-logo {
        font-family: 'Syne', sans-serif !important;
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--gold) !important;
        letter-spacing: -0.02em;
    }
    .wealth-tagline {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.7rem;
        color: var(--text-secondary);
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .wealth-badge {
        background: rgba(201,168,76,0.10);
        border: 1px solid var(--border);
        color: var(--gold);
        font-family: 'DM Mono', monospace !important;
        font-size: 0.65rem;
        letter-spacing: 0.1em;
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        text-transform: uppercase;
    }

    /* Metric Cards */
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }
    .metric-card {
        background: var(--surface-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
        padding: 1.25rem 1.5rem;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s;
    }
    .metric-card:hover { border-color: var(--border); }
    .metric-card::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 2px;
        background: var(--accent-color, transparent);
    }
    .metric-label {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.65rem;
        color: var(--text-muted);
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-family: 'Syne', sans-serif !important;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .metric-sub {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.7rem;
        color: var(--text-secondary);
        margin-top: 0.25rem;
    }

    /* Section panels */
    .panel {
        background: var(--surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .panel-title {
        font-family: 'Syne', sans-serif !important;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--gold);
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .panel-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border-subtle);
    }

    /* Alert boxes */
    .alert-danger {
        background: rgba(224,92,92,0.08);
        border: 1px solid rgba(224,92,92,0.3);
        border-left: 3px solid var(--danger);
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
        margin: 1rem 0;
    }
    .alert-success {
        background: rgba(76,175,130,0.08);
        border: 1px solid rgba(76,175,130,0.3);
        border-left: 3px solid var(--success);
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
        margin: 1rem 0;
    }
    .alert-warning {
        background: rgba(201,168,76,0.08);
        border: 1px solid rgba(201,168,76,0.25);
        border-left: 3px solid var(--gold);
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
        margin: 1rem 0;
    }
    .alert-title {
        font-family: 'Syne', sans-serif !important;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .alert-body {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.75rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }

    /* Comparison table */
    .compare-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.78rem;
    }
    .compare-table th {
        background: var(--surface-3);
        color: var(--gold);
        font-family: 'Syne', sans-serif !important;
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--border);
        text-align: left;
    }
    .compare-table td {
        padding: 0.65rem 1rem;
        border-bottom: 1px solid var(--border-subtle);
        color: var(--text-secondary);
        vertical-align: top;
    }
    .compare-table tr:last-child td { border-bottom: none; }
    .compare-table tr:hover td { background: rgba(255,255,255,0.02); }
    .td-label { color: var(--text-muted) !important; font-size: 0.68rem !important; }
    .td-pn { color: var(--info) !important; }
    .td-pj { color: var(--success) !important; }
    .td-winner { color: var(--gold) !important; font-weight: 600 !important; }

    /* Benchmark gauge */
    .gauge-container {
        background: var(--surface-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius);
        padding: 1.25rem;
        margin: 0.5rem 0;
    }
    .gauge-bar-bg {
        background: var(--surface-3);
        border-radius: 4px;
        height: 8px;
        position: relative;
        margin: 0.75rem 0;
        overflow: visible;
    }
    .gauge-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    .gauge-label {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* CTA Button */
    .stButton > button {
        background: linear-gradient(135deg, var(--gold), var(--gold-dim)) !important;
        color: var(--obsidian) !important;
        border: none !important;
        border-radius: var(--radius) !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.05em !important;
        padding: 0.75rem 2rem !important;
        width: 100% !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }

    /* Streamlit overrides */
    .stSelectbox > div > div { background: var(--surface-2) !important; border-color: var(--border-subtle) !important; color: var(--text-primary) !important; }
    .stNumberInput > div > div > input { background: var(--surface-2) !important; border-color: var(--border-subtle) !important; color: var(--text-primary) !important; }
    .stSlider > div > div > div { background: var(--gold) !important; }
    label[data-testid="stWidgetLabel"] { color: var(--text-secondary) !important; font-family: 'DM Mono', monospace !important; font-size: 0.72rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; }
    [data-testid="stTab"] { background: transparent !important; }
    [data-testid="stTabsTabList"] { border-bottom: 1px solid var(--border-subtle) !important; }
    button[data-testid="stTab"] { color: var(--text-muted) !important; font-family: 'Syne', sans-serif !important; }
    button[data-testid="stTab"][aria-selected="true"] { color: var(--gold) !important; border-bottom: 2px solid var(--gold) !important; }
    [data-testid="stExpander"] { border-color: var(--border-subtle) !important; background: var(--surface) !important; }
    .stMarkdown hr { border-color: var(--border-subtle) !important; }
    [data-testid="column"] { padding: 0 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def fmt_cop(value: float) -> str:
    """Format as COP with M/K shorthand."""
    if abs(value) >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}MM"
    elif abs(value) >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"${value/1_000:.0f}K"
    return f"${value:,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value*100:.2f}%"


def calc_pn_impuesto(renta_liquida: float) -> float:
    """Calcula impuesto PN usando tabla Art 241 ET."""
    impuesto = 0.0
    rangos = FISCAL["pn"]["imporrenta_rango"]
    for i, (lim_inf, lim_sup, tarifa) in enumerate(rangos):
        if renta_liquida <= lim_inf:
            break
        base = min(renta_liquida, lim_sup) - lim_inf
        impuesto += base * tarifa
    return impuesto


def analyze_sobreprecio(precio_m2_usuario: float, benchmark_zona: dict) -> dict:
    avg = benchmark_zona["precio_m2_avg"]
    desviacion = (precio_m2_usuario - avg) / avg
    return {
        "desviacion": desviacion,
        "es_sobreprecio": desviacion > 0.15,
        "es_oportunidad": desviacion < -0.10,
        "avg": avg,
        "min": benchmark_zona["precio_m2_min"],
        "max": benchmark_zona["precio_m2_max"],
    }


def calcular_escudo_fiscal(
    valor_inmueble: float,
    canon_mensual: float,
    financiacion_pct: float,
    tasa_hipoteca: float,
    ingresos_anuales_pn: float,
) -> dict:
    """Motor fiscal completo PN vs SAS."""
    renta_bruta_anual = canon_mensual * 12
    valor_deuda = valor_inmueble * financiacion_pct
    intereses_anuales = valor_deuda * tasa_hipoteca

    # ── PERSONA NATURAL ──────────────────────────────────────────────────────
    costos_pn = renta_bruta_anual * FISCAL["pn"]["deduccion_costos_arrendamiento_pct"]
    renta_neta_pn = renta_bruta_anual - costos_pn - intereses_anuales
    renta_total_pn = ingresos_anuales_pn + renta_neta_pn
    impuesto_pn = calc_pn_impuesto(renta_total_pn)
    impuesto_solo_pn = calc_pn_impuesto(ingresos_anuales_pn)
    impuesto_incremental_pn = impuesto_pn - impuesto_solo_pn
    ingreso_neto_pn = renta_neta_pn - impuesto_incremental_pn

    # ── PERSONA JURÍDICA (SAS) ────────────────────────────────────────────────
    depreciacion_anual = valor_inmueble * FISCAL["pj"]["depreciacion_tasa"]
    costos_admin_pj = renta_bruta_anual * 0.12  # Administración, seguros, mant.
    ica_pj = renta_bruta_anual * FISCAL["pj"]["ica_tasa"]
    renta_neta_pj = renta_bruta_anual - costos_admin_pj - intereses_anuales - depreciacion_anual - ica_pj
    renta_neta_pj = max(renta_neta_pj, 0)  # Floor en 0
    impuesto_pj = renta_neta_pj * FISCAL["pj"]["imporrenta_tarifa"]
    dividendos_brutos = renta_neta_pj - impuesto_pj
    # Impuesto dividendos (tarifa 15% sobre el exceso de UVT)
    impuesto_dividendos = dividendos_brutos * 0.10
    ingreso_neto_pj = dividendos_brutos - impuesto_dividendos

    ahorro_fiscal = ingreso_neto_pj - ingreso_neto_pn
    tasa_efectiva_pn = impuesto_incremental_pn / max(renta_neta_pn, 1)
    tasa_efectiva_pj = (impuesto_pj + impuesto_dividendos) / max(renta_bruta_anual - costos_admin_pj - ica_pj, 1)

    cap_rate_pn = ingreso_neto_pn / valor_inmueble
    cap_rate_pj = ingreso_neto_pj / valor_inmueble

    return {
        # PN
        "renta_bruta": renta_bruta_anual,
        "costos_pn": costos_pn,
        "intereses": intereses_anuales,
        "renta_neta_pn": renta_neta_pn,
        "impuesto_incremental_pn": impuesto_incremental_pn,
        "ingreso_neto_pn": ingreso_neto_pn,
        "tasa_efectiva_pn": tasa_efectiva_pn,
        "cap_rate_pn": cap_rate_pn,
        # PJ
        "depreciacion": depreciacion_anual,
        "costos_admin_pj": costos_admin_pj,
        "ica_pj": ica_pj,
        "renta_neta_pj": renta_neta_pj,
        "impuesto_pj": impuesto_pj,
        "dividendos_brutos": dividendos_brutos,
        "impuesto_dividendos": impuesto_dividendos,
        "ingreso_neto_pj": ingreso_neto_pj,
        "tasa_efectiva_pj": tasa_efectiva_pj,
        "cap_rate_pj": cap_rate_pj,
        # Delta
        "ahorro_fiscal_anual": ahorro_fiscal,
        "ahorro_10_anos": ahorro_fiscal * 10,
        "ganador": "SAS" if ahorro_fiscal > 0 else "PN",
    }


def calcular_go_salida(
    valor_compra: float,
    valor_venta: float,
    anos_tenencia: int,
    es_pj: bool,
) -> dict:
    """Ganancia Ocasional al vender."""
    # Ajuste por inflación (IGAC) — simplificado 4% anual
    costo_fiscal = valor_compra * ((1.04) ** anos_tenencia)
    go_bruta = max(valor_venta - costo_fiscal, 0)
    tarifa = FISCAL["pj"]["ganancia_ocasional"] if es_pj else FISCAL["pn"]["ganancia_ocasional"]
    impuesto_go = go_bruta * tarifa
    utilidad_neta = (valor_venta - valor_compra) - impuesto_go
    return {
        "go_bruta": go_bruta,
        "costo_fiscal_ajustado": costo_fiscal,
        "tarifa": tarifa,
        "impuesto_go": impuesto_go,
        "utilidad_neta": utilidad_neta,
        "roi": (utilidad_neta / valor_compra) if valor_compra > 0 else 0,
    }


def generar_reporte_texto(proyecto, zona, benchmark, inputs, fiscal_result, go_result_pj) -> str:
    """Genera el contenido del reporte de due diligence en texto plano."""
    hoy = datetime.now().strftime("%d de %B de %Y")
    reporte = f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║         CORENTA WEALTH OS — REPORTE DE DUE DILIGENCE INMOBILIARIO             ║
╚══════════════════════════════════════════════════════════════════════════════════╝

Generado el: {hoy}
Proyecto: {proyecto}
Zona: {zona}

════════════════════════════════════════════════════
  1. INTELIGENCIA DE MERCADO — BENCHMARKING
════════════════════════════════════════════════════

  Precio/m² Ingresado:     {fmt_cop(inputs['precio_m2'])}
  Precio/m² Promedio Zona: {fmt_cop(benchmark['precio_m2_avg'])}
  Desviación vs Mercado:   {(inputs['precio_m2']/benchmark['precio_m2_avg']-1)*100:.1f}%

  Renta/m² Esperada Zona:  {fmt_cop(benchmark['renta_m2_avg'])}/mes
  Cap Rate Referencia:     {benchmark['cap_rate_ref']*100:.2f}%

  NOTA: {benchmark['notas']}

════════════════════════════════════════════════════
  2. ESCUDO FISCAL — PN vs SAS
════════════════════════════════════════════════════

  Valor Inmueble:          {fmt_cop(inputs['valor_inmueble'])}
  Canon Mensual:           {fmt_cop(inputs['canon_mensual'])}
  Renta Bruta Anual:       {fmt_cop(fiscal_result['renta_bruta'])}

  ── Persona Natural ──
  Costos Presuntos (30%):  {fmt_cop(fiscal_result['costos_pn'])}
  Intereses Deducibles:    {fmt_cop(fiscal_result['intereses'])}
  Renta Neta Gravable:     {fmt_cop(fiscal_result['renta_neta_pn'])}
  Impuesto Incremental:    {fmt_cop(fiscal_result['impuesto_incremental_pn'])}
  Tasa Efectiva:           {fmt_pct(fiscal_result['tasa_efectiva_pn'])}
  Ingreso Neto Real:       {fmt_cop(fiscal_result['ingreso_neto_pn'])}
  Cap Rate Neto PN:        {fmt_pct(fiscal_result['cap_rate_pn'])}

  ── SAS (Persona Jurídica) ──
  Depreciación Anual (45a):{fmt_cop(fiscal_result['depreciacion'])}
  Costos Admin + ICA:      {fmt_cop(fiscal_result['costos_admin_pj'] + fiscal_result['ica_pj'])}
  Intereses Deducibles:    {fmt_cop(fiscal_result['intereses'])}
  Renta Neta Gravable:     {fmt_cop(fiscal_result['renta_neta_pj'])}
  Imporrenta (35%):        {fmt_cop(fiscal_result['impuesto_pj'])}
  Impuesto Dividendos:     {fmt_cop(fiscal_result['impuesto_dividendos'])}
  Tasa Efectiva Total:     {fmt_pct(fiscal_result['tasa_efectiva_pj'])}
  Ingreso Neto Real:       {fmt_cop(fiscal_result['ingreso_neto_pj'])}
  Cap Rate Neto SAS:       {fmt_pct(fiscal_result['cap_rate_pj'])}

  ── RESULTADO ──
  Ahorro Fiscal Anual:     {fmt_cop(fiscal_result['ahorro_fiscal_anual'])}
  Ahorro Proyectado 10a:   {fmt_cop(fiscal_result['ahorro_10_anos'])}
  Vehículo Recomendado:    {fiscal_result['ganador']}

════════════════════════════════════════════════════
  3. ESTRATEGIA DE SALIDA (Venta vía SAS)
════════════════════════════════════════════════════

  Ganancia Ocasional Bruta:{fmt_cop(go_result_pj['go_bruta'])}
  Costo Fiscal Ajustado:   {fmt_cop(go_result_pj['costo_fiscal_ajustado'])}
  Tarifa GO (PJ 10%):      {fmt_pct(go_result_pj['tarifa'])}
  Impuesto GO:             {fmt_cop(go_result_pj['impuesto_go'])}
  Utilidad Neta:           {fmt_cop(go_result_pj['utilidad_neta'])}
  ROI Total:               {fmt_pct(go_result_pj['roi'])}

════════════════════════════════════════════════════
  PRÓXIMOS PASOS — CORENTA S.A.S.
════════════════════════════════════════════════════

  Este reporte identifica una oportunidad de optimización fiscal significativa.
  Para estructurar correctamente su inversión, Corenta ofrece:

  ✓ Constitución de SAS inmobiliaria (objeto social adecuado)
  ✓ Contabilidad y declaraciones (renta, IVA, ICA)
  ✓ Planeación tributaria anual y auditoría de contratos
  ✓ Acompañamiento en due diligence jurídico y fiduciario

  Contacto: jcperez@corenta.co | www.corenta.co
  NIT: [CORENTA S.A.S. — Barranquilla, Colombia]

════════════════════════════════════════════════════
  DISCLAIMER LEGAL
════════════════════════════════════════════════════

  Este reporte es informativo y no constituye asesoría tributaria formal.
  Las cifras se basan en la normativa colombiana vigente (ET, Ley 2277/2022).
  Corenta S.A.S. no se responsabiliza por decisiones tomadas sin consulta
  profesional individualizada.

═══════════════════════════════════════════════════════════════════════
  © {datetime.now().year} Corenta S.A.S. — Sistema Operativo del Inversionista Inmobiliario
═══════════════════════════════════════════════════════════════════════
"""
    return reporte


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()

    # ── HEADER ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="wealth-header">
        <div>
            <div class="wealth-logo">◈ CORENTA WEALTH OS</div>
            <div class="wealth-tagline">Sistema Operativo del Inversionista Inmobiliario · Colombia</div>
        </div>
        <div class="wealth-badge">MVP v1.0 · Due Diligence Engine</div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABS ───────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "◈  Análisis de Proyecto",
        "⚖  Escudo Fiscal PN vs SAS",
        "📊  Estrategia de Salida"
    ])

    # ═══════════════════════════════════════════════════════════════
    # TAB 1: INTELIGENCIA DE MERCADO
    # ═══════════════════════════════════════════════════════════════
    with tab1:
        col_input, col_result = st.columns([1, 1.3], gap="large")

        with col_input:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">01 · Datos del Proyecto</div>', unsafe_allow_html=True)

            proyecto_nombre = st.text_input("Nombre del Proyecto", value="Moretti by Colpatria", key="nombre")

            ciudad = st.selectbox("Ciudad", options=list(BENCHMARK_DB.keys()), key="ciudad")
            zona = st.selectbox("Zona / Barrio", options=list(BENCHMARK_DB[ciudad].keys()), key="zona")

            area_m2 = st.number_input("Área (m²)", min_value=20.0, max_value=500.0, value=65.0, step=1.0, key="area")
            precio_total = st.number_input(
                "Precio Total (COP)", min_value=50_000_000, max_value=5_000_000_000,
                value=451_000_000, step=5_000_000, key="precio_total"
            )
            precio_m2_calc = precio_total / area_m2 if area_m2 > 0 else 0

            st.markdown(f"""
            <div style="background:var(--surface-2);border:1px solid var(--border-subtle);
            border-radius:8px;padding:0.75rem 1rem;margin:0.5rem 0;">
                <span style="color:var(--text-muted);font-size:0.65rem;letter-spacing:0.1em;
                text-transform:uppercase;font-family:'DM Mono',monospace;">Precio/m² calculado</span><br>
                <span style="color:var(--gold);font-size:1.2rem;font-weight:700;
                font-family:'Syne',sans-serif;">{fmt_cop(precio_m2_calc)}</span>
            </div>
            """, unsafe_allow_html=True)

            tipo_inmueble = st.selectbox(
                "Tipo", ["Apartamento Nuevo (Planos)", "Apartamento Usado", "Casa", "Local Comercial", "Bodega"], key="tipo"
            )
            estrato = st.selectbox("Estrato", [3, 4, 5, 6], index=2, key="estrato")
            entrega = st.text_input("Fecha de Entrega Proyectada", value="Junio 2028", key="entrega")

            st.markdown('</div>', unsafe_allow_html=True)

        with col_result:
            benchmark = BENCHMARK_DB[ciudad][zona]
            analisis = analyze_sobreprecio(precio_m2_calc, benchmark)

            # Alerta de Precio
            if analisis["es_sobreprecio"]:
                desv_pct = analisis["desviacion"] * 100
                st.markdown(f"""
                <div class="alert-danger">
                    <div class="alert-title" style="color:var(--danger);">
                        ⚠ ALERTA: RIESGO DE SOBREPRECIO DETECTADO
                    </div>
                    <div class="alert-body">
                        El precio/m² ingresado (<strong style="color:var(--text-primary);">{fmt_cop(precio_m2_calc)}</strong>)
                        supera en <strong style="color:var(--danger);">+{desv_pct:.1f}%</strong> el promedio de mercado
                        para la zona <em>{zona}</em> ({fmt_cop(benchmark['precio_m2_avg'])}/m²).
                        <br><br>
                        Precio justo estimado: <strong style="color:var(--text-primary);">{fmt_cop(benchmark['precio_m2_avg'] * area_m2)}</strong>
                        &nbsp;|&nbsp; Diferencial: <strong style="color:var(--danger);">{fmt_cop(precio_total - benchmark['precio_m2_avg'] * area_m2)}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif analisis["es_oportunidad"]:
                st.markdown(f"""
                <div class="alert-success">
                    <div class="alert-title" style="color:var(--success);">✓ OPORTUNIDAD: PRECIO POR DEBAJO DEL MERCADO</div>
                    <div class="alert-body">
                        Descuento de <strong>{abs(analisis['desviacion'])*100:.1f}%</strong> vs promedio zona.
                        Margen implícito de valorización desde el día 1.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-warning">
                    <div class="alert-title" style="color:var(--gold);">◈ PRECIO EN RANGO DE MERCADO</div>
                    <div class="alert-body">
                        El precio/m² está dentro del rango normal para {zona}.
                        Validar condiciones de entrega y calidad de acabados.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Benchmark Gauges
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">02 · Benchmark de Mercado</div>', unsafe_allow_html=True)

            # Gauge Precio m²
            bmin, bavg, bmax = benchmark['precio_m2_min'], benchmark['precio_m2_avg'], benchmark['precio_m2_max']
            rango = bmax - bmin
            pos_user = min(max((precio_m2_calc - bmin) / rango * 100, 0), 100) if rango > 0 else 50
            pos_avg = (bavg - bmin) / rango * 100 if rango > 0 else 50
            color_bar = "#E05C5C" if analisis["es_sobreprecio"] else "#4CAF82" if analisis["es_oportunidad"] else "#C9A84C"

            st.markdown(f"""
            <div class="gauge-container">
                <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <span class="gauge-label">Precio / m²</span>
                    <span style="color:var(--gold);font-family:'Syne',sans-serif;font-size:0.9rem;font-weight:600;">{fmt_cop(precio_m2_calc)}</span>
                </div>
                <div class="gauge-bar-bg">
                    <div class="gauge-bar-fill" style="width:{pos_avg:.0f}%;background:rgba(255,255,255,0.1);position:absolute;top:0;left:0;height:100%;"></div>
                    <div style="position:absolute;top:-3px;left:{pos_user:.0f}%;width:14px;height:14px;
                    background:{color_bar};border-radius:50%;transform:translateX(-50%);
                    border:2px solid var(--obsidian);"></div>
                </div>
                <div style="display:flex;justify-content:space-between;margin-top:0.25rem;">
                    <span class="gauge-label">{fmt_cop(bmin)}</span>
                    <span style="color:var(--text-secondary);font-size:0.65rem;font-family:'DM Mono',monospace;">avg {fmt_cop(bavg)}</span>
                    <span class="gauge-label">{fmt_cop(bmax)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Gauge Renta m²
            rmin, ravg, rmax = benchmark['renta_m2_min'], benchmark['renta_m2_avg'], benchmark['renta_m2_max']
            renta_estimada_m2 = ravg
            renta_estimada_total = renta_estimada_m2 * area_m2
            pos_renta = 50  # siempre en avg
            cap_rate_est = (renta_estimada_total * 12) / precio_total if precio_total > 0 else 0

            st.markdown(f"""
            <div class="gauge-container">
                <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <span class="gauge-label">Renta / m² estimada zona</span>
                    <span style="color:var(--success);font-family:'Syne',sans-serif;font-size:0.9rem;font-weight:600;">{fmt_cop(ravg)}/m²</span>
                </div>
                <div style="margin-top:0.75rem;display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;">
                    <div style="text-align:center;">
                        <div class="gauge-label">Canon Est.</div>
                        <div style="color:var(--text-primary);font-family:'Syne',sans-serif;font-size:1rem;font-weight:600;">{fmt_cop(renta_estimada_total)}/mes</div>
                    </div>
                    <div style="text-align:center;">
                        <div class="gauge-label">Cap Rate Est.</div>
                        <div style="color:{'var(--success)' if cap_rate_est >= 0.06 else 'var(--gold)'};font-family:'Syne',sans-serif;font-size:1rem;font-weight:600;">{fmt_pct(cap_rate_est)}</div>
                    </div>
                    <div style="text-align:center;">
                        <div class="gauge-label">Ref. Zona</div>
                        <div style="color:var(--info);font-family:'Syne',sans-serif;font-size:1rem;font-weight:600;">{fmt_pct(benchmark['cap_rate_ref'])}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:var(--surface-3);border-radius:8px;padding:0.75rem 1rem;margin-top:0.75rem;">
                <span style="color:var(--text-muted);font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;font-family:'DM Mono',monospace;">
                📍 {benchmark['notas']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # TAB 2: ESCUDO FISCAL
    # ═══════════════════════════════════════════════════════════════
    with tab2:
        col_params, col_fiscal = st.columns([1, 1.4], gap="large")

        with col_params:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">03 · Parámetros Fiscales</div>', unsafe_allow_html=True)

            valor_inmueble_f = st.number_input(
                "Valor Inmueble (COP)", min_value=50_000_000, max_value=5_000_000_000,
                value=451_000_000, step=5_000_000, key="valor_f"
            )
            canon_mensual = st.number_input(
                "Canon Mensual (COP)", min_value=500_000, max_value=20_000_000,
                value=2_400_000, step=100_000, key="canon"
            )
            ingresos_anuales_pn = st.number_input(
                "Ingresos Anuales PN (salario/honorarios)", min_value=0, max_value=1_000_000_000,
                value=120_000_000, step=5_000_000, key="ingresos_pn",
                help="Ingrese sus ingresos anuales como Persona Natural para calcular el impuesto marginal"
            )
            financiacion_pct = st.slider(
                "% Financiado con Crédito Hipotecario", min_value=0, max_value=80, value=50, step=5, key="finpct"
            )
            tasa_hipoteca = st.slider(
                "Tasa Hipotecaria Anual (%)", min_value=8.0, max_value=20.0, value=14.5, step=0.5, key="tasa"
            )

            st.markdown('</div>', unsafe_allow_html=True)

        with col_fiscal:
            result = calcular_escudo_fiscal(
                valor_inmueble=valor_inmueble_f,
                canon_mensual=canon_mensual,
                financiacion_pct=financiacion_pct / 100,
                tasa_hipoteca=tasa_hipoteca / 100,
                ingresos_anuales_pn=ingresos_anuales_pn,
            )

            # Summary metrics
            st.markdown(f"""
            <div class="metric-grid">
                <div class="metric-card" style="--accent-color:var(--info);">
                    <div class="metric-label">Cap Rate Neto PN</div>
                    <div class="metric-value" style="color:var(--info);">{fmt_pct(result['cap_rate_pn'])}</div>
                    <div class="metric-sub">Tasa efect. {fmt_pct(result['tasa_efectiva_pn'])}</div>
                </div>
                <div class="metric-card" style="--accent-color:var(--success);">
                    <div class="metric-label">Cap Rate Neto SAS</div>
                    <div class="metric-value" style="color:var(--success);">{fmt_pct(result['cap_rate_pj'])}</div>
                    <div class="metric-sub">Tasa efect. {fmt_pct(result['tasa_efectiva_pj'])}</div>
                </div>
                <div class="metric-card" style="--accent-color:var(--gold);">
                    <div class="metric-label">Ahorro Fiscal/año</div>
                    <div class="metric-value" style="color:var(--gold);">{fmt_cop(result['ahorro_fiscal_anual'])}</div>
                    <div class="metric-sub">Vía {result['ganador']}</div>
                </div>
                <div class="metric-card" style="--accent-color:var(--gold);">
                    <div class="metric-label">Ahorro 10 años</div>
                    <div class="metric-value" style="color:var(--gold);">{fmt_cop(result['ahorro_10_anos'])}</div>
                    <div class="metric-sub">Valor presente aprox.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Comparison Table
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">04 · Escudo Fiscal Comparativo</div>', unsafe_allow_html=True)

            st.markdown(f"""
            <table class="compare-table">
                <thead>
                    <tr>
                        <th>Concepto</th>
                        <th style="color:var(--info);">Persona Natural</th>
                        <th style="color:var(--success);">SAS (PJ)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="td-label">Renta Bruta Anual</td>
                        <td class="td-pn">{fmt_cop(result['renta_bruta'])}</td>
                        <td class="td-pj">{fmt_cop(result['renta_bruta'])}</td>
                    </tr>
                    <tr>
                        <td class="td-label">Costos Deducibles</td>
                        <td class="td-pn">{fmt_cop(result['costos_pn'])} <span style="font-size:0.65rem;color:var(--text-muted);">(30% pres.)</span></td>
                        <td class="td-pj">{fmt_cop(result['costos_admin_pj'] + result['ica_pj'])} <span style="font-size:0.65rem;color:var(--text-muted);">(admin+ICA)</span></td>
                    </tr>
                    <tr>
                        <td class="td-label">Intereses Hipoteca</td>
                        <td class="td-pn">{fmt_cop(result['intereses'])}</td>
                        <td class="td-pj">{fmt_cop(result['intereses'])}</td>
                    </tr>
                    <tr>
                        <td class="td-label">Depreciación Lineal (45a)</td>
                        <td style="color:var(--text-muted);">N/A</td>
                        <td class="td-pj" style="font-weight:600;">{fmt_cop(result['depreciacion'])} ✓</td>
                    </tr>
                    <tr>
                        <td class="td-label">Renta Neta Gravable</td>
                        <td class="td-pn">{fmt_cop(result['renta_neta_pn'])}</td>
                        <td class="td-pj">{fmt_cop(result['renta_neta_pj'])}</td>
                    </tr>
                    <tr>
                        <td class="td-label">Impuesto Renta</td>
                        <td class="td-pn">{fmt_cop(result['impuesto_incremental_pn'])} <span style="font-size:0.65rem;color:var(--text-muted);">(marginal)</span></td>
                        <td class="td-pj">{fmt_cop(result['impuesto_pj'])} <span style="font-size:0.65rem;color:var(--text-muted);">(35%)</span></td>
                    </tr>
                    <tr>
                        <td class="td-label">Impuesto Dividendos</td>
                        <td style="color:var(--text-muted);">N/A</td>
                        <td class="td-pj">{fmt_cop(result['impuesto_dividendos'])} <span style="font-size:0.65rem;color:var(--text-muted);">(10%)</span></td>
                    </tr>
                    <tr style="border-top:1px solid var(--border);">
                        <td class="td-label" style="font-weight:600;color:var(--text-secondary);">Ingreso Neto Real</td>
                        <td class="td-pn" style="font-size:1rem;font-family:'Syne',sans-serif;font-weight:700;">{fmt_cop(result['ingreso_neto_pn'])}</td>
                        <td class="td-pj" style="font-size:1rem;font-family:'Syne',sans-serif;font-weight:700;">{fmt_cop(result['ingreso_neto_pj'])}</td>
                    </tr>
                    <tr>
                        <td class="td-label" style="font-weight:600;color:var(--text-secondary);">Tasa Efectiva Total</td>
                        <td class="td-pn">{fmt_pct(result['tasa_efectiva_pn'])}</td>
                        <td class="td-pj">{fmt_pct(result['tasa_efectiva_pj'])}</td>
                    </tr>
                    <tr style="background:rgba(201,168,76,0.05);">
                        <td class="td-label" style="color:var(--gold);font-weight:700;">Ventaja SAS / año</td>
                        <td colspan="2" class="td-winner" style="font-size:1rem;font-family:'Syne',sans-serif;">
                            {fmt_cop(abs(result['ahorro_fiscal_anual']))} a favor de {result['ganador']}
                        </td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # TAB 3: ESTRATEGIA DE SALIDA
    # ═══════════════════════════════════════════════════════════════
    with tab3:
        col_salida, col_result_salida = st.columns([1, 1.3], gap="large")

        with col_salida:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">05 · Proyección de Salida</div>', unsafe_allow_html=True)

            valor_compra_s = st.number_input(
                "Precio de Compra (COP)", min_value=50_000_000, max_value=5_000_000_000,
                value=451_000_000, step=5_000_000, key="compra_s"
            )
            valorizacion_anual = st.slider(
                "Valorización Anual Estimada (%)", min_value=2.0, max_value=15.0, value=7.0, step=0.5, key="valorizacion"
            )
            anos_tenencia = st.slider(
                "Años de Tenencia", min_value=1, max_value=25, value=10, step=1, key="anos"
            )

            valor_venta_calc = valor_compra_s * ((1 + valorizacion_anual / 100) ** anos_tenencia)
            st.markdown(f"""
            <div style="background:var(--surface-2);border:1px solid var(--border-subtle);border-radius:8px;padding:1rem;margin:0.75rem 0;">
                <div class="gauge-label" style="margin-bottom:0.5rem;">Valor de Venta Proyectado</div>
                <div style="color:var(--gold);font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;">{fmt_cop(valor_venta_calc)}</div>
                <div style="color:var(--text-muted);font-family:'DM Mono',monospace;font-size:0.7rem;margin-top:0.25rem;">
                    Plusvalía bruta: {fmt_cop(valor_venta_calc - valor_compra_s)} en {anos_tenencia} años
                </div>
            </div>
            """, unsafe_allow_html=True)

            vende_como = st.radio(
                "Vende como:", ["Persona Natural (15% GO)", "SAS (10% GO)"], key="tipo_venta"
            )
            es_pj_venta = "SAS" in vende_como

            st.markdown('</div>', unsafe_allow_html=True)

        with col_result_salida:
            go_result = calcular_go_salida(
                valor_compra=valor_compra_s,
                valor_venta=valor_venta_calc,
                anos_tenencia=anos_tenencia,
                es_pj=es_pj_venta,
            )

            go_result_alt = calcular_go_salida(
                valor_compra=valor_compra_s,
                valor_venta=valor_venta_calc,
                anos_tenencia=anos_tenencia,
                es_pj=not es_pj_venta,
            )

            label_sel = "SAS" if es_pj_venta else "PN"
            label_alt = "PN" if es_pj_venta else "SAS"
            ahorro_go = go_result["utilidad_neta"] - go_result_alt["utilidad_neta"]

            st.markdown(f"""
            <div class="metric-grid">
                <div class="metric-card" style="--accent-color:var(--success);">
                    <div class="metric-label">Utilidad Neta ({label_sel})</div>
                    <div class="metric-value" style="color:var(--success);">{fmt_cop(go_result['utilidad_neta'])}</div>
                    <div class="metric-sub">ROI: {fmt_pct(go_result['roi'])}</div>
                </div>
                <div class="metric-card" style="--accent-color:var(--danger);">
                    <div class="metric-label">Impuesto GO ({label_sel})</div>
                    <div class="metric-value" style="color:var(--danger);">{fmt_cop(go_result['impuesto_go'])}</div>
                    <div class="metric-sub">Tarifa {fmt_pct(go_result['tarifa'])}</div>
                </div>
                <div class="metric-card" style="--accent-color:var(--gold);">
                    <div class="metric-label">Ventaja vs {label_alt}</div>
                    <div class="metric-value" style="color:var(--gold);">{fmt_cop(abs(ahorro_go))}</div>
                    <div class="metric-sub">{'Ahorro estructurando vía SAS' if ahorro_go > 0 else 'En este escenario PN ventaja'}</div>
                </div>
                <div class="metric-card" style="--accent-color:var(--info);">
                    <div class="metric-label">Plusvalía Bruta</div>
                    <div class="metric-value" style="color:var(--info);">{fmt_cop(valor_venta_calc - valor_compra_s)}</div>
                    <div class="metric-sub">{anos_tenencia} años · {valorizacion_anual:.1f}% anual</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">06 · Waterfall de Salida</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <table class="compare-table">
                <thead>
                    <tr><th>Concepto</th><th>Valor</th></tr>
                </thead>
                <tbody>
                    <tr><td class="td-label">Precio de Venta</td><td style="color:var(--text-primary);">{fmt_cop(valor_venta_calc)}</td></tr>
                    <tr><td class="td-label">(-) Costo Fiscal Ajustado por IGAC</td><td style="color:var(--danger);">({fmt_cop(go_result['costo_fiscal_ajustado'])})</td></tr>
                    <tr><td class="td-label">= Ganancia Ocasional Gravable</td><td style="color:var(--text-primary);">{fmt_cop(go_result['go_bruta'])}</td></tr>
                    <tr><td class="td-label">(-) Impuesto GO ({fmt_pct(go_result['tarifa'])} · {label_sel})</td><td style="color:var(--danger);">({fmt_cop(go_result['impuesto_go'])})</td></tr>
                    <tr><td class="td-label">(-) Precio de Compra Original</td><td style="color:var(--danger);">({fmt_cop(valor_compra_s)})</td></tr>
                    <tr style="background:rgba(201,168,76,0.05);border-top:1px solid var(--border);">
                        <td class="td-label" style="color:var(--gold);font-weight:700;">= Utilidad Neta Final</td>
                        <td class="td-winner" style="font-size:1.1rem;font-family:'Syne',sans-serif;">{fmt_cop(go_result['utilidad_neta'])}</td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)

            if ahorro_go > 1_000_000:
                st.markdown(f"""
                <div class="alert-success" style="margin-top:1rem;">
                    <div class="alert-title" style="color:var(--success);">✓ OPTIMIZACIÓN ESTRUCTURAL DISPONIBLE</div>
                    <div class="alert-body">
                        Estructurando la inversión y la venta a través de una SAS, el ahorro en impuesto de
                        Ganancia Ocasional sería de <strong style="color:var(--success);">{fmt_cop(abs(ahorro_go))}</strong>
                        comparado con vender como Persona Natural (tarifa 15% vs 10%).
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # CTA — GENERAR REPORTE
    # ═══════════════════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">◈ Descargar Reporte de Due Diligence</div>', unsafe_allow_html=True)

    col_cta1, col_cta2, col_cta3 = st.columns([1.5, 1, 1])
    with col_cta1:
        st.markdown("""
        <div style="padding:0.25rem 0 1rem;">
            <p style="color:var(--text-secondary);font-family:'DM Mono',monospace;font-size:0.75rem;line-height:1.7;margin:0;">
            El reporte incluye: Benchmark de mercado · Análisis PN vs SAS ·
            Waterfall de salida · Recomendaciones de estructuración patrimonial.
            </p>
            <p style="color:var(--gold);font-family:'DM Mono',monospace;font-size:0.7rem;margin-top:0.5rem;letter-spacing:0.05em;">
            Para implementar la estructura óptima, agenda una consulta con Corenta S.A.S.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_cta2:
        # Build report data for download
        try:
            benchmark_actual = BENCHMARK_DB[st.session_state.get("ciudad", "Barranquilla")][st.session_state.get("zona", list(BENCHMARK_DB["Barranquilla"].keys())[0])]
            area = st.session_state.get("area", 65.0)
            precio_total_val = st.session_state.get("precio_total", 451_000_000)
            precio_m2_val = precio_total_val / area if area > 0 else 0
            canon_val = st.session_state.get("canon", 2_400_000)
            valor_f_val = st.session_state.get("valor_f", 451_000_000)
            ingresos_val = st.session_state.get("ingresos_pn", 120_000_000)
            fin_pct_val = st.session_state.get("finpct", 50) / 100
            tasa_val = st.session_state.get("tasa", 14.5) / 100

            result_reporte = calcular_escudo_fiscal(valor_f_val, canon_val, fin_pct_val, tasa_val, ingresos_val)
            anos_tenencia_rep = st.session_state.get("anos", 10)
            valorizacion_rep = st.session_state.get("valorizacion", 7.0)
            compra_s_rep = st.session_state.get("compra_s", 451_000_000)
            venta_calc_rep = compra_s_rep * ((1 + valorizacion_rep / 100) ** anos_tenencia_rep)
            go_rep = calcular_go_salida(compra_s_rep, venta_calc_rep, anos_tenencia_rep, True)

            inputs_reporte = {
                "precio_m2": precio_m2_val,
                "valor_inmueble": valor_f_val,
                "canon_mensual": canon_val,
            }

            reporte_texto = generar_reporte_texto(
                proyecto=st.session_state.get("nombre", "Proyecto"),
                zona=st.session_state.get("zona", "Zona"),
                benchmark=benchmark_actual,
                inputs=inputs_reporte,
                fiscal_result=result_reporte,
                go_result_pj=go_rep,
            )

            st.download_button(
                label="⬇ Descargar Reporte (.txt)",
                data=reporte_texto.encode("utf-8"),
                file_name=f"corenta_due_diligence_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
            )
        except Exception as e:
            st.error(f"Error generando reporte: {e}")

    with col_cta3:
        st.markdown("""
        <a href="mailto:jcperez@corenta.co?subject=Consulta Due Diligence Inmobiliario&body=Hola Juan Carlos, quiero agendar una consulta para estructurar mi inversión inmobiliaria."
        style="display:block;text-align:center;background:var(--surface-3);border:1px solid var(--border);
        color:var(--gold);font-family:'Syne',sans-serif;font-size:0.8rem;font-weight:600;
        padding:0.75rem 1rem;border-radius:var(--radius);text-decoration:none;letter-spacing:0.05em;
        transition:background 0.2s;">
            ✉ Agendar Consulta → Corenta
        </a>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── FOOTER ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;padding:2rem 0 1rem;border-top:1px solid var(--border-subtle);margin-top:2rem;">
        <span style="color:var(--text-muted);font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.1em;">
        © {datetime.now().year} CORENTA S.A.S. · NIT · Barranquilla, Colombia ·
        jcperez@corenta.co · Normativa: ET, Ley 2277/2022, Decreto 1625/2016
        </span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
