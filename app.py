import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"⚠️ Error de configuración: {e}")
    st.stop()

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Legado Maestro", page_icon="🍎")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("Legado Maestro")
    st.info("💡 Herramienta de Apoyo Docente")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente - Taller Laboral")
    st.write("---")

# --- 3. LÓGICA DE LA APLICACIÓN ---
st.title("🍎 Asistente Educativo - Zulia")
st.subheader("Planificador Semanal por Actividades")

# NUEVO CUADRO: Rango de Fechas
rango_fecha = st.text_input("Ingresa el lapso de la semana:", placeholder="Ej: Del 19 al 23 de enero de 2026")

# NUEVO CUADRO: Aula / Grupo
grado = st.text_input("Aula / Grupo:", value="Mantenimiento y Servicios Generales")

# NUEVO CUADRO: Cronograma libre
st.markdown("### 📝 Cronograma de la Semana")
st.info("Escribe el día y tus actividades. La IA se encargará de darle el formato profesional a cada una.")
notas_docente = st.text_area(
    "Escribe aquí (Ej: Lunes: Higiene personal. Martes: Mantenimiento general...)",
    height=200,
    placeholder="Lunes: [Actividades...]\nMartes: [Actividades...]\nMiércoles: [Actividades...]"
)

if st.button("🚀 Generar Planificación Estructurada"):
    if rango_fecha and notas_docente:
        with st.spinner('Luis, estoy organizando tus actividades en el formato oficial...'):
            try:
                # PROMPT DE ESTRUCTURACIÓN:
                # Gemini usará los nombres de los días como delimitadores
                prompt = f"""
                Actúa como Luis Atencio, bachiller docente del Taller Laboral 'Elena Rosa Aranguibel'.
                Tu tarea es tomar las notas rápidas del docente y organizarlas en una planificación profesional.

                LAPSO: {rango_fecha}
                AULA: {grado}

                NOTAS DEL DOCENTE:
                {notas_docente}

                INSTRUCCIONES DE FORMATO PARA CADA DÍA MENCIONADO:
                1. Día y Fecha: (Usa el lapso {rango_fecha} para asignar la fecha exacta a cada día).
                2. Título de la Actividad: (Basado en lo que escribió el docente).
                3. Competencia: (Redacta una competencia técnica acorde a la actividad).
                4. Exploración: (Breve conversatorio o dinámica inicial).
                5. Desarrollo: (Explica paso a paso las actividades que el docente anotó).
                6. Cierre: (Rutina de aseo personal y reflexión).
                7. Mantenimiento: (Tarea técnica de orden y limpieza del taller).

                REGLAS DE ORO:
                - Si el docente anotó varias actividades para un día, inclúyelas todas en el Desarrollo.
                - Mantén el tono zuliano, sencillo y motivador ("¡Epale mi gente!").
                - No inventes días que el docente no mencionó.
                - Firma al final: Luis Atencio, Bachiller Docente.
                """
                
                respuesta = model.generate_content(prompt)
                st.success("¡Planificación organizada con éxito!")
                st.markdown(respuesta.text)
            except Exception as e:
                st.error(f"Error técnico: {e}")
    else:
        st.warning("Luis, por favor ingresa el lapso de fecha y al menos una actividad.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("<div style='text-align: center'>Desarrollado con ❤️ por <b>Luis Atencio</b> para el Taller Laboral.</div>", unsafe_allow_html=True)
