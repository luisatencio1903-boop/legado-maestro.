import streamlit as st
import pandas as pd
import time
from utils.comunes import ahora_ve
from cerebros.nucleo import generar_respuesta

def render_archivo(conn):
    # Recuperamos URL para las funciones internas
    try:
        URL_HOJA = st.secrets["GSHEETS_URL"]
    except:
        st.error("Error: No se detectó la configuración de secretos (GSHEETS_URL).")
        return

    # -------------------------------------------------------------------------
    # CÓDIGO ORIGINAL RESTAURADO (VERSIÓN MAESTRA)
    # -------------------------------------------------------------------------
        
    # --- 1. GESTIÓN DE MEMORIA Y ESTADO ---
    if 'visor_plan_activo' not in st.session_state: st.session_state.visor_plan_activo = False
    if 'visor_plan_data' not in st.session_state: st.session_state.visor_plan_data = {}
    if 'resumen_alumno_ia' not in st.session_state: st.session_state.resumen_alumno_ia = ""
    if 'alumno_seleccionado_temp' not in st.session_state: st.session_state.alumno_seleccionado_temp = None
    
    # Inicialización del Caché (Las fotocopias)
    if 'cache_ejecucion' not in st.session_state: st.session_state.cache_ejecucion = None
    if 'cache_evaluaciones' not in st.session_state: st.session_state.cache_evaluaciones = None
    if 'cache_planes' not in st.session_state: st.session_state.cache_planes = None
    if 'cache_pensums' not in st.session_state: st.session_state.cache_pensums = None

    # --- FUNCIÓN DE SINCRONIZACIÓN (IR A DIRECCIÓN) ---
    def sincronizar_datos():
        try:
            with st.spinner("🔄 Yendo a dirección a actualizar los archivos..."):
                st.session_state.cache_ejecucion = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
                st.session_state.cache_evaluaciones = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                st.session_state.cache_planes = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                st.session_state.cache_pensums = conn.read(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", ttl=0)
            st.success("✅ Datos actualizados.")
            time.sleep(0.5)
        except Exception as e: st.error(f"Error sincronizando: {e}")

    # --- FUNCIÓN TARJETA BITÁCORA ---
    def renderizar_tarjeta(row_act, df_evals):
        fecha = row_act['FECHA']
        titulo = row_act['ACTIVIDAD_TITULO']
        resumen = row_act['RESUMEN_LOGROS']
        fotos_str = str(row_act['EVIDENCIA_FOTO'])
        
        with st.container(border=True):
            c_tit, c_fecha = st.columns([4, 1])
            c_tit.markdown(f"**📌 {titulo}**")
            c_fecha.caption(f"📅 {fecha}")
            
            if fotos_str and fotos_str != "None" and fotos_str != "":
                urls = fotos_str.split("|") if "|" in fotos_str else [fotos_str]
                cols_f = st.columns(len(urls))
                for i, url in enumerate(urls):
                    with cols_f[i]:
                        if "http" in url: st.image(url, use_container_width=True)
            else: st.info("📷 Sin foto.")
            
            if resumen and resumen != "None": st.markdown(f"**📝 Bitácora:** {resumen}")

            if not df_evals.empty:
                evals_dia = df_evals[df_evals['FECHA'] == fecha]
                if not evals_dia.empty:
                    st.divider()
                    st.markdown("📊 **Resultados:**")
                    col_juicio = 'EVALUACION_IA' if 'EVALUACION_IA' in evals_dia.columns else None
                    if col_juicio:
                        textos = evals_dia[col_juicio].astype(str).str.upper()
                        cons = textos.str.count("CONSOLIDADO").sum()
                        proc = textos.str.count("PROCESO").sum()
                        ini = textos.str.count("INICIADO").sum()
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Total", len(evals_dia))
                        m2.metric("Consolidado", int(cons))
                        m3.metric("Proceso", int(proc))
                        m4.metric("Iniciado", int(ini))

    # --- ENCABEZADO ---
    if not st.session_state.visor_plan_activo:
        c_head, c_btn = st.columns([3, 1])
        with c_head: st.header("📂 Mi Archivo Pedagógico")
        with c_btn:
            if st.button("🔄 ACTUALIZAR DATOS", help="Recargar desde Google Sheets"):
                sincronizar_datos()
                st.rerun()

    # Carga inicial automática si está vacío
    if st.session_state.cache_ejecucion is None:
        sincronizar_datos()
        st.rerun()

    # --- FILTRADO DE DATOS (USANDO CACHÉ) ---
    try:
        df_full = st.session_state.cache_ejecucion
        mis_clases = df_full[df_full['USUARIO'] == st.session_state.u['NOMBRE']]

        df_ev_full = st.session_state.cache_evaluaciones
        mis_evaluaciones = df_ev_full[df_ev_full['USUARIO'] == st.session_state.u['NOMBRE']] if not df_ev_full.empty else pd.DataFrame()

        df_pl_full = st.session_state.cache_planes
        mis_planes = df_pl_full[df_pl_full['USUARIO'] == st.session_state.u['NOMBRE']] if not df_pl_full.empty else pd.DataFrame()

        df_pe_full = st.session_state.cache_pensums
        mis_pensums = df_pe_full[(df_pe_full['USUARIO'] == st.session_state.u['NOMBRE']) & (df_pe_full['ESTADO'] == "ACTIVO")] if not df_pe_full.empty else pd.DataFrame()

    except Exception as e:
        st.warning("Cargando datos...")
        st.stop()

    # =====================================================================
    # MODO VISOR (PANTALLA COMPLETA)
    # =====================================================================
    if st.session_state.visor_plan_activo:
        data = st.session_state.visor_plan_data
        idx_original = data['INDICE_ORIGINAL']
        
        c_back, c_tit = st.columns([1, 6])
        with c_back:
            if st.button("🔙 VOLVER", use_container_width=True):
                st.session_state.visor_plan_activo = False
                st.rerun()
        with c_tit:
            st.subheader(f"📖 Editando: {data['TEMA']}")

        texto_editado = st.text_area("Contenido:", value=data['CONTENIDO'], height=600)
        
        if st.button("💾 GUARDAR CAMBIOS (NUBE)", type="primary", use_container_width=True):
            try:
                df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                df_master.at[idx_original, 'CONTENIDO'] = texto_editado
                conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                # Actualizar caché
                st.session_state.cache_planes.at[idx_original, 'CONTENIDO'] = texto_editado
                st.session_state.visor_plan_data['CONTENIDO'] = texto_editado
                st.success("✅ Guardado.")
            except Exception as e: st.error(f"Error: {e}")

    # =====================================================================
    # MODO NORMAL (PESTAÑAS)
    # =====================================================================
    else:
        tab_bitacora, tab_planes, tab_evals = st.tabs(["📸 Bitácora", "🗓️ Planificaciones", "📊 Evaluaciones"])

        # --- PESTAÑA 1: BITÁCORA (CON LAS CARPETAS VISIBLES) ---
        with tab_bitacora:
            st.subheader("📸 Bitácora de Clases")
            opciones = ["📘 Portafolio General"]
            mapa_pensums = {}
            for i, row in mis_pensums.iterrows():
                opciones.append(f"🟢 Pensum: {row['TITULO_PENSUM']}")
                mapa_pensums[row['TITULO_PENSUM']] = row['CONTENIDO_FULL']
            seleccion = st.selectbox("Portafolio:", opciones)
            st.divider()

            if "General" in seleccion:
                clases_general = mis_clases[(mis_clases['ID_BLOQUE'].isna()) | (mis_clases['ID_BLOQUE'].astype(str) == "0")].sort_values(by="FECHA", ascending=False)
                if clases_general.empty: st.info("No hay bitácoras generales.")
                else:
                    clases_general['MES'] = pd.to_datetime(clases_general['FECHA'], dayfirst=True, errors='coerce').dt.strftime('%B %Y')
                    for mes in clases_general['MES'].unique():
                        with st.expander(f"🗓️ {mes}", expanded=True):
                            for i, row in clases_general[clases_general['MES'] == mes].iterrows():
                                renderizar_tarjeta(row, mis_evaluaciones)
            else:
                # LÓGICA DE PENSUMS (CORREGIDA PARA MOSTRAR CARPETAS VACÍAS)
                nombre_pensum = seleccion.replace("🟢 Pensum: ", "")
                texto_full = mapa_pensums.get(nombre_pensum, "")
                nombres_bloques = {}
                import re
                for line in texto_full.split('\n'):
                    match = re.search(r'(\d+)\.\s*BLOQUE:?\s*(.*)', line, re.IGNORECASE)
                    if match: nombres_bloques[int(match.group(1))] = match.group(2).strip()
                
                # Generamos SIEMPRE los bloques del 1 al 14 (o los que haya)
                for num_bloque in range(1, 15):
                    titulo_bloque = nombres_bloques.get(num_bloque, "Tema Específico")
                    
                    # Filtramos las clases de este bloque
                    mis_clases['ID_BLOQUE_STR'] = mis_clases['ID_BLOQUE'].astype(str).str.replace(".0", "").str.strip()
                    clases_bloque = mis_clases[mis_clases['ID_BLOQUE_STR'] == str(num_bloque)].sort_values(by="FECHA", ascending=False)
                    
                    cantidad = len(clases_bloque)
                    # Icono cambia si tiene contenido o no, pero la carpeta SIEMPRE APARECE
                    icono = "📂" if cantidad > 0 else "📁"
                    estado_abierto = True if cantidad > 0 else False
                    
                    # Renderizamos el expander SIEMPRE
                    with st.expander(f"{icono} BLOQUE {num_bloque}: {titulo_bloque} ({cantidad})", expanded=estado_abierto):
                        if clases_bloque.empty:
                            st.caption("📭 Carpeta vacía. Esperando consolidación de actividad...")
                        else:
                            for i, row in clases_bloque.iterrows(): 
                                renderizar_tarjeta(row, mis_evaluaciones)

        # --- PESTAÑA 2: PLANIFICACIONES (CON SWITCH Y CACHÉ) ---
        with tab_planes:
            st.subheader("🗓️ Gestión de Planificaciones")
            if mis_planes.empty: st.info("No hay planes guardados.")
            else:
                mis_planes_sorted = mis_planes.sort_index(ascending=False)
                for i, row in mis_planes_sorted.iterrows():
                    fecha = row['FECHA']
                    tema = row['TEMA']
                    contenido = row['CONTENIDO']
                    estado = str(row['ESTADO']).strip().upper() if 'ESTADO' in row else "GUARDADO"
                    es_activa = (estado == "ACTIVO")
                    
                    titulo_card = f"🟢 {fecha} | {tema} (ACTIVA)" if es_activa else f"⚪ {fecha} | {tema}"
                    
                    with st.expander(titulo_card, expanded=es_activa):
                        c_tog, c_visor, c_del = st.columns([2, 2, 1])
                        with c_tog:
                            if st.toggle("Activa", value=es_activa, key=f"tog_{i}"):
                                if not es_activa:
                                    try:
                                        df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                                        df_master.loc[df_master['USUARIO'] == st.session_state.u['NOMBRE'], 'ESTADO'] = "GUARDADO"
                                        df_master.at[i, 'ESTADO'] = "ACTIVO"
                                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                                        # Actualizar caché manualmente para no recargar todo
                                        st.session_state.cache_planes.loc[st.session_state.cache_planes['USUARIO'] == st.session_state.u['NOMBRE'], 'ESTADO'] = "GUARDADO"
                                        st.session_state.cache_planes.at[i, 'ESTADO'] = "ACTIVO"
                                        st.toast("⚡ ACTIVADA")
                                        time.sleep(0.5)
                                        st.rerun()
                                    except: pass
                            else:
                                if es_activa:
                                    try:
                                        df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                                        df_master.at[i, 'ESTADO'] = "GUARDADO"
                                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                                        st.session_state.cache_planes.at[i, 'ESTADO'] = "GUARDADO"
                                        st.rerun()
                                    except: pass
                        
                        with c_visor:
                            if st.button("📖 VISOR", key=f"v_{i}", use_container_width=True):
                                st.session_state.visor_plan_activo = True
                                row_d = row.to_dict(); row_d['INDICE_ORIGINAL'] = i
                                st.session_state.visor_plan_data = row_d
                                st.rerun()
                        
                        with c_del:
                            if st.button("🗑️", key=f"d_{i}"):
                                try:
                                    df_master = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                                    df_master = df_master.drop(index=i)
                                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_master)
                                    st.session_state.cache_planes = st.session_state.cache_planes.drop(index=i)
                                    st.rerun()
                                except: pass

        # --- PESTAÑA 3: EVALUACIONES (USANDO CACHÉ = VELOCIDAD) ---
        with tab_evals:
            st.subheader("📊 Historial Académico")
            if mis_evaluaciones.empty:
                st.info("No hay evaluaciones.")
            else:
                lista_estudiantes = sorted(mis_evaluaciones['ESTUDIANTE'].dropna().unique())
                # Selección segura con memoria
                idx_sel = 0
                if st.session_state.alumno_seleccionado_temp in lista_estudiantes:
                    idx_sel = lista_estudiantes.index(st.session_state.alumno_seleccionado_temp)
                
                seleccion_alumno = st.selectbox("👤 Selecciona un Estudiante:", lista_estudiantes, index=idx_sel)
                st.session_state.alumno_seleccionado_temp = seleccion_alumno
                
                if seleccion_alumno:
                    df_alumno = mis_evaluaciones[mis_evaluaciones['ESTUDIANTE'] == seleccion_alumno].sort_values(by="FECHA", ascending=False)
                    
                    c_m1, c_m2 = st.columns([1, 2])
                    c_m1.metric("Registros", len(df_alumno))
                    with c_m2:
                        if st.button("✨ Generar Boletín (IA)", key="btn_bol_ia", use_container_width=True):
                            with st.spinner("Analizando..."):
                                txt = ""
                                for _, r in df_alumno.iterrows():
                                    txt += f"- {r['FECHA']}: {r.get('ANECDOTA','')} | {r.get('EVALUACION_IA','')}\n"
                                st.session_state.resumen_alumno_ia = generar_respuesta([{"role":"user","content":f"Redacta un informe cualitativo para el boletín escolar de {seleccion_alumno} basado en: {txt}"}], 0.7)

                    if st.session_state.resumen_alumno_ia:
                        st.info("📄 Informe:")
                        st.write(st.session_state.resumen_alumno_ia)
                        if st.button("Cerrar"):
                            st.session_state.resumen_alumno_ia = ""
                            st.rerun()
                    
                    st.divider()
                    st.dataframe(df_alumno[['FECHA', 'ACTIVIDAD', 'ANECDOTA', 'EVALUACION_IA']], hide_index=True, use_container_width=True)
