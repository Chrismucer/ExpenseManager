"""
components.py — Componentes reutilizables de la interfaz de usuario.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import MONTHS, CATEGORIES, CONCEPT_PRESETS, UTILITY_ITEMS
from database import save_expense, update_expense, delete_expense


# ---------------------------------------------------------------------------
# SIDEBAR: Añadir gasto
# ---------------------------------------------------------------------------

def sidebar_add_expense(current_year: int, current_month_index: int) -> None:
    """Renderiza el formulario lateral para añadir un nuevo gasto."""
    st.sidebar.header("➕ Añadir Gasto")

    expense_year = st.sidebar.number_input(
        "Año", min_value=2020, max_value=2035, value=current_year
    )
    expense_month = st.sidebar.selectbox(
        "Mes", MONTHS, index=current_month_index
    )
    expense_category = st.sidebar.selectbox("Categoría", CATEGORIES)

    presets = CONCEPT_PRESETS[expense_category]
    selected_preset = st.sidebar.selectbox("Concepto", presets)

    if selected_preset == "Otro (Personalizado)":
        expense_item = st.sidebar.text_input("Concepto personalizado:")
    else:
        expense_item = selected_preset

    is_utility = expense_item in UTILITY_ITEMS
    expense_period = ""
    expense_consumption: float | None = None
    expense_unit_price: float | None = None

    if is_utility:
        st.sidebar.markdown("---")
        st.sidebar.markdown("📅 **Periodo del Suministro**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Inicio", value=datetime.now(), key="add_start")
        with col2:
            end_date = st.date_input("Fin", value=datetime.now(), key="add_end")
        expense_period = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

        st.sidebar.markdown("⚡ **Métricas de Consumo**")
        expense_consumption = st.sidebar.number_input(
            "Consumo (kWh o m³)", min_value=0.0, step=0.1, value=0.0
        )
        expense_unit_price = st.sidebar.number_input(
            "Precio por unidad (€)", min_value=0.0, step=0.001, value=0.0, format="%.4f"
        )
        suggested = round(expense_consumption * expense_unit_price, 2)
        final_cost = st.sidebar.number_input(
            "Coste Total (€)", min_value=0.0, step=0.01, value=suggested
        )
    else:
        final_cost = st.sidebar.number_input(
            "Coste Total (€)", min_value=0.0, step=0.01, value=0.0
        )
        expense_period = expense_month

    st.sidebar.markdown("---")
    if st.sidebar.button("💾 Guardar Gasto", use_container_width=True, type="primary"):
        if not expense_item or expense_item.strip() == "":
            st.sidebar.error("El concepto no puede estar vacío.")
        elif final_cost <= 0:
            st.sidebar.error("El coste debe ser mayor que 0 €.")
        else:
            ok = save_expense(
                year=int(expense_year),
                month=expense_month,
                category=expense_category,
                item=expense_item.strip(),
                period=expense_period,
                consumption=expense_consumption,
                unit_price=expense_unit_price,
                cost=final_cost,
            )
            if ok:
                st.sidebar.success(f"✅ '{expense_item}' guardado con éxito.")
                st.rerun()


# ---------------------------------------------------------------------------
# TAB: Gestión (editar + eliminar)
# ---------------------------------------------------------------------------

def tab_manage(filtered_df: pd.DataFrame) -> None:
    """Renderiza la pestaña de gestión: editar y eliminar registros."""
    if filtered_df.empty:
        st.info("No hay registros en este mes para gestionar.")
        return

    # ---- Eliminar -------------------------------------------------------
    st.markdown("### 🗑️ Eliminar Gasto")
    st.caption("Se usa el ID único de cada registro — nunca se borrará más de un gasto a la vez.")

    # Mapa label → id para el selectbox
    labels = {
        f"[{row['id']}] {row['item']} — {row['cost']:.2f} €": row["id"]
        for _, row in filtered_df.iterrows()
    }
    selected_label = st.selectbox("Selecciona el gasto a eliminar", list(labels.keys()))
    selected_id = labels[selected_label]

    # Botón → confirmación en 2 pasos
    if st.button("🗑️ Eliminar", type="secondary"):
        st.session_state["pending_delete_id"] = selected_id
        st.session_state["pending_delete_label"] = selected_label

    if st.session_state.get("pending_delete_id") == selected_id and "pending_delete_label" in st.session_state:
        st.warning(f"¿Seguro que quieres eliminar **{st.session_state['pending_delete_label']}**?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Sí, eliminar", type="primary"):
                if delete_expense(st.session_state["pending_delete_id"]):
                    st.success("Gasto eliminado correctamente.")
                    st.session_state.pop("pending_delete_id", None)
                    st.session_state.pop("pending_delete_label", None)
                    st.rerun()
        with col_no:
            if st.button("❌ Cancelar"):
                st.session_state.pop("pending_delete_id", None)
                st.session_state.pop("pending_delete_label", None)
                st.rerun()

    st.markdown("---")

    # ---- Editar ---------------------------------------------------------
    st.markdown("### ✏️ Editar Gasto Existente")

    edit_label = st.selectbox(
        "Selecciona el gasto a editar",
        list(labels.keys()),
        key="edit_select",
    )
    edit_id = labels[edit_label]
    row = filtered_df[filtered_df["id"] == edit_id].iloc[0]

    with st.form("edit_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_category = st.selectbox(
                "Categoría",
                CATEGORIES,
                index=CATEGORIES.index(row["category"]) if row["category"] in CATEGORIES else 0,
            )
            new_item = st.text_input("Concepto", value=row["item"])
        with col2:
            new_cost = st.number_input("Coste Total (€)", min_value=0.0, step=0.01, value=float(row["cost"]))
            new_period = st.text_input("Periodo", value=str(row["period"]) if pd.notnull(row["period"]) else "")

        is_utility = row["item"] in UTILITY_ITEMS
        new_consumption: float | None = None
        new_unit_price: float | None = None
        if is_utility:
            col3, col4 = st.columns(2)
            with col3:
                new_consumption = st.number_input(
                    "Consumo (kWh/m³)", min_value=0.0, step=0.1,
                    value=float(row["consumption"]) if pd.notnull(row["consumption"]) else 0.0,
                )
            with col4:
                new_unit_price = st.number_input(
                    "Precio unitario (€)", min_value=0.0, step=0.001, format="%.4f",
                    value=float(row["unit_price"]) if pd.notnull(row["unit_price"]) else 0.0,
                )

        submitted = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
        if submitted:
            if not new_item.strip():
                st.error("El concepto no puede estar vacío.")
            elif new_cost <= 0:
                st.error("El coste debe ser mayor que 0 €.")
            else:
                if update_expense(
                    expense_id=edit_id,
                    category=new_category,
                    item=new_item.strip(),
                    period=new_period,
                    consumption=new_consumption,
                    unit_price=new_unit_price,
                    cost=new_cost,
                ):
                    st.success(f"✅ Gasto actualizado correctamente.")
                    st.rerun()
