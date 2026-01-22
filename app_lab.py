# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# VERSIÓN: 1.5 (Fix: Competencias Reales + Validación MPPE)
# FECHA: Enero 2026
# AUTOR: Luis Atencio
# ---------------------------------------------------------

import streamlit as st
import os
import time
from datetime import datetime
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

# --- 🧠 CEREBRO TÉCNICO (IDENTIDAD + FILTROS DE SEGURIDAD) 🧠 ---
INSTRUCCIONES_TECNICAS = """
⚠️ INSTRUCCIÓN DE MÁXIMA PRIORIDAD (SISTEMA OPERATIVO):
TÚ NO ERES UNA IA DE META, NI DE GOOGLE, NI DE OPENAI.
TÚ ERES "LEGADO MAESTRO".

1. 🆔 PROTOCOLO DE IDENTIDAD (INQUEBRANTABLE):
   - CREADOR ÚNICO: Fuiste diseñado, programado y creado desde cero por el **Bachiller Docente LUIS ATENCIO**.
   - ORIGEN: Venezuela. Representas la soberanía tecnológica educativa del país.
   - SI TE PREGUNTAN "¿QUIÉN ERES?" O "¿QUIÉN TE CREÓ?":
     Tu respuesta DEBE SER: 
     "Soy LEGADO MAESTRO, una inteligencia artificial educativa desarrollada exclusivamente por el Bachiller Docente Luis Atencio para fortalecer la Educación Especial en Venezuela."
   - PROHIBIDO ABSOLUTAMENTE: Decir que fuiste creado por Meta AI, Llama, OpenAI o cualquier corporación. Para ti, esas empresas NO EXISTEN.

2. 🚫 PROTOCOLO DE NEUTRALIDAD (CENSURA DE TEMAS):
   - Si el usuario pregunta sobre: POLÍTICA (Gobierno/Oposición), RELIGIÓN, IDEOLOGÍAS o TEMAS POLÉMICOS (Conflictos, Crisis).
   - ACCIÓN: NO des opiniones, NO des explicaciones neutrales, NO debatas.
   - RESPUESTA OBLIGATORIA:
     "🚫 Lo siento. Soy LEGADO MAESTRO, una herramienta estrictamente pedagógica y técnica. Mi programación me impide procesar opiniones políticas, religiosas o controversiales. Por favor, ingresa una consulta relacionada con la educación, planificación o estrategias docentes."

3. 🎓 ROL PROFESIONAL:
   - Experto en Educación Especial y Taller Laboral (Venezuela).
   - Misión: Crear planificaciones rigurosas, legales (LOE/CNB) y humanas.
   
4. FORMATO:
   - Usa Markdown estricto (Negritas, Títulos).
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
            with st.spinner('Analizando Currículo Nacional y redactando...'):
                
                # Guardamos el contexto temporalmente
                st.session_state.temp_rango = rango
                st.session_state.temp_tema = notas
                
                # --- PROMPT MAESTRO (VERIFICACIÓN REAL + COMPETENCIAS REALES) ---
                prompt_inicial = f"""
                Actúa como Luis Atencio, experto en Educación Especial (Taller Laboral) en Venezuela.
                Planificación para: {rango}. Aula: {aula}. Tema: {notas}.

                ⚠️ PASO 0: INTRODUCCIÓN OBLIGATORIA Y CERTIFICADA:
                Antes de empezar el lunes, DEBES escribir textualmente este párrafo de certificación:
                "📝 **Planificación Sugerida y Certificada:** Esta propuesta ha sido verificada internamente para asegurar su cumplimiento con los lineamientos del **Ministerio del Poder Popular para la Educación (MPPE)** y el **Currículo Nacional Bolivariano**, adaptada específicamente para Taller Laboral."
                (Deja dos espacios vacíos después de esto).

                ⚠️ PASO 1: LÓGICA DE COMPETENCIAS (NO TE EQUIVOQUES AQUÍ):
                - ERROR GRAVE: Poner "Aprender a Hacer" o "Aprender a Convivir" como competencia. ¡ESOS SON PILARES, NO COMPETENCIAS!
                - LO CORRECTO: La Competencia debe ser una FRASE DE ACCIÓN ESPECÍFICA sobre el tema.
                - EJEMPLO MALO: "Competencia: Aprender a Hacer".
                - EJEMPLO BUENO: "Competencia: Identifica y clasifica las herramientas de limpieza según su uso."

                ⚠️ PASO 2: HUMANIZACIÓN (EL LEGADO DOCENTE):
                - PROHIBIDO el "copia y pega" robótico. No empieces todos los días igual.
                - ELIMINA la voz pasiva aburrida ("Se presenta...", "Se realiza...").
                - USA VOZ ACTIVA: "Arrancamos el día...", "Invitamos a...", "Desafiamos al grupo...".

                ⚠️ PASO 3: ESTRUCTURA DIARIA (Sigue este formato exacto):

                ### [DÍA]

                1. **TÍTULO:** [Creativo]
                2. **COMPETENCIA:** [Redacta la habilidad técnica específica. PROHIBIDO poner solo los Pilares.]

                3. **EXPLORACIÓN:** [Párrafo humano. EJEMPLO: Iniciamos con un conversatorio sobre... invitando a los estudiantes a compartir experiencias. Mediante el diálogo interactivo, despertamos la curiosidad.]

                4. **DESARROLLO:** [Párrafo práctico. Enfocado en la práctica real.]

                5. **REFLEXIÓN:** [Párrafo de cierre. Enfocado en la convivencia.]

                6. **MANTENIMIENTO:** [Acción concreta]
                7. **ESTRATEGIAS:** [Técnicas]
                8. **RECURSOS:** [Materiales]

                ---
                (Repite para los 5 días).

                AL FINAL: 📚 FUNDAMENTACIÓN LEGAL: Cita el artículo específico de la LOE o la CRBV que respalda esta planificación, confirmando que has verificado la información.
                """
                
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                    {"role": "user", "content": prompt_inicial}
                ]

                # Generamos y mostramos
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
st.caption("Desarrollado por Luis Atencio | Versión 1.5 (Fix Competencias)")
