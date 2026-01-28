import streamlit as st
from groq import Groq

# --- IMPORTACIÓN DE LOS ESPECIALISTAS (LOS ARCHIVOS QUE CREASTE) ---
from cerebros import tel, caipa, ieeb, aula_integrada, upe, inicial

# Configuración inicial del cliente IA
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        MODELO_USADO = "llama-3.3-70b-versatile"
    else:
        client = None
except:
    client = None

def generar_respuesta(mensajes_historial, temperatura=0.7):
    """Función técnica para enviar mensajes a la IA."""
    if not client:
        return "Error: Falta configurar GROQ_API_KEY en Secrets."
    
    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes_historial,
            model=MODELO_USADO,
            temperature=temperatura,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error de conexión con IA: {e}"

# ==============================================================================
# EL DIRECTOR DE ORQUESTA (SELECTOR MODULAR)
# ==============================================================================
def seleccionar_cerebro_modalidad(modalidad):
    """
    Recibe la selección del menú (Planificador) y busca el archivo
    correspondiente en la carpeta 'cerebros'.
    """
    
    # 1. BASE COMÚN (Identidad General del Proyecto)
    base_identidad = """
    ERES "SUPER DOCENTE 2.0", ASISTENTE PEDAGÓGICO VENEZOLANO.
    MARCO: Conceptualización y Política de Educación Especial y Currículo Nacional Bolivariano.
    CREADOR: Luis Atencio (Bachiller Docente).
    TONO: Profesional, Empático y Técnico-Pedagógico.
    """

    # 2. SELECCIÓN DINÁMICA DEL ESPECIALISTA
    prompt_especifico = ""
    
    # Busca palabras clave en la selección del usuario
    if "Taller" in modalidad or "T.E.L." in modalidad:
        prompt_especifico = tel.obtener_prompt()
        
    elif "Instituto" in modalidad or "I.E.E.B." in modalidad:
        prompt_especifico = ieeb.obtener_prompt()

    elif "Autismo" in modalidad or "C.A.I.P.A." in modalidad:
        prompt_especifico = caipa.obtener_prompt()
        
    elif "Aula Integrada" in modalidad:
        prompt_especifico = aula_integrada.obtener_prompt()

    elif "Unidad Psico-Educativa" in modalidad or "U.P.E." in modalidad:
        prompt_especifico = upe.obtener_prompt()
        
    elif "Inicial" in modalidad:
        prompt_especifico = inicial.obtener_prompt()
    
    else:
        # Fallback por si algo falla
        prompt_especifico = "ROL: DOCENTE DE EDUCACIÓN ESPECIAL (INTEGRAL). ENFOQUE: Atención a la Diversidad."

    # 3. RETORNA LA MEZCLA (Base + Especialista)
    return base_identidad + "\n" + prompt_especifico
