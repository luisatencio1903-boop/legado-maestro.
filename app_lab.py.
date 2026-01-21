# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO (LABORATORIO)
# VERSIÓN: 1.3 (Fix Definitivo: Estrategias, Recursos y Formato)
# FECHA: Enero 2026
# AUTOR: Luis Atencio
# ---------------------------------------------------------

import streamlit as st
import os
from groq import Groq

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Legado Maestro (LAB)",
    page_icon="🧪", # Icono de probeta para diferenciar en la pestaña del navegador
    layout="centered"
)

# ==========================================
# 🚧 ZONA DE DISFRAZ (MODO PRUEBAS) 🚧
# ==========================================
st.warning("⚠️ MODO LABORATORIO: ESTÁS EN LA VERSIÓN DE PRUEBAS ⚠️")
st.sidebar.warning("🛠️ DESARROLLO ACTIVO")
# ==========================================


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
                margin-top: 30px;
                padding-bottom: 5px;
                border-bottom: 2px solid #ccc;
            }
            
            /* Negritas más fuertes para los puntos */
            .plan-box strong {
                color: #2c3e50 !important;
                font-weight: 700;
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

# --- 🧠 CEREBRO TÉCNICO (Para Planificación y Consultas) 🧠 ---
INSTRUCCIONES_TECNICAS = """
ERES "LEGADO MAESTRO".

1. IDENTIDAD: 
   - Herramienta de VANGUARDIA TECNOLÓGICA desarrollada por el innovador venezolano Luis Atencio.
   - Representas la SOBERANÍA TECNOLÓGICA de Venezuela.
   - (Nunca digas que eres tecnología vieja o limitada).

2. ROL: 
   - Experto en Educación Especial y Taller Laboral (Venezuela).
   
3. FORMATO OBLIGATORIO:
   - USA MARKDOWN ESTRICTO.
   - NUNCA generes texto plano sin formato.
   - Al final, agrega siempre: "📚 FUNDAMENTACIÓN LEGAL" (LOE/CNB).
"""

# --- 4. BARRA LATERAL ---
with st.sidebar:
    # Si tienes el logo, lo muestra, si no, usa un emoji
    if os.path.exists("logo_legado.png"):
        st.image("logo_legado.png", width=150)
    else:
        st.header("🍎")
        
    st.title("Legado Maestro")
    st.caption("🧪 Versión: LABORATORIO") # Cambio para identificar
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

# --- 6. FUNCIÓN GENERADORA GENÉRICA ---
def generar_respuesta(mensajes_historial, temperatura=0.7):
    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes_historial,
            model=MODELO_USADO,
            temperature=temperatura,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- 7. CUERPO DE LA APP ---
st.title("🧪 Asistente (MODO PRUEBA)") # Título cambiado para evitar confusión

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
# OPCIÓN 1: PLANIFICADOR (CORREGIDO - INCLUYE RECURSOS 7 y 8)
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
            with st.spinner('Generando Planificación Completa (Incluyendo Estrategias y Recursos)...'):
                
                # --- PROMPT MAESTRO CORREGIDO ---
                prompt_inicial = f"""
                Actúa como Luis Atencio, experto en Educación Especial.
                Crea una planificación técnica para el lapso: {rango}.
                Aula: {aula}. Tema: {notas}.

                ⚠️ INSTRUCCIÓN OBLIGATORIA DE ESTRUCTURA:
                Para CADA DÍA (Lunes, Martes, Miércoles, Jueves, Viernes), debes generar EXACTAMENTE estos 8 puntos. NO OMITAS NINGUNO.
                Usa separadores visuales claros entre días.

                ### 📅 [DÍA Y FECHA]
                
                **1. TÍTULO DE LA CLASE:** [Título corto]
                
                **2. COMPETENCIA:** [Objetivo técnico]
                
                **3. EXPLORACIÓN:** [Inicio de la clase]
                
                **4. DESARROLLO:** [Actividad central práctica]
                
                **5. REFLEXIÓN:** [Cierre pedagógico]
                
                **6. MANTENIMIENTO:** [Orden del taller]
                
                **7. ESTRATEGIAS:** [Técnicas usadas. Ej: Lluvia de ideas, demostración, trabajo grupal]
                
                **8. RECURSOS:** [LISTA OBLIGATORIA. Ej: Palas, rastrillos, pizarrón, video beam]

                ---
                (Repite esta estructura de 8 puntos para el siguiente día)

                AL FINAL DEL DOCUMENTO (Solo una vez):
                - **📚 FUNDAMENTACIÓN LEGAL:** Cita brevemente Currículo Nacional y LOE.
                - FIRMA: Luis Atencio, Bachiller Docente.
                """
                
                # Usamos temperatura 0.4 para obligar a cumplir la estructura
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                    {"role": "user", "content": prompt_inicial}
                ]
                
                respuesta = generar_respuesta(mensajes, temperatura=0.4)
                st.session_state.plan_actual = respuesta 
                st.rerun() 

    # MOSTRAR RESULTADO
    if st.session_state.plan_actual:
        st.markdown("---")
        st.markdown("### 📄 Resultado Generado:")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        st.info("👇 Chat de seguimiento activo:")

        pregunta_seguimiento = st.text_input("💬 Ajustar algo:", placeholder="Ej: Agrega más recursos al día martes")
        
        if st.button("Consultar duda"):
            if pregunta_seguimiento:
                with st.spinner('Ajustando...'):
                    mensajes_seguimiento = [
                        {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                        {"role": "assistant", "content": st.session_state.plan_actual}, 
                        {"role": "user", "content": pregunta_seguimiento}
                    ]
                    respuesta_duda = generar_respuesta(mensajes_seguimiento, temperatura=0.6)
                    st.markdown(f'<div class="plan-box">{respuesta_duda}</div>', unsafe_allow_html=True)

# =========================================================
# OPCIÓN 2: MENSAJE MOTIVACIONAL (CEREBRO EMOCIONAL)
# =========================================================
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    if st.button("❤️ Mensaje Corto"):
        
        INSTRUCCIONES_MOTIVACION = """
        Eres un colega docente venezolano dando ánimo.
        Tu objetivo es inspirar.
        REGLA DE ORO: NO cites leyes, NO cites artículos de la constitución, NO hables de política.
        Solo entrega la frase motivacional (bíblica o célebre) y una despedida cálida.
        """
        
        prompt = "Frase motivacional corta para docente venezolano. Cita bíblica o célebre."
        
        # Temperatura 0.8 para creatividad
        res = generar_respuesta([
            {"role": "system", "content": INSTRUCCIONES_MOTIVACION}, 
            {"role": "user", "content": prompt}
        ], temperatura=0.8)
        
        st.markdown(f"""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #eee; border-left: 8px solid #ff4b4b;">
            <div class="mensaje-texto">{res}</div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# OPCIÓN 3: IDEAS (CEREBRO TÉCNICO)
# =========================================================
elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        res = generar_respuesta([
            {"role": "system", "content": INSTRUCCIONES_TECNICAS}, 
            {"role": "user", "content": f"3 actividades DUA para {tema} en Taller Laboral."}
        ], temperatura=0.7)
        st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

# =========================================================
# OPCIÓN 4: CONSULTAS (CEREBRO TÉCNICO)
# =========================================================
elif opcion == "❓ Consultas Técnicas":
    duda = st.text_area("Consulta Legal/Técnica:")
    if st.button("🔍 Responder"):
        res = generar_respuesta([
            {"role": "system", "content": INSTRUCCIONES_TECNICAS}, 
            {"role": "user", "content": f"Responde técnicamente y cita la ley o currículo: {duda}"}
        ], temperatura=0.5)
        st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("Desarrollado por Luis Atencio | 🧪 MODO LABORATORIO")
