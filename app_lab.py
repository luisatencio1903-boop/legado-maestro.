# --- DENTRO DE LA VISTA DOCENTE -> Pestaña p2 (Ejecución Hoy) ---
with p2:
    st.subheader(f"🚀 Control de Ejecución: {datetime.now().strftime('%d/%m/%Y')}")
    
    # 1. Buscamos si hay un plan aprobado para este docente
    aprobado = df_base[(df_base['USUARIO'] == u['NOMBRE']) & (df_base['ESTADO'] == 'APROBADO')]
    
    if aprobado.empty:
        st.warning("⚠️ No hay planes aprobados para hoy. El Director debe autorizar tu planificación.")
    else:
        # Recuperamos la información del plan
        fila_plan = aprobado.iloc[-1]
        st.markdown(f"<div class='card'><b>Actividad Autorizada:</b> {fila_plan['TEMA']}</div>", unsafe_allow_html=True)
        
        # 2. LÓGICA DEL CRONÓMETRO
        if 'clase_activa' not in st.session_state:
            st.session_state.clase_activa = False

        if not st.session_state.clase_activa:
            # Configuración antes de iniciar
            duracion_meta = st.number_input("Duración prevista (minutos):", min_value=10, max_value=180, value=45)
            if st.button("▶️ INICIAR ACTIVIDAD Y CRONÓMETRO"):
                st.session_state.clase_activa = True
                st.session_state.hora_inicio_dt = datetime.now()
                st.session_state.hora_fin_meta = st.session_state.hora_inicio_dt + timedelta(minutes=duracion_meta)
                
                # Actualizar en Excel para que el Director vea "EN CURSO"
                idx = aprobado.index[-1]
                df_base.loc[idx, 'ESTADO'] = 'EN CURSO'
                df_base.loc[idx, 'HORA_INICIO'] = st.session_state.hora_inicio_dt.strftime("%H:%M")
                conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_base)
                st.rerun()
        else:
            # 3. MOSTRAR TIEMPO RESTANTE
            ahora = datetime.now()
            faltante = st.session_state.hora_fin_meta - ahora
            
            if faltante.total_seconds() > 0:
                mins, segs = divmod(int(faltante.total_seconds()), 60)
                st.markdown(f"### ⏳ Tiempo Restante: **{mins:02d}:{segs:02d}**")
                st.progress(min(1.0, 1 - (faltante.total_seconds() / (45 * 60)))) # Barra de progreso visual
            else:
                st.error("⏰ ¡TIEMPO CUMPLIDO! Por favor, cierre la actividad.")

            st.markdown("---")
            st.write("📸 **Carga de Evidencias (En curso)**")
            foto = st.file_uploader("Subir foto de la actividad", type=['jpg', 'png'])
            
            # 4. BOTÓN DE CULMINACIÓN (ESTRICTO)
            if st.button("⏹️ CULMINAR ACTIVIDAD"):
                st.session_state.clase_activa = False
                
                # Sellar en Excel
                idx = aprobado.index[-1]
                df_base.loc[idx, 'ESTADO'] = 'FINALIZADO'
                df_base.loc[idx, 'HORA_FIN'] = datetime.now().strftime("%H:%M")
                conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_base)
                
                st.balloons()
                st.success("Actividad finalizada y evidencias guardadas con éxito.")
                time.sleep(2)
                st.rerun()
