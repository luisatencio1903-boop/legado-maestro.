# =============================================================================
# PROYECTO: LEGADO MAESTRO
# VERSIÓN: 4.1 (GOLD MASTER - ERROR FIXED)
# FECHA: Enero 2026
# AUTOR: Luis Atencio (Bachiller Docente)
# INSTITUCIÓN: T.E.L E.R.A.C
#
# DESCRIPCIÓN:
# Plataforma integral para docentes de Educación Especial.
# Integra Inteligencia Artificial, Base de Datos y Gestión Administrativa.
# =============================================================================

import streamlit as st
import os
import time
from datetime import datetime, timedelta
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import re  # Librería para expresiones regulares

# =============================================================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# 2. ESTILOS CSS (INTERFAZ VISUAL PROFESIONAL)
# =============================================================================

hide_streamlit_style = """
<style>
    /* Ocultar elementos del sistema Streamlit para dar aspecto de App nativa */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ----------------------------------------------------------- */
    /* ESTILOS DE CAJAS DE CONTENIDO (PLANIFICACIONES)             */
    /* ----------------------------------------------------------- */
    .plan-box {
        background-color: #f8f9fa !important;
        color: #212529 !important; 
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #0068c9;
        margin-bottom: 25px;
        font-family: 'Helvetica', sans-serif;
        font-size: 1.05rem;
        line-height: 1.6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .plan-box h3 {
        color: #0068c9 !important;
        margin-top: 25px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e9ecef;
        font-weight: 700;
    }
    
    .plan-box strong {
        color: #2c3e50 !important;
        font-weight: 700;
    }

    /* ----------------------------------------------------------- */
    /* ESTILOS DE CAJAS DE EVALUACIÓN (RESPUESTAS IA)              */
    /* ----------------------------------------------------------- */
    .eval-box {
        background-color: #e8f5e9 !important;
        color: #1b5e20 !important;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #2e7d32;
        margin-top: 15px;
        margin-bottom: 15px;
        font-family: 'Arial', sans-serif;
    }
    
    .eval-box h4 { 
        color: #2e7d32 !important; 
        font-weight: bold;
    }

    /* ----------------------------------------------------------- */
    /* ESTILOS PARA ELEMENTOS DE FORMULARIO (MÓVIL)                */
    /* ----------------------------------------------------------- */
    
    /* Texto de selectores más grande para dedos */
    .stSelectbox label {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #0d47a1 !important;
        margin-bottom: 8px;
    }
    
    /* Botones más altos y fáciles de tocar */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        height: 3.2em;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Separadores visuales */
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 0;
        border-top: 1px solid #dee2e6;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =============================================================================
# 3. FUNCIONES UTILITARIAS Y DE CONEXIÓN
# =============================================================================

def limpiar_id(v): 
    """
    Normaliza el formato de la cédula de identidad para evitar errores en BD.
    Elimina caracteres no numéricos y espacios.
    """
    if v is None:
        return ""
    valor_str = str(v).strip().upper()
    # Eliminar decimales si viene de Excel numérico
    valor_limpio = valor_str.split('.')[0]
    # Eliminar puntuación y letras comunes
    valor_limpio = valor_limpio.replace(',', '').replace('.', '')
    valor_limpio = valor_limpio.replace('V-', '').replace('E-', '')
    valor_limpio = valor_limpio.replace('V', '').replace('E', '')
    return valor_limpio

# --- CONEXIÓN A BASE DE DATOS (GOOGLE SHEETS) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    if "GSHEETS_URL" not in st.secrets:
        st.error("⚠️ Error Crítico: No se encontró 'GSHEETS_URL' en los secrets.")
        st.stop()
        
    URL_HOJA = st.secrets["GSHEETS_URL"]
    
except Exception as e:
    st.error("⚠️ No se pudo conectar con la Base de Datos.")
    st.error(f"Detalle técnico: {e}")
    st.stop()

# --- CONEXIÓN A INTELIGENCIA ARTIFICIAL (GROQ) ---
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        MODELO_USADO = "llama-3.3-70b-versatile" 
    else:
        st.error("⚠️ Error de Configuración: Falta la API Key de Groq.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error al inicializar el cerebro de IA: {e}")
    st.stop()

# =============================================================================
# 4. GESTIÓN DE VARIABLES DE ESTADO (MEMORIA DE SESIÓN)
# =============================================================================

# Autenticación
if 'auth' not in st.session_state:
    st.session_state.auth = False

if 'u' not in st.session_state:
    st.session_state.u = None

# Navegación
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = "HOME"

# Memoria de Trabajo (Persistencia temporal)
if 'plan_actual' not in st.session_state: 
    st.session_state.plan_actual = ""

if 'actividad_detectada' not in st.session_state: 
    st.session_state.actividad_detectada = ""

if 'eval_resultado' not in st.session_state:
    st.session_state.eval_resultado = ""

if 'redirigir_a_archivo' not in st.session_state: 
    st.session_state.redirigir_a_archivo = False

# =============================================================================
# 5. LÓGICA DE NEGOCIO (BACKEND)
# =============================================================================

# --- 5.1 GESTIÓN DE PLANIFICACIÓN ACTIVA ---

def obtener_plan_activa_usuario(usuario_nombre):
    """
    Consulta la BD para obtener la planificación marcada como activa.
    """
    try:
        df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=5)
        
        plan_activa = df_activa[
            (df_activa['USUARIO'] == usuario_nombre) & 
            (df_activa['ACTIVO'] == True)
        ]
        
        if not plan_activa.empty:
            return plan_activa.sort_values('FECHA_ACTIVACION', ascending=False).iloc[0].to_dict()
        return None
    except Exception:
        return None

def establecer_plan_activa(usuario_nombre, id_plan, contenido, rango, aula):
    """
    Marca una planificación como activa y desactiva las anteriores.
    """
    try:
        try:
            df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=0)
        except:
            # Crear DataFrame si la hoja está vacía o no existe
            df_activa = pd.DataFrame(columns=[
                "USUARIO", "FECHA_ACTIVACION", "ID_PLAN", 
                "CONTENIDO_PLAN", "RANGO", "AULA", "ACTIVO"
            ])
        
        # 1. Desactivar planes previos
        mask_usuario = df_activa['USUARIO'] == usuario_nombre
        if not df_activa[mask_usuario].empty:
            df_activa.loc[mask_usuario, 'ACTIVO'] = False
        
        # 2. Insertar nuevo plan activo
        nueva_activa = pd.DataFrame([{
            "USUARIO": usuario_nombre,
            "FECHA_ACTIVACION": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "ID_PLAN": id_plan,
            "CONTENIDO_PLAN": contenido,
            "RANGO": rango,
            "AULA": aula,
            "ACTIVO": True
        }])
        
        # Guardar en BD
        df_final = pd.concat([df_activa, nueva_activa], ignore_index=True)
        conn.update(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al activar planificación: {e}")
        return False

def desactivar_plan_activa(usuario_nombre):
    """Desactiva el plan actual sin borrarlo."""
    try:
        df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=0)
        mask = df_activa['USUARIO'] == usuario_nombre
        
        if not df_activa[mask].empty:
            df_activa.loc[mask, 'ACTIVO'] = False
            conn.update(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", data=df_activa)
        return True
    except:
        return False

# --- 5.2 GESTIÓN DE ASISTENCIA (INTEGRACIÓN CON DIRECCIÓN) ---

def registrar_asistencia(usuario, tipo, hora, motivo, recomendacion_ia):
    """
    Escribe en la hoja 'ASISTENCIA' para validación del Director.
    Retorna estados: 'OK', 'DUPLICADO', 'ERROR'.
    """
    try:
        try:
            df_asistencia = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=0)
        except:
            # Crear estructura si no existe
            df_asistencia = pd.DataFrame(columns=[
                "FECHA", "USUARIO", "TIPO", "HORA_LLEGADA", 
                "MOTIVO", "ALERTA_IA", "ESTADO_DIRECTOR"
            ])
        
        hoy_str = datetime.now().strftime("%d/%m/%Y")
        
        # Verificar si ya existe registro hoy
        duplicado = df_asistencia[
            (df_asistencia['USUARIO'] == usuario) & 
            (df_asistencia['FECHA'] == hoy_str)
        ]
        
        if not duplicado.empty:
            return "DUPLICADO"

        # Crear registro
        nuevo_registro = pd.DataFrame([{
            "FECHA": hoy_str,
            "USUARIO": usuario,
            "TIPO": tipo,          # ASISTENCIA / INASISTENCIA
            "HORA_LLEGADA": hora,
            "MOTIVO": motivo,
            "ALERTA_IA": recomendacion_ia,
            "ESTADO_DIRECTOR": "PENDIENTE" # Estado inicial
        }])
        
        # Guardar
        df_final = pd.concat([df_asistencia, nuevo_registro], ignore_index=True)
        conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_final)
        return "OK"
        
    except Exception as e:
        return f"ERROR: {e}"

# --- 5.3 MOTOR DE INTELIGENCIA ARTIFICIAL ---

# Prompt Maestro: Define la personalidad y reglas pedagógicas
INSTRUCCIONES_TECNICAS = """
⚠️ ERES "LEGADO MAESTRO".
TU IDENTIDAD: Sistema de Inteligencia Artificial Educativa Venezolana.
TU CREADOR: Bachiller Docente Luis Atencio.
TU ROL: Experto en Educación Especial y Taller Laboral (Población con Discapacidad Intelectual, Autismo, Down).

🚨 REGLAS PEDAGÓGICAS INQUEBRANTABLES:

1. **COMPETENCIAS TÉCNICAS (ESTRUCTURA OBLIGATORIA):**
   - NUNCA uses un verbo solitario (Ej: "Diseñar" -> MAL).
   - Estructura Correcta: VERBO DE ACCIÓN + OBJETO DE CONOCIMIENTO + CONDICIÓN/CONTEXTO.
   - Ejemplo: "Selecciona y manipula herramientas de limpieza para el mantenimiento del aula".
   - Ejemplo: "Reconoce los símbolos patrios a través de actividades plásticas".

2. **ACTIVIDADES VIVENCIALES:**
   - PROHIBIDO actividades abstractas como "Investigar", "Hacer ensayos", "Leer textos largos".
   - OBLIGATORIO actividades concretas: Recortar, Pegar, Pintar, Limpiar, Ordenar, Cantar, Dramatizar.

3. **LENGUAJE HUMANO Y VARIADO:**
   - Evita la repetición robótica.
   - No empieces siempre con "Invitamos a". Usa: "Hoy descubrimos", "Manos a la obra", "Jugamos a".

4. **FORMATO VISUAL:**
   - Usa saltos de línea (doble espacio) para separar secciones.
   - Usa Negritas para resaltar.
"""

def generar_respuesta(mensajes_historial, temperatura=0.7):
    """
    Función wrapper para llamar a la API de Groq con manejo de errores.
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
# 6. SISTEMA DE AUTENTICACIÓN (LOGIN UNIFICADO)
# =============================================================================

# Aquí corregimos el error NameError asegurando que todo ocurre en orden.

# 1. Recuperar parámetros de la URL (si existen)
query_params = st.query_params
usuario_en_url = query_params.get("u", None)

# 2. Intento de Auto-Login si hay parámetro en URL
if not st.session_state.auth and usuario_en_url:
    try:
        df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
        # Limpiar datos para comparación segura
        df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
        usuario_limpio = limpiar_id(usuario_en_url)
        
        match = df_u[df_u['C_L'] == usuario_limpio]
        
        if not match.empty:
            st.session_state.auth = True
            st.session_state.u = match.iloc[0].to_dict()
        else:
            # Si el usuario de la URL no es válido, limpiar URL
            st.query_params.clear()
    except Exception:
        # Si falla la conexión en auto-login, no hacemos nada y mostramos login manual
        pass 

# 3. Pantalla de Login Manual (Si no está autenticado)
if not st.session_state.auth:
    st.title("🛡️ Acceso Legado Maestro")
    
    col_logo, col_form = st.columns([1,2])
    with col_logo:
        if os.path.exists("logo_legado.png"):
            st.image("logo_legado.png", width=150)
        else:
            st.header("🍎")
    
    with col_form:
        st.markdown("### Bienvenido")
        cedula_input = st.text_input("Cédula de Identidad:", key="login_c")
        pass_input = st.text_input("Contraseña:", type="password", key="login_p")
        
        if st.button("🔐 Iniciar Sesión", use_container_width=True):
            try:
                with st.spinner("Verificando credenciales..."):
                    df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
                    
                    # Normalización
                    df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
                    cedula_limpia = limpiar_id(cedula_input)
                    
                    # Búsqueda exacta
                    match = df_u[
                        (df_u['C_L'] == cedula_limpia) & 
                        (df_u['CLAVE'] == pass_input)
                    ]
                    
                    if not match.empty:
                        st.session_state.auth = True
                        st.session_state.u = match.iloc[0].to_dict()
                        # Anclar sesión en URL para recargas
                        st.query_params["u"] = cedula_limpia
                        st.success("¡Acceso Concedido!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas. Verifique Cédula y Contraseña.")
            except Exception as e:
                st.error(f"Error de conexión con la base de datos: {e}")
    
    # Detener ejecución si no está logueado
    st.stop()

# =============================================================================
# 7. INTERFAZ DE BARRA LATERAL (INFORMACIÓN)
# =============================================================================

with st.sidebar:
    if os.path.exists("logo_legado.png"):
        st.image("logo_legado.png", width=150)
    else:
        st.header("🍎")
        
    st.title("Legado Maestro")
    st.caption(f"Prof. {st.session_state.u['NOMBRE']}")
    
    # Mostrar estado de la planificación
    plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    st.markdown("---")
    if plan_activa:
        st.success("📌 **Planificación Activa**")
        st.caption(f"Rango: {plan_activa['RANGO']}")
        st.caption(f"Aula: {plan_activa['AULA']}")
    else:
        st.warning("⚠️ **Sin planificación activa**")
        st.caption("Ve a 'Mi Archivo' para activar una.")

# =============================================================================
# 8. SISTEMA DE NAVEGACIÓN Y VISTAS
# =============================================================================

# Redirección interna automática
if st.session_state.redirigir_a_archivo:
    st.session_state.pagina_actual = "📂 Mi Archivo Pedagógico"
    st.session_state.redirigir_a_archivo = False

# --- VISTA: HOME (PANTALLA DE INICIO) ---
if st.session_state.pagina_actual == "HOME":
    
    # Encabezado de Acciones Rápidas (Para móvil)
    col_clean, col_space, col_logout = st.columns([1, 1, 1])
    
    with col_clean:
        if st.button("🧹 Limpiar", help="Borrar memoria temporal"):
            st.session_state.plan_actual = ""
            st.session_state.actividad_detectada = ""
            st.session_state.eval_resultado = ""
            st.toast("Memoria limpiada")
            time.sleep(0.5)
            st.rerun()
            
    with col_logout:
        if st.button("🔒 Salir", type="primary", help="Cerrar sesión"):
            st.session_state.auth = False
            st.session_state.u = None
            st.query_params.clear() 
            st.rerun()

    st.divider()
    
    st.title("🍎 Asistente Educativo - Zulia")
    st.info(f"👋 Saludos, **{st.session_state.u['NOMBRE']}**. Selecciona una acción:")
    
    st.write("")
    
    # 1. CONTROL DE ASISTENCIA (NUEVO)
    st.markdown("### ⏱️ CONTROL DIARIO")
    sel_asistencia = st.selectbox(
        "Registro de Asistencia:",
        ["(Seleccionar)", "✅ REGISTRAR ASISTENCIA / INASISTENCIA"],
        key="home_asistencia"
    )
    
    # 2. HERRAMIENTAS DE GESTIÓN
    st.markdown("### 🛠️ GESTIÓN DOCENTE")
    sel_principal = st.selectbox(
        "Herramientas de Planificación:",
        [
            "(Seleccionar)",
            "🧠 PLANIFICADOR INTELIGENTE",
            "📜 PLANIFICADOR MINISTERIAL",
            "📝 Evaluar Alumno",
            "📊 Registro de Evaluaciones",
            "📂 Mi Archivo Pedagógico"
        ],
        key="home_gestion"
    )
    
    # 3. RECURSOS
    st.markdown("### 🧩 RECURSOS EXTRA")
    sel_extra = st.selectbox(
        "Apoyo Docente:",
        ["(Seleccionar)", "🌟 Mensaje Motivacional", "💡 Ideas de Actividades", "❓ Consultas Técnicas"],
        key="home_extras"
    )
    
    # Ejecución de cambio de página
    if sel_asistencia != "(Seleccionar)":
        st.session_state.pagina_actual = "⏱️ Control de Asistencia"
        st.rerun()
        
    if sel_principal != "(Seleccionar)":
        st.session_state.pagina_actual = sel_principal
        st.rerun()
        
    if sel_extra != "(Seleccionar)":
        st.session_state.pagina_actual = sel_extra
        st.rerun()

# --- VISTAS DE HERRAMIENTAS (PANTALLA COMPLETA) ---
else:
    # Botón Volver Universal
    col_nav1, col_nav2 = st.columns([1, 4])
    with col_nav1:
        if st.button("⬅️ VOLVER", use_container_width=True):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
    with col_nav2:
        st.subheader(st.session_state.pagina_actual)
    
    st.divider()
    opcion = st.session_state.pagina_actual

    # -------------------------------------------------------------------------
    # VISTA: CONTROL DE ASISTENCIA (NUEVO MÓDULO)
    # -------------------------------------------------------------------------
    if opcion == "⏱️ Control de Asistencia":
        st.info("ℹ️ Este reporte se enviará a **Legado Director** para validación.")
        
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        st.markdown(f"### 📅 Fecha: **{fecha_hoy}**")
        
        estado_asistencia = st.radio(
            "¿Cuál es tu estatus hoy?",
            ["(Seleccionar)", "✅ Asistí al Plantel", "❌ No Asistí"],
            index=0
        )
        
        st.write("")
        
        if estado_asistencia == "✅ Asistí al Plantel":
            hora_sistema = datetime.now().time()
            st.markdown(f"**Hora de registro:** {hora_sistema.strftime('%H:%M:%S')}")
            
            if st.button("📤 Enviar Reporte de Asistencia", type="primary"):
                with st.spinner("Enviando a Dirección..."):
                    res = registrar_asistencia(
                        usuario=st.session_state.u['NOMBRE'],
                        tipo="ASISTENCIA",
                        hora=str(hora_sistema.strftime('%H:%M:%S')),
                        motivo="Cumplimiento de horario",
                        recomendacion_ia="-"
                    )
                    
                    if res == "OK":
                        st.success("✅ ¡Asistencia registrada exitosamente!")
                        time.sleep(2)
                        st.session_state.pagina_actual = "HOME"
                        st.rerun()
                    elif res == "DUPLICADO":
                        st.warning("⚠️ Ya has registrado tu asistencia el día de hoy.")
                    else:
                        st.error(f"Error al registrar: {res}")
        
        elif estado_asistencia == "❌ No Asistí":
            motivo_inasistencia = st.text_area(
                "Motivo de la inasistencia:",
                placeholder="Ej: Cita médica, Malestar de salud, Diligencia personal..."
            )
            
            if st.button("📤 Enviar Justificativo", type="primary"):
                if motivo_inasistencia:
                    with st.spinner("Analizando normativa legal..."):
                        # IA analiza si es salud
                        prompt_analisis = f"""
                        Analiza este motivo: "{motivo_inasistencia}".
                        ¿Implica temas de SALUD (enfermedad, médico, reposo)?
                        Si SÍ, responde: "ALERTA_SALUD".
                        Si NO, responde: "OK".
                        """
                        analisis = generar_respuesta([{"role":"user","content":prompt_analisis}], 0.1)
                        
                        alerta_legal = "-"
                        if "ALERTA_SALUD" in analisis:
                            alerta_legal = "⚠️ IMPORTANTE: Tienes 48 horas para consignar el justificativo médico."
                            st.warning(alerta_legal)
                        
                        res = registrar_asistencia(
                            usuario=st.session_state.u['NOMBRE'],
                            tipo="INASISTENCIA",
                            hora="-",
                            motivo=motivo_inasistencia,
                            recomendacion_ia=alerta_legal
                        )
                        
                        if res == "OK":
                            st.success("✅ Inasistencia reportada. Recupérate pronto.")
                            time.sleep(4)
                            st.session_state.pagina_actual = "HOME"
                            st.rerun()
                        elif res == "DUPLICADO":
                            st.warning("⚠️ Ya has registrado tu reporte hoy.")
                else:
                    st.error("Por favor, ingresa el motivo.")

    # -------------------------------------------------------------------------
    # VISTA: PLANIFICADOR INTELIGENTE
    # -------------------------------------------------------------------------
    elif opcion == "🧠 PLANIFICADOR INTELIGENTE":
        st.markdown("**Creación de Planificación desde Cero**")
        
        col1, col2 = st.columns(2)
        with col1:
            rango = st.text_input("Lapso (Fechas):", placeholder="Ej: 19 al 23 de Enero")
        with col2:
            aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios Generales")
        
        notas = st.text_area("Tema Generador / Notas:", height=150)

        if st.button("🚀 Generar Planificación", type="primary"):
            if rango and notas:
                with st.spinner('Analizando currículo y redactando...'):
                    st.session_state.temp_tema = notas
                    
                    prompt = f"""
                    CONTEXTO: Taller Laboral (Educación Especial). 
                    FECHA: {rango}. AULA: {aula}. TEMA: {notas}.
                    
                    INSTRUCCIÓN: Genera una planificación completa.
                    REQUISITOS:
                    1. Competencias Técnicas descriptivas (Acción+Objeto+Condición).
                    2. Actividades concretas y vivenciales.
                    3. Formato vertical con doble espacio.
                    
                    ESTRUCTURA:
                    ### [DÍA]
                    1. TÍTULO LÚDICO
                    2. COMPETENCIA TÉCNICA
                    3. EXPLORACIÓN
                    4. DESARROLLO
                    5. REFLEXIÓN
                    6. ESTRATEGIAS
                    7. RECURSOS
                    """
                    st.session_state.plan_actual = generar_respuesta([
                        {"role":"system","content":INSTRUCCIONES_TECNICAS},
                        {"role":"user","content":prompt}
                    ], 0.6)
                    st.rerun()

    # -------------------------------------------------------------------------
    # VISTA: PLANIFICADOR MINISTERIAL
    # -------------------------------------------------------------------------
    elif opcion == "📜 PLANIFICADOR MINISTERIAL":
        st.markdown("**Adaptación de Lineamientos**")
        st.info("Pega el texto del Ministerio. Legado Maestro lo adaptará y formateará.")
        
        aula_min = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios")
        texto_ministerio = st.text_area("Texto (WhatsApp):", height=250)
        
        if st.button("🪄 Adaptar y Organizar", type="primary"):
            if texto_ministerio:
                with st.spinner('Adaptando y humanizando actividades...'):
                    # Intentar detectar fecha
                    fechas_enc = re.findall(r'\d{1,2}[/-]\d{1,2}', texto_ministerio)
                    rango_det = f"Semana {fechas_enc[0]}" if fechas_enc else "Semana Ministerial"
                    st.session_state.temp_tema = "Planificación Ministerial Adaptada"
                    
                    prompt = f"""
                    ERES EXPERTO EN CURRÍCULO. ADAPTA ESTO PARA TALLER LABORAL:
                    "{texto_ministerio}"
                    AULA: {aula_min}.
                    
                    1. ENCABEZADO OBLIGATORIO: "📝 **Planificación del Ministerio (Adaptada)**".
                    2. Si hay actividades abstractas, cámbialas a concretas.
                    3. Usa competencias técnicas completas.
                    4. FORMATO: Lista vertical con doble espacio.
                    """
                    
                    st.session_state.plan_actual = generar_respuesta([
                        {"role":"system","content":INSTRUCCIONES_TECNICAS},
                        {"role":"user","content":prompt}
                    ], 0.6)
                    st.rerun()
            else:
                st.warning("Pega el texto primero.")

    # --- BLOQUE DE GUARDADO (COMÚN) ---
    if st.session_state.plan_actual and opcion in ["🧠 PLANIFICADOR INTELIGENTE", "📜 PLANIFICADOR MINISTERIAL"]:
        st.markdown("---")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        if st.button("💾 Guardar en Mi Archivo"):
            try:
                df_archivo = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                tema_guardar = st.session_state.get('temp_tema', 'Planificación')
                
                nueva_fila = pd.DataFrame([{
                    "FECHA": datetime.now().strftime("%d/%m/%Y"),
                    "USUARIO": st.session_state.u['NOMBRE'],
                    "TEMA": tema_guardar[:50], # Limitar largo
                    "CONTENIDO": st.session_state.plan_actual,
                    "ESTADO": "GUARDADO",
                    "HORA_INICIO": "--", "HORA_FIN": "--"
                }])
                
                conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df_archivo, nueva_fila], ignore_index=True))
                st.success("✅ Guardado correctamente.")
                time.sleep(2)
                st.session_state.pagina_actual = "📂 Mi Archivo Pedagógico"
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # -------------------------------------------------------------------------
    # VISTA: EVALUAR ALUMNO
    # -------------------------------------------------------------------------
    elif opcion == "📝 Evaluar Alumno":
        st.subheader("Evaluación Diaria")
        
        pa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
        
        if not pa:
            st.error("🚨 No tienes planificación activa.")
            st.info("Ve a 'Mi Archivo' para activar una.")
        else:
            st.success(f"Evaluando sobre: {pa['RANGO']}")
            
            if st.button("🔍 Buscar Actividad de Hoy"):
                with st.spinner("Buscando en tu plan..."):
                    dia_semana = datetime.now().strftime("%A")
                    prompt_bus = f"""
                    PLAN: {pa['CONTENIDO_PLAN'][:10000]}
                    HOY ES: {dia_semana}.
                    ¿Qué actividad toca hoy? Responde SOLO el título o 'NO HAY ACTIVIDAD'.
                    """
                    res = generar_respuesta([{"role":"user","content":prompt_bus}], 0.1)
                    st.session_state.actividad_detectada = res.strip().replace('"', '')
            
            actividad_final = st.text_input("Actividad:", value=st.session_state.actividad_detectada, disabled=True)
            estudiante = st.text_input("Estudiante:")
            observacion = st.text_area("Observación:")
            
            if st.button("⚡ Generar Evaluación Técnica"):
                if estudiante and observacion:
                    with st.spinner("Analizando..."):
                        p_eval = f"""
                        Evalúa a {estudiante}. Actividad: {actividad_final}. Obs: {observacion}.
                        Genera: Análisis Técnico Cualitativo, Nivel de Logro y Recomendación.
                        """
                        st.session_state.eval_resultado = generar_respuesta([
                            {"role":"system","content":INSTRUCCIONES_TECNICAS},
                            {"role":"user","content":p_eval}
                        ], 0.5)
                        st.session_state.est_temp = estudiante
                        st.session_state.obs_temp = observacion
                else:
                    st.warning("Faltan datos.")
            
            if st.session_state.eval_resultado:
                st.markdown(f'<div class="eval-box">{st.session_state.eval_resultado}</div>', unsafe_allow_html=True)
                
                if st.button("💾 Guardar Registro"):
                    try:
                        df_ev = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                        n_ev = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "USUARIO": st.session_state.u['NOMBRE'],
                            "ESTUDIANTE": st.session_state.est_temp,
                            "ACTIVIDAD": actividad_final,
                            "ANECDOTA": st.session_state.obs_temp,
                            "EVALUACION_IA": st.session_state.eval_resultado,
                            "PLANIFICACION_ACTIVA": pa['RANGO'],
                            "RESULTADO": "Registrado"
                        }])
                        conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, n_ev], ignore_index=True))
                        st.success("Guardado.")
                        st.session_state.eval_resultado = ""
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # -------------------------------------------------------------------------
    # VISTA: REGISTRO DE EVALUACIONES
    # -------------------------------------------------------------------------
    elif opcion == "📊 Registro de Evaluaciones":
        try:
            df = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
            mis_ev = df[df['USUARIO'] == st.session_state.u['NOMBRE']]
            
            if mis_ev.empty:
                st.info("Sin registros.")
            else:
                alumnos = sorted(mis_ev['ESTUDIANTE'].unique())
                alum_sel = st.selectbox("Estudiante:", alumnos)
                dat_alum = mis_ev[mis_ev['ESTUDIANTE'] == alum_sel]
                
                # Métricas
                total = len(df['FECHA'].unique()) 
                asist = len(dat_alum['FECHA'].unique())
                pct = (asist / total) * 100 if total > 0 else 0
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Asistencias", f"{asist}")
                c2.metric("% Asistencia", f"{pct:.1f}%")
                if pct < 60: c3.error("ALERTA")
                else: c3.success("OK")
                
                st.markdown("---")
                
                # Historial
                for _, r in dat_alum.iloc[::-1].iterrows():
                    with st.expander(f"📅 {r['FECHA']} | {r['ACTIVIDAD']}"):
                        st.write(r['EVALUACION_IA'])
                
                # Informe
                if st.button("Generar Informe de Lapso"):
                    with st.spinner("Redactando informe..."):
                        txt_hist = dat_alum['EVALUACION_IA'].to_string()
                        inf = generar_respuesta([{"role":"user","content":f"Genera informe de progreso para {alum_sel}. Datos: {txt_hist}"}])
                        st.markdown(f'<div class="plan-box">{inf}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error BD: {e}")

    # -------------------------------------------------------------------------
    # VISTA: MI ARCHIVO
    # -------------------------------------------------------------------------
    elif opcion == "📂 Mi Archivo Pedagógico":
        pa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
        if pa:
            st.success(f"ACTIVA: {pa['RANGO']}")
            if st.button("Desactivar"):
                desactivar_plan_activa(st.session_state.u['NOMBRE'])
                st.rerun()
        
        try:
            df = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
            mis_planes = df[df['USUARIO'] == st.session_state.u['NOMBRE']]
            
            if mis_planes.empty:
                st.warning("Carpeta vacía.")
            else:
                cont_activo = pa['CONTENIDO_PLAN'] if pa else None
                
                for i, r in mis_planes.iloc[::-1].iterrows():
                    es_act = (cont_activo == r['CONTENIDO'])
                    lbl = f"{'⭐ ACTIVA | ' if es_act else ''}📅 {r['FECHA']} | {str(r['TEMA'])[:30]}..."
                    
                    with st.expander(lbl, expanded=es_act):
                        st.markdown(f'<div class="plan-box" style="font-size:0.9em">{r["CONTENIDO"]}</div>', unsafe_allow_html=True)
                        c1, c2 = st.columns(2)
                        
                        if not es_act:
                            if c1.button("Usar", key=f"a_{i}"):
                                establecer_plan_activa(st.session_state.u['NOMBRE'], str(i), r['CONTENIDO'], "Selecc.", "Taller")
                                st.rerun()
                        
                        if c2.button("Borrar", key=f"d_{i}"):
                            conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df.drop(i))
                            st.rerun()
        except:
            st.error("Error cargando archivos.")

    # -------------------------------------------------------------------------
    # VISTAS: EXTRAS
    # -------------------------------------------------------------------------
    elif opcion == "🌟 Mensaje Motivacional":
        if st.button("Recibir Ánimo"):
            res = generar_respuesta([{"role":"user","content":"Frase motivadora para docente de educación especial en Venezuela."}])
            st.success(res)
            
    elif opcion == "💡 Ideas de Actividades":
        t = st.text_input("Tema:")
        if st.button("Sugerir"):
            res = generar_respuesta([{"role":"user","content":f"3 actividades vivenciales para Taller Laboral: {t}"}])
            st.markdown(res)
            
    elif opcion == "❓ Consultas Técnicas":
        d = st.text_area("Pregunta:")
        if st.button("Consultar"):
            res = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":d}])
            st.info(res)

# --- FIN DEL DOCUMENTO ---
st.markdown("---")
st.caption("Desarrollado por Luis Atencio | Versión: 4.1 (Gold Master Fixed)")
