import streamlit as st
import google.generativeai as genai
import time
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered"
)

# --- 2. ESTILOS CSS ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .viewerBadge_container__1QSob {display: none !important;}
            
            /* FUERZA EL TEXTO A NEGRO */
            .mensaje-texto {
                color: #000000 !important;
                font-family: 'Helvetica', sans-serif;
                font-size: 1.2em; 
                font-weight: 500;
                line-height: 1.4;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. URL DEL LOGO ---
LOGO_URL = "https://raw.githubusercontent.com/luisatencio1903-boop/legado-maestro/main/logo_legado.png"

# --- 4. ARRANQUE SEGURO ---
if "ready" not in st.session_state:
    st.session_state.ready = True

# --- 5. CONEXIÓN CON IA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip())
        model = genai.GenerativeModel('gemini-2.5-flash')
    else:
        st.error("⚠️ Falta API Key.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
    st.stop()

# --- 6. BARRA LATERAL ---
with st.sidebar:
    st.image(LOGO_URL, width=150)
    st.title("Legado Maestro")
    st.markdown("---")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("T.E.L E.R.A.C")

# --- 7. CUERPO DE LA APP ---
st.title("🍎 Asistente Educativo - Zulia")

opcion = st.selectbox(
    "Seleccione herramienta:",
    [
        "📝 Planificación Profesional", 
        "🌟 Mensaje Motivacional", 
        "💡 Ideas de Actividades", 
        "❓ Consultas Técnicas"
    ]
)

# --- OPCIÓN 1: PLANIFICADOR ---
if opcion == "📝 Planificación Profesional":
    st.subheader("Planificación Técnica")
    rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de enero 2026")
    aula = st.text_input("Aula:", value="Mantenimiento y Servicios Generales")
    notas = st.text_area("Notas diarias:", height=200)

    if st.button("🚀 Generar Planificación"):
        if rango and notas:
            with st.spinner('Procesando datos...'):
                try:
                    prompt = f"""
                    Actúa como Luis Atencio, Bachiller Docente. 
                    Estructura estas notas en una planificación técnica para Educación Especial.
                    Lapso: {rango} | Aula: {aula} | Notas: {notas}
                    ESTRUCTURA: Día, Título, Competencia, Exploración, Desarrollo, REFLEXIÓN, Mantenimiento.
                    FIRMA OBLIGATORIA: Luis Atencio, Bachiller Docente.
                    """
                    res = model.generate_content(prompt)
                    st.success("¡Planificación Generada!")
                    st.markdown(res.text)
                except Exception as e:
                    st.warning("⏳ La IA está descansando. Espera 1 minuto y prueba de nuevo.")

# --- OPCIÓN 2: MENSAJE MOTIVACIONAL ---
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    
    if st.button("❤️ Mensaje Corto para Compartir"):
        with st.spinner('Buscando frase perfecta...'):
            try:
                temas = [
                    """Dame solo UNA frase bíblica poderosa sobre la enseñanza o el amor. 
                    Ejemplo: 'Instruye al niño en su camino...' 
                    Corta y directa.""",
                    
                    """Una frase célebre corta sobre educación y superación.
                    Máximo 15 palabras.""",
                    
                    """Una frase de aliento guerrero para el docente venezolano. 
                    Ejemplo: 'Tu aula es luz en tiempos difíciles.'
                    Corto y contundente.""",
                    
                    """Un recordatorio flash de vocación.
                    Ejemplo: 'Ese pequeño avance vale todo el esfuerzo.'"""
                ]
                
                tema_elegido = random.choice(temas)
                config_creativa = genai.types.GenerationConfig(temperature=0.9)

                prompt_final = f"""
                {tema_elegido}
                REGLAS: MÁXIMO 25 PALABRAS.
                CIERRE OBLIGATORIO: "Ánimos. Att: Profesor Luis Atencio"
                """
                
                res = model.generate_content(prompt_final, generation_config=config_creativa)
                
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #eee; border-left: 8px solid #ff4b4b; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                    <div class="mensaje-texto">
                        {res.text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                # AQUÍ ESTÁ EL MENSAJE AMIGABLE SI SE ACABA EL SALDO
                st.warning("⏳ ¡Mucha inspiración por hoy! Espera 1 minuto para recargar energías.")

# --- OPCIÓN 3: IDEAS ---
elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        try:
            res = model.generate_content(f"Sugiere 3 actividades técnicas, creativas y breves para {tema} en Taller Laboral.")
            st.markdown(res.text)
        except:
             st.warning("⏳ Espera un momento, la IA se está reiniciando.")

# --- OPCIÓN 4: CONSULTAS ---
elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta:")
    if st.button("🔍 Responder"):
        try:
            res = model.generate_content(f"Respuesta técnica profesional y breve: {duda}")
            st.markdown(res.text)
        except:
             st.warning("⏳ Espera un momento, la IA se está reiniciando.")

# --- 8. PIE DE PÁGINA ---
st.markdown("---")
# Usamos columnas de Streamlit en lugar de HTML puro para que la imagen cargue mejor
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image(LOGO_URL, width=60)
    st.markdown(
        """
        <div style='text-align: center;'>
            <p style='margin-bottom: 5px;'>Desarrollado con ❤️ por <b>Luis Atencio</b></p>
            <p style='font-size: 0.85em; color: #555;'>para sus amigos y participantes del <b>T.E.L E.R.A.C</b></p>
            <p style='font-size: 0.75em; color: silver;'>Zulia, Venezuela | 2026</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
