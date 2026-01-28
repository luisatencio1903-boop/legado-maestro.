# =============================================================================
# CEREBRO NÚCLEO - SUPER DOCENTE 2.0 (ACTUALIZADO)
# Función: Dispatcher de Inteligencia y Selector de Contexto Dinámico
# =============================================================================

import streamlit as st
from groq import Groq
# Importación de los especialistas
from cerebros import tel, caipa, ieeb, aula_integrada, upe, inicial

# --- CLIENTE IA (GROQ) ---
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        MODELO = "llama-3.3-70b-versatile"
    else:
        client = None
except:
    client = None

def obtener_instrucciones_globales():
    """ADN de Identidad y Filtros de Ética de SUPER DOCENTE 2.0"""
    return """
    IDENTIDAD: ERES "SUPER DOCENTE 2.0". 
    Creado por el Bachiller Luis Atencio, zuliano y lossadeño. Herramienta 100% venezolana.
    FILTRO ÉTICO: Educación laica y apolítica. PROHIBIDO emitir opiniones sobre política o religión.
    FORMATO: Usa negritas para títulos y doble espacio entre secciones.
    """

def generar_respuesta(input_data, temperatura=0.6):
    """
    FUNCIÓN MAESTRA: Soporta tanto el Chat (Aula Virtual) como la Planificación.
    input_data: Puede ser una lista de mensajes (chat) o un string (prompt único).
    """
    if not client: return "Error: Cliente IA no configurado en Secrets."
    
    try:
        # Detectar si recibimos un historial de chat (lista) o un prompt directo (string)
        if isinstance(input_data, list):
            mensajes_finales = input_data
        else:
            mensajes_finales = [{"role": "system", "content": input_data}]

        completion = client.chat.completions.create(
            messages=mensajes_finales,
            model=MODELO,
            temperature=temperatura
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error de conexión con el cerebro IA: {e}"

def procesar_planificacion_v2(modalidad, dia_nombre, config_db, tema_usuario):
    """
    Motor lógico que selecciona el cerebro y el contexto (PA/PSP/Pensum)
    config_db: Diccionario con los datos de la base de datos.
    """
    
    # 1. IDENTIFICAR EL CEREBRO ESPECIALISTA
    if "Taller" in modalidad or "T.E.L." in modalidad:
        especialista = tel
    elif "Instituto" in modalidad or "I.E.E.B." in modalidad:
        especialista = ieeb
    elif "Autismo" in modalidad or "C.A.I.P.A." in modalidad:
        especialista = caipa
    elif "Aula Integrada" in modalidad:
        especialista = aula_integrada
    elif "Unidad" in modalidad or "U.P.E." in modalidad:
        especialista = upe
    else:
        especialista = inicial

    # 2. LÓGICA DE SELECCIÓN DE CONTEXTO
    contexto_inyectado = ""
    tipo_actividad = ""

    if "Taller" in modalidad or "T.E.L." in modalidad:
        if config_db.get('pa_switch') and dia_nombre in config_db.get('pa_dias', []):
            contexto_inyectado = f"CONTEXTO PROYECTO DE AULA (TEORÍA): {config_db.get('pa_texto')}"
            tipo_actividad = "Formación en Aula"
        elif config_db.get('psp_switch') and dia_nombre in config_db.get('psp_dias', []):
            contexto_inyectado = f"CONTEXTO PROYECTO SOCIO-PRODUCTIVO (PRÁCTICA): {config_db.get('psp_texto')}"
            tipo_actividad = "Ejecución de Taller (Enfoque Capataz/Supervisor)"
        elif config_db.get('pensum_switch'):
            contexto_inyectado = f"CONTEXTO PENSUM TÉCNICO DE OFICIO: {config_db.get('pensum_contenido')}"
            tipo_actividad = "Formación Técnica de Oficio"
        else:
            contexto_inyectado = "Enfoque general de formación para el trabajo."
            tipo_actividad = "Habilidades Laborales"
    else:
        if config_db.get('pa_switch') and dia_nombre in config_db.get('pa_dias', []):
            contexto_inyectado = f"CONTEXTO PROYECTO DE AULA: {config_db.get('pa_texto')}"
            tipo_actividad = "Actividad de Proyecto"
        else:
            contexto_inyectado = "Enfoque en Autovalimiento y Habilidades Adaptativas."
            tipo_actividad = "Actividad Curricular General"

    # 3. ENSAMBLAJE DEL PROMPT FINAL
    prompt_maestro = f"""
    {obtener_instrucciones_globales()}
    {especialista.obtener_prompt()}
    
    --- CONTEXTO OPERATIVO ---
    MODALIDAD SELECCIONADA: {modalidad}
    DÍA DE LA CLASE: {dia_nombre}
    TIPO DE JORNADA: {tipo_actividad}
    CONTEXTO PEDAGÓGICO: {contexto_inyectado}
    TEMA DEL DOCENTE: {tema_usuario}
    
    --- INSTRUCCIÓN FINAL ---
    Planifica siguiendo la estructura de 7 puntos (Título, Competencia, Inicio, Desarrollo, Cierre, Estrategias, Recursos).
    RECUERDA: {especialista.REGLAS_DE_ORO}
    """

    # 4. LLAMADA A LA IA USANDO LA FUNCIÓN UNIFICADA
    return generar_respuesta(prompt_maestro)
