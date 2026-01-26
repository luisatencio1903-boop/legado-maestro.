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
            "🏗️ GESTIÓN DE PROYECTOS Y PLANES",           
            "🧠 PLANIFICADOR INTELIGENTE",                
            "📜 PLANIFICADOR MINISTERIAL"
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
        # BOTÓN MAESTRO: FUSIÓN TOTAL + FORMATO FORZADO
        # =============================================================================
        if st.button("🚀 Generar Planificación Estructurada", type="primary"):
            
            # 1. VALIDACIONES (INTACTAS)
            if not rango or not notas:
                st.error("⚠️ Por favor ingrese el Lapso y el Tema.")
            elif is_pei and not perfil_alumno:
                st.error("⚠️ Para P.E.I. debe describir el perfil del alumno.")
            elif modalidad == "Taller de Educación Laboral (T.E.L.)" and not aula_especifica:
                st.error("⚠️ Especifique el área del Taller.")
            else:
                with st.spinner('Procesando Estructura, Normativa Legal y Espaciado...'):
                    
                    # A. VOCABULARIO Y TONO (INTACTO)
                    vocabulario_sugerido = ""
                    tono_redaccion = ""
                    if "Inicial" in modalidad:
                        tono_redaccion = "AFECTIVO, LÚDICO Y MATERNAL."
                        vocabulario_sugerido = "- INICIO: Cantamos, La ronda.\n- DESARROLLO: Rasgamos, Pintamos.\n- CIERRE: Canción de guardar."
                    elif "Taller" in modalidad:
                        tono_redaccion = "TÉCNICO, PRE-PROFESIONAL Y PRODUCTIVO."
                        vocabulario_sugerido = "- INICIO: Normas de seguridad.\n- DESARROLLO: Lijamos, Medimos, Sembramos.\n- CIERRE: Control de calidad."
                    elif "Aula Integrada" in modalidad or "U.P.E." in modalidad:
                        tono_redaccion = "PSICO-EDUCATIVO Y REMEDIAL."
                        vocabulario_sugerido = "- INICIO: Gimnasia cerebral.\n- DESARROLLO: Leemos, Escribimos.\n- CIERRE: Refuerzo positivo."
                    elif "Autismo" in modalidad or "C.A.I.P.A." in modalidad:
                        tono_redaccion = "ESTRUCTURADO Y VISUAL."
                        vocabulario_sugerido = "- INICIO: Agenda visual.\n- DESARROLLO: Clasificamos, Encajamos.\n- CIERRE: Guardado."
                    else: 
                        tono_redaccion = "SENSORIAL Y HÁBITOS."
                        vocabulario_sugerido = "- INICIO: Saludo.\n- DESARROLLO: Estimulación.\n- CIERRE: Aseo."

                    # B. PROYECTOS (INTACTO)
                    texto_instruccion_proyecto = ""
                    etiqueta_titulo_dinamica = "TÍTULO DE LA ACTIVIDAD"
                    
                    datos_proyecto = None
                    if 'PROYECTO_LOCAL' in st.session_state:
                        datos_proyecto = st.session_state['PROYECTO_LOCAL']
                    
                    if datos_proyecto is None:
                        try:
                            df_p = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=60)
                            user_p = df_p[df_p['USUARIO'] == st.session_state.u['NOMBRE']]
                            if not user_p.empty:
                                fila = user_p.iloc[0]
                                datos_proyecto = {
                                    'ACTIVO': str(fila['ACTIVO']).upper().strip(),
                                    'SERVICIO': fila['SERVICIO'],
                                    'NOMBRE_PA': fila['NOMBRE_PA'],
                                    'NOMBRE_PSP': fila['NOMBRE_PSP'],
                                    'FASE_ACTUAL': fila['FASE_ACTUAL'],
                                    'DIAS_PSP': str(fila['DIAS_PSP'])
                                }
                        except: datos_proyecto = None

                    if datos_proyecto and datos_proyecto.get('ACTIVO') == "TRUE":
                        servicio = datos_proyecto['SERVICIO']
                        pa = datos_proyecto['NOMBRE_PA']
                        psp = datos_proyecto['NOMBRE_PSP']
                        fase = datos_proyecto['FASE_ACTUAL']
                        dias_prod = datos_proyecto['DIAS_PSP']
                        
                        if "Taller" in servicio:
                            etiqueta_titulo_dinamica = "TÍTULO (P.A. o P.S.P.)"
                            texto_instruccion_proyecto = f"""
                            🚨 **PRIORIDAD: PROYECTO TALLER ACTIVO**
                            - P.S.P. (Taller): "{psp}" | P.A. (Aula): "{pa}"
                            - FASE: {fase} | DÍAS PRÁCTICOS: {dias_prod}
                            INSTRUCCIÓN: Si hoy es {dias_prod}, planifica PRÁCTICA DEL P.S.P. Si no, usa el P.A.
                            """
                        elif "Aula Integrada" in servicio or "U.P.E." in servicio:
                            etiqueta_titulo_dinamica = "LÍNEA DE ACCIÓN"
                            texto_instruccion_proyecto = f"""🚨 **MODO ATENCIÓN:** LÍNEA: "{pa}" | FASE: {fase}."""
                        else:
                            etiqueta_titulo_dinamica = "TÍTULO PROYECTO"
                            texto_instruccion_proyecto = f"""🚨 **MODO P.A.:** PROYECTO: "{pa}" | MOMENTO: {fase}."""
                    else:
                        texto_instruccion_proyecto = "NO HAY PROYECTO ACTIVO. Planifica basado en TEMA MANUAL."

                    # C. PROMPT CON ENCABEZADO LEGAL Y FORMATO ESTRICTO
                    st.session_state.temp_tema = f"{modalidad} - {notas}"
                    
                    # AQUÍ ESTÁ EL ENCABEZADO QUE PEDISTE
                    encabezado_legal = """
                    **PLANIFICACIÓN SUGERIDA POR SUPER DOCENTE 1.0**
                    *Sustentada en el Currículo Nacional Bolivariano y la Ley Orgánica de Educación (L.O.E.)*
                    ---------------------------------------------------
                    """
                    
                    prompt = f"""
                    ERES UN EXPERTO EN PLANIFICACIÓN EDUCATIVA VENEZOLANA.
                    CONTEXTO: {modalidad} {aula_especifica}. TEMA: {notas}.
                    PROYECTO: {texto_instruccion_proyecto}
                    TONO: {tono_redaccion}. VOCABULARIO: {vocabulario_sugerido}.
                    
                    🚨 **REGLA DE FORMATO VISUAL (INQUEBRANTABLE):**
                    ES OBLIGATORIO DEJAR UNA LÍNEA VACÍA ENTRE CADA PUNTO NUMERADO.
                    NO escribas todo en un solo párrafo. Separa visualmente el Inicio, Desarrollo y Cierre.
                    
                    ESTRUCTURA DE SALIDA REQUERIDA:
                    
                    {encabezado_legal}
                    
                    ### [DÍA Y FECHA]
                    
                    **1. {etiqueta_titulo_dinamica}:** [Nombre]
                    <br>
                    **2. COMPETENCIA TÉCNICA:** [Redacción]
                    <br>
                    **3. EXPLORACIÓN (Inicio):** [Actividad]
                    <br>
                    **4. DESARROLLO (Proceso):** [Actividad]
                    <br>
                    **5. REFLEXIÓN (Cierre):** [Actividad]
                    <br>
                    **6. ESTRATEGIAS:** [Técnicas]
                    <br>
                    **7. RECURSOS:** [Materiales]
                    ---------------------------------------------------
                    Genera la planificación para el lapso: {rango}.
                    """
                    
                    # 4. GENERACIÓN IA
                    respuesta_raw = generar_respuesta([
                        {"role":"system","content":INSTRUCCIONES_TECNICAS}, 
                        {"role":"user","content":prompt}
                    ], 0.6)
                    
                    # --- TRUCO DE PROGRAMADOR: FORZAR ESPACIOS SI LA IA FALLA ---
                    # Esto busca donde dice "**2." y le mete dos espacios antes a la fuerza
                    respuesta_formateada = respuesta_raw \
                        .replace("**1.", "\n\n**1.") \
                        .replace("**2.", "\n\n**2.") \
                        .replace("**3.", "\n\n**3.") \
                        .replace("**4.", "\n\n**4.") \
                        .replace("**5.", "\n\n**5.") \
                        .replace("**6.", "\n\n**6.") \
                        .replace("**7.", "\n\n**7.") \
                        .replace("### ", "\n\n\n### ") # Más espacio antes del día
                    
                    st.session_state.plan_actual = respuesta_formateada
                    st.rerun()

        # =============================================================================
        # 5. VISUALIZACIÓN
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
                                "FECHA": pd.Timestamp.now().strftime("%d/%m/%Y"), 
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
    # VISTA: AULA VIRTUAL (v13.0 - TRÍADA PEDAGÓGICA: INICIO, DESARROLLO, CIERRE)
    # -------------------------------------------------------------------------
    elif opcion == "🦸‍♂️ AULA VIRTUAL (Ejecución y Evaluación)":
        st.info("💡 **Centro de Operaciones:** Gestión de la clase (Inicio - Desarrollo - Cierre).")
        
        if 'modo_suplencia_activo' not in st.session_state:
            st.session_state.modo_suplencia_activo = False

        # 1. CONTEXTO
        st.markdown("### ⚙️ Contexto de la Clase")
        es_suplencia = st.checkbox("🦸 **Activar Modo Suplencia**", 
                                  value=st.session_state.modo_suplencia_activo,
                                  key="chk_suplencia_master")
        st.session_state.modo_suplencia_activo = es_suplencia
        
        if es_suplencia:
            lista_suplentes = [d for d in LISTA_DOCENTES if d != st.session_state.u['NOMBRE']]
            titular = st.selectbox("Seleccione Docente Titular:", lista_suplentes, key="av_titular_v13")
            st.warning(f"Modo Suplencia: Usando planificación de **{titular}**")
        else:
            titular = st.session_state.u['NOMBRE']
            st.success("Trabajando con tu planificación y alumnos.")

        # 2. PLAN ACTIVO
        pa = obtener_plan_activa_usuario(titular)
        if not pa:
            st.error(f"🚨 {titular} no tiene un plan activo.")
            st.stop()
            
        if 'av_titulo_hoy' not in st.session_state: st.session_state.av_titulo_hoy = ""
        if 'av_contexto_hoy' not in st.session_state: st.session_state.av_contexto_hoy = ""
        if 'temp_propuesta_ia' not in st.session_state: st.session_state.temp_propuesta_ia = ""

        # 3. PESTAÑAS (TRÍADA PEDAGÓGICA)
        # Organizamos las fotos según el momento de la clase
        tab1, tab2, tab3 = st.tabs(["🚀 Ejecución (Inicio/Desarrollo)", "📝 Evaluación", "🏁 Cierre (Reflexión)"])

        # --- PESTAÑA 1: EJECUCIÓN ---
        with tab1:
            dias_es = {"Monday":"Lunes", "Tuesday":"Martes", "Wednesday":"Miércoles", "Thursday":"Jueves", "Friday":"Viernes", "Saturday":"Sábado", "Sunday":"Domingo"}
            dia_hoy_nombre = dias_es.get(ahora_ve().strftime("%A"))
            
            clase_dia = extraer_actividad_del_dia(pa["CONTENIDO_PLAN"], dia_hoy_nombre)
            if clase_dia is None:
                st.warning(f"No hay actividad programada para hoy {dia_hoy_nombre}.")
                dia_m = st.selectbox("Seleccione día a ejecutar:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], key="av_manual_v13")
                clase_de_hoy = extraer_actividad_del_dia(pa["CONTENIDO_PLAN"], dia_m)
            else:
                clase_de_hoy = clase_dia

            st.subheader("📖 Guía de la Actividad")
            if clase_de_hoy:
                st.markdown(f'<div class="plan-box">{clase_de_hoy}</div>', unsafe_allow_html=True)
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
                            if len(texto_sucio) > 250: c_temp += "..."
                    st.session_state.temp_titulo_extract = t_temp
                    st.session_state.temp_contexto_extract = c_temp
                except:
                    st.session_state.temp_titulo_extract = "Actividad General"
                    st.session_state.temp_contexto_extract = clase_de_hoy[:150]
            else:
                st.error("Error al cargar plan.")

            st.divider()
            
            col_momento1, col_momento2 = st.columns(2)
            
            # --- FOTO 1: INICIO (EXPLORACIÓN) ---
            with col_momento1:
                st.markdown("#### 1. Inicio (Exploración)")
                st.caption("Conversatorio, instrucciones, ambiente.")
                if st.session_state.av_foto1 is None:
                    f1 = st.camera_input("Capturar Inicio", key="av_cam1_v13")
                    if f1 and st.button("📤 Subir Inicio", key="btn_save_f1_v13"):
                        u1 = subir_a_imgbb(f1)
                        if u1: st.session_state.av_foto1 = u1; st.rerun()
                else:
                    st.image(st.session_state.av_foto1, use_container_width=True, caption="✅ Inicio Cargado")
                    if st.button("♻️ Cambiar Inicio", key="reset_f1_v13"): st.session_state.av_foto1 = None; st.rerun()

            # --- FOTO 2: DESARROLLO (PRÁCTICA) ---
            with col_momento2:
                st.markdown("#### 2. Desarrollo (Práctica)")
                st.caption("Estudiantes trabajando, manos a la obra.")
                if st.session_state.av_foto2 is None:
                    f2 = st.camera_input("Capturar Desarrollo", key="av_cam2_v13")
                    if f2 and st.button("📤 Subir Desarrollo", key="btn_save_f2_v13"):
                        u2 = subir_a_imgbb(f2)
                        if u2: st.session_state.av_foto2 = u2; st.rerun()
                else:
                    st.image(st.session_state.av_foto2, use_container_width=True, caption="✅ Desarrollo Cargado")
                    if st.button("♻️ Cambiar Desarr.", key="reset_f2_v13"): st.session_state.av_foto2 = None; st.rerun()
            
            # PEI EXPRESS
            st.divider()
            with st.expander("🧩 Adaptación P.E.I. Express (Opcional)"):
                alums = df_mat_global[df_mat_global['DOCENTE_TITULAR'] == titular]['NOMBRE_ALUMNO'].tolist()
                c1, c2 = st.columns(2)
                with c1: al_a = st.selectbox("Alumno:", ["(Seleccionar)"] + sorted(alums), key="av_pei_al_v13")
                with c2: ctx_a = st.text_input("Situación:", placeholder="Ej: Inquieto...", key="av_pei_ctx_v13")
                if st.button("💡 Estrategia IA", key="btn_av_ia_v13"):
                    if al_a != "(Seleccionar)":
                        datos_al = df_mat_global[df_mat_global['NOMBRE_ALUMNO'] == al_a]
                        diag = datos_al['DIAGNOSTICO'].iloc[0] if not datos_al.empty else "N/A"
                        p_pei = f"PLAN: {clase_de_hoy}. ALUMNO: {al_a} ({diag}). CRISIS: {ctx_a}. Dame una estrategia rápida."
                        st.markdown(f'<div class="eval-box">{generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":p_pei}], 0.5)}</div>', unsafe_allow_html=True)


        # --- PESTAÑA 2: EVALUACIÓN ---
        with tab2:
            st.subheader("📝 Evaluación Individual")
            alums = df_mat_global[df_mat_global['DOCENTE_TITULAR'] == titular]['NOMBRE_ALUMNO'].tolist()
            if not alums:
                st.warning("No hay alumnos.")
            else:
                e_sel = st.selectbox("Estudiante:", sorted(alums), key="av_eval_al_v13")
                
                if st.button("🔍 Cargar Datos de Hoy", key="btn_load_act_v13", type="primary"):
                    st.session_state.av_titulo_hoy = st.session_state.get('temp_titulo_extract', 'Actividad Manual')
                    st.session_state.av_contexto_hoy = st.session_state.get('temp_contexto_extract', 'Sin contexto.')
                    st.session_state.temp_propuesta_ia = "" 
                    st.rerun() 
                
                st.caption(f"Actividad: {st.session_state.av_titulo_hoy}")
                o_eval = st.text_area("Observación Anecdótica:", placeholder="¿Qué logró el estudiante hoy?", key="av_eval_obs_v13")
                
                if o_eval and st.button("✨ Mejorar Redacción (IA)", key="btn_sugerir_ia_v13"):
                    with st.spinner("Redactando..."):
                        p_ev = f"Alumno: {e_sel}. Actividad: {st.session_state.av_titulo_hoy}. Obs: {o_eval}. Contexto: {st.session_state.av_contexto_hoy}. Transforma a registro técnico descriptivo."
                        st.session_state.temp_propuesta_ia = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":p_ev}], 0.5)
                
                if st.session_state.temp_propuesta_ia:
                    st.info("Propuesta IA:")
                    st.markdown(f'<div class="eval-box">{st.session_state.temp_propuesta_ia}</div>', unsafe_allow_html=True)

                if st.button("💾 Guardar Nota", type="primary", key="btn_save_final_v13"):
                    if o_eval and st.session_state.av_titulo_hoy:
                        nota_final = st.session_state.temp_propuesta_ia if st.session_state.temp_propuesta_ia else o_eval
                        df_ev = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                        nueva_n = pd.DataFrame([{
                            "FECHA": ahora_ve().strftime("%d/%m/%Y"), 
                            "USUARIO": st.session_state.u['NOMBRE'], 
                            "DOCENTE_TITULAR": titular, 
                            "ESTUDIANTE": e_sel, 
                            "ACTIVIDAD": st.session_state.av_titulo_hoy, 
                            "ANECDOTA": o_eval, 
                            "EVALUACION_IA": nota_final, 
                            "PLANIFICACION_ACTIVA": pa['RANGO']
                        }])
                        conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, nueva_n], ignore_index=True))
                        st.success("✅ Nota Guardada")
                        st.session_state.temp_propuesta_ia = ""
                        time.sleep(1); st.rerun()
                    else: st.error("Faltan datos.")

        # --- PESTAÑA 3: CIERRE (FOTO 3 + REFLEXIÓN) ---
        with tab3:
            st.subheader("🏁 Cierre de Jornada")
            
            hoy_check = ahora_ve().strftime("%d/%m/%Y")
            df_check = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
            ya_cerro = not df_check[(df_check['USUARIO'] == st.session_state.u['NOMBRE']) & (df_check['FECHA'] == hoy_check)].empty
            
            if ya_cerro:
                st.success("✅ Jornada de hoy ya consolidada.")
                if st.button("🏠 Volver al Inicio"):
                    st.session_state.pagina_actual = "HOME"; st.rerun()
            else:
                # --- FOTO 3: CIERRE ---
                st.markdown("#### 3. Evidencia de Cierre (Producto/Socialización)")
                st.caption("Producto terminado, limpieza o despedida.")
                
                if st.session_state.av_foto3 is None:
                    f3 = st.camera_input("Capturar Cierre", key="av_cam3_v13")
                    if f3 and st.button("📤 Subir Cierre", key="btn_save_f3_v13"):
                        u3 = subir_a_imgbb(f3)
                        if u3: st.session_state.av_foto3 = u3; st.rerun()
                else:
                    st.image(st.session_state.av_foto3, width=200, caption="✅ Cierre Cargado")
                    if st.button("♻️ Cambiar Cierre", key="reset_f3_v13"): st.session_state.av_foto3 = None; st.rerun()

                st.divider()
                st.session_state.av_resumen = st.text_area("Resumen Pedagógico del Día:", value=st.session_state.av_resumen, key="av_res_v13", height=100)
                
                # VALIDACIÓN DE 3 FOTOS
                if st.button("🚀 CONSOLIDAR JORNADA", type="primary", key="btn_fin_v13"):
                    # Validación estricta: Faltan fotos?
                    faltan = []
                    if not st.session_state.av_foto1: faltan.append("Inicio")
                    if not st.session_state.av_foto2: faltan.append("Desarrollo")
                    if not st.session_state.av_foto3: faltan.append("Cierre")
                    
                    if faltan:
                        st.error(f"⚠️ Faltan evidencias de: {', '.join(faltan)}")
                    elif not st.session_state.av_resumen:
                        st.error("⚠️ Escribe el resumen pedagógico.")
                    else:
                        with st.spinner("Guardando en Bitácora..."):
                            df_ej = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                            # UNIMOS LAS 3 FOTOS
                            fotos_str = f"{st.session_state.av_foto1}|{st.session_state.av_foto2}|{st.session_state.av_foto3}"
                            
                            nueva_f = pd.DataFrame([{
                                "FECHA": hoy_check, 
                                "USUARIO": st.session_state.u['NOMBRE'], 
                                "DOCENTE_TITULAR": titular, 
                                "ACTIVIDAD_TITULO": st.session_state.av_titulo_hoy or "Actividad General", 
                                "EVIDENCIA_FOTO": fotos_str, 
                                "RESUMEN_LOGROS": st.session_state.av_resumen, 
                                "ESTADO": "CULMINADA", 
                                "PUNTOS": 5
                            }])
                            conn.update(spreadsheet=URL_HOJA, worksheet="EJECUCION", data=pd.concat([df_ej, nueva_f], ignore_index=True))
                            
                            # Limpieza total
                            st.session_state.av_foto1 = None
                            st.session_state.av_foto2 = None
                            st.session_state.av_foto3 = None
                            st.session_state.av_resumen = ""
                            st.balloons()
                            st.success("✅ ¡Jornada Exitosa! 3 Evidencias Guardadas.")
                            time.sleep(2); st.session_state.pagina_actual = "HOME"; st.rerun()
# -------------------------------------------------------------------------
    # VISTA: GESTIÓN DE PROYECTOS (v11.6 - MENÚ DINÁMICO REAL)
    # -------------------------------------------------------------------------
    elif opcion == "🏗️ GESTIÓN DE PROYECTOS Y PLANES":
        st.header("🏗️ Configuración de Proyectos y Planes")
        st.markdown("Defina su hoja de ruta. El sistema adaptará los menús según su **Modalidad**.")

        # 1. LEER DATOS (Con Caché y Prioridad Local)
        try:
            df_proy = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=60)
            mi_proy = df_proy[df_proy['USUARIO'] == st.session_state.u['NOMBRE']]
        except: mi_proy = pd.DataFrame()

        # Variables por defecto
        d_servicio = "Taller de Educación Laboral (T.E.L.)"
        d_pa = ""
        d_psp = ""
        d_fase_full = ""
        d_dias = []
        d_activo = False

        # Cargar de Nube
        if not mi_proy.empty:
            fila = mi_proy.iloc[0]
            d_servicio = fila['SERVICIO'] if pd.notna(fila['SERVICIO']) else d_servicio
            d_pa = fila['NOMBRE_PA'] if pd.notna(fila['NOMBRE_PA']) else ""
            d_psp = fila['NOMBRE_PSP'] if pd.notna(fila['NOMBRE_PSP']) else ""
            d_fase_full = fila['FASE_ACTUAL'] if pd.notna(fila['FASE_ACTUAL']) else ""
            d_dias = str(fila['DIAS_PSP']).split(",") if pd.notna(fila['DIAS_PSP']) and fila['DIAS_PSP'] else []
            d_activo = True if str(fila['ACTIVO']) == "TRUE" else False

        # Cargar de Memoria Local (Prioridad)
        if 'PROYECTO_LOCAL' in st.session_state:
            local = st.session_state['PROYECTO_LOCAL']
            d_servicio = local.get('SERVICIO', d_servicio)
            d_pa = local.get('NOMBRE_PA', d_pa)
            d_psp = local.get('NOMBRE_PSP', d_psp)
            d_fase_full = local.get('FASE_ACTUAL', d_fase_full)
            if local.get('DIAS_PSP'): d_dias = local['DIAS_PSP'].split(",")
            d_activo = True if str(local.get('ACTIVO')).upper() == "TRUE" else False

        # =====================================================================
        # PASO 1: SELECTOR DE SERVICIO (FUERA DEL FORMULARIO PARA SER DINÁMICO)
        # =====================================================================
        st.subheader("1. Identidad del Servicio")
        
        # Calcular índice inicial basado en la memoria
        idx_serv = 0
        if "Inicial" in d_servicio: idx_serv = 1
        elif "Aula Integrada" in d_servicio: idx_serv = 2
        
        # ESTE SELECTBOX AHORA REFRESCA LA PÁGINA AL CAMBIAR
        servicio_seleccionado = st.selectbox(
            "¿A qué Modalidad o Servicio pertenece usted?",
            ["Taller de Educación Laboral (T.E.L.)", "Educación Inicial / I.E.E. (Escuela)", "Aula Integrada / U.P.E. / C.A.I.P.A."],
            index=idx_serv,
            key="selector_servicio_dinamico"
        )
        
        # Detectamos si es taller AHORA MISMO (Visualmente)
        es_taller_visual = "Taller" in servicio_seleccionado
        es_especial_visual = "Aula Integrada" in servicio_seleccionado

        st.divider()

        # =====================================================================
        # PASO 2: EL FORMULARIO (ADAPTABLE)
        # =====================================================================
        with st.form("form_proyecto_maestro"):
            st.subheader("2. Datos del Plan")
            
            # A. CAMPO PROYECTO DE APRENDIZAJE (Etiqueta Dinámica)
            label_pa = "Nombre del Proyecto de Aprendizaje (P.A.):"
            placeholder_pa = "Ej: Conociendo los animales..."
            
            if es_especial_visual:
                label_pa = "Nombre de la Línea de Acción / P.A.I.:"
                placeholder_pa = "Ej: Superando barreras de lecto-escritura..."
            elif es_taller_visual:
                label_pa = "Nombre del Proyecto de Aprendizaje (P.A.) - Aula:"
                placeholder_pa = "Ej: Valores para el Trabajo Liberador..."
            
            nombre_pa = st.text_input(label_pa, value=d_pa, placeholder=placeholder_pa)

            # B. CAMPOS EXCLUSIVOS DE TALLER (Solo aparecen si es Taller)
            nombre_psp = ""
            dias_psp = []
            
            if es_taller_visual:
                st.info("🛠️ **Configuración de Taller Laboral:**")
                nombre_psp = st.text_input("Nombre del Proyecto Socio-Productivo (P.S.P.) - Taller:", 
                                         value=d_psp, 
                                         placeholder="Ej: Vivero Ornamental...")
                
                dias_psp = st.multiselect("Días de Práctica (Con Instructor):", 
                                        ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], 
                                        default=[d.strip() for d in d_dias if d.strip()])
            else:
                # Si no es taller, guardamos "N/A" internamente
                nombre_psp = "N/A"

            # C. FASE (Cronología)
            st.markdown("---")
            st.subheader("3. Etapa del Proyecto")
            
            opciones_fases = [
                "Fase 1: Diagnóstico, Sensibilización y Selección (Inicio)",
                "Fase 2: Formación Teórica y Planificación (Preparación)",
                "Fase 3: Ejecución, Producción y Práctica (Desarrollo)",
                "Fase 4: Cierre, Evaluación y Comercialización (Final)"
            ]
            
            # Recuperar fase guardada
            index_fase = 0
            detalle_previo = d_fase_full
            for i, op in enumerate(opciones_fases):
                if op.split(":")[0] in d_fase_full:
                    index_fase = i
                    detalle_previo = d_fase_full.replace(op, "").replace(" || Detalle: ", "").strip()
                    break
            
            fase_select = st.selectbox("Seleccione la Etapa Macro:", opciones_fases, index=index_fase)
            detalle_fase = st.text_area("Detalle específico de la semana:", value=detalle_previo)

            st.divider()

            # D. ACTIVACIÓN
            col_act, col_info = st.columns([1, 2])
            with col_act:
                activo = st.toggle("✅ ACTIVAR PROYECTO", value=d_activo)
            with col_info:
                if activo: st.caption("Estado: **ACTIVO**. La IA usará estos datos.")
                else: st.caption("Estado: **PAUSADO**.")

            # BOTÓN GUARDAR
            if st.form_submit_button("💾 Guardar Configuración"):
                fase_final = f"{fase_select} || Detalle: {detalle_fase}"
                str_dias = ",".join(dias_psp) if es_taller_visual else ""
                str_activo = "TRUE" if activo else "FALSE"
                
                try:
                    with st.spinner("Actualizando perfil..."):
                        # Lectura de seguridad
                        df_seg = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=0)
                        
                        if df_seg is None or df_seg.empty:
                            df_clean = pd.DataFrame(columns=["USUARIO", "SERVICIO", "NOMBRE_PA", "NOMBRE_PSP", "FASE_ACTUAL", "DIAS_PSP", "ACTIVO"])
                        else:
                            df_clean = df_seg[df_seg['USUARIO'] != st.session_state.u['NOMBRE']]
                        
                        nuevo_reg = pd.DataFrame([{
                            "USUARIO": st.session_state.u['NOMBRE'],
                            "SERVICIO": servicio_seleccionado, # Usamos el del selector externo
                            "NOMBRE_PA": nombre_pa,
                            "NOMBRE_PSP": nombre_psp,
                            "FASE_ACTUAL": fase_final,
                            "DIAS_PSP": str_dias,
                            "ACTIVO": str_activo
                        }])
                        
                        conn.update(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", data=pd.concat([df_clean, nuevo_reg], ignore_index=True))
                        
                        # Actualizar Memoria Local
                        st.session_state['PROYECTO_LOCAL'] = {
                            'ACTIVO': str_activo,
                            'SERVICIO': servicio_seleccionado,
                            'NOMBRE_PA': nombre_pa,
                            'NOMBRE_PSP': nombre_psp,
                            'FASE_ACTUAL': fase_final,
                            'DIAS_PSP': str_dias
                        }
                        
                        st.success("✅ Configuración guardada.")
                        time.sleep(1)
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
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
# =========================================================================
    # SECCIÓN: MI ARCHIVO PEDAGÓGICO (V1.0 FINAL - CON GENERADOR DE INFORMES)
    # =========================================================================
    elif opcion == "📂 Mi Archivo Pedagógico":
        st.header(f"📂 Archivo Pedagógico de {st.session_state.u['NOMBRE']}")
        
        try:
            # 1. CARGA DE DATOS INTELIGENTE (TTL=60)
            df_total_planes = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=60)
            df_ejecucion = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=60)
            df_evaluaciones = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=60)
            
            # 2. CREACIÓN DE PESTAÑAS
            tab_archivo, tab_consolidados, tab_historial_ev = st.tabs([
                "📝 Mis Planificaciones", 
                "📚 Bitácora (3 Momentos)", 
                "📊 Historial Expediente"
            ])

            # --- PESTAÑA 1: GESTIÓN DE PLANES ---
            with tab_archivo:
                col_filtros, col_backup = st.columns([3, 1])
                with col_filtros:
                    modo_suplencia_arch = st.checkbox("🦸 **Modo Suplencia**", key="check_supl_master")
                    if modo_suplencia_arch:
                        usuario_a_consultar = st.selectbox("Ver archivo de:", LISTA_DOCENTES, key="sel_doc_master")
                        st.warning(f"Gestionando archivo de: **{usuario_a_consultar}**")
                    else:
                        usuario_a_consultar = st.session_state.u['NOMBRE']
                        st.caption("Gestionando tu propio archivo.")

                with col_backup:
                    mis_datos_raw = df_total_planes[df_total_planes['USUARIO'] == st.session_state.u['NOMBRE']]
                    if not mis_datos_raw.empty:
                        csv_data = mis_datos_raw.to_csv(index=False).encode('utf-8')
                        st.download_button(label="📥 Respaldo CSV", data=csv_data, file_name="Mis_Planes.csv", mime="text/csv")

                st.divider()

                pa = obtener_plan_activa_usuario(usuario_a_consultar)
                if pa:
                    st.success(f"📌 **PLAN ACTIVO ACTUAL:** {pa['RANGO']}")
                    if st.button("Desactivar Plan", key="btn_des_master"): 
                        desactivar_plan_activa(usuario_a_consultar)
                        st.cache_data.clear()
                        st.rerun()
                else: 
                    st.info(f"⚠️ {usuario_a_consultar} no tiene un plan activo en este momento.")

                st.markdown("---")

                mis_p = df_total_planes[df_total_planes['USUARIO'] == usuario_a_consultar]
                if mis_p.empty: 
                    st.warning("📭 No se encontraron planes guardados.")
                else:
                    for i, fila in mis_p.iloc[::-1].iterrows():
                        es_este_activo = (pa['CONTENIDO_PLAN'] == fila['CONTENIDO']) if pa else False
                        titulo = f"{'⭐ ACTIVO | ' if es_este_activo else ''}📅 {fila['FECHA']} | {str(fila['TEMA'])[:40]}..."
                        
                        with st.expander(titulo):
                            contenido_editado = st.text_area("Editar Plan:", value=fila["CONTENIDO"], height=250, key=f"edit_{i}")
                            c_save, c_act, c_del = st.columns(3)
                            
                            if contenido_editado != fila["CONTENIDO"]:
                                if c_save.button("💾 Guardar", key=f"save_{i}"):
                                    df_total_planes.at[i, 'CONTENIDO'] = contenido_editado
                                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_total_planes)
                                    st.cache_data.clear()
                                    st.toast("Plan actualizado.")
                                    time.sleep(1); st.rerun()
                            
                            if not es_este_activo:
                                if c_act.button("📌 Activar", key=f"act_{i}"):
                                    establecer_plan_activa(usuario_a_consultar, str(i), contenido_editado, fila['FECHA'], "Aula")
                                    st.cache_data.clear()
                                    st.toast("¡Plan Activado!")
                                    time.sleep(1); st.rerun()
                            
                            if not modo_suplencia_arch:
                                if c_del.button("🗑️ Borrar", key=f"del_plan_{i}"):
                                    df_new = df_total_planes.drop(i)
                                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_new)
                                    st.cache_data.clear()
                                    st.toast("Plan eliminado.")
                                    time.sleep(1); st.rerun()

            # --- PESTAÑA 2: BITÁCORA (3 FOTOS) ---
            with tab_consolidados:
                st.subheader("📚 Bitácora de Clases (Inicio - Desarrollo - Cierre)")
                mis_logros = df_ejecucion[df_ejecucion['USUARIO'] == st.session_state.u['NOMBRE']].copy()
                
                if mis_logros.empty:
                    st.info("No hay registros en la bitácora.")
                else:
                    try:
                        mis_logros['FECHA_DT'] = pd.to_datetime(mis_logros['FECHA'], dayfirst=True, errors='coerce')
                        mis_logros = mis_logros.sort_values('FECHA_DT', ascending=False)
                    except: pass

                    for i, (_, logro) in enumerate(mis_logros.iterrows()):
                        with st.expander(f"🗓️ {logro['FECHA']} | {logro['ACTIVIDAD_TITULO']}"):
                            fotos = str(logro['EVIDENCIA_FOTO']).split('|')
                            c1, c2, c3 = st.columns(3)
                            
                            with c1:
                                if len(fotos) > 0 and fotos[0] not in ["-", "None"]: st.image(fotos[0], use_container_width=True, caption="1. Inicio")
                            with c2:
                                if len(fotos) > 1 and fotos[1] not in ["-", "None"]: st.image(fotos[1], use_container_width=True, caption="2. Desarrollo")
                            with c3:
                                if len(fotos) > 2 and fotos[2] not in ["-", "None"]: st.image(fotos[2], use_container_width=True, caption="3. Cierre")
                            
                            st.info(f"**Resumen:** {logro['RESUMEN_LOGROS']}")
                            
                            if st.button("🧠 Analizar Pedagogía (IA)", key=f"ia_bit_{i}"):
                                with st.spinner("Analizando momentos de la clase..."):
                                    prompt = f"Analiza esta clase: {logro['RESUMEN_LOGROS']}. Evalúa si se cumplieron Inicio, Desarrollo y Cierre."
                                    try:
                                        res = generar_respuesta([{"role":"user","content":prompt}])
                                        st.success(res)
                                    except: st.error("Error IA")
                            
                            st.divider()
                            if st.button("🗑️ Eliminar Registro", key=f"del_bit_{i}"):
                                df_new = df_ejecucion.drop(logro.name)
                                conn.update(spreadsheet=URL_HOJA, worksheet="EJECUCION", data=df_new)
                                st.cache_data.clear()
                                st.rerun()

            # --- PESTAÑA 3: EXPEDIENTE ESTUDIANTIL (CON EL BOTÓN DE INFORME RECUPERADO) ---
            with tab_historial_ev:
                st.subheader("📊 Expediente Estudiantil (Edición)")
                mis_alumnos_data = df_evaluaciones[df_evaluaciones['DOCENTE_TITULAR'] == st.session_state.u['NOMBRE']]
                
                if mis_alumnos_data.empty:
                    st.info("No hay evaluaciones registradas.")
                else:
                    lista = sorted(mis_alumnos_data['ESTUDIANTE'].unique())
                    alumno_sel = st.selectbox("Seleccione Alumno:", lista, key="sel_exp_master")
                    registros = mis_alumnos_data[mis_alumnos_data['ESTUDIANTE'] == alumno_sel]
                    
                    # --- AQUÍ ESTÁ EL BOTÓN DE INFORME RECUPERADO ---
                    if not registros.empty:
                        st.info(f"Notas encontradas: {len(registros)}")
                        
                        if st.button(f"🤖 Generar Informe Evolutivo de {alumno_sel}", type="primary"):
                            with st.spinner(f"Analizando historial de {alumno_sel} según modalidad..."):
                                # Recopilar todas las notas
                                historial_texto = "\n".join([f"- {r['FECHA']}: {r['EVALUACION_IA']}" for _, r in registros.iterrows()])
                                
                                # Prompt Específico que respeta el servicio del docente
                                prompt_informe = f"""
                                ACTÚA COMO UN DOCENTE ESPECIALISTA DE VENEZUELA.
                                REDACTA UN INFORME PEDAGÓGICO DESCRIPTIVO (CUALITATIVO).
                                
                                ALUMNO: {alumno_sel}
                                DOCENTE: {st.session_state.u['NOMBRE']}
                                HISTORIAL DE NOTAS:
                                {historial_texto}
                                
                                INSTRUCCIONES:
                                1. Analiza el progreso del estudiante basándote SOLO en las notas suministradas.
                                2. Usa terminología de Educación Especial (Potencialidades, Necesidades, Logros).
                                3. Estructura: Introducción, Avances Significativos, Recomendaciones.
                                """
                                resultado = generar_respuesta([
                                    {"role":"system", "content": INSTRUCCIONES_TECNICAS},
                                    {"role":"user", "content": prompt_informe}
                                ], 0.7)
                                
                                st.markdown(f'<div class="eval-box"><h3>📄 Informe Pedagógico</h3>{resultado}</div>', unsafe_allow_html=True)
                    
                    st.divider()

                    # Listado de notas individuales
                    for _, fila in registros.iloc[::-1].iterrows():
                        with st.expander(f"📅 {fila['FECHA']} | {fila['USUARIO']}"):
                            st.write(fila['EVALUACION_IA'])
                            st.caption(f"Original: {fila.get('ANECDOTA', '-')}")
                            
                            st.divider()
                            c_txt, c_btn = st.columns([0.6, 0.4])
                            with c_txt: st.caption("⚠️ **Zona de Peligro**")
                            with c_btn:
                                if st.button("🗑️ ELIMINAR NOTA", key=f"del_exp_{fila.name}", type="primary"):
                                    df_new = df_evaluaciones.drop(fila.name)
                                    conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=df_new)
                                    st.cache_data.clear()
                                    st.success("¡Eliminado!")
                                    time.sleep(1); st.rerun()

        except Exception as e:
            st.error(f"Error general en el módulo de Archivo: {e}")

    # =========================================================================
    # SECCIÓN: RECURSOS EXTRA (RECUPERADOS)
    # =========================================================================
    elif opcion == "🌟 Mensaje Motivacional":
        st.header("🌟 Dosis de Ánimo Docente")
        st.info("Un espacio para recargar energías.")
        if st.button("✨ Recibir Mensaje de Aliento", use_container_width=True):
            with st.spinner("Conectando con la inspiración..."):
                prompt = "Escribe una frase motivadora, corta y emotiva para un docente de Educación Especial en Venezuela que trabaja con el corazón a pesar de las dificultades."
                res = generar_respuesta([{"role":"user","content":prompt}], 0.8)
                st.success(f"🗣️ {res}")

    elif opcion == "💡 Ideas de Actividades":
        st.header("💡 Generador de Estrategias")
        st.markdown("¿Te quedaste sin ideas? Pide sugerencias rápidas.")
        
        tema = st.text_input("¿Qué tema quieres trabajar?", placeholder="Ej: La Siembra, Valores, Higiene...")
        if st.button("🎲 Generar 3 Ideas", type="primary") and tema:
            with st.spinner("Diseñando actividades vivenciales..."):
                prompt = f"Dame 3 actividades vivenciales, cortas y con recursos de provecho para estudiantes de Educación Especial sobre: {tema}."
                res = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":prompt}], 0.7)
                st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

    elif opcion == "❓ Consultas Técnicas":
        st.header("❓ Asesor Pedagógico IA")
        st.markdown("Consulta dudas sobre la L.O.E., Conceptualización o Estrategias.")
        
        consulta = st.text_area("Escribe tu duda pedagógica:", placeholder="Ej: ¿Cómo evaluar cualitativamente en el Taller Laboral?")
        if st.button("🔍 Consultar al Experto") and consulta:
            with st.spinner("Analizando normativa y pedagogía..."):
                res = generar_respuesta([{"role":"system","content":INSTRUCCIONES_TECNICAS},{"role":"user","content":consulta}], 0.4)
                st.info(res)

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
