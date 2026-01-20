import streamlit as st
import google.generativeai as genai

# --- CONFIGURACIÓN DE SEGURIDAD (Limpieza de clave) ---
try:
    # Limpiamos posibles espacios en blanco en la clave de Secrets
    raw_key = st.secrets["GOOGLE_API_KEY"]
    clean_key = raw_key.strip() 
    genai.configure(api_key=clean_key)
    
    # Usamos el nombre completo del modelo para evitar el error 'NotFound'
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ Error en la configuración de seguridad: {e}")
    st.stop()

# --- CONFIGURACIÓN DE LA PÁGINA (Tu esencia) ---
st.set_page_config(page_title="Legado Maestro", page_icon="🍎")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("Legado Maestro")
    st.info("💡 Apoyo Docente")
    st.caption("👨‍🏫 **Prof. Luis Atencio**")
    st.caption("Taller Laboral 'Elena Rosa Aranguibel'")

st.title("🍎 Asistente Educativo")
st.subheader("Planificación Pedagógica")

opcion = st.selectbox(
    "¿Qué vamos a trabajar hoy, colega?",
    ["📝 Crear Plan de Clase", "🔧 Consultar Mantenimiento", "💡 Idea para Actividad"]
)

if opcion == "📝 Crear Plan de Clase":
    tema = st.text_input("Tema (Ej: Higiene, Efemérides)")
    grado = st.text_input("Grupo (Ej: Mantenimiento)", value="Mantenimiento y Servicios Generales")
    
    if st.button("✨ Generar Plan"):
        if tema and grado:
            with st.spinner('Procesando orden del Prof. Luis...'):
                try:
                    prompt = f"Actúa como docente de Educación Especial en el Zulia. Crea un plan sobre {tema} para el grupo {grado} (Semana 19-23 de enero 2026). Incluye Inicio, Desarrollo y Cierre."
                    respuesta = model.generate_content(prompt)
                    st.success("¡Planificación lista!")
                    st.markdown(respuesta.text)
                except Exception as e:
                    st.error(f"Error al conectar con la IA: {e}")
        else:
            st.warning("Por favor, completa los campos.")

# --- TU SELLO AL PIE ---
st.markdown("---")
st.markdown("<div style='text-align: center'>Desarrollado con ❤️ por <b>Luis Atencio</b></div>", unsafe_allow_html=True)
