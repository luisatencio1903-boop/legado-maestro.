import streamlit as st
import pandas as pd
from datetime import datetime
from groq import Groq
from streamlit_gsheets import GSheetsConnection

# --- 1. ESTILOS DE ALTO CONTRASTE ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .docente-card { 
        background-color: #F8F9FA; 
        padding: 25px; 
        border-radius: 15px; 
        border-left: 8px solid #007BFF;
        color: #1A1A1A !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .status-badge {
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
    }
    h1, h2, h3, p { color: #1A1A1A !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DEL NAVEGADOR DOCENTE ---
def vista_docente(u, conn, URL_HOJA):
    st.title(f"🏫 Gestión de Aula: {u['NOMBRE']}")
    
    # Sistema de ventanas tipo navegador
    tab_plan, tab_ejecucion, tab_memoria = st.tabs(["📅 Planificación Semanal", "🚀 Actividad de Hoy", "📜 Mi Memoria"])

    # --- VENTANA 1: PLANIFICACIÓN ---
    with tab_plan:
        st.subheader("Diseño Pedagógico Semanal")
        with st.container():
            st.markdown("<div class='docente-card'>", unsafe_allow_html=True)
            tema_propuesto = st.text_input("Tema para la próxima semana:", placeholder="Ej: Electricidad Básica")
            
            if st.button("🧠 Generar Plan con IA"):
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # Generamos el plan de 8 puntos técnicos
                res = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Planifica 8 puntos técnicos para {tema_propuesto}."}],
                    model="llama-3.3-70b-versatile"
                )
                st.session_state.temp_plan = res.choices[0].message.content
            
            if 'temp_plan' in st.session_state:
                st.write(st.session_state.temp_plan)
                if st.button("📤 Enviar a Dirección para Aprobación"):
                    # Aquí guardamos en la Hoja1 con ESTADO = "PENDIENTE"
                    st.success("Enviado. El Director revisará tu plan pronto.")
            st.markdown("</div>", unsafe_allow_html=True)

    # --- VENTANA 2: ACTIVIDAD DE HOY (SISTEMA DE CONTROL) ---
    with tab_ejecucion:
        df_hoy = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
        # Buscamos si hay algo aprobado para este usuario hoy
        plan_aprobado = df_hoy[(df_hoy['USUARIO'] == u['NOMBRE']) & (df_hoy['ESTADO'] == 'APROBADO')]

        if plan_aprobado.empty:
            st.warning("⚠️ No tienes actividades aprobadas para hoy. Contacta al Director.")
        else:
            fila_plan = plan_aprobado.iloc[-1]
            st.markdown(f"""
                <div class='docente-card'>
                    <h3>✅ Plan Aprobado: {fila_plan['TEMA']}</h3>
                    <p><b>Instrucción del Director:</b> {fila_plan.get('OBSERVACIONES', 'Sin observaciones.')}</p>
                </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("▶️ INICIAR ACTIVIDAD"):
                    st.session_state.clase_activa = True
                    # Actualizar ESTADO a 'EN CURSO' y HORA_INICIO en el Excel
            with c2:
                if st.button("⏹️ CULMINAR ACTIVIDAD"):
                    st.session_state.clase_activa = False
                    # Actualizar ESTADO a 'FINALIZADO' y HORA_FIN
            
            if st.session_state.get('clase_activa'):
                st.info("🕒 Actividad en curso... No olvides cargar tu evidencia al finalizar.")
                st.file_uploader("📸 Cargar Evidencia Fotográfica (En vivo)")

    # --- VENTANA 3: MEMORIA ---
    with tab_memoria:
        st.subheader("Historial de mis actividades")
        df_total = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
        st.dataframe(df_total[df_total['USUARIO'] == u['NOMBRE']])
