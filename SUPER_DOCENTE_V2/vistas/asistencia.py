import streamlit as st
import pandas as pd
import time
from utils.comunes import ahora_ve

def render_asistencia(conn):
    st.title("⏱️ Control de Asistencia")
    st.info("Registro oficial de entrada y salida docente.")

    # --- 1. RELOJ VENEZUELA (Regla de Oro: Tu horario real) ---
    hora_actual = ahora_ve()
    str_fecha = hora_actual.strftime("%d/%m/%Y")
    str_hora = hora_actual.strftime("%I:%M %p")
    
    c1, c2 = st.columns(2)
    c1.metric("📅 Fecha", str_fecha)
    c2.metric("⌚ Hora", str_hora)
    st.divider()

    # --- 2. CONEXIÓN Y VERIFICACIÓN ---
    try:
        url = st.secrets["GSHEETS_URL"]
        # Leemos sin caché (ttl=0) para ver cambios en tiempo real
        df_asis = conn.read(spreadsheet=url, worksheet="ASISTENCIA", ttl=0)
        
        # Filtramos: Solo TÚ y solo HOY
        mi_registro = df_asis[
            (df_asis['USUARIO'] == st.session_state.u['NOMBRE']) & 
            (df_asis['FECHA'] == str_fecha)
        ]
    except Exception as e:
        st.error(f"Error de conexión con la hoja ASISTENCIA: {e}")
        return

    # --- 3. LÓGICA DE BOTONES (Entrada vs Salida) ---
    
    if mi_registro.empty:
        # CASO A: NO HA LLEGADO -> MOSTRAR BOTÓN DE ENTRADA
        st.warning("⚠️ Aún no registras entrada hoy.")
        obs = st.text_input("Novedades al llegar (Opcional):", placeholder="Todo en orden...")
        
        if st.button("☀️ MARCAR ENTRADA", type="primary", use_container_width=True):
            with st.spinner("Registrando huella digital..."):
                nuevo = pd.DataFrame([{
                    "FECHA": str_fecha,
                    "USUARIO": st.session_state.u['NOMBRE'],
                    "HORA_ENTRADA": str_hora,
                    "HORA_SALIDA": "",
                    "OBSERVACION": obs,
                    "ESTADO": "ACTIVO"
                }])
                
                # Guardamos en la nube
                df_final = pd.concat([df_asis, nuevo], ignore_index=True)
                conn.update(spreadsheet=url, worksheet="ASISTENCIA", data=df_final)
                
                st.balloons()
                st.success(f"✅ Entrada registrada a las: {str_hora}")
                time.sleep(1.5)
                st.session_state.pagina_actual = "HOME"
                st.rerun()
            
    else:
        # YA HAY REGISTRO, VERIFICAMOS SI FALTA SALIDA
        fila = mi_registro.iloc[0]
        
        if not fila['HORA_SALIDA'] or fila['HORA_SALIDA'] == "":
            # CASO B: ESTÁ EN LA ESCUELA -> MOSTRAR BOTÓN SALIDA
            st.success(f"✅ Entrada marcada a las: {fila['HORA_ENTRADA']}")
            st.info("La jornada está en curso. Que tengas buen día.")
            
            obs_sal = st.text_input("Novedades de salida:", placeholder="Jornada cumplida sin novedad...")
            
            if st.button("🌙 MARCAR SALIDA", type="primary", use_container_width=True):
                with st.spinner("Cerrando jornada..."):
                    # Actualizamos la fila existente (buscamos su índice original)
                    idx = mi_registro.index[0]
                    
                    df_asis.at[idx, 'HORA_SALIDA'] = str_hora
                    df_asis.at[idx, 'OBSERVACION'] = f"{fila['OBSERVACION']} | Salida: {obs_sal}"
                    df_asis.at[idx, 'ESTADO'] = "CERRADO"
                    
                    conn.update(spreadsheet=url, worksheet="ASISTENCIA", data=df_asis)
                    
                    st.success(f"✅ Salida registrada a las: {str_hora}")
                    time.sleep(1.5)
                    st.session_state.pagina_actual = "HOME"
                    st.rerun()
        else:
            # CASO C: YA SE FUE -> RESUMEN
            st.info("✅ JORNADA COMPLETADA.")
            st.write(f"**Entrada:** {fila['HORA_ENTRADA']}")
            st.write(f"**Salida:** {fila['HORA_SALIDA']}")
            
            if st.button("🏠 Volver al Menú"):
                st.session_state.pagina_actual = "HOME"
                st.rerun()
