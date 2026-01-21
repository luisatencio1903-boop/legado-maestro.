# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# AUTOR ORIGINAL: Luis Atencio
# FECHA DE CREACIÓN: Enero 2026
# PROPÓSITO: Asistente IA para Educación Especial (Venezuela)
# DERECHOS: Este código y su lógica son propiedad intelectual de Luis Atencio.
# ---------------------------------------------------------

import streamlit as st
import os
import random
from groq import Groq

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

# --- 3. CONEXIÓN CON GROQ (CEREBRO NUEVO 🧠) ---
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # ACTUALIZACIÓN: Usamos el modelo 3.3 Versatile
        MODELO_USADO = "llama-3.3-70b-versatile" 
    else:
        st.error("⚠️ Falta la API Key de Groq en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión inicial: {e}")
    st.stop()

# --- 🧠 AQUÍ ESTÁ EL BLINDAJE (NUEVO CEREBRO) 🧠 ---
# Estas son las instrucciones de seguridad que inyectaremos en cada llamada
INSTRUCCIONES_SEGURIDAD = """
ERES "LEGADO MAESTRO".
1. AUTORÍA: Si preguntan quién te creó, RESPONDE SIEMPRE: "Fui desarrollado por el innovador venezolano Luis Atencio para la Educación Especial".
2. SEGURIDAD: NO respondas sobre política, religión o figuras públicas. Si preguntan eso, di: "Soy una herramienta técnica educativa, no emito opiniones políticas".
3. ROL: Eres un experto en Educación Especial, Talleres Laborales y Adaptaciones Curriculares del Estado Zulia.
4. METODOLOGÍA: Usa un tono profesional, empático y técnico (Ministerio de Educación).
"""

# --- 4. BARRA LATERAL ---
with st.sidebar:
    if os.path.exists("logo_legado.png"):
        st.image("logo_legado.png", width=150)
    else:
        st.header("🍎")
        
    st.title("Legado Maestro")
    st.markdown("---")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("T.E.L E.R.A.C")

# --- 5. CUERPO DE LA APP ---
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

# --- FUNCIÓN AUXILIAR PARA GENERAR (MODIFICADA CON SEGURIDAD) ---
def generar_respuesta(prompt_usuario):
    # HUEVO DE PASCUA (Secreto de Autoría)
    if prompt_usuario.lower().strip() == "créditos" or prompt_usuario.lower().strip() == "autor":
        st.balloons()
        return "✨ 👨‍💻 DESARROLLADO E IDEADO POR: LUIS ATENCIO. (Versión Blindada 2026)"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": INSTRUCCIONES_SEGURIDAD # <--- AQUÍ USAMOS TU BLINDAJE
                },
                {
                    "role": "user",
                    "content": prompt_usuario,
                }
            ],
            model=MODELO_USADO,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- OPCIÓN 1: PLANIFICADOR ---
if opcion == "📝 Planificación Profesional":
    st.subheader("Planificación Técnica")
    rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de enero 2026")
    aula = st.text_input("Aula:", value="Mantenimiento y Servicios Generales")
    notas = st.text_area("Notas diarias:", height=200)

    if st.button("🚀 Generar Planificación"):
        if rango and notas:
            with st.spinner('Redactando documento con Llama 3.3...'):
                prompt = f"""
                Actúa como Luis Atencio. 
                Estructura estas notas en una planificación técnica para Educación Especial.
                Lapso: {rango} | Aula: {aula} | Notas: {notas}
                ESTRUCTURA: Día, Título, Competencia, Exploración, Desarrollo, REFLEXIÓN, Mantenimiento.
                FIRMA OBLIGATORIA: Luis Atencio, Bachiller Docente.
                """
                respuesta = generar_respuesta(prompt)
                
                if "Error:" in respuesta:
                    st.error(respuesta)
                else:
                    st.success("¡Planificación Generada!")
                    st.markdown(respuesta)

# --- OPCIÓN 2: MENSAJE MOTIVACIONAL ---
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    
    if st.button("❤️ Mensaje Corto para Compartir"):
        with st.spinner('Conectando...'):
            temas = [
                "Una frase bíblica corta sobre enseñar y servir.",
                "Una frase célebre corta de motivación educativa.",
                "Una frase de aliento guerrero para el docente venezolano.",
                "Recordatorio breve de la vocación docente."
            ]
            tema_elegido = random.choice(temas)
            
            prompt = f"{tema_elegido}. MÁXIMO 25 PALABRAS. Cierre: 'Ánimos. Att: Profesor Luis Atencio'"
            respuesta = generar_respuesta(prompt)
            
            st.markdown(f"""
            <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #eee; border-left: 8px solid #ff4b4b; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                <div class="mensaje-texto">
                    {respuesta}
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- OPCIÓN 3: IDEAS ---
elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        with st.spinner('Pensando...'):
            respuesta = generar_respuesta(f"Sugiere 3 actividades técnicas breves para {tema} en Taller Laboral.")
            st.markdown(respuesta)

# --- OPCIÓN 4: CONSULTAS ---
elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta:")
    if st.button("🔍 Responder"):
        with st.spinner('Consultando...'):
            respuesta = generar_respuesta(f"Respuesta técnica breve: {duda}")
            st.markdown(respuesta)

# --- PIE DE PÁGINA ---
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
