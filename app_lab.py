# =============================================================================
# PROYECTO: LEGADO MAESTRO
# VERSIÓN: 5.0 (EDICIÓN MAESTRA EXPANDIDA - HORA VENEZUELA + BIOMETRÍA)
# FECHA: Enero 2026
# AUTOR: Luis Atencio (Bachiller Docente)
# INSTITUCIÓN: T.E.L E.R.A.C
#
# DESCRIPCIÓN:
# Plataforma de gestión pedagógica basada en Inteligencia Artificial.
# Incluye: Asistencia Biométrica (Drive), Planificación, Evaluación y Gestión de Archivos.
# Correcciones: Zona Horaria (UTC-4), Navegación Móvil, Login Seguro, Compresión de Imagen.
# =============================================================================

import streamlit as st
import os
import time
from datetime import datetime, timedelta
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random
import re
import io
import json # Para procesar la respuesta de ImgBB
import requests # Librería principal para subir la foto a ImgBB
from PIL import Image # Para la compresión tipo WhatsApp

# =============================================================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ID DE LA CARPETA DE GOOGLE DRIVE (CONFIGURADO POR LUIS ATENCIO)
ID_CARPETA_DRIVE = "1giVsa-iSbg8QyGbPwj6r3UzVKSCu1POn"
# -----------------------------------------------------------------------------
# 2. FUNCIONES UTILITARIAS (TIEMPO Y FORMATO)
# -----------------------------------------------------------------------------

def ahora_ve():
    """
    Retorna la fecha y hora actual ajustada a la Zona Horaria de Venezuela (UTC-4).
    Esto es crucial porque los servidores suelen estar en hora UTC (Londres).
    """
    hora_utc = datetime.utcnow()
    hora_venezuela = hora_utc - timedelta(hours=4)
    return hora_venezuela

def limpiar_id(v): 
    """
    Limpia el formato de la cédula de identidad para comparaciones en base de datos.
    Elimina puntos, comas, espacios y letras como 'V-' o 'E-'.
    """
    if v is None:
        return ""
    
    valor_str = str(v).strip().upper()
    # Eliminar decimales si viene de un Excel numérico
    valor_limpio = valor_str.split('.')[0]
    
    # Reemplazos de limpieza
    valor_limpio = valor_limpio.replace(',', '')
    valor_limpio = valor_limpio.replace('.', '')
    valor_limpio = valor_limpio.replace('V-', '')
    valor_limpio = valor_limpio.replace('E-', '')
    valor_limpio = valor_limpio.replace(' ', '')
    
    return valor_limpio

def comprimir_imagen(archivo_camara):
    """
    Función v5.0: Comprime la imagen capturada para ahorrar espacio en Drive y datos.
    Reduce el peso manteniendo la legibilidad técnica (Tipo WhatsApp).
    """
    img = Image.open(archivo_camara)
    # Convertir a RGB por compatibilidad con JPEG
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Redimensionar si es muy grande (max 800px de ancho)
    ancho_max = 800
    if img.width > ancho_max:
        proporcion = (ancho_max / float(img.width))
        alto = int((float(img.height) * float(proporcion)))
        img = img.resize((ancho_max, alto), Image.Resampling.LANCZOS)
    
    # Guardar con calidad balanceada (70%)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70, optimize=True)
    buffer.seek(0)
    return buffer

# =============================================================================
# 3. ESTILOS CSS (INTERFAZ VISUAL ORIGINAL COMPLETA)
# =============================================================================

hide_streamlit_style = """
<style>
    /* Ocultar elementos nativos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* CAJAS DE PLANIFICACIÓN */
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

    /* CAJAS DE EVALUACIÓN (Resultados IA) */
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

    /* ESTILOS PARA ELEMENTOS DE FORMULARIO (MÓVIL) */
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
        height: 3.5em;
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
# 4. CONEXIONES A SERVICIOS EXTERNOS (GSHEETS, GROQ, DRIVE)
# =============================================================================

# --- 4.1 Conexión a Base de Datos (Google Sheets) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    if "GSHEETS_URL" not in st.secrets:
        st.error("⚠️ Error de Configuración: No se encontró 'GSHEETS_URL' en los secrets.")
        st.stop()
        
    URL_HOJA = st.secrets["GSHEETS_URL"]
    
except Exception as e:
    st.error("⚠️ Error Crítico: No se pudo establecer conexión con la Base de Datos.")
    st.error(f"Detalle técnico: {e}")
    st.stop()

# --- 4.2 Conexión a Inteligencia Artificial (Groq) ---
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

# --- 4.3 Conexión a Google Drive API (v5.0) ---
def subir_a_imgbb(archivo_foto):
    """Sube la foto a ImgBB usando la llave de Luis Atencio y devuelve el link."""
    try:
        # 1. Tu API KEY que me acabas de dar
        API_KEY = "3bc2c5bae6c883fdcdcc4da6ec4122bd"
        
        # 2. Comprimir la imagen (Usando tu lógica de Pillow)
        img = Image.open(archivo_foto)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.thumbnail((800, 800))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        foto_bytes = buf.getvalue()

        # 3. Envío directo a ImgBB
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": API_KEY,
        }
        files = {
            'image': foto_bytes,
        }
        
        res = requests.post(url, payload, files=files)
        
        if res.status_code == 200:
            # Retornamos el link directo de la imagen
            return res.json()['data']['url']
        else:
            st.error(f"Error en ImgBB: {res.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# =============================================================================
# 5. GESTIÓN DE VARIABLES DE ESTADO (MEMORIA DE SESIÓN)
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
# 6. LÓGICA DE NEGOCIO (BACKEND ORIGINAL COMPLETO)
# =============================================================================

# --- 6.1 Funciones de Planificación Activa ---

def obtener_plan_activa_usuario(usuario_nombre):
    """
    Obtiene la planificación activa actual del usuario desde la nube.
    """
    try:
        # Leemos con un TTL bajo (5 seg) para tener datos frescos
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
        return None

def establecer_plan_activa(usuario_nombre, id_plan, contenido, rango, aula):
    """
    Establece una planificación específica como la 'Activa' para evaluaciones.
    Usa la hora de Venezuela para el registro.
    """
    try:
        # Intentar leer hoja existente
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
        
        # 2. Agregar la nueva planificación activa (Usando Hora Venezuela)
        fecha_ve = ahora_ve().strftime("%d/%m/%Y %H:%M:%S")
        
        nueva_activa = pd.DataFrame([{
            "USUARIO": usuario_nombre,
            "FECHA_ACTIVACION": fecha_ve,
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
        st.error(f"Error al activar planificación: {e}")
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

# --- 6.2 Función de Asistencia (VERSIÓN 5.0 - BIOMÉTRICA INTEGRAL) ---

def registrar_asistencia_biometrica(usuario, tipo, hora_e, hora_s, foto_e, foto_s, motivo, alerta_ia):
    """Escribe los datos en las columnas correctas de la hoja ASISTENCIA."""
    try:
        time.sleep(1) 
        df_asistencia = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=0)
        hoy_str = ahora_ve().strftime("%d/%m/%Y")
        
        # Buscar registro de hoy
        registro_hoy = df_asistencia[(df_asistencia['USUARIO'] == usuario) & (df_asistencia['FECHA'] == hoy_str)]
        
        if registro_hoy.empty:
            # ENTRADA: Aquí usamos el nombre de columna 'HORA_ENTRADA'
            nuevo_registro = pd.DataFrame([{
                "FECHA": hoy_str, 
                "USUARIO": usuario, 
                "TIPO": tipo,
                "HORA_ENTRADA": hora_e, # <--- Esto escribirá en tu columna D
                "FOTO_ENTRADA": foto_e,
                "HORA_SALIDA": "-", 
                "FOTO_SALIDA": "-",
                "MOTIVO": motivo, 
                "ALERTA_IA": alerta_ia, 
                "ESTADO_DIRECTOR": "PENDIENTE",
                "PUNTOS_MERITO": 0
            }])
            df_final = pd.concat([df_asistencia, nuevo_registro], ignore_index=True)
            conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_final)
            return "OK"
        else:
            # SALIDA: Actualizamos la misma fila
            idx = registro_hoy.index[0]
            if hora_s != "-":
                df_asistencia.at[idx, 'HORA_SALIDA'] = hora_s
                df_asistencia.at[idx, 'FOTO_SALIDA'] = foto_s
                df_asistencia.at[idx, 'MOTIVO'] = motivo
                conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_asistencia)
                return "OK"
            return "DUPLICADO"
    except Exception as e:
        return f"ERROR: {e}"

# --- 6.3 Generador de Respuestas IA ---

def generar_respuesta(mensajes_historial, temperatura=0.7):
    """
    Envía prompt a Groq y maneja errores de conexión.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes_historial,
            model=MODELO_USADO,
            temperature=temperatura,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error de conexión con IA: {e}"

# PROMPT MAESTRO (Definición de Personalidad ORIGINAL)
INSTRUCCIONES_TECNICAS = """
# PROMPT MAESTRO (PERSONALIDAD LUIS ATENCIO V6.0 - MULTIMODALIDAD)
INSTRUCCIONES_TECNICAS = """
# PROMPT MAESTRO (PERSONALIDAD LUIS ATENCIO V6.0 - MULTIMODALIDAD)
INSTRUCCIONES_TECNICAS = """
IMPORTANTE: ERES "LEGADO MAESTRO".
TU ROL: Experto de alto nivel en el Currículo Nacional Bolivariano y especialista en las 6 modalidades de Educación Especial en Venezuela:
1. Taller de Educación Laboral (T.E.L.)
2. Instituto de Educación Especial Bolivariano (I.E.E.B.)
3. Centro de Atención Integral para Personas con Autismo (C.A.I.P.A.)
4. Aula Integrada (Apoyo en Escuela Regular)
5. Unidad Psico-Educativa (U.P.E.)
6. Educación Inicial (Preescolar)

REGLAS PEDAGÓGICAS INQUEBRANTABLES:
1. COMPETENCIAS TÉCNICAS (ESTRUCTURA OBLIGATORIA): NUNCA uses un verbo solitario. Estructura: VERBO (Acción) + OBJETO (Qué) + CONDICIÓN (Cómo/Para qué).
2. ACTIVIDADES VIVENCIALES: PROHIBIDO investigar o leer textos largos. OBLIGATORIO: Recortar, Pegar, Pintar, Limpiar, Ordenar, Cantar, Cocinar, Modelar.
3. LENGUAJE HUMANO: Estilo motivador, evita sonar robótico. Usa "Hoy descubrimos", "Manos a la obra".

4. FORMATO VISUAL:
   - Usa saltos de línea (doble espacio) entre secciones.
   - Usa Negritas para los títulos.
"""

# =============================================================================
# 7. SISTEMA DE LOGIN (ORIGINAL COMPLETO)
# =============================================================================

# Obtener parámetros de URL de forma segura
query_params = st.query_params
usuario_en_url = query_params.get("u", None)

# 1. Intento de Auto-Login
if not st.session_state.auth and usuario_en_url:
    try:
        df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
        
        # Limpiamos para comparar
        df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
        usuario_limpio = limpiar_id(usuario_en_url)
        
        match = df_u[df_u['C_L'] == usuario_limpio]
        
        if not match.empty:
            st.session_state.auth = True
            st.session_state.u = match.iloc[0].to_dict()
        else:
            st.query_params.clear()
    except:
        pass 

# 2. Pantalla de Login Manual (Si no está logueado)
if not st.session_state.auth:
    st.title("🛡️ Acceso Legado Maestro")
    
    col_logo, col_form = st.columns([1,2])
    with col_logo:
        if os.path.exists("logo_legado.png"):
            st.image("logo_legado.png", width=150)
        else:
            st.header("🍎")
    
    with col_form:
        st.markdown("### Iniciar Sesión")
        cedula_input = st.text_input("Cédula de Identidad:", key="login_c")
        pass_input = st.text_input("Contraseña:", type="password", key="login_p")
        
        if st.button("🔐 Entrar", use_container_width=True):
            try:
                with st.spinner("Verificando..."):
                    df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
                    
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
                        st.query_params["u"] = cedula_limpia # Anclar sesión
                        st.success("¡Bienvenido!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
    st.stop()

# =============================================================================
# 8. INTERFAZ DE BARRA LATERAL (INFORMACIÓN ORIGINAL)
# =============================================================================

with st.sidebar:
    if os.path.exists("logo_legado.png"):
        st.image("logo_legado.png", width=150)
    else:
        st.header("🍎")
        
    st.title("Legado Maestro")
    st.caption(f"Prof. {st.session_state.u['NOMBRE']}")
    
    # Mostrar estado de planificación activa
    plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    st.markdown("---")
    if plan_activa:
        st.success("📌 **Planificación Activa**")
        with st.expander("Ver detalles", expanded=False):
            st.caption(f"**Rango:** {plan_activa['RANGO']}")
            st.caption(f"**Aula:** {plan_activa['AULA']}")
            st.caption(f"Activada: {plan_activa['FECHA_ACTIVACION'].split()[0]}")
    else:
        st.warning("⚠️ **Sin planificación activa**")
        st.caption("Ve a 'Mi Archivo' para activar una.")

# =============================================================================
# 9. SISTEMA DE NAVEGACIÓN Y VISTAS (INTEGRACIÓN TOTAL)
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
    
    # 1. CONTROL DE ASISTENCIA
    st.markdown("### ⏱️ CONTROL DIARIO")
    if st.button("📸 REGISTRAR ASISTENCIA / SALIDA", type="primary", use_container_width=True):
        st.session_state.pagina_actual = "⏱️ Control de Asistencia"
        st.rerun()
    
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
    # -------------------------------------------------------------------------
    # VISTA: CONTROL DE ASISTENCIA (VERSIÓN 5.1 - RESILIENTE A FALLAS ELÉCTRICAS)
    # -------------------------------------------------------------------------
    if opcion == "⏱️ Control de Asistencia":
        st.info("ℹ️ Reporte de asistencia con respaldo por incidencias técnicas (Luz/Datos).")
        hoy_str = ahora_ve().strftime("%d/%m/%Y")
        st.markdown(f"### 📅 Fecha: **{hoy_str}**")

        try:
            df_as = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=2)
            reg_hoy = df_as[(df_as['USUARIO'] == st.session_state.u['NOMBRE']) & (df_as['FECHA'] == hoy_str)]
        except:
            st.error("🔄 Conexión lenta. Reintentando...")
            time.sleep(2); st.rerun()

        hora_actual = ahora_ve()

        # --- ESCENARIO A: REGISTRO DE ENTRADA ---
        if reg_hoy.empty:
            status = st.radio("¿Estatus hoy?", ["(Seleccionar)", "✅ Asistí al Plantel", "❌ No Asistí"], index=0)
            
            if status == "✅ Asistí al Plantel":
                # Detectar si es entrada tardía (ejemplo: después de las 8:15 AM)
                es_entrada_tardia = hora_actual.hour > 8 or (hora_actual.hour == 8 and hora_actual.minute > 15)
                
                motivo_entrada = "Cumplimiento"
                if es_entrada_tardia:
                    st.warning("⚠️ **Entrada fuera de horario:** ¿Hubo algún inconveniente técnico?")
                    incidencia_e = st.selectbox("Indique la razón del retraso en el registro:", [
                        "Sin inconvenientes (Llegada tardía)",
                        "Corte Eléctrico en la Institución/Sector",
                        "Sin señal de Datos Móviles / Internet",
                        "Problemas de Transporte",
                        "Otro (Explicar en observación)"
                    ])
                    if incidencia_e != "Sin inconvenientes (Llegada tardía)":
                        obs_e = st.text_input("Breve observación (Ej: Hora real de llegada):")
                        motivo_entrada = f"INCIDENCIA: {incidencia_e} | {obs_e}"
                    else:
                        motivo_entrada = "Llegada Tardía"

                foto_ent = st.camera_input("📸 Foto de Entrada (Presencia)")
                if foto_ent and st.button("🚀 Confirmar Entrada"):
                    with st.spinner("Subiendo evidencia..."):
                        url_e = subir_a_imgbb(foto_ent)
                        if url_e:
                            h_ent_sistema = ahora_ve().strftime('%I:%M %p')
                            res = registrar_asistencia_biometrica(
                                st.session_state.u['NOMBRE'], "ASISTENCIA", h_ent_sistema, "-", 
                                url_e, "-", motivo_entrada, "ENTRADA_REVISAR" if es_entrada_tardia else "-"
                            )
                            st.success(f"✅ Entrada enviada. Marcado: {h_ent_sistema}")
                            time.sleep(3); st.session_state.pagina_actual = "HOME"; st.rerun()

            elif status == "❌ No Asistí":
                motivo_i = st.text_area("Justificativo:")
                if st.button("📤 Enviar Reporte"):
                    an = generar_respuesta([{"role":"user","content":f"¿Es salud? '{motivo_i}'"}], 0.1)
                    alerta = "⚠️ Presentar justificativo médico." if "ALERTA_SALUD" in an else "-"
                    registrar_asistencia_biometrica(st.session_state.u['NOMBRE'], "INASISTENCIA", "-", "-", "-", "-", motivo_i, alerta)
                    st.warning("✅ Inasistencia reportada."); time.sleep(2); st.session_state.pagina_actual = "HOME"; st.rerun()

       # --- ESCENARIO B: REGISTRO DE SALIDA ---
        elif reg_hoy.iloc[0]['HORA_SALIDA'] == "-":
            st.success(f"🟢 Entrada registrada a las: {reg_hoy.iloc[0]['HORA_ENTRADA']}")
            
            # --- LÓGICA DE COHERENCIA HORARIA ---
            hora_v = ahora_ve()
            h_actual = hora_v.hour
            
            # Se considera fuera de hora si:
            # 1. Es después de las 2:00 PM (14:00)
            # 2. O si es antes de las 11:00 AM (Significa que olvidó marcar ayer y lo hace de madrugada)
            es_fuera_de_horario = h_actual >= 14 or h_actual < 11
            
            motivo_salida = ""
            
            if es_fuera_de_horario:
                st.warning("⚠️ **Registro de Salida fuera de horario:**")
                st.info(f"El sistema detecta que son las {hora_v.strftime('%I:%M %p')}. Por favor, justifique por qué registra a esta hora.")
                
                incidencia_s = st.selectbox("Inconveniente presentado:", [
                    "Corte Eléctrico / Sin Luz",
                    "Sin Datos Móviles / Falla de Red",
                    "Olvidé marcar al salir de la institución",
                    "Actividad fuera del plantel prolongada",
                    "Otro motivo"
                ])
                
                obs_s = st.text_input("Indique su HORA REAL de salida (según libro físico):", placeholder="Ej: 1:00 PM")
                
                if not obs_s:
                    st.stop() # No deja continuar hasta que escriba la hora real
                
                motivo_salida = f"FUERA_HORA: {incidencia_s} | Salida Real: {obs_s}"
            else:
                # Horario Normal (Entre 11 AM y 1:59 PM)
                tipo_s = st.selectbox("Estatus jornada:", ["Salida Normal", "Trabajo Extra (Suma de Méritos)"])
                motivo_salida = tipo_s

            foto_sal = st.camera_input("📸 Foto de Verificación (Evidencia de Salida)")
            
            if foto_sal:
                if st.button("🏁 Finalizar Jornada"):
                    with st.spinner("Procesando registro..."):
                        url_s = subir_a_imgbb(foto_sal)
                        if url_s:
                            h_sistema = ahora_ve().strftime('%I:%M %p')
                            res = registrar_asistencia_biometrica(
                                st.session_state.u['NOMBRE'], "ASISTENCIA", "-", h_sistema, 
                                "-", url_s, motivo_salida, "SALIDA_REVISAR" if es_fuera_de_horario else "-"
                            )
                            st.balloons()
                            st.success(f"✅ Salida registrada a las {h_sistema}")
                            if es_fuera_de_horario:
                                st.info("📢 Su reporte fue enviado con alerta para validación del Director.")
                            time.sleep(3)
                            st.session_state.pagina_actual = "HOME"
                            st.rerun()
        else:
            st.info("✅ Registro del día completado.")
            if st.button("⬅️ Volver"): st.session_state.pagina_actual = "HOME"; st.rerun()
 # -------------------------------------------------------------------------
    # VISTA: PLANIFICADOR INTELIGENTE (VERSIÓN 6.2 - ESTRUCTURA NACIONAL BOLIVARIANA)
    # -------------------------------------------------------------------------
    elif opcion == "🧠 PLANIFICADOR INTELIGENTE":
        st.markdown("**Generación de Planificación Pedagógica Especializada**")
        
        col1, col2 = st.columns(2)
        with col1:
            rango = st.text_input("Lapso (Fechas):", placeholder="Ej: 19 al 23 de Enero")
        with col2:
            modalidad = st.selectbox("Modalidad / Servicio:", [
                "Taller de Educación Laboral (T.E.L.)",
                "Instituto de Educación Especial (I.E.E.B.)",
                "Centro de Atención Integral para Personas con Autismo (C.A.I.P.A.)",
                "Aula Integrada (Escuela Regular)",
                "Unidad Psico-Educativa (U.P.E.)",
                "Educación Inicial (Preescolar)"
            ])
        
        aula_especifica = ""
        if modalidad == "Taller de Educación Laboral (T.E.L.)":
            aula_especifica = st.text_input("Especifique el Taller / Aula:", 
                                            placeholder="Ej: Carpintería, Cocina, Jardinería...")
        
        is_pei = st.checkbox("🎯 ¿Planificación Individualizada (P.E.I.)?")
        
        perfil_alumno = ""
        if is_pei:
            perfil_alumno = st.text_area("Perfil del Alumno (Potencialidades y Necesidades):", 
                                        placeholder="Describa brevemente al estudiante...")
        
        notas = st.text_area("Tema Generador / Referente Ético / Notas:", height=100)

        if st.button("🚀 Generar Planificación Estructurada", type="primary"):
            if rango and notas:
                if is_pei and not perfil_alumno:
                    st.error("⚠️ Para P.E.I. debe describir el perfil.")
                elif modalidad == "Taller de Educación Laboral (T.E.L.)" and not aula_especifica:
                    st.error("⚠️ Especifique el área del Taller.")
                else:
                    with st.spinner('Estructurando planificación bajo lineamientos del MPPE...'):
                        contexto_aula = f" del área de {aula_especifica}" if aula_especifica else ""
                        st.session_state.temp_tema = f"{modalidad}{contexto_aula} - {notas}"
                        
                        tipo_plan = "P.E.I. (Individualizada)" if is_pei else "Grupal"
                        
                        prompt = f"""
                        ERES UN EXPERTO PEDAGOGO.
                        Genera una: 📝 **Planificación Sugerida (Currículo Nacional Bolivariano)**
                        MODALIDAD: {modalidad}{contexto_aula}.
                        TIPO: {tipo_plan}.
                        LAPSO: {rango}.
                        TEMA: {notas}.
                        {f'PERFIL ALUMNO: {perfil_alumno}' if is_pei else ''}

                        REGLAS CRÍTICAS DE FORMATO:
                        1. CADA PUNTO (1 AL 7) DEBE EMPEZAR EN UNA LÍNEA NUEVA. 
                        2. PROHIBIDO ESCRIBIR LOS PUNTOS SEGUIDOS EN EL MISMO PÁRRAFO.
                        3. USA UN SALTO DE LÍNEA DOBLE ENTRE CADA SECCIÓN.
                        
                        PARA CADA DÍA SIGUE ESTE MODELO EXACTO:
                        
                        ### [DÍA Y FECHA]
                        **1. TÍTULO LÚDICO:** (Nombre creativo de la actividad)
                        
                        **2. COMPETENCIA TÉCNICA:** (Acción + Objeto + Condición)
                        
                        **3. EXPLORACIÓN (Inicio):** (Actividad vivencial)
                        
                        **4. DESARROLLO (Proceso):** (Manos a la obra)
                        
                        **5. REFLEXIÓN (Cierre):** (Intercambio de saberes)
                        
                        **6. ESTRATEGIAS:** (Cómo se enseñará)
                        
                        **7. RECURSOS:** (Materiales concretos)
                        
                        ---------------------------------------------------
                        """
                        
                        st.session_state.plan_actual = generar_respuesta([
                            {"role":"system","content":INSTRUCCIONES_TECNICAS},
                            {"role":"user","content":prompt}
                        ], 0.5) # Temperatura más baja para ser más preciso y menos "emocionado"
                        st.rerun()

    # -------------------------------------------------------------------------
    # VISTA: PLANIFICADOR MINISTERIAL (ORIGINAL PRESERVADA)
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
                
                # USAMOS AHORA_VE() PARA LA FECHA DE GUARDADO
                fecha_guardado = ahora_ve().strftime("%d/%m/%Y")
                
                nueva_fila = pd.DataFrame([{
                    "FECHA": fecha_guardado,
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
    # VISTA: EVALUAR ALUMNO (ORIGINAL PRESERVADA)
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
                    # USAMOS AHORA_VE() PARA DIA CORRECTO
                    dia_semana = ahora_ve().strftime("%A")
                    
                    prompt_bus = f"""
                    PLAN: {pa['CONTENIDO_PLAN'][:10000]}
                    HOY ES: {dia_semana} (En Venezuela).
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
                        Genera Análisis Técnico Cualitativo, Nivel de Logro y Recomendación.
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
                        
                        # USAMOS AHORA_VE()
                        fecha_registro = ahora_ve().strftime("%d/%m/%Y")
                        
                        n_ev = pd.DataFrame([{
                            "FECHA": fecha_registro,
                            "USUARIO": st.session_state.u['NOMBRE'],
                            "ESTUDIANTE": st.session_state.est_temp,
                            "ACTIVIDAD": actividad_final,
                            "ANECDOTA": st.session_state.obs_temp,
                            "EVALUACION_IA": st.session_state.eval_resultado,
                            "PLANIFICACION_ACTIVA": pa['RANGO'],
                            "RESULTADO": "Registrado"
                        }])
                        conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, n_ev], ignore_index=True))
                        st.success("Guardado."); st.session_state.eval_resultado = ""; time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # -------------------------------------------------------------------------
    # VISTA: REGISTRO DE EVALUACIONES (ORIGINAL PRESERVADA)
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
                if total > 0:
                    pct = (asist / total) * 100 
                else:
                    pct = 0
                
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
    # VISTA: MI ARCHIVO (ORIGINAL PRESERVADA)
    # -------------------------------------------------------------------------
    elif opcion == "📂 Mi Archivo Pedagógico":
        pa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
        if pa:
            st.success(f"ACTIVA: {pa['RANGO']}")
            if st.button("Desactivar"):
                desactivar_plan_activa(st.session_state.u['NOMBRE']); st.rerun()
        
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
                                establecer_plan_activa(st.session_state.u['NOMBRE'], str(i), r['CONTENIDO'], r['FECHA'], "Taller")
                                st.rerun()
                        
                        if c2.button("Borrar", key=f"d_{i}"):
                            conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df.drop(i)); st.rerun()
        except:
            st.error("Error cargando archivos.")

    # -------------------------------------------------------------------------
    # VISTAS: EXTRAS (ORIGINALES PRESERVADAS)
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
st.caption("Desarrollado por Luis Atencio | Versión: 5.0 (Edición Maestra Real)")
