"""
auth.py — Autenticación segura con protección anti-fuerza bruta y expiración de sesión.
"""

import streamlit as st
import time

# Configuración de seguridad
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300       # 5 minutos de bloqueo
SESSION_TIMEOUT_SECONDS = 3600  # 1 hora de sesión activa


def _is_locked_out() -> bool:
    """Devuelve True si el usuario está bloqueado temporalmente."""
    lockout_until = st.session_state.get("lockout_until", 0)
    return time.time() < lockout_until


def _seconds_remaining() -> int:
    return max(0, int(st.session_state.get("lockout_until", 0) - time.time()))


def _session_expired() -> bool:
    """Devuelve True si la sesión ha caducado por inactividad."""
    last_active = st.session_state.get("last_active", 0)
    return (time.time() - last_active) > SESSION_TIMEOUT_SECONDS


def refresh_session() -> None:
    """Actualiza el timestamp de actividad. Llamar en cada interacción."""
    st.session_state["last_active"] = time.time()


def logout() -> None:
    """Cierra la sesión del usuario."""
    for key in ("authenticated", "last_active", "session_token"):
        st.session_state.pop(key, None)


def check_password() -> bool:
    """
    Muestra el formulario de login si es necesario.
    Devuelve True sólo cuando el usuario está autenticado y la sesión es válida.
    """
    # Expiración automática por inactividad
    if st.session_state.get("authenticated") and _session_expired():
        logout()
        st.warning("⏱️ Tu sesión ha caducado por inactividad. Por favor, vuelve a iniciar sesión.")

    if st.session_state.get("authenticated"):
        refresh_session()
        return True

    # --- Formulario de login ---
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("## 🔒 Acceso al Panel")
        st.markdown("Introduce tus credenciales para continuar.")
        st.markdown("")

        if _is_locked_out():
            remaining = _seconds_remaining()
            st.error(f"🚫 Cuenta bloqueada. Inténtalo de nuevo en {remaining} segundos.")
            return False

        username = st.text_input("Usuario", key="login_username")
        password = st.text_input("Contraseña", type="password", key="login_password")

        if st.button("Iniciar Sesión", use_container_width=True, type="primary"):
            try:
                valid_user = st.secrets["auth"]["username"]
                valid_pass = st.secrets["auth"]["password"]
            except KeyError:
                st.error("⚠️ Faltan las credenciales en los Secrets de Streamlit.")
                return False

            if username == valid_user and password == valid_pass:
                st.session_state["authenticated"] = True
                st.session_state["last_active"] = time.time()
                st.session_state["failed_attempts"] = 0
                st.session_state.pop("lockout_until", None)
                st.rerun()
            else:
                attempts = st.session_state.get("failed_attempts", 0) + 1
                st.session_state["failed_attempts"] = attempts
                remaining_tries = MAX_FAILED_ATTEMPTS - attempts

                if attempts >= MAX_FAILED_ATTEMPTS:
                    st.session_state["lockout_until"] = time.time() + LOCKOUT_SECONDS
                    st.error(f"🚫 Demasiados intentos fallidos. Bloqueado durante {LOCKOUT_SECONDS // 60} minutos.")
                else:
                    st.error(f"❌ Credenciales incorrectas. Te quedan {remaining_tries} intento(s).")

    return False
