"""
app.py — Punto de entrada principal.

Estructura del proyecto:
  app.py          → Entrada principal (este archivo)
  auth.py         → Autenticación segura
  database.py     → Capa de acceso a datos (gastos + presupuestos)
  config.py       → Constantes
  components.py   → Dialogs y componentes UI
  charts.py       → Visualizaciones Plotly
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from auth import check_password
from database import load_expenses, load_budgets, get_budget
from config import MONTHS
from components import dialog_add_expense, dialog_logout, dialog_set_budget, tab_manage
from charts import (
    chart_pie, chart_bar_historical, chart_trend_line,
    chart_category_detail, chart_budget_gauge,
)

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Gastos del Hogar",
    layout="wide",
    page_icon="💰",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# CSS global
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

/* ── Selectbox: sin teclado en móvil ─────────────────────────────── */
div[data-baseweb="select"] input {
    caret-color: transparent !important;
    pointer-events: none !important;
}

/* ── Todos los botones: altura mínima cómoda para el pulgar ──────── */
div.stButton > button {
    min-height: 44px;
}

/* ── Tabs: más grandes y fáciles de pulsar en móvil ─────────────── */
button[data-baseweb="tab"] {
    font-size: 1rem !important;
    padding: 12px 16px !important;
    min-height: 52px !important;
}
div[data-baseweb="tab-list"] {
    gap: 4px !important;
}

/* ── Dialog: ancho máximo en móvil ───────────────────────────────── */
div[data-testid="stDialog"] > div {
    max-width: 96vw !important;
    width: 96vw !important;
}

/* ── Métricas: 2 columnas siempre (ya lo forzamos en Python) ─────── */
@media (max-width: 480px) {
    button[data-baseweb="tab"] {
        font-size: 0.85rem !important;
        padding: 10px 8px !important;
    }
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
current_month_index = now.month - 1

# ---------------------------------------------------------------------------
# Barra superior: título + acciones
# ---------------------------------------------------------------------------
col_title, col_btn_add, col_btn_budget, col_btn_refresh, col_btn_logout = st.columns(
    [4, 1, 1, 1, 1]
)
with col_title:
    st.title("💰 Gastos del Hogar")

with col_btn_add:
    st.markdown("<div style='padding-top:18px'>", unsafe_allow_html=True)
    if st.button("➕ Añadir", use_container_width=True, type="primary"):
        dialog_add_expense(current_year, current_month_index)
    st.markdown("</div>", unsafe_allow_html=True)

with col_btn_budget:
    st.markdown("<div style='padding-top:18px'>", unsafe_allow_html=True)
    if st.button("🎯 Presupuesto", use_container_width=True):
        budget_now = get_budget(current_year, MONTHS[current_month_index])
        dialog_set_budget(current_year, current_month_index, budget_now)
    st.markdown("</div>", unsafe_allow_html=True)

with col_btn_refresh:
    st.markdown("<div style='padding-top:18px'>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", use_container_width=True):
        load_expenses.clear()
        load_budgets.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col_btn_logout:
    st.markdown("""
    <div style='padding-top:18px'>
    <style>
    div[data-testid="stHorizontalBlock"] div.stButton:last-child button {
        background-color: #EF4444 !important;
        border-color: #EF4444 !important;
        color: white !important;
    }
    div[data-testid="stHorizontalBlock"] div.stButton:last-child button:hover {
        background-color: #DC2626 !important;
        border-color: #DC2626 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("🚪 Salir", use_container_width=True, key="btn_logout"):
        dialog_logout()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
df = load_expenses()
budgets_df = load_budgets()

if df.empty:
    st.info("Aún no hay gastos registrados. Pulsa ➕ para añadir el primero.")
    st.stop()

# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
col_f1, col_f2 = st.columns(2)

with col_f1:
    available_years = sorted(df["year"].unique())
    default_year_idx = (
        available_years.index(current_year)
        if current_year in available_years
        else len(available_years) - 1
    )
    selected_year = st.selectbox("📅 Año", available_years, index=default_year_idx)

with col_f2:
    year_df = df[df["year"] == selected_year]
    available_months = [m for m in MONTHS if m in year_df["month"].unique()]
    default_month = MONTHS[current_month_index]
    default_month_idx = (
        available_months.index(default_month)
        if default_month in available_months
        else 0
    )
    selected_month = st.selectbox("🗓️ Mes", available_months, index=default_month_idx)

filtered_df = year_df[year_df["month"] == selected_month]

# Presupuesto del mes seleccionado
monthly_budget = get_budget(int(selected_year), selected_month)

# Mes anterior → delta KPI
prev_month_idx = MONTHS.index(selected_month) - 1
prev_month_total = 0.0
if prev_month_idx >= 0:
    prev_month_name = MONTHS[prev_month_idx]
    prev_df = year_df[year_df["month"] == prev_month_name]
    prev_month_total = float(prev_df["cost"].sum())

# ---------------------------------------------------------------------------
# KPIs — 2 filas × 2 columnas (legible en móvil)
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

kpi_r1c1, kpi_r1c2 = st.columns(2)
kpi_r1c1.metric(
    label=f"Total {selected_month}",
    value=f"{monthly_total:,.2f} €",
    delta=f"{delta_vs_prev:+,.2f} € vs anterior" if delta_vs_prev is not None else None,
    delta_color="inverse",
)
kpi_r1c2.metric(label=f"Acumulado {selected_year}", value=f"{yearly_total:,.2f} €")

kpi_r2c1, kpi_r2c2 = st.columns(2)
kpi_r2c1.metric(label="Media mensual", value=f"{monthly_avg:,.2f} €")

if monthly_budget:
    remaining = monthly_budget - monthly_total
    kpi_r2c2.metric(
        label="Presupuesto restante",
        value=f"{remaining:,.2f} €",
        delta=f"de {monthly_budget:,.2f} € totales",
        delta_color="off",
    )
else:
    kpi_r2c2.metric(label="Mayor categoría", value=top_category)

st.markdown("---")

# ---------------------------------------------------------------------------
# Pestañas — iconos grandes, fáciles de pulsar en móvil
# ---------------------------------------------------------------------------
tab_charts, tab_data, tab_manage_tab = st.tabs([
    "📊  Gráficos",
    "📋  Datos",
    "⚙️  Gestión",
])

with tab_charts:
    # Si hay presupuesto, mostrar gauge arriba del todo
    if monthly_budget:
        chart_budget_gauge(monthly_total, monthly_budget, selected_month)
        st.markdown("---")

    c1, c2 = st.columns([1, 1])
    with c1:
        chart_pie(filtered_df, selected_month)
    with c2:
        chart_bar_historical(year_df, selected_year)

    st.markdown("---")
    c3, c4 = st.columns([1, 1])
    with c3:
        chart_trend_line(year_df, selected_year, budgets_df)
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
                "Consumo (kWh/m³)": lambda v: f"{v:,.1f}"   if pd.notnull(v) else "—",
                "Precio Unit. (€)": lambda v: f"{v:,.4f} €" if pd.notnull(v) else "—",
                "Coste (€)":        lambda v: f"{v:,.2f} €" if pd.notnull(v) else "0.00 €",
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
