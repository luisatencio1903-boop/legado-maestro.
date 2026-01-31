import streamlit as st
import pandas as pd
import time

def render_validacion(conn, URL_HOJA):
    try:
        df_as = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=0)
        df_ej = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
    except:
        st.error("Error al conectar con la base de datos.")
        return

    tab1, tab2 = st.tabs(["🕒 Asistencias", "🏫 Actividades de Aula"])

    with tab1:
        st.subheader("Validación de Asistencia Biométrica")
        pendientes_as = df_as[df_as['ESTADO_DIRECTOR'] == "PENDIENTE"]
        
        if pendientes_as.empty:
            st.success("No hay asistencias pendientes por validar.")
        else:
            for idx, fila in pendientes_as.iterrows():
                with st.expander(f"👤 {fila['USUARIO']} | 📅 {fila['FECHA']} | {fila['TIPO']}"):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if fila['FOTO_ENTRADA'] != "-":
                            st.image(fila['FOTO_ENTRADA'], caption="Foto Entrada")
                        if fila['FOTO_SALIDA'] != "-":
                            st.image(fila['FOTO_SALIDA'], caption="Foto Salida")
                    with c2:
                        st.write(f"**Hora Entrada:** {fila['HORA_ENTRADA']}")
                        st.write(f"**Hora Salida:** {fila['HORA_SALIDA']}")
                        st.write(f"**Justificación:** {fila['MOTIVO']}")
                        st.write(f"**Alerta Sistema:** {fila['ALERTA_IA']}")
                        
                        col_b1, col_b2 = st.columns(2)
                        if col_b1.button("✅ Aprobar", key=f"btn_ap_as_{idx}"):
                            df_as.at[idx, 'ESTADO_DIRECTOR'] = "APROBADO"
                            conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_as)
                            st.rerun()
                        if col_b2.button("❌ Rechazar", key=f"btn_re_as_{idx}"):
                            df_as.at[idx, 'ESTADO_DIRECTOR'] = "RECHAZADO"
                            conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_as)
                            st.rerun()

    with tab2:
        st.subheader("Certificación de Actividades Culminadas")
        pendientes_ej = df_ej[df_ej['ESTADO'] == "PENDIENTE"]
        
        if pendientes_ej.empty:
            st.success("No hay actividades de aula pendientes por certificar.")
        else:
            for idx, fila in pendientes_ej.iterrows():
                with st.expander(f"🏫 {fila['ACTIVIDAD_TITULO']} | 👤 {fila['USUARIO']}"):
                    st.write(f"**Fecha:** {fila['FECHA']}")
                    
                    fotos = str(fila['EVIDENCIA_FOTO']).split('|')
                    cols_f = st.columns(len(fotos))
                    for i, f_url in enumerate(fotos):
                        if "http" in f_url:
                            cols_f[i].image(f_url.strip(), use_container_width=True)
                    
                    st.write(f"**Resumen de Logros:** {fila['RESUMEN_LOGROS']}")
                    
                    col_b3, col_b4 = st.columns(2)
                    if col_b3.button("🏆 Certificar Actividad", key=f"btn_ap_ej_{idx}"):
                        df_ej.at[idx, 'ESTADO'] = "CULMINADA"
                        conn.update(spreadsheet=URL_HOJA, worksheet="EJECUCION", data=df_ej)
                        st.rerun()
                    if col_b4.button("❌ Invalidar", key=f"btn_re_ej_{idx}"):
                        df_ej.at[idx, 'ESTADO'] = "RECHAZADA"
                        conn.update(spreadsheet=URL_HOJA, worksheet="EJECUCION", data=df_ej)
                        st.rerun()
