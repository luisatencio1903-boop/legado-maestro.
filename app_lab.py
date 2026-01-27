# ============================================================================
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
    
# Memoria para el AULA VIRTUAL (Persistencia entre navegaciones)
if 'av_foto1' not in st.session_state: st.session_state.av_foto1 = None
if 'av_foto2' not in st.session_state: st.session_state.av_foto2 = None
if 'av_foto3' not in st.session_state: st.session_state.av_foto3 = None # <--- NUEVA FOTO (CIERRE)
if 'av_resumen' not in st.session_state: st.session_state.av_resumen = ""
# =============================================================================
# 6. LÓGICA DE NEGOCIO (BACKEND ORIGINAL COMPLETO)
# =============================================================================

# --- 6.1 Funciones de Planificación Activa ---

def obtener_plan_activa_usuario(usuario_nombre):
    """
    Obtiene la planificación activa actual del usuario desde la nube.
    MODO ECO ACTIVADO: Consulta cada 60 segundos, no cada 5.
    """
    try:
        # CAMBIO AQUÍ: ttl=60 (Antes era 5)
        df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=60)
        
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
    
    # Encabezado de Acciones Rápidas (3 Botones: Actualizar, Limpiar, Salir)
    col_update, col_clean, col_logout = st.columns([1.2, 1, 1])
    
    # 1. BOTÓN ACTUALIZAR (CONEXIÓN NUBE)
    with col_update:
        if st.button("♻️ ACTUALIZAR", help="Forzar descarga de alumnos y planes nuevos de Google Sheets"):
            # Esto borra la memoria caché de la Base de Datos
            st.cache_data.clear()
            st.toast("☁️ Conectando con Google Sheets...", icon="🔄")
            time.sleep(1)
            st.success("¡Sistema Sincronizado!")
            time.sleep(1)
            st.rerun()

    # 2. BOTÓN LIMPIAR (MEMORIA LOCAL)
    with col_clean:
        if st.button("🧹 LIMPIAR", help="Borrar texto en pantalla y reiniciar variables temporales"):
            # Esto solo borra lo que estás haciendo en el momento (No la base de datos)
            st.session_state.plan_actual = ""
            st.session_state.actividad_detectada = ""
            st.session_state.eval_resultado = ""
            st.session_state.temp_propuesta_ia = ""
            st.toast("✨ Mesa de trabajo limpia")
            time.sleep(0.5)
            st.rerun()
            
    # 3. BOTÓN SALIR
    with col_logout:
        if st.button("🔒 SALIR", type="primary", help="Cerrar sesión segura"):
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
            "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)",
            "📂 Mi Archivo Pedagógico",
            "🧠 PLANIFICADOR INTELIGENTE",
            "📜 PLANIFICADOR MINISTERIAL",
            "🏗️ FÁBRICA DE PENSUMS",  # <--- NUEVO MÓDULO AQUÍ
            "🏗️ GESTIÓN DE PROYECTOS Y PLANES"
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
                # Definimos las variables de tiempo
                es_tarde = h_actual > 8 or (h_actual == 8 and h_min > 15)
                es_madrugada = h_actual < 6
                motivo_e = "Cumplimiento"
                alerta_e = "-"

                # 1. CASO MADRUGADA
                if es_madrugada:
                    st.warning("⚠️ Horario de Madrugada")
                    motivo_e = f"MADRUGADA: {st.text_input('Justificación:', placeholder='Ej: Vigilancia...')}"
                
                # 2. CASO TARDANZA (Aquí empieza el bloque nuevo corregido)
                elif es_tarde:
                    st.error("🚨 Llegada Tardía (> 8:15 AM)")
                    
                    # LISTA DESPLEGABLE ESTANDARIZADA
                    motivo_lista = [
                        "Seleccione motivo...",
                        "⛈️ Condiciones Climáticas (Lluvia/Vía)",
                        "🔌 Falla Eléctrica / Sin Señal",
                        "🚌 Transporte / Combustible",
                        "🤝 Diligencia Institucional",
                        "🏥 Salud / Cita Médica",
                        "👨‍👩‍👧‍👦 Asunto Familiar de Fuerza Mayor",
                        "🕒 Otro"
                    ]
                    justif_sel = st.selectbox("Motivo del Retraso:", motivo_lista)
                    
                    if justif_sel != "Seleccione motivo...":
                        if justif_sel == "🕒 Otro":
                            texto_extra = st.text_input("Especifique:")
                            motivo_e = f"RETRASO: {texto_extra}" if texto_extra else None
                        else:
                            motivo_e = f"RETRASO: {justif_sel}"
                        
                        if motivo_e:
                            alerta_e = "TARDANZA"
                            if "Salud" in justif_sel:
                                st.warning("⚠️ **Recordatorio:** Debes consignar el justificativo médico en Dirección (48h).")
                        else:
                            st.stop()
                    else:
                        st.stop()

                # 3. FOTO DE ENTRADA (Siempre visible si asistió)
                f_ent = st.camera_input("Foto Entrada")
                if f_ent and st.button("🚀 Marcar Entrada"):
                    url = subir_a_imgbb(f_ent)
                    if url:
                        registrar_asistencia_v7(st.session_state.u['NOMBRE'], "ASISTENCIA", hora_display, "-", url, "-", motivo_e, alerta_e, 10, "-")
                        st.success("Entrada Registrada."); time.sleep(2); st.session_state.pagina_actual="HOME"; st.rerun()

            # --- SECCIÓN DE INASISTENCIA (MEJORADA CON LISTA) ---
            elif status == "❌ No Asistí":
                st.markdown("### Reporte de Inasistencia")
                motivo_falta = st.selectbox("Causa de la falta:", [
                    "🏥 Salud (Reposo/Cita)",
                    "🚗 Falla Mecánica / Transporte",
                    "📄 Diligencia Administrativa",
                    "🛑 Paro / Protesta",
                    "🏠 Calamidad Doméstica",
                    "👤 Asuntos Personales"
                ])
                
                detalles_falta = st.text_input("Detalles adicionales (Opcional):")
                mot_final = f"{motivo_falta} - {detalles_falta}"
                
                # ALERTA INTELIGENTE
                alerta = "-"
                if "Salud" in motivo_falta:
                    alerta = "⚠️ REPOSO: Entregar justificativo"
                    st.info("ℹ️ El sistema ha marcado esto como incidencia de Salud. Recuerda los soportes.")

                if st.button("Enviar Reporte de Falta"):
                    registrar_asistencia_v7(st.session_state.u['NOMBRE'], "INASISTENCIA", "-", "-", "-", "-", mot_final, alerta, 0, "-") # 0 Puntos por falta
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
    # VISTA: PLANIFICADOR INTELIGENTE (ESTRATEGIAS DIRECTAS + CNB)
    # -------------------------------------------------------------------------
    elif opcion == "🧠 PLANIFICADOR INTELIGENTE":
        st.markdown("**Generación de Planificación Pedagógica Especializada**")
        
        # 1. INTERFAZ DE USUARIO (INTACTA)
        col1, col2 = st.columns(2)
        with col1:
            rango = st.text_input("Lapso (Fechas):", placeholder="Ej: 26 al 30 de Enero")
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

        # =============================================================================
        # BOTÓN MAESTRO: ESTRATEGIAS LIMPIAS
        # =============================================================================
        if st.button("🚀 Generar Planificación Estructurada", type="primary"):
            
            # VALIDACIONES
            if not rango or not notas:
                st.error("⚠️ Por favor ingrese el Lapso y el Tema.")
            elif is_pei and not perfil_alumno:
                st.error("⚠️ Para P.E.I. debe describir el perfil del alumno.")
            elif modalidad == "Taller de Educación Laboral (T.E.L.)" and not aula_especifica:
                st.error("⚠️ Especifique el área del Taller.")
            else:
                with st.spinner('Super Docente 1.0 alineando estrategias y léxico...'):
                    
                    # A. TONO (INTACTO)
                    vocabulario_sugerido = ""
                    tono_redaccion = ""
                    if "Inicial" in modalidad:
                        tono_redaccion = "AFECTIVO Y LÚDICO."
                    elif "Taller" in modalidad:
                        tono_redaccion = "PRODUCTIVO Y EMANCIPADOR."
                    elif "Autismo" in modalidad:
                        tono_redaccion = "ESTRUCTURADO Y VISUAL."
                    else: 
                        tono_redaccion = "PSICO-EDUCATIVO."

                    # B. PROYECTOS (INTACTO)
                    texto_instruccion_proyecto = ""
                    try:
                        df_p = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=0)
                        user_p = df_p[df_p['USUARIO'] == st.session_state.u['NOMBRE']]
                        if not user_p.empty:
                            fila = user_p.iloc[0]
                            pa = fila.get('TITULO_PA', 'Valores')
                            psp = fila.get('TITULO_PSP', 'Productivo')
                            dias_pa = str(fila.get('DIAS_PA', ''))
                            dias_psp = str(fila.get('DIAS_PSP', ''))
                            
                            texto_instruccion_proyecto = f"""
                            CONTEXTO DE PROYECTOS ACTIVOS:
                            1. P.A. (Aula): "{pa}" (Días sugeridos: {dias_pa}).
                            2. P.S.P. (Taller): "{psp}" (Días sugeridos: {dias_psp}).
                            """
                    except: 
                        texto_instruccion_proyecto = "Usa el Tema Generador como eje central."

                    # C. PENSUM (INTACTO)
                    texto_bloque_pensum = ""
                    nombre_bloque_pensum = ""
                    try:
                        df_bib = conn.read(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", ttl=0)
                        pensum_act = df_bib[(df_bib['USUARIO'] == st.session_state.u['NOMBRE']) & (df_bib['ESTADO'] == "ACTIVO")]
                        if not pensum_act.empty:
                            fila_pen = pensum_act.iloc[0]
                            nombre_bloque_pensum = fila_pen.get('BLOQUE_ACTUAL', "Contenido General")
                            full_txt = fila_pen['CONTENIDO_FULL']
                            inicio = full_txt.find(nombre_bloque_pensum)
                            if inicio != -1:
                                fin = full_txt.find("BLOQUE:", inicio + 20)
                                texto_bloque_pensum = full_txt[inicio:fin] if fin != -1 else full_txt[inicio:]
                            else:
                                texto_bloque_pensum = full_txt[:2500]
                    except: pass

                    # D. CONSTRUCCIÓN DEL PROMPT (MODIFICADO PARA ESTRATEGIAS)
                    st.session_state.temp_tema = f"{modalidad} - {notas}"
                    
                    encabezado_legal = """
                    **PLANIFICACIÓN SUGERIDA POR SUPER DOCENTE 1.0**
                    *Sustentada en el Currículo Nacional Bolivariano y la Ley Orgánica de Educación (L.O.E.)*
                    ---------------------------------------------------
                    """
                    
                    contexto_pensum = ""
                    if texto_bloque_pensum:
                        contexto_pensum = f"""
                        💎 **INSUMO TÉCNICO (PENSUM ACTIVO):**
                        BLOQUE: "{nombre_bloque_pensum}"
                        CONTENIDO DEL PENSUM:
                        {texto_bloque_pensum}
                        (Extrae de aquí las estrategias si están mencionadas y el contenido técnico).
                        """

                    # REGLAS DE REDACCIÓN (ACTUALIZADAS: ESTRATEGIAS DIRECTAS)
                    reglas_super_docente = """
                    🚨 **REGLAS DE REDACCIÓN OBLIGATORIAS (ANTI-ROBOT):**
                    
                    1. **COMPETENCIA TÉCNICA (Punto 2):** Estructura: VERBO (Infinitivo) + OBJETO + CONDICIÓN.
                    
                    2. **ROTACIÓN DE SINÓNIMOS (INICIOS):**
                       - Indagamos, Socializamos, Conversamos, Visualizamos, Debatimos.
                       - NO repitas el mismo verbo de inicio dos días seguidos.
                    
                    3. **ESTRATEGIAS (Punto 6) - ¡MUY IMPORTANTE!:**
                       - **NO EXPLIQUES LA ESTRATEGIA.** NO digas "Usamos la técnica para...".
                       - **SOLO MENCIONA EL NOMBRE.** Haz una lista separada por comas o guiones.
                       - Usa terminología del Currículo Bolivariano.
                       - EJEMPLO CORRECTO: "Lluvia de ideas, Conversatorio, Práctica guiada, Observación directa."
                       - EJEMPLO INCORRECTO: "Utilizamos la lluvia de ideas para fomentar la participación..." (ESTO ESTÁ PROHIBIDO).
                    
                    4. **ENFOQUE VIVENCIAL:** Todo es "Aprender Haciendo".
                    """

                    prompt = f"""
                    ERES SUPER DOCENTE 1.0, EXPERTO EN PLANIFICACIÓN VENEZOLANA.
                    CONTEXTO: {modalidad} {aula_especifica}. 
                    TEMA: {notas}. LAPSO: {rango}.
                    
                    {reglas_super_docente}
                    
                    {texto_instruccion_proyecto}
                    
                    {contexto_pensum}
                    
                    PERFIL PEI: {perfil_alumno if is_pei else "Grupo regular"}.
                    TONO: {tono_redaccion}.
                    
                    🚨 **FORMATO VISUAL:** DEJA UNA LÍNEA VACÍA ENTRE CADA PUNTO.
                    
                    ESTRUCTURA DE SALIDA (Repite para Lunes a Viernes):
                    
                    {encabezado_legal}
                    
                    ### [DÍA Y FECHA]
                    
                    **1. TÍTULO DE LA ACTIVIDAD:** (Corto y motivador)
                    <br>
                    **2. COMPETENCIA TÉCNICA:** (Verbo Infinitivo + Qué + Para qué)
                    <br>
                    **3. EXPLORACIÓN (Inicio):** [Verbo 1ra persona plural + Actividad]
                    <br>
                    **4. DESARROLLO (Proceso):** [Actividad Vivencial Práctica]
                    <br>
                    **5. REFLEXIÓN (Cierre):** [Sistematización]
                    <br>
                    **6. ESTRATEGIAS:** [LISTADO CONCRETO SIN EXPLICACIÓN. Ej: Lluvia de ideas, Socialización, Práctica Guiada]
                    <br>
                    **7. RECURSOS:** [Materiales]
                    ---------------------------------------------------
                    """
                    
                    # LLAMADA A LA IA
                    respuesta_raw = generar_respuesta([
                        {"role":"system","content":INSTRUCCIONES_TECNICAS}, 
                        {"role":"user","content":prompt}
                    ], 0.7)
                    
                    # FORMATEO VISUAL
                    respuesta_formateada = respuesta_raw \
                        .replace("**1.", "\n\n**1.") \
                        .replace("**2.", "\n\n**2.") \
                        .replace("**3.", "\n\n**3.") \
                        .replace("**4.", "\n\n**4.") \
                        .replace("**5.", "\n\n**5.") \
                        .replace("**6.", "\n\n**6.") \
                        .replace("**7.", "\n\n**7.") \
                        .replace("### ", "\n\n\n### ")
                    
                    st.session_state.plan_actual = respuesta_formateada
                    st.rerun()

        # =============================================================================
        # 5. VISUALIZACIÓN Y GUARDADO (INTACTO)
        # =============================================================================
        if st.session_state.plan_actual:
            st.divider()
            st.success("✅ **Planificación Generada Exitosamente**")
            
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 25px; border-radius: 10px; background-color: #fcfcfc; line-height: 1.8;">
                {st.session_state.plan_actual}
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            col_guardar, col_borrar = st.columns([1, 1])
            with col_guardar:
                if st.button("💾 Guardar en Mi Archivo", key="btn_guardar_final"):
                    try:
                        with st.spinner("Guardando..."):
                            df_historia = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                            tema_guardar = st.session_state.get('temp_tema', notas)
                            nuevo_registro = pd.DataFrame([{
                                "FECHA": ahora_ve().strftime("%d/%m/%Y"), 
                                "USUARIO": st.session_state.u['NOMBRE'], 
                                "TEMA": tema_guardar[:50] + "...", 
                                "CONTENIDO": st.session_state.plan_actual, 
                                "ESTADO": "GUARDADO", 
                                "HORA_INICIO": "--", "HORA_FIN": "--"
                            }])
                            conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df_historia, nuevo_registro], ignore_index=True))
                            st.success("¡Guardado!")
                            time.sleep(1.5)
                            st.session_state.plan_actual = ""
                            st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

            with col_borrar:
                if st.button("🗑️ Descartar", type="secondary", key="btn_descartar"):
                    st.session_state.plan_actual = ""
                    st.rerun()
# -------------------------------------------------------------------------
    # VISTA: AULA VIRTUAL V14.0 (MAESTRA: V13 + CACHÉ + IA + CÁMARAS SECUENCIALES)
    # -------------------------------------------------------------------------
    elif opcion == "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)":
        
        # --- 1. GESTIÓN DE MEMORIA (CACHÉ / FOTOCOPIAS) ---
        # Inicializamos los espacios de memoria si están vacíos
        if 'cache_planes' not in st.session_state: st.session_state.cache_planes = None
        if 'cache_evaluaciones' not in st.session_state: st.session_state.cache_evaluaciones = None
        if 'cache_ejecucion' not in st.session_state: st.session_state.cache_ejecucion = None
        if 'cache_matricula' not in st.session_state: st.session_state.cache_matricula = None
        
        # Variables de estado originales (V13)
        if 'modo_suplencia_activo' not in st.session_state: st.session_state.modo_suplencia_activo = False
        if 'av_titulo_hoy' not in st.session_state: st.session_state.av_titulo_hoy = ""
        if 'av_contexto_hoy' not in st.session_state: st.session_state.av_contexto_hoy = ""
        if 'temp_propuesta_ia' not in st.session_state: st.session_state.temp_propuesta_ia = ""
        
        # Variables para fotos (V13)
        if 'av_foto1' not in st.session_state: st.session_state.av_foto1 = None
        if 'av_foto2' not in st.session_state: st.session_state.av_foto2 = None
        if 'av_foto3' not in st.session_state: st.session_state.av_foto3 = None
        if 'av_resumen' not in st.session_state: st.session_state.av_resumen = ""
        
        # Variable para el Chat Asistente (NUEVO)
        if 'chat_asistente_aula' not in st.session_state: st.session_state.chat_asistente_aula = []

        # --- FUNCIÓN DE SINCRONIZACIÓN (IR A DIRECCIÓN) ---
        def sincronizar_aula():
            try:
                with st.spinner("🔄 Actualizando datos desde Dirección (Google)..."):
                    # Usamos ttl=0 para forzar descarga real
                    st.session_state.cache_planes = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                    st.session_state.cache_evaluaciones = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                    st.session_state.cache_ejecucion = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                    # CORRECCIÓN: Nombre exacto de tu hoja
                    st.session_state.cache_matricula = conn.read(spreadsheet=URL_HOJA, worksheet="MATRICULA_GLOBAL", ttl=0) 
                st.success("✅ Datos actualizados en memoria.")
                time.sleep(0.5)
            except Exception as e: st.error(f"Error sincronizando: {e}")

        # Auto-carga inicial
        if st.session_state.cache_planes is None or st.session_state.cache_matricula is None:
            sincronizar_aula()
            st.rerun()

        # --- ENCABEZADO Y CONTEXTO ---
        c_head, c_btn = st.columns([3, 1])
        with c_head:
            st.info("💡 **Centro de Operaciones:** Gestión de la clase (Inicio - Desarrollo - Cierre).")
        with c_btn:
            if st.button("🔄 RECARGAR DATOS"):
                sincronizar_aula()
                st.rerun()

        st.markdown("### ⚙️ Contexto de la Clase")
        es_suplencia = st.checkbox("🦸 **Activar Modo Suplencia**", 
                                  value=st.session_state.modo_suplencia_activo,
                                  key="chk_suplencia_master")
        st.session_state.modo_suplencia_activo = es_suplencia
        
        # Determinar lista de docentes para suplencia usando CACHÉ
        try:
            if st.session_state.cache_matricula is not None and not st.session_state.cache_matricula.empty:
                if 'DOCENTE_TITULAR' in st.session_state.cache_matricula.columns:
                    lista_docentes_real = sorted(st.session_state.cache_matricula['DOCENTE_TITULAR'].dropna().unique().tolist())
                else: lista_docentes_real = [st.session_state.u['NOMBRE']]
            else: lista_docentes_real = [st.session_state.u['NOMBRE']]
        except: lista_docentes_real = [st.session_state.u['NOMBRE']]

        if es_suplencia:
            lista_suplentes = [d for d in lista_docentes_real if d != st.session_state.u['NOMBRE']]
            if not lista_suplentes: lista_suplentes = ["No hay otros docentes"]
            titular = st.selectbox("Seleccione Docente Titular:", lista_suplentes, key="av_titular_v13")
            st.warning(f"Modo Suplencia: Usando planificación y alumnos de **{titular}**")
        else:
            titular = st.session_state.u['NOMBRE']
            st.success(f"Trabajando con tu planificación y alumnos ({titular}).")

        # --- 2. BUSCAR PLAN ACTIVO (USANDO CACHÉ) ---
        pa = None
        try:
            df_planes = st.session_state.cache_planes
            plan_activo = df_planes[
                (df_planes['USUARIO'] == titular) & 
                (df_planes['ESTADO'] == "ACTIVO")
            ]
            if not plan_activo.empty:
                fila = plan_activo.iloc[0]
                pa = {"CONTENIDO_PLAN": fila['CONTENIDO'], "RANGO": fila.get('FECHA', 'S/F')}
        except: pass

        if not pa:
            st.error(f"🚨 {titular} no tiene un plan activo. Ve a Archivo Pedagógico y activa uno.")
            st.stop()

        # --- 3. PESTAÑAS (TRÍADA PEDAGÓGICA) ---
        tab1, tab2, tab3 = st.tabs(["🚀 Ejecución (Inicio/Desarrollo)", "📝 Evaluación", "🏁 Cierre (Reflexión)"])

        # =====================================================================
        # PESTAÑA 1: EJECUCIÓN + ASISTENTE IA + CÁMARAS SECUENCIALES
        # =====================================================================
        with tab1:
            dias_es = {"Monday":"Lunes", "Tuesday":"Martes", "Wednesday":"Miércoles", "Thursday":"Jueves", "Friday":"Viernes", "Saturday":"Sábado", "Sunday":"Domingo"}
            dia_hoy_nombre = dias_es.get(ahora_ve().strftime("%A"))
            
            import re
            patron = f"(?i)(###|\*\*)\s*{dia_hoy_nombre}.*?(?=(###|\*\*)\s*(Lunes|Martes|Miércoles|Jueves|Viernes)|$)"
            match = re.search(patron, pa["CONTENIDO_PLAN"], re.DOTALL)
            clase_dia = match.group(0) if match else None

            if clase_dia is None:
                st.warning(f"No hay actividad programada para hoy {dia_hoy_nombre}.")
                dia_m = st.selectbox("Seleccione día a ejecutar:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], key="av_manual_v13")
                patron_m = f"(?i)(###|\*\*)\s*{dia_m}.*?(?=(###|\*\*)\s*(Lunes|Martes|Miércoles|Jueves|Viernes)|$)"
                match_m = re.search(patron_m, pa["CONTENIDO_PLAN"], re.DOTALL)
                clase_de_hoy = match_m.group(0) if match_m else "Sin actividad."
            else:
                clase_de_hoy = clase_dia

            st.subheader("📖 Guía de la Actividad")
            if clase_de_hoy:
                st.markdown(f'<div class="plan-box">{clase_de_hoy}</div>', unsafe_allow_html=True)
                
                # Extracción de contexto para evaluación (V13 Logic)
                try:
                    lineas = clase_de_hoy.split('\n')
                    t_temp = "Actividad del Día"
                    c_temp = "Sin contexto."
                    for linea in lineas:
                        if "**1." in linea:
                            parte_sucia = linea.split(":")[1] if ":" in linea else linea
                            t_temp = parte_sucia.replace("**", "").strip()
                        if "**4." in linea:
                            texto_sucio = linea.replace("**4. DESARROLLO (Proceso):**", "")
                            c_temp = texto_sucio[:250].strip() 
                    st.session_state.temp_titulo_extract = t_temp
                    st.session_state.temp_contexto_extract = c_temp
                except:
                    st.session_state.temp_titulo_extract = "Actividad General"
                    st.session_state.temp_contexto_extract = clase_de_hoy[:150]
            
            # --- NUEVO: ASISTENTE IA (INTEGRADO AQUÍ) ---
            with st.expander("🤖 Consultar al Asistente Pedagógico (IA)", expanded=False):
                st.caption("Pregunta sobre dinámicas, adaptaciones o dudas de esta clase.")
                pregunta_docente = st.text_input("Tu pregunta:", key="chat_input_aula")
                if st.button("Consultar IA", key="btn_chat_aula"):
                    if pregunta_docente:
                        with st.spinner("Pensando..."):
                            prompt = f"CONTEXTO CLASE: {clase_de_hoy}. PREGUNTA DOCENTE: {pregunta_docente}. DAME UNA RESPUESTA BREVE Y PRÁCTICA."
                            resp = generar_respuesta([{"role":"user","content":prompt}], 0.7)
                            st.session_state.chat_asistente_aula.append({"user": pregunta_docente, "ia": resp})
                
                for msg in reversed(st.session_state.chat_asistente_aula[-2:]):
                    st.markdown(f"**Tú:** {msg['user']}")
                    st.info(f"**IA:** {msg['ia']}")

            st.divider()
            
            # --- PEI EXPRESS (MOVIDO ARRIBA DE LAS CÁMARAS) ---
            with st.expander("🧩 Adaptación P.E.I. Express (Planificar antes de ejecutar)"):
                try:
                    df_mat = st.session_state.cache_matricula
                    alums = df_mat[df_mat['DOCENTE_TITULAR'] == titular]['NOMBRE_ALUMNO'].dropna().unique().tolist()
                except: alums = []
                
                c1, c2 = st.columns(2)
                with c1: al_a = st.selectbox("Alumno:", ["(Seleccionar)"] + sorted(alums), key="av_pei_al_v13")
                with c2: ctx_a = st.text_input("Situación:", placeholder="Ej: Crisis sensorial...", key="av_pei_ctx_v13")
                
                if st.button("💡 Estrategia IA", key="btn_av_ia_v13"):
                    if al_a != "(Seleccionar)":
                        p_pei = f"PLAN: {clase_de_hoy}. ALUMNO: {al_a}. SITUACIÓN: {ctx_a}. Dame estrategia rápida."
                        st.markdown(f'<div class="eval-box">{generar_respuesta([{"role":"user","content":p_pei}], 0.7)}</div>', unsafe_allow_html=True)
            
            st.divider()

            # --- CÁMARAS SECUENCIALES (BLOQUEO PARA NO COLAPSAR) ---
            col_momento1, col_momento2 = st.columns(2)
            
            # FOTO 1: INICIO (Siempre activa)
            with col_momento1:
                st.markdown("#### 1. Inicio")
                if st.session_state.av_foto1 is None:
                    f1 = st.camera_input("Capturar Inicio", key="av_cam1_v13")
                    if f1 and st.button("📤 Subir Inicio", key="btn_save_f1_v13"):
                        u1 = subir_a_imgbb(f1)
                        if u1: st.session_state.av_foto1 = u1; st.rerun()
                else:
                    st.image(st.session_state.av_foto1, use_container_width=True, caption="✅ Inicio")
                    if st.button("♻️ Reset Inicio", key="reset_f1_v13"): st.session_state.av_foto1 = None; st.rerun()

            # FOTO 2: DESARROLLO (Bloqueada hasta tener Foto 1)
            with col_momento2:
                st.markdown("#### 2. Desarrollo")
                if st.session_state.av_foto1 is None:
                    st.info("🔒 **Cámara Bloqueada**")
                    st.caption("Complete la evidencia de **Inicio** para desbloquear.")
                else:
                    if st.session_state.av_foto2 is None:
                        f2 = st.camera_input("Capturar Desarrollo", key="av_cam2_v13")
                        if f2 and st.button("📤 Subir Desarrollo", key="btn_save_f2_v13"):
                            u2 = subir_a_imgbb(f2)
                            if u2: st.session_state.av_foto2 = u2; st.rerun()
                    else:
                        st.image(st.session_state.av_foto2, use_container_width=True, caption="✅ Desarrollo")
                        if st.button("♻️ Reset Desarr.", key="reset_f2_v13"): st.session_state.av_foto2 = None; st.rerun()

        # =====================================================================
        # PESTAÑA 2: EVALUACIÓN (V13 + CACHÉ + MATRÍCULA CORRECTA)
        # =====================================================================
        with tab2:
            st.subheader("📝 Evaluación Individual")
            try:
                df_mat = st.session_state.cache_matricula
                alums = df_mat[df_mat['DOCENTE_TITULAR'] == titular]['NOMBRE_ALUMNO'].dropna().unique().tolist()
            except: alums = []
            
            if not alums:
                st.warning(f"No se encontraron alumnos para **{titular}** en 'MATRICULA_GLOBAL'.")
            else:
                e_sel = st.selectbox("Estudiante:", sorted(alums), key="av_eval_al_v13")
                
                if st.button("🔍 Cargar Datos de Hoy", key="btn_load_act_v13"):
                    st.session_state.av_titulo_hoy = st.session_state.get('temp_titulo_extract', 'Actividad Manual')
                    st.session_state.av_contexto_hoy = st.session_state.get('temp_contexto_extract', 'Sin contexto.')
                    st.session_state.temp_propuesta_ia = ""
                    st.rerun()
                
                st.caption(f"Actividad: {st.session_state.av_titulo_hoy}")
                o_eval = st.text_area("Observación Anecdótica:", placeholder="¿Qué logró hoy?", key="av_eval_obs_v13")
                
                if o_eval and st.button("✨ Mejorar Redacción (IA)", key="btn_sugerir_ia_v13"):
                    with st.spinner("Redactando..."):
                        p_ev = f"Alumno: {e_sel}. Obs: {o_eval}. Contexto: {st.session_state.av_contexto_hoy}. Mejora redacción pedagógica."
                        st.session_state.temp_propuesta_ia = generar_respuesta([{"role":"user","content":p_ev}], 0.5)
                
                if st.session_state.temp_propuesta_ia:
                    st.info("Propuesta IA:")
                    st.write(st.session_state.temp_propuesta_ia)

                if st.button("💾 Guardar Nota", type="primary", key="btn_save_final_v13"):
                    if o_eval and st.session_state.av_titulo_hoy:
                        nota_final = st.session_state.temp_propuesta_ia if st.session_state.temp_propuesta_ia else o_eval
                        
                        try:
                            # 1. Guardar en NUBE (EVALUACIONES)
                            nueva_n = pd.DataFrame([{
                                "FECHA": ahora_ve().strftime("%d/%m/%Y"), 
                                "USUARIO": st.session_state.u['NOMBRE'], 
                                "DOCENTE_TITULAR": titular, 
                                "ESTUDIANTE": e_sel, 
                                "ACTIVIDAD": st.session_state.av_titulo_hoy, 
                                "ANECDOTA": o_eval, 
                                "EVALUACION_IA": nota_final, # Regla de Oro: Tu columna
                                "PLANIFICACION_ACTIVA": pa['RANGO']
                            }])
                            df_ev = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                            conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, nueva_n], ignore_index=True))
                            
                            # 2. Guardar en CACHÉ
                            if st.session_state.cache_evaluaciones is not None:
                                st.session_state.cache_evaluaciones = pd.concat([st.session_state.cache_evaluaciones, nueva_n], ignore_index=True)

                            st.success("✅ Nota Guardada")
                            st.session_state.temp_propuesta_ia = ""
                            time.sleep(1); st.rerun()
                        except Exception as e: st.error(f"Error guardando: {e}")
                    else: st.error("Faltan datos.")

        # =====================================================================
        # PESTAÑA 3: CIERRE (FOTO 3 BLOQUEADA + CONSOLIDACIÓN)
        # =====================================================================
        with tab3:
            st.subheader("🏁 Cierre de Jornada")
            
            # Verificación en CACHÉ
            try:
                hoy_check = ahora_ve().strftime("%d/%m/%Y")
                df_check = st.session_state.cache_ejecucion
                ya_cerro = not df_check[(df_check['USUARIO'] == st.session_state.u['NOMBRE']) & (df_check['FECHA'] == hoy_check)].empty
            except: ya_cerro = False
            
            if ya_cerro:
                st.success("✅ Jornada de hoy ya consolidada.")
                if st.button("🏠 Volver"): st.session_state.pagina_actual = "HOME"; st.rerun()
            else:
                st.markdown("#### 3. Evidencia de Cierre")
                # BLOQUEO DE CÁMARA 3: Requiere Desarrollo listo
                if st.session_state.av_foto2 is None:
                     st.info("🔒 **Cámara Bloqueada**")
                     st.caption("Complete la evidencia de **Desarrollo** para habilitar el Cierre.")
                else:
                    if st.session_state.av_foto3 is None:
                        f3 = st.camera_input("Capturar Cierre", key="av_cam3_v13")
                        if f3 and st.button("📤 Subir Cierre", key="btn_save_f3_v13"):
                            u3 = subir_a_imgbb(f3)
                            if u3: st.session_state.av_foto3 = u3; st.rerun()
                    else:
                        st.image(st.session_state.av_foto3, width=200, caption="✅ Cierre")
                        if st.button("♻️ Reset Cierre", key="reset_f3_v13"): st.session_state.av_foto3 = None; st.rerun()

                st.divider()
                st.session_state.av_resumen = st.text_area("Resumen Pedagógico:", value=st.session_state.av_resumen, key="av_res_v13", height=100)
                
                if st.button("🚀 CONSOLIDAR JORNADA", type="primary", key="btn_fin_v13"):
                    # Validación V13
                    faltan = []
                    if not st.session_state.av_foto1: faltan.append("Inicio")
                    if not st.session_state.av_foto2: faltan.append("Desarrollo")
                    if not st.session_state.av_foto3: faltan.append("Cierre")
                    
                    if faltan:
                        st.error(f"⚠️ Faltan evidencias: {', '.join(faltan)}")
                    elif not st.session_state.av_resumen:
                        st.error("⚠️ Falta el resumen.")
                    else:
                        with st.spinner("Guardando Bitácora..."):
                            try:
                                fotos_str = f"{st.session_state.av_foto1}|{st.session_state.av_foto2}|{st.session_state.av_foto3}"
                                nueva_f = pd.DataFrame([{
                                    "FECHA": hoy_check, 
                                    "USUARIO": st.session_state.u['NOMBRE'], 
                                    "DOCENTE_TITULAR": titular, 
                                    "ACTIVIDAD_TITULO": st.session_state.av_titulo_hoy or "General", 
                                    "EVIDENCIA_FOTO": fotos_str, 
                                    "RESUMEN_LOGROS": st.session_state.av_resumen, 
                                    "ESTADO": "CULMINADA", 
                                    "PUNTOS": 5
                                }])
                                
                                # 1. Guardar NUBE
                                df_ej = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                                conn.update(spreadsheet=URL_HOJA, worksheet="EJECUCION", data=pd.concat([df_ej, nueva_f], ignore_index=True))
                                
                                # 2. Guardar CACHÉ
                                if st.session_state.cache_ejecucion is not None:
                                    st.session_state.cache_ejecucion = pd.concat([st.session_state.cache_ejecucion, nueva_f], ignore_index=True)
                                
                                # Limpieza
                                st.session_state.av_foto1 = None
                                st.session_state.av_foto2 = None
                                st.session_state.av_foto3 = None
                                st.session_state.av_resumen = ""
                                st.balloons()
                                st.success("✅ ¡Jornada Exitosa!")
                                time.sleep(2); st.session_state.pagina_actual = "HOME"; st.rerun()
                            except Exception as e: st.error(f"Error: {e}")
# -------------------------------------------------------------------------
    # VISTA: FÁBRICA DE PENSUMS Y BIBLIOTECA (VERSIÓN DEFINITIVA: GESTIÓN TOTAL)
    # -------------------------------------------------------------------------
    elif opcion == "🏗️ FÁBRICA DE PENSUMS":
        st.header("🏗️ Fábrica de Diseño Instruccional")
        st.markdown("Generador estandarizado de currículo y gestión de activación por Bloques.")

        # --- MEMORIA TEMPORAL ---
        if 'fp_fase1' not in st.session_state: st.session_state.fp_fase1 = ""
        if 'fp_fase2' not in st.session_state: st.session_state.fp_fase2 = ""
        if 'fp_fase3' not in st.session_state: st.session_state.fp_fase3 = ""
        if 'fp_completo' not in st.session_state: st.session_state.fp_completo = ""
        
        # Estado del Visor de Lectura
        if 'visor_activo' not in st.session_state: st.session_state.visor_activo = False
        if 'visor_data' not in st.session_state: st.session_state.visor_data = {}

        tab_fabrica, tab_biblioteca = st.tabs(["🏭 Línea de Producción (Crear)", "📚 Biblioteca y Configuración"])

        # =====================================================================
        # PESTAÑA 1: LA FÁBRICA (CREACIÓN DE PENSUMS)
        # =====================================================================
        with tab_fabrica:
            st.subheader("1. Ficha Técnica")
            c1, c2 = st.columns(2)
            with c1:
                especialidad = st.text_input("Especialidad a Crear:", placeholder="Ej: Educación Musical")
            with c2:
                docente_resp = st.text_input("Docente Responsable:", value=st.session_state.u['NOMBRE'])
            
            contexto_extra = st.text_area("Recursos y Enfoque (Clave para la adaptación):", 
                                        placeholder="Ej: Tenemos instrumentos de percusión, queremos formar una banda, no hay electricidad...")
            
            st.divider()

            # FASE 1
            st.markdown("### 🔹 Fase 1: Fundamentación Institucional")
            if st.button("Generar Fase 1 (Fundamentación)", type="primary"):
                if especialidad:
                    with st.spinner("Redactando bases..."):
                        prompt_f1 = f"""
                        ACTÚA COMO COORDINADOR DEL TEL ERAC (ZULIA).
                        REDACTA LA "FUNDAMENTACIÓN Y METAS" PARA EL PENSUM DE: {especialidad}.
                        CONTEXTO: "{contexto_extra}".
                        ESTRUCTURA OBLIGATORIA:
                        1. Encabezado Oficial: República Bolivariana... TEL ERAC.
                        2. PEIC VIGENTE: "Una escuela sustentable...". Vértice 5.
                        3. JUSTIFICACIÓN: Adaptada a {especialidad}.
                        4. METAS: Independencia laboral, Resiliencia, Autoestima.
                        5. LIMITACIONES (ZULIA): Fallas eléctricas, transporte, economía multimoneda.
                        REGLA DE ORO: NO ESCRIBAS NINGUNA CONCLUSIÓN O DESPEDIDA.
                        """
                        st.session_state.fp_fase1 = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":prompt_f1}], 0.7)
                else: st.error("Falta el nombre.")
            
            if st.session_state.fp_fase1:
                st.session_state.fp_fase1 = st.text_area("Edición Fase 1:", value=st.session_state.fp_fase1, height=200)

            # FASE 2
            st.markdown("### 🔹 Fase 2: Temario y Contenidos")
            st.info("La IA generará listas de conceptos (Temario) para que el Planificador tenga material.")
            
            if st.button("Generar Fase 2 (Temario)", type="primary"):
                if st.session_state.fp_fase1:
                    with st.spinner("Diseñando Estructura de Temas..."):
                        prompt_f2 = f"""
                        CONTEXTO: {especialidad}. RECURSOS: {contexto_extra}.
                        TAREA: DISEÑA LOS BLOQUES DE CONTENIDO (TEMARIO).
                        IMPORTANTE: NO GENERES ACTIVIDADES ESPECÍFICAS. GENERA LISTAS DE CONCEPTOS.
                        FORMATO DE NUMERACIÓN ESTRICTO: "1. BLOQUE: [NOMBRE]"
                        
                        ORDEN EXACTO:
                        1. BLOQUE: INTRODUCCIÓN A {especialidad}
                        2. BLOQUE: ATENCIÓN AL PÚBLICO
                        3. BLOQUE: [TEMA TÉCNICO BÁSICO DE {especialidad}]
                        4. BLOQUE: SEGURIDAD E HIGIENE
                        5. BLOQUE: [TEMA TÉCNICO INTERMEDIO DE {especialidad}]
                        6. BLOQUE: SERVICIOS Y TRÁMITES
                        7. BLOQUE: [TEMA TÉCNICO AVANZADO DE {especialidad}]
                        8. BLOQUE: IDENTIDAD Y TIEMPO
                        9. BLOQUE: PROYECTO DE VIDA
                        10. BLOQUE: TECNOLOGÍA
                        11. BLOQUE: CONO MONETARIO
                        12. BLOQUE: SALUD INTEGRAL
                        13. BLOQUE: P.S.P. (Producto Final)
                        14. BLOQUE: MERCADEO Y VENTAS
                        NO AGREGUES CONCLUSIONES.
                        """
                        st.session_state.fp_fase2 = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":prompt_f2}], 0.7)
                else: st.error("Genera la Fase 1 primero.")

            if st.session_state.fp_fase2:
                st.session_state.fp_fase2 = st.text_area("Edición Fase 2:", value=st.session_state.fp_fase2, height=300)

            # FASE 3
            st.markdown("### 🔹 Fase 3: Estrategias y Evaluación")
            if st.button("Generar Fase 3 (Metodología)", type="primary"):
                if st.session_state.fp_fase2:
                    with st.spinner("Creando metodología..."):
                        prompt_f3 = f"""
                        PARA EL PENSUM DE: {especialidad}.
                        GENERA: ESTRATEGIAS, RECURSOS Y EVALUACIÓN.
                        NO HAGAS CONCLUSIONES.
                        - ESTRATEGIAS: Vivenciales.
                        - RECURSOS: "{contexto_extra}", materiales de provecho.
                        - EVALUACIÓN: Lista de Cotejo, Observación.
                        """
                        st.session_state.fp_fase3 = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":prompt_f3}], 0.6)
                else: st.error("Genera la Fase 2 primero.")

            if st.session_state.fp_fase3:
                st.session_state.fp_fase3 = st.text_area("Edición Fase 3:", value=st.session_state.fp_fase3, height=200)

            st.divider()

            # CONSOLIDACIÓN
            st.markdown("### 🔗 Consolidación Final")
            if st.button("🔗 UNIR TODO EL DOCUMENTO", type="primary", use_container_width=True):
                if st.session_state.fp_fase1 and st.session_state.fp_fase2 and st.session_state.fp_fase3:
                    st.session_state.fp_completo = f"""
================================================================
DISEÑO INSTRUCCIONAL: {especialidad.upper()}
INSTITUCIÓN: TEL ELENA ROSA ARANGUREN DE CASTELLANO (ERAC)
DOCENTE RESPONSABLE: {docente_resp}
FECHA: {ahora_ve().strftime("%d/%m/%Y")}
================================================================

{st.session_state.fp_fase1}

----------------------------------------------------------------
MALLA CURRICULAR Y TEMARIO (CONTENIDOS)
----------------------------------------------------------------
{st.session_state.fp_fase2}

----------------------------------------------------------------
ESTRATEGIAS METODOLÓGICAS Y EVALUACIÓN
----------------------------------------------------------------
{st.session_state.fp_fase3}
                    """
                    st.success("✅ Documento Unificado.")
                else:
                    st.error("Faltan fases.")

            if st.session_state.fp_completo:
                st.markdown("#### 📄 Vista Previa y Edición Final")
                st.session_state.fp_completo = st.text_area("Documento Maestro (Editable):", 
                                                          value=st.session_state.fp_completo, height=400)
                
                c_save, c_down = st.columns(2)
                with c_save:
                    if st.button("💾 Guardar en Biblioteca"):
                        try:
                            try:
                                df_lib = conn.read(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", ttl=0)
                            except:
                                # Creamos columnas base si es nuevo
                                df_lib = pd.DataFrame(columns=["FECHA", "USUARIO", "TITULO_PENSUM", "CONTENIDO_FULL", "ESTADO", "DIAS", "BLOQUE_ACTUAL"])

                            nuevo_pen = pd.DataFrame([{
                                "FECHA": ahora_ve().strftime("%d/%m/%Y"),
                                "USUARIO": st.session_state.u['NOMBRE'],
                                "TITULO_PENSUM": especialidad,
                                "CONTENIDO_FULL": st.session_state.fp_completo,
                                "ESTADO": "INACTIVO", 
                                "DIAS": "",
                                "BLOQUE_ACTUAL": "1. BLOQUE: INTRODUCCIÓN" # Valor inicial por defecto
                            }])
                            conn.update(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", data=pd.concat([df_lib, nuevo_pen], ignore_index=True))
                            st.balloons()
                            st.success("Guardado en la Nube.")
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

                with c_down:
                    st.download_button("📥 Descargar Archivo (.txt)", data=st.session_state.fp_completo, file_name=f"PENSUM_{especialidad}_ERAC.txt")

        # =====================================================================
        # PESTAÑA 2: BIBLIOTECA (GESTIÓN + VISOR + SELECTOR DE BLOQUE)
        # =====================================================================
        with tab_biblioteca:
            
            # ESCENARIO A: MODO LECTURA ACTIVADO (Visor Pantalla Completa)
            if st.session_state.visor_activo:
                data = st.session_state.visor_data
                
                c_vol, c_tit = st.columns([1, 6])
                with c_vol:
                    if st.button("🔙 SALIR", use_container_width=True):
                        st.session_state.visor_activo = False
                        st.rerun()
                with c_tit:
                    st.subheader(f"📖 Leyendo: {data['TITULO_PENSUM']}")
                
                st.divider()
                
                busqueda = st.text_input("🔍 Buscar en el documento:", placeholder="Escribe para filtrar...")
                texto_completo = data['CONTENIDO_FULL']
                
                if busqueda:
                    st.markdown(f"**Resultados para: '{busqueda}'**")
                    lineas = texto_completo.split('\n')
                    encontrado = False
                    for i, linea in enumerate(lineas):
                        if busqueda.lower() in linea.lower():
                            st.info(f"📍 Línea {i}: ...{linea.strip()}...")
                            encontrado = True
                    if not encontrado: st.warning("No se encontraron coincidencias.")
                    st.divider()

                st.text_area("Documento Maestro:", value=texto_completo, height=800)


            # ESCENARIO B: GESTIÓN DE TARJETAS (SELECTOR DE BLOQUES)
            else:
                st.subheader("📚 Gestión de Pensums, Horarios y Bloques")
                try:
                    df_biblio = conn.read(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", ttl=0)
                    mis_p = df_biblio[df_biblio['USUARIO'] == st.session_state.u['NOMBRE']]
                    
                    if mis_p.empty:
                        st.info("No tienes pensums registrados.")
                    else:
                        for i, row in mis_p.iterrows():
                            # Variables Actuales
                            estado_actual = row['ESTADO']
                            es_activo = (estado_actual == "ACTIVO")
                            
                            # Recuperar Días
                            dias_guardados = []
                            if "DIAS" in row and pd.notna(row['DIAS']) and row['DIAS'] != "":
                                dias_guardados = str(row['DIAS']).split(",")
                            
                            # Recuperar Bloque Actual (NUEVO)
                            bloque_guardado = "1. BLOQUE: INTRODUCCIÓN"
                            if "BLOQUE_ACTUAL" in row and pd.notna(row['BLOQUE_ACTUAL']) and row['BLOQUE_ACTUAL'] != "":
                                bloque_guardado = row['BLOQUE_ACTUAL']

                            # --- MAGIA: DETECTAR LOS BLOQUES DEL TEXTO ---
                            texto_full = row['CONTENIDO_FULL']
                            lista_bloques_detectados = []
                            # Escaneo simple de líneas que parecen bloques
                            for linea in texto_full.split('\n'):
                                if "BLOQUE:" in linea.upper():
                                    lista_bloques_detectados.append(linea.strip())
                            
                            if not lista_bloques_detectados:
                                lista_bloques_detectados = ["1. BLOQUE: GENERAL (No detectados)"]

                            # Título visual
                            titulo_card = f"🟢 {row['TITULO_PENSUM']}" if es_activo else f"⚪ {row['TITULO_PENSUM']} (Inactivo)"
                            
                            with st.expander(titulo_card):
                                st.caption(f"Fecha: {row['FECHA']}")
                                
                                # 1. BOTÓN LECTURA
                                if st.button(f"📖 ABRIR / CONSULTAR", key=f"read_{i}", use_container_width=True):
                                    st.session_state.visor_activo = True
                                    st.session_state.visor_data = row
                                    st.rerun()
                                
                                st.divider()
                                
                                # 2. CONFIGURACIÓN COMPLETA
                                c_conf, c_del = st.columns([3, 1])
                                
                                with c_conf:
                                    st.markdown("##### ⚙️ Configuración del Planificador")
                                    
                                    # A. INTERRUPTOR
                                    nuevo_estado_bool = st.toggle("Activar Pensum", value=es_activo, key=f"tog_{i}")
                                    
                                    if nuevo_estado_bool:
                                        # B. SELECTOR DE DÍAS (¿Cuándo?)
                                        seleccion_dias = st.multiselect(
                                            "¿Qué días das esta clase?", 
                                            ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], 
                                            default=dias_guardados, 
                                            key=f"ms_{i}"
                                        )

                                        # C. SELECTOR DE BLOQUE (¿Qué tema?)
                                        st.info("📌 **¿En qué Bloque estás trabajando esta semana?**")
                                        
                                        # Encontrar índice del bloque guardado
                                        idx_bloque = 0
                                        if bloque_guardado in lista_bloques_detectados:
                                            idx_bloque = lista_bloques_detectados.index(bloque_guardado)
                                        elif len(lista_bloques_detectados) > 0:
                                            idx_bloque = 0
                                            
                                        seleccion_bloque = st.selectbox(
                                            "Selecciona el Bloque Actual:",
                                            lista_bloques_detectados,
                                            index=idx_bloque,
                                            key=f"sb_bloq_{i}",
                                            help="La IA generará actividades SOLO de este tema."
                                        )
                                    else:
                                        st.caption("Activa el Pensum para configurar Días y Bloques.")
                                        seleccion_dias = []
                                        seleccion_bloque = ""
                                        
                                    # BOTÓN GUARDAR
                                    if st.button("💾 Guardar Configuración", key=f"upd_{i}"):
                                        try:
                                            df_biblio.at[i, 'ESTADO'] = "ACTIVO" if nuevo_estado_bool else "INACTIVO"
                                            df_biblio.at[i, 'DIAS'] = ",".join(seleccion_dias)
                                            # GUARDAMOS EL BLOQUE
                                            df_biblio.at[i, 'BLOQUE_ACTUAL'] = seleccion_bloque 
                                            
                                            conn.update(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", data=df_biblio)
                                            st.toast(f"✅ Guardado: {seleccion_bloque}")
                                            time.sleep(1)
                                            st.rerun()
                                        except Exception as e: st.error(f"Error (Verifica columna BLOQUE_ACTUAL): {e}")

                                with c_del:
                                    st.write("")
                                    st.write("")
                                    if st.button("🗑️", key=f"del_{i}"):
                                        df_new = df_biblio.drop(i)
                                        conn.update(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", data=df_new)
                                        st.rerun()

                except Exception as e:
                    st.warning(f"Error cargando biblioteca: {e}")
# -------------------------------------------------------------------------
    # VISTA: GESTIÓN DE PROYECTOS (ACTUALIZADO: HORARIOS SEPARADOS PA vs PSP)
    # -------------------------------------------------------------------------
    elif opcion == "🏗️ GESTIÓN DE PROYECTOS Y PLANES":
        st.header("🏗️ Configuración de Proyectos y Planes")
        st.markdown("Defina su hoja de ruta. El sistema diferenciará los días de Teoría (P.A.) y Práctica (P.S.P.).")

        # 1. LEER DATOS (Con Caché y Prioridad Local)
        try:
            df_proy = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=0)
            # Filtramos por usuario
            mi_proy = df_proy[df_proy['USUARIO'] == st.session_state.u['NOMBRE']]
        except:
            mi_proy = pd.DataFrame()

        # FORMULARIO
        with st.form("form_config_proyectos"):
            
            st.subheader("1. Identidad del Servicio")
            # Intentamos recuperar el valor guardado, si no, valor por defecto
            idx_mod = 0
            if not mi_proy.empty and "MODALIDAD" in mi_proy.columns:
                mod_guardada = mi_proy.iloc[0]['MODALIDAD']
                lista_ops = ["Taller de Educación Laboral (T.E.L.)", "Aula Integrada", "Escuela Especial"]
                if mod_guardada in lista_ops:
                    idx_mod = lista_ops.index(mod_guardada)

            modalidad = st.selectbox("¿A qué Modalidad o Servicio pertenece usted?", 
                                   ["Taller de Educación Laboral (T.E.L.)", "Aula Integrada", "Escuela Especial"],
                                   index=idx_mod)
            
            st.divider()
            
            st.subheader("2. Datos de los Proyectos y Horarios")
            
            # --- SECCIÓN A: PROYECTO DE APRENDIZAJE (P.A.) ---
            st.markdown("##### 📘 Proyecto de Aprendizaje (P.A. - Aula/Teoría)")
            st.caption("Días dedicados a la formación académica, valores y teoría en el aula.")
            
            # Recuperar Titulo PA
            val_pa = "VALORES PARA EL TRABAJO LIBERADOR"
            if not mi_proy.empty and "TITULO_PA" in mi_proy.columns:
                 val_pa = mi_proy.iloc[0]['TITULO_PA']
            pa_titulo = st.text_input("Nombre del P.A.:", value=val_pa)
            
            # Recuperar Días PA
            dias_pa_default = []
            if not mi_proy.empty and "DIAS_PA" in mi_proy.columns and pd.notna(mi_proy.iloc[0]['DIAS_PA']):
                # Convertimos string "Lunes,Martes" a lista ["Lunes", "Martes"]
                raw_pa = str(mi_proy.iloc[0]['DIAS_PA'])
                if raw_pa.strip() != "":
                    dias_pa_default = raw_pa.split(",")
                    # Limpiamos espacios por si acaso
                    dias_pa_default = [d.strip() for d in dias_pa_default if d.strip() in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]]

            dias_pa_sel = st.multiselect("Seleccione los días de P.A. (Aula):", 
                                       ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
                                       default=dias_pa_default,
                                       key="sel_dias_pa")

            st.write("") # Espacio visual
            st.divider()

            # --- SECCIÓN B: PROYECTO SOCIO-PRODUCTIVO (P.S.P.) ---
            st.markdown("##### 🛠️ Proyecto Socio-Productivo (P.S.P. - Taller/Práctica)")
            st.caption("Días dedicados a la práctica laboral, taller y manos a la obra.")
            
            # Recuperar Titulo PSP
            val_psp = "VIVERO ORNAMENTAL"
            if not mi_proy.empty and "TITULO_PSP" in mi_proy.columns:
                 val_psp = mi_proy.iloc[0]['TITULO_PSP']
            psp_titulo = st.text_input("Nombre del P.S.P.:", value=val_psp)
            
            # Recuperar Días PSP
            dias_psp_default = []
            if not mi_proy.empty and "DIAS_PSP" in mi_proy.columns and pd.notna(mi_proy.iloc[0]['DIAS_PSP']):
                raw_psp = str(mi_proy.iloc[0]['DIAS_PSP'])
                if raw_psp.strip() != "":
                    dias_psp_default = raw_psp.split(",")
                    dias_psp_default = [d.strip() for d in dias_psp_default if d.strip() in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]]

            dias_psp_sel = st.multiselect("Seleccione los días de P.S.P. (Taller):", 
                                        ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
                                        default=dias_psp_default,
                                        key="sel_dias_psp")

            st.divider()
            
            # ESTADO DEL PROYECTO
            c_tog, c_st = st.columns([1, 4])
            with c_tog:
                # Recuperar estado
                estado_val = True
                if not mi_proy.empty and "ESTADO" in mi_proy.columns:
                    if mi_proy.iloc[0]['ESTADO'] == "PAUSADO":
                        estado_val = False
                activo = st.toggle("✅ ACTIVAR PROYECTO", value=estado_val)
            with c_st:
                st.caption("Si desactiva, el sistema usará planificación genérica.")

            submitted = st.form_submit_button("💾 Guardar Configuración")
            
            if submitted:
                try:
                    # Preparamos los días como texto separado por comas
                    str_dias_pa = ",".join(dias_pa_sel)
                    str_dias_psp = ",".join(dias_psp_sel)
                    
                    # 1. Borramos el registro anterior del usuario para no duplicar
                    df_nuevo = df_proy[df_proy['USUARIO'] != st.session_state.u['NOMBRE']]
                    
                    # 2. Creamos el nuevo registro con TODOS los campos
                    registro_actualizado = pd.DataFrame([{
                        "FECHA": ahora_ve().strftime("%d/%m/%Y"),
                        "USUARIO": st.session_state.u['NOMBRE'],
                        "MODALIDAD": modalidad,
                        "TITULO_PA": pa_titulo,
                        "TITULO_PSP": psp_titulo,
                        "DIAS_PA": str_dias_pa,    # <--- GUARDAMOS DÍAS PA EN SU COLUMNA
                        "DIAS_PSP": str_dias_psp,  # <--- GUARDAMOS DÍAS PSP EN SU COLUMNA
                        "ESTADO": "ACTIVO" if activo else "PAUSADO"
                    }])
                    
                    # 3. Guardamos
                    conn.update(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", data=pd.concat([df_nuevo, registro_actualizado], ignore_index=True))
                    st.success("✅ ¡Horarios diferenciados guardados correctamente!")
                    time.sleep(1.5)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al guardar: {e}. (Asegúrate de que las columnas DIAS_PA y DIAS_PSP existen en la hoja CONFIG_PROYECTO).")
  # -------------------------------------------------------------------------
    # VISTA: REGISTRO DE EVALUACIONES (v12.5 PRUEBA FINAL)
    # -------------------------------------------------------------------------
    elif opcion == "📊 Registro de Evaluaciones":
        # 1. CAMBIO VISIBLE: Si no ves este título, NO se ha guardado el archivo
        st.title("🛠️ MODO MANTENIMIENTO: BORRADO") 
        
        try:
            df_historial = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
            
            # Filtro
            mis_alumnos_data = df_historial[df_historial['DOCENTE_TITULAR'] == st.session_state.u['NOMBRE']]
            
            if mis_alumnos_data.empty:
                st.info("No hay datos.")
            else:
                lista = sorted(mis_alumnos_data['ESTUDIANTE'].unique())
                alumno_sel = st.selectbox("Alumno:", lista)
                registros = mis_alumnos_data[mis_alumnos_data['ESTUDIANTE'] == alumno_sel]
                
                st.write(f"Encontradas: {len(registros)}")
                st.divider()

                # BUCLE SIMPLIFICADO
                for _, fila in registros.iloc[::-1].iterrows():
                    
                    # 1. LA TARJETA (Solo para ver)
                    with st.expander(f"📅 {fila['FECHA']} | {fila['USUARIO']}"):
                        st.write(fila['EVALUACION_IA'])
                    
                    # 2. EL BOTÓN (AFUERA DE LA TARJETA - IMPOSIBLE NO VERLO)
                    # Está al mismo nivel que el expander, no adentro.
                    col_a, col_b = st.columns([0.7, 0.3])
                    with col_a:
                        st.caption("👆 Revisa la nota arriba antes de borrar.")
                    with col_b:
                        # Botón directo, sin complicaciones
                        if st.button("🗑️ BORRAR", key=f"del_{fila.name}", type="primary"):
                            df_new = df_historial.drop(fila.name)
                            conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=df_new)
                            st.success("¡Borrado!")
                            time.sleep(1)
                            st.rerun()
                    
                    st.divider() # Línea para separar cada nota

        except Exception as e:
            st.error(f"Error: {e}")
# -------------------------------------------------------------------------
    # VISTA: MI ARCHIVO PEDAGÓGICO (VERSIÓN MAESTRA: CACHÉ + CARPETAS VISIBLES)
    # -------------------------------------------------------------------------
    elif opcion == "📂 Mi Archivo Pedagógico":
        
        # --- 1. GESTIÓN DE MEMORIA Y ESTADO ---
        if 'visor_plan_activo' not in st.session_state: st.session_state.visor_plan_activo = False
        if 'visor_plan_data' not in st.session_state: st.session_state.visor_plan_data = {}
        if 'resumen_alumno_ia' not in st.session_state: st.session_state.resumen_alumno_ia = ""
        if 'alumno_seleccionado_temp' not in st.session_state: st.session_state.alumno_seleccionado_temp = None
        
        # Inicialización del Caché (Las fotocopias)
        if 'cache_ejecucion' not in st.session_state: st.session_state.cache_ejecucion = None
        if 'cache_evaluaciones' not in st.session_state: st.session_state.cache_evaluaciones = None
        if 'cache_planes' not in st.session_state: st.session_state.cache_planes = None
        if 'cache_pensums' not in st.session_state: st.session_state.cache_pensums = None

        # --- FUNCIÓN DE SINCRONIZACIÓN (IR A DIRECCIÓN) ---
        def sincronizar_datos():
            try:
                with st.spinner("🔄 Yendo a dirección a actualizar los archivos..."):
                    st.session_state.cache_ejecucion = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                    st.session_state.cache_evaluaciones = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                    st.session_state.cache_planes = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                    st.session_state.cache_pensums = conn.read(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", ttl=0)
                st.success("✅ Datos actualizados.")
                time.sleep(0.5)
            except Exception as e: st.error(f"Error sincronizando: {e}")

        # --- FUNCIÓN TARJETA BITÁCORA ---
        def renderizar_tarjeta(row_act, df_evals):
            fecha = row_act['FECHA']
            titulo = row_act['ACTIVIDAD_TITULO']
            resumen = row_act['RESUMEN_LOGROS']
            fotos_str = str(row_act['EVIDENCIA_FOTO'])
            
            with st.container(border=True):
                c_tit, c_fecha = st.columns([4, 1])
                c_tit.markdown(f"**📌 {titulo}**")
                c_fecha.caption(f"📅 {fecha}")
                
                if fotos_str and fotos_str != "None" and fotos_str != "":
                    urls = fotos_str.split("|") if "|" in fotos_str else [fotos_str]
                    cols_f = st.columns(len(urls))
                    for i, url in enumerate(urls):
                        with cols_f[i]:
                            if "http" in url: st.image(url, use_container_width=True)
                else: st.info("📷 Sin foto.")
                
                if resumen and resumen != "None": st.markdown(f"**📝 Bitácora:** {resumen}")

                if not df_evals.empty:
                    evals_dia = df_evals[df_evals['FECHA'] == fecha]
                    if not evals_dia.empty:
                        st.divider()
                        st.markdown("📊 **Resultados:**")
                        col_juicio = 'EVALUACION_IA' if 'EVALUACION_IA' in evals_dia.columns else None
                        if col_juicio:
                            textos = evals_dia[col_juicio].astype(str).str.upper()
                            cons = textos.str.count("CONSOLIDADO").sum()
                            proc = textos.str.count("PROCESO").sum()
                            ini = textos.str.count("INICIADO").sum()
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Total", len(evals_dia))
                            m2.metric("Consolidado", int(cons))
                            m3.metric("Proceso", int(proc))
                            m4.metric("Iniciado", int(ini))

        # --- ENCABEZADO ---
        if not st.session_state.visor_plan_activo:
            c_head, c_btn = st.columns([3, 1])
            with c_head: st.header("📂 Mi Archivo Pedagógico")
            with c_btn:
                if st.button("🔄 ACTUALIZAR DATOS", help="Recargar desde Google Sheets"):
                    sincronizar_datos()
                    st.rerun()

        # Carga inicial automática si está vacío
        if st.session_state.cache_ejecucion is None:
            sincronizar_datos()
            st.rerun()

        # --- FILTRADO DE DATOS (USANDO CACHÉ) ---
        try:
            df_full = st.session_state.cache_ejecucion
            mis_clases = df_full[df_full['USUARIO'] == st.session_state.u['NOMBRE']]

            df_ev_full = st.session_state.cache_evaluaciones
            mis_evaluaciones = df_ev_full[df_ev_full['USUARIO'] == st.session_state.u['NOMBRE']] if not df_ev_full.empty else pd.DataFrame()

            df_pl_full = st.session_state.cache_planes
            mis_planes = df_pl_full[df_pl_full['USUARIO'] == st.session_state.u['NOMBRE']] if not df_pl_full.empty else pd.DataFrame()

            df_pe_full = st.session_state.cache_pensums
            mis_pensums = df_pe_full[(df_pe_full['USUARIO'] == st.session_state.u['NOMBRE']) & (df_pe_full['ESTADO'] == "ACTIVO")] if not df_pe_full.empty else pd.DataFrame()

        except Exception as e:
            st.warning("Cargando datos...")
            st.stop()

        # =====================================================================
        # MODO VISOR (PANTALLA COMPLETA)
        # =====================================================================
        if st.session_state.visor_plan_activo:
            data = st.session_state.visor_plan_data
            idx_original = data['INDICE_ORIGINAL']
            
            c_back, c_tit = st.columns([1, 6])
            with c_back:
                if st.button("🔙 VOLVER", use_container_width=True):
                    st.session_state.visor_plan_activo = False
                    st.rerun()
            with c_tit:
                st.subheader(f"📖 Editando: {data['TEMA']}")

            texto_editado = st.text_area("Contenido:", value=data['CONTENIDO'], height=600)
            
            if st.button("💾 GUARDAR CAMBIOS (NUBE)", type="primary", use_container_width=True):
                try:
                    df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                    df_master.at[idx_original, 'CONTENIDO'] = texto_editado
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                    # Actualizar caché
                    st.session_state.cache_planes.at[idx_original, 'CONTENIDO'] = texto_editado
                    st.session_state.visor_plan_data['CONTENIDO'] = texto_editado
                    st.success("✅ Guardado.")
                except Exception as e: st.error(f"Error: {e}")

        # =====================================================================
        # MODO NORMAL (PESTAÑAS)
        # =====================================================================
        else:
            tab_bitacora, tab_planes, tab_evals = st.tabs(["📸 Bitácora", "🗓️ Planificaciones", "📊 Evaluaciones"])

            # --- PESTAÑA 1: BITÁCORA (CON LAS CARPETAS VISIBLES) ---
            with tab_bitacora:
                st.subheader("📸 Bitácora de Clases")
                opciones = ["📘 Portafolio General"]
                mapa_pensums = {}
                for i, row in mis_pensums.iterrows():
                    opciones.append(f"🟢 Pensum: {row['TITULO_PENSUM']}")
                    mapa_pensums[row['TITULO_PENSUM']] = row['CONTENIDO_FULL']
                seleccion = st.selectbox("Portafolio:", opciones)
                st.divider()

                if "General" in seleccion:
                    clases_general = mis_clases[(mis_clases['ID_BLOQUE'].isna()) | (mis_clases['ID_BLOQUE'].astype(str) == "0")].sort_values(by="FECHA", ascending=False)
                    if clases_general.empty: st.info("No hay bitácoras generales.")
                    else:
                        clases_general['MES'] = pd.to_datetime(clases_general['FECHA'], dayfirst=True, errors='coerce').dt.strftime('%B %Y')
                        for mes in clases_general['MES'].unique():
                            with st.expander(f"🗓️ {mes}", expanded=True):
                                for i, row in clases_general[clases_general['MES'] == mes].iterrows():
                                    renderizar_tarjeta(row, mis_evaluaciones)
                else:
                    # LÓGICA DE PENSUMS (CORREGIDA PARA MOSTRAR CARPETAS VACÍAS)
                    nombre_pensum = seleccion.replace("🟢 Pensum: ", "")
                    texto_full = mapa_pensums.get(nombre_pensum, "")
                    nombres_bloques = {}
                    import re
                    for line in texto_full.split('\n'):
                        match = re.search(r'(\d+)\.\s*BLOQUE:?\s*(.*)', line, re.IGNORECASE)
                        if match: nombres_bloques[int(match.group(1))] = match.group(2).strip()
                    
                    # Generamos SIEMPRE los bloques del 1 al 14 (o los que haya)
                    for num_bloque in range(1, 15):
                        titulo_bloque = nombres_bloques.get(num_bloque, "Tema Específico")
                        
                        # Filtramos las clases de este bloque
                        mis_clases['ID_BLOQUE_STR'] = mis_clases['ID_BLOQUE'].astype(str).str.replace(".0", "").str.strip()
                        clases_bloque = mis_clases[mis_clases['ID_BLOQUE_STR'] == str(num_bloque)].sort_values(by="FECHA", ascending=False)
                        
                        cantidad = len(clases_bloque)
                        # Icono cambia si tiene contenido o no, pero la carpeta SIEMPRE APARECE
                        icono = "📂" if cantidad > 0 else "📁"
                        estado_abierto = True if cantidad > 0 else False
                        
                        # AQUI ESTA LA CORRECCIÓN: Renderizamos el expander SIEMPRE
                        with st.expander(f"{icono} BLOQUE {num_bloque}: {titulo_bloque} ({cantidad})", expanded=estado_abierto):
                            if clases_bloque.empty:
                                st.caption("📭 Carpeta vacía. Esperando consolidación de actividad...")
                            else:
                                for i, row in clases_bloque.iterrows(): 
                                    renderizar_tarjeta(row, mis_evaluaciones)

            # --- PESTAÑA 2: PLANIFICACIONES (CON SWITCH Y CACHÉ) ---
            with tab_planes:
                st.subheader("🗓️ Gestión de Planificaciones")
                if mis_planes.empty: st.info("No hay planes guardados.")
                else:
                    mis_planes_sorted = mis_planes.sort_index(ascending=False)
                    for i, row in mis_planes_sorted.iterrows():
                        fecha = row['FECHA']
                        tema = row['TEMA']
                        contenido = row['CONTENIDO']
                        estado = str(row['ESTADO']).strip().upper() if 'ESTADO' in row else "GUARDADO"
                        es_activa = (estado == "ACTIVO")
                        
                        titulo_card = f"🟢 {fecha} | {tema} (ACTIVA)" if es_activa else f"⚪ {fecha} | {tema}"
                        
                        with st.expander(titulo_card, expanded=es_activa):
                            c_tog, c_visor, c_del = st.columns([2, 2, 1])
                            with c_tog:
                                if st.toggle("Activa", value=es_activa, key=f"tog_{i}"):
                                    if not es_activa:
                                        try:
                                            df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                                            df_master.loc[df_master['USUARIO'] == st.session_state.u['NOMBRE'], 'ESTADO'] = "GUARDADO"
                                            df_master.at[i, 'ESTADO'] = "ACTIVO"
                                            conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                                            # Actualizar caché manualmente para no recargar todo
                                            st.session_state.cache_planes.loc[st.session_state.cache_planes['USUARIO'] == st.session_state.u['NOMBRE'], 'ESTADO'] = "GUARDADO"
                                            st.session_state.cache_planes.at[i, 'ESTADO'] = "ACTIVO"
                                            st.toast("⚡ ACTIVADA")
                                            time.sleep(0.5)
                                            st.rerun()
                                        except: pass
                                else:
                                    if es_activa:
                                        try:
                                            df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                                            df_master.at[i, 'ESTADO'] = "GUARDADO"
                                            conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                                            st.session_state.cache_planes.at[i, 'ESTADO'] = "GUARDADO"
                                            st.rerun()
                                        except: pass
                            
                            with c_visor:
                                if st.button("📖 VISOR", key=f"v_{i}", use_container_width=True):
                                    st.session_state.visor_plan_activo = True
                                    row_d = row.to_dict(); row_d['INDICE_ORIGINAL'] = i
                                    st.session_state.visor_plan_data = row_d
                                    st.rerun()
                            
                            with c_del:
                                if st.button("🗑️", key=f"d_{i}"):
                                    try:
                                        df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                                        df_master = df_master.drop(index=i)
                                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                                        st.session_state.cache_planes = st.session_state.cache_planes.drop(index=i)
                                        st.rerun()
                                    except: pass

            # --- PESTAÑA 3: EVALUACIONES (USANDO CACHÉ = VELOCIDAD) ---
            with tab_evals:
                st.subheader("📊 Historial Académico")
                if mis_evaluaciones.empty:
                    st.info("No hay evaluaciones.")
                else:
                    lista_estudiantes = sorted(mis_evaluaciones['ESTUDIANTE'].dropna().unique())
                    # Selección segura con memoria
                    idx_sel = 0
                    if st.session_state.alumno_seleccionado_temp in lista_estudiantes:
                        idx_sel = lista_estudiantes.index(st.session_state.alumno_seleccionado_temp)
                    
                    seleccion_alumno = st.selectbox("👤 Selecciona un Estudiante:", lista_estudiantes, index=idx_sel)
                    st.session_state.alumno_seleccionado_temp = seleccion_alumno
                    
                    if seleccion_alumno:
                        df_alumno = mis_evaluaciones[mis_evaluaciones['ESTUDIANTE'] == seleccion_alumno].sort_values(by="FECHA", ascending=False)
                        
                        c_m1, c_m2 = st.columns([1, 2])
                        c_m1.metric("Registros", len(df_alumno))
                        with c_m2:
                            if st.button("✨ Generar Boletín (IA)", key="btn_bol_ia", use_container_width=True):
                                with st.spinner("Analizando..."):
                                    txt = ""
                                    for _, r in df_alumno.iterrows():
                                        txt += f"- {r['FECHA']}: {r.get('ANECDOTA','')} | {r.get('EVALUACION_IA','')}\n"
                                    st.session_state.resumen_alumno_ia = generar_respuesta([{"role":"user","content":f"Redacta un informe cualitativo para el boletín escolar de {seleccion_alumno} basado en: {txt}"}], 0.7)

                        if st.session_state.resumen_alumno_ia:
                            st.info("📄 Informe:")
                            st.write(st.session_state.resumen_alumno_ia)
                            if st.button("Cerrar"):
                                st.session_state.resumen_alumno_ia = ""
                                st.rerun()
                        
                        st.divider()
                        st.dataframe(df_alumno[['FECHA', 'ACTIVIDAD', 'ANECDOTA', 'EVALUACION_IA']], hide_index=True, use_container_width=True)
# =============================================================================
# PIE DE PÁGINA OFICIAL (v1.0)
# =============================================================================
st.markdown("---")
col_f1, col_f2 = st.columns([3, 1])
with col_f1:
    st.markdown("**© 2026 SUPER DOCENTE**")
    st.caption("Tecnología educativa hecha en La Concepción, Zulia.")
    st.caption("Desarrollado por: **Luis Atencio** (Bachiller Docente).")
with col_f2:
    try: 
        # Versión final para presentación
        st.caption(f"v1.0 | {ahora_ve().strftime('%I:%M %p')}")
    except: 
        st.caption("v1.0")
