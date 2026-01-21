# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO (LABORATORIO)
# VERSIÓN: 2.0 (Conexión Blindada - Hoja1)
# ---------------------------------------------------------

import streamlit as st
import pandas as pd
from datetime import datetime
from groq import Groq
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Legado Maestro LAB", page_icon="🧪", layout="centered")

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    .plan-box {
        background-color: #f0f2f6 !important;
        color: #000000 !important; 
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0068c9;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error de conexión inicial: {e}")

# --- 4. FUNCIÓN DE GUARDADO (CONFIGURADA PARA 'Hoja1') ---
def guardar_en_nube(aula, tema, contenido):
    try:
        # Limpiamos la URL de cualquier espacio invisible
        url_hoja = st.secrets["GSHEETS_URL"].strip()
        
        # Leemos la hoja (Usamos 'Hoja1' sin espacios)
        df_existente = conn.read(spreadsheet=url_hoja, worksheet="Hoja1", ttl=0)
        
        nueva_fila = pd.DataFrame([{
            "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Aula": aula,
            "Tema": tema,
            "Contenido": contenido
        }])
        
        # Unimos los datos
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        
        # Actualizamos la hoja en la nube
        conn.update(spreadsheet=url_hoja, worksheet="Hoja1", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- 5. LÓGICA DE IA (GROQ) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def generar_respuesta(mensajes):
    chat_completion = client.chat.completions.create(
        messages=mensajes, 
        model="llama-3.3-70b-versatile", 
        temperature=0.4
    )
    return chat_completion.choices[0].message.content

# --- 6. INTERFAZ ---
st.title("📝 Registro en la Nube (Prueba)")

with st.sidebar:
    st.subheader("📂 Gaveta Digital")
    if st.button("🔄 Actualizar"):
        st.rerun()
    
    # Intento de lectura para mostrar historial rápido
    try:
        url_check = st.secrets["GSHEETS_URL"].strip()
        df_ver = conn.read(spreadsheet=url_check, worksheet="Hoja1", ttl=0)
        if not df_ver.empty:
            for i, row in df_ver.tail(3).iterrows():
                st.success(f"📌 {row['Fecha']}\n{row['Tema']}")
    except:
        st.caption("Conexión pendiente...")

# Formulario
aula = st.text_input("Aula/Taller:", value="Mantenimiento")
tema = st.text_input("Tema central:")
notas = st.text_area("Detalles:")

if st.button("🚀 Generar Planificación"):
    if tema:
        with st.spinner('Procesando...'):
            prompt = f"Actúa como Luis Atencio. Crea una planificación técnica de 8 puntos para {aula} sobre {tema}. Notas: {notas}."
            res = generar_respuesta([{"role": "user", "content": prompt}])
            st.session_state.plan_temp = res
            st.rerun()

if 'plan_temp' in st.session_state:
    st.markdown(f'<div class="plan-box">{st.session_state.plan_temp}</div>', unsafe_allow_html=True)
    
    if st.button("💾 GUARDAR EN GOOGLE SHEETS"):
        with st.spinner("Subiendo datos a la nube..."):
            if guardar_en_nube(aula, tema, st.session_state.plan_temp):
                st.success("✅ ¡Guardado exitoso en el Excel!")
                st.balloons()
