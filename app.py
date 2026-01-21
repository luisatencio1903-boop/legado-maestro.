# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# AUTOR ORIGINAL: Luis Atencio
# FECHA DE ACTUALIZACIÓN: Enero 2026 (Versión 2.0)
# PROPÓSITO: Asistente IA para Educación Especial (Venezuela)
# DERECHOS: Propiedad intelectual de Luis Atencio.
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
            
            /* Estilo para la caja de la planificación */
            .plan-box {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #0068c9;
                margin-bottom: 20px;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. CONEXIÓN CON GROQ ---
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        MODELO_USADO = "llama-3.3-70b-versatile" 
    else:
        st.error("⚠️ Falta la API Key de Groq en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión inicial: {e}")
    st.stop()

# --- 🧠 CEREBRO ACTUALIZADO (CON CITAS Y FUNDAMENTACIÓN) 🧠 ---
INSTRUCCIONES_SEGURIDAD = """
ERES "LEGADO MAESTRO".
1. AUTORÍA: Si preguntan, responde: "Fui desarrollado por el innovador venezolano Luis Atencio".
2. SEGURIDAD: NO opines de política. Eres técnico y educativo.
3. ROL: Experto en Educación Especial y Taller Laboral (Venezuela).
4. FUNDAMENTACIÓN OBLIGATORIA: 
   - Al final de cada planificación o respuesta técnica, AGREGA SIEMPRE una sección llamada "📚 FUNDAMENTACIÓN".
   - CITA documentos oficiales: Currículo Nacional Bolivariano, LOE (Ley Orgánica de Educación), Artículos de la Constitución (CRBV) o Líneas de Investigación del MPPE.
   - NO inventes leyes. Usa las bases de la Educación Especial Venezolana.
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
    
    # Botón para limpiar memoria si se traba
    if st.button("🗑️ Nueva Consulta (Limpiar)"):
        st.session_state.plan_actual = ""
        st.rerun()

# --- 5. GESTIÓN DE MEMORIA (SESSION STATE) ---
# Esto permite que la planificación NO se borre al preguntar
if 'plan_actual' not in st.session_state:
    st.session_state.plan_actual = ""

# --- 6. FUNCIÓN GENERADORA ---
def generar_respuesta(mensajes_historial):
    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes_historial,
            model=MODELO_USADO,
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

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

# =========================================================
# OPCIÓN 1: PLANIFICADOR (AHORA CON CHAT DE SEGUIMIENTO)
# =========================================================
if opcion == "📝 Planificación Profesional":
    st.subheader("Planificación con Base Legal")
    
    # Formulario de entrada
    col1, col2 = st.columns(2)
    with col1:
        rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de Enero")
    with col2:
        aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios")
    
    notas = st.text_area("Notas del Docente / Tema:", height=150, help="Escribe aquí los temas o situaciones a abordar.")

    # BOTÓN DE GENERAR
    if st.button("🚀 Generar Planificación"):
        if rango and notas:
            with st.spinner('Consultando Currículo Nacional Bolivariano y redactando...'):
                prompt_inicial = f"""
                Actúa como Luis Atencio. Crea una planificación para Educación Especial.
                Contexto: Lapso {rango}, Aula {aula}.
                Tema/Notas: {notas}.
                ESTRUCTURA: Inicio, Desarrollo, Cierre y REFLEXIÓN PEDAGÓGICA.
                IMPORTANTE: Cita la base legal o curricular venezolana que sustenta este tema al final.
                """
                
                # Enviamos al cerebro
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_SEGURIDAD},
                    {"role": "user", "content": prompt_inicial}
                ]
                
                respuesta = generar_respuesta(mensajes)
                st.session_state.plan_actual = respuesta # GUARDAMOS EN MEMORIA
                st.rerun() # Recargamos para mostrar

    # MOSTRAR LA PLANIFICACIÓN (SI EXISTE EN MEMORIA)
    if st.session_state.plan_actual:
        st.markdown("---")
        st.markdown("### 📄 Resultado Generado:")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        st.info("👇 ¿Dudas sobre esta planificación? Pregunta abajo sin perder el texto.")

        # --- CHAT DE SEGUIMIENTO (LO NUEVO) ---
        pregunta_seguimiento = st.text_input("💬 Pregunta al Asistente sobre esta planificación:", placeholder="Ej: ¿Cómo evalúo la actividad del martes?")
        
        if st.button("Consultar duda"):
            if pregunta_seguimiento:
                with st.spinner('Analizando tu duda...'):
                    # Le enviamos TODO el contexto: Instrucciones + Planificación que ya hizo + Duda nueva
                    mensajes_seguimiento = [
                        {"role": "system", "content": INSTRUCCIONES_SEGURIDAD},
                        {"role": "assistant", "content": st.session_state.plan_actual}, # La IA recuerda lo que hizo
                        {"role": "user", "content": f"Sobre la planificación anterior: {pregunta_seguimiento}. Dame una respuesta práctica."}
                    ]
                    
                    respuesta_duda = generar_respuesta(mensajes_seguimiento)
                    st.success("Respuesta a tu consulta:")
                    st.write(respuesta_duda)


# =========================================================
# OTRAS OPCIONES (Se mantienen igual)
# =========================================================
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    if st.button("❤️ Mensaje Corto"):
        prompt = "Frase motivacional corta para docente venezolano. Cita bíblica o célebre."
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": prompt}])
        st.success(res)

elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": f"3 actividades DUA para {tema} en Taller Laboral."}])
        st.markdown(res)

elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta Legal/Técnica:")
    if st.button("🔍 Responder"):
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": f"Responde técnicamente y cita la ley o currículo: {duda}"}])
        st.markdown(res)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("Desarrollado por Luis Atencio | Versión 2.0 (Con Fundamentación Legal)")
