"""
charts.py — Todas las visualizaciones con Plotly.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import MONTHS, CATEGORY_COLORS


def chart_pie(filtered_df: pd.DataFrame, month: str) -> None:
    st.markdown(f"#### 🍰 Por Categoría — {month}")
    if filtered_df.empty:
        st.info("Sin datos para este mes.")
        return
    fig = px.pie(
        filtered_df, values="cost", names="category", hole=0.42,
        color="category", color_discrete_map=CATEGORY_COLORS,
    )
    fig.update_traces(textinfo="percent+label", pull=[0.03] * len(filtered_df))
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)


def chart_bar_historical(year_df: pd.DataFrame, year: int) -> None:
    st.markdown(f"#### 📊 Histórico — {year}")
    if year_df.empty:
        st.info("Sin datos para este año.")
        return
    historical = year_df.groupby(["month", "category"])["cost"].sum().reset_index()
    historical["month"] = pd.Categorical(historical["month"], categories=MONTHS, ordered=True)
    historical = historical.sort_values("month")
    fig = px.bar(
        historical, x="month", y="cost", color="category", barmode="stack",
        color_discrete_map=CATEGORY_COLORS,
        labels={"month": "Mes", "cost": "Gastos (€)", "category": "Categoría"},
    )
    fig.update_layout(margin=dict(t=20, b=40, l=20, r=20), legend_title_text="Categoría")
    st.plotly_chart(fig, use_container_width=True)


def chart_trend_line(year_df: pd.DataFrame, year: int, budgets_df: pd.DataFrame | None = None) -> None:
    st.markdown(f"#### 📈 Tendencia — {year}")
    if year_df.empty:
        st.info("Sin datos para este año.")
        return

    monthly_totals = year_df.groupby("month")["cost"].sum().reset_index()
    monthly_totals["month"] = pd.Categorical(monthly_totals["month"], categories=MONTHS, ordered=True)
    monthly_totals = monthly_totals.sort_values("month")

    fig = go.Figure()

    # Línea de gasto real
    fig.add_trace(go.Scatter(
        x=monthly_totals["month"],
        y=monthly_totals["cost"],
        name="Gasto real",
        mode="lines+markers+text",
        text=[f"{v:,.0f} €" for v in monthly_totals["cost"]],
        textposition="top center",
        line=dict(color="#3B82F6", width=2.5),
        marker=dict(size=8, color="#3B82F6"),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.08)",
    ))

    # Línea de presupuesto (si existe)
    if budgets_df is not None and not budgets_df.empty:
        budget_year = budgets_df[budgets_df["year"] == year].copy()
        if not budget_year.empty:
            budget_year["month"] = pd.Categorical(budget_year["month"], categories=MONTHS, ordered=True)
            budget_year = budget_year.sort_values("month")
            fig.add_trace(go.Scatter(
                x=budget_year["month"],
                y=budget_year["amount"],
                name="Presupuesto",
                mode="lines+markers",
                line=dict(color="#10B981", width=2, dash="dash"),
                marker=dict(size=6, color="#10B981"),
            ))

    fig.update_layout(
        xaxis_title="Mes", yaxis_title="€",
        margin=dict(t=20, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_category_detail(filtered_df: pd.DataFrame, month: str) -> None:
    st.markdown(f"#### 🔍 Por Concepto — {month}")
    if filtered_df.empty:
        st.info("Sin datos para este mes.")
        return
    detail = filtered_df.groupby(["item", "category"])["cost"].sum().reset_index()
    detail = detail.sort_values("cost", ascending=True)
    fig = px.bar(
        detail, x="cost", y="item", color="category", orientation="h",
        color_discrete_map=CATEGORY_COLORS,
        labels={"cost": "Coste (€)", "item": "Concepto", "category": "Categoría"},
        text=detail["cost"].apply(lambda v: f"{v:,.2f} €"),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=True, margin=dict(t=20, b=40, l=20, r=20),
        yaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)


def chart_budget_gauge(monthly_total: float, budget: float, month: str) -> None:
    """Gauge que muestra % consumido del presupuesto mensual."""
    st.markdown(f"#### 🎯 Presupuesto — {month}")
    remaining = budget - monthly_total
    pct = min(monthly_total / budget * 100, 100) if budget > 0 else 0
    color = "#10B981" if pct < 75 else "#F59E0B" if pct < 90 else "#EF4444"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=monthly_total,
        delta={"reference": budget, "valueformat": ".2f", "suffix": " €",
               "decreasing": {"color": "#10B981"}, "increasing": {"color": "#EF4444"}},
        number={"suffix": " €", "valueformat": ",.2f"},
        title={"text": f"Gastado de {budget:,.2f} €<br><span style='font-size:0.85em;color:{'#10B981' if remaining>=0 else '#EF4444'}'>"
                       f"{'Quedan' if remaining >= 0 else 'Excedido en'} {abs(remaining):,.2f} €</span>"},
        gauge={
            "axis": {"range": [0, budget], "tickformat": ",.0f"},
            "bar": {"color": color},
            "bgcolor": "#1e2530",
            "bordercolor": "#374151",
            "steps": [
                {"range": [0, budget * 0.75], "color": "rgba(16,185,129,0.1)"},
                {"range": [budget * 0.75, budget * 0.90], "color": "rgba(245,158,11,0.1)"},
                {"range": [budget * 0.90, budget], "color": "rgba(239,68,68,0.1)"},
            ],
            "threshold": {"line": {"color": "#EF4444", "width": 3}, "value": budget},
        },
    ))
    fig.update_layout(margin=dict(t=60, b=20, l=30, r=30), height=280,
                      paper_bgcolor="rgba(0,0,0,0)", font_color="#ffffff")
    st.plotly_chart(fig, use_container_width=True)
