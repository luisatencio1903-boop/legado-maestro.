# ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO - VERSIÓN DEFINITIVA (MEGA)
# FUSIÓN: Estilo V1.3 + Potencia V2.0
# AUTOR: Luis Atencio
# LÍNEAS ESTIMADAS: 400+
# ---------------------------------------------------------

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import time
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Legado Maestro",
    page_icon="🍎",
    layout="wide"
)

# --- 2. ESTILOS CSS (TUS ESTILOS AMADOS V1.3 + EXTRAS) ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* CAJA DE PLANIFICACIÓN (TU DISEÑO ORIGINAL) */
    .plan-box {
        background-color: #f0f2f6 !important;
        color: #000000 !important; 
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0068c9;
        margin-bottom: 20px;
        font-family: sans-serif;
    }
    .plan-box h3 { color: #0068c9 !important; border-bottom: 2px solid #ccc; }
    .plan-box strong { color: #2c3e50 !important; font-weight: 700; }

    /* ESTILOS DE LA TORRE DE CONTROL Y EJECUCIÓN */
    .card-aula { background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 8px solid #004a99; margin-bottom: 10px; color: black !important; }
    .status-vivo { color: #d9534f !important; font-weight: bold; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    
    /* MENSAJES MOTIVACIONALES (TU DISEÑO ORIGINAL) */
    .mensaje-texto {
        color: #000000 !important;
        font-family: 'Helvetica', sans-serif;
        font-size: 1.2em; 
        font-weight: 500;
        line-height: 1.4;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. CONEXIONES (GROQ + GOOGLE SHEETS) ---
try:
    # Conexión IA
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        MODELO_USADO = "llama-3.3-70b-versatile" 
    
    # Conexión Base de Datos
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_HOJA = st.secrets["GSHEETS_URL"]
    
except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
    st.stop()

def limpiar_id(v): return str(v).strip().split('.')[0].replace(',', '').replace('.', '')

# --- 4. GESTIÓN DE MEMORIA (TODAS LAS VARIABLES) ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'u' not in st.session_state: st.session_state.u = None
if 'plan_actual' not in st.session_state: st.session_state.plan_actual = ""
if 'clase_activa' not in st.session_state: st.session_state.clase_activa = False
if 'meta_mins' not in st.session_state: st.session_state.meta_mins = 45
if 'eval_tecnica' not in st.session_state: st.session_state.eval_tecnica = ""

# --- 5. SISTEMA DE LOGIN (EL PORTERO) ---
if not st.session_state.auth:
    st.title("🛡️ Acceso Legado Maestro")
    c = st.text_input("Cédula:")
    p = st.text_input("Contraseña:", type="password")
    
    if st.button("Ingresar al Sistema"):
        try:
            df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
            df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
            match = df_u[(df_u['C_L'] == limpiar_id(c)) & (df_u['CLAVE'] == p)]
            if not match.empty:
                st.session_state.auth = True
                st.session_state.u = match.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        except:
            st.error("Error conectando a la base de datos.")

# --- 6. APLICACIÓN PRINCIPAL ---
else:
    u = st.session_state.u
    
    # --- BARRA LATERAL (TU IDENTIDAD V1.3) ---
    with st.sidebar:
        if os.path.exists("logo_legado.png"): st.image("logo_legado.png", width=150)
        else: st.header("🍎")
        
        st.title("Legado Maestro")
        st.caption(f"👤 **{u['NOMBRE']}**")
        st.caption(f"Rol: {u['ROL']}")
        
        st.markdown("---")
        
        # MENÚ COMPLETO (INTEGRACIÓN)
        if u['ROL'] == "DOCENTE":
            opcion = st.radio("Herramientas:", 
                [
                    "📝 Planificación Pro", 
                    "🚀 Clase en Vivo", 
                    "📂 Expedientes", 
                    "🌟 Motivación",  # <-- TU EXTRA ORIGINAL
                    "💡 Ideas DUA",    # <-- TU EXTRA ORIGINAL
                    "❓ Consultas"     # <-- TU EXTRA ORIGINAL
                ]
            )
        elif u['ROL'] == "DIRECTOR":
            opcion = st.radio("Herramientas:", ["🏛️ Torre de Control"])
            
        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # CARGA DE DATOS CENTRAL
    try:
        df_act = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
    except:
        st.error("Error leyendo Hoja1. Verifique Google Sheets.")
        st.stop()

    # =========================================================
    # OPCIÓN 1: PLANIFICADOR (LÓGICA V1.3 + BASE DE DATOS)
    # =========================================================
    if u['ROL'] == "DOCENTE" and opcion == "📝 Planificación Pro":
        st.subheader("Planificación Técnica (Taller Laboral)")
        
        col1, col2 = st.columns(2)
        with col1: rango = st.text_input("Lapso:", placeholder="Ej: 19 al 23 de Enero")
        with col2: aula = st.text_input("Aula:", value="Mantenimiento")
        notas = st.text_area("Tema / Objetivo:", height=100)

        # Aviso si ya hay plan
        p_existente = df_act[(df_act['USUARIO'] == u['NOMBRE']) & (df_act['ESTADO'].isin(['PENDIENTE', 'APROBADO']))]
        if not p_existente.empty:
            st.warning(f"⚠️ Plan Activo: {p_existente.iloc[-1]['TEMA']} ({p_existente.iloc[-1]['ESTADO']})")
        
        if st.button("🚀 Generar y Enviar"):
            if rango and notas:
                with st.spinner('Generando Planificación Completa...'):
                    # --- TU PROMPT MAESTRO DE LA V1.3 (INTACTO) ---
                    prompt = f"""
                    Actúa como Luis Atencio. Planificación técnica para {rango}. Aula: {aula}. Tema: {notas}.
                    
                    ESTRUCTURA OBLIGATORIA (NO OMITAS NADA):
                    1. TÍTULO DE LA CLASE
                    2. COMPETENCIA
                    3. EXPLORACIÓN
                    4. DESARROLLO
                    5. REFLEXIÓN
                    6. MANTENIMIENTO
                    7. ESTRATEGIAS
                    8. RECURSOS
                    
                    Al final agrega: 📚 FUNDAMENTACIÓN LEGAL.
                    """
                    res = client.chat.completions.create(messages=[{"role":"user", "content": prompt}], model=MODELO_USADO).choices[0].message.content
                    
                    # GUARDAR EN DB
                    nueva = pd.DataFrame([{
                        "FECHA": datetime.now().strftime("%d/%m/%Y"), "USUARIO": u['NOMBRE'], 
                        "TEMA": notas, "CONTENIDO": res, "ESTADO": "PENDIENTE", 
                        "HORA_INICIO": "--", "HORA_FIN": "--"
                    }])
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df_act, nueva], ignore_index=True))
                    st.session_state.plan_actual = res
                    st.success("Plan generado y enviado a Dirección.")
                    st.rerun()

        if st.session_state.plan_actual:
            st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)

    # =========================================================
    # OPCIÓN 2: EJECUCIÓN (CRONÓMETRO + BASE DE DATOS)
    # =========================================================
    elif u['ROL'] == "DOCENTE" and opcion == "🚀 Clase en Vivo":
        st.subheader("🚀 Control de Aula")
        aprobado = df_act[(df_act['USUARIO']==u['NOMBRE']) & (df_act['ESTADO'].isin(['APROBADO', 'EN CURSO']))]
        
        if aprobado.empty:
            st.info("No tienes planes aprobados para ejecutar hoy.")
        else:
            act = aprobado.iloc[-1]
            st.markdown(f"<div class='plan-box'><h3>Objetivo: {act['TEMA']}</h3></div>", unsafe_allow_html=True)
            
            # CONTROL DE TIEMPO BLINDADO
            if not st.session_state.clase_activa:
                st.session_state.meta_mins = st.number_input("Duración (min):", 1, 180, st.session_state.meta_mins)
                if st.button("▶️ INICIAR"):
                    st.session_state.clase_activa = True
                    st.session_state.fin_meta = datetime.now() + timedelta(minutes=st.session_state.meta_mins)
                    idx = aprobado.index[-1]
                    df_act.loc[idx, 'ESTADO'] = 'EN CURSO'
                    df_act.loc[idx, 'HORA_INICIO'] = datetime.now().strftime("%H:%M")
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_act)
                    st.rerun()
            else:
                restante = st.session_state.fin_meta - datetime.now()
                secs = restante.total_seconds()
                
                if secs > 0:
                    mins, s = divmod(int(secs), 60)
                    st.markdown(f"### ⏳ {mins:02d}:{s:02d}")
                    try:
                        st.progress(max(0.0, min(1.0, 1 - (secs/(st.session_state.meta_mins*60)))))
                    except: pass
                else: st.error("⏰ TIEMPO CUMPLIDO")
                
                if st.button("⏹️ CULMINAR"):
                    st.session_state.clase_activa = False
                    idx = df_act[df_act['USUARIO']==u['NOMBRE']].index[-1]
                    df_act.loc[idx, 'ESTADO'] = 'FINALIZADO'
                    df_act.loc[idx, 'HORA_FIN'] = datetime.now().strftime("%H:%M")
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_act)
                    st.balloons()
                    st.rerun()

# =========================================================
    # OPCIÓN 3: EXPEDIENTES (TRANSFORMADOR IA)
    # =========================================================
    elif u['ROL'] == "DOCENTE" and opcion == "📂 Expedientes":
        st.subheader("Transformador Pedagógico")
        alum = st.text_input("Alumno:")
        nota = st.text_area("Observación Anecdótica:")
        
        if st.button("🪄 Procesar"):
            with st.spinner("Analizando..."):
                prompt = f"Traduce a informe técnico pedagógico para el alumno {alum}: {nota}"
                res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=MODELO_USADO).choices[0].message.content
                st.session_state.eval_tecnica = res
        
        if st.session_state.eval_tecnica:
            st.markdown(f'<div class="plan-box">{st.session_state.eval_tecnica}</div>', unsafe_allow_html=True)
            if st.button("💾 Guardar en Base de Datos"):
                try:
                    df_ev = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                    new = pd.DataFrame([{"FECHA":datetime.now().strftime("%d/%m/%Y"), "ALUMNO":alum.upper(), "INFORME":st.session_state.eval_tecnica}])
                    conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, new], ignore_index=True))
                    st.success("Guardado en Expediente.")
                except: st.error("Error: Falta la hoja EVALUACIONES.")

    # =========================================================
    # TUS EXTRAS ORIGINALES DE LA VERSIÓN 1.3 (RECUPERADOS)
    # =========================================================
    elif u['ROL'] == "DOCENTE" and opcion == "🌟 Motivación":
        st.subheader("Dosis de Ánimo Express ⚡")
        if st.button("❤️ Mensaje Corto"):
            res = client.chat.completions.create(messages=[{"role":"user", "content": "Frase motivacional corta docente venezolano."}], model=MODELO_USADO).choices[0].message.content
            st.markdown(f'<div style="border-left: 8px solid #ff4b4b; padding:20px; background:white;"><div class="mensaje-texto">{res}</div></div>', unsafe_allow_html=True)

    elif u['ROL'] == "DOCENTE" and opcion == "💡 Ideas DUA":
        st.subheader("Generador de Ideas DUA")
        tema = st.text_input("Tema:")
        if st.button("✨ Sugerir"):
            res = client.chat.completions.create(messages=[{"role":"user", "content": f"3 actividades DUA para {tema}"}], model=MODELO_USADO).choices[0].message.content
            st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

    elif u['ROL'] == "DOCENTE" and opcion == "❓ Consultas":
        st.subheader("Asesoría Legal y Técnica")
        duda = st.text_area("Duda Técnica:")
        if st.button("🔍 Responder"):
            res = client.chat.completions.create(messages=[{"role":"user", "content": f"Responde como experto LOE/CNB: {duda}"}], model=MODELO_USADO).choices[0].message.content
            st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

    # =========================================================
    # MÓDULO DIRECTOR (TORRE DE CONTROL)
    # =========================================================
    elif u['ROL'] == "DIRECTOR" and opcion == "🏛️ Torre de Control":
        st.title("🏛️ Torre de Control")
        f_ver = st.date_input("Consultar Fecha:", datetime.now())
        df_dia = df_act[df_act['FECHA'] == f_ver.strftime("%d/%m/%Y")]
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Pendientes")
            pend = df_dia[df_dia['ESTADO'] == 'PENDIENTE']
            if pend.empty: st.info("Todo al día.")
            for i, r in pend.iterrows():
                with st.expander(f"{r['USUARIO']} - {r['TEMA']}"):
                    st.write(r['CONTENIDO'])
                    if st.button("✅ Aprobar", key=f"ap_{i}"):
                        df_act.loc[i, 'ESTADO'] = 'APROBADO'
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_act)
                        st.rerun()
        with c2:
            st.subheader("En Vivo")
            vivos = df_dia[df_dia['ESTADO'] == 'EN CURSO']
            if vivos.empty: st.info("Sin actividad en aula.")
            for _, r in vivos.iterrows():
                st.markdown(f"<div class='card-aula'><h4>{r['USUARIO']}</h4><span class='status-vivo'>● EN CLASE</span><br>Inicio: {r['HORA_INICIO']}</div>", unsafe_allow_html=True)

# =========================================================
    # OPCIÓN 3: EXPEDIENTES (TRANSFORMADOR IA)
    # =========================================================
    elif u['ROL'] == "DOCENTE" and opcion == "📂 Expedientes":
        st.subheader("Transformador Pedagógico")
        alum = st.text_input("Alumno:")
        nota = st.text_area("Observación Anecdótica:")
        
        if st.button("🪄 Procesar"):
            with st.spinner("Analizando..."):
                prompt = f"Traduce a informe técnico pedagógico para el alumno {alum}: {nota}"
                res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=MODELO_USADO).choices[0].message.content
                st.session_state.eval_tecnica = res
        
        if st.session_state.eval_tecnica:
            st.markdown(f'<div class="plan-box">{st.session_state.eval_tecnica}</div>', unsafe_allow_html=True)
            if st.button("💾 Guardar en Base de Datos"):
                try:
                    df_ev = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                    new = pd.DataFrame([{"FECHA":datetime.now().strftime("%d/%m/%Y"), "ALUMNO":alum.upper(), "INFORME":st.session_state.eval_tecnica}])
                    conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev, new], ignore_index=True))
                    st.success("Guardado en Expediente.")
                except: st.error("Error: Falta la hoja EVALUACIONES.")

    # =========================================================
    # TUS EXTRAS ORIGINALES DE LA VERSIÓN 1.3 (RECUPERADOS)
    # =========================================================
    elif u['ROL'] == "DOCENTE" and opcion == "🌟 Motivación":
        st.subheader("Dosis de Ánimo Express ⚡")
        if st.button("❤️ Mensaje Corto"):
            res = client.chat.completions.create(messages=[{"role":"user", "content": "Frase motivacional corta docente venezolano."}], model=MODELO_USADO).choices[0].message.content
            st.markdown(f'<div style="border-left: 8px solid #ff4b4b; padding:20px; background:white;"><div class="mensaje-texto">{res}</div></div>', unsafe_allow_html=True)

    elif u['ROL'] == "DOCENTE" and opcion == "💡 Ideas DUA":
        st.subheader("Generador de Ideas DUA")
        tema = st.text_input("Tema:")
        if st.button("✨ Sugerir"):
            res = client.chat.completions.create(messages=[{"role":"user", "content": f"3 actividades DUA para {tema}"}], model=MODELO_USADO).choices[0].message.content
            st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

    elif u['ROL'] == "DOCENTE" and opcion == "❓ Consultas":
        st.subheader("Asesoría Legal y Técnica")
        duda = st.text_area("Duda Técnica:")
        if st.button("🔍 Responder"):
            res = client.chat.completions.create(messages=[{"role":"user", "content": f"Responde como experto LOE/CNB: {duda}"}], model=MODELO_USADO).choices[0].message.content
            st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)

    # =========================================================
    # MÓDULO DIRECTOR (TORRE DE CONTROL)
    # =========================================================
    elif u['ROL'] == "DIRECTOR" and opcion == "🏛️ Torre de Control":
        st.title("🏛️ Torre de Control")
        f_ver = st.date_input("Consultar Fecha:", datetime.now())
        df_dia = df_act[df_act['FECHA'] == f_ver.strftime("%d/%m/%Y")]
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Pendientes")
            pend = df_dia[df_dia['ESTADO'] == 'PENDIENTE']
            if pend.empty: st.info("Todo al día.")
            for i, r in pend.iterrows():
                with st.expander(f"{r['USUARIO']} - {r['TEMA']}"):
                    st.write(r['CONTENIDO'])
                    if st.button("✅ Aprobar", key=f"ap_{i}"):
                        df_act.loc[i, 'ESTADO'] = 'APROBADO'
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_act)
                        st.rerun()
        with c2:
            st.subheader("En Vivo")
            vivos = df_dia[df_dia['ESTADO'] == 'EN CURSO']
            if vivos.empty: st.info("Sin actividad en aula.")
            for _, r in vivos.iterrows():
                st.markdown(f"<div class='card-aula'><h4>{r['USUARIO']}</h4><span class='status-vivo'>● EN CLASE</span><br>Inicio: {r['HORA_INICIO']}</div>", unsafe_allow_html=True)
