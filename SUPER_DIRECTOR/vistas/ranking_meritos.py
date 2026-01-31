import streamlit as st
import pandas as pd
import time

def render_ranking(conn, URL_HOJA):
    try:
        df_as = conn.read(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", ttl=0)
        df_ej = conn.read(spreadsheet=URL_HOJA, worksheet="EJECUCION", ttl=0)
        df_us = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
    except:
        st.error("Error al cargar datos de méritos.")
        return

    st.subheader("🏆 Cuadro de Honor: Docente del Año")
    st.markdown("Cómputo automático de puntos por cumplimiento, ejecución y solidaridad.")

    pts_as = df_as.groupby('USUARIO')['PUNTOS_MERITO'].sum().reset_index()
    pts_ej = df_ej[df_ej['ESTADO'] == 'CULMINADA'].groupby('USUARIO')['PUNTOS'].sum().reset_index()
    
    ranking = df_us[df_us['ROL'] != 'DIRECTOR'][['NOMBRE']].copy()
    ranking = ranking.merge(pts_as, left_on='NOMBRE', right_on='USUARIO', how='left').fillna(0)
    ranking = ranking.merge(pts_ej, left_on='NOMBRE', right_on='USUARIO', how='left').fillna(0)
    
    ranking['TOTAL'] = ranking['PUNTOS_MERITO'] + ranking['PUNTOS']
    ranking = ranking[['NOMBRE', 'PUNTOS_MERITO', 'PUNTOS', 'TOTAL']].sort_values(by='TOTAL', ascending=False)

    col1, col2, col3 = st.columns(3)
    top = ranking.head(3)
    
    if not top.empty:
        with col1:
            if len(top) >= 1:
                st.markdown(f"🥇 **1er Lugar**\n### {top.iloc[0]['NOMBRE']}\n{top.iloc[0]['TOTAL']} pts")
        with col2:
            if len(top) >= 2:
                st.markdown(f"🥈 **2do Lugar**\n### {top.iloc[1]['NOMBRE']}\n{top.iloc[1]['TOTAL']} pts")
        with col3:
            if len(top) >= 3:
                st.markdown(f"🥉 **3er Lugar**\n### {top.iloc[2]['NOMBRE']}\n{top.iloc[2]['TOTAL']} pts")

    st.divider()

    st.dataframe(
        ranking.rename(columns={
            'NOMBRE': 'Docente',
            'PUNTOS_MERITO': 'Pts. Asistencia',
            'PUNTOS': 'Pts. Actividades',
            'TOTAL': 'Puntaje Total'
        }),
        hide_index=True,
        use_container_width=True
    )

    st.divider()
    st.markdown("### 🎖️ Asignar Puntos Extraordinarios")
    st.caption("Uso exclusivo del Director para premiar labores especiales (Comisiones, Eventos, Carteleras).")
    
    with st.form("puntos_manuales"):
        doc_sel = st.selectbox("Seleccione Docente:", df_us[df_us['ROL'] != 'DIRECTOR']['NOMBRE'])
        pts_ext = st.number_input("Puntos a otorgar:", min_value=1, max_value=50, value=5)
        motivo_ext = st.text_input("Motivo del reconocimiento:")
        btn_ext = st.form_submit_button("Otorgar Mérito Especial")
        
        if btn_ext:
            if motivo_ext:
                nueva_as = pd.DataFrame([{
                    "FECHA": time.strftime("%d/%m/%Y"),
                    "USUARIO": doc_sel,
                    "TIPO": "MÉRITO ESPECIAL",
                    "HORA_ENTRADA": "-",
                    "FOTO_ENTRADA": "-",
                    "HORA_SALIDA": "-",
                    "FOTO_SALIDA": "-",
                    "MOTIVO": motivo_ext,
                    "ALERTA_IA": "BONO_DIRECTOR",
                    "ESTADO_DIRECTOR": "APROBADO",
                    "PUNTOS_MERITO": pts_ext,
                    "SUPLENCIA_A": "-"
                }])
                df_final = pd.concat([df_as, nueva_as], ignore_index=True)
                conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_final)
                st.success(f"Se han otorgado {pts_ext} puntos a {doc_sel}.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Debe indicar un motivo para el mérito especial.")
