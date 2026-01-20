import streamlit as st
import google.generativeai as genai
import time
import random
import os # <--- Importamos esto para verificar si la imagen existe

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

# --- 3. ARRANQUE SEGURO ---
if "ready" not in st.session_state:
    st.session_state.ready = True

# --- 4. CONEXIÓN CON IA (MODELO RÁPIDO) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip())
        # Usamos el modelo 1.5 que es el más resistente a bloqueos
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.error("⚠️ Falta API Key.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
    st.stop()

# --- 5. BARRA LATERAL (CON PROTECCIÓN DE IMAGEN ROTA) ---
with st.sidebar:
    # Verificamos si el archivo existe realmente
    if os.path.exists("logo_legado.png"):
        st.image("logo_legado.png", width=150)
    else:
        # Si no encuentra la imagen, pone la Manzana en vez del error feo
        st.markdown("<h1 style='text-align: center;'>🍎</h1>", unsafe_allow_html=True)
        
    st.title("Legado Maestro")
    st.markdown("---")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("T.E.L E.R.A.C")

# --- 6. CUERPO DE LA APP ---
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
            with st.spinner('Redactando documento...'):
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
                    st.warning("⏳ El sistema se está recargando. Intenta de nuevo en 1 min.")

# --- OPCIÓN 2: MENSAJE MOTIVACIONAL ---
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    
    if st.button("❤️ Mensaje Corto para Compartir"):
        with st.spinner('Buscando las palabras correctas...'):
            try:
                temas = [
                    "Dame solo UNA frase bíblica poderosa sobre enseñar. Corta.",
                    "Una frase célebre corta sobre educación y superación.",
                    "Una frase de aliento guerrero para el docente venezolano. Corta.",
                    "Un recordatorio flash de vocación docente."
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
                st.warning("⏳ El sistema se está recargando. Intenta de nuevo en 1 min.")

# --- OPCIÓN 3: IDEAS ---
elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        try:
            with st.spinner('Pensando ideas...'):
                res = model.generate_content(f"Sugiere 3 actividades técnicas breves para {tema} en Taller Laboral.")
                st.markdown(res.text)
        except:
             st.warning("⏳ El sistema se está recargando. Intenta de nuevo en 1 min.")

# --- OPCIÓN 4: CONSULTAS ---
elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta:")
    if st.button("🔍 Responder"):
        try:
            with st.spinner('Consultando...'):
                res = model.generate_content(f"Respuesta técnica breve: {duda}")
                st.markdown(res.text)
        except:
             st.warning("⏳ El sistema se está recargando. Intenta de nuevo en 1 min.")

# --- 7. PIE DE PÁGINA (SOLO TEXTO PARA EVITAR ERRORES) ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <p style='font-size: 1.5em; margin-bottom: 5px;'>🍎</p>
        <p style='margin-bottom: 2px;'>Desarrollado con ❤️ por <b>Luis Atencio</b></p>
        <p style='font-size: 0.85em; color: #555; margin-bottom: 2px;'>para sus amigos y participantes del <b>T.E.L E.R.A.C</b></p>
        <p style='font-size: 0.75em; color: silver;'>Zulia, Venezuela | 2026</p>
    </div>
    """, 
    unsafe_allow_html=True
)
