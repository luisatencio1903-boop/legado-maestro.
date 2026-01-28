import streamlit as st
from datetime import datetime, timedelta

# --- HORA VENEZUELA (UTC-4) ---
def ahora_ve():
    """
    Retorna la fecha y hora actual ajustada a la Zona Horaria de Venezuela.
    Esencial para que la asistencia no marque 'madrugada' cuando es de día.
    """
    hora_utc = datetime.utcnow()
    hora_venezuela = hora_utc - timedelta(hours=4)
    return hora_venezuela

# --- LIMPIEZA DE CÉDULA ---
def limpiar_id(v): 
    """
    Limpia el formato de la cédula para comparaciones en base de datos.
    Elimina puntos, comas, espacios y letras como 'V-' o 'E-'.
    """
    if v is None:
        return ""
    
    valor_str = str(v).strip().upper()
    # Eliminar decimales si viene de un Excel numérico (ej: 12345.0)
    valor_limpio = valor_str.split('.')[0]
    
    # Reemplazos de limpieza (Regla de Oro: Tu lista original)
    valor_limpio = valor_limpio.replace(',', '')
    valor_limpio = valor_limpio.replace('.', '')
    valor_limpio = valor_limpio.replace('V-', '')
    valor_limpio = valor_limpio.replace('E-', '')
    valor_limpio = valor_limpio.replace(' ', '')
    
    return valor_limpio
