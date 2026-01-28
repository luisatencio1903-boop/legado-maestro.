# ============================================================================
# PROYECTO: SUPER DOCENTE V2 (MODULAR)
# AUTOR: Luis Atencio
# FECHA: Enero 2026
# DESCRIPCIÓN: Archivo principal (Orquestador). Carga configuración y enruta.
# ============================================================================

import streamlit as st
import time

# --- 1. CONFIGURACIÓN DE PÁGINA (IGUAL QUE V1) ---
st.set_page_config(
    page_title="SUPER DOCENTE 2.0",
    page_icon="logo_legado.png", # Asegúrate de subir la imagen luego a la carpeta raíz
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. GESTIÓN DE MEMORIA DE SESIÓN (REGLA DE ORO: NO PERDER NADA) ---
# Inicializamos todas las variables que usa tu V1 para que los módulos funcionen.

# Autenticación y Usuario
if 'auth' not in st.session_state: st.session_state.auth = False
if 'u' not in st.session_state: st.session_state.u = None
if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = "HOME"

# Variables del Aula Virtual (V13/V14)
if 'av_foto1' not in st.session_state: st.session_state.av_foto1 = None
if 'av_foto2' not in st.session_state: st.session_state.av_foto2 = None
if 'av_foto3' not in st.session_state: st.session_state.av_foto3 = None
if 'av_resumen' not in st.session_state: st.session_state.av_resumen = ""
if 'modo_suplencia_activo' not in st.session_state: st.session_state.modo_suplencia_activo = False
if 'chat_asistente_aula' not in st.session_state: st.session_state.chat_asistente_aula = []

# Variables del Planificador y Fábrica
if 'plan_actual' not in st.session_state: st.session_state.plan_actual = ""
if 'fp_completo' not in st.session_state: st.session_state.fp_completo = ""

# --- 3. IMPORTACIÓN DE MÓDULOS (LA ESTRATEGIA MODULAR) ---
# Intentamos importar. Si fallan es porque aun no creas los archivos (Es normal ahora).
try:
    from utils.db import conectar_db
    from utils.visuales import cargar_css
    from vistas.login import render_login
    from vistas.sidebar import render_sidebar
    from vistas.home import render_home
    # Aquí iremos añadiendo: from vistas.aula import render_aula, etc.
    
    modulos_ok = True
except ImportError:
    modulos_ok = False

# --- 4. EJECUCIÓN PRINCIPAL ---
def main():
    # A. Cargar Estilos CSS (Tu diseño visual exacto)
    if modulos_ok:
        cargar_css() # Esto cargará tu estilo azul/verde original
        conn = conectar_db()
    else:
        st.warning("⚠️ **ESTRUCTURA EN CONSTRUCCIÓN**")
        st.info("Has creado el 'app.py' correctamente. Ahora debes crear las carpetas 'utils' y 'vistas' para que el sistema arranque.")
        return

    # B. Lógica de Navegación (Igual que V1)
    if not st.session_state.auth:
        render_login(conn)
    else:
        # Renderizar la Barra Lateral (Con tu logo y datos)
        render_sidebar(conn)

        # Enrutador (El Switch gigante de tu V1, pero ordenado)
        if st.session_state.pagina_actual == "HOME":
            render_home(conn)
        
        # Aquí conectaremos los demás módulos paso a paso:
        elif st.session_state.pagina_actual == "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)":
             from vistas.aula_virtual import render_aula
             render_aula(conn)
             
        elif st.session_state.pagina_actual == "📂 Mi Archivo Pedagógico":
             from vistas.archivo import render_archivo
             render_archivo(conn)
             
        # ... y así con el resto ...

if __name__ == "__main__":
    main()
