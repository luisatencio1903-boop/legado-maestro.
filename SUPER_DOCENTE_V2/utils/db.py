import streamlit as st
import pandas as pd
import requests
import time
from utils.maletin import persistir_en_dispositivo, recuperar_del_dispositivo

# --- ESCUDO DE IMPORTACIÓN v2.1 (Para que la App arranque sin internet) ---
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None

def conectar_db():
    """Intenta conectar a Google Sheets. Si falla o no hay librería, retorna None."""
    if GSheetsConnection is None:
        return None
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn
    except:
        return None

def guardar_asistencia_hibrida(conn, datos):
    """Decide si guarda en Google o en el teléfono según la señal."""
    URL_HOJA = st.secrets["GSHEETS_URL"]
    
    # 1. Intentar guardado en la Nube (Online)
    if conn is not None:
        try:
            df = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=0)
            df_final = pd.concat([df, pd.DataFrame([datos])], ignore_index=True)
            conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_final)
            st.success("✅ Sincronizado con Dirección (Google Sheets)")
            return True
        except:
            pass
            
    # 2. FALLBACK: Si no hay internet o falla la conexión, al Maletín (Offline)
    persistir_en_dispositivo("cola_asistencia", datos)
    st.warning("📡 Sin señal. Registro protegido en la memoria del teléfono.")
    return False

def guardar_evaluacion_hibrida(conn, datos):
    """Guarda la nota del alumno en el teléfono si no hay internet."""
    URL_HOJA = st.secrets["GSHEETS_URL"]
    
    if conn is not None:
        try:
            df = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
            df_final = pd.concat([df, pd.DataFrame([datos])], ignore_index=True)
            conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=df_final)
            st.success("✅ Evaluación enviada a la Nube.")
            return True
        except:
            pass
            
    # Guardar en una lista de pendientes dentro del celular
    pendientes = recuperar_del_dispositivo("cola_evaluaciones") or []
    pendientes.append(datos)
    persistir_en_dispositivo("cola_evaluaciones", pendientes)
    st.warning("📝 Evaluación guardada localmente (Modo Offline).")
    return False

def cargar_datos_maestros(conn, url):
    """Carga las listas de alumnos y profes."""
    if conn is None:
        return pd.DataFrame(), pd.DataFrame()
    try:
        profes = conn.read(spreadsheet=url, worksheet="USUARIOS", ttl=600)
        matricula = conn.read(spreadsheet=url, worksheet="MATRICULA_GLOBAL", ttl=600)
        return profes, matricula
    except:
        return pd.DataFrame(), pd.DataFrame()
