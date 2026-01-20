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

# --- 2. ESTILOS CSS (Modo App Nativa + Texto Negro) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .viewerBadge_container__1QSob {display: none !important;}
            
            /* FUERZA EL TEXTO A NEGRO */
            .mensaje-texto {
                color: #000000 !important;
                font-family: 'Georgia', serif; /* Tipografía más elegante para mensajes */
                font-size: 1.15em;
                line-height: 1.6;
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
                    st.error(f"Error: {e}")

# --- OPCIÓN 2: MENSAJE MOTIVACIONAL (LIBERTAD CREATIVA TOTAL 🎨) ---
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Inspiración Diaria ✨")
    
    if st.button("❤️ Generar Mensaje Sorpresa"):
        with st.spinner('Conectando con la inspiración...'):
            try:
                # LISTA DE TEMAS ABIERTOS (Sin instrucciones rígidas)
                temas = [
                    # Opción 1: Espiritualidad Libre
                    """Reflexiona libremente sobre la belleza espiritual de enseñar a niños con necesidades especiales. 
                    Usa un lenguaje poético y reconfortante sobre cómo esta labor agrada a Dios. 
                    No uses frases cliché. Sé profundo y original.""",
                    
                    # Opción 2: El Poder de la Educación
                    """Crea un mensaje potente sobre cómo un maestro cambia el futuro con pequeños gestos. 
                    Inspírate en grandes educadores pero habla con tus propias palabras. 
                    Enfócate en el impacto invisible pero eterno de la enseñanza.""",
                    
                    # Opción 3: Resiliencia y Esperanza (Sin mencionar crisis explícita)
                    """Escribe una carta breve de aliento a un colega que quizás está cansado hoy. 
                    Recuérdale por qué empezó en este camino. 
                    Usa metáforas sobre sembrar, cultivar y la paciencia. Sé muy humano y cálido.""",
                    
                    # Opción 4: La Alegría de los Participantes
                    """Enfócate en la sonrisa y el logro de un participante del Taller Laboral. 
                    Cómo ese pequeño avance vale todo el esfuerzo del mundo. 
                    Celebra las pequeñas victorias."""
                ]
                
                # ELEGIR TEMA AL AZAR
                tema_elegido = random.choice(temas)
                
                # CONFIGURACIÓN DE ALTA CREATIVIDAD (Temperature = 1.0)
                config_creativa = genai.types.GenerationConfig(temperature=1.0)

                prompt_final = f"""
                {tema_elegido}
                
                REGLAS DE ORO:
                1. Sé totalmente original, evita repetir estructuras anteriores.
                2. Habla con emoción genuina, de colega a colega.
                3. CIERRE OBLIGATORIO: "Ánimos. Att: Profesor Luis Atencio"
                """
                
                # Generamos con la nueva configuración de creatividad
                res = model.generate_content(prompt_final, generation_config=config_creativa)
                
                # MUESTRA EL MENSAJE
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 25px; border-radius: 15px; border-left: 6px solid #ff4b4b; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                    <h4 style="color: #000000 !important; margin-top: 0;">🌟 Mensaje para hoy:</h4>
                    <div class="mensaje-texto">
                        {res.text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error("Error al conectar con la inspiración.")

# --- OPCIÓN 3: IDEAS ---
elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        res = model.generate_content(f"Sugiere 3 actividades técnicas, creativas y breves para {tema} en Taller Laboral.")
        st.markdown(res.text)

# --- OPCIÓN 4: CONSULTAS ---
elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta:")
    if st.button("🔍 Responder"):
        res = model.generate_content(f"Respuesta técnica profesional y breve: {duda}")
        st.markdown(res.text)

# --- 8. PIE DE PÁGINA ---
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center;'>
        <img src='{LOGO_URL}' width='50'><br>
        <p style='margin-bottom: 5px;'>Desarrollado con ❤️ por <b>Luis Atencio</b></p>
        <p style='font-size: 0.85em; color: #555;'>para sus amigos y participantes del <b>T.E.L E.R.A.C</b></p>
        <p style='font-size: 0.75em; color: silver;'>Zulia, Venezuela | 2026</p>
    </div>
    """, 
    unsafe_allow_html=True
)
