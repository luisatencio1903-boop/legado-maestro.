import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
from utils.comunes import ahora_ve, limpiar_id, cargar_universo_datos

st.set_page_config(
    page_title="SUPER DIRECTOR 1.0",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
    .alert-box { background-color: #ffebee; border-left: 5px solid #c62828; padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #b71c1c; }
</style>
""", unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_HOJA = st.secrets["GSHEETS_URL"]
except:
    st.error("Error de conexión.")
    st.stop()

if 'auth_dir' not in st.session_state: st.session_state.auth_dir = False
if 'u_dir' not in st.session_state: st.session_state.u_dir = None
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "HOME"

query_params = st.query_params
usuario_en_url = query_params.get("u", None)

if not st.session_state.auth_dir and usuario_en_url:
    try:
        df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
        df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
        usuario_limpio = limpiar_id(usuario_en_url)
        match = df_u[(df_u['C_L'] == usuario_limpio) & (df_u['ROL'] == "DIRECTOR")]
        if not match.empty:
            st.session_state.auth_dir = True
            st.session_state.u_dir = match.iloc[0].to_dict()
        else:
            st.query_params.clear()
    except: pass

if not st.session_state.auth_dir:
    st.title("🛡️ Acceso: SUPER DIRECTOR")
    st.caption("Panel de Control - T.E.L. E.R.A.C.")
    with st.form("login_dir"):
        cedula_input = st.text_input("Cédula de Identidad:")
        clave_input = st.text_input("Contraseña:", type="password")
        if st.form_submit_button("AUTORIZAR INGRESO", use_container_width=True):
            try:
                df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
                df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
                cedula_limpia = limpiar_id(cedula_input)
                match = df_u[(df_u['C_L'] == cedula_limpia) & (df_u['CLAVE'] == clave_input)]
                
                if not match.empty:
                    if match.iloc[0]['ROL'] == "DIRECTOR":
                        st.session_state.auth_dir = True
                        st.session_state.u_dir = match.iloc[0].to_dict()
                        st.query_params["u"] = cedula_limpia
                        st.rerun()
                    else: st.error("Acceso Denegado: Rol insuficiente.")
                else: st.error("Credenciales incorrectas.")
            except Exception as e: st.error(f"Error de base de datos: {e}")
    st.stop()

col_sync, col_logout = st.columns([1, 1])
with col_sync:
    if st.button("♻️ ACTUALIZAR"):
        st.cache_data.clear()
        st.toast("Sincronizando con Google Sheets...")
        time.sleep(1)
        st.rerun()
with col_logout:
    if st.button("🔒 SALIR"):
        st.session_state.auth_dir = False
        st.session_state.u_dir = None
        st.query_params.clear()
        st.rerun()

universo = cargar_universo_datos(conn, URL_HOJA)

if st.session_state.vista_actual == "HOME":
    st.write(f"**Director:** {st.session_state.u_dir['NOMBRE']}")
    st.title("🛡️ Panel de Control")
    st.divider()

    st.markdown("### 🚦 ESTADO DEL PLANTEL (HOY)")
    hoy = ahora_ve().strftime("%d/%m/%Y")
    
    # Uso de get para evitar errores si la carga falló parcialmente
    df_as = universo.get("asistencia", pd.DataFrame())
    df_ej = universo.get("ejecucion", pd.DataFrame())
    
    if not df_as.empty and not df_ej.empty:
        data_hoy = df_as[df_as['FECHA'] == hoy]
        pres = len(data_hoy[data_hoy['TIPO'] == "ASISTENCIA"])
        fals = len(data_hoy[data_hoy['TIPO'] == "INASISTENCIA"])
        pend_as = len(df_as[df_as['ESTADO_DIRECTOR'] == "PENDIENTE"])
        pend_ej = len(df_ej[df_ej['ESTADO'] == "PENDIENTE"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Presentes", f"{pres}")
        c2.metric("Faltas", f"{fals}")
        c3.metric("Pendientes", f"{pend_as + pend_ej}")

        st.divider()

        st.markdown("### ⚠️ ALERTAS DE INCUMPLIMIENTO")
        docs_con_salida = data_hoy[(data_hoy['TIPO'] == "ASISTENCIA") & (data_hoy['HORA_SALIDA'] != "-")]
        sin_foto_s = docs_con_salida[docs_con_salida['FOTO_SALIDA'] == "-"]
        if not sin_foto_s.empty:
            for _, fila in sin_foto_s.iterrows():
                st.markdown(f"<div class='alert-box'>📸 <b>{fila['USUARIO']}</b> marcó salida sin foto de evidencia.</div>", unsafe_allow_html=True)

        docs_presentes = data_hoy[data_hoy['TIPO'] == "ASISTENCIA"]['USUARIO'].tolist()
        docs_ejecutaron = df_ej[df_ej['FECHA'] == hoy]['USUARIO'].tolist()
        faltan_ej = [d for d in docs_presentes if d not in docs_ejecutaron]
        if faltan_ej:
            for d in faltan_ej:
                st.markdown(f"<div class='alert-box' style='background-color:#fff3e0;border-left-color:#fb8c00;color:#e65100;'>🏫 <b>{d}</b> no ha culminado actividad en Aula Virtual.</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Esperando sincronización de datos...")

    st.divider()
    st.markdown("### 🛠️ GESTIÓN ESTRATÉGICA")
    sel = st.selectbox("Herramienta:", ["(Seleccionar)", "📊 Informe Diario Gestión", "📩 Revisión de Planes", "📸 Validar Evidencias", "🏆 Ranking de Méritos"])
    if sel != "(Seleccionar)":
        st.session_state.vista_actual = sel
        st.rerun()

else:
    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.vista_actual = "HOME"
        st.rerun()
    st.subheader(st.session_state.vista_actual)
    st.divider()

    if st.session_state.vista_actual == "📊 Informe Diario Gestión":
        from vistas import informe_diario
        informe_diario.render_informe(universo)
    elif st.session_state.vista_actual == "📩 Revisión de Planes":
        from vistas import revision_planes
        # CORRECCIÓN VITAL: Se pasan 3 argumentos
        revision_planes.render_revision(conn, URL_HOJA, universo)
    elif st.session_state.vista_actual == "📸 Validar Evidencias":
        from vistas import validar_evidencias
        validar_evidencias.render_validacion(conn, URL_HOJA, universo)
    elif st.session_state.vista_actual == "🏆 Ranking de Méritos":
        from vistas import ranking_meritos
        # AQUÍ ESTÁ LA ACTUALIZACIÓN FINAL: Se pasan los 3 argumentos
        ranking_meritos.render_ranking(conn, URL_HOJA, universo)
