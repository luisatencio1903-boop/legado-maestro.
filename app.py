import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE PÁGINA (ESTABLECE EL NOMBRE E ICONO DE LA APP) ---
st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered"
)

# --- 2. CONFIGURACIÓN DE SEGURIDAD ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        genai.configure(api_key=api_key)
        # Se utiliza Gemini 2.5 Flash por su alta velocidad y precisión técnica
        model = genai.GenerativeModel('gemini-2.5-flash')
    else:
        st.error("⚠️ Configure 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión con el servidor de IA: {e}")
    st.stop()

# --- 3. IDENTIDAD INSTITUCIONAL (SIDEBAR) ---
with st.sidebar:
    try:
        st.image("logo_legado.png", width=150)
    except:
        st.warning("⚠️ Cargando escudo institucional...")
            
    st.title("Legado Maestro")
    st.markdown("---")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("Taller Laboral 'Elena Rosa Aranguibel'")
    st.write("---")
    st.info("💡 Apoyo pedagógico técnico para Educación Especial.")

# --- 4. ASISTENTE EDUCATIVO - CUERPO PRINCIPAL ---
st.title("🍎 Asistente Educativo - Zulia")

opcion = st.selectbox(
    "¿Qué vamos a trabajar hoy, colega?",
    ["📝 Planificador Semanal Profesional", "💡 Ideas para Actividades Laborales", "❓ Consultas Técnicas"]
)

# --- OPCIÓN 1: PLANIFICADOR ---
if opcion == "📝 Planificador Semanal Profesional":
    st.subheader("Estructuración de Planificación Semanal")
    rango = st.text_input("Lapso de la semana:", placeholder="Ej: del 19 al 23 de enero de 2026")
    aula = st.text_input("Aula / Grupo:", value="Mantenimiento y Servicios Generales")
    
    st.info("Ingrese sus notas diarias. El profesor Luis les dará el formato técnico profesional.")
    notas = st.text_area("Cronograma de actividades:", height=200, placeholder="Lunes: actividad...")

    if st.button("🚀 Generar Planificación Estructurada"):
        if rango and notas:
            with st.spinner('Procesando planificación técnica...'):
                try:
                    prompt = f"""
                    Actúa como Luis Atencio, Bachiller Docente del Taller Laboral 'Elena Rosa Aranguibel'.
                    Organiza estas notas en una planificación formal, técnica y concisa para Educación Especial.

                    DATOS: LAPSO: {rango} | AULA: {aula} | DOCENTE: Luis Atencio.
                    NOTAS: {notas}

                    ESTRUCTURA OBLIGATORIA POR DÍA:
                    1. Día y Fecha (Acorde al lapso {rango}).
                    2. Título (Técnico y breve).
                    3. Competencia (Redacción profesional en tercera persona).
                    4. Exploración (Concisa, sin coloquialismos ni referencias religiosas).
                    5. Desarrollo (Pasos prácticos detallados en viñetas).
                    6. REFLEXIÓN (Evaluación del aprendizaje y rutina de aseo personal resumida).
                    7. Mantenimiento (Tarea técnica de orden y limpieza del taller).

                    REQUISITOS: Tono profesional, laico y resumido. Firma: Luis Atencio, Bachiller Docente.
                    """
                    res = model.generate_content(prompt)
                    st.success("¡Planificación generada con éxito!")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error técnico: {e}")

# --- OPCIÓN 2: IDEAS ---
elif opcion == "💡 Ideas para Actividades Laborales":
    st.subheader("Generador de Estrategias Prácticas")
    habilidad = st.text_input("Habilidad o técnica a fortalecer:")
    if st.button("✨ Sugerir Actividades"):
        with st.spinner('Buscando estrategias...'):
            res = model.generate_content(f"Como Bachiller Docente, sugiere 3 actividades técnicas breves para trabajar {habilidad} en educación especial. Tono profesional y laico.")
            st.markdown(res.text)

# --- OPCIÓN 3: CONSULTAS ---
elif opcion == "❓ Consultas Técnicas":
    st.subheader("Consultoría Pedagógica Especializada")
    duda = st.text_area("Ingrese su duda técnica:")
    if st.button("🔍 Responder"):
        with st.spinner('Analizando...'):
            res = model.generate_content(f"Respuesta técnica y profesional sobre educación especial para taller laboral: {duda}")
            st.markdown(res.text)

# --- 5. FIRMA Y MARCA PROFESIONAL AL PIE ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <p style='margin-bottom: 0;'>Desarrollado con ❤️ por <b>Luis Atencio</b></p>
        <p style='font-size: 0.85em; color: gray;'>Bachiller Docente - Taller Laboral 'Elena Rosa Aranguibel'</p>
        <p style='font-size: 0.75em; color: silver;'>Zulia, Venezuela | 2026</p>
    </div>
    """, 
    unsafe_allow_html=True
)
