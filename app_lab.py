# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# VERSIÓN: 1.3 (Fix Definitivo: Estrategias, Recursos y Formato)
# FECHA: Enero 2026
# AUTOR: Luis Atencio
# ---------------------------------------------------------

import streamlit as st
import os
import time
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered"
)

# 1. Función para limpiar cédulas
def limpiar_id(v): return str(v).strip().split('.')[0].replace(',', '').replace('.', '')

# 2. Inicializar Estado de Autenticación
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'u' not in st.session_state:
    st.session_state.u = None

# 3. Conexión a Base de Datos (Solo si se necesita login)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_HOJA = st.secrets["GSHEETS_URL"]
except:
    st.error("⚠️ Error conectando con la Base de Datos.")
    st.stop()

if not st.session_state.auth:
    st.title("🛡️ Acceso Legado Maestro")
    st.markdown("Ingrese sus credenciales para acceder a la plataforma.")
    
    col_a, col_b = st.columns([1,2])
    with col_a:
        if os.path.exists("logo_legado.png"):
            st.image("logo_legado.png", width=150)
        else:
            st.header("🍎")
    
    with col_b:
        c_in = st.text_input("Cédula de Identidad:", key="login_c")
        p_in = st.text_input("Contraseña:", type="password", key="login_p")
        
        if st.button("🔐 Iniciar Sesión"):
            try:
                # Leemos la hoja USUARIOS
                df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
                df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
                
                # Verificamos credenciales
                match = df_u[(df_u['C_L'] == limpiar_id(c_in)) & (df_u['CLAVE'] == p_in)]
                
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.u = match.iloc[0].to_dict()
                    st.success("¡Bienvenido!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
    
    # ESTA LÍNEA ES MÁGICA: Detiene la carga aquí si no hay login.
    # Así no tienes que indentar ni mover tu código original de abajo.
    st.stop()

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
    st.markdown("---")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("T.E.L E.R.A.C")
    
    if st.button("🗑️ Limpiar Memoria"):
        st.session_state.plan_actual = ""
        st.rerun()
        st.markdown("---")
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.auth = False
        st.session_state.u = None
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
# OPCIÓN 1: PLANIFICADOR (FLUJO: BORRADOR -> GUARDAR)
# =========================================================
if opcion == "📝 Planificación Profesional":
    st.subheader("Planificación Técnica (Taller Laboral)")
    
    # Entradas de datos
    col1, col2 = st.columns(2)
    with col1:
        rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de Enero")
    with col2:
        aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios Generales")
    
    notas = st.text_area("Notas del Docente / Tema:", height=150)

    # --- PASO 1: GENERAR BORRADOR (NO GUARDA EN BD) ---
    if st.button("🚀 Generar Borrador con IA"):
        if rango and notas:
            with st.spinner('Redactando propuesta...'):
                
                # Guardamos el contexto temporalmente
                st.session_state.temp_rango = rango
                st.session_state.temp_tema = notas
                
        # --- PROMPT MODO TWITTER (MAX 280 CARACTERES) ---
                prompt_inicial = f"""
                Actúa como Luis Atencio. Planificación técnica para: {rango}.
                Aula: {aula}. Tema: {notas}.

                ⚠️ INSTRUCCIONES DE FORMATO:
                - Antes del título de cada día (Ej: "### Lunes"), deja UNA LÍNEA VACÍA.

                ⚠️ CONTROL DE EXTENSIÓN ESTRICTO (Regla del Tweet):
                - En EXPLORACIÓN, DESARROLLO y REFLEXIÓN:
                - Imagina que estás escribiendo un TWEET.
                - Tienes un LÍMITE DURO de 280 caracteres (unas 40-50 palabras) por punto.
                - Ve directo al grano. NO uses introducciones como "En esta parte haremos...". Empieza con el verbo.
                - Ejemplo perfecto: "Los estudiantes clasifican herramientas reales de limpieza en una mesa, debatiendo en grupos de 3 cuál es el uso correcto de cada una para fijar el conocimiento práctico." (Esto es un Tweet perfecto).

                ESTRUCTURA DIARIA (Lunes a Viernes):

                ### [DÍA]
                
                1. **TÍTULO:** [Corto]
                2. **COMPETENCIA:** [Objetivo]
                3. **EXPLORACIÓN:** [Longitud de un TWEET. Máx 280 caracteres.]
                4. **DESARROLLO:** [Longitud de un TWEET. Máx 280 caracteres.]
                5. **REFLEXIÓN:** [Longitud de un TWEET. Máx 280 caracteres.]
                6. **MANTENIMIENTO:** [Acción]
                7. **ESTRATEGIAS:** [Técnicas]
                8. **RECURSOS:** [Lista]

                ---
                (Repite estructura)

                AL FINAL: 📚 FUNDAMENTACIÓN LEGAL (LOE/CNB).
                """
                
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                    {"role": "user", "content": prompt_inicial}
                ]
                
                # Generamos y mostramos en pantalla (SOLO MEMORIA RAM)
                respuesta = generar_respuesta(mensajes, temperatura=0.4)
                st.session_state.plan_actual = respuesta
                st.rerun()

    # --- MOSTRAR RESULTADO Y OPCIÓN DE GUARDAR ---
    if st.session_state.plan_actual:
        st.markdown("---")
        st.info("👀 Revisa el borrador abajo. Si te gusta, guárdalo en tu carpeta.")
        
        # Muestra el plan en la caja bonita
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        # --- PASO 2: GUARDAR DEFINITIVO (SOLO SI EL USUARIO QUIERE) ---
        col_save_1, col_save_2 = st.columns([2,1])
        with col_save_1:
            if st.button("💾 SÍ, GUARDAR EN MI CARPETA"):
                try:
                    with st.spinner("Archivando en el expediente..."):
                        # 1. Leemos la base de datos actual
                        df_act = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                        
                        # 2. Preparamos el paquete de datos
                        # Usamos los datos guardados o los actuales
                        tema_guardar = st.session_state.get('temp_tema', notas)
                        
                        nueva_fila = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "USUARIO": st.session_state.u['NOMBRE'], # Nombre del docente logueado
                            "TEMA": tema_guardar,
                            "CONTENIDO": st.session_state.plan_actual,
                            "ESTADO": "GUARDADO",
                            "HORA_INICIO": "--", "HORA_FIN": "--"
                        }])
                        
                        # 3. Enviamos a Google Sheets
                        datos_actualizados = pd.concat([df_act, nueva_fila], ignore_index=True)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=datos_actualizados)
                        
                        st.success("✅ ¡Planificación archivada con éxito!")
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

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
st.caption("Desarrollado por Luis Atencio | Versión 1.3 (Fix Recursos)")
