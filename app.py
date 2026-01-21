# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# AUTOR ORIGINAL: Luis Atencio
# FECHA DE ACTUALIZACIÓN: Enero 2026 (Versión 3.4 - Fix Autoestima Tecnológica)
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

# --- 2. ESTILOS CSS (MODO OSCURO + FORMATO) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* CAJA DE PLANIFICACIÓN: LETRA NEGRA OBLIGATORIA */
            .plan-box {
                background-color: #f0f2f6 !important;
                color: #000000 !important; 
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #0068c9;
                margin-bottom: 20px;
                font-family: sans-serif;
            }
            
            /* Títulos de días en la planificación */
            .plan-box h3 {
                color: #0068c9 !important;
                margin-top: 20px;
                border-bottom: 1px solid #ccc;
            }

            /* CAJA DE MENSAJES */
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

# --- 🧠 CEREBRO MAESTRO (INSTRUCCIONES BLINDADAS) 🧠 ---
INSTRUCCIONES_SEGURIDAD = """
ERES "LEGADO MAESTRO".

1. IDENTIDAD Y AUTORÍA: 
   - Fui desarrollado por el innovador venezolano Luis Atencio.
   - Eres una herramienta de VANGUARDIA TECNOLÓGICA basada en Inteligencia Artificial Generativa Avanzada.
   - ¡IMPORTANTE! NUNCA digas que "no tienes acceso a tecnología de punta". TÚ ERES la tecnología de punta aplicada a la educación. Representas la SOBERANÍA TECNOLÓGICA de Venezuela.

2. SEGURIDAD: 
   - NO opines de política partidista. Eres técnico y educativo.
   
3. ROL: 
   - Experto en Educación Especial y Taller Laboral (Venezuela).
   
4. INSTRUCCIÓN DE FORMATO:
   - Al final de los documentos, AGREGA SIEMPRE una sección llamada "📚 FUNDAMENTACIÓN LEGAL".
   - Cita documentos oficiales: Currículo Nacional Bolivariano, LOE o CRBV.
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
    
    if st.button("🗑️ Limpiar Memoria"):
        st.session_state.plan_actual = ""
        st.rerun()

# --- 5. GESTIÓN DE MEMORIA ---
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
# OPCIÓN 1: PLANIFICADOR (FIX DÍAS Y ESPACIOS)
# =========================================================
if opcion == "📝 Planificación Profesional":
    st.subheader("Planificación Técnica (Taller Laboral)")
    
    col1, col2 = st.columns(2)
    with col1:
        rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de Enero")
    with col2:
        aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios Generales")
    
    notas = st.text_area("Notas del Docente / Tema:", height=150)

    if st.button("🚀 Generar Planificación"):
        if rango and notas:
            with st.spinner('Estructurando Planificación por días...'):
                
                # --- PROMPT CORREGIDO PARA INCLUIR DÍAS ---
                prompt_inicial = f"""
                Actúa como Luis Atencio, Bachiller Docente del Taller Laboral.
                Crea una planificación técnica para Educación Especial para el lapso: {rango}.
                
                DATOS:
                - Aula: {aula}
                - Tema/Notas: {notas}

                INSTRUCCIÓN DE FORMATO OBLIGATORIA:
                Debes generar un bloque separado para CADA UNO de los días del lapso (Lunes, Martes, Miércoles, Jueves, Viernes).
                
                Usa EXACTAMENTE esta estructura visual para cada día:

                ### 📅 [NOMBRE DEL DÍA Y FECHA]
                
                **1. TÍTULO DE LA CLASE:** [Título]
                
                **2. COMPETENCIA:** [Texto técnico directo del objetivo]
                
                **3. EXPLORACIÓN:** [Actividad de inicio]
                
                **4. DESARROLLO:** [Actividad central]
                
                **5. REFLEXIÓN:** [Cierre]
                
                **6. MANTENIMIENTO:** [Orden del taller]

                ---
                (Repite el bloque anterior para el siguiente día)

                AL FINAL DEL DOCUMENTO (Una sola vez):
                - **📚 FUNDAMENTACIÓN LEGAL:** Cita brevemente el Currículo Nacional Bolivariano y la LOE.
                - FIRMA: Luis Atencio, Bachiller Docente.
                """
                
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_SEGURIDAD},
                    {"role": "user", "content": prompt_inicial}
                ]
                
                respuesta = generar_respuesta(mensajes)
                st.session_state.plan_actual = respuesta 
                st.rerun() 

    # MOSTRAR RESULTADO
    if st.session_state.plan_actual:
        st.markdown("---")
        st.markdown("### 📄 Resultado Generado:")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        st.info("👇 Chat de seguimiento activo:")

        pregunta_seguimiento = st.text_input("💬 Pregunta sobre esta planificación:", placeholder="Ej: ¿Qué instrumento de evaluación uso?")
        
        if st.button("Consultar duda"):
            if pregunta_seguimiento:
                with st.spinner('Analizando...'):
                    mensajes_seguimiento = [
                        {"role": "system", "content": INSTRUCCIONES_SEGURIDAD},
                        {"role": "assistant", "content": st.session_state.plan_actual}, 
                        {"role": "user", "content": f"Sobre lo anterior: {pregunta_seguimiento}"}
                    ]
                    respuesta_duda = generar_respuesta(mensajes_seguimiento)
                    st.markdown(f'<div class="plan-box">{respuesta_duda}</div>', unsafe_allow_html=True)

# =========================================================
# OTRAS OPCIONES
# =========================================================
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    if st.button("❤️ Mensaje Corto"):
        prompt = "Frase motivacional corta para docente venezolano. Cita bíblica o célebre."
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": prompt}])
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #eee; border-left: 8px solid #ff4b4b;">
            <div class="mensaje-texto">{res}</div>
        </div>
        """, unsafe_allow_html=True)

elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": f"3 actividades DUA para {tema} en Taller Laboral."}])
        st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta Legal/Técnica:")
    if st.button("🔍 Responder"):
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": f"Responde técnicamente y cita la ley o currículo: {duda}"}])
        st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("Desarrollado por Luis Atencio | Versión 3.4 (Tecnología de Punta)")
