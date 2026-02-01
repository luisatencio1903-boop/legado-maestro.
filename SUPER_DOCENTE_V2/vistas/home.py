import streamlit as st
import time
from utils.maletin import recuperar_del_dispositivo

def render_home(conn):
    # --- 1. BOTONERA SUPERIOR (ACCIONES RÁPIDAS V1) ---
    col_update, col_clean, col_logout = st.columns([1.2, 1, 1])
    
    with col_update:
        if st.button("♻️ ACTUALIZAR", help="Descargar datos frescos de Google"):
            st.cache_data.clear()
            st.toast("☁️ Sincronizando...", icon="🔄")
            time.sleep(1)
            st.rerun()

    with col_clean:
        if st.button("🧹 LIMPIAR"):
            st.session_state.plan_actual = ""
            st.session_state.av_resumen = ""
            st.toast("✨ Memoria limpia")
            time.sleep(0.5)
            st.rerun()
            
    with col_logout:
        if st.button("🔒 SALIR", type="primary"):
            st.session_state.auth = False
            st.session_state.u = None
            st.rerun()

    st.divider()

    # --- NUEVO: DETECTOR DE TRABAJO PENDIENTE (RESILIENCIA v2.0) ---
    asis_p = recuperar_del_dispositivo("maletin_asistencia")
    clase_p = recuperar_del_dispositivo("maletin_super_docente")
    
    if asis_p or (clase_p and (clase_p.get("av_foto1") or clase_p.get("av_resumen") != "")):
        st.warning("📢 **¡Atención!** Tienes registros guardados en este dispositivo que aún no han sido subidos a la nube.")
        if st.button("🚀 IR A SINCRONIZAR AHORA", use_container_width=True):
            st.session_state.pagina_actual = "🚀 Sincronizar Jornada"
            st.rerun()
        st.divider()
    
    # --- 2. BIENVENIDA ---
    st.title("🍎 Asistente Educativo - Zulia")
    st.info(f"👋 Saludos, **{st.session_state.u['NOMBRE']}**. Selecciona una acción:")
    
    st.write("")
    
    # --- 3. MENÚ DE NAVEGACIÓN ---
    
    # A. Control Diario
    st.markdown("### ⏱️ CONTROL DIARIO")
    if st.button("📸 REGISTRAR ASISTENCIA / SALIDA", type="primary", use_container_width=True):
        st.session_state.pagina_actual = "⏱️ Control de Asistencia"
        st.rerun()
    
    # B. Gestión Docente
    st.markdown("### 🛠️ GESTIÓN DOCENTE")
    opciones_gestion = [
        "(Seleccionar)",
        "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)",
        "📂 Mi Archivo Pedagógico",
        "🧠 PLANIFICADOR INTELIGENTE",
        "📜 PLANIFICADOR MINISTERIAL",
        "🏗️ FÁBRICA DE PENSUMS",
        "🏗️ GESTIÓN DE PROYECTOS Y PLANES"
    ]
    
    sel_principal = st.selectbox("Herramientas de Planificación:", opciones_gestion, key="home_gestion")
    
    # C. Recursos Extra
    st.markdown("### 🧩 RECURSOS EXTRA")
    opciones_extra = [
        "(Seleccionar)", 
        "🌟 Mensaje Motivacional", 
        "💡 Ideas de Actividades", 
        "❓ Consultas Técnicas"
    ]
    sel_extra = st.selectbox("Apoyo Docente:", opciones_extra, key="home_extras")
    
    # --- LÓGICA DE REDIRECCIÓN ---
    if sel_principal != "(Seleccionar)":
        st.session_state.pagina_actual = sel_principal
        st.rerun()
        
    if sel_extra != "(Seleccionar)":
        st.session_state.pagina_actual = sel_extra
        st.rerun()
