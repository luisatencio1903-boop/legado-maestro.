import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def ahora_ve():
    return datetime.utcnow() - timedelta(hours=4)

def limpiar_id(v):
    if v is None: return ""
    return str(v).strip().upper().replace(',', '').replace('.', '').replace('V-', '').replace('E-', '').replace(' ', '')

@st.cache_data(ttl=300)
def cargar_universo_datos(_conn, url):
    asistencia = _conn.read(spreadsheet=url, worksheet="ASISTENCIA")
    evaluaciones = _conn.read(spreadsheet=url, worksheet="EVALUACIONES")
    ejecucion = _conn.read(spreadsheet=url, worksheet="EJECUCION")
    usuarios = _conn.read(spreadsheet=url, worksheet="USUARIOS")
    matricula = _conn.read(spreadsheet=url, worksheet="MATRICULA_GLOBAL")
    planes = _conn.read(spreadsheet=url, worksheet="Hoja1")
    return {
        "asistencia": asistencia,
        "evaluaciones": evaluaciones,
        "ejecucion": ejecucion,
        "usuarios": usuarios,
        "matricula": matricula,
        "planes": planes
    }

def obtener_metricas_dashboard(universo):
    df_as = universo["asistencia"]
    hoy = ahora_ve().strftime("%d/%m/%Y")
    
    data_hoy = df_as[df_as['FECHA'] == hoy]
    presentes = len(data_hoy[data_hoy['TIPO'] == "ASISTENCIA"])
    faltas = len(data_hoy[data_hoy['TIPO'] == "INASISTENCIA"])
    
    pendientes_as = len(df_as[df_as['ESTADO_DIRECTOR'] == "PENDIENTE"])
    pendientes_ej = len(universo["ejecucion"][universo["ejecucion"]['ESTADO'] == "PENDIENTE"])
    
    return {
        "presentes": presentes,
        "faltas": faltas,
        "pendientes_total": pendientes_as + pendientes_ej
    }

def aplicar_estilos_director():
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
        .report-card { background-color: white; padding: 20px; border-radius: 15px; border-left: 10px solid #1e3a8a; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .plan-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 8px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)
