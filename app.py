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
        # Cambio 3: Texto de acceso
        st.subheader("🔒 Acceso")
        input_username = st.text_input("Usuario")
        input_password = st.text_input("Contraseña", type="password")
        
        if st.button("Iniciar Sesión"):
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
    # --- GET CURRENT DATE FOR AUTOMATIC SELECTION ---
    current_time = datetime.now()
    current_year = current_time.year
    current_month_index = current_time.month - 1  # Jan is 1, so index is 0
    
    months_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    # --- MAIN DASHBOARD ---
    # Cambio 2: Título principal
    st.title("📊 Panel de Control: Gastos Mensuales")
    st.markdown("---")

    # --- SIDEBAR: DYNAMIC EXPENSE INPUT ---
    st.sidebar.header("➕ Añadir Nuevo Gasto")
    
    expense_year = st.sidebar.number_input("Año", min_value=2020, max_value=2035, value=current_year)
    expense_month = st.sidebar.selectbox("Mes", months_list, index=current_month_index)
    
    expense_category = st.sidebar.selectbox("Categoría", ["Suministros", "Telecomunicaciones", "Suscripciones", "Alimentación", "Otros"])
    
    concept_presets = {
        "Suministros": ["Luz", "Agua", "Gas", "Otro (Personalizado)"],
        "Telecomunicaciones": ["Internet/Móvil", "Teléfono Fijo", "Otro (Personalizado)"],
        "Suscripciones": ["Netflix", "Amazon Prime", "Spotify", "Disney+", "HBO Max", "Otro (Personalizado)"],
        "Alimentación": ["Supermercado", "Restaurantes", "Otro (Personalizado)"],
        "Otros": ["Varios", "Otro (Personalizado)"]
    }
    
    selected_preset = st.sidebar.selectbox("Concepto", concept_presets[expense_category])
    
    if selected_preset == "Otro (Personalizado)":
        expense_item = st.sidebar.text_input("Escribe el concepto personalizado:")
    else:
        expense_item = selected_preset

    is_utility = expense_item in ["Luz", "Agua", "Gas"]
    
    expense_period = ""
    expense_consumption = 0.0
    expense_unit_price = 0.0
    fixed_cost = 0.0

    if is_utility:
        st.sidebar.markdown("---")
        st.sidebar.markdown("📅 **Periodo del Suministro**")
        col_date1, col_date2 = st.sidebar.columns(2)
        with col_date1:
            start_date = st.date_input("Inicio", value=current_time)
        with col_date2:
            end_date = st.date_input("Fin", value=current_time)
        
        expense_period = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        st.sidebar.markdown("⚡ **Métricas de Consumo**")
        expense_consumption = st.sidebar.number_input("Consumo (kWh o m³)", min_value=0.0, step=0.1, value=0.0)
        expense_unit_price = st.sidebar.number_input("Precio por unidad (€)", min_value=0.0, step=0.001, value=0.0, format="%.4f")
        
        calculated_utility_cost = expense_consumption * expense_unit_price
        final_cost = st.sidebar.number_input("Coste Total (€)", min_value=0.0, step=0.01, value=calculated_utility_cost)
    else:
        final_cost = st.sidebar.number_input("Coste Total (€)", min_value=0.0, step=0.01, value=0.0)
        expense_period = expense_month

    save_button = st.sidebar.button("Guardar Gasto", use_container_width=True)
    
    if save_button:
        if expense_item.strip() == "":
            st.sidebar.error("El concepto no puede estar vacío.")
        elif final_cost <= 0:
            st.sidebar.error("El coste debe ser mayor que 0 €.")
        else:
            with conn.session as session:
                session.execute(
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
                session.commit()
            st.sidebar.success(f"¡{expense_item} guardado con éxito!")
            st.rerun()

    # --- DATA RETRIEVAL ---
    try:
        df = conn.query("SELECT * FROM expenses", ttl=0)
    except Exception as database_error:
        st.error(f"Error conectando a la base de datos: {database_error}")
        st.stop()

    if df.empty:
        st.info("Aún no hay gastos registrados. Utiliza el menú de la izquierda para añadir el primero.")
    else:
        # --- GLOBAL FILTERS ---
        st.subheader("🔍 Filtros de Visualización")
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            available_years = sorted(df["year"].unique())
            default_year_index = available_years.index(current_year) if current_year in available_years else len(available_years) - 1
            selected_year = st.selectbox("Selecciona el Año", available_years, index=default_year_index)
            
        with col_filter2:
            available_months = df[df["year"] == selected_year]["month"].unique()
            default_month_name = months_list[current_month_index]
            default_month_index = list(available_months).index(default_month_name) if default_month_name in available_months else 0
            selected_month = st.selectbox("Selecciona el Mes", available_months, index=default_month_index)

        filtered_df = df[(df["year"] == selected_year) & (df["month"] == selected_month)]
        year_df = df[df["year"] == selected_year]

        # --- KPI METRICS ---
        st.markdown("### 📈 Resumen Financiero")
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        monthly_total = filtered_df["cost"].sum()
        yearly_total = year_df["cost"].sum()
        most_expensive_category = filtered_df.groupby("category")["cost"].sum().idxmax() if not filtered_df.empty else "N/A"
        
        kpi_col1.metric(label=f"Total Gastos ({selected_month} {selected_year})", value=f"{monthly_total:,.2f} €")
        kpi_col2.metric(label=f"Total Acumulado Año ({selected_year})", value=f"{yearly_total:,.2f} €")
        kpi_col3.metric(label="Categoría de Mayor Gasto (Mes)", value=most_expensive_category)

        st.markdown("---")

        # --- STATISTICS AND CHARTS ---
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown(f"#### 🍰 Distribución por Categoría ({selected_month})")
            if not filtered_df.empty:
                pie_chart = px.pie(filtered_df, values="cost", names="category", hole=0.4,
                                 color_discrete_sequence=px.colors.sequential.RdBu)
                pie_chart.update_traces(textinfo="percent+label")
                st.plotly_chart(pie_chart, use_container_width=True)
            else:
                st.info("No hay datos para mostrar gráficos en este mes.")

        with chart_col2:
            st.markdown(f"#### 📊 Histórico Mensual del Año ({selected_year})")
            if not year_df.empty:
                historical_df = year_df.groupby(["month", "category"])["cost"].sum().reset_index()
                historical_df["month"] = pd.Categorical(historical_df["month"], categories=months_list, ordered=True)
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
                "Consumo (kWh/m³)": lambda val: f"{val:,.1f}" if pd.notnull(val) else "-",
                "Precio Unitario (€)": lambda val: f"{val:,.4f}" if pd.notnull(val) else "-",
                "Coste Total (€)": lambda val: f"{val:,.2f} €" if pd.notnull(val) else "0.00 €"
            }), use_container_width=True)

            # --- DELETE RECORDS ---
            st.markdown("#### 🗑️ Gestionar Registros")
            record_to_delete = st.selectbox("Selecciona un concepto para eliminar (si es necesario)", filtered_df["item"].unique())
            
            # Cambio 1: Nombre del botón
            if st.button("Eliminar Gasto"):
                with conn.session as session:
                    # Corrección técnica: Convertir los datos a formatos de Python nativos (int y str)
                    session.execute(
                        text("DELETE FROM expenses WHERE year=:year AND month=:month AND item=:item"),
                        {
                            "year": int(selected_year), 
                            "month": str(selected_month), 
                            "item": str(record_to_delete)
                        }
                    )
                    session.commit()
                st.success(f"Gasto '{record_to_delete}' eliminado correctamente.")
                st.rerun()
        else:
             st.info("No hay registros detallados en este mes.")
