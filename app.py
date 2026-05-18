"""
app.py — Punto de entrada principal. Orquesta autenticación, datos y UI.

Estructura del proyecto:
  app.py          → Entrada principal (este archivo)
  auth.py         → Autenticación segura con anti-fuerza bruta y expiración de sesión
  database.py     → Capa de acceso a datos (Supabase / SQLAlchemy)
  config.py       → Constantes: meses, categorías, colores, etc.
  components.py   → Componentes de UI: sidebar, gestión (editar/eliminar)
  charts.py       → Visualizaciones Plotly
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from auth import check_password, logout
from database import load_expenses
from config import MONTHS
from components import sidebar_add_expense, tab_manage
from charts import chart_pie, chart_bar_historical, chart_trend_line, chart_category_detail

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Control de Gastos del Hogar",
    layout="wide",
    page_icon="💰",
)

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
# Sidebar: añadir gasto + botón de cerrar sesión
# ---------------------------------------------------------------------------
sidebar_add_expense(current_year, current_month_index)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    logout()
    st.rerun()

# Botón de refresco manual (evita saturar la BD)
if st.sidebar.button("🔄 Actualizar Datos", use_container_width=True):
    load_expenses.clear()
    st.rerun()

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
df = load_expenses()

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
st.title("💰 Panel de Control: Gastos del Hogar")
st.markdown("---")

if df.empty:
    st.info("Aún no hay gastos registrados. Usa el menú de la izquierda para añadir el primero.")
    st.stop()

# ---------------------------------------------------------------------------
# Filtros globales
# ---------------------------------------------------------------------------
st.subheader("🔍 Filtros")
col_f1, col_f2 = st.columns(2)

with col_f1:
    available_years = sorted(df["year"].unique())
    default_year_idx = available_years.index(current_year) if current_year in available_years else len(available_years) - 1
    selected_year = st.selectbox("Año", available_years, index=default_year_idx)

with col_f2:
    year_df = df[df["year"] == selected_year]
    available_months = [m for m in MONTHS if m in year_df["month"].unique()]
    default_month = MONTHS[current_month_index]
    default_month_idx = available_months.index(default_month) if default_month in available_months else 0
    selected_month = st.selectbox("Mes", available_months, index=default_month_idx)

filtered_df = year_df[year_df["month"] == selected_month]

# Mes anterior para calcular delta en KPIs
prev_month_idx = MONTHS.index(selected_month) - 1
prev_month_total = 0.0
if prev_month_idx >= 0:
    prev_month_name = MONTHS[prev_month_idx]
    prev_df = year_df[year_df["month"] == prev_month_name]
    prev_month_total = float(prev_df["cost"].sum())

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
st.markdown("### 📈 Resumen Financiero")
k1, k2, k3, k4 = st.columns(4)

monthly_total = float(filtered_df["cost"].sum())
yearly_total = float(year_df["cost"].sum())
monthly_avg = yearly_total / max(len(available_months), 1)
top_category = (
    filtered_df.groupby("category")["cost"].sum().idxmax()
    if not filtered_df.empty else "—"
)

delta_vs_prev = monthly_total - prev_month_total if prev_month_total > 0 else None

k1.metric(
    label=f"Total {selected_month} {selected_year}",
    value=f"{monthly_total:,.2f} €",
    delta=f"{delta_vs_prev:+,.2f} € vs mes anterior" if delta_vs_prev is not None else None,
    delta_color="inverse",
)
k2.metric(label=f"Acumulado {selected_year}", value=f"{yearly_total:,.2f} €")
k3.metric(label="Media Mensual (año)", value=f"{monthly_avg:,.2f} €")
k4.metric(label="Mayor Categoría (mes)", value=top_category)

st.markdown("---")

# ---------------------------------------------------------------------------
# Pestañas principales
# ---------------------------------------------------------------------------
tab_charts, tab_data, tab_manage_tab = st.tabs(["📊 Gráficos", "📋 Datos", "⚙️ Gestión"])

with tab_charts:
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        chart_pie(filtered_df, selected_month)
    with row1_col2:
        chart_bar_historical(year_df, selected_year)

    st.markdown("---")
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        chart_trend_line(year_df, selected_year)
    with row2_col2:
        chart_category_detail(filtered_df, selected_month)

with tab_data:
    st.markdown(f"#### 📋 Desglose de Gastos — {selected_month} {selected_year}")

    if filtered_df.empty:
        st.info("No hay registros en este mes.")
    else:
        display_df = filtered_df.drop(columns=["year", "month"]).copy()
        display_df = display_df.rename(columns={
            "id": "ID",
            "category": "Categoría",
            "item": "Concepto",
            "period": "Periodo",
            "consumption": "Consumo (kWh/m³)",
            "unit_price": "Precio Unitario (€)",
            "cost": "Coste Total (€)",
        })

        st.dataframe(
            display_df.style.format({
                "Consumo (kWh/m³)": lambda v: f"{v:,.1f}" if pd.notnull(v) else "—",
                "Precio Unitario (€)": lambda v: f"{v:,.4f} €" if pd.notnull(v) else "—",
                "Coste Total (€)": lambda v: f"{v:,.2f} €" if pd.notnull(v) else "0.00 €",
            }),
            use_container_width=True,
        )

        # Descarga CSV
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Descargar CSV",
            data=csv,
            file_name=f"gastos_{selected_month}_{selected_year}.csv",
            mime="text/csv",
        )

with tab_manage_tab:
    tab_manage(filtered_df)
