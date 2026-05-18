"""
config.py — Constantes, listas y configuración de la aplicación.
Modificar aquí para cambiar categorías, conceptos, etc. sin tocar la lógica.
"""

MONTHS: list[str] = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

CATEGORIES: list[str] = [
    "Suministros",
    "Telecomunicaciones",
    "Suscripciones",
    "Alimentación",
    "Transporte",
    "Salud",
    "Ocio",
    "Otros",
]

CONCEPT_PRESETS: dict[str, list[str]] = {
    "Suministros": ["Luz", "Agua", "Gas", "Otro (Personalizado)"],
    "Telecomunicaciones": ["Internet/Móvil", "Teléfono Fijo", "Otro (Personalizado)"],
    "Suscripciones": ["Netflix", "Amazon Prime", "Spotify", "Disney+", "HBO Max", "Otro (Personalizado)"],
    "Alimentación": ["Supermercado", "Restaurantes", "Mercado", "Otro (Personalizado)"],
    "Transporte": ["Gasolina", "Transporte Público", "Parking", "Otro (Personalizado)"],
    "Salud": ["Farmacia", "Médico", "Seguro Médico", "Otro (Personalizado)"],
    "Ocio": ["Cine/Teatro", "Viajes", "Deporte", "Otro (Personalizado)"],
    "Otros": ["Varios", "Otro (Personalizado)"],
}

# Conceptos que requieren campos extra (periodo, consumo, precio unitario)
UTILITY_ITEMS: set[str] = {"Luz", "Agua", "Gas"}

# Colores por categoría (para gráficos)
CATEGORY_COLORS: dict[str, str] = {
    "Suministros":       "#EF4444",
    "Telecomunicaciones": "#3B82F6",
    "Suscripciones":     "#8B5CF6",
    "Alimentación":      "#10B981",
    "Transporte":        "#F59E0B",
    "Salud":             "#EC4899",
    "Ocio":              "#06B6D4",
    "Otros":             "#6B7280",
}
