# ExpenseManager

# 💰 Control de Gastos del Hogar

Panel de control para gestionar gastos mensuales del hogar, construido con **Streamlit** y **Supabase**.

---

## 📁 Estructura del Proyecto

```
ExpenseManager/
├── app.py           → Punto de entrada principal
├── auth.py          → Autenticación segura
├── database.py      → Capa de acceso a datos (Supabase)
├── config.py        → Categorías, meses, colores, etc.
├── components.py    → Componentes de UI (sidebar, gestión)
├── charts.py        → Visualizaciones Plotly
├── requirements.txt → Dependencias Python
└── README.md        → Este archivo
```

---

## 🚀 Instalación y Configuración

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar Secrets de Streamlit

Crea el archivo `.streamlit/secrets.toml` con:

```toml
[connections.supabase]
url = "postgresql://..."     # URL de conexión de Supabase

[auth]
username = "tu_usuario"
password = "tu_contraseña_segura"
```

### 3. Crear la tabla en Supabase

Ejecuta este SQL en el editor de Supabase:

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id          SERIAL PRIMARY KEY,
    year        INTEGER        NOT NULL,
    month       TEXT           NOT NULL,
    category    TEXT           NOT NULL,
    item        TEXT           NOT NULL,
    period      TEXT,
    consumption NUMERIC(10, 3),
    unit_price  NUMERIC(10, 4),
    cost        NUMERIC(10, 2) NOT NULL,
    created_at  TIMESTAMPTZ    DEFAULT NOW()
);
```

### 4. Ejecutar la aplicación
```bash
streamlit run app.py
```

---

## 🔐 Seguridad

| Mejora | Detalle |
|---|---|
| Bloqueo por intentos fallidos | Bloqueado 5 min tras 5 intentos incorrectos |
| Expiración de sesión | Sesión caduca tras 1 hora de inactividad |
| Borrado por ID único | `DELETE` siempre usa el `id` — nunca borra registros duplicados por error |
| Confirmación antes de borrar | Diálogo de 2 pasos para evitar borrados accidentales |

---

## ✨ Funcionalidades

- ➕ **Añadir gastos** con soporte para suministros (consumo + precio/unidad)
- ✏️ **Editar gastos** existentes directamente desde la pestaña de gestión
- 🗑️ **Eliminar** con confirmación en 2 pasos (usando ID único)
- 📊 **4 gráficos**: donut por categoría, barras históricas, línea de tendencia, detalle por concepto
- 📈 **KPIs** con delta vs mes anterior
- ⬇️ **Exportar CSV** de cualquier mes filtrado
- 🔄 **Refresco manual** de datos para no saturar la BD
- 🚪 **Cerrar sesión** desde el sidebar

---

## 🛠️ Personalización

Para añadir/quitar categorías o conceptos, edita únicamente **`config.py`** — no hace falta tocar ningún otro archivo.
