"""
database.py — Capa de acceso a datos.
Todas las operaciones con Supabase viven aquí.

Tablas:
  expenses   → gastos
  budgets    → presupuestos mensuales (year, month, amount)
"""

import streamlit as st
import pandas as pd
from sqlalchemy import text


# ---------------------------------------------------------------------------
# Gastos
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def load_expenses() -> pd.DataFrame:
    conn = st.connection("supabase", type="sql")
    try:
        df = conn.query("SELECT * FROM expenses ORDER BY year DESC, id DESC", ttl=0)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        st.stop()


def save_expense(year: int, month: str, category: str, item: str,
                 period: str, consumption: float | None,
                 unit_price: float | None, cost: float) -> bool:
    conn = st.connection("supabase", type="sql")
    try:
        with conn.session as session:
            session.execute(
                text("""
                    INSERT INTO expenses
                        (year, month, category, item, period, consumption, unit_price, cost)
                    VALUES
                        (:year, :month, :category, :item, :period, :consumption, :unit_price, :cost)
                """),
                {
                    "year": year, "month": month, "category": category,
                    "item": item, "period": period,
                    "consumption": consumption if consumption and consumption > 0 else None,
                    "unit_price": unit_price if unit_price and unit_price > 0 else None,
                    "cost": cost,
                },
            )
            session.commit()
        load_expenses.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar el gasto: {e}")
        return False


def update_expense(expense_id: int, category: str, item: str,
                   period: str, consumption: float | None,
                   unit_price: float | None, cost: float) -> bool:
    conn = st.connection("supabase", type="sql")
    try:
        with conn.session as session:
            session.execute(
                text("""
                    UPDATE expenses
                    SET category    = :category,
                        item        = :item,
                        period      = :period,
                        consumption = :consumption,
                        unit_price  = :unit_price,
                        cost        = :cost
                    WHERE id = :id
                """),
                {
                    "id": int(expense_id), "category": category, "item": item,
                    "period": period,
                    "consumption": consumption if consumption and consumption > 0 else None,
                    "unit_price": unit_price if unit_price and unit_price > 0 else None,
                    "cost": cost,
                },
            )
            session.commit()
        load_expenses.clear()
        return True
    except Exception as e:
        st.error(f"Error al actualizar el gasto: {e}")
        return False


def delete_expense(expense_id: int) -> bool:
    conn = st.connection("supabase", type="sql")
    try:
        with conn.session as session:
            session.execute(
                text("DELETE FROM expenses WHERE id = :id"),
                {"id": int(expense_id)},
            )
            session.commit()
        load_expenses.clear()
        return True
    except Exception as e:
        st.error(f"Error al eliminar el gasto: {e}")
        return False


# ---------------------------------------------------------------------------
# Presupuestos
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def load_budgets() -> pd.DataFrame:
    """Carga todos los presupuestos mensuales."""
    conn = st.connection("supabase", type="sql")
    try:
        df = conn.query("SELECT * FROM budgets", ttl=0)
        return df
    except Exception as e:
        # Si la tabla no existe aún devolvemos DataFrame vacío
        return pd.DataFrame(columns=["year", "month", "amount"])


def get_budget(year: int, month: str) -> float | None:
    """Devuelve el presupuesto de un mes concreto, o None si no existe."""
    df = load_budgets()
    if df.empty:
        return None
    row = df[(df["year"] == year) & (df["month"] == month)]
    if row.empty:
        return None
    return float(row.iloc[0]["amount"])


def save_budget(year: int, month: str, amount: float) -> bool:
    """Inserta o actualiza el presupuesto de un mes (upsert)."""
    conn = st.connection("supabase", type="sql")
    try:
        with conn.session as session:
            session.execute(
                text("""
                    INSERT INTO budgets (year, month, amount)
                    VALUES (:year, :month, :amount)
                    ON CONFLICT (year, month)
                    DO UPDATE SET amount = EXCLUDED.amount
                """),
                {"year": year, "month": month, "amount": amount},
            )
            session.commit()
        load_budgets.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar el presupuesto: {e}")
        return False
