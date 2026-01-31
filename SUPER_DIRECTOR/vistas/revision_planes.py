import streamlit as st
import pandas as pd
import time

def render_revision(conn, URL_HOJA):
    try:
        df_planes = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
    except:
        st.error("Error al conectar con el archivo pedagógico.")
        return

    st.subheader("📩 Buzón de Planificaciones Semanales")
    st.markdown("Revisión de planes enviados para la implementación de la próxima semana.")

    pendientes = df_planes[df_planes['ESTADO'] == "PENDIENTE"]

    if pendientes.empty:
        st.success("No hay planificaciones nuevas por revisar en el buzón.")
    else:
        for idx, fila in pendientes.iterrows():
            with st.expander(f"📄 {fila['TEMA']} | 👤 {fila['USUARIO']} | 📅 {fila['FECHA']}"):
                st.markdown(f'<div class="plan-box">{fila["CONTENIDO"]}</div>', unsafe_allow_html=True)
                
                st.divider()
                st.markdown("#### ⚖️ Decisión de Dirección")
                comentario = st.text_area("Sugerencias o correcciones (Solo si manda a corregir):", key=f"com_{idx}")
                
                c1, c2 = st.columns(2)
                
                if c1.button("✅ Aprobar e Implementar", key=f"btn_ap_pl_{idx}", use_container_width=True):
                    df_planes.at[idx, 'ESTADO'] = "APROBADO"
                    df_planes.at[idx, 'COMENTARIO_DIRECTOR'] = "Aprobada para su ejecución."
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_planes)
                    st.success("Planificación aprobada.")
                    time.sleep(1)
                    st.rerun()
                
                if c2.button("❌ Mandar a Corregir", key=f"btn_re_pl_{idx}", use_container_width=True):
                    if comentario:
                        df_planes.at[idx, 'ESTADO'] = "CORRECCION"
                        df_planes.at[idx, 'COMENTARIO_DIRECTOR'] = comentario
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_planes)
                        st.warning("Planificación devuelta para correcciones.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Debe escribir un comentario para que el docente sepa qué corregir.")
