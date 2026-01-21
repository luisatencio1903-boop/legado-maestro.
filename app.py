# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# AUTOR ORIGINAL: Luis Atencio
# FECHA DE ACTUALIZACIÓN: Enero 2026 (Versión 2.1 - Fix Modo Oscuro)
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

# --- 2. ESTILOS CSS (CORREGIDO PARA MODO OSCURO) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* ESTILO PARA LA CAJA DE LA PLANIFICACIÓN */
            /* Aquí forzamos el color de letra a NEGRO para que se vea en móviles */
            .plan-box {
                background-color: #f0f2f6 !important; /* Fondo Gris Claro */
                color: #000000 !important;             /* LETRA NEGRA OBLIGATORIA */
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #0068c9;
                margin-bottom: 20px;
                font-family: sans-serif;
            }
            
            /* ESTILO PARA MENSAJES MOTIVACIONALES */
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

# --- 🧠 CEREBRO CON FUNDAMENTACIÓN Y SEGURIDAD 🧠 ---
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
    
    # Botón para limpiar memoria
    if st.button("🗑️ Nueva Consulta (Limpiar)"):
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
# OPCIÓN 1: PLANIFICADOR
# =========================================================
if opcion == "📝 Planificación Profesional":
    st.subheader("Planificación con Base Legal")
    
    col1, col2 = st.columns(2)
    with col1:
        rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de Enero")
    with col2:
        aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios")
    
    notas = st.text_area("Notas del Docente / Tema:", height=150, help="Escribe aquí los temas o situaciones a abordar.")

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
                
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_SEGURIDAD},
                    {"role": "user", "content": prompt_inicial}
                ]
                
                respuesta = generar_respuesta(mensajes)
                st.session_state.plan_actual = respuesta 
                st.rerun() 

    # MOSTRAR LA PLANIFICACIÓN
    if st.session_state.plan_actual:
        st.markdown("---")
        st.markdown("### 📄 Resultado Generado:")
        
        # Aquí usamos la clase CSS .plan-box que arreglamos arriba
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        st.info("👇 ¿Dudas sobre esta planificación? Pregunta abajo sin perder el texto.")

        # CHAT DE SEGUIMIENTO
        pregunta_seguimiento = st.text_input("💬 Pregunta al Asistente sobre esta planificación:", placeholder="Ej: ¿Cómo evalúo la actividad del martes?")
        
        if st.button("Consultar duda"):
            if pregunta_seguimiento:
                with st.spinner('Analizando tu duda...'):
                    mensajes_seguimiento = [
                        {"role": "system", "content": INSTRUCCIONES_SEGURIDAD},
                        {"role": "assistant", "content": st.session_state.plan_actual}, 
                        {"role": "user", "content": f"Sobre la planificación anterior: {pregunta_seguimiento}. Dame una respuesta práctica."}
                    ]
                    
                    respuesta_duda = generar_respuesta(mensajes_seguimiento)
                    st.success("Respuesta a tu consulta:")
                    # Usamos también la caja blanca para la respuesta de la duda, para que se lea bien
                    st.markdown(f'<div class="plan-box">{respuesta_duda}</div>', unsafe_allow_html=True)


# =========================================================
# OTRAS OPCIONES
# =========================================================
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    if st.button("❤️ Mensaje Corto"):
        prompt = "Frase motivacional corta para docente venezolano. Cita bíblica o célebre."
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": prompt}])
        # Usamos la clase mensaje-texto que también tiene letra negra forzada
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #eee; border-left: 8px solid #ff4b4b; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
            <div class="mensaje-texto">{res}</div>
        </div>
        """, unsafe_allow_html=True)

elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": f"3 actividades DUA para {tema} en Taller Laboral."}])
        # Usamos la caja corregida
        st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta Legal/Técnica:")
    if st.button("🔍 Responder"):
        res = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_SEGURIDAD}, {"role": "user", "content": f"Responde técnicamente y cita la ley o currículo: {duda}"}])
        # Usamos la caja corregida
        st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("Desarrollado por Luis Atencio | Versión 2.1 (Compatible con Modo Oscuro)")
