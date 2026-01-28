# =============================================================================
# CEREBRO NÚCLEO - SUPER DOCENTE 2.0
# Funcción: Dispatcher de Inteligencia y Selector de Contexto Dinámico
# =============================================================================

import streamlit as st
from groq import Groq
from cerebros import tel, caipa, ieeb, aula_integrada, upe, inicial

# --- CLIENTE IA (GROQ) ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    MODELO = "llama-3.3-70b-versatile"
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

def procesar_planificacion_v2(modalidad, dia_nombre, config_db, tema_usuario):
    """
    Motor lógico que selecciona el cerebro y el contexto (PA/PSP/Pensum)
    config_db: Diccionario con {pa_texto, pa_dias, psp_texto, psp_dias, pensum_bloque, switches}
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

    # 2. LÓGICA DE SELECCIÓN DE CONTEXTO (LA BATUTA DEL DIRECTOR)
    contexto_inyectado = ""
    tipo_actividad = ""

    # Caso A: Docente de Taller (T.E.L.)
    if especialista == tel:
        if config_db['pa_switch'] and dia_nombre in config_db['pa_dias']:
            contexto_inyectado = f"CONTEXTO PROYECTO DE AULA (TEORÍA): {config_db['pa_texto']}"
            tipo_actividad = "Formación en Aula"
        elif config_db['psp_switch'] and dia_nombre in config_db['psp_dias']:
            contexto_inyectado = f"CONTEXTO PROYECTO SOCIO-PRODUCTIVO (PRÁCTICA): {config_db['psp_texto']}"
            tipo_actividad = "Ejecución de Taller (Enfoque Capataz/Supervisor)"
        elif config_db['pensum_switch']:
            contexto_inyectado = f"CONTEXTO PENSUM TÉCNICO DE OFICIO: {config_db['pensum_contenido']}"
            tipo_actividad = "Formación Técnica de Oficio"
        else:
            contexto_inyectado = "Enfoque general de formación para el trabajo."
            tipo_actividad = "Habilidades Laborales"

    # Caso B: Otros Servicios (I.E.E.B, CAIPA, etc.)
    else:
        if config_db['pa_switch'] and dia_nombre in config_db['pa_dias']:
            contexto_inyectado = f"CONTEXTO PROYECTO DE AULA: {config_db['pa_texto']}"
            tipo_actividad = "Actividad de Proyecto"
        else:
            # Para IEEB/CAIPA, si no hay PA, se basa en su ADN (Vida diaria / Autonomía)
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

    # 4. LLAMADA A LA IA
    return llamar_ia_groq(prompt_maestro)

def llamar_ia_groq(prompt_completo, temperatura=0.6):
    """Ejecuta la petición a Groq Cloud"""
    if not client: return "Error: Cliente IA no configurado."
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": prompt_completo}],
            model=MODELO,
            temperature=temperatura
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error de conexión con el cerebro IA: {e}"
