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
# Actualización: Sistema de Resiliencia Local (Maletín de Campo - Paso 3).
# =============================================================================

import streamlit as st
import time

# --- 1. IMPORTAR HERRAMIENTAS Y ESTILOS ---
from utils.visuales import cargar_css
from utils.db import conectar_db, cargar_datos_maestros
# NUEVAS HERRAMIENTAS PARA EL MALETÍN (PASO 3)
from utils.maletin import inicializar_maletin, recuperar_del_dispositivo, persistir_en_dispositivo

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
    page_title="SUPER DOCENTE 1.0",
    page_icon="🍎",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Cargar Estilos CSS (Visuales preservados)
cargar_css()

# =============================================================================
# 4. GESTIÓN DE MEMORIA Y RESILIENCIA (SESSION STATE + LOCAL STORAGE)
# =============================================================================

# A. Inicializamos variables de sesión estándar (Lógica Original v5.0)
if 'auth' not in st.session_state: 
    st.session_state.auth = False
    
if 'u' not in st.session_state: 
    st.session_state.u = None
    
if 'pagina_actual' not in st.session_state: 
    st.session_state.pagina_actual = "HOME"

# Variables globales del Aula Virtual para evitar errores al cambiar de pantalla
if 'av_foto1' not in st.session_state: 
    st.session_state.av_foto1 = None
    
if 'av_foto2' not in st.session_state: 
    st.session_state.av_foto2 = None
    
if 'av_foto3' not in st.session_state: 
    st.session_state.av_foto3 = None
    
if 'av_resumen' not in st.session_state: 
    st.session_state.av_resumen = ""
    
if 'modo_suplencia_activo' not in st.session_state: 
    st.session_state.modo_suplencia_activo = False

# B. LÓGICA DE RECUPERACIÓN (EL "ESCUDO" CONTRA EL RESETEO DEL NAVEGADOR)
# Intentamos recuperar el "Maletín de Campo" desde el disco duro del teléfono/PC
try:
    # Esta función busca si hay algo guardado físicamente en el navegador
    datos_recuperados = recuperar_del_dispositivo("maletin_super_docente")
    
    if datos_recuperados:
        # Si el navegador se cerró por culpa de WhatsApp, restauramos los datos
        for clave, valor in datos_recuperados.items():
            # Solo restauramos si la sesión actual está vacía para no sobreescribir
            if clave in st.session_state:
                if st.session_state[clave] is None or st.session_state[clave] == "":
                    st.session_state[clave] = valor
                    
        # Aviso visual para el docente
        st.toast("🔄 Sesión recuperada desde el dispositivo", icon="📱")
except Exception as e:
    # Si falla la recuperación, el sistema continúa limpio
    pass

# =============================================================================
# 5. CONEXIÓN A LA BASE DE DATOS
# =============================================================================
conn = conectar_db()
if not conn:
    st.error("⚠️ Error de conexión: El sistema requiere acceso a Google Sheets.")
    st.stop()

# =============================================================================
# 6. RUTEO PRINCIPAL (EL CEREBRO DE NAVEGACIÓN)
# =============================================================================

if not st.session_state.auth:
    # ESCENARIO A: NO ESTÁ LOGUEADO -> MOSTRAR PANTALLA DE LOGIN
    login.render_login(conn)

else:
    # ESCENARIO B: YA ENTRÓ -> MOSTRAR INTERFAZ DEL SISTEMA
    
    # 1. Renderizar Barra Lateral (Créditos y Planificación Activa)
    sidebar.render_sidebar(conn)
    
    # 2. Router de Páginas (Switch Central)
    # Obtenemos la página desde la memoria de sesión
    pg = st.session_state.pagina_actual

    if pg == "HOME":
        home.render_home(conn)

    elif pg == "⏱️ Control de Asistencia":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_asistencia"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        asistencia.render_asistencia(conn)

    elif pg == "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_aula"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        aula_virtual.render_aula(conn)

    elif pg == "🧠 PLANIFICADOR INTELIGENTE":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_planificador"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        planificador.render_planificador(conn)

    elif pg == "🏗️ FÁBRICA DE PENSUMS":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_fabrica"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        fabrica.render_fabrica(conn)
        
    elif pg == "🏗️ GESTIÓN DE PROYECTOS Y PLANES":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_proyectos"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        proyectos.render_proyectos(conn)

    elif pg == "📜 PLANIFICADOR MINISTERIAL":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_ministerial"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        ministerial.render_ministerial(conn)

    elif pg == "📂 Mi Archivo Pedagógico":
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_archivo"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        archivo.render_archivo(conn)

    # EXTRAS (Mensajes Motivacionales, Ideas y Consultas)
    elif pg in ["🌟 Mensaje Motivacional", "💡 Ideas de Actividades", "❓ Consultas Técnicas"]:
        if st.button("⬅️ VOLVER AL MENÚ", use_container_width=True, key="btn_back_extras"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
        extras.render_extras(conn)
    
    # --- PIE DE PÁGINA (FIRMA INSTITUCIONAL v1.0) ---
    st.divider()
    col_pie1, col_pie2 = st.columns([3, 1])
    with col_pie1:
        st.caption("© 2026 SUPER DOCENTE | Desarrollado para el T.E.L E.R.A.C por: **Luis Atencio**")
    with col_pie2:
        st.caption("v2.0 Modular")
