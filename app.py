import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Control de Gastos del Hogar", layout="wide", page_icon="💰")

# --- CONEXIÓN A BASE DE DATOS (SQLite Local) ---
# Nota: Para producción en la nube, se cambia por una conexión a PostgreSQL (ej. Supabase)
def init_db():
    conn = sqlite3.connect("gastos_hogar.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano INTEGER,
            mes TEXT,
            categoria TEXT,
            concepto TEXT,
            periodo TEXT,
            consumo REAL,
            precio_unitario REAL,
            coste REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- AUTENTICACIÓN SIMPLE (Profesional para Streamlit) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.subheader("🔒 Acceso al Sistema de Gastos")
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            # Credenciales de ejemplo (Cámbialas o conéctalas a tu DB)
            if user == "admin" and password == "hogar2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        return False
    return True

if check_password():
    # --- PANEL PRINCIPAL ---
    st.title("📊 Panel de Control: Gastos Mensuales del Hogar")
    st.markdown("---")

    # --- SIDERBAR: AÑADIR GASTOS ---
    st.sidebar.header("➕ Añadir Nuevo Gasto")
    
    with st.sidebar.form("form_gasto", clear_on_submit=True):
        ano = st.number_input("Año", min_value=2020, max_value=2035, value=datetime.now().year)
        mes = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        categoria = st.selectbox("Categoría", ["Suministros", "Telecomunicaciones", "Suscripciones", "Alimentación", "Otros"])
        concepto = st.text_input("Concepto (ej. Luz, Netflix, Supermercado)")
        periodo = st.text_input("Periodo (ej. Mayo, 01/05-31/05)")
        
        st.markdown("**Solo para Suministros (Opcional):**")
        consumo = st.number_input("Consumo (kWh o m³)", min_value=0.0, step=0.1, value=0.0)
        precio_unitario = st.number_input("Precio por unidad (€)", min_value=0.0, step=0.001, value=0.0, format="%.4f")
        
        st.markdown("**Coste Fijo o Total:**")
        coste_fijo = st.number_input("Coste Total (€) *Si se calcula por consumo, dejar en 0*", min_value=0.0, step=0.01, value=0.0)
        
        submit = st.form_submit_button("Guardar Gasto")
        
        if submit:
            # Calcular coste si es por consumo
            coste_final = coste_fijo if coste_fijo > 0 else (consumo * precio_unitario)
            
            if concepto == "":
                st.sidebar.error("El concepto es obligatorio")
            elif coste_final == 0:
                st.sidebar.error("El coste debe ser mayor que 0")
            else:
                conn = sqlite3.connect("gastos_hogar.db")
                c = conn.cursor()
                c.execute('''
                    INSERT INTO gastos (ano, mes, categoria, concepto, periodo, consumo, precio_unitario, coste)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ano, mes, categoria, concepto, periodo, consumo if consumo > 0 else None, precio_unitario if precio_unitario > 0 else None, coste_final))
                conn.commit()
                conn.close()
                st.sidebar.success("¡Gasto guardado correctamente!")
                st.rerun()

    # --- OBTENCIÓN DE DATOS ---
    conn = sqlite3.connect("gastos_hogar.db")
    df = pd.read_sql_query("SELECT * FROM gastos", conn)
    conn.close()

    if df.empty:
        st.info("Aún no hay gastos registrados. Utiliza el menú de la izquierda para añadir el primero.")
    else:
        # --- FILTROS GLOBALES ---
        st.subheader("🔍 Filtros de Visualización")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            anos_disponibles = sorted(df["ano"].unique())
            ano_sel = st.selectbox("Selecciona el Año", anos_disponibles, index=len(anos_disponibles)-1)
        with col_f2:
            meses_disponibles = df[df["ano"] == ano_sel]["mes"].unique()
            mes_sel = st.selectbox("Selecciona el Mes", meses_disponibles)

        # Filtrar DataFrame
        df_filtrado = df[(df["ano"] == ano_sel) & (df["mes"] == mes_sel)]
        df_ano = df[df["ano"] == ano_sel]

        # --- KPI METRICS ---
        st.markdown("### 📈 Resumen Financiero")
        kpi1, kpi2, kpi3 = st.columns(3)
        
        total_mes = df_filtrado["coste"].sum()
        total_ano = df_ano["coste"].sum()
        cat_mas_cara = df_filtrado.groupby("categoria")["coste"].sum().idxmax() if not df_filtrado.empty else "N/A"
        
        kpi1.metric(label=f"Total Gastos ({mes_sel} {ano_sel})", value=f"{total_mes:,.2f} €")
        kpi2.metric(label=f"Total Acumulado Año ({ano_sel})", value=f"{total_ano:,.2f} €")
        kpi3.metric(label="Categoría de Mayor Gasto (Mes)", value=cat_mas_cara)

        st.markdown("---")

        # --- ESTADÍSTICAS Y GRÁFICOS ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown(f"#### 🍰 Distribución por Categoría ({mes_sel})")
            fig_pie = px.pie(df_filtrado, values="coste", names="categoria", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            st.markdown(f"#### 📊 Histórico Mensual del Año ({ano_sel})")
            # Ordenar meses cronológicamente para el gráfico
            orden_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            df_historico = df_ano.groupby(["mes", "categoria"])["coste"].sum().reset_index()
            df_historico["mes"] = pd.Categorical(df_historico["mes"], categories=orden_meses, ordered=True)
            df_historico = df_historico.sort_values("mes")
            
            fig_bar = px.bar(df_historico, x="mes", y="coste", color="categoria", barmode="stack",
                             labels={"mes": "Mes", "coste": "Gastos (€)", "categoria": "Categoría"})
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABLA DE DATOS DETALLADA ---
        st.markdown("---")
        st.markdown(f"#### 📋 Desglose de Gastos de {mes_sel}")
        
        # Formatear tabla para vista profesional
        df_vista = df_filtrado.drop(columns=["id", "ano", "mes"])
        df_vista = df_vista.rename(columns={
            "categoria": "Categoría", "concepto": "Concepto", "periodo": "Periodo",
            "consumo": "Consumo (kWh/m³)", "precio_unitario": "Precio Unitario (€)", "coste": "Coste Total (€)"
        })
        
        st.dataframe(df_vista.style.format({
            "Consumo (kWh/m³)": "{:,.1f}",
            "Precio Unitario (€)": "{:,.4f}",
            "Coste Total (€)": "{:,.2f} €"
        }), use_container_width=True)

        # Opción para borrar un registro
        st.markdown("#### 🗑️ Gestionar Registros")
        registro_borrar = st.selectbox("Selecciona un concepto para eliminar (si es necesario)", df_filtrado["concepto"].unique())
        if st.button("Eliminar Registro"):
            conn = sqlite3.connect("gastos_hogar.db")
            c = conn.cursor()
            c.execute("DELETE FROM gastos WHERE ano=? AND mes=? AND concepto=?", (ano_sel, mes_sel, registro_borrar))
            conn.commit()
            conn.close()
            st.success(f"Registro '{registro_borrar}' eliminado.")
            st.rerun()
