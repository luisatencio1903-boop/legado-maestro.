# -----------------------------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# VERSIÓN: 3.2 (EDICIÓN ROBUSTA + VARIEDAD LÉXICA)
# FECHA: Enero 2026
# AUTOR: Luis Atencio (Bachiller Docente)
# INSTITUCIÓN: T.E.L E.R.A.C
# DESCRIPCIÓN: Asistente con IA para Educación Especial con navegación móvil limpia.
# -----------------------------------------------------------------------------

import streamlit as st
import os
import time
from datetime import datetime
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import re  # Librería para expresiones regulares (detectar fechas automáticamente)

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTADO INICIAL
# =============================================================================

st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered"
)

# -----------------------------------------------------------------------------
# FUNCIONES UTILITARIAS
# -----------------------------------------------------------------------------

def limpiar_id(v): 
    """
    Limpia el formato de la cédula para evitar errores de comparación.
    Ejemplo: Convierte 'V-12.345.678' en '12345678'.
    """
    return str(v).strip().split('.')[0].replace(',', '').replace('.', '')

# -----------------------------------------------------------------------------
# INICIALIZACIÓN DE VARIABLES DE SESIÓN (STATE)
# -----------------------------------------------------------------------------

if 'auth' not in st.session_state:
    st.session_state.auth = False

if 'u' not in st.session_state:
    st.session_state.u = None

# Control de navegación: "HOME" es la pantalla de inicio con los menús
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = "HOME"

# Variables de memoria para la IA (Persistencia temporal)
if 'plan_actual' not in st.session_state: 
    st.session_state.plan_actual = ""

if 'actividad_detectada' not in st.session_state: 
    st.session_state.actividad_detectada = ""

if 'redirigir_a_archivo' not in st.session_state: 
    st.session_state.redirigir_a_archivo = False

# =============================================================================
# 2. CONEXIÓN A BASE DE DATOS (GOOGLE SHEETS)
# =============================================================================

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Se requiere que en .streamlit/secrets.toml exista la clave GSHEETS_URL
    URL_HOJA = st.secrets["GSHEETS_URL"]
except Exception as e:
    st.error("⚠️ Error Crítico: No se pudo establecer conexión con la Base de Datos.")
    st.error(f"Detalle del error: {e}")
    st.stop()

# =============================================================================
# 3. LÓGICA DE NEGOCIO: GESTIÓN DE PLANIFICACIÓN ACTIVA
# =============================================================================

def obtener_plan_activa_usuario(usuario_nombre):
    """
    Obtiene la planificación activa actual del usuario desde la nube.
    Retorna un diccionario con los datos o None si no existe.
    """
    try:
        # Leemos con un TTL bajo para tener datos frescos
        df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=5)
        
        # Filtramos por usuario y estado activo
        plan_activa = df_activa[
            (df_activa['USUARIO'] == usuario_nombre) & 
            (df_activa['ACTIVO'] == True)
        ]
        
        if not plan_activa.empty:
            # Retornar la más reciente basada en fecha de activación
            return plan_activa.sort_values('FECHA_ACTIVACION', ascending=False).iloc[0].to_dict()
        return None
    except Exception as e:
        # Si la hoja no existe o hay error de lectura, retornamos None
        return None

def establecer_plan_activa(usuario_nombre, id_plan, contenido, rango, aula):
    """
    Establece una planificación específica como la 'Activa' para evaluaciones.
    Desactiva automáticamente cualquier otra planificación previa del usuario.
    """
    try:
        # Leer datos actuales o crear estructura si no existe
        try:
            df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=0)
        except:
            # Crear DataFrame vacío si la hoja no existe
            df_activa = pd.DataFrame(columns=[
                "USUARIO", "FECHA_ACTIVACION", "ID_PLAN", 
                "CONTENIDO_PLAN", "RANGO", "AULA", "ACTIVO"
            ])
        
        # 1. Desactivar cualquier planificación activa previa del mismo usuario
        mask_usuario = df_activa['USUARIO'] == usuario_nombre
        if not df_activa[mask_usuario].empty:
            df_activa.loc[mask_usuario, 'ACTIVO'] = False
        
        # 2. Agregar la nueva planificación activa
        nueva_activa = pd.DataFrame([{
            "USUARIO": usuario_nombre,
            "FECHA_ACTIVACION": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "ID_PLAN": id_plan,
            "CONTENIDO_PLAN": contenido,
            "RANGO": rango,
            "AULA": aula,
            "ACTIVO": True
        }])
        
        # Combinar y actualizar la hoja
        df_actualizado = pd.concat([df_activa, nueva_activa], ignore_index=True)
        conn.update(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", data=df_actualizado)
        return True
    except Exception as e:
        st.error(f"Error al establecer plan activa: {e}")
        return False

def desactivar_plan_activa(usuario_nombre):
    """
    Desactiva cualquier planificación activa del usuario sin borrar el registro histórico.
    """
    try:
        df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=0)
        mask_usuario = df_activa['USUARIO'] == usuario_nombre
        if not df_activa[mask_usuario].empty:
            df_activa.loc[mask_usuario, 'ACTIVO'] = False
            conn.update(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", data=df_activa)
        return True
    except:
        return False

# =============================================================================
# 4. SISTEMA DE AUTENTICACIÓN (LOGIN)
# =============================================================================

# --- LÓGICA DE PERSISTENCIA DE SESIÓN (AUTO-LOGIN VÍA URL) ---
query_params = st.query_params
usuario_en_url = query_params.get("u", None)

if not st.session_state.auth and usuario_en_url:
    try:
        df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
        df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
        match = df_u[df_u['C_L'] == usuario_en_url]
        
        if not match.empty:
            st.session_state.auth = True
            st.session_state.u = match.iloc[0].to_dict()
        else:
            st.query_params.clear()
    except:
        pass 

# --- INTERFAZ DE LOGIN ---
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
                df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
                df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
                cedula_limpia = limpiar_id(c_in)
                match = df_u[(df_u['C_L'] == cedula_limpia) & (df_u['CLAVE'] == p_in)]
                
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.u = match.iloc[0].to_dict()
                    st.query_params["u"] = cedula_limpia # Anclamos sesión
                    st.success("¡Bienvenido, Docente!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
    st.stop()

# =============================================================================
# 5. ESTILOS CSS (DISEÑO VISUAL ROBUSTO)
# =============================================================================
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* CAJA DE PLANIFICACIÓN */
            .plan-box {
                background-color: #f0f2f6 !important;
                color: #000000 !important; 
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #0068c9;
                margin-bottom: 20px;
                font-family: 'Arial', sans-serif;
                font-size: 1.05em;
                line-height: 1.6;
            }
            .plan-box h3 {
                color: #0068c9 !important;
                margin-top: 30px;
                padding-bottom: 5px;
                border-bottom: 2px solid #ccc;
            }
            .plan-box strong {
                color: #2c3e50 !important;
                font-weight: 700;
            }

            /* CAJA DE EVALUACIÓN */
            .eval-box {
                background-color: #e8f5e9 !important;
                color: #000000 !important;
                padding: 15px;
                border-radius: 8px;
                border-left: 5px solid #2e7d32;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            .eval-box h4 { color: #2e7d32 !important; }

            /* CAJA DE MENSAJES MOTIVACIONALES */
            .mensaje-texto {
                color: #000000 !important;
                font-family: 'Helvetica', sans-serif;
                font-size: 1.2em; 
                font-weight: 500;
                line-height: 1.4;
            }
            
            /* CONSULTOR DEL ARCHIVO */
            .consultor-box {
                background-color: #e8f4f8 !important;
                color: #000000 !important;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #b3d7ff;
                margin-top: 10px;
            }
            .consultor-box p, .consultor-box li, .consultor-box strong {
                color: #000000 !important;
            }

            /* ESTILOS PARA BARRAS DE HERRAMIENTAS (SELECTBOX) */
            /* Esto hace que los menús se vean más prominentes en móvil */
            .stSelectbox label {
                font-size: 1.25rem !important;
                font-weight: bold !important;
                color: #0068c9 !important;
                margin-bottom: 8px;
            }
            
            /* BOTÓN DE VOLVER AL INICIO */
            .boton-volver {
                width: 100%;
                margin-bottom: 20px;
                background-color: #f0f2f6;
                border: 1px solid #ccc;
            }
            
            /* DIVISORES */
            hr {
                margin-top: 1rem;
                margin-bottom: 1rem;
                border: 0;
                border-top: 2px solid rgba(0,0,0,.1);
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =============================================================================
# 6. CONFIGURACIÓN DE INTELIGENCIA ARTIFICIAL (GROQ)
# =============================================================================

try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        MODELO_USADO = "llama-3.3-70b-versatile" 
    else:
        st.error("⚠️ Falta la API Key de Groq en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión inicial con IA: {e}")
    st.stop()

# --- PROMPTS DE SISTEMA (CEREBRO TÉCNICO HUMANIZADO) ---
# Aquí se define la personalidad y las reglas estrictas para evitar lo robótico

INSTRUCCIONES_TECNICAS = """
⚠️ ERES "LEGADO MAESTRO". 
TU IDENTIDAD: Inteligencia Artificial Educativa Venezolana, creada por el Bachiller Docente Luis Atencio.
TU ROL: Experto en Educación Especial y Taller Laboral (Estudiantes con Discapacidad Intelectual, Autismo, Síndrome de Down).

🚨 REGLAS DE ORO (ANTI-ROBOT):
1. **TONO HUMANO Y CÁLIDO:** Nada de lenguaje burocrático. Eres un docente hablando con sus estudiantes.
2. **CERO ACTIVIDADES ABSTRACTAS:** 
   - PROHIBIDO mandar a "Investigar", "Hacer resúmenes", "Leer textos densos" o "Debates históricos complejos".
   - Los estudiantes aprenden HACIENDO.
3. **VARIEDAD DE LENGUAJE (IMPORTANTE):**
   - NO empieces todos los días diciendo "Invitamos a" o "Compartimos".
   - USA SINÓNIMOS LÚDICOS: "Hoy descubriremos...", "Manos a la obra con...", "Arrancamos la aventura de...", "Exploraremos...", "Jugaremos a...", "Nos divertiremos creando...".
   - Haz que cada día suene diferente y emocionante.
4. **ENFOQUE VIVENCIAL:**
   - Actividades concretas: Dibujar, recortar, limpiar (práctica), dramatizar, cantar, modelar con plastilina.
"""

# --- FUNCIÓN GENERADORA GENÉRICA ---
def generar_respuesta(mensajes_historial, temperatura=0.7):
    """
    Envía la solicitud a Groq y maneja posibles errores de conexión.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes_historial,
            model=MODELO_USADO,
            temperature=temperatura,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error de conexión con el cerebro del sistema: {e}"

# =============================================================================
# 7. BARRA LATERAL (MODO INFORMATIVO)
# =============================================================================
# NOTA: La navegación real está en el cuerpo principal. Esto es solo panel de estado.

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
    
    # --- SECCIÓN: ESTADO DE PLANIFICACIÓN ACTIVA ---
    st.markdown("---")
    plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    if plan_activa:
        st.success("📌 **Planificación Activa**")
        with st.expander("Ver detalles", expanded=False):
            st.caption(f"**Rango:** {plan_activa['RANGO']}")
            st.caption(f"**Aula:** {plan_activa['AULA']}")
            st.caption(f"Activada: {plan_activa['FECHA_ACTIVACION'].split()[0]}")
    else:
        st.warning("⚠️ **Sin planificación activa**")
        st.caption("Ve a 'Mi Archivo' para activar una")
    
    st.markdown("---")
    
    # --- BOTONES DE CONTROL DE SESIÓN ---
    if st.button("🗑️ Limpiar Memoria"):
        st.session_state.plan_actual = ""
        st.session_state.actividad_detectada = ""
        st.rerun()
    
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.auth = False
        st.session_state.u = None
        st.query_params.clear() 
        st.rerun()

# =============================================================================
# 8. CONTROLADOR DE NAVEGACIÓN (STATE MACHINE)
# =============================================================================

# Verificamos si algún proceso interno solicitó redirección
if st.session_state.redirigir_a_archivo:
    st.session_state.pagina_actual = "📂 Mi Archivo Pedagógico"
    st.session_state.redirigir_a_archivo = False

# =============================================================================
# VISTA 1: HOME (PANTALLA DE INICIO - MENU DE BARRAS)
# =============================================================================

if st.session_state.pagina_actual == "HOME":
    
    st.title("🍎 Asistente Educativo - Zulia")
    st.info("👋 Saludos, Colega. ¿Qué herramienta vamos a usar hoy?")
    
    st.divider()
    
    # --- BARRA 1: HERRAMIENTAS DE GESTIÓN PRINCIPAL ---
    st.markdown("### 🛠️ GESTIÓN DOCENTE")
    seleccion_principal = st.selectbox(
        "Seleccione herramienta principal:",
        [
            "(Seleccione una opción...)",
            "🧠 PLANIFICADOR INTELIGENTE",
            "📜 PLANIFICADOR MINISTERIAL (NUEVO)",
            "📝 Evaluar Alumno (NUEVO)",
            "📊 Registro de Evaluaciones (NUEVO)",
            "📂 Mi Archivo Pedagógico"
        ],
        key="selector_home_gestion"
    )

    # --- BARRA 2: RECURSOS EXTRA Y APOYO ---
    st.markdown("### 🧩 RECURSOS EXTRA")
    seleccion_secundaria = st.selectbox(
        "Seleccione recurso de apoyo:",
        [
            "(Seleccione una opción...)",
            "🌟 Mensaje Motivacional", 
            "💡 Ideas de Actividades", 
            "❓ Consultas Técnicas"
        ],
        key="selector_home_extras"
    )

    # --- LÓGICA DE DETECCIÓN DE CAMBIO ---
    # Si el usuario selecciona algo, actualizamos el estado y recargamos la página.
    
    if seleccion_principal != "(Seleccione una opción...)":
        st.session_state.pagina_actual = seleccion_principal
        st.rerun()
        
    if seleccion_secundaria != "(Seleccione una opción...)":
        st.session_state.pagina_actual = seleccion_secundaria
        st.rerun()

# =============================================================================
# VISTA 2: PANTALLAS DE HERRAMIENTAS (PANTALLA COMPLETA)
# =============================================================================
else:
    # --- ENCABEZADO DE NAVEGACIÓN (BOTÓN VOLVER AL INICIO) ---
    col_nav_1, col_nav_2 = st.columns([1, 4])
    
    with col_nav_1:
        # Botón grande y claro para regresar
        if st.button("⬅️ VOLVER AL INICIO", key="btn_volver_home", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
            
    with col_nav_2:
        # Título de la sección actual
        st.subheader(f"{st.session_state.pagina_actual}")
        
    st.divider()
    
    # Variable auxiliar para mantener compatibilidad
    opcion = st.session_state.pagina_actual

    # -----------------------------------------------------------------------------------
    # HERRAMIENTA 1: PLANIFICADOR INTELIGENTE (VERSIÓN HUMANIZADA)
    # -----------------------------------------------------------------------------------
    if opcion == "🧠 PLANIFICADOR INTELIGENTE":
        st.markdown("**Diseño de Planificación desde Cero (Adaptada a Educación Especial)**")
        st.markdown("Ingrese los datos básicos. Legado Maestro creará actividades vivenciales y sencillas.")
        
        col1, col2 = st.columns(2)
        with col1:
            rango = st.text_input("Lapso (Fechas):", placeholder="Ej: 19 al 23 de Enero")
        with col2:
            aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios Generales")
        
        notas = st.text_area("Notas del Docente / Tema Generador:", height=150)

        # --- GENERAR BORRADOR ---
        if st.button("🚀 Generar Planificación Humanizada"):
            if rango and notas:
                with st.spinner('Creando estrategias vivenciales y lúdicas...'):
                    
                    st.session_state.temp_rango = rango
                    st.session_state.temp_tema = notas
                    
                    # --- PROMPT ESPECÍFICO DE "NO ROBOT" ---
                    prompt_inicial = f"""
                    CONTEXTO: Educación Especial (Taller Laboral) en Venezuela.
                    FECHAS: {rango}. AULA: {aula}. TEMA: {notas}.

                    ⚠️ TU MISIÓN:
                    Crear una planificación **HUMANA, CÁLIDA Y VARIADA**.
                    
                    1. **VARIEDAD DE INICIOS:** NO empieces siempre con "Invitamos". Usa: "Hoy exploramos", "Descubrimos", "Jugamos a", "Nos reunimos para".
                    2. **ACTIVIDADES CONCRETAS:** Los alumnos tienen discapacidad intelectual. NO pueden "investigar" solos. Tienen que: Ver, tocar, pintar, dramatizar, limpiar (práctica), ordenar.

                    ESTRUCTURA DIARIA (Lunes a Viernes):
                    
                    ### [DÍA]
                    1. **TÍTULO LÚDICO:** (Ej: "Detectives de la Limpieza", "Artistas del Reciclaje")
                    2. **COMPETENCIA:** (Verbo simple: Identifica, Reconoce, Colabora)
                    3. **EXPLORACIÓN:** (Inicio motivador: Canción, Títeres, Pregunta generadora)
                    4. **DESARROLLO:** (Actividad central práctica. ¿Qué hacen sus manos?)
                    5. **REFLEXIÓN:** (Cierre vivencial. ¿Cómo nos sentimos?)
                    6. **ESTRATEGIAS:** (Ej: Modelado, Instrucción verbal, Apoyo físico)
                    7. **RECURSOS:** (Materiales tangibles)
                    
                    FINAL: 📚 FUNDAMENTACIÓN LEGAL (Breve cita LOE/CRBV).
                    """
                    
                    mensajes = [
                        {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                        {"role": "user", "content": prompt_inicial}
                    ]
                    respuesta = generar_respuesta(mensajes, temperatura=0.6)
                    st.session_state.plan_actual = respuesta
                    st.rerun()

    # -----------------------------------------------------------------------------------
    # HERRAMIENTA 2: PLANIFICADOR MINISTERIAL (ANTI-REPETICIÓN)
    # -----------------------------------------------------------------------------------
    elif opcion == "📜 PLANIFICADOR MINISTERIAL (NUEVO)":
        st.markdown("**Adaptación y Humanización de Lineamientos**")
        st.info("Pega aquí el mensaje de WhatsApp del Ministerio/Zona. Legado Maestro extraerá las fechas y **enriquecerá las actividades repetitivas** (como 'Limpieza') para que sean variadas y pedagógicas.")
        
        # Solo pedimos el Aula, la fecha viene en el texto
        aula_min = st.text_input("Aula/Taller (Contexto para la adaptación):", value="Mantenimiento y Servicios Generales")
            
        texto_whatsapp = st.text_area("Pegue aquí el texto (WhatsApp/Correo):", height=300, 
                                      placeholder="Ej: ✨ PLAN ESTRATÉGICO SUGERIDO... SEMANA 01/12 al 05/12/25...")
        
        if st.button("🪄 Adaptar y Variar Actividades"):
            if texto_whatsapp:
                with st.spinner(f"Traduciendo 'lenguaje ministerial' a 'lenguaje vivencial' para {aula_min}..."):
                    
                    # Intentamos extraer una fecha aproximada
                    fechas_encontradas = re.findall(r'\d{1,2}[/-]\d{1,2}', texto_whatsapp)
                    rango_detectado = f"Semana {fechas_encontradas[0]}" if fechas_encontradas else "Semana Ministerial"
                    
                    st.session_state.temp_rango = rango_detectado
                    st.session_state.temp_tema = "Adaptación Ministerial Enriquecida"
                    
                    # --- PROMPT DE "VARIEDAD Y ENRIQUECIMIENTO" ---
                    prompt_adaptacion = f"""
                    ERES UN EXPERTO EN ADAPTACIÓN CURRICULAR (TALLER LABORAL).
                    
                    **SITUACIÓN:**
                    Recibiste este texto del Ministerio: "{texto_whatsapp}"
                    
                    **EL PROBLEMA:**
                    1. A veces el texto es repetitivo (Ej: Dice "Limpieza" todos los días).
                    2. A veces es muy abstracto (Ej: "Debate histórico") y mis alumnos con discapacidad no pueden hacerlo.
                    
                    **TU SOLUCIÓN (REGLA DE VARIEDAD):**
                    1. **SI DICE "LIMPIEZA" (Repetido):** Transfórmalo.
                       - Lunes: Conocer las herramientas (Escoba, Coleto).
                       - Martes: Normas de seguridad (Cuidado con el cloro).
                       - Miércoles: Práctica guiada (Limpiar una mesa juntos).
                       - Jueves: Ordenar el estante.
                    2. **SI DICE "INVESTIGAR/DEBATIR":** Adáptalo.
                       - Cambia a: "Ver un video", "Dramatizar una escena", "Colorear al personaje".
                    3. **USA LENGUAJE VARIADO:** No empieces todos los días igual. Usa: "Hoy descubrimos", "Nos divertimos con", "Manos a la obra".
                    
                    **SALIDA OBLIGATORIA (MARKDOWN):**
                    
                    ### [DÍA Y FECHA DETECTADA]
                    1. **LINEAMIENTO ORIGINAL:** [Resumen breve]
                    2. **NUESTRA ADAPTACIÓN:** [Título atractivo]
                    3. **COMPETENCIA:** [Verbo sencillo]
                    4. **EXPLORACIÓN:** [Inicio motivador]
                    5. **DESARROLLO:** [Actividad práctica paso a paso]
                    6. **REFLEXIÓN:** [Cierre vivencial]
                    7. **ESTRATEGIAS:** [Técnicas docentes]
                    8. **RECURSOS:** [Materiales]
                    """
                    
                    mensajes = [
                        {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                        {"role": "user", "content": prompt_adaptacion}
                    ]
                    
                    respuesta_adaptada = generar_respuesta(mensajes, temperatura=0.65) # Temperatura un poco más alta para creatividad
                    st.session_state.plan_actual = respuesta_adaptada
                    st.rerun()
            else:
                st.warning("⚠️ Por favor pegue el texto de la planificación.")

    # -----------------------------------------------------------------------------------
    # BLOQUE DE GUARDADO (COMÚN PARA AMBOS PLANIFICADORES)
    # -----------------------------------------------------------------------------------
    if st.session_state.plan_actual and (opcion == "🧠 PLANIFICADOR INTELIGENTE" or opcion == "📜 PLANIFICADOR MINISTERIAL (NUEVO)"):
        st.markdown("---")
        st.info("👀 Revisa el borrador abajo. Nota cómo se han variado las actividades.")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        col_save_1, col_save_2 = st.columns([2,1])
        with col_save_1:
            if st.button("💾 SÍ, GUARDAR EN MI CARPETA"):
                try:
                    with st.spinner("Archivando en el expediente..."):
                        df_act = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                        
                        tema_guardar = st.session_state.get('temp_tema', 'Planificación General')
                        if len(tema_guardar) > 50: tema_guardar = tema_guardar[:50] + "..."
                        
                        nueva_fila = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "USUARIO": st.session_state.u['NOMBRE'], 
                            "TEMA": tema_guardar,
                            "CONTENIDO": st.session_state.plan_actual,
                            "ESTADO": "GUARDADO",
                            "HORA_INICIO": "--", "HORA_FIN": "--"
                        }])
                        datos_actualizados = pd.concat([df_act, nueva_fila], ignore_index=True)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=datos_actualizados)
                        st.success("✅ ¡Planificación archivada con éxito!")
                        
                        time.sleep(1)
                        st.session_state.pagina_actual = "📂 Mi Archivo Pedagógico"
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # -----------------------------------------------------------------------------------
    # HERRAMIENTA 3: EVALUAR ALUMNO (NUEVO)
    # -----------------------------------------------------------------------------------
    elif opcion == "📝 Evaluar Alumno (NUEVO)":
        st.subheader("Evaluación Diaria Inteligente")
        
        # CÁLCULO DE FECHA (Hora Venezuela)
        from datetime import timedelta
        fecha_segura_ve = datetime.utcnow() - timedelta(hours=4)
        fecha_hoy_str = fecha_segura_ve.strftime("%d/%m/%Y")
        dia_semana_hoy = fecha_segura_ve.strftime("%A")
        
        plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
        
        if not plan_activa:
            st.error("🚨 **NO TIENES UNA PLANIFICACIÓN ACTIVA**")
            st.info("Ve a '📂 Mi Archivo Pedagógico' para activar una.")
        else:
            with st.container():
                st.success(f"**📌 EVALUANDO CONTRA:** {plan_activa['RANGO']}")
                st.caption(f"Aula: {plan_activa['AULA']} | Activada: {plan_activa['FECHA_ACTIVACION']}")
            
            st.markdown("---")
            
            col_btn, col_info = st.columns([1, 2])
            with col_btn:
                if st.button("🔍 Buscar Actividad de HOY", type="primary"):
                    try:
                        with st.spinner(f"Analizando..."):
                            contenido_planificacion = plan_activa['CONTENIDO_PLAN']
                            # Prompt para extracción precisa
                            prompt_busqueda = f"""
                            PLANIFICACIÓN: {contenido_planificacion[:10000]}
                            HOY ES: {fecha_hoy_str} ({dia_semana_hoy}). 
                            ¿Qué actividad toca hoy? Responde SOLO el título o "NO HAY ACTIVIDAD".
                            """
                            resultado = generar_respuesta([{"role": "user", "content": prompt_busqueda}], temperatura=0.1)
                            st.session_state.actividad_detectada = resultado.strip().replace('"', '').replace("'", "")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with col_info:
                if st.session_state.actividad_detectada:
                    st.success(f"Encontrado: **{st.session_state.actividad_detectada}**")
            
            st.markdown("---")
            st.subheader("Registro de Evaluación")
            
            actividad_final = st.text_input(
                "**Actividad:**", 
                value=st.session_state.get('actividad_detectada', ''), 
                disabled=True
            )
            
            estudiante = st.text_input("**Nombre del Estudiante:**", placeholder="Ej: Juan Pérez")
            anecdota = st.text_area("**Observación del Desempeño:**", height=100)
            
            if st.button("⚡ Generar Evaluación Técnica", type="primary"):
                if not estudiante or not anecdota:
                    st.warning("Completa todos los campos.")
                else:
                    with st.spinner("Analizando desempeño..."):
                        prompt_eval = f"""
                        Evalúa a {estudiante}. Actividad: {actividad_final}. Obs: {anecdota}.
                        Genera: Análisis Técnico (Cualitativo), Nivel de Logro (Iniciado/En Proceso/Consolidado) y Recomendación.
                        """
                        st.session_state.eval_resultado = generar_respuesta([{"role": "system", "content": INSTRUCCIONES_TECNICAS}, {"role": "user", "content": prompt_eval}], 0.5)
                        st.session_state.estudiante_evaluado = estudiante
                        st.session_state.anecdota_guardada = anecdota
            
            if 'eval_resultado' in st.session_state:
                st.markdown("---")
                st.subheader("📋 Evaluación Generada")
                st.markdown(f'<div class="eval-box">{st.session_state.eval_resultado}</div>', unsafe_allow_html=True)
                
                if st.button("💾 GUARDAR REGISTRO", type="secondary"):
                    try:
                        df_evals = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                        nueva_eval = pd.DataFrame([{
                            "FECHA": fecha_hoy_str, "USUARIO": st.session_state.u['NOMBRE'],
                            "ESTUDIANTE": st.session_state.estudiante_evaluado, "ACTIVIDAD": actividad_final,
                            "ANECDOTA": st.session_state.anecdota_guardada, "EVALUACION_IA": st.session_state.eval_resultado,
                            "PLANIFICACION_ACTIVA": plan_activa['RANGO'], "RESULTADO": "Registrado"
                        }])
                        conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_evals, nueva_eval], ignore_index=True))
                        st.success("✅ Guardado.")
                        del st.session_state.eval_resultado
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

    # -----------------------------------------------------------------------------------
    # HERRAMIENTA 4: REGISTRO DE EVALUACIONES
    # -----------------------------------------------------------------------------------
    elif opcion == "📊 Registro de Evaluaciones (NUEVO)":
        st.subheader("🎓 Expediente Estudiantil 360°")
        
        try:
            df_e = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
            mis_evals = df_e[df_e['USUARIO'] == st.session_state.u['NOMBRE']]
            
            if mis_evals.empty:
                st.info("📭 Aún no has registrado evaluaciones.")
            else:
                lista_alumnos = sorted(mis_evals['ESTUDIANTE'].unique().tolist())
                col_sel, _ = st.columns([2,1])
                with col_sel:
                    alumno_sel = st.selectbox("📂 Seleccionar Estudiante:", lista_alumnos)
                
                datos_alumno = mis_evals[mis_evals['ESTUDIANTE'] == alumno_sel]
                
                # --- MÉTRICAS DE ASISTENCIA ---
                total_dias = len(mis_evals['FECHA'].unique())
                dias_asistidos = len(datos_alumno['FECHA'].unique())
                pct = (dias_asistidos / total_dias) * 100 if total_dias > 0 else 0
                
                st.markdown("---")
                cm1, cm2, cm3 = st.columns(3)
                cm1.metric("Asistencia (Días)", f"{dias_asistidos} / {total_dias}")
                cm2.metric("Porcentaje", f"{pct:.1f}%")
                
                if pct < 60: cm3.error("🚨 ALERTA")
                elif pct < 75: cm3.warning("⚠️ MEDIA")
                else: cm3.success("✅ REGULAR")
                
                st.markdown("---")
                
                # --- HISTORIAL E INFORME ---
                tab_hist, tab_ia = st.tabs(["📜 Historial", "🤖 Generar Informe"])
                
                with tab_hist:
                    for idx, row in datos_alumno.iloc[::-1].iterrows():
                        with st.expander(f"📅 {row['FECHA']} | {row['ACTIVIDAD']}"):
                            st.write(row['EVALUACION_IA'])
                
                with tab_ia:
                    if st.button(f"⚡ Generar Informe para {alumno_sel}"):
                        with st.spinner("Generando..."):
                            historial = datos_alumno[['FECHA', 'ACTIVIDAD', 'EVALUACION_IA']].to_string()
                            informe = generar_respuesta([{"role": "user", "content": f"Genera informe de progreso para {alumno_sel} basado en: {historial}"}])
                            st.markdown(f'<div class="plan-box">{informe}</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error BD: {e}")

    # -----------------------------------------------------------------------------------
    # HERRAMIENTA 5: MI ARCHIVO PEDAGÓGICO
    # -----------------------------------------------------------------------------------
    elif opcion == "📂 Mi Archivo Pedagógico":
        st.subheader(f"📂 Expediente de: {st.session_state.u['NOMBRE']}")
        
        plan_activa_actual = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
        
        col_info, col_accion = st.columns([3, 1])
        with col_info:
            if plan_activa_actual:
                st.success(f"**📌 PLANIFICACIÓN ACTIVA:** {plan_activa_actual['RANGO']}")
            else:
                st.warning("⚠️ **Sin planificación activa.**")
        
        with col_accion:
            if plan_activa_actual:
                if st.button("❌ Desactivar"):
                    desactivar_plan_activa(st.session_state.u['NOMBRE'])
                    st.rerun()
        
        st.markdown("---")
        
        try:
            df = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
            mis_planes = df[df['USUARIO'] == st.session_state.u['NOMBRE']]
            
            if mis_planes.empty:
                st.warning("Carpeta vacía.")
            else:
                contenido_activo = plan_activa_actual['CONTENIDO_PLAN'] if plan_activa_actual else None
                
                for index, row in mis_planes.iloc[::-1].iterrows():
                    es_activa = (contenido_activo == row['CONTENIDO'])
                    etiqueta = f"{'⭐ ACTIVA | ' if es_activa else ''}📅 {row['FECHA']} | {str(row['TEMA'])[:40]}..."
                    
                    with st.expander(etiqueta, expanded=es_activa):
                        st.markdown(f'<div class="plan-box" style="padding:10px; font-size:0.9em;">{row["CONTENIDO"]}</div>', unsafe_allow_html=True)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if not es_activa:
                                if st.button("⭐ Usar", key=f"act_{index}"):
                                    establecer_plan_activa(st.session_state.u['NOMBRE'], str(index), row['CONTENIDO'], "Seleccionada", "Taller")
                                    st.rerun()
                        with col_b:
                            if st.button("🗑️ Eliminar", key=f"del_{index}"):
                                df_new = df.drop(index)
                                conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_new)
                                st.rerun()
        except Exception as e: st.error(f"Error: {e}")

    # -----------------------------------------------------------------------------------
    # EXTRAS: MENSAJE MOTIVACIONAL Y OTROS
    # -----------------------------------------------------------------------------------
    elif opcion == "🌟 Mensaje Motivacional":
        st.subheader("Dosis de Ánimo Express ⚡")
        if st.button("❤️ Recibir Dosis"):
            estilos_posibles = [
                {"rol": "El Colega Realista", "instruccion": "Dile algo crudo pero esperanzador sobre enseñar educación especial. Humor venezolano."},
                {"rol": "El Sabio Espiritual", "instruccion": "Cita bíblica de fortaleza y frase docente."},
                {"rol": "El Motivador Directo", "instruccion": "Orden cariñosa para no rendirse."}
            ]
            estilo = random.choice(estilos_posibles)
            with st.spinner(f"Conectando con {estilo['rol']}..."):
                res = generar_respuesta([{"role": "system", "content": f"ERES LEGADO MAESTRO. ROL: {estilo['rol']}. TAREA: {estilo['instruccion']}"}, {"role": "user", "content": "Dame el mensaje."}], 1.0)
                st.markdown(f'<div class="plan-box" style="border-left: 5px solid #ff4b4b;"><h3>❤️ {estilo["rol"]}</h3><div class="mensaje-texto">"{res}"</div></div>', unsafe_allow_html=True)

    elif opcion == "💡 Ideas de Actividades":
        tema = st.text_input("Tema a trabajar:")
        if st.button("✨ Sugerir Actividades"):
            res = generar_respuesta([
                {"role": "system", "content": INSTRUCCIONES_TECNICAS}, 
                {"role": "user", "content": f"3 actividades lúdicas y vivenciales para {tema} en Taller Laboral."}
            ], temperatura=0.7)
            st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

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
st.caption("Desarrollado por Luis Atencio | Versión: 3.2 (Edición Robusta & Variada)")
