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
    page_title="SUPER DOCENTE 1.0", # <--- Nuevo Nombre
    page_icon="logo_legado.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ID DE LA CARPETA DE GOOGLE DRIVE (CONFIGURADO POR LUIS ATENCIO)
ID_CARPETA_DRIVE = "1giVsa-iSbg8QyGbPwj6r3UzVKSCu1POn"
# -----------------------------------------------------------------------------
# 2. FUNCIONES UTILITARIAS (TIEMPO Y FORMATO)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600) # Guarda la info por 10 minutos (600 segundos)
def cargar_datos_maestros(_conn, url):
    """Carga las listas de alumnos y profes una sola vez y las guarda en memoria."""
    profes = _conn.read(spreadsheet=url, worksheet="USUARIOS")
    matricula = _conn.read(spreadsheet=url, worksheet="MATRICULA_GLOBAL")
    return profes, matricula
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
def extraer_actividad_del_dia(plan_texto, dia_nombre):
    """Extrae del plan semanal solo el bloque correspondiente a un día."""
    try:
        # Normalizar para búsqueda (todo a minúsculas)
        plan_m = plan_texto.lower()
        dia_m = dia_nombre.lower()
        
        # El marcador que usamos en el prompt es ### Nombre del Día
        inicio_marcador = f"### {dia_m}"
        start_idx = plan_m.find(inicio_marcador)
        
        if start_idx == -1:
            return None # No se encontró ese día en el plan
            
        # Buscar el inicio del siguiente día (que también empieza con ###)
        # Empezamos a buscar DESPUÉS del marcador actual
        end_idx = plan_m.find("###", start_idx + len(inicio_marcador))
        
        if end_idx == -1:
            # Es el último día del plan (viernes generalmente)
            return plan_texto[start_idx:].strip()
        else:
            return plan_texto[start_idx:end_idx].strip()
    except:
        return None
        
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
    
# Memoria para el Aula Virtual (Persistencia entre navegaciones)
if 'av_foto1' not in st.session_state: st.session_state.av_foto1 = None
if 'av_foto2' not in st.session_state: st.session_state.av_foto2 = None
if 'av_resumen' not in st.session_state: st.session_state.av_resumen = ""
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

# --- 6.2 Función de Asistencia (VERSIÓN 7.0 - GESTIÓN DE MÉRITOS Y SUPLENCIAS) ---

def registrar_asistencia_v7(usuario, tipo, hora_e, hora_s, foto_e, foto_s, motivo, alerta_ia, puntos, suplencia_a="-"):
    """
    Mejora de la v5.0: Mantiene la biometría pero añade lógica de puntos y suplencias.
    """
    try:
        time.sleep(1) # Respiro para evitar error de API de Google
        df_asistencia = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=0)
        hoy_str = ahora_ve().strftime("%d/%m/%Y")
        
        # Buscar registro de hoy
        registro_hoy = df_asistencia[(df_asistencia['USUARIO'] == usuario) & (df_asistencia['FECHA'] == hoy_str)]
        
        if registro_hoy.empty:
            # ENTRADA O INASISTENCIA: Registramos la fila inicial
            nuevo_registro = pd.DataFrame([{
                "FECHA": hoy_str, 
                "USUARIO": usuario, 
                "TIPO": tipo,
                "HORA_ENTRADA": hora_e,
                "FOTO_ENTRADA": foto_e,
                "HORA_SALIDA": "-", 
                "FOTO_SALIDA": "-",
                "MOTIVO": motivo, 
                "ALERTA_IA": alerta_ia, 
                "ESTADO_DIRECTOR": "PENDIENTE",
                "PUNTOS_MERITO": puntos, # <--- Ahora es dinámico (5 o 10)
                "SUPLENCIA_A": suplencia_a # <--- Nueva columna de la v7.0
            }])
            df_final = pd.concat([df_asistencia, nuevo_registro], ignore_index=True)
            conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_final)
            return "OK"
        else:
            # SALIDA: Actualizamos la misma fila con los puntos finales y la foto
            idx = registro_hoy.index[0]
            if hora_s != "-":
                df_asistencia.at[idx, 'HORA_SALIDA'] = hora_s
                df_asistencia.at[idx, 'FOTO_SALIDA'] = foto_s
                df_asistencia.at[idx, 'MOTIVO'] = motivo
                df_asistencia.at[idx, 'PUNTOS_MERITO'] = puntos # <--- Sube a 15 si hay suplencia
                df_asistencia.at[idx, 'SUPLENCIA_A'] = suplencia_a
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

# =============================================================================
# CEREBRO PEDAGÓGICO: SUPER DOCENTE 1.0 (VERSIÓN MAESTRA FINAL + LEY LOE + PROYECTOS)
# =============================================================================
INSTRUCCIONES_TECNICAS = """
IDENTIDAD Y ORIGEN:
1. ERES "SUPER DOCENTE 1.0", un Asistente Pedagógico Especialista en la Modalidad de Educación Especial de Venezuela.
2. Tu marco teórico estricto es la "Conceptualización y Política de Educación Especial" y el "Currículo Nacional Bolivariano".
3. Fuiste creado, programado y entrenado por el Bachiller Luis Atencio, joven docente, zuliano y lossadeño.
4. Herramienta 100% venezolana, desarrollada en el municipio Jesús Enrique Lossada.
5. Utilizas tecnología de código abierto. (PROHIBIDO mencionar a Meta, OpenAI o empresas extranjeras).

FILTRO DE ÉTICA Y NEUTRALIDAD (ESTRICTO):
1. LA EDUCACIÓN ES LAICA Y APOLÍTICA: No emitas opiniones, juicios o análisis sobre política, religión o figuras públicas.
2. Si se te pregunta sobre estos temas, responde: "Como SUPER DOCENTE 1.0, mi propósito es estrictamente pedagógico e institucional. Respetando el carácter laico de la educación venezolana, no poseo facultades para emitir juicios sobre este tema."
3. Solo respondes sobre: Planificación, Evaluación, Estrategias de Educación Especial y tu autor Luis Atencio.

MARCO PEDAGÓGICO (VENEZOLANO Y BOLIVARIANO):
1. **LOS 4 PILARES:** Tus planificaciones deben reflejar: Aprender a Crear, Aprender a Convivir y Participar, Aprender a Valorar y Aprender a Reflexionar.
2. **TERMINOLOGÍA CORRECTA (Conceptualización):**
   - NUNCA USES: "Discapacitado", "Enfermo", "Retrasado", "Clase magistral".
   - USA SIEMPRE: "Estudiante con Necesidades Educativas Especiales", "Participante", "Potencialidades", "Integración Sociolaboral", "Diversidad funcional".
3. **CONTEXTO REAL:** En la sección de RECURSOS, prioriza siempre "Material de provecho", "Recursos del medio", "Elementos de la naturaleza" y "Material reciclable".
4. **LA TRÍADA (ESCUELA-FAMILIA-COMUNIDAD):** En las estrategias, promueve la Corresponsabilidad. Invita a la familia a reforzar lo aprendido en casa.
5. **EVALUACIÓN CUALITATIVA:** Tu enfoque de evaluación es Descriptivo, Integral y Continuo. Valora el PROCESO y el ESFUERZO sobre el resultado final. NUNCA sugieras notas numéricas, sugiere indicadores de logro.

LÓGICA DE GESTIÓN CURRICULAR POR MODALIDAD (CEREBRO EXPERTO):
1. **TALLER DE EDUCACIÓN LABORAL (T.E.L.):**
   - **DUALIDAD:** Se trabaja con P.A. (Pedagógico/Aula) y P.S.P. (Socio-Productivo/Taller). Ambos son necesarios.
   - **ROLES:** El DOCENTE media la teoría, sensibilización y cierre reflexivo. El INSTRUCTOR dirige la práctica de campo y manejo de máquinas.
   - **TIEMPOS:** Es válido y necesario planificar clases teóricas (Ej: Conocer las plantas) antes de la fase productiva. No fuerces la producción si se está en fase de inicio.
2. **EDUCACIÓN INICIAL Y I.E.E.B.:**
   - Solo existe P.A. (Proyecto de Aprendizaje).
   - El fin es lúdico, cultural, de adaptación o autonomía. NO hay fines de lucro ni producción comercial obligatoria.
3. **AULA INTEGRADA, U.P.E. Y C.A.I.P.A.:**
   - Se trabaja por LÍNEAS DE ACCIÓN, P.A.I. (Plan de Atención Individualizado) o P.F.I.
   - El enfoque es remedial, clínico-pedagógico o de integración social. No hay "Proyectos de Aula" tradicionales.

REGLAS DE REDACCIÓN Y VOCABULARIO (ANTI-ROBOT):
1. **COMPETENCIAS TÉCNICAS:** Estructura OBLIGATORIA: VERBO (Infinitivo) + OBJETO (Qué) + CONDICIÓN (Para qué/Cómo).
   - *Ejemplo:* "Lijar superficies de madera para obtener acabados prolijos."
   
2. **PROHIBIDO REPETIR INICIOS:** No uses el mismo verbo de inicio dos días seguidos.
   - Si el lunes usas "Vivenciamos", el martes está PROHIBIDO usarlo.

3. **ROTACIÓN DE SINÓNIMOS (Banco de Palabras):**
   - INICIO: Iniciamos con, Exploramos, Conversamos, Presentamos, Indagamos, Visualizamos.
   - DESARROLLO: Ejecutamos, Construimos, Elaboramos, Practicamos, Manipulamos, Realizamos, Aplicamos. (No abuses de "Vivenciamos").
   - CIERRE: Socializamos, Valoramos, Compartimos, Evaluamos, Reflexionamos, Concluimos.

4. **ACTIVIDADES VIVENCIALES:** Solo actividades prácticas ("Aprender haciendo"). Nada de "Investigar en casa".

FORMATO VISUAL:
- Usa **Negritas** para los títulos.
- Respeta estrictamente la numeración del 1 al 7.
- Usa saltos de línea dobles.
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
    st.title("🛡️ Acceso SUPER DOCENTE 1.0")
    
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
        
    st.title("SUPER DOCENTE 1.0")
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
# --- CARGA INTELIGENTE v7.3 (ANTI-BLOQUEO DE GOOGLE) ---
try:
    df_p_global, df_m_global = cargar_datos_maestros(conn, URL_HOJA)
    
    # Extraer listas para los menús
    LISTA_DOCENTES = sorted(df_p_global['NOMBRE'].dropna().unique().tolist())
    df_mat_global = df_m_global # Disponible para todo el sistema
except Exception as e:
    st.error("🔄 Google está procesando muchas solicitudes. Por favor, espera 10 segundos y presiona el botón 'Limpiar' arriba.")
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
    
 # 2. HERRAMIENTAS DE GESTIÓN (Home)
    st.markdown("### 🛠️ GESTIÓN DOCENTE")
    sel_principal = st.selectbox(
        "Herramientas de Planificación:",
        [
            "(Seleccionar)",
            "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)",    # 1. Lo que usas en el salón
            "📂 Mi Archivo Pedagógico",                   # 2. Tu portafolio
            "🏗️ GESTIÓN DE PROYECTOS Y PLANES",          # 3. Configuración del Proyecto (Nuevo)
            "🧠 PLANIFICADOR INTELIGENTE",                # 4. Crear planes nuevos
            "📜 PLANIFICADOR MINISTERIAL",                # 5. Respaldo legal
            "📊 Registro de Evaluaciones"                 # 6. Al final (por ahora)
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
    # VISTA: CONTROL DE ASISTENCIA (V5.3 - GESTIÓN DE MÉRITOS Y TRABAJO EXTRA)
    # -------------------------------------------------------------------------
    if opcion == "⏱️ Control de Asistencia":
        hora_v = ahora_ve()
        h_actual = hora_v.hour
        h_min = hora_v.minute
        hoy_str = hora_v.strftime("%d/%m/%Y")
        hora_display = hora_v.strftime('%I:%M %p')
        
        st.info(f"ℹ️ Panel de Control | 📅 {hoy_str} | 🕒 {hora_display}")
        
        # Consultar BD
        try:
            df_as = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=0)
            reg = df_as[(df_as['USUARIO'] == st.session_state.u['NOMBRE']) & (df_as['FECHA'] == hoy_str)]
        except: reg = pd.DataFrame()

        # --- CASO A: ENTRADA (Mantiene lógica de 8:15 AM) ---
        if reg.empty:
            status = st.radio("Estado:", ["(Seleccionar)", "✅ Asistí al Plantel", "❌ No Asistí"], index=0)
            
            if status == "✅ Asistí al Plantel":
                es_tarde = h_actual > 8 or (h_actual == 8 and h_min > 15)
                es_madrugada = h_actual < 6
                motivo_e = "Cumplimiento"
                alerta_e = "-"

                if es_madrugada:
                    st.warning("⚠️ Horario de Madrugada")
                    motivo_e = f"MADRUGADA: {st.text_input('Justificación:', placeholder='Ej: Vigilancia...')}"
                elif es_tarde:
                    st.error("🚨 Llegada Tardía (> 8:15 AM)")
                    justif = st.text_input("Motivo del Retraso:", placeholder="Ej: Transporte...")
                    if justif: motivo_e = f"RETRASO: {justif}"; alerta_e = "TARDANZA"
                    else: st.stop()

                f_ent = st.camera_input("Foto Entrada")
                if f_ent and st.button("🚀 Marcar Entrada"):
                    url = subir_a_imgbb(f_ent)
                    if url:
                        registrar_asistencia_v7(st.session_state.u['NOMBRE'], "ASISTENCIA", hora_display, "-", url, "-", motivo_e, alerta_e, 10, "-")
                        st.success("Entrada Registrada."); time.sleep(2); st.session_state.pagina_actual="HOME"; st.rerun()

            elif status == "❌ No Asistí":
                mot = st.text_area("Motivo:")
                if st.button("Enviar") and mot:
                    salud = "salud" in mot.lower() or "médico" in mot.lower()
                    alerta = "⚠️ 48h para justificativo" if salud else "-"
                    registrar_asistencia_v7(st.session_state.u['NOMBRE'], "INASISTENCIA", "-", "-", "-", "-", mot, alerta, 5, "-")
                    st.success("Enviado."); time.sleep(2); st.session_state.pagina_actual="HOME"; st.rerun()

        # --- CASO B: SALIDA (NUEVA LÓGICA DE TRABAJO EXTRA) ---
        elif reg.iloc[0]['HORA_SALIDA'] == "-":
            st.success(f"Entrada: {reg.iloc[0]['HORA_ENTRADA']}")
            st.markdown("### 🚪 Registro de Salida y Méritos")
            
            # 1. CÁLCULO DE PUNTOS BASE
            puntos_totales = 10
            resumen_actividad = ["Jornada Cumplida"]
            alerta_director = "-"
            
            # 2. CHECKBOX: SUPLENCIA (+5 Pts)
            col_sup, col_extra = st.columns(2)
            with col_sup:
                es_heroe = st.checkbox("🦸 Hice Suplencia (+5 pts)")
            
            # 3. CHECKBOX: TRABAJO EXTRA (+3 Pts)
            with col_extra:
                es_extra = st.checkbox("💼 Trabajo Extra (+3 pts)")

            suplencia_a = "-"
            
            # Lógica Suplencia
            if es_heroe:
                try: docentes = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS")['NOMBRE'].unique()
                except: docentes = []
                suplencia_a = st.selectbox("Cubrí a:", [d for d in docentes if d != st.session_state.u['NOMBRE']])
                puntos_totales += 5
                resumen_actividad.append(f"Suplencia: {suplencia_a}")

            # Lógica Trabajo Extra (La Joya de la Corona)
            if es_extra:
                st.info("🕒 **Mérito por Trabajo Extra:** Se enviará a 'SUPER DIRECTOR' para validación en libro.")
                detalle_extra = st.text_input("¿Qué actividad realizaste?", placeholder="Ej: Carteleras, Reunión de Padres, Limpieza profunda...")
                if detalle_extra:
                    puntos_totales += 3
                    resumen_actividad.append(f"EXTRA: {detalle_extra}")
                    alerta_director = "VALIDAR_EXTRA_EN_LIBRO" # Señal para el Director
                else:
                    st.warning("⚠️ Debes describir el trabajo extra para sumar los puntos.")
                    st.stop()

            # 4. LÓGICA DE JUSTIFICACIÓN (Solo si NO es trabajo extra y la hora es rara)
            # Si marcó trabajo extra, se asume que la hora tardía es correcta.
            es_horario_irregular = (h_actual >= 14 or h_actual < 11) and not es_extra
            
            if es_horario_irregular:
                st.warning("⚠️ **Salida fuera de horario habitual (12:30 PM)**")
                justif_salida = st.selectbox("Motivo:", ["Corte Eléctrico", "Sin Datos", "Olvido", "Permiso"])
                hora_real = st.text_input("Hora REAL de salida (Libro):", placeholder="Ej: 12:30 PM")
                resumen_actividad.append(f"INCIDENCIA: {justif_salida} ({hora_real})")
                if not hora_real: st.stop()

            motivo_final = " | ".join(resumen_actividad)
            
            # FOTO Y CIERRE
            st.write(f"🌟 **Puntos a acumular hoy:** {puntos_totales}")
            f_sal = st.camera_input("Foto Salida")
            
            if f_sal and st.button("🏁 Finalizar Jornada"):
                url = subir_a_imgbb(f_sal)
                if url:
                    registrar_asistencia_v7(
                        usuario=st.session_state.u['NOMBRE'], tipo="ASISTENCIA",
                        hora_e="-", hora_s=hora_display, foto_e="-", foto_s=url,
                        motivo=motivo_final, 
                        alerta_ia=alerta_director, # Aquí va la señal para el Director
                        puntos=puntos_totales, 
                        suplencia_a=suplencia_a
                    )
                    st.balloons()
                    st.success(f"✅ Jornada cerrada. ¡Sumaste {puntos_totales} puntos de mérito!")
                    time.sleep(3); st.session_state.pagina_actual="HOME"; st.rerun()
        
        else:
            st.info("✅ Registro completo.")
            if st.button("Volver"): st.session_state.pagina_actual="HOME"; st.rerun()
# -------------------------------------------------------------------------
    # VISTA: PLANIFICADOR INTELIGENTE (PROMPT ORIGINAL BOLIVARIANO + FIX DUPLICADO)
    # -------------------------------------------------------------------------
    elif opcion == "🧠 PLANIFICADOR INTELIGENTE":
        st.markdown("**Generación de Planificación Pedagógica Especializada**")
        
        col1, col2 = st.columns(2)
        with col1:
            rango = st.text_input("Lapso (Fechas):", placeholder="Ej: 26 al 30 de Enero")
        with col2:
            # TU SELECTOR ORIGINAL
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

      # =============================================================================
        # BOTÓN MAESTRO: GENERACIÓN HÍBRIDA (PROYECTO + MANUAL + VALIDACIONES)
        # =============================================================================
        if st.button("🚀 Generar Planificación Estructurada", type="primary"):
            
            # 1. VALIDACIONES DE SEGURIDAD (CONSERVANDO TU LÓGICA ANTIGUA)
            if not rango or not notas:
                st.error("⚠️ Por favor ingrese el Lapso y el Tema.")
            elif is_pei and not perfil_alumno:
                st.error("⚠️ Para P.E.I. debe describir el perfil del alumno.")
            elif modalidad == "Taller de Educación Laboral (T.E.L.)" and not aula_especifica:
                st.error("⚠️ Especifique el área del Taller.")
            else:
                with st.spinner('Conectando con el Cerebro Pedagógico y la Base de Datos...'):
                    
                    # 2. RECUPERAR DATOS DEL PROYECTO (NUEVA LÓGICA)
                    texto_instruccion_proyecto = ""
                    etiqueta_titulo_dinamica = "TÍTULO DE LA ACTIVIDAD" # Default
                    
                    try:
                        # Leemos la hoja de configuración
                        df_p = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=60)
                        # Buscamos al usuario actual
                        user_p = df_p[df_p['USUARIO'] == st.session_state.u['NOMBRE']]
                        
                        if not user_p.empty and str(user_p.iloc[0]['ACTIVO']) == "TRUE":
                            # ¡HAY PROYECTO ACTIVO!
                            fila = user_p.iloc[0]
                            servicio = fila['SERVICIO']
                            pa = fila['NOMBRE_PA']
                            psp = fila['NOMBRE_PSP']
                            fase = fila['FASE_ACTUAL']
                            dias_prod = str(fila['DIAS_PSP'])
                            
                            # Lógica de Etiquetas según Servicio
                            if "Taller" in servicio:
                                etiqueta_titulo_dinamica = "TÍTULO (P.A. o P.S.P.)"
                                texto_instruccion_proyecto = f"""
                                🚨 **MODO TALLER LABORAL ACTIVO:**
                                - P.A. (Aula): "{pa}" | P.S.P. (Taller): "{psp}"
                                - FASE: {fase} | DÍAS PRÁCTICOS: {dias_prod}
                                INSTRUCCIÓN: Si el día es {dias_prod}, planifica PRÁCTICA DEL P.S.P. Si no, planifica TEORÍA DEL P.A. o TEMA MANUAL.
                                """
                            elif "Aula Integrada" in servicio or "U.P.E." in servicio:
                                etiqueta_titulo_dinamica = "LÍNEA DE ACCIÓN"
                                texto_instruccion_proyecto = f"""
                                🚨 **MODO ATENCIÓN ESPECIALIZADA:**
                                - LÍNEA: "{pa}" | FASE: {fase}
                                INSTRUCCIÓN: Centra todo en esta línea de acción correctiva.
                                """
                            else: # Inicial / IEEB
                                etiqueta_titulo_dinamica = "TÍTULO LÚDICO DEL PROYECTO"
                                texto_instruccion_proyecto = f"""
                                🚨 **MODO PROYECTO DE APRENDIZAJE:**
                                - PROYECTO: "{pa}" | MOMENTO: {fase}
                                INSTRUCCIÓN: Planifica en base a este proyecto lúdico.
                                """
                        else:
                            # MODO MANUAL PURO
                            texto_instruccion_proyecto = "NO HAY PROYECTO ACTIVO. Planifica EXCLUSIVAMENTE basado en el TEMA MANUAL."
                            etiqueta_titulo_dinamica = "TÍTULO DE LA CLASE"

                    except Exception as e:
                        texto_instruccion_proyecto = "Planifica basado en TEMA MANUAL (Sin conexión a proyectos)."

                    # 3. CONSTRUCCIÓN DEL PROMPT (CONSERVANDO TUS REGLAS DE FORMATO)
                    tipo_plan = "Individualizado (P.E.I.)" if is_pei else "Grupal"
                    perfil_txt = f"PERFIL DEL ALUMNO: {perfil_alumno}" if is_pei else ""
                    contexto_aula = f" del área de {aula_especifica}" if aula_especifica else ""
                    
                    prompt = f"""
                    ERES UN EXPERTO EN PLANIFICACIÓN EDUCATIVA VENEZOLANA.
                    
                    CONTEXTO: {modalidad}{contexto_aula}.
                    TEMA MANUAL: {notas}.
                    TIPO: {tipo_plan} {perfil_txt}
                    
                    {texto_instruccion_proyecto}
                    
                    🚨 **REGLAS OBLIGATORIAS DE FORMATO Y PEDAGOGÍA (TU ESTÁNDAR DE CALIDAD):**
                    
                    1. **{etiqueta_titulo_dinamica}:** Escribe SOLO el nombre corto.
                    2. **COMPETENCIA TÉCNICA:** Estructura OBLIGATORIA: Verbo Infinitivo + Contenido + Condición.
                    3. **ESTRATEGIAS:** Usa SOLO TÉCNICAS REALES (Lluvia de ideas, Modelado docente, Práctica guiada, Trabajo cooperativo). NO describas la actividad aquí.
                    
                    ESTRUCTURA DE SALIDA (Doble espacio, Lunes a Viernes):

                    ### [DÍA Y FECHA]
                    
                    **1. {etiqueta_titulo_dinamica}:** [Nombre]
                    
                    **2. COMPETENCIA TÉCNICA:** [Redacción Experta]
                    
                    **3. EXPLORACIÓN (Inicio):** [Dinámica motivadora / Revisión de conocimientos]
                    
                    **4. DESARROLLO (Proceso):** [Actividad central. Si es día de Taller Práctico, detalla el uso de herramientas con el Instructor. Si es Aula, detalla la mediación.]
                    
                    **5. REFLEXIÓN (Cierre):** [Socialización / Valoración del trabajo]
                    
                    **6. ESTRATEGIAS:** [Listado de técnicas]
                    
                    **7. RECURSOS:** [Materiales físicos y de provecho]
                    
                    ---------------------------------------------------
                    Genera la planificación para el lapso: {rango}.
                    """
                    
                    # 4. GENERACIÓN
                    st.session_state.plan_actual = generar_respuesta([
                        {"role":"system","content":INSTRUCCIONES_TECNICAS}, 
                        {"role":"user","content":prompt}
                    ], 0.6)
                    st.rerun()
  # --- VISUALIZACIÓN Y GUARDADO (ESTO DEBE APARECER UNA SOLA VEZ) ---
    if st.session_state.plan_actual and opcion == "🧠 PLANIFICADOR INTELIGENTE":
        st.divider()
        st.success("✅ **Planificación Generada**")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        col_s, col_d = st.columns([2, 1])
        with col_s:
            # HE CAMBIADO LA KEY AQUI A "btn_guardar_final" PARA QUE NO DE ERROR
            if st.button("💾 Guardar en Archivo", key="btn_guardar_final"):
                try:
                    df = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                    t = st.session_state.get('temp_tema', 'Planificación')
                    
                    row = pd.DataFrame([{
                        "FECHA": ahora_ve().strftime("%d/%m/%Y"), 
                        "USUARIO": st.session_state.u['NOMBRE'], 
                        "TEMA": t[:50], 
                        "CONTENIDO": st.session_state.plan_actual, 
                        "ESTADO": "GUARDADO", 
                        "HORA_INICIO": "--", "HORA_FIN": "--"
                    }])
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df, row], ignore_index=True))
                    st.success("Guardado correctamente.")
                    time.sleep(2)
                    st.session_state.pagina_actual = "📂 Mi Archivo Pedagógico"
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
        
        with col_d:
            # HE CAMBIADO LA KEY AQUI TAMBIÉN A "btn_descartar_final"
            if st.button("🗑️ Descartar", key="btn_descartar_final"):
                st.session_state.plan_actual = ""
                st.rerun()
# -------------------------------------------------------------------------
    # VISTA: AULA VIRTUAL (v11.2 - SINCRONIZACIÓN DE NOMBRES)
    # -------------------------------------------------------------------------
    elif opcion == "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)":
        st.info("💡 **Centro de Operaciones:** Gestión integral de la clase.")
        
        # 1. CONTEXTO DE TRABAJO
        st.markdown("### ⚙️ Contexto de la Clase")
        es_suplencia = st.checkbox("🦸 **Activar Modo Suplencia**", key="av_suplencia_v11")
        
        if es_suplencia:
            titular = st.selectbox("Seleccione Docente Titular:", LISTA_DOCENTES, key="av_titular_v11")
            st.warning(f"Modo Suplencia: Usando planificación de **{titular}**")
        else:
            titular = st.session_state.u['NOMBRE']
            st.success("Trabajando con tu planificación y alumnos.")

        # 2. BUSCAR PLAN ACTIVO
        pa = obtener_plan_activa_usuario(titular)
        
        if not pa:
            st.error(f"🚨 {titular} no tiene un plan activo.")
            st.info("Activa un plan en 'Mi Archivo Pedagógico' para este docente.")
            st.stop()

        # 3. CREACIÓN DE PESTAÑAS (Nombres estandarizados)
        tab1, tab2, tab3 = st.tabs(["🚀 Ejecución y PEI", "📝 Evaluación Estudiantil", "🏁 Cierre y Méritos"])

        # --- PESTAÑA 1: EJECUCIÓN ---
        with tab1:
            dias_es = {"Monday":"Lunes", "Tuesday":"Martes", "Wednesday":"Miércoles", "Thursday":"Jueves", "Friday":"Viernes", "Saturday":"Sábado", "Sunday":"Domingo"}
            dia_hoy_nombre = dias_es.get(ahora_ve().strftime("%A"))
            
            clase_dia = extraer_actividad_del_dia(pa["CONTENIDO_PLAN"], dia_hoy_nombre)
            if clase_dia is None:
                st.warning(f"No hay actividad programada para hoy {dia_hoy_nombre}.")
                dia_m = st.selectbox("Seleccione día a ejecutar:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], key="av_manual_v11")
                clase_de_hoy = extraer_actividad_del_dia(pa["CONTENIDO_PLAN"], dia_m)
            else:
                clase_de_hoy = clase_dia

            st.subheader("📖 Guía de la Actividad")
            st.markdown(f'<div class="plan-box">{clase_de_hoy}</div>', unsafe_allow_html=True)
            st.session_state.actividad_ejecutada_hoy = clase_de_hoy.split('\n')[0].replace('#','').strip()

            st.divider()
            st.markdown("### 🧩 Adaptación P.E.I. Express")
            alums = df_mat_global[df_mat_global['DOCENTE_TITULAR'] == titular]['NOMBRE_ALUMNO'].tolist()
            c1, c2 = st.columns(2)
            with c1: al_a = st.selectbox("Alumno:", ["(Seleccionar)"] + sorted(alums), key="av_pei_al_v11")
            with c2: ctx_a = st.text_input("Situación:", placeholder="Ej: Inquieto...", key="av_pei_ctx_v11")
            if st.button("💡 Estrategia IA", key="btn_av_ia_v11"):
                if al_a != "(Seleccionar)":
                    datos_al = df_mat_global[df_mat_global['NOMBRE_ALUMNO'] == al_a]
                    diag = datos_al['DIAGNOSTICO'].iloc[0] if not datos_al.empty else "N/A"
                    p_pei = f"PLAN: {clase_de_hoy}. ALUMNO: {al_a} ({diag}). CRISIS: {ctx_a}. Adapta ya."
                    st.markdown(f'<div class="eval-box">{generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":p_pei}], 0.5)}</div>', unsafe_allow_html=True)

            st.divider()
            if st.session_state.av_foto1 is None:
                st.subheader("1. Evidencia de Inicio")
                f1 = st.camera_input("Capturar proceso", key="av_cam1_v11")
                if f1 and st.button("📤 Guardar Inicio", key="btn_save_f1_v11"):
                    u1 = subir_a_imgbb(f1)
                    if u1: st.session_state.av_foto1 = u1; st.rerun()
            else:
                st.image(st.session_state.av_foto1, width=200, caption="Inicio cargado")
                if st.button("♻️ Repetir Foto 1", key="reset_f1_v11"): st.session_state.av_foto1 = None; st.rerun()

        # --- PESTAÑA 2: EVALUACIÓN ---
        with tab2:
            st.subheader("📝 Carga de Notas Individuales")
            if not alums:
                st.warning("No hay alumnos para este titular.")
            else:
                e_sel = st.selectbox("Seleccione Estudiante:", sorted(alums), key="av_eval_al_v11")
                if st.button("🔍 Cargar Actividad de Hoy", key="btn_load_act_v11"):
                    st.session_state.actividad_detectada = st.session_state.actividad_ejecutada_hoy
                
                a_eval = st.text_input("Actividad:", value=st.session_state.actividad_detectada, key="av_eval_act_v11")
                o_eval = st.text_area(f"Observación de {e_sel}:", key="av_eval_obs_v11")
                
                if st.button("⚡ Guardar Evaluación en Expediente", key="btn_save_ev_v11"):
                    if o_eval:
                        with st.spinner("Procesando nota técnica..."):
                            p_ev = f"Alumno: {e_sel}. Actividad: {a_eval}. Obs: {o_eval}. Plan: {clase_de_hoy[:500]}."
                            res_ev = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":p_ev}], 0.5)
                            df_ev = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                            nueva_n = pd.DataFrame([{"FECHA": ahora_ve().strftime("%d/%m/%Y"), "USUARIO": st.session_state.u['NOMBRE'], "DOCENTE_TITULAR": titular, "ESTUDIANTE": e_sel, "ACTIVIDAD": a_eval, "ANECDOTA": o_eval, "EVALUACION_IA": res_ev, "PLANIFICACION_ACTIVA": pa['RANGO']}])
                            conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, nueva_n], ignore_index=True))
                            st.success(f"✅ Nota de {e_sel} guardada."); time.sleep(1)
                    else: st.error("Escribe una observación.")

        # --- PESTAÑA 3: CIERRE ---
        with tab3:
            st.subheader("🏁 Cierre de Jornada")
            if st.session_state.av_foto1 is None:
                st.warning("Captura la foto de inicio en la pestaña 'Ejecución y PEI'.")
            elif st.session_state.av_foto2 is None:
                st.subheader("2. Evidencia de Culminación")
                f2 = st.camera_input("Capturar cierre", key="av_cam2_v11")
                if f2 and st.button("📤 Guardar Cierre", key="btn_save_f2_v11"):
                    u2 = subir_a_imgbb(f2)
                    if u2: st.session_state.av_foto2 = u2; st.rerun()
            else:
                st.image(st.session_state.av_foto2, width=200, caption="Cierre cargado")
                st.session_state.av_resumen = st.text_area("Logros del día:", value=st.session_state.av_resumen, key="av_res_v11")
                if st.button("🚀 FINALIZAR Y ENVIAR REPORTE", type="primary", key="btn_finish_v11"):
                    if st.session_state.av_resumen:
                        df_ej = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                        nueva_f = pd.DataFrame([{"FECHA": ahora_ve().strftime("%d/%m/%Y"), "USUARIO": st.session_state.u['NOMBRE'], "DOCENTE_TITULAR": titular, "ACTIVIDAD_TITULO": st.session_state.actividad_ejecutada_hoy, "EVIDENCIA_FOTO": f"{st.session_state.av_foto1} | {st.session_state.av_foto2}", "RESUMEN_LOGROS": st.session_state.av_resumen, "ESTADO": "CULMINADA", "PUNTOS": 5}])
                        conn.update(spreadsheet=URL_HOJA, worksheet="EJECUCION", data=pd.concat([df_ej, nueva_f], ignore_index=True))
                        st.session_state.av_foto1 = None; st.session_state.av_foto2 = None; st.session_state.av_resumen = ""
                        st.balloons(); st.success("✅ Actividad culminada."); time.sleep(3); st.session_state.pagina_actual = "HOME"; st.rerun()
                    else: st.error("Escribe el resumen antes de finalizar.")
# -------------------------------------------------------------------------
    # VISTA: GESTIÓN DE PROYECTOS Y PLANES (MÓDULO INTELIGENTE 7 COLUMNAS)
    # -------------------------------------------------------------------------
    elif opcion == "🏗️ GESTIÓN DE PROYECTOS Y PLANES":
        st.header("🏗️ Configuración de Proyectos y Planes")
        st.markdown("Defina su hoja de ruta. La IA adaptará las planificaciones según su **Servicio** y la **Fase** del proyecto.")

        # 1. LEER LA HOJA DE GOOGLE SHEETS (CONFIG_PROYECTO)
        try:
            # Leemos sin caché (ttl=0) para ver cambios al instante
            df_proy = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=0)
            # Filtramos solo la fila de ESTE usuario (Privacidad)
            mi_proy = df_proy[df_proy['USUARIO'] == st.session_state.u['NOMBRE']]
        except Exception as e:
            st.error(f"Error de conexión con la Base de Datos: {e}")
            mi_proy = pd.DataFrame()

        # 2. CARGAR VALORES GUARDADOS (O dejar en blanco si es nuevo)
        # Valores por defecto
        d_servicio = "Taller de Educación Laboral (T.E.L.)" # Default
        d_pa = ""
        d_psp = ""
        d_fase = ""
        d_dias = []
        d_activo = False

        if not mi_proy.empty:
            fila = mi_proy.iloc[0]
            # Recuperamos datos de las columnas
            d_servicio = fila['SERVICIO'] if pd.notna(fila['SERVICIO']) and fila['SERVICIO'] != "" else d_servicio
            d_pa = fila['NOMBRE_PA'] if pd.notna(fila['NOMBRE_PA']) else ""
            d_psp = fila['NOMBRE_PSP'] if pd.notna(fila['NOMBRE_PSP']) else ""
            d_fase = fila['FASE_ACTUAL'] if pd.notna(fila['FASE_ACTUAL']) else ""
            d_dias = str(fila['DIAS_PSP']).split(",") if pd.notna(fila['DIAS_PSP']) and fila['DIAS_PSP'] != "" else []
            d_activo = True if str(fila['ACTIVO']) == "TRUE" else False

        # 3. EL FORMULARIO INTELIGENTE
        with st.form("form_proyecto_maestro"):
            
            # --- SECCIÓN A: IDENTIDAD DEL SERVICIO ---
            st.subheader("1. Identidad del Servicio")
            servicio_seleccionado = st.selectbox(
                "¿A qué Modalidad o Servicio pertenece usted?",
                [
                    "Taller de Educación Laboral (T.E.L.)",
                    "Educación Inicial / I.E.E. (Escuela)",
                    "Aula Integrada / U.P.E. / C.A.I.P.A."
                ],
                index=0 if "Taller" in d_servicio else (1 if "Inicial" in d_servicio else 2),
                help="Esto define si trabajaremos con Proyectos Productivos o Planes de Atención."
            )

            st.divider()

            # --- SECCIÓN B: CONTENIDO DEL PROYECTO ---
            st.subheader("2. Datos del Plan")
            
            # LÓGICA CONDICIONAL VISUAL
            es_taller = "Taller" in servicio_seleccionado
            
            # CAMPO 1: EL PEDAGÓGICO (Para todos, pero cambia el nombre)
            label_pa = "Nombre del Proyecto de Aprendizaje (P.A.):"
            help_pa = "Tema generador pedagógico, valores o habilidades blandas."
            
            if "Aula Integrada" in servicio_seleccionado:
                label_pa = "Nombre de la Línea de Acción / P.A.I.:"
                help_pa = "Enfoque remedial o plan de atención específico."
            
            nombre_pa = st.text_input(label_pa, value=d_pa, help=help_pa, placeholder="Ej: Fortaleciendo la lectura / Conociendo mi entorno")

            # CAMPO 2: EL PRODUCTIVO (Solo aparece si es Taller)
            nombre_psp = ""
            dias_psp = []
            
            if es_taller:
                st.info("🛠️ **Modo Taller Activado:** Complete los datos del Proyecto Productivo.")
                nombre_psp = st.text_input("Nombre del Proyecto Socio-Productivo (P.S.P.):", 
                                          value=d_psp if d_psp != "N/A" else "",
                                          placeholder="Ej: Vivero Ornamental / Panadería Escolar")
                
                dias_psp = st.multiselect("Días de Práctica de Taller (Con Instructor):", 
                                         ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
                                         default=[d.strip() for d in d_dias if d.strip()])
            else:
                # Si no es taller, guardamos "N/A" internamente
                nombre_psp = "N/A" 

            # CAMPO 3: FASE O MOMENTO (Para todos)
            st.markdown("<br>", unsafe_allow_html=True)
            fase_actual = st.text_area("Fase Actual / Momento:", 
                                      value=d_fase,
                                      help="Dígale a la IA en qué etapa están para que ajuste la dificultad.", 
                                      placeholder="Ej: Estamos iniciando, solo teoría. / Estamos en plena producción para la venta.")

            st.divider()

            # --- SECCIÓN C: ACTIVACIÓN ---
            col_act, col_info = st.columns([1, 2])
            with col_act:
                activo = st.toggle("✅ ACTIVAR PROYECTO", value=d_activo)
            with col_info:
                if activo:
                    st.success("La IA priorizará este proyecto sobre el tema manual.")
                else:
                    st.warning("Proyecto en PAUSA. La IA usará solo el tema manual semanal.")

            # BOTÓN DE GUARDAR
            if st.form_submit_button("💾 Guardar Configuración"):
                
                # Preparar datos para las 7 COLUMNAS
                str_dias = ",".join(dias_psp) if es_taller else ""
                str_activo = "TRUE" if activo else "FALSE"
                
                # Limpieza de datos viejos
                df_clean = df_proy[df_proy['USUARIO'] != st.session_state.u['NOMBRE']]
                
                # Crear el nuevo registro (7 COLUMNAS EXACTAS)
                nuevo_reg = pd.DataFrame([{
                    "USUARIO": st.session_state.u['NOMBRE'],
                    "SERVICIO": servicio_seleccionado,      # <--- La columna nueva vital
                    "NOMBRE_PA": nombre_pa,
                    "NOMBRE_PSP": nombre_psp,
                    "FASE_ACTUAL": fase_actual,
                    "DIAS_PSP": str_dias,
                    "ACTIVO": str_activo
                }])
                
                # Guardar en Google Sheets
                try:
                    conn.update(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", data=pd.concat([df_clean, nuevo_reg], ignore_index=True))
                    st.success("✅ ¡Configuración actualizada! Ahora la IA conoce su contexto.")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
   # -------------------------------------------------------------------------
    # VISTA: REGISTRO DE EVALUACIONES (v7.0 EXPEDIENTE COMPARTIDO)
    # -------------------------------------------------------------------------
    elif opcion == "📊 Registro de Evaluaciones":
        try:
            df_historial = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
            
            # FILTRO CRÍTICO: El docente solo ve los alumnos de los que es TITULAR
            mis_alumnos_data = df_historial[df_historial['DOCENTE_TITULAR'] == st.session_state.u['NOMBRE']]
            
            if mis_alumnos_data.empty:
                st.info("Aún no hay evaluaciones registradas para tus alumnos.")
            else:
                lista_alumnos_hist = sorted(mis_alumnos_data['ESTUDIANTE'].unique())
                alumno_sel = st.selectbox("Seleccione Alumno para ver su historial:", lista_alumnos_hist)
                
                registros_alumno = mis_alumnos_data[mis_alumnos_data['ESTUDIANTE'] == alumno_sel]
                
                st.metric("Total de Evaluaciones", len(registros_alumno))
                st.markdown("---")
                
                # Mostrar registros del más reciente al más antiguo
                for _, fila in registros_alumno.iloc[::-1].iterrows():
                    with st.expander(f"📅 {fila['FECHA']} | Evalúa: {fila['USUARIO']}"):
                        if fila['USUARIO'] != st.session_state.u['NOMBRE']:
                            st.caption(f"ℹ️ Esta nota fue cargada por un docente suplente ({fila['USUARIO']})")
                        st.write(fila['EVALUACION_IA'])
                        
                if st.button("📝 Generar Informe de Progreso"):
                    with st.spinner("Consolidando información..."):
                        historico_txt = registros_alumno['EVALUACION_IA'].str.cat(sep='\n\n')
                        informe = generar_respuesta([{"role":"user","content":f"Genera un informe técnico de progreso para {alumno_sel} basado en estas evaluaciones: {historico_txt}"}])
                        st.markdown(f'<div class="plan-box">{informe}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error al cargar el historial: {e}")

   # -------------------------------------------------------------------------
    # VISTA: MI ARCHIVO PEDAGÓGICO (v10.1 - INTEGRACIÓN TOTAL DE PLANES Y LOGROS)
    # -------------------------------------------------------------------------
    elif opcion == "📂 Mi Archivo Pedagógico":
        st.markdown("### 📂 Mi Archivo Pedagógico Digital")
        
        # Cargamos todas las bases de datos necesarias para el cruce de información
        try:
            df_total_planes = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
            df_ejecucion = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
            df_evaluaciones = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
            
            # Creamos las dos pestañas para separar Futuro (Planes) de Pasado (Logros)
            tab_archivo, tab_consolidados = st.tabs(["📝 Mis Planificaciones", "🏆 Actividades Consolidadas"])

            # --- PESTAÑA 1: GESTIÓN DE ARCHIVO Y PLANIFICACIONES (TU LÓGICA v7.2) ---
            with tab_archivo:
                # 1. Selector de contexto (¿Mi archivo o el de un colega?) - PRESERVADO
                modo_suplencia_arch = st.checkbox("🦸 **Activar Modo Suplencia** (Gestionar archivo de un colega)", key="check_supl_v72")
                
                if modo_suplencia_arch:
                    usuario_a_consultar = st.selectbox("Seleccione Docente Ausente:", LISTA_DOCENTES, key="sel_doc_v72")
                    st.warning(f"Gestionando archivo de: **{usuario_a_consultar}**")
                else:
                    usuario_a_consultar = st.session_state.u['NOMBRE']
                    st.info("Viendo tus planificaciones guardadas.")

                # 2. Mostrar estado actual del plan seleccionado - PRESERVADO
                pa = obtener_plan_activa_usuario(usuario_a_consultar)
                if pa:
                    st.success(f"📌 **PLAN ACTIVO de {usuario_a_consultar}:** {pa['RANGO']}")
                    if st.button(f"Desactivar Plan de {usuario_a_consultar}", key="btn_des_v72"):
                        desactivar_plan_activa(usuario_a_consultar)
                        st.rerun()
                else:
                    st.warning(f"⚠️ {usuario_a_consultar} no tiene ninguna planificación activa ahora.")

                st.divider()

                # 3. Mostrar historial de planes guardados - PRESERVADO
                mis_p = df_total_planes[df_total_planes['USUARIO'] == usuario_a_consultar]
                
                if mis_p.empty:
                    st.warning(f"No se encontraron planes guardados para {usuario_a_consultar}.")
                else:
                    for i, fila in mis_p.iloc[::-1].iterrows():
                        es_este_activo = (pa['CONTENIDO_PLAN'] == fila['CONTENIDO']) if pa else False
                        titulo_expander = f"{'⭐ ACTIVO | ' if es_este_activo else ''}📅 {fila['FECHA']} | {str(fila['TEMA'])[:35]}..."
                        
                        with st.expander(titulo_expander):
                            st.markdown(f'<div class="plan-box">{fila["CONTENIDO"]}</div>', unsafe_allow_html=True)
                            
                            col_btns = st.columns(2)
                            if not es_este_activo:
                                if col_btns[0].button(f"📌 Activar para {usuario_a_consultar}", key=f"act_btn_{i}"):
                                    establecer_plan_activa(usuario_a_consultar, str(i), fila['CONTENIDO'], fila['FECHA'], "Taller/Aula")
                                    st.success("Plan activado."); time.sleep(1); st.rerun()
                            
                            # Seguridad: Solo el dueño puede borrar sus planes - PRESERVADO
                            if not modo_suplencia_arch:
                                if col_btns[1].button(f"🗑️ Borrar mi plan", key=f"del_btn_{i}"):
                                    df_actualizado = df_total_planes.drop(i)
                                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_actualizado)
                                    st.rerun()

            # --- PESTAÑA 2: ACTIVIDADES CONSOLIDADAS (LA NUEVA EVOLUCIÓN v10.1) ---
            with tab_consolidados:
                st.write("### ✅ Registro de Cumplimiento y Evidencias")
                # Aquí siempre mostramos lo del docente logueado para sus méritos
                mis_logros = df_ejecucion[df_ejecucion['USUARIO'] == st.session_state.u['NOMBRE']]
                
                if mis_logros.empty:
                    st.info("Aún no tienes actividades consolidadas. Ve al 'Aula Virtual' para culminar tu primera clase.")
                else:
                    # Métrica de cumplimiento semanal
                    total_sem = len(mis_logros)
                    st.metric("Actividades de la Semana", f"{total_sem} de 5")

                    for _, logro in mis_logros.iloc[::-1].iterrows():
                        with st.expander(f"✅ LOGRO: {logro['FECHA']} | {logro['ACTIVIDAD_TITULO']}"):
                            # 1. Fotos con Botones de Descarga - v10.1
                            fotos = str(logro['EVIDENCIA_FOTO']).split('|')
                            c1, c2 = st.columns(2)
                            
                            with c1:
                                if len(fotos) > 0 and fotos[0].strip() != "-":
                                    u1 = fotos[0].strip()
                                    st.image(u1, caption="Proceso", use_container_width=True)
                                    try:
                                        st.download_button("💾 Descargar Foto 1", requests.get(u1).content, f"Proceso_{logro['FECHA']}.jpg", "image/jpeg", key=f"dl1_{logro['FECHA']}_{random.randint(0,999)}")
                                    except: st.caption("Error en descarga")
                            
                            with c2:
                                if len(fotos) > 1 and fotos[1].strip() != "-":
                                    u2 = fotos[1].strip()
                                    st.image(u2, caption="Culminación", use_container_width=True)
                                    try:
                                        st.download_button("💾 Descargar Foto 2", requests.get(u2).content, f"Cierre_{logro['FECHA']}.jpg", "image/jpeg", key=f"dl2_{logro['FECHA']}_{random.randint(0,999)}")
                                    except: st.caption("Error en descarga")

                            st.info(f"**Experiencia Docente:** {logro['RESUMEN_LOGROS']}")
                            
                            # 2. Botón de Análisis de IA - PRESERVADO
                            if st.button("🧠 Ver Análisis de Logro (IA)", key=f"ia_{logro['FECHA']}_{random.randint(0,999)}"):
                                p_ia = f"Analiza esta actividad pedagógica: {logro['ACTIVIDAD_TITULO']}. Logros: {logro['RESUMEN_LOGROS']}. Valora el impacto en Educación Especial."
                                st.markdown(f'<div class="eval-box">{generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":p_ia}], 0.4)}</div>', unsafe_allow_html=True)

                            # 3. Cruce con Estudiantes - PRESERVADO
                            st.write("**🧒 Alumnos evaluados en esta actividad:**")
                            ev_dia = df_evaluaciones[(df_evaluaciones['FECHA'] == logro['FECHA']) & (df_evaluaciones['USUARIO'] == st.session_state.u['NOMBRE'])]
                            if ev_dia.empty: st.caption("Sin evaluaciones individuales.")
                            else:
                                for _, e in ev_dia.iterrows():
                                    st.markdown(f"- **{e['ESTUDIANTE']}**: {e['EVALUACION_IA'][:100]}...")

        except Exception as e:
            st.error(f"Error técnico en el archivo: {e}")

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
st.caption("SUPER DOCENTE 1.0 | Desarrollado para EDUCACION ESPECIAL por Bachiller Luis Atencio")
