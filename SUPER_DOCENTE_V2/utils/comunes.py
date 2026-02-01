import streamlit as st
import pandas as pd
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

# --- CARGA DEL UNIVERSO DE DATOS (v2.0 Modular) ---
@st.cache_data(ttl=600)
def cargar_datos_maestros(_conn, url):
    """Carga las listas de alumnos y profes una sola vez y las guarda en memoria."""
    try:
        profes = _conn.read(spreadsheet=url, worksheet="USUARIOS")
        matricula = _conn.read(spreadsheet=url, worksheet="MATRICULA_GLOBAL")
        return profes, matricula
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- ESTILOS VISUALES (v2.0) ---
def aplicar_estilos_director():
    """Centraliza los estilos CSS para que no se repitan en cada archivo."""
    st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp { background-color: #f1f5f9; }
        .stSelectbox label { font-size: 1.2rem !important; font-weight: 800 !important; color: #1e3a8a !important; }
        .stButton button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: 700; background-color: #1e3a8a; color: white; border: none; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; border-top: 5px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)
