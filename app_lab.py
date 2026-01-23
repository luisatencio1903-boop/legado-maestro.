# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# VERSIÓN: 2.4.4 (SESIÓN PERSISTENTE + CACHÉ OPTIMIZADO)
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
import random
import re

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

# --- SISTEMA DE CACHÉ PARA EVITAR RATE LIMITS ---
class CacheManager:
    def __init__(self):
        self.cache_data = {}
        self.cache_timestamps = {}
    
    def get(self, key, max_age_seconds=30):
        """Obtiene datos del caché si no han expirado"""
        if key in self.cache_data and key in self.cache_timestamps:
            age = time.time() - self.cache_timestamps[key]
            if age < max_age_seconds:
                return self.cache_data[key]
        return None
    
    def set(self, key, data):
        """Guarda datos en el caché"""
        self.cache_data[key] = data
        self.cache_timestamps[key] = time.time()
    
    def clear(self, key=None):
        """Limpia el caché"""
        if key:
            if key in self.cache_data:
                del self.cache_data[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
        else:
            self.cache_data.clear()
            self.cache_timestamps.clear()

# Instancia global del caché
cache = CacheManager()

# --- FUNCIONES DE LECTURA CON CACHÉ (PERO NO PARA LOGIN) ---
def leer_con_cache(worksheet, ttl_seconds=30, force_refresh=False, usar_cache=True):
    """Lee una hoja de Google Sheets con caché para evitar rate limits"""
    
    # CRÍTICO: Para USUARIOS durante el auto-login, NO usar caché
    if worksheet == "USUARIOS" and not usar_cache:
        try:
            return conn.read(spreadsheet=URL_HOJA, worksheet=worksheet, ttl=0)
        except:
            return pd.DataFrame()
    
    cache_key = f"sheet_{worksheet}"
    
    # Intentar obtener del caché primero (si no forzamos refresco)
    if usar_cache and not force_refresh:
        cached_data = cache.get(cache_key, max_age_seconds=ttl_seconds)
        if cached_data is not None:
            return cached_data
    
    try:
        # Leer de Google Sheets
        df = conn.read(spreadsheet=URL_HOJA, worksheet=worksheet, ttl=0)
        
        # Guardar en caché
        if usar_cache:
            cache.set(cache_key, df)
        return df
    except Exception as e:
        # Si hay error, intentar usar caché aunque esté expirado
        if cache_key in cache.cache_data and usar_cache:
            return cache.cache_data[cache_key]
        # Si no hay nada en caché, devolver DataFrame vacío
        return pd.DataFrame()

# --- FUNCIÓN DE ESCRITURA CON REINTENTOS ---
def escribir_con_reintento(worksheet, data, max_intentos=3):
    """Escribe datos en Google Sheets con reintentos en caso de error 429"""
    for intento in range(max_intentos):
        try:
            conn.update(spreadsheet=URL_HOJA, worksheet=worksheet, data=data)
            # Limpiar caché de esta hoja después de escribir
            cache.clear(f"sheet_{worksheet}")
            return True
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if intento < max_intentos - 1:
                    wait_time = (intento + 1) * 2  # Esperar 2, 4, 6 segundos
                    time.sleep(wait_time)
                    continue
                else:
                    st.error(f"❌ Error de límite de cuota después de {max_intentos} intentos")
                    return False
            else:
                st.error(f"❌ Error al escribir en {worksheet}: {str(e)[:100]}")
                return False
    return False

# --- SISTEMA DE PLANIFICACIÓN ACTIVA (OPTIMIZADO) ---
def obtener_plan_activa_usuario(usuario_nombre):
    """Obtiene la planificación activa actual del usuario desde la nube (con caché)"""
    try:
        # Leer la hoja con caché
        df_activa = leer_con_cache("PLAN_ACTIVA", ttl_seconds=60)
        
        if df_activa.empty:
            return None
        
        if 'ACTIVO' not in df_activa.columns:
            return None
        
        # Convertir ACTIVO a string y buscar 'True' o 'TRUE'
        df_activa['ACTIVO_STR'] = df_activa['ACTIVO'].astype(str).str.upper()
        
        # Filtrar
        plan_activa = df_activa[
            (df_activa['USUARIO'] == usuario_nombre) & 
            (df_activa['ACTIVO_STR'] == 'TRUE')
        ]
        
        if not plan_activa.empty:
            # Retornar la más reciente
            return plan_activa.sort_values('FECHA_ACTIVACION', ascending=False).iloc[0].to_dict()
        return None
    except Exception as e:
        return None

def establecer_plan_activa(usuario_nombre, id_plan, contenido, rango, aula):
    """Establece una planificación como la activa para el usuario (con reintentos)"""
    try:
        # Pequeña pausa para reducir rate limits
        time.sleep(0.5)
        
        # Leer datos actuales con caché forzando refresco
        df_activa = leer_con_cache("PLAN_ACTIVA", force_refresh=True)
        
        # Si el DataFrame está vacío o no tiene columnas, inicializarlo
        if df_activa.empty or 'USUARIO' not in df_activa.columns:
            columnas = ["USUARIO", "FECHA_ACTIVACION", "ID_PLAN", 
                       "CONTENIDO_PLAN", "RANGO", "AULA", "ACTIVO"]
            df_activa = pd.DataFrame(columns=columnas)
        
        # 1. Desactivar cualquier planificación activa previa del mismo usuario
        if not df_activa.empty:
            mask_usuario = df_activa['USUARIO'] == usuario_nombre
            if mask_usuario.any():
                df_activa.loc[mask_usuario, 'ACTIVO'] = False
        
        # 2. Agregar la nueva planificación activa
        nueva_activa = pd.DataFrame([{
            "USUARIO": usuario_nombre,
            "FECHA_ACTIVACION": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "ID_PLAN": str(id_plan),
            "CONTENIDO_PLAN": str(contenido)[:5000],  # Limitar tamaño
            "RANGO": str(rango),
            "AULA": str(aula),
            "ACTIVO": True
        }])
        
        # Combinar y actualizar
        df_actualizado = pd.concat([df_activa, nueva_activa], ignore_index=True)
        
        # Escribir con reintentos
        if escribir_con_reintento("PLAN_ACTIVA", df_actualizado):
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"Error al establecer plan activa: {str(e)[:200]}")
        return False

def desactivar_plan_activa(usuario_nombre):
    """Desactiva cualquier planificación activa del usuario"""
    try:
        df_activa = leer_con_cache("PLAN_ACTIVA", force_refresh=True)
        if not df_activa.empty:
            mask_usuario = df_activa['USUARIO'] == usuario_nombre
            if mask_usuario.any():
                df_activa.loc[mask_usuario, 'ACTIVO'] = False
                escribir_con_reintento("PLAN_ACTIVA", df_activa)
        return True
    except:
        return False

# =========================================================
# ¡¡¡CRÍTICO: AUTO-LOGIN DEBE ESTAR ANTES DE CUALQUIER CACHÉ!!!
# =========================================================

# --- LÓGICA DE PERSISTENCIA DE SESIÓN (AUTO-LOGIN) ---
query_params = st.query_params
usuario_en_url = query_params.get("u", None)

# AUTO-LOGIN: Si hay parámetro 'u' en la URL y no estamos autenticados
if not st.session_state.auth and usuario_en_url:
    try:
        # CRÍTICO: Para auto-login, LEER DIRECTAMENTE SIN CACHÉ
        df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
        df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
        match = df_u[df_u['C_L'] == usuario_en_url]
        
        if not match.empty:
            st.session_state.auth = True
            st.session_state.u = match.iloc[0].to_dict()
            st.success(f"✅ Sesión restaurada para {st.session_state.u['NOMBRE']}")
            time.sleep(1)
            st.rerun()
        else:
            st.query_params.clear()
    except Exception as e:
        # Si falla, intentar con caché como último recurso
        try:
            df_u = leer_con_cache("USUARIOS", ttl_seconds=0, force_refresh=True)
            if not df_u.empty:
                df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
                match = df_u[df_u['C_L'] == usuario_en_url]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.u = match.iloc[0].to_dict()
                    st.success(f"✅ Sesión restaurada desde caché")
                    time.sleep(1)
                    st.rerun()
        except:
            st.query_params.clear()

# --- FORMULARIO DE LOGIN (SOLO SI NO HAY AUTO-LOGIN) ---
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
                # Para login inicial, podemos usar caché
                df_u = leer_con_cache("USUARIOS", ttl_seconds=300, usar_cache=True)
                df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
                cedula_limpia = limpiar_id(c_in)
                match = df_u[(df_u['C_L'] == cedula_limpia) & (df_u['CLAVE'] == p_in)]
                
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.u = match.iloc[0].to_dict()
                    # ESTO ES CLAVE: Anclar sesión en URL
                    st.query_params["u"] = cedula_limpia
                    st.success("¡Bienvenido!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas.")
            except Exception as e:
                st.error(f"Error de conexión: {str(e)[:100]}")
    st.stop()

# --- 2. ESTILOS CSS (MODO OSCURO + FORMATO) ---
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
                font-family: sans-serif;
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

            /* CAJA DE MENSAJES */
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

            /* ESTILO PARA BOTÓN ACTIVO */
            .boton-activo {
                background-color: #ffd700 !important;
                color: #000000 !important;
                border: 2px solid #ffa500 !important;
            }
            
            /* INDICADOR DE ACTIVA */
            .indicador-activa {
                background-color: #d4edda !important;
                border-left: 5px solid #28a745 !important;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
            }
            
            /* MENSAJE DE CACHÉ */
            .cache-message {
                background-color: #fff3cd !important;
                border-left: 5px solid #ffc107 !important;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
                font-size: 0.9em;
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

# --- 4. BARRA LATERAL DINÁMICA ---
with st.sidebar:
    if os.path.exists("logo_legado.png"):
        st.image("logo_legado.png", width=150)
    else:
        st.header("🍎")
        
    st.title("Legado Maestro")
    st.markdown("---")
    
    # --- INFORMACIÓN DEL USUARIO AUTENTICADO ---
    if st.session_state.u:
        nombre_usuario = st.session_state.u.get('NOMBRE', 'Usuario')
        rol_usuario = st.session_state.u.get('ROL', 'DOCENTE')
        
        st.caption(f"👤 **{nombre_usuario}**")
        st.caption(f"🔧 {rol_usuario}")
        
        if nombre_usuario.upper() == "LUIS ATENCIO":
            st.caption("Bachiller Docente")
            st.caption("T.E.L E.R.A.C")
    else:
        st.caption("👤 **Usuario no identificado**")
        st.caption("🔧 Rol desconocido")
    
    # --- INDICADOR DE PLANIFICACIÓN ACTIVA ---
    st.markdown("---")
    plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    if plan_activa:
        st.success("📌 **Planificación Activa**")
        st.caption(f"**Rango:** {plan_activa.get('RANGO', 'No especificado')}")
        st.caption(f"**Aula:** {plan_activa.get('AULA', 'Taller Laboral')}")
        st.caption(f"Activada: {plan_activa.get('FECHA_ACTIVACION', 'Fecha no disponible').split()[0]}")
        
        with st.expander("Acciones", expanded=False):
            if st.button("Cambiar Planificación", key="sidebar_cambiar"):
                st.session_state.redirigir_a_archivo = True
                st.rerun()
            if st.button("Desactivar", key="sidebar_desactivar"):
                if desactivar_plan_activa(st.session_state.u['NOMBRE']):
                    st.success("Planificación desactivada")
                    time.sleep(1)
                    st.rerun()
    else:
        st.warning("⚠️ **Sin planificación activa**")
        st.caption("Ve a 'Mi Archivo' para activar una")
    
    st.markdown("---")
    
    # Botón para limpiar caché manualmente
    if st.button("🔄 Refrescar Datos", help="Forzar actualización de datos desde Google Sheets"):
        cache.clear()
        st.success("✅ Caché limpiado. Los datos se cargarán nuevamente.")
        time.sleep(1)
        st.rerun()
    
    if st.button("🗑️ Limpiar Memoria"):
        for key in list(st.session_state.keys()):
            if key not in ['auth', 'u', 'redirigir_a_archivo']:
                del st.session_state[key]
        st.rerun()
    
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.auth = False
        st.session_state.u = None
        st.query_params.clear() 
        st.rerun()

# --- 5. GESTIÓN DE MEMORIA ---
if 'plan_actual' not in st.session_state: st.session_state.plan_actual = ""
if 'actividad_detectada' not in st.session_state: st.session_state.actividad_detectada = ""
if 'redirigir_a_archivo' not in st.session_state: st.session_state.redirigir_a_archivo = False

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

# Redirección automática si se solicita desde sidebar
if st.session_state.get('redirigir_a_archivo', False):
    opcion = "📂 Mi Archivo Pedagógico"
    st.session_state.redirigir_a_archivo = False
else:
    opcion = st.selectbox(
        "Seleccione herramienta:",
        [
            "📝 Planificación Profesional", 
            "📝 Evaluar Alumno (NUEVO)",
            "📊 Registro de Evaluaciones (NUEVO)",
            "📂 Mi Archivo Pedagógico",
            "🌟 Mensaje Motivacional", 
            "💡 Ideas de Actividades", 
            "❓ Consultas Técnicas"
        ]
    )

# =========================================================
# 1. PLANIFICADOR (FLUJO: BORRADOR -> GUARDAR)
# =========================================================
if opcion == "📝 Planificación Profesional":
    st.subheader("Planificación Técnica (Taller Laboral)")
    
    col1, col2 = st.columns(2)
    with col1:
        rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de Enero")
    with col2:
        aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios Generales")
    
    notas = st.text_area("Notas del Docente / Tema:", height=150)

    # --- PASO 1: GENERAR BORRADOR ---
    if st.button("🚀 Generar Borrador con IA"):
        if rango and notas:
            with st.spinner('Analizando Currículo Nacional y redactando...'):
                
                st.session_state.temp_rango = rango
                st.session_state.temp_tema = notas
                
                # --- PROMPT MAESTRO ---
                prompt_inicial = f"""
                Actúa como Luis Atencio, experto en Educación Especial (Taller Laboral) en Venezuela.
                Planificación para: {rango}. Aula: {aula}. Tema: {notas}.

                ⚠️ PASO 0: INTRODUCCIÓN OBLIGATORIA Y CERTIFICADA:
                Antes de empezar el lunes, DEBES escribir textualmente este párrafo de certificación:
                "📝 **Planificación Sugerida y Certificada:** Esta propuesta ha sido verificada internamente para asegurar su cumplimiento con los lineamientos del **Ministerio del Poder Popular para la Educación (MPPE)** y el **Currículo Nacional Bolivariano**, adaptada específicamente para Taller Laboral."
                (Deja dos espacios vacíos después de esto).

                ⚠️ PASO 1: LÓGICA DE COMPETENCIAS:
                - LO CORRECTO: La Competencia debe ser una FRASE DE ACCIÓN ESPECÍFICA sobre el tema.
                - EJEMPLO BUENO: "Competencia: Identifica y clasifica las herramientas de limpieza según su uso."

                ⚠️ PASO 2: HUMANIZACIÓN (EL LEGADO DOCENTE):
                - PROHIBIDO el "copia y pega" robótico. No empieces todos los días igual.
                - ELIMINA la voz pasiva aburrida.
                - USA VOZ ACTIVA: "Arrancamos el día...", "Invitamos a...", "Desafiamos al grupo...".

                ⚠️ PASO 3: ESTRUCTURA DIARIA (Sigue este formato exacto):

                ### [DÍA]

                1. **TÍTULO:** [Creativo]
                2. **COMPETENCIA:** [Redacta la habilidad técnica específica]

                3. **EXPLORACIÓN:** [Párrafo humano. EJEMPLO: Iniciamos con un conversatorio sobre... invitando a los estudiantes a compartir experiencias. Mediante el diálogo interactivo, despertamos la curiosidad.]

                4. **DESARROLLO:** [Párrafo práctico. Enfocado en la práctica real.]

                5. **REFLEXIÓN:** [Párrafo de cierre. Enfocado en la convivencia.]

                6. **MANTENIMIENTO:** [Acción concreta]
                7. **ESTRATEGIAS:** [Técnicas]
                8. **RECURSOS:** [Materiales]

                ---
                (Repite para los 5 días).

                AL FINAL: 📚 FUNDAMENTACIÓN LEGAL: Cita el artículo específico de la LOE o la CRBV.
                """
                
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                    {"role": "user", "content": prompt_inicial}
                ]
                respuesta = generar_respuesta(mensajes, temperatura=0.4)
                st.session_state.plan_actual = respuesta
                st.rerun()

    # --- PASO 2: GUARDAR ---
    if st.session_state.plan_actual:
        st.markdown("---")
        st.info("👀 Revisa el borrador abajo. Si te gusta, guárdalo en tu carpeta.")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        col_save_1, col_save_2 = st.columns([2,1])
        with col_save_1:
            if st.button("💾 SÍ, GUARDAR EN MI CARPETA"):
                try:
                    with st.spinner("Archivando en el expediente..."):
                        df_act = leer_con_cache("Hoja1", ttl_seconds=30)
                        tema_guardar = st.session_state.get('temp_tema', notas)
                        nueva_fila = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "USUARIO": st.session_state.u['NOMBRE'], 
                            "TEMA": tema_guardar,
                            "CONTENIDO": st.session_state.plan_actual,
                            "ESTADO": "GUARDADO",
                            "HORA_INICIO": "--", "HORA_FIN": "--"
                        }])
                        datos_actualizados = pd.concat([df_act, nueva_fila], ignore_index=True)
                        
                        if escribir_con_reintento("Hoja1", datos_actualizados):
                            st.success("✅ ¡Planificación archivada con éxito!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar. Intenta nuevamente en unos segundos.")
                except Exception as e:
                    st.error(f"Error al guardar: {str(e)[:100]}")

# =========================================================
# 2. EVALUAR ALUMNO (USANDO PLANIFICACIÓN ACTIVA)
# =========================================================
elif opcion == "📝 Evaluar Alumno (NUEVO)":
    st.subheader("Evaluación Diaria Inteligente")
    
    # --- CÁLCULO DE FECHA SEGURA (HORA VENEZUELA) ---
    from datetime import timedelta
    fecha_segura_ve = datetime.utcnow() - timedelta(hours=4)
    fecha_hoy_str = fecha_segura_ve.strftime("%d/%m/%Y")
    dia_semana_hoy = fecha_segura_ve.strftime("%A")
    
    # --- VERIFICACIÓN CRÍTICA: ¿HAY PLANIFICACIÓN ACTIVA? ---
    plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    if not plan_activa:
        st.error("""
        🚨 **NO TIENES UNA PLANIFICACIÓN ACTIVA PARA ESTA SEMANA**
        
        **Para poder evaluar, necesitas:**
        
        1. Ir a **📂 Mi Archivo Pedagógico**
        2. Revisar tus planificaciones guardadas
        3. Seleccionar una y hacer clic en **"⭐ Usar Esta Semana"**
        
        Esto le indica al sistema **qué planificación usar para buscar actividades**.
        """)
        st.info("💡 **Consejo:** Activa la planificación que corresponde a **esta semana laboral**.")
        st.stop()
    
    # --- MOSTRAR PLANIFICACIÓN ACTIVA ---
    with st.container():
        st.success(f"**📌 EVALUANDO CONTRA:** {plan_activa.get('RANGO', 'Planificación activa')}")
        st.caption(f"Aula: {plan_activa.get('AULA', 'Taller Laboral')} | Activada: {plan_activa.get('FECHA_ACTIVACION', 'Fecha no disponible')}")
    
    st.markdown("---")
    
    # --- BOTÓN PARA BUSCAR ACTIVIDAD DE HOY ---
    col_btn, col_info = st.columns([1, 2])
    
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔍 Buscar Actividad de HOY", type="primary"):
            try:
                with st.spinner(f"Analizando planificación activa ({dia_semana_hoy})..."):
                    # USAR EXCLUSIVAMENTE LA PLANIFICACIÓN ACTIVA
                    contenido_planificacion = plan_activa.get('CONTENIDO_PLAN', '')
                    
                    # PROMPT MEJORADO PARA IDENTIFICAR ACTIVIDADES
                    prompt_busqueda = f"""
                    Eres un asistente pedagógico especializado en analizar planificaciones.
                    
                    **PLANIFICACIÓN OFICIAL DE LA SEMANA:**
                    {contenido_planificacion[:8000]}
                    
                    **INSTRUCCIÓN CRÍTICA:** 
                    Hoy es {fecha_hoy_str} ({dia_semana_hoy}). 
                    
                    **TU TAREA:** 
                    1. Revisa la planificación anterior
                    2. Identifica EXACTAMENTE qué actividad está programada para HOY
                    3. Si encuentras una actividad para hoy, responde SOLO con el NOMBRE/TÍTULO de esa actividad
                    4. Si NO hay actividad programada para hoy, responde: "NO_HAY_ACTIVIDAD_PARA_HOY"
                    
                    **EJEMPLO DE RESPUESTA CORRECTA:**
                    "Identificación de herramientas básicas de limpieza"
                    
                    **NO INCLUYAS:** Fechas, explicaciones, días de la semana, ni texto adicional.
                    """
                    
                    resultado = generar_respuesta([
                        {"role": "system", "content": "Eres un analista de planificaciones preciso y conciso."},
                        {"role": "user", "content": prompt_busqueda}
                    ], temperatura=0.1)
                    
                    resultado_limpio = resultado.strip().replace('"', '').replace("'", "")
                    
                    # VERIFICAR RESULTADO
                    if "NO_HAY_ACTIVIDAD" in resultado_limpio.upper() or len(resultado_limpio) < 5:
                        st.session_state.actividad_detectada = "NO HAY ACTIVIDAD PROGRAMADA PARA HOY"
                        st.error("❌ No hay actividades programadas para hoy en tu planificación activa.")
                    else:
                        st.session_state.actividad_detectada = resultado_limpio
                        st.success(f"✅ **Actividad encontrada:** {resultado_limpio}")
                        
            except Exception as e:
                st.error(f"Error en la búsqueda: {e}")
    
    with col_info:
        st.info("""
        **🔒 Sistema Blindado:**
        - Solo busca en tu **planificación activa actual**
        - No revisa otras planificaciones guardadas
        - Fecha bloqueada por el servidor
        """)
    
    # --- FORMULARIO DE EVALUACIÓN ---
    st.markdown("---")
    st.subheader("Registro de Evaluación")
    
    # Campo de actividad (bloqueado - viene de la planificación activa)
    actividad_final = st.text_input(
        "**Actividad Programada (Extraída de tu Planificación Activa):**",
        value=st.session_state.get('actividad_detectada', ''),
        disabled=True,
        help="Esta actividad viene de tu planificación oficial de la semana"
    )
    
    # Resto del formulario
    estudiante = st.text_input("**Nombre del Estudiante:**", placeholder="Ej: Juan Pérez")
    anecdota = st.text_area("**Observación del Desempeño:**", 
                           height=100, 
                           placeholder="Describe específicamente qué hizo el estudiante hoy...")
    
    # --- GENERAR EVALUACIÓN ---
    if st.button("⚡ Generar Evaluación Técnica", type="primary"):
        if not estudiante or not anecdota:
            st.warning("⚠️ Completa todos los campos antes de generar.")
        elif "NO HAY ACTIVIDAD" in actividad_final:
            st.error("❌ No puedes evaluar sin una actividad programada para hoy.")
        else:
            with st.spinner("Analizando desempeño pedagógico..."):
                prompt_eval = f"""
                ACTÚA COMO EXPERTO EN EVALUACIÓN DE EDUCACIÓN ESPECIAL (VENEZUELA).
                
                DATOS DE EVALUACIÓN:
                - Fecha: {fecha_hoy_str}
                - Estudiante: {estudiante}
                - Actividad Programada: {actividad_final}
                - Observación del Docente: "{anecdota}"
                
                GENERA UNA EVALUACIÓN TÉCNICA que incluya:
                1. **Análisis del Desempeño:** Basado en la observación
                2. **Nivel de Logro:** (Consolidado / En Proceso / Iniciado)
                3. **Recomendación Pedagógica:** Breve sugerencia para seguir trabajando
                
                FORMATO ESTRICTO (Markdown):
                **Evaluación Técnica:**
                [Tu análisis aquí]
                
                **Nivel de Logro:** [Consolidado/En Proceso/Iniciado]
                
                **Recomendación:** [Tu recomendación aquí]
                """
                
                evaluacion_generada = generar_respuesta([
                    {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                    {"role": "user", "content": prompt_eval}
                ], temperatura=0.5)
                
                st.session_state.eval_resultado = evaluacion_generada
                st.session_state.estudiante_evaluado = estudiante
                st.session_state.anecdota_guardada = anecdota
    
    # --- MOSTRAR Y GUARDAR RESULTADO ---
    if 'eval_resultado' in st.session_state:
        st.markdown("---")
        st.subheader("📋 Evaluación Generada")
        st.markdown(f'<div class="eval-box">{st.session_state.eval_resultado}</div>', unsafe_allow_html=True)
        
        # BOTÓN PARA GUARDAR
        if st.button("💾 GUARDAR EN REGISTRO OFICIAL", type="secondary"):
            try:
                # Leer evaluaciones existentes
                df_evals = leer_con_cache("EVALUACIONES", ttl_seconds=30)
                
                nueva_eval = pd.DataFrame([{
                    "FECHA": fecha_hoy_str,
                    "USUARIO": st.session_state.u['NOMBRE'],
                    "ESTUDIANTE": st.session_state.estudiante_evaluado,
                    "ACTIVIDAD": actividad_final,
                    "ANECDOTA": st.session_state.anecdota_guardada,
                    "EVALUACION_IA": st.session_state.eval_resultado,
                    "PLANIFICACION_ACTIVA": plan_activa.get('RANGO', ''),
                    "RESULTADO": "Registrado"
                }])
                
                # Guardar
                df_actualizado = pd.concat([df_evals, nueva_eval], ignore_index=True)
                
                if escribir_con_reintento("EVALUACIONES", df_actualizado):
                    st.success(f"✅ Evaluación de {st.session_state.estudiante_evaluado} guardada correctamente.")
                    
                    # Limpiar estado
                    del st.session_state.eval_resultado
                    del st.session_state.estudiante_evaluado
                    del st.session_state.anecdota_guardada
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar. Intenta nuevamente en unos segundos.")
                
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# =========================================================
# 3. REGISTRO DE EVALUACIONES
# =========================================================
elif opcion == "📊 Registro de Evaluaciones (NUEVO)":
    st.subheader("🎓 Expediente Estudiantil 360°")
    
    try:
        # 1. Cargamos TODA la base de datos de evaluaciones (con caché)
        df_e = leer_con_cache("EVALUACIONES", ttl_seconds=60)
        
        # Filtramos solo las de este docente (para privacidad)
        mis_evals = df_e[df_e['USUARIO'] == st.session_state.u['NOMBRE']]
        
        if mis_evals.empty:
            st.info("📭 Aún no has registrado evaluaciones. Ve a la opción 'Evaluar Alumno' para empezar.")
        else:
            # 2. SELECTOR DE ALUMNO (El centro de todo)
            lista_alumnos = sorted(mis_evals['ESTUDIANTE'].unique().tolist())
            col_sel, col_vacio = st.columns([2,1])
            with col_sel:
                alumno_sel = st.selectbox("📂 Seleccionar Expediente del Estudiante:", lista_alumnos)
            
            st.markdown("---")
            
            # 3. CÁLCULO DE ASISTENCIA INTELIGENTE
            total_dias_clase = len(mis_evals['FECHA'].unique())
            datos_alumno = mis_evals[mis_evals['ESTUDIANTE'] == alumno_sel]
            dias_asistidos = len(datos_alumno['FECHA'].unique())
            
            try:
                porcentaje_asistencia = (dias_asistidos / total_dias_clase) * 100
            except:
                porcentaje_asistencia = 0
            
            # 4. TABLERO DE MÉTRICAS (ASISTENCIA)
            st.markdown(f"### 📊 Reporte de Asistencia: {alumno_sel}")
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Días Asistidos", f"{dias_asistidos} / {total_dias_clase}")
            col_m1.caption("Basado en evaluaciones realizadas")
            
            col_m2.metric("Porcentaje de Asistencia", f"{porcentaje_asistencia:.1f}%")
            
            # Lógica de Semáforo para el Estado
            if porcentaje_asistencia >= 75:
                col_m3.success("✅ ASISTENCIA REGULAR")
            elif 50 <= porcentaje_asistencia < 75:
                col_m3.warning("⚠️ ASISTENCIA MEDIA")
            else:
                col_m3.error("🚨 CRÍTICO")
            
            # 5. ALERTA DE REPRESENTANTE
            if porcentaje_asistencia < 60:
                st.error(f"""
                🚨 **ALERTA DE DESERCIÓN ESCOLAR DETECTADA**
                El estudiante {alumno_sel} tiene una asistencia del {porcentaje_asistencia:.1f}%, lo cual es crítico.
                
                👉 **ACCIÓN RECOMENDADA:** CITAR AL REPRESENTANTE DE INMEDIATO.
                """)
            
            st.markdown("---")
            
            # 6. HISTORIAL DE EVALUACIONES (Tus fichas desplegables)
            st.markdown(f"### 📑 Historial de Evaluaciones de {alumno_sel}")
            
            # Pestañas para organizar la vista
            tab_hist, tab_ia = st.tabs(["📜 Bitácora de Actividades", "🤖 Generar Informe IA"])
            
            with tab_hist:
                if datos_alumno.empty:
                    st.write("No hay registros.")
                else:
                    # Iteramos solo sobre los datos de este alumno
                    for idx, row in datos_alumno.iloc[::-1].iterrows():
                        fecha = row['FECHA']
                        actividad = row['ACTIVIDAD']
                        
                        with st.expander(f"📅 {fecha} | {actividad}"):
                            st.markdown(f"**📝 Observación Docente:**")
                            st.info(f"_{row['ANECDOTA']}_")
                            
                            st.markdown(f"**🤖 Análisis Técnico (Legado Maestro):**")
                            st.markdown(f'<div class="eval-box">{row["EVALUACION_IA"]}</div>', unsafe_allow_html=True)
            
            with tab_ia:
                st.info("La IA analizará todo el historial de arriba para crear un informe de lapso.")
                
                # CLAVE ÚNICA PARA GUARDAR EL INFORME DE ESTE ALUMNO ESPECÍFICO
                key_informe = f"informe_guardado_{alumno_sel}"
                
                # Botón para generar (o regenerar)
                if st.button(f"⚡ Generar Informe de Progreso para {alumno_sel}"):
                    with st.spinner("Leyendo todas las evaluaciones del estudiante..."):
                        # Recopilamos todo el texto de las IAs previas
                        historial_texto = datos_alumno[['FECHA', 'ACTIVIDAD', 'EVALUACION_IA']].to_string()
                        
                        prompt_informe = f"""
                        ACTÚA COMO UN SUPERVISOR DE EDUCACIÓN ESPECIAL EXPERTO.
                        
                        Genera un INFORME CUALITATIVO DE PROGRESO para el estudiante: {alumno_sel}.
                        
                        DATOS DE ASISTENCIA: {porcentaje_asistencia:.1f}% ({dias_asistidos} de {total_dias_clase} días).
                        
                        HISTORIAL DE EVALUACIONES DIARIAS:
                        {historial_texto}
                        
                        ESTRUCTURA DEL INFORME:
                        1. **Resumen de Asistencia:** (Menciona si es preocupante o buena).
                        2. **Evolución de Competencias:** (¿Ha mejorado desde la primera fecha hasta la última?).
                        3. **Fortalezas Consolidadas:**
                        4. **Debilidades / Áreas de Atención:**
                        5. **Recomendación Final:**
                        """
                        
                        # Guardamos el resultado en la memoria de sesión
                        st.session_state[key_informe] = generar_respuesta([
                            {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                            {"role": "user", "content": prompt_informe}
                        ], temperatura=0.6)
                
                # MOSTRAR EL INFORME SI EXISTE EN MEMORIA (Así no se borra al recargar)
                if key_informe in st.session_state:
                    st.markdown(f'<div class="plan-box"><h3>📄 Informe de Progreso: {alumno_sel}</h3>{st.session_state[key_informe]}</div>', unsafe_allow_html=True)
                    
                    # Botón opcional para limpiar
                    if st.button("Limpiar Informe", key=f"clean_{alumno_sel}"):
                        del st.session_state[key_informe]
                        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Error conectando con la base de datos. Detalle: {e}")

# =========================================================
# 4. MI ARCHIVO PEDAGÓGICO (CON SISTEMA DE PLANIFICACIÓN ACTIVA)
# =========================================================
elif opcion == "📂 Mi Archivo Pedagógico":
    st.subheader(f"📂 Expediente de: {st.session_state.u['NOMBRE']}")
    
    # OBTENER PLANIFICACIÓN ACTIVA ACTUAL
    plan_activa_actual = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    # PANEL INFORMATIVO SUPERIOR
    col_info, col_accion = st.columns([3, 1])
    with col_info:
        if plan_activa_actual:
            st.success(f"**📌 PLANIFICACIÓN ACTIVA ACTUAL:** {plan_activa_actual.get('RANGO', 'No especificado')}")
            st.caption(f"Aula: {plan_activa_actual.get('AULA', 'Taller Laboral')} | Activada: {plan_activa_actual.get('FECHA_ACTIVACION', 'Fecha no disponible').split()[0]}")
        else:
            st.warning("⚠️ **No tienes una planificación activa para esta semana.**")
            st.caption("Selecciona una planificación y haz clic en '⭐ Usar Esta Semana'")
    
    with col_accion:
        if plan_activa_actual:
            if st.button("❌ Desactivar", help="Dejar de usar esta planificación para evaluar"):
                if desactivar_plan_activa(st.session_state.u['NOMBRE']):
                    st.success("Planificación desactivada.")
                    time.sleep(1)
                    st.rerun()
    
    st.markdown("---")
    st.info("Selecciona una planificación para **trabajar esta semana**. El sistema de evaluación usará **solo esta**.")
    
    try:
        df = leer_con_cache("Hoja1", ttl_seconds=60)
        mis_planes = df[df['USUARIO'] == st.session_state.u['NOMBRE']]
        
        if mis_planes.empty:
            st.warning("Aún no tienes planificaciones guardadas.")
        else:
            # IDENTIFICAR CUÁL ES LA ACTIVA ACTUAL (por contenido)
            contenido_activo_actual = plan_activa_actual.get('CONTENIDO_PLAN', '') if plan_activa_actual else ''
            
            for index, row in mis_planes.iloc[::-1].iterrows():
                # DETERMINAR SI ESTA ES LA ACTIVA
                es_activa = (str(contenido_activo_actual).strip() == str(row['CONTENIDO']).strip())
                
                # CREAR ETIQUETA CON INDICADOR
                etiqueta_base = f"📅 {row['FECHA']} | 📌 {str(row['TEMA'])[:40]}..."
                if es_activa:
                    etiqueta = f"⭐ **ACTIVA** | {etiqueta_base}"
                else:
                    etiqueta = etiqueta_base
                
                # EXPANDER PARA CADA PLANIFICACIÓN
                with st.expander(etiqueta, expanded=es_activa):
                    # ENCABEZADO SI ES ACTIVA
                    if es_activa:
                        st.success("✅ **ESTA ES TU PLANIFICACIÓN ACTIVA PARA LA SEMANA**")
                        st.markdown("El sistema de evaluación buscará actividades **solo en esta planificación**.")
                    
                    # CONTENIDO (solo lectura para mantener integridad)
                    st.markdown(f"**Contenido de la planificación:**")
                    st.markdown(f'<div class="plan-box" style="padding:10px; font-size:0.9em;">{row["CONTENIDO"]}</div>', unsafe_allow_html=True)
                    
                    # BOTONES DE ACCIÓN
                    col_acciones = st.columns([2, 1, 1])
                    
                    with col_acciones[0]:
                        # CONSULTOR INTELIGENTE
                        with st.expander("🤖 Consultar sobre este plan", expanded=False):
                            pregunta = st.text_input("Tu duda:", key=f"preg_{index}", placeholder="Ej: ¿Cómo evalúo esto?")
                            if st.button("Consultar", key=f"btn_{index}"):
                                if pregunta:
                                    with st.spinner("Analizando..."):
                                        prompt_contextual = f"""
                                        ACTÚA COMO ASESOR PEDAGÓGICO. CONTEXTO: {row['CONTENIDO']}. PREGUNTA: "{pregunta}".
                                        Responde directo y útil.
                                        """
                                        respuesta = generar_respuesta([
                                            {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                                            {"role": "user", "content": prompt_contextual}
                                        ], temperatura=0.5)
                                        st.markdown(f'<div class="consultor-box">💡 **Respuesta:**<br>{respuesta}</div>', unsafe_allow_html=True)
                    
                    with col_acciones[1]:
                        # BOTÓN PARA ACTIVAR ESTA PLANIFICACIÓN
                        if not es_activa:
                            st.write("")  # Espacio
                            if st.button("⭐ Usar Esta Semana", key=f"activar_{index}", 
                                       help="Establece esta planificación como la oficial para evaluar esta semana",
                                       type="secondary"):
                                
                                # Extraer información básica (intento automático)
                                contenido = row['CONTENIDO']
                                rango = "Semana Actual"
                                aula = "Taller Laboral"
                                
                                # Intentar extraer rango del contenido
                                patron_rango = r'Planificación para:\s*(.*?)(?:\n|$)'
                                match_rango = re.search(patron_rango, str(contenido), re.IGNORECASE)
                                if match_rango:
                                    rango = match_rango.group(1)
                                
                                # Establecer como activa
                                if establecer_plan_activa(
                                    usuario_nombre=st.session_state.u['NOMBRE'],
                                    id_plan=str(index),
                                    contenido=contenido,
                                    rango=rango,
                                    aula=aula
                                ):
                                    st.success("✅ ¡Planificación establecida como ACTIVA!")
                                    st.balloons()
                                    time.sleep(2)
                                    st.rerun()
                    
                    with col_acciones[2]:
                        # BOTÓN DE ELIMINAR
                        esta_borrando = st.session_state.get(f"confirm_del_{index}", False)
                        
                        if not esta_borrando:
                            st.write("")  # Espacio
                            if st.button("🗑️", key=f"del_init_{index}", help="Eliminar esta planificación"):
                                st.session_state[f"confirm_del_{index}"] = True
                                st.rerun()
                        else:
                            st.error("⚠️ ¿Eliminar esta planificación?")
                            if st.button("✅ Sí, eliminar", key=f"confirm_{index}"):
                                # Si es la activa, desactivarla primero
                                if es_activa:
                                    desactivar_plan_activa(st.session_state.u['NOMBRE'])
                                
                                # Eliminar de la hoja principal
                                df_actualizado = df.drop(index)
                                
                                if escribir_con_reintento("Hoja1", df_actualizado):
                                    st.success("🗑️ Planificación eliminada.")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Error al eliminar. Intenta nuevamente.")
                            
                            if st.button("❌ No, conservar", key=f"cancel_{index}"):
                                st.session_state[f"confirm_del_{index}"] = False
                                st.rerun()

    except Exception as e:
        st.error(f"Error cargando archivo: {e}")

# =========================================================
# OTROS MÓDULOS (EXTRAS)
# =========================================================
elif opcion == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    if st.button("❤️ Recibir Dosis"):
        estilos_posibles = [
            {"rol": "El Colega Realista", "instruccion": "Dile algo crudo pero esperanzador sobre enseñar. Humor venezolano. NO SALUDES."},
            {"rol": "El Sabio Espiritual", "instruccion": "Cita bíblica de fortaleza y frase docente. NO SALUDES."},
            {"rol": "El Motivador Directo", "instruccion": "Orden cariñosa para no rendirse. Ej: '¡Límpiate las rodillas!'. NO SALUDES."},
            {"rol": "El Observador", "instruccion": "Pregunta sobre su mejor alumno o momento feliz. NO SALUDES."}
        ]
        estilo = random.choice(estilos_posibles)
        prompt = "Dame el mensaje."
        with st.spinner(f"Modo {estilo['rol']}..."):
            res = generar_respuesta([{"role": "system", "content": f"ERES LEGADO MAESTRO. ROL: {estilo['rol']}. TAREA: {estilo['instruccion']}"}, {"role": "user", "content": prompt}], 1.0)
            st.markdown(f'<div class="plan-box" style="border-left: 5px solid #ff4b4b;"><h3>❤️ {estilo["rol"]}</h3><div class="mensaje-texto">"{res}"</div></div>', unsafe_allow_html=True)

elif opcion == "💡 Ideas de Actividades":
    tema = st.text_input("Tema a trabajar:")
    if st.button("✨ Sugerir"):
        res = generar_respuesta([
            {"role": "system", "content": INSTRUCCIONES_TECNICAS}, 
            {"role": "user", "content": f"3 actividades DUA para {tema} en Taller Laboral."}
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
st.caption("Desarrollado por Luis Atencio | Versión: 2.4.4 (Sesión Persistente + Caché) | ✅ Sesión se mantiene al recargar")
