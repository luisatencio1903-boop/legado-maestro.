import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN DE SEGURIDAD ---
try:
    # El .strip() elimina cualquier espacio invisible que pueda haber en tu captura de Secrets
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    
    # Intentamos con el modelo más estable
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ Error de configuración: {e}")
    st.stop()

# --- INTERFAZ (Tu diseño, Luis) ---
st.set_page_config(page_title="Legado Maestro", page_icon="🍎")

with st.sidebar:
    st.title("Legado Maestro")
    st.info("💡 Herramienta Docente")
    st.caption("👨‍🏫 **Prof. Luis Atencio**")
    st.caption("Taller 'Elena Rosa Aranguibel'")

st.title("🍎 Asistente Educativo - Zulia")

# --- BOTÓN DE DIAGNÓSTICO (Solo para probar) ---
if st.button("🔍 Probar conexión con Google"):
    try:
        # Esto nos dirá qué modelos realmente puede ver tu clave
        modelos = [m.name for m in genai.list_models()]
        st.write("Tu clave tiene acceso a:", modelos)
    except Exception as e:
        st.error(f"Tu clave API parece no tener permisos: {e}")

# --- LÓGICA DE PLANIFICACIÓN ---
tema = st.text_input("Tema de la clase")
grupo = st.text_input("Grupo", value="Mantenimiento y Servicios Generales")

if st.button("✨ Generar Plan"):
    if tema:
        with st.spinner('El Prof. Luis está consultando a la IA...'):
            try:
                # Si 'gemini-1.5-flash' da 404, el sistema nos dirá por qué
                prompt = f"Crea un plan de clase sobre {tema} para {grupo} en el Zulia."
                respuesta = model.generate_content(prompt)
                st.markdown(respuesta.text)
            except Exception as e:
                st.error(f"Error 404 persistente. Intenta reiniciar la App en el panel de Streamlit. Detalle: {e}")

st.markdown("---")
st.markdown("<center>Desarrollado por <b>Luis Atencio</b></center>", unsafe_allow_html=True)
