"""
app.py — Punto de entrada principal. Orquesta autenticación, datos y UI.

Estructura del proyecto:
  app.py          → Entrada principal (este archivo)
  auth.py         → Autenticación segura con anti-fuerza bruta y expiración de sesión
  database.py     → Capa de acceso a datos (Supabase / SQLAlchemy)
  config.py       → Constantes: meses, categorías, colores, etc.
  components.py   → Componentes de UI: dialog añadir gasto, gestión (editar/eliminar)
  charts.py       → Visualizaciones Plotly
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from auth import check_password, logout
from database import load_expenses
from config import MONTHS
from components import dialog_add_expense, tab_manage
from charts import chart_pie, chart_bar_historical, chart_trend_line, chart_category_detail

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Gastos del Hogar",
    layout="wide",
    page_icon="💰",
    initial_sidebar_state="collapsed",   # sidebar oculto por defecto en móvil
)

# ---------------------------------------------------------------------------
# CSS global: corrige selectbox difuminado + mejora móvil
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Selectbox: texto siempre visible ────────────────────────────── */
div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: #ffffff !important;
}
li[role="option"] {
    color: #ffffff !important;
    background-color: #1e2530 !important;
}
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background-color: #3B82F6 !important;
    color: #ffffff !important;
}

/* ── Botón principal: tamaño cómodo para el pulgar ───────────────── */
div.stButton > button[kind="primary"] {
    min-height: 48px;
    font-size: 1rem;
}

/* ── Métricas: apiladas en móvil ─────────────────────────────────── */
@media (max-width: 640px) {
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    /* Tabs: texto más pequeño para que quepan en pantalla estrecha */
    button[data-baseweb="tab"] {
        font-size: 0.78rem !important;
        padding: 8px 6px !important;
    }
}

/* ── Dialog: ocupa más pantalla en móvil ─────────────────────────── */
div[data-testid="stDialog"] > div {
    max-width: 96vw !important;
    width: 96vw !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------
if not check_password():
    st.stop()

# ---------------------------------------------------------------------------
# Fecha actual
# ---------------------------------------------------------------------------
now = datetime.now()
current_year = now.year
current_month_index = now.month - 1  # 0-based

# ---------------------------------------------------------------------------
# Barra superior: título + botón añadir
# ---------------------------------------------------------------------------
col_title, col_actions = st.columns([4, 1])
with col_title:
    st.title("💰 Gastos del Hogar")
with col_actions:
    st.markdown("<div style='padding-top:18px'>", unsafe_allow_html=True)
    if st.button("➕ Añadir", help="Añadir gasto", use_container_width=True, type="primary"):
        dialog_add_expense(current_year, current_month_index)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
df = load_expenses()

# Botón refresco manual (discreto, bajo el título)
if st.button("🔄 Actualizar datos", type="secondary"):
    load_expenses.clear()
    st.rerun()

if df.empty:
    st.info("Aún no hay gastos registrados. Pulsa ➕ para añadir el primero.")
    st.stop()

# ---------------------------------------------------------------------------
# Filtros — selectores en fila, compactos
# ---------------------------------------------------------------------------

col_yr, _ = st.columns([1, 2])
with col_yr:
    available_years = sorted(df["year"].unique())
    default_year_idx = (
        available_years.index(current_year)
        if current_year in available_years
        else len(available_years) - 1
    )
    selected_year = st.selectbox("📅 Año", available_years, index=default_year_idx)

# Radio no abre teclado en movil
st.markdown("")

year_df = df[df["year"] == selected_year]
available_months = [m for m in MONTHS if m in year_df["month"].unique()]
default_month = MONTHS[current_month_index]
default_month_idx = (
    available_months.index(default_month)
    if default_month in available_months
    else 0
)
st.markdown("**Mes**")
selected_month = st.radio(
    "Mes",
    available_months,
    index=default_month_idx,
    horizontal=True,
    label_visibility="collapsed",
)

filtered_df = year_df[year_df["month"] == selected_month]

# Mes anterior → delta KPI
prev_month_idx = MONTHS.index(selected_month) - 1
prev_month_total = 0.0
if prev_month_idx >= 0:
    prev_month_name = MONTHS[prev_month_idx]
    prev_df = year_df[year_df["month"] == prev_month_name]
    prev_month_total = float(prev_df["cost"].sum())

# ---------------------------------------------------------------------------
# KPIs — 2×2 en móvil, 4 en fila en escritorio
# ---------------------------------------------------------------------------
st.markdown("### 📈 Resumen")

monthly_total = float(filtered_df["cost"].sum())
yearly_total  = float(year_df["cost"].sum())
monthly_avg   = yearly_total / max(len(available_months), 1)
top_category  = (
    filtered_df.groupby("category")["cost"].sum().idxmax()
    if not filtered_df.empty else "—"
)
delta_vs_prev = monthly_total - prev_month_total if prev_month_total > 0 else None

# Fila 1
kpi_r1c1, kpi_r1c2 = st.columns(2)
kpi_r1c1.metric(
    label=f"Total {selected_month}",
    value=f"{monthly_total:,.2f} €",
    delta=f"{delta_vs_prev:+,.2f} € vs anterior" if delta_vs_prev is not None else None,
    delta_color="inverse",
)
kpi_r1c2.metric(label=f"Acumulado {selected_year}", value=f"{yearly_total:,.2f} €")

# Fila 2
kpi_r2c1, kpi_r2c2 = st.columns(2)
kpi_r2c1.metric(label="Media mensual", value=f"{monthly_avg:,.2f} €")
kpi_r2c2.metric(label="Mayor categoría", value=top_category)

st.markdown("---")

# ---------------------------------------------------------------------------
# Pestañas principales
# ---------------------------------------------------------------------------
tab_charts, tab_data, tab_manage_tab = st.tabs(["📊 Gráficos", "📋 Datos", "⚙️ Gestión"])

with tab_charts:
    # En móvil los gráficos se apilan (1 columna); en escritorio van en 2 columnas
    c1, c2 = st.columns([1, 1])
    with c1:
        chart_pie(filtered_df, selected_month)
    with c2:
        chart_bar_historical(year_df, selected_year)

    st.markdown("---")
    c3, c4 = st.columns([1, 1])
    with c3:
        chart_trend_line(year_df, selected_year)
    with c4:
        chart_category_detail(filtered_df, selected_month)

with tab_data:
    st.markdown(f"#### 📋 {selected_month} {selected_year}")

    if filtered_df.empty:
        st.info("No hay registros en este mes.")
    else:
        display_df = filtered_df.drop(columns=["year", "month"]).copy()
        display_df = display_df.rename(columns={
            "id":          "ID",
            "category":    "Categoría",
            "item":        "Concepto",
            "period":      "Periodo",
            "consumption": "Consumo (kWh/m³)",
            "unit_price":  "Precio Unit. (€)",
            "cost":        "Coste (€)",
        })
        st.dataframe(
            display_df.style.format({
                "Consumo (kWh/m³)":  lambda v: f"{v:,.1f}"   if pd.notnull(v) else "—",
                "Precio Unit. (€)":  lambda v: f"{v:,.4f} €" if pd.notnull(v) else "—",
                "Coste (€)":         lambda v: f"{v:,.2f} €" if pd.notnull(v) else "0.00 €",
            }),
            use_container_width=True,
        )

        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Descargar CSV",
            data=csv,
            file_name=f"gastos_{selected_month}_{selected_year}.csv",
            mime="text/csv",
            use_container_width=True,
        )

with tab_manage_tab:
    tab_manage(filtered_df)

# ---------------------------------------------------------------------------
# Zona de cierre de sesión — al final de la página, separada visualmente
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<style>
/* Expander de logout en rojo */
div[data-testid="stExpander"] details summary p {
    color: #EF4444 !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

with st.expander("🚪 Cerrar sesión"):
    st.warning("¿Seguro que quieres cerrar la sesión? Tendrás que volver a introducir tus credenciales.")
    col_logout, col_cancel = st.columns(2)
    with col_logout:
        if st.button("✅ Sí, cerrar sesión", use_container_width=True, type="primary", key="confirm_logout"):
            logout()
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True, key="cancel_logout"):
            st.rerun()
