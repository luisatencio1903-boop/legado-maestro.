# ============================================================================
# PROYECTO: SUPER DOCENTE 2.0 (EVOLUCIÓN MODULAR)
# BASADO EN: LEGADO MAESTRO V5.0
# FECHA: Enero 2026
# AUTOR: Luis Atencio (Bachiller Docente)
# INSTITUCIÓN: T.E.L E.R.A.C
#
# DESCRIPCIÓN:
# Plataforma de gestión pedagógica basada en Inteligencia Artificial.
# Incluye: Asistencia Biométrica, Planificación, Evaluación y Gestión de Archivos.
# Estructura: Modular (Vistas, Utils, Cerebros).
# =============================================================================

import streamlit as st
import time

# --- 1. IMPORTAR HERRAMIENTAS Y ESTILOS ---
from utils.visuales import cargar_css
from utils.db import conectar_db, cargar_datos_maestros

# --- 2. IMPORTAR TODAS LAS VISTAS (MÓDULOS) ---
from vistas import login
from vistas import home
from vistas import sidebar
from vistas import asistencia
from vistas import aula_virtual
from vistas import planificador
from vistas import fabrica
from vistas import proyectos
from vistas import ministerial
from vistas import archivo
from vistas import extras

# --- 3. CONFIGURACIÓN INICIAL DE LA PÁGINA ---
st.set_page_config(
    page_title="SUPER DOCENTE 2.0",
    page_icon="🍎",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Cargar Estilos CSS (Visuales)
cargar_css()

# --- 4. GESTIÓN DE MEMORIA (SESSION STATE) ---
# Variables fundamentales para que el sistema no se pierda
if 'auth' not in st.session_state: st.session_state.auth = False
if 'u' not in st.session_state: st.session_state.u = None
if 'pagina_actual' not in st.session_state: st.session_state.pagina_actual = "HOME"

# Variables globales del Aula Virtual para evitar errores al cambiar de pantalla
if 'av_foto1' not in st.session_state: st.session_state.av_foto1 = None
if 'av_foto2' not in st.session_state: st.session_state.av_foto2 = None
if 'av_foto3' not in st.session_state: st.session_state.av_foto3 = None
if 'av_resumen' not in st.session_state: st.session_state.av_resumen = ""
if 'modo_suplencia_activo' not in st.session_state: st.session_state.modo_suplencia_activo = False

# --- 5. CONEXIÓN A LA BASE DE DATOS ---
conn = conectar_db()
if not conn:
    st.stop() # Si no hay internet o falla Google Sheets, se detiene aquí.

# --- 6. RUTEO PRINCIPAL (EL CEREBRO DE NAVEGACIÓN) ---

if not st.session_state.auth:
    # ESCENARIO A: NO ESTÁ LOGUEADO -> MOSTRAR LOGIN
    login.render_login(conn)

else:
    # ESCENARIO B: YA ENTRÓ -> MOSTRAR SISTEMA
    
    # 1. Renderizar Barra Lateral (Siempre visible con créditos)
    sidebar.render_sidebar(conn)
    
    # 2. Router de Páginas (Switch)
    pg = st.session_state.pagina_actual

    if pg == "HOME":
        home.render_home(conn)

    elif pg == "⏱️ Control de Asistencia":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        asistencia.render_asistencia(conn)

    elif pg == "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        aula_virtual.render_aula(conn)

    elif pg == "🧠 PLANIFICADOR INTELIGENTE":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        planificador.render_planificador(conn)

    elif pg == "🏗️ FÁBRICA DE PENSUMS":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        fabrica.render_fabrica(conn)
        
    elif pg == "🏗️ GESTIÓN DE PROYECTOS Y PLANES":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        proyectos.render_proyectos(conn)

    elif pg == "📜 PLANIFICADOR MINISTERIAL":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        ministerial.render_ministerial(conn)

    elif pg == "📂 Mi Archivo Pedagógico":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        archivo.render_archivo(conn)
        
    elif pg == "📊 Registro de Evaluaciones":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        st.info("💡 Tip: Puedes ver y gestionar las evaluaciones en 'Mi Archivo Pedagógico'.")
        archivo.render_archivo(conn)

    # EXTRAS (Mensajes, Ideas, Consultas)
    elif pg in ["🌟 Mensaje Motivacional", "💡 Ideas de Actividades", "❓ Consultas Técnicas"]:
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        extras.render_extras(conn)
    
    # --- PIE DE PÁGINA (FIRMA FINAL) ---
    st.divider()
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption("© 2026 SUPER DOCENTE | Desarrollado por: **Luis Atencio**")
    with c2:
        st.caption("v2.0 Modular")
