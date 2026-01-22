import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Legado Maestro - Zulia", layout="wide")

# --- ESTILOS CSS (Blanco y Negro para contraste) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #000000 !important; font-weight: 700 !important; }
    .stButton>button { background-color: #004a99; color: white !important; font-weight: bold; border-radius: 8px; height: 3em; }
    .card-aula { background: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 10px solid #004a99; margin-bottom: 15px; color: black !important; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .status-vivo { color: #d9534f !important; font-weight: bold; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
URL_HOJA = st.secrets["GSHEETS_URL"]

def limpiar_id(v): 
    return str(v).strip().split('.')[0].replace(',', '').replace('.', '')

# --- INICIALIZACIÓN DE MEMORIA (AQUÍ ESTÁ LA SOLUCIÓN A TUS ERRORES) ---
# Esto asegura que las variables existan antes de usarlas
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.u = None
    st.session_state.plan_edicion = ""
    st.session_state.clase_activa = False
    st.session_state.fin_meta = None
    st.session_state.meta_mins = 45  # <--- ESTO EVITA EL ERROR DEL TEMPORIZADOR
    st.session_state.eval_tecnica = ""
    st.session_state.tema_actual = ""

# --- SISTEMA DE ACCESO Y SEGURIDAD ---
if not st.session_state.auth:
    st.title("🛡️ Seguridad Legado Maestro - Zulia")
    t_log, t_reg = st.tabs(["🔐 Iniciar Sesión", "📝 Registro de Nómina"])

    with t_log:
        c_in = st.text_input("Cédula de Identidad", key="login_c")
        p_in = st.text_input("Contraseña", type="password", key="login_p")
        if st.button("ACCEDER AL SISTEMA"):
            # Leemos la hoja de usuarios
            df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
            
            # Limpiamos las cédulas para evitar errores de puntos o espacios
            df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
            match = df_u[(df_u['C_L'] == limpiar_id(c_in)) & (df_u['CLAVE'] == p_in)]
            
            if not match.empty:
                st.session_state.auth = True
                st.session_state.u = match.iloc[0].to_dict()
                st.success("¡Bienvenido! Cargando sistema...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Cédula o contraseña incorrecta.")

    with t_reg:
        st.subheader("Activación de Personal")
        c_re = st.text_input("Ingrese su Cédula para validar", key="reg_c")
        p_re = st.text_input("Cree su Clave de Acceso", type="password", key="reg_p")
        
        if st.button("ACTIVAR MI CUENTA"):
            df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
            df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
            ced_limpia = limpiar_id(c_re)
            
            if ced_limpia in df_u['C_L'].values:
                idx = df_u.index[df_u['C_L'] == ced_limpia][0]
                
                # Verificamos si ya tenía clave
                if pd.notna(df_u.loc[idx, 'CLAVE']) and str(df_u.loc[idx, 'CLAVE']) != "":
                    st.warning("Usted ya tiene una cuenta activa. Vaya a Iniciar Sesión.")
                else:
                    df_u.loc[idx, 'CLAVE'] = p_re
                    df_u.loc[idx, 'ESTADO'] = "ACTIVO"
                    # Guardamos sin la columna temporal C_L
                    conn.update(spreadsheet=URL_HOJA, worksheet="USUARIOS", data=df_u.drop(columns=['C_L']))
                    st.success("✅ Cuenta activada. Ya puede iniciar sesión.")
            else:
                st.error("🚫 Su cédula no aparece en la nómina oficial.")

# --- FIN DEL BLOQUE DE SEGURIDAD ---

# --- PANTALLA PRINCIPAL (CUANDO YA ENTRASTE) ---
else:
    u = st.session_state.u
    st.sidebar.title(f"👤 {u['NOMBRE']}")
    st.sidebar.info(f"Rol: {u['ROL']}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    # Cargamos los datos de la escuela
    df_act = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)

    # ==========================================
    # MÓDULO DEL DOCENTE
    # ==========================================
    if u['ROL'] == "DOCENTE":
        st.header(f"👨‍🏫 Aula Virtual: {u['NOMBRE']}")
        t1, t2, t3, t4 = st.tabs(["📅 Planificación", "🚀 Clase en Vivo", "📝 Evaluación IA", "📂 Expediente"])

        # --- PESTAÑA 1: PLANIFICACIÓN ---
        with t1:
            # Verificamos si ya tiene un plan activo
            p_existente = df_act[(df_act['USUARIO'] == u['NOMBRE']) & (df_act['ESTADO'].isin(['PENDIENTE', 'APROBADO']))]
            
            if not p_existente.empty:
                est = p_existente.iloc[-1]
                st.info(f"Usted ya tiene un plan activo: '{est['TEMA']}' ({est['ESTADO']})")
            else:
                st.subheader("Nueva Planificación")
                st.session_state.tema_actual = st.text_input("Tema de la clase:")
                
                if st.button("🧠 Generar Propuesta con IA"):
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    res = client.chat.completions.create(
                        messages=[{"role":"user","content":f"Plan de 8 puntos técnicos para {st.session_state.tema_actual}."}], 
                        model="llama-3.3-70b-versatile"
                    )
                    st.session_state.plan_edicion = res.choices[0].message.content
                
                if st.session_state.plan_edicion:
                    plan_final = st.text_area("Edite su plan:", value=st.session_state.plan_edicion, height=250)
                    if st.button("📤 ENVIAR AL DIRECTOR"):
                        nueva = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%d/%m/%Y"), "USUARIO": u['NOMBRE'], 
                            "TEMA": st.session_state.tema_actual, "CONTENIDO": plan_final, 
                            "ESTADO": "PENDIENTE", "HORA_INICIO": "--:--", "HORA_FIN": "--:--"
                        }])
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df_act, nueva], ignore_index=True))
                        st.success("Enviado."); st.rerun()

        # --- PESTAÑA 2: EJECUCIÓN (CRONÓMETRO) ---
        with t2:
            ap = df_act[(df_act['USUARIO']==u['NOMBRE']) & (df_act['ESTADO'].isin(['APROBADO', 'EN CURSO']))]
            if ap.empty: 
                st.warning("No hay clases aprobadas para iniciar.")
            else:
                act = ap.iloc[-1]
                st.markdown(f"<div class='card-aula'><b>Objetivo:</b> {act['TEMA']}</div>", unsafe_allow_html=True)
                
                if not st.session_state.clase_activa:
                    # Usamos la variable de sesión para que no se borre
                    st.session_state.meta_mins = st.number_input("Duración (minutos):", 10, 180, st.session_state.meta_mins)
                    
                    if st.button("▶️ INICIAR CLASE"):
                        st.session_state.clase_activa = True
                        st.session_state.fin_meta = datetime.now() + timedelta(minutes=st.session_state.meta_mins)
                        # Guardamos inicio en Excel
                        idx = ap.index[-1]
                        df_act.loc[idx, 'ESTADO'] = 'EN CURSO'
                        df_act.loc[idx, 'HORA_INICIO'] = datetime.now().strftime("%H:%M")
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_act)
                        st.rerun()
                else:
                    restante = st.session_state.fin_meta - datetime.now()
                    if restante.total_seconds() > 0:
                        mins, segs = divmod(int(restante.total_seconds()), 60)
                        st.markdown(f"### ⏳ Tiempo Restante: {mins:02d}:{segs:02d}")
                        st.progress(max(0.0, min(1.0, 1 - (restante.total_seconds() / (st.session_state.meta_mins * 60)))))
                    else:
                        st.error("⏰ TIEMPO CUMPLIDO")
                    
                    if st.button("⏹️ CULMINAR ACTIVIDAD"):
                        st.session_state.clase_activa = False
                        idx = df_act[df_act['USUARIO']==u['NOMBRE']].index[-1]
                        df_act.loc[idx, 'ESTADO'] = 'FINALIZADO'
                        df_act.loc[idx, 'HORA_FIN'] = datetime.now().strftime("%H:%M")
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_act)
                        st.balloons(); st.rerun()

        # --- PESTAÑA 3: TRANSFORMADOR IA ---
        with t3:
            st.subheader("Transformador Pedagógico")
            alum = st.text_input("Alumno:", placeholder="Ej: Greilyz")
            nota = st.text_area("Observación natural:")
            if st.button("🪄 PROCESAR INFORME TÉCNICO"):
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(messages=[{"role":"user","content":f"Traduce a informe técnico para {alum}: {nota}"}], model="llama-3.3-70b-versatile")
                st.session_state.eval_tecnica = res.choices[0].message.content
            
            if st.session_state.eval_tecnica:
                st.info(st.session_state.eval_tecnica)
                if st.button("💾 GUARDAR EN EXPEDIENTE"):
                    df_ev = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                    new_ev = pd.DataFrame([{"FECHA":datetime.now().strftime("%d/%m/%Y"), "ALUMNO":alum.upper(), "INFORME":st.session_state.eval_tecnica}])
                    conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, new_ev], ignore_index=True))
                    st.success("Guardado.")

        # --- PESTAÑA 4: CONSULTA DE EXPEDIENTES ---
        with t4:
            st.subheader("📂 Historial de Alumnos")
            df_hist = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
            if not df_hist.empty:
                sel = st.selectbox("Seleccione Alumno:", df_hist['ALUMNO'].unique())
                st.table(df_hist[df_hist['ALUMNO'] == sel])

# ==========================================
    # MÓDULO DEL DIRECTOR
    # ==========================================
    elif u['ROL'] == "DIRECTOR":
        st.title("🏛️ Torre de Control - Supervisión")
        
        # Filtro de fecha
        fecha_ver = st.date_input("Consultar Fecha:", datetime.now())
        f_str = fecha_ver.strftime("%d/%m/%Y")
        
        # Filtramos la data por fecha
        df_dia = df_act[df_act['FECHA'] == f_str]
        
        # Panel de Métricas
        col1, col2 = st.columns(2)
        
        # --- COLUMNA IZQUIERDA: APROBACIONES ---
        with col1:
            st.subheader("📥 Planes Pendientes")
            pendientes = df_dia[df_dia['ESTADO'] == 'PENDIENTE']
            
            if pendientes.empty:
                st.info("No hay planes pendientes de revisión.")
            else:
                for i, r in pendientes.iterrows():
                    with st.expander(f"Plan de: {r['USUARIO']}"):
                        st.write(r['CONTENIDO'])
                        if st.button("✅ APROBAR PLAN", key=f"apr_{i}"):
                            df_act.loc[i, 'ESTADO'] = 'APROBADO'
                            conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_act)
                            st.success(f"Plan de {r['USUARIO']} aprobado.")
                            time.sleep(1)
                            st.rerun()

        # --- COLUMNA DERECHA: MONITOR EN VIVO ---
        with col2:
            st.subheader("👀 Actividad en Aula (En Vivo)")
            vivos = df_dia[df_dia['ESTADO'] == 'EN CURSO']
            
            if vivos.empty:
                st.info("No hay docentes dando clase en este momento.")
            else:
                for _, r in vivos.iterrows():
                    st.markdown(f"""
                        <div class='card-aula'>
                            <h4 style='margin:0'>{r['USUARIO']}</h4>
                            <span class='status-vivo'>● EN VIVO</span><br>
                            <b>Tema:</b> {r['TEMA']}<br>
                            <b>Inicio:</b> {r['HORA_INICIO']}
                        </div>
                    """, unsafe_allow_html=True)
                    
# --- FIN DEL CÓDIGO MAESTRO ---
