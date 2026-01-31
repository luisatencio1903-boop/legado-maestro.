import streamlit as st
import pandas as pd
import time

# Actualizamos la entrada para recibir el universo de datos
def render_ranking(conn, URL_HOJA, universo):
    try:
        # --- CAMBIO CLAVE: Usamos los datos ya cargados en memoria ---
        # Usamos .copy() para manipular los datos sin afectar la fuente original hasta guardar
        df_as = universo['ASISTENCIA'].copy()
        df_ej = universo['EJECUCION'].copy()
        df_us = universo['USUARIOS'].copy()
    except KeyError as e:
        st.error(f"Error técnico: Falta la hoja {e} en la carga de datos.")
        return
    except Exception as e:
        st.error(f"Error al procesar datos de méritos: {e}")
        return

    st.subheader("🏆 Cuadro de Honor: Docente del Año")
    st.markdown("Cómputo automático de puntos por cumplimiento, ejecución y solidaridad.")

    # --- LÓGICA DE CÁLCULO (Se mantiene idéntica, solo que ahora es instantánea) ---
    pts_as = df_as.groupby('USUARIO')['PUNTOS_MERITO'].sum().reset_index()
    # Filtramos solo actividades culminadas para sumar puntos
    pts_ej = df_ej[df_ej['ESTADO'] == 'CULMINADA'].groupby('USUARIO')['PUNTOS'].sum().reset_index()
    
    # Preparamos el ranking base excluyendo al director
    ranking = df_us[df_us['ROL'] != 'DIRECTOR'][['NOMBRE']].copy()
    
    # Cruzamos (Merge) los puntos de asistencia y ejecución
    ranking = ranking.merge(pts_as, left_on='NOMBRE', right_on='USUARIO', how='left').fillna(0)
    ranking = ranking.merge(pts_ej, left_on='NOMBRE', right_on='USUARIO', how='left').fillna(0)
    
    # Calculamos totales
    ranking['TOTAL'] = ranking['PUNTOS_MERITO'] + ranking['PUNTOS']
    ranking = ranking[['NOMBRE', 'PUNTOS_MERITO', 'PUNTOS', 'TOTAL']].sort_values(by='TOTAL', ascending=False)

    # --- VISUALIZACIÓN DEL PODIO ---
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
        # Usamos la lista de usuarios cargada en memoria
        doc_sel = st.selectbox("Seleccione Docente:", df_us[df_us['ROL'] != 'DIRECTOR']['NOMBRE'])
        pts_ext = st.number_input("Puntos a otorgar:", min_value=1, max_value=50, value=5)
        motivo_ext = st.text_input("Motivo del reconocimiento:")
        btn_ext = st.form_submit_button("Otorgar Mérito Especial")
        
        if btn_ext:
            if motivo_ext:
                # Creamos el nuevo registro
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
                
                # Unimos con el histórico actual (que vino del universo)
                df_final = pd.concat([df_as, nueva_as], ignore_index=True)
                
                # ESCRITURA: Aquí sí usamos conn para guardar en la nube
                try:
                    conn.update(spreadsheet=URL_HOJA, worksheet="ASISTENCIA", data=df_final)
                    st.success(f"Se han otorgado {pts_ext} puntos a {doc_sel}.")
                    
                    # Limpiamos caché para que al recargar aparezca el nuevo puntaje
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar en la base de datos: {e}")
            else:
                st.error("Debe indicar un motivo para el mérito especial.")
