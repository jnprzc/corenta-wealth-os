# Corenta Wealth OS — MVP v1.0
**Motor de Due Diligence Inmobiliario para Colombia**

---

## Setup (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy en Streamlit Cloud (gratis)

1. Subir `app.py` y `requirements.txt` a un repo de GitHub
2. Ir a https://share.streamlit.io → New app
3. Apuntar al repo y archivo `app.py`
4. URL resultante: `https://[tu-app].streamlit.app`

## Estructura del MVP

### Tab 1 — Análisis de Proyecto (Benchmarking)
- Ingreso de datos del inmueble (ciudad, zona, área, precio)
- Cálculo automático de precio/m²
- Comparación vs. base de datos de mercado (8 zonas: Barranquilla, Bogotá, Medellín)
- **Alerta de Sobreprecio** si el precio supera >15% el promedio de zona
- Gauge visual de posición vs. rango min-max
- Cap rate estimado vs. referencia de zona

### Tab 2 — Escudo Fiscal (PN vs SAS)
- Motor fiscal completo Colombia 2024-2025
- Persona Natural: tabla Art. 241 ET, costos presuntos 30%, tasa marginal
- SAS: depreciación lineal 45 años, ICA, dividendos 10%
- Comparativa de ingreso neto real y cap rate neto
- Cálculo de ahorro fiscal anual y proyectado a 10 años

### Tab 3 — Estrategia de Salida
- Proyección de valorización con input de tasa anual
- Ganancia Ocasional: PN 15% vs. SAS 10%
- Ajuste por costo fiscal IGAC (inflación acumulada)
- Waterfall visual de utilidad neta

### CTA — Reporte Descargable
- Genera reporte `.txt` de Due Diligence completo
- Actúa como lead magnet para contratar servicios de Corenta

---

## Expandir la Base de Datos de Benchmark

El diccionario `BENCHMARK_DB` en `app.py` es la fuente de verdad del mercado.
Agregar zonas es tan simple como:

```python
BENCHMARK_DB["Cartagena"] = {
    "Bocagrande / El Laguito": {
        "precio_m2_min": 7_500_000,
        "precio_m2_max": 14_000_000,
        "precio_m2_avg": 10_200_000,
        "renta_m2_min": 45_000,
        "renta_m2_max": 90_000,
        "renta_m2_avg": 65_000,
        "cap_rate_ref": 0.076,
        "notas": "Alta demanda turística / Airbnb.",
    },
}
```

---

## Roadmap hacia el "Norte Completo"

| Fase | Feature | Stack |
|------|---------|-------|
| MVP | Due Diligence + Escudo Fiscal | Streamlit |
| v2 | Mapa interactivo de zonas | Folium + Streamlit |
| v2 | Auth + dashboard multi-cliente | Supabase |
| v3 | API de precios real (scraping) | FastAPI + BeautifulSoup |
| v3 | Generación de PDF del reporte | reportlab |
| v4 | Alertas de "momento de salida" | Python + cron |
| v5 | SaaS con planes pagos | Stripe |

---

© 2025 Corenta S.A.S. — jcperez@corenta.co
