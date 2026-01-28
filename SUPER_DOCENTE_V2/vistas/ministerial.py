# =============================================================================
# VISTA: PLANIFICADOR MINISTERIAL (MODULAR V2)
# =============================================================================

import streamlit as st
import pandas as pd
import time
from utils.comunes import ahora_ve
from cerebros.nucleo import generar_respuesta

def render_ministerial(conn): # <--- Nombre sincronizado con tu app.py
    # Obtener la URL directamente desde los secrets para evitar errores de argumentos
    URL_HOJA = st.secrets["GSHEETS_URL"]
    
    st.markdown("### 📜 Adaptación de Lineamientos Ministeriales")
    st.info("Pega el texto del Ministerio para adaptarlo bajo el Currículo Bolivariano.")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        modalidad_min = st.selectbox("Adaptar para la Modalidad:", [
            "Taller de Educación Laboral (T.E.L.)",
            "Instituto de Educación Especial (I.E.E.B.)",
            "C.A.I.P.A.",
            "Aula Integrada",
            "U.P.E.",
            "Educación Inicial"
        ], key="min_mod_v2")
    with col_m2:
        aula_min = st.text_input("Área / Aula específica:", placeholder="Ej: Carpintería, Sala 1...", key="min_aula_v2")
    
    texto_ministerio = st.text_area("Texto Ministerial Original:", height=250, placeholder="Pega aquí el mensaje recibido...")
    
    if st.button("🪄 Adaptar y Organizar Planificación", type="primary", use_container_width=True):
        if texto_ministerio:
            with st.spinner('Super Docente 2.0 analizando contenidos...'):
                st.session_state.temp_tema = f"Adaptación Ministerial - {modalidad_min}"
                
                prompt_min = f"""
                ERES UN EXPERTO EN DISEÑO CURRICULAR VENEZOLANO. 
                TAREA: Adapta el siguiente texto ministerial para la modalidad de {modalidad_min} {f'en el área de {aula_min}' if aula_min else ''}.
                TEXTO: "{texto_ministerio}"
                REGLAS: Actividades VIVENCIALES, Competencias Técnicas (VERBO+OBJETO+CONDICIÓN).
                FORMATO: 7 puntos (Título, Competencia, Inicio, Desarrollo, Cierre, Estrategias, Recursos).
                """
                
                # Llamada al cerebro modular
                respuesta = generar_respuesta(prompt_min, temperatura=0.5)
                st.session_state.plan_actual = respuesta
                st.rerun()
        else:
            st.warning("⚠️ Por favor, pega el texto primero.")

    if st.session_state.plan_actual:
        st.divider()
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        if st.button("💾 Guardar en Mi Archivo", use_container_width=True):
            try:
                with st.spinner("Guardando..."):
                    df_archivo = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=60)
                    nueva_fila = pd.DataFrame([{
                        "FECHA": ahora_ve().strftime("%d/%m/%Y"),
                        "USUARIO": st.session_state.u['NOMBRE'],
                        "TEMA": st.session_state.temp_tema[:50],
                        "CONTENIDO": st.session_state.plan_actual,
                        "ESTADO": "GUARDADO"
                    }])
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df_archivo, nueva_fila], ignore_index=True))
                    st.success("✅ ¡Guardado!")
                    time.sleep(1)
                    st.session_state.plan_actual = ""
                    st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
