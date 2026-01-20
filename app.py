import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    # Usamos Gemini 2.5 Flash por su precisión en seguir estructuras
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"⚠️ Error en la configuración: {e}")
    st.stop()

# --- 2. CONFIGURACIÓN DE LA PÁGINA (Identidad Luis Atencio) ---
st.set_page_config(page_title="Legado Maestro", page_icon="🍎")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("Legado Maestro")
    st.info("💡 Herramienta de Apoyo Docente")
    st.caption("👨‍🏫 **Prof. Luis Atencio**")
    st.caption("Taller Laboral 'Elena Rosa Aranguibel'")
    st.write("---")

# --- 3. LÓGICA DE LA APLICACIÓN ---
st.title("🍎 Asistente Educativo - Zulia")
st.subheader("Planificación para Educación Especial")

opcion = st.selectbox(
    "¿Qué vamos a trabajar hoy, colega?",
    ["📝 Crear Plan de Clase", "🔧 Consultar Mantenimiento", "💡 Idea para Actividad"]
)

if opcion == "📝 Crear Plan de Clase":
    tema = st.text_input("Ingresa el tema central de la semana:")
    mes = st.selectbox("Selecciona el mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    
    if st.button("✨ Generar Planificación con mi Estructura"):
        if tema:
            with st.spinner('Luis, estoy organizando el plan según tu formato de aula...'):
                try:
                    # PROMPT DE ESTRUCTURA: Obligamos a la IA a seguir tu orden exacto
                    prompt = f"""
                    Actúa como el Prof. Luis Atencio, docente de Educación Especial en el Zulia.
                    Genera una planificación semanal para el Taller Laboral 'Elena Rosa Aranguibel'.
                    
                    TEMA SEMANAL: {tema}
                    MES: {mes} de 2026.

                    ESTRUCTURA OBLIGATORIA PARA CADA DÍA (Lunes a Viernes):
                    1. Día y Fecha: (Calcula las fechas según el mes indicado).
                    2. Título de la Actividad: (Relacionado con el tema y mantenimiento).
                    3. Competencia: (Definición técnica de la habilidad a desarrollar).
                    4. Exploración: (Conversatorio inicial o teoría corta).
                    5. Desarrollo: (Pasos prácticos de la actividad en el aula/taller).
                    6. Cierre: (Reflexión y rutina de aseo personal obligatoria).
                    7. Mantenimiento: (Tarea específica de limpieza u organización de herramientas).

                    REGLAS DE ORO:
                    - Usa lenguaje motivador y zuliano (Ej: "¡Epale mi gente!").
                    - Enfócate en habilidades pre-laborales, autonomía y seguridad.
                    - No dejes campos vacíos ni uses corchetes [ ].
                    - Firma al final como Prof. Luis Atencio.
                    """
                    
                    respuesta = model.generate_content(prompt)
                    st.success("¡Planificación lista bajo tu formato!")
                    st.markdown(respuesta.text)
                except Exception as e:
                    st.error(f"Error técnico: {e}")
        else:
            st.warning("Luis, por favor indica el tema de la semana.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("<div style='text-align: center'>Desarrollado con ❤️ por <b>Luis Atencio</b></div>", unsafe_allow_html=True)
