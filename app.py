import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Control de Gastos del Hogar", layout="wide", page_icon="💰")

# --- DATABASE CONNECTION (Supabase via Streamlit) ---
conn = st.connection("supabase", type="sql")

# --- SECURE AUTHENTICATION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.subheader("🔒 Acceso")
        input_username = st.text_input("Usuario")
        input_password = st.text_input("Contraseña", type="password")

        if st.button("Iniciar Sesión"):
            # Reading credentials securely from Streamlit Cloud Secrets
            try:
                valid_username = st.secrets["auth"]["username"]
                valid_password = st.secrets["auth"]["password"]

                if input_username == valid_username and input_password == valid_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except KeyError:
                st.error("⚠️ Error de configuración: Faltan las credenciales en los Secrets de Streamlit.")
        return False
    return True

if check_password():
    # --- MAIN DASHBOARD ---
    st.title("📊 Gastos Mensuales")
    st.markdown("---")

    # --- SIDEBAR: ADD EXPENSES ---
    st.sidebar.header("➕ Añadir gasto")

    with st.sidebar.form("expense_form", clear_on_submit=True):
        expense_year = st.number_input("Año", min_value=2020, max_value=2035, value=datetime.now().year)
        expense_month = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        expense_category = st.selectbox("Categoría", ["Suministros", "Telecomunicaciones", "Suscripciones", "Alimentación", "Otros"])
        expense_item = st.text_input("Concepto (ej. Luz, Netflix, Supermercado)")
        expense_period = st.text_input("Periodo (ej. Mayo, 01/05-31/05)")

        st.markdown("**Solo para Suministros (Opcional):**")
        expense_consumption = st.number_input("Consumo (kWh o m³)", min_value=0.0, step=0.1, value=0.0)
        expense_unit_price = st.number_input("Precio por unidad (€)", min_value=0.0, step=0.001, value=0.0, format="%.4f")
        
        st.markdown("**Coste Fijo o Total:**")
        fixed_cost = st.number_input("Coste Total (€) *Si se calcula por consumo, dejar en 0*", min_value=0.0, step=0.01, value=0.0)
        
        submit_button = st.form_submit_button("Guardar Gasto")
        
        if submit_button:
            final_cost = fixed_cost if fixed_cost > 0 else (expense_consumption * expense_unit_price)
            
            if expense_item == "":
                st.sidebar.error("El concepto es obligatorio")
            elif final_cost == 0:
                st.sidebar.error("El coste debe ser mayor que 0")
            else:
                # Insert into Supabase
                with conn.session as s:
                    s.execute(
                        text("""
                            INSERT INTO expenses (year, month, category, item, period, consumption, unit_price, cost)
                            VALUES (:year, :month, :category, :item, :period, :consumption, :unit_price, :cost)
                        """),
                        {
                            "year": expense_year, "month": expense_month, "category": expense_category, 
                            "item": expense_item, "period": expense_period, 
                            "consumption": expense_consumption if expense_consumption > 0 else None, 
                            "unit_price": expense_unit_price if expense_unit_price > 0 else None, 
                            "cost": final_cost
                        }
                    )
                    s.commit()
                st.sidebar.success("¡Gasto guardado correctamente!")
                st.rerun()

    # --- DATA RETRIEVAL ---
    # ttl=0 ensures it always fetches fresh data from the database
    try:
        df = conn.query("SELECT * FROM expenses", ttl=0)
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        st.stop()

    if df.empty:
        st.info("Aún no hay gastos registrados. Utiliza el menú de la izquierda para añadir el primero.")
    else:
        # --- GLOBAL FILTERS ---
        st.subheader("🔍 Filtros de Visualización")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            available_years = sorted(df["year"].unique())
            selected_year = st.selectbox("Selecciona el Año", available_years, index=len(available_years)-1)
        with col_f2:
            available_months = df[df["year"] == selected_year]["month"].unique()
            selected_month = st.selectbox("Selecciona el Mes", available_months)

        filtered_df = df[(df["year"] == selected_year) & (df["month"] == selected_month)]
        year_df = df[df["year"] == selected_year]

        # --- KPI METRICS ---
        st.markdown("### 📈 Resumen Financiero")
        kpi1, kpi2, kpi3 = st.columns(3)
        
        monthly_total = filtered_df["cost"].sum()
        yearly_total = year_df["cost"].sum()
        most_expensive_category = filtered_df.groupby("category")["cost"].sum().idxmax() if not filtered_df.empty else "N/A"
        
        kpi1.metric(label=f"Total Gastos ({selected_month} {selected_year})", value=f"{monthly_total:,.2f} €")
        kpi2.metric(label=f"Total Acumulado Año ({selected_year})", value=f"{yearly_total:,.2f} €")
        kpi3.metric(label="Categoría de Mayor Gasto (Mes)", value=most_expensive_category)

        st.markdown("---")

        # --- STATISTICS AND CHARTS ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown(f"#### 🍰 Distribución por Categoría ({selected_month})")
            if not filtered_df.empty:
                pie_chart = px.pie(filtered_df, values="cost", names="category", hole=0.4,
                                 color_discrete_sequence=px.colors.sequential.RdBu)
                pie_chart.update_traces(textinfo="percent+label")
                st.plotly_chart(pie_chart, use_container_width=True)
            else:
                st.info("No hay datos para mostrar gráficos en este mes.")

        with col_g2:
            st.markdown(f"#### 📊 Histórico Mensual del Año ({selected_year})")
            if not year_df.empty:
                month_order = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                historical_df = year_df.groupby(["month", "category"])["cost"].sum().reset_index()
                historical_df["month"] = pd.Categorical(historical_df["month"], categories=month_order, ordered=True)
                historical_df = historical_df.sort_values("month")
                
                bar_chart = px.bar(historical_df, x="month", y="cost", color="category", barmode="stack",
                                 labels={"month": "Mes", "cost": "Gastos (€)", "category": "Categoría"})
                st.plotly_chart(bar_chart, use_container_width=True)
            else:
                st.info("No hay datos históricos para este año.")

        # --- DETAILED DATA TABLE ---
        st.markdown("---")
        st.markdown(f"#### 📋 Desglose de Gastos de {selected_month}")
        
        if not filtered_df.empty:
            display_df = filtered_df.drop(columns=["id", "year", "month"])
            display_df = display_df.rename(columns={
                "category": "Categoría", 
                "item": "Concepto", 
                "period": "Periodo",
                "consumption": "Consumo (kWh/m³)", 
                "unit_price": "Precio Unitario (€)", 
                "cost": "Coste Total (€)"
            })
            
            st.dataframe(display_df.style.format({
                "Consumo (kWh/m³)": "{:,.1f}",
                "Precio Unitario (€)": "{:,.4f}",
                "Coste Total (€)": "{:,.2f} €"
            }), use_container_width=True)

            # --- DELETE RECORDS ---
            st.markdown("#### 🗑️ Gestionar Registros")
            record_to_delete = st.selectbox("Selecciona un concepto para eliminar (si es necesario)", filtered_df["item"].unique())
            
            if st.button("Eliminar Registro"):
                with conn.session as s:
                    s.execute(
                        text("DELETE FROM expenses WHERE year=:year AND month=:month AND item=:item"),
                        {"year": selected_year, "month": selected_month, "item": record_to_delete}
                    )
                    s.commit()
                st.success(f"Registro '{record_to_delete}' eliminado.")
                st.rerun()
        else:
             st.info("No hay registros detallados en este mes.")
