import streamlit as st
import pandas as pd
import time
import re
from utils.comunes import ahora_ve
from utils.drive_api import subir_a_imgbb
from cerebros.nucleo import generar_respuesta
# --- NUEVAS HERRAMIENTAS DE RESILIENCIA (PASO 4) ---
from utils.maletin import persistir_en_dispositivo, borrar_del_dispositivo
from utils.traductor import foto_a_texto

def render_aula(conn):
    # Recuperamos la URL para las conexiones internas
    try:
        URL_HOJA = st.secrets["GSHEETS_URL"]
    except:
        st.error("Error de configuración: No se encontró GSHEETS_URL.")
        return

    # --- FUNCIÓN DE RESPALDO LOCAL (v2.0 Offline-First) ---
    def respaldar_en_maletin():
        """Guarda el estado actual de la clase en la memoria física del dispositivo."""
        estado_clase = {
            "av_foto1": st.session_state.av_foto1,
            "av_foto2": st.session_state.av_foto2,
            "av_foto3": st.session_state.av_foto3,
            "av_resumen": st.session_state.av_resumen,
            "av_titulo_hoy": st.session_state.av_titulo_hoy,
            "av_contexto_hoy": st.session_state.av_contexto_hoy,
            "modo_suplencia_activo": st.session_state.modo_suplencia_activo,
            "pagina_actual": st.session_state.pagina_actual
        }
        persistir_en_dispositivo("maletin_super_docente", estado_clase)

    # -------------------------------------------------------------------------
    # 1. GESTIÓN DE MEMORIA (CACHÉ / FOTOCOPIAS) - v14.0 ORIGINAL
    # -------------------------------------------------------------------------
    if 'cache_planes' not in st.session_state: 
        st.session_state.cache_planes = None
        
    if 'cache_evaluaciones' not in st.session_state: 
        st.session_state.cache_evaluaciones = None
        
    if 'cache_ejecucion' not in st.session_state: 
        st.session_state.cache_ejecucion = None
        
    if 'cache_matricula' not in st.session_state: 
        st.session_state.cache_matricula = None
    
    # Variables de estado originales (V13/V14)
    if 'modo_suplencia_activo' not in st.session_state: 
        st.session_state.modo_suplencia_activo = False
        
    if 'av_titulo_hoy' not in st.session_state: 
        st.session_state.av_titulo_hoy = ""
        
    if 'av_contexto_hoy' not in st.session_state: 
        st.session_state.av_contexto_hoy = ""
        
    if 'temp_propuesta_ia' not in st.session_state: 
        st.session_state.temp_propuesta_ia = ""
    
    # Variables para fotos secuenciales
    if 'av_foto1' not in st.session_state: 
        st.session_state.av_foto1 = None
        
    if 'av_foto2' not in st.session_state: 
        st.session_state.av_foto2 = None
        
    if 'av_foto3' not in st.session_state: 
        st.session_state.av_foto3 = None
        
    if 'av_resumen' not in st.session_state: 
        st.session_state.av_resumen = ""
    
    # Variable para el Chat Asistente
    if 'chat_asistente_aula' not in st.session_state: 
        st.session_state.chat_asistente_aula = []

    # --- FUNCIÓN DE SINCRONIZACIÓN (IR A DIRECCIÓN) ---
    def sincronizar_aula():
        try:
            with st.spinner("🔄 Actualizando datos desde Dirección (Google)..."):
                # Usamos ttl=0 para forzar descarga real de todas las hojas
                st.session_state.cache_planes = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                st.session_state.cache_evaluaciones = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                st.session_state.cache_ejecucion = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                st.session_state.cache_matricula = conn.read(spreadsheet=URL_HOJA, worksheet="MATRICULA_GLOBAL", ttl=0) 
            st.success("✅ Datos actualizados en memoria.")
            time.sleep(0.5)
        except Exception as e: 
            st.error(f"Error sincronizando con Google Sheets: {e}")

    # Auto-carga inicial si el caché está vacío
    if st.session_state.cache_planes is None or st.session_state.cache_matricula is None:
        sincronizar_aula()
        st.rerun()

    # --- ENCABEZADO Y CONTEXTO ---
    c_head, c_btn = st.columns([3, 1])
    with c_head:
        st.info("💡 **Centro de Operaciones:** Gestión de la clase (Inicio - Desarrollo - Cierre).")
    with c_btn:
        if st.button("🔄 RECARGAR DATOS"):
            sincronizar_aula()
            st.rerun()

    st.markdown("### ⚙️ Contexto de la Clase")
    es_suplencia = st.checkbox("🦸 **Activar Modo Suplencia**", 
                                value=st.session_state.modo_suplencia_activo,
                                key="chk_suplencia_master")
    
    # Guardar estado de suplencia en el maletín si cambia
    if es_suplencia != st.session_state.modo_suplencia_activo:
        st.session_state.modo_suplencia_activo = es_suplencia
        respaldar_en_maletin()
    
    # Determinar lista de docentes para suplencia usando CACHÉ
    try:
        if st.session_state.cache_matricula is not None and not st.session_state.cache_matricula.empty:
            if 'DOCENTE_TITULAR' in st.session_state.cache_matricula.columns:
                lista_docentes_real = sorted(st.session_state.cache_matricula['DOCENTE_TITULAR'].dropna().unique().tolist())
            else: 
                lista_docentes_real = [st.session_state.u['NOMBRE']]
        else: 
            lista_docentes_real = [st.session_state.u['NOMBRE']]
    except: 
        lista_docentes_real = [st.session_state.u['NOMBRE']]

    if es_suplencia:
        lista_suplentes = [d for d in lista_docentes_real if d != st.session_state.u['NOMBRE']]
        if not lista_suplentes: 
            lista_suplentes = ["No hay otros docentes registrados"]
        titular = st.selectbox("Seleccione Docente Titular:", lista_suplentes, key="av_titular_v13")
        st.warning(f"Modo Suplencia: Usando planificación y alumnos de **{titular}**")
    else:
        titular = st.session_state.u['NOMBRE']
        st.success(f"Trabajando con tu planificación y alumnos ({titular}).")

    # --- 2. BUSCAR PLAN ACTIVO (USANDO CACHÉ) ---
    pa = None
    try:
        df_planes = st.session_state.cache_planes
        plan_activo = df_planes[
            (df_planes['USUARIO'] == titular) & 
            (df_planes['ESTADO'] == "ACTIVO")
        ]
        if not plan_activo.empty:
            fila = plan_activo.iloc[0]
            pa = {"CONTENIDO_PLAN": fila['CONTENIDO'], "RANGO": fila.get('FECHA', 'S/F')}
    except: 
        pass

    if not pa:
        st.error(f"🚨 {titular} no tiene un plan activo. Ve a Archivo Pedagógico y activa uno.")
        return 

    # --- 3. PESTAÑAS (TRÍADA PEDAGÓGICA) ---
    tab1, tab2, tab3 = st.tabs(["🚀 Ejecución (Inicio/Desarrollo)", "📝 Evaluación", "🏁 Cierre (Reflexión)"])

    # =====================================================================
    # PESTAÑA 1: EJECUCIÓN + ASISTENTE IA + CÁMARAS SECUENCIALES
    # =====================================================================
    with tab1:
        dias_es = {"Monday":"Lunes", "Tuesday":"Martes", "Wednesday":"Miércoles", "Thursday":"Jueves", "Friday":"Viernes", "Saturday":"Sábado", "Sunday":"Domingo"}
        dia_hoy_nombre = dias_es.get(ahora_ve().strftime("%A"))
        
        # Extracción por Regex - v14.0 Original
        patron = f"(?i)(###|\*\*)\s*{dia_hoy_nombre}.*?(?=(###|\*\*)\s*(Lunes|Martes|Miércoles|Jueves|Viernes)|$)"
        match = re.search(patron, pa["CONTENIDO_PLAN"], re.DOTALL)
        clase_dia = match.group(0) if match else None

        if clase_dia is None:
            st.warning(f"No hay actividad programada para hoy {dia_hoy_nombre}.")
            dia_m = st.selectbox("Seleccione día a ejecutar:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], key="av_manual_v13")
            patron_m = f"(?i)(###|\*\*)\s*{dia_m}.*?(?=(###|\*\*)\s*(Lunes|Martes|Miércoles|Jueves|Viernes)|$)"
            match_m = re.search(patron_m, pa["CONTENIDO_PLAN"], re.DOTALL)
            clase_de_hoy = match_m.group(0) if match_m else "Sin actividad encontrada en el plan."
        else:
            clase_de_hoy = clase_dia

        st.subheader("📖 Guía de la Actividad")
        if clase_de_hoy:
            st.markdown(f'<div class="plan-box">{clase_de_hoy}</div>', unsafe_allow_html=True)
            
            # Extracción Quirúrgica de Título y Desarrollo para la Evaluación
            try:
                lineas_plan = clase_de_hoy.split('\n')
                t_ext, c_ext = "Actividad del Día", "Sin contexto detallado."
                for linea in lineas_plan:
                    if "**1." in linea: 
                        t_ext = linea.split(":")[1].replace("**", "").strip() if ":" in linea else linea.replace("**1. TÍTULO DE LA ACTIVIDAD:**", "").strip()
                    if "**4." in linea: 
                        c_ext = linea.replace("**4. DESARROLLO (Proceso):**", "").strip()
                st.session_state.temp_titulo_extract = t_ext
                st.session_state.temp_contexto_extract = c_ext
            except:
                st.session_state.temp_titulo_extract = "Actividad General"
                st.session_state.temp_contexto_extract = clase_de_hoy[:200]
        
        # --- ASISTENTE IA EN VIVO ---
        with st.expander("🤖 Consultar al Asistente Pedagógico (IA)", expanded=False):
            st.caption("Escribe tus dudas sobre cómo mediar esta clase o adaptar materiales.")
            pregunta_docente = st.text_input("Tu pregunta:", key="chat_input_aula")
            if st.button("Consultar IA", key="btn_chat_aula"):
                if pregunta_docente:
                    with st.spinner("Super Docente pensando..."):
                        prompt_chat = f"PLANIFICACIÓN DE HOY: {clase_de_hoy}. PREGUNTA DEL DOCENTE: {pregunta_docente}. Responde de forma técnica y práctica."
                        resp_ia = generar_respuesta([{"role":"user","content":prompt_chat}], 0.7)
                        st.session_state.chat_asistente_aula.append({"user": pregunta_docente, "ia": resp_ia})
            
            # Historial del chat dentro de la clase
            for msg in reversed(st.session_state.chat_asistente_aula[-3:]):
                st.markdown(f"**Pregunta:** {msg['user']}")
                st.info(f"**Sugerencia:** {msg['ia']}")

        st.divider()
        
        # --- PEI EXPRESS ---
        with st.expander("🧩 Adaptación P.E.I. Express"):
            try:
                df_mat = st.session_state.cache_matricula
                alumnado = df_mat[df_mat['DOCENTE_TITULAR'] == titular]['NOMBRE_ALUMNO'].dropna().unique().tolist()
            except: 
                alumnado = []
            
            col_pei1, col_pei2 = st.columns(2)
            with col_pei1: 
                al_p = st.selectbox("Seleccione Alumno:", ["(Seleccionar)"] + sorted(alumnado), key="av_pei_al_v13")
            with col_pei2: 
                ctx_p = st.text_input("Crisis o Necesidad:", placeholder="Ej: No quiere tocar texturas...", key="av_pei_ctx_v13")
            
            if st.button("💡 Generar Estrategia de Apoyo", key="btn_av_ia_v13"):
                if al_p != "(Seleccionar)":
                    with st.spinner("Analizando perfil..."):
                        p_pei_ia = f"ACTIVIDAD: {clase_de_hoy}. ALUMNO: {al_p}. DIFICULTAD: {ctx_p}. Dame una adaptación vivencial inmediata."
                        st.markdown(f'<div class="eval-box">{generar_respuesta([{"role":"user","content":p_pei_ia}], 0.7)}</div>', unsafe_allow_html=True)
        
        st.divider()

        # --- SISTEMA DE CÁMARAS SECUENCIALES CON RESPALDO LOCAL ---
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("#### 1. Evidencia de Inicio")
            if st.session_state.av_foto1 is None:
                f1_cam = st.camera_input("Capturar Inicio", key="av_cam1_v13")
                if f1_cam and st.button("📤 Guardar Momento 1", key="btn_save_f1_v13"):
                    with st.spinner("Procesando..."):
                        u1_link = subir_a_imgbb(f1_cam)
                        # Si no hay internet, convertimos a Base64 para el maletín
                        st.session_state.av_foto1 = u1_link if u1_link else foto_a_texto(f1_cam)
                        respaldar_en_maletin()
                        st.rerun()
            else:
                st.image(st.session_state.av_foto1, use_container_width=True, caption="✅ Fase de Inicio")
                if st.button("♻️ Reset Foto 1", key="reset_f1_v13"): 
                    st.session_state.av_foto1 = None
                    respaldar_en_maletin()
                    st.rerun()

        with col_c2:
            st.markdown("#### 2. Evidencia de Desarrollo")
            if st.session_state.av_foto1 is None:
                st.info("🔒 Cámara de Desarrollo bloqueada. Capture el **Inicio** primero.")
            else:
                if st.session_state.av_foto2 is None:
                    f2_cam = st.camera_input("Capturar Proceso", key="av_cam2_v13")
                    if f2_cam and st.button("📤 Guardar Momento 2", key="btn_save_f2_v13"):
                        with st.spinner("Procesando..."):
                            u2_link = subir_a_imgbb(f2_cam)
                            st.session_state.av_foto2 = u2_link if u2_link else foto_a_texto(f2_cam)
                            respaldar_en_maletin()
                            st.rerun()
                else:
                    st.image(st.session_state.av_foto2, use_container_width=True, caption="✅ Fase de Desarrollo")
                    if st.button("♻️ Reset Foto 2", key="reset_f2_v13"): 
                        st.session_state.av_foto2 = None
                        respaldar_en_maletin()
                        st.rerun()

    # =====================================================================
    # PESTAÑA 2: EVALUACIÓN INDIVIDUAL - v14.0 ORIGINAL
    # =====================================================================
    with tab2:
        st.subheader("📝 Evaluación del Desempeño Estudiantil")
        try:
            df_m_v14 = st.session_state.cache_matricula
            alumnos_lista = df_m_v14[df_m_v14['DOCENTE_TITULAR'] == titular]['NOMBRE_ALUMNO'].dropna().unique().tolist()
        except: 
            alumnos_lista = []
        
        if not alumnos_lista:
            st.warning(f"No hay alumnos registrados para **{titular}** en la matrícula global.")
        else:
            sel_est = st.selectbox("Seleccione Estudiante a Evaluar:", sorted(alumnos_lista), key="av_eval_est_v13")
            
            if st.button("🔍 Cargar Actividad del Día", key="btn_load_act_v13_e"):
                st.session_state.av_titulo_hoy = st.session_state.get('temp_titulo_extract', 'Actividad de Taller')
                st.session_state.av_contexto_hoy = st.session_state.get('temp_contexto_extract', 'Sin descripción.')
                st.session_state.temp_propuesta_ia = ""
                respaldar_en_maletin()
                st.rerun()
            
            st.info(f"**Evaluando:** {st.session_state.av_titulo_hoy}")
            txt_obs = st.text_area("Observación Anecdótica (Hechos observables):", 
                                   placeholder="Describa qué hizo el alumno y cómo lo logró...",
                                   key="av_eval_obs_v13_e")
            
            # Botón de mejora IA preservado de v14
            if txt_obs and st.button("✨ Refinar Redacción Pedagógica (IA)", key="btn_ia_refine"):
                with st.spinner("Redactando nota profesional..."):
                    p_refine = f"ALUMNO: {sel_est}. HECHOS: {txt_obs}. CONTEXTO: {st.session_state.av_contexto_hoy}. Redacta una evaluación cualitativa profesional."
                    st.session_state.temp_propuesta_ia = generar_respuesta([{"role":"user","content":p_refine}], 0.5)
            
            if st.session_state.temp_propuesta_ia:
                st.success("Propuesta de la IA:")
                st.write(st.session_state.temp_propuesta_ia)

            if st.button("💾 GUARDAR EVALUACIÓN EN NUBE", type="primary", key="btn_save_eval_v14"):
                if txt_obs and st.session_state.av_titulo_hoy:
                    nota_final = st.session_state.temp_propuesta_ia if st.session_state.temp_propuesta_ia else txt_obs
                    try:
                        nueva_fila_ev = pd.DataFrame([{
                            "FECHA": ahora_ve().strftime("%d/%m/%Y"), 
                            "USUARIO": st.session_state.u['NOMBRE'], 
                            "DOCENTE_TITULAR": titular, 
                            "ESTUDIANTE": sel_est, 
                            "ACTIVIDAD": st.session_state.av_titulo_hoy, 
                            "ANECDOTA": txt_obs, 
                            "EVALUACION_IA": nota_final, 
                            "PLANIFICACION_ACTIVA": pa['RANGO']
                        }])
                        df_ev_v14 = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                        conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=pd.concat([df_ev_v14, nueva_fila_ev], ignore_index=True))
                        st.success(f"✅ Evaluación de {sel_est} guardada exitosamente.")
                        st.session_state.temp_propuesta_ia = ""
                        time.sleep(1); st.rerun()
                    except: 
                        st.error("Error: Sin conexión a Google Sheets. Intente al recuperar señal.")
                else: 
                    st.error("⚠️ Faltan datos (Actividad u Observación).")

    # =====================================================================
    # PESTAÑA 3: CIERRE - v14.0 COMPLETA
    # =====================================================================
    with tab3:
        st.subheader("🏁 Cierre y Consolidación de Jornada")
        try:
            f_hoy = ahora_ve().strftime("%d/%m/%Y")
            df_e_v14 = st.session_state.cache_ejecucion
            comprobar_cierre = not df_e_v14[(df_e_v14['USUARIO'] == st.session_state.u['NOMBRE']) & (df_e_v14['FECHA'] == f_hoy)].empty
        except: 
            comprobar_cierre = False
        
        if comprobar_cierre:
            st.success("✅ La jornada pedagógica de hoy ya ha sido consolidada en Dirección.")
            if st.button("🏠 Volver al Inicio"): 
                st.session_state.pagina_actual = "HOME"
                st.rerun()
        else:
            st.markdown("#### 3. Evidencia de Cierre (Resultado Final)")
            if st.session_state.av_foto2 is None:
                 st.info("🔒 Cámara de Cierre bloqueada. Complete la fase de **Desarrollo**.")
            else:
                if st.session_state.av_foto3 is None:
                    f3_cam = st.camera_input("Capturar Cierre", key="av_cam3_v13")
                    if f3_cam and st.button("📤 Guardar Momento 3", key="btn_save_f3_v13"):
                        with st.spinner("Subiendo..."):
                            u3_link = subir_a_imgbb(f3_cam)
                            st.session_state.av_foto3 = u3_link if u3_link else foto_a_texto(f3_cam)
                            respaldar_en_maletin()
                            st.rerun()
                else:
                    st.image(st.session_state.av_foto3, width=250, caption="✅ Fase de Cierre")
                    if st.button("♻️ Reset Foto 3", key="reset_f3_v13"): 
                        st.session_state.av_foto3 = None
                        respaldar_en_maletin()
                        st.rerun()

            st.divider()
            st.subheader("📝 Sistematización de Logros")
            st.session_state.av_resumen = st.text_area("Resumen Pedagógico del Día (Logros y retos):", 
                                                     value=st.session_state.av_resumen, 
                                                     key="av_res_v13_area", height=120)
            
            # Autoguardado del resumen al perder foco
            if st.session_state.av_resumen:
                respaldar_en_maletin()

            if st.button("🚀 CONSOLIDAR ACTIVIDAD Y SUMAR MÉRITOS", type="primary", key="btn_final_consolidar"):
                if not st.session_state.av_foto3: 
                    st.error("⚠️ Falta la foto de culminación de la clase.")
                elif not st.session_state.av_resumen: 
                    st.error("⚠️ Debe redactar el resumen de logros de la jornada.")
                else:
                    with st.spinner("Enviando bitácora final a Dirección..."):
                        try:
                            f_str = f"{st.session_state.av_foto1}|{st.session_state.av_foto2}|{st.session_state.av_foto3}"
                            nueva_ejecucion = pd.DataFrame([{
                                "FECHA": f_hoy, 
                                "USUARIO": st.session_state.u['NOMBRE'], 
                                "DOCENTE_TITULAR": titular, 
                                "ACTIVIDAD_TITULO": st.session_state.av_titulo_hoy or "Jornada Pedagógica", 
                                "EVIDENCIA_FOTO": f_str, 
                                "RESUMEN_LOGROS": st.session_state.av_resumen, 
                                "ESTADO": "CULMINADA", 
                                "PUNTOS": 5
                            }])
                            df_ej_v14 = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                            conn.update(spreadsheet=URL_HOJA, worksheet="EJECUCION", data=pd.concat([df_ej_v14, nueva_ejecucion], ignore_index=True))
                            
                            # LIMPIEZA TOTAL (Nube exitosa -> Borrar Maletín)
                            st.session_state.av_foto1 = st.session_state.av_foto2 = st.session_state.av_foto3 = None
                            st.session_state.av_resumen = ""
                            from utils.maletin import borrar_del_dispositivo
                            borrar_del_dispositivo("maletin_super_docente")
                            
                            st.balloons()
                            st.success("✅ ¡Felicidades! Actividad consolidada y méritos sumados.")
                            time.sleep(2)
                            st.session_state.pagina_actual = "HOME"
                            st.rerun()
                        except:
                            st.error("⚠️ Fallo de conexión. Sus datos y fotos están seguros en la memoria de este teléfono.")
