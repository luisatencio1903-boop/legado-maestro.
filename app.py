import streamlit as st
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN DE IDENTIDAD VISUAL ---
# El icono aparecerá al instalar la app en el celular
st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered"
)

# --- 2. PREVENCIÓN DE ERROR DE SERVIDOR ---
if "ready" not in st.session_state:
    with st.spinner("Conectando con el Taller Laboral..."):
        time.sleep(2)  # Estabiliza la conexión para evitar el Error 500
    st.session_state.ready = True

# --- 3. CONFIGURACIÓN DE LA IA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip())
        model = genai.GenerativeModel('gemini-2.5-flash')
    else:
        st.error("⚠️ Falta configurar GOOGLE_API_KEY en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error técnico: {e}")
    st.stop()

# --- 4. BARRA LATERAL: IDENTIDAD DEL DOCENTE ---
with st.sidebar:
    # Intenta cargar el logo institucional
    try:
        st.image("logo_legado.png", width=150)
    except:
        st.warning("⚠️ Cargando escudo institucional...")
            
    st.title("Legado Maestro")
    st.markdown("---")
    # Tu firma profesional
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("Taller Laboral 'Elena Rosa Aranguibel'")
    st.write("---")
    st.info("💡 Fortaleciendo la Educación Especial en el Zulia.")

# --- 5. CUERPO PRINCIPAL ---
st.title("🍎 Asistente Educativo - Zulia")

opcion = st.selectbox(
    "¿Qué vamos a trabajar hoy, colega?",
    ["📝 Planificador Semanal Profesional", "💡 Ideas para Actividades", "❓ Consultas Técnicas"]
)

if opcion == "📝 Planificador Semanal Profesional":
    st.subheader("Planificación Técnica Estructurada")
    rango = st.text_input("Lapso de la semana:", placeholder="Ej: del 19 al 23 de enero de 2026")
    aula = st.text_input("Aula / Grupo:", value="Mantenimiento y Servicios Generales")
    st.info("El profesor Luis Atencio se encargará de dar el formato profesional a sus notas.")
    notas = st.text_area("Cronograma de actividades:", height=200)

    if st.button("🚀 Generar Planificación"):
        if rango and notas:
            with st.spinner('Procesando datos pedagógicos...'):
                try:
                    # Instrucción estricta para que la IA siempre firme como tú
                    prompt = f"""
                    Actúa como Luis Atencio, Bachiller Docente del Taller Laboral 'Elena Rosa Aranguibel'.
                    Organiza estas notas en una planificación formal, técnica y concisa para Educación Especial.
                    
                    DATOS: LAPSO: {rango} | AULA: {aula} | DOCENTE: Luis Atencio.
                    NOTAS: {notas}

                    ESTRUCTURA POR DÍA:
                    1. Día y Fecha.
                    2. Título (Técnico).
                    3. Competencia (Profesional).
                    4. Exploración (Concisa, sin religión).
                    5. Desarrollo (Viñetas técnicas).
                    6. REFLEXIÓN (Evaluación y aseo).
                    7. Mantenimiento (Orden y limpieza).

                    REGLA DE ORO: Tono profesional y laico. 
                    AL FINAL DEL DOCUMENTO DEBES FIRMAR OBLIGATORIAMENTE COMO: 
                    Luis Atencio, Bachiller Docente.
                    """
                    res = model.generate_content(prompt)
                    st.success("¡Planificación generada con éxito!")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error técnico de la IA: {e}")

# --- 6. MARCA Y FIRMA FINAL (FOOTER) ---
st.markdown("---")
# Firma visual en el pie de página
st.markdown(
    """
    <div style='text-align: center;'>
        <p style='margin-bottom: 0;'>Desarrollado con ❤️ por <b>Luis Atencio</b></p>
        <p style='font-size: 0.85em; color: gray;'>Bachiller Docente - Zulia, 2026</p>
    </div>
    """, 
    unsafe_allow_html=True
)
