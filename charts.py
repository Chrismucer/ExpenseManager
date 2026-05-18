"""
charts.py — Todas las visualizaciones con Plotly.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import MONTHS, CATEGORY_COLORS


def _color_sequence(df_col: pd.Series) -> list[str]:
    """Devuelve colores en el orden en que aparecen las categorías."""
    return [CATEGORY_COLORS.get(cat, "#6B7280") for cat in df_col.unique()]


def chart_pie(filtered_df: pd.DataFrame, month: str) -> None:
    """Gráfico de distribución por categoría (donut)."""
    st.markdown(f"#### 🍰 Distribución por Categoría — {month}")
    if filtered_df.empty:
        st.info("Sin datos para este mes.")
        return

    fig = px.pie(
        filtered_df,
        values="cost",
        names="category",
        hole=0.42,
        color="category",
        color_discrete_map=CATEGORY_COLORS,
    )
    fig.update_traces(textinfo="percent+label", pull=[0.03] * len(filtered_df))
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)


def chart_bar_historical(year_df: pd.DataFrame, year: int) -> None:
    """Gráfico de barras apiladas mensual del año."""
    st.markdown(f"#### 📊 Histórico Mensual — {year}")
    if year_df.empty:
        st.info("Sin datos para este año.")
        return

    historical = year_df.groupby(["month", "category"])["cost"].sum().reset_index()
    historical["month"] = pd.Categorical(historical["month"], categories=MONTHS, ordered=True)
    historical = historical.sort_values("month")

    fig = px.bar(
        historical,
        x="month",
        y="cost",
        color="category",
        barmode="stack",
        color_discrete_map=CATEGORY_COLORS,
        labels={"month": "Mes", "cost": "Gastos (€)", "category": "Categoría"},
    )
    fig.update_layout(margin=dict(t=20, b=40, l=20, r=20), legend_title_text="Categoría")
    st.plotly_chart(fig, use_container_width=True)


def chart_trend_line(year_df: pd.DataFrame, year: int) -> None:
    """Gráfico de línea con tendencia de gasto total mes a mes."""
    st.markdown(f"#### 📈 Tendencia de Gasto Total — {year}")
    if year_df.empty:
        st.info("Sin datos para este año.")
        return

    monthly_totals = year_df.groupby("month")["cost"].sum().reset_index()
    monthly_totals["month"] = pd.Categorical(monthly_totals["month"], categories=MONTHS, ordered=True)
    monthly_totals = monthly_totals.sort_values("month")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_totals["month"],
        y=monthly_totals["cost"],
        mode="lines+markers+text",
        text=[f"{v:,.0f} €" for v in monthly_totals["cost"]],
        textposition="top center",
        line=dict(color="#3B82F6", width=2.5),
        marker=dict(size=8, color="#3B82F6"),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.update_layout(
        xaxis_title="Mes",
        yaxis_title="Total (€)",
        margin=dict(t=20, b=40, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_category_detail(filtered_df: pd.DataFrame, month: str) -> None:
    """Gráfico de barras horizontales con el detalle de items del mes."""
    st.markdown(f"#### 🔍 Detalle por Concepto — {month}")
    if filtered_df.empty:
        st.info("Sin datos para este mes.")
        return

    detail = filtered_df.groupby(["item", "category"])["cost"].sum().reset_index()
    detail = detail.sort_values("cost", ascending=True)

    fig = px.bar(
        detail,
        x="cost",
        y="item",
        color="category",
        orientation="h",
        color_discrete_map=CATEGORY_COLORS,
        labels={"cost": "Coste (€)", "item": "Concepto", "category": "Categoría"},
        text=detail["cost"].apply(lambda v: f"{v:,.2f} €"),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=True,
        margin=dict(t=20, b=40, l=20, r=20),
        yaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)
