import streamlit as st
import pandas as pd
import time
from utils.comunes import ahora_ve

def render_archivo(conn):
    st.title("📂 Mi Archivo Pedagógico")
    st.info("Gestiona tus documentos, activa planes antiguos y revisa tu historial.")

    # URL Helper
    try:
        url = st.secrets["GSHEETS_URL"]
    except:
        st.error("Error de configuración (Secrets).")
        return

    # Pestañas de Gestión
    tab_planes, tab_eval, tab_bit = st.tabs(["📜 Mis Planificaciones", "📝 Registro de Evaluaciones", "🚀 Bitácora de Clases"])

    # ==========================================================
    # PESTAÑA 1: GESTIÓN DE PLANES (Hoja1)
    # ==========================================================
    with tab_planes:
        col_up, col_info = st.columns([1, 3])
        with col_up:
            if st.button("🔄 Actualizar Lista", key="btn_refresh_planes"):
                st.cache_data.clear()
                st.rerun()
        
        # Cargar datos frescos
        try:
            df_planes = conn.read(spreadsheet=url, worksheet="Hoja1", ttl=0)
            # Filtrar solo mis planes (Regla de Oro: Privacidad)
            mis_planes = df_planes[df_planes['USUARIO'] == st.session_state.u['NOMBRE']].copy()
            
            if mis_planes.empty:
                st.warning("No tienes planificaciones guardadas.")
            else:
                # Mostrar del más nuevo al más viejo
                mis_planes = mis_planes.sort_index(ascending=False)
                
                st.write(f"Tienes **{len(mis_planes)}** planes guardados.")
                
                for i, row in mis_planes.iterrows():
                    # Estado Visual
                    es_activo = row.get('ESTADO') == 'ACTIVO'
                    icono = "🟢" if es_activo else "⚫"
                    titulo_expander = f"{icono} {row.get('TITULO', 'Sin Título')} | {row.get('FECHA', 'S/F')}"
                    
                    with st.expander(titulo_expander):
                        st.caption(f"**Tipo:** {row.get('TIPO', '--')} | **Creado:** {row.get('CREADO_EL', '--')}")
                        st.text_area("Contenido:", value=row.get('CONTENIDO', ''), height=200, disabled=True, key=f"txt_p_{i}")
                        
                        c1, c2 = st.columns(2)
                        
                        # BOTÓN 1: ACTIVAR (Lógica de Switch)
                        with c1:
                            if not es_activo:
                                if st.button(f"⚡ ACTIVAR ESTE PLAN", key=f"btn_act_{i}"):
                                    with st.spinner("Cambiando plan activo..."):
                                        # 1. Ponemos INACTIVO a todos los planes de este usuario
                                        df_planes.loc[df_planes['USUARIO'] == st.session_state.u['NOMBRE'], 'ESTADO'] = 'INACTIVO'
                                        # 2. Ponemos ACTIVO solo a este (usando el índice original 'i')
                                        df_planes.at[i, 'ESTADO'] = 'ACTIVO'
                                        # 3. Guardamos
                                        conn.update(spreadsheet=url, worksheet="Hoja1", data=df_planes)
                                        st.success("✅ Plan Activado. Ve al Aula Virtual.")
                                        time.sleep(1)
                                        st.rerun()
                            else:
                                st.button("✅ YA ESTÁ ACTIVO", disabled=True, key=f"btn_dsb_{i}")

                        # BOTÓN 2: ELIMINAR
                        with c2:
                            if st.button(f"🗑️ Eliminar Definitivamente", key=f"btn_del_{i}"):
                                with st.spinner("Borrando..."):
                                    # Borrar fila por índice
                                    df_planes = df_planes.drop(i)
                                    conn.update(spreadsheet=url, worksheet="Hoja1", data=df_planes)
                                    st.success("🗑️ Eliminado.")
                                    time.sleep(1)
                                    st.rerun()

        except Exception as e:
            st.error(f"Error cargando planes: {e}")

    # ==========================================================
    # PESTAÑA 2: EVALUACIONES (Lectura)
    # ==========================================================
    with tab_eval:
        if st.button("🔄 Refrescar Notas", key="btn_refresh_eval"):
            st.cache_data.clear(); st.rerun()
            
        try:
            df_ev = conn.read(spreadsheet=url, worksheet="EVALUACIONES", ttl=0)
            mis_evals = df_ev[df_ev['USUARIO'] == st.session_state.u['NOMBRE']]
            
            if mis_evals.empty:
                st.info("No has registrado evaluaciones.")
            else:
                # Mostramos tabla interactiva
                st.dataframe(mis_evals[['FECHA', 'ESTUDIANTE', 'ACTIVIDAD', 'EVALUACION_IA']], use_container_width=True)
        except Exception as e:
            st.error("No se pudo leer la hoja EVALUACIONES.")

    # ==========================================================
    # PESTAÑA 3: BITÁCORA (Lectura)
    # ==========================================================
    with tab_bit:
        if st.button("🔄 Refrescar Bitácora", key="btn_refresh_bit"):
            st.cache_data.clear(); st.rerun()
            
        try:
            df_bit = conn.read(spreadsheet=url, worksheet="EJECUCION", ttl=0)
            mis_bit = df_bit[df_bit['USUARIO'] == st.session_state.u['NOMBRE']]
            
            if mis_bit.empty:
                st.info("No has consolidado clases aún.")
            else:
                st.dataframe(mis_bit[['FECHA', 'ACTIVIDAD_TITULO', 'RESUMEN_LOGROS']], use_container_width=True)
        except Exception as e:
            st.error("No se pudo leer la hoja EJECUCION.")
