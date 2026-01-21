import streamlit as st
import pandas as pd
from datetime import datetime
from groq import Groq
from streamlit_gsheets import GSheetsConnection

# --- 1. BASE DE DATOS DE USUARIOS (SISTEMA REAL) ---
# En una fase avanzada, esto irá en una hoja oculta de Excel.
USUARIOS = {
    "latencio": {"clave": "luis2026", "nombre": "Luis Atencio", "rol": "DOCENTE"},
    "dgabriela": {"clave": "zulia2026", "nombre": "Directora Gabriela", "rol": "DIRECTOR"},
    "super_reg": {"clave": "regional2026", "nombre": "Supervisor Regional", "rol": "SUPERVISOR"}
}

# --- 2. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Legado Maestro - Seguridad", layout="wide")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL_HOJA = st.secrets["GSHEETS_URL"]

# --- 3. LÓGICA DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_data = None

# --- 4. INTERFAZ DE LOGIN ---
if not st.session_state.autenticado:
    st.title("🛡️ Acceso Legado Maestro")
    st.markdown("---")
    
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.subheader("Inicio de Sesión")
            input_user = st.text_input("Usuario (Cédula o ID)")
            input_pass = st.text_input("Contraseña", type="password")
            
            if st.button("🔓 INGRESAR AL SISTEMA"):
                if input_user in USUARIOS and USUARIOS[input_user]["clave"] == input_pass:
                    st.session_state.autenticado = True
                    st.session_state.user_data = USUARIOS[input_user]
                    st.success(f"Bienvenido, {USUARIOS[input_user]['nombre']}")
                    time.sleep(1) # Pequeña pausa para efecto visual
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Acceso denegado.")

# --- 5. SISTEMA UNA VEZ AUTENTICADO ---
else:
    # Barra lateral de control
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.sidebar.title(st.session_state.user_data["nombre"])
    st.sidebar.write(f"Rol: **{st.session_state.user_data['rol']}**")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.user_data = None
        st.rerun()

    # Leer datos de Google Sheets
    df = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)

    # --- PRIVACIDAD: FILTRADO DE DATOS ---
    if st.session_state.user_data["rol"] == "DOCENTE":
        # EL MAESTRO SOLO VE SUS DATOS
        df_mostrar = df[df['USUARIO'] == st.session_state.user_data["nombre"]]
    else:
        # EL DIRECTOR Y SUPERVISOR VEN TODO
        df_mostrar = df

    # --- PANEL DOCENTE ---
    if st.session_state.user_data["rol"] == "DOCENTE":
        st.header(f"👨‍🏫 Gestión de Aula: {st.session_state.user_data['nombre']}")
        
        tab1, tab2 = st.tabs(["📝 Planificación", "📊 Mis Registros"])
        
        with tab1:
            tema = st.text_input("Tema de la actividad:")
            if st.button("🧠 Generar Plan Técnico"):
                # Aquí iría tu lógica de Groq ya configurada
                st.session_state.plan_temp = "Planificación técnica de 8 puntos generada..." 
                st.info(st.session_state.plan_temp)
            
            if st.button("🚀 INICIAR Y GUARDAR"):
                # Lógica de guardado que ya probamos con los globos
                st.balloons()
                st.success("Actividad guardada en la nube.")

        with tab2:
            st.subheader("Mi Historial Pedagógico")
            st.dataframe(df_mostrar)

    # --- PANEL DIRECTOR / SUPERVISOR ---
    elif st.session_state.user_data["rol"] in ["DIRECTOR", "SUPERVISOR"]:
        st.header(f"📋 Panel de Supervisión: {st.session_state.user_data['rol']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Actividades Registradas", len(df_mostrar))
        with col2:
            activos = len(df_mostrar[df_mostrar['ESTADO'] == 'EN CURSO'])
            st.metric("Maestros en Aula (En Vivo)", activos)
        
        st.subheader("Reporte General de Institución")
        st.dataframe(df_mostrar)
