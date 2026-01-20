import streamlit as st
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered"
)

# --- 2. EVITAR ERROR 500 (ESPERA DE INICIO) ---
if "app_ready" not in st.session_state:
    with st.spinner("Cargando Asistente Educativo..."):
        time.sleep(2)  # Da tiempo al servidor para despertar
    st.session_state.app_ready = True

# --- 3. CONFIGURACIÓN DE SEGURIDAD ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip())
        model = genai.GenerativeModel('gemini-2.5-flash')
    else:
        st.error("⚠️ Falta la llave API en los Secrets de Streamlit.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
    st.stop()

# --- 4. IDENTIDAD EN BARRA LATERAL ---
with st.sidebar:
    try:
        st.image("logo_legado.png", width=150)
    except:
        st.warning("⚠️ Cargando logo institucional...")
            
    st.title("Legado Maestro")
    st.markdown("---")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("Taller Laboral 'Elena Rosa Aranguibel'")
    st.write("---")

# --- 5. CUERPO DE LA APP ---
st.title("🍎 Asistente Educativo - Zulia")

opcion = st.selectbox(
    "¿Qué vamos a trabajar hoy, colega?",
    ["📝 Planificador Semanal", "💡 Ideas Prácticas", "❓ Consultas Técnicas"]
)

if opcion == "📝 Planificador Semanal":
    st.subheader("Planificación Técnica Profesional")
    rango = st.text_input("Lapso de la semana:", placeholder="Ej: 19 al 23 de enero 2026")
    aula = st.text_input("Aula / Grupo:", value="Mantenimiento y Servicios Generales")
    st.info("Escribe tus notas. El profesor Luis Atencio les dará el formato oficial.")
    notas = st.text_area("Notas del cronograma:", height=200)

    if st.button("🚀 Generar Planificación Estructurada"):
        if rango and notas:
            with st.spinner('Procesando datos técnicos...'):
                try:
                    prompt = f"""
                    Actúa como Luis Atencio, Bachiller Docente.
                    Estructura estas notas en una planificación formal y técnica para Educación Especial.
                    LAPSO: {rango} | AULA: {aula} | DOCENTE: Luis Atencio.
                    NOTAS: {notas}

                    ESTRUCTURA:
                    1. Día y Fecha.
                    2. Título (Técnico).
                    3. Competencia (Profesional).
                    4. Exploración (Concisa, sin coloquialismos ni religión).
                    5. Desarrollo (Viñetas paso a paso).
                    6. REFLEXIÓN (Evaluación y aseo).
                    7. Mantenimiento (Orden y limpieza).

                    REGLAS: Tono técnico, profesional y laico.
                    FIRMA: Luis Atencio, Bachiller Docente.
                    """
                    res = model.generate_content(prompt)
                    st.success("¡Planificación generada con éxito!")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error técnico: {e}")

elif opcion == "💡 Ideas Prácticas":
    st.subheader("Generador de Estrategias")
    tema = st.text_input("¿Qué técnica quieres fortalecer?")
    if st.button("✨ Sugerir"):
        res = model.generate_content(f"Sugiere 3 actividades breves y técnicas para {tema}. Tono profesional.")
        st.markdown(res.text)

elif opcion == "❓ Consultas Técnicas":
    st.subheader("Consultoría Pedagógica")
    pregunta = st.text_area("Duda técnica:")
    if st.button("🔍 Responder"):
        res = model.generate_content(f"Responde de forma profesional sobre educación especial: {pregunta}")
        st.markdown(res.text)

# --- 6. MARCA PROFESIONAL AL PIE ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <p style='margin-bottom: 0;'>Desarrollado con ❤️ por <b>Luis Atencio</b></p>
        <p style='font-size: 0.85em; color: gray;'>Bachiller Docente - Zulia, 2026</p>
    </div>
    """, 
    unsafe_allow_html=True
)
