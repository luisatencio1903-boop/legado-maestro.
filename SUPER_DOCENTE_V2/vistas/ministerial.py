import streamlit as st
import pandas as pd
import time
import re
from utils.comunes import ahora_ve
from cerebros.nucleo import generar_respuesta

def render_ministerial(conn):
    # --- 1. INICIALIZACIÓN DE VARIABLES DE ESTADO (Blindaje V2.0) ---
    if 'plan_actual' not in st.session_state:
        st.session_state.plan_actual = ""
    if 'temp_tema' not in st.session_state:
        st.session_state.temp_tema = ""
    
    URL_HOJA = st.secrets["GSHEETS_URL"]

    # --- 2. INTERFAZ (Tu diseño original preservado) ---
    st.markdown("### 📜 PLANIFICADOR MINISTERIAL")
    st.markdown("*Adaptación de Lineamientos*")
    st.info("Pega el texto del Ministerio. SUPER DOCENTE 2.0 lo adaptará y formateará.")
    
    aula_min = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios", key="aula_min_v2")
    texto_ministerio = st.text_area("Texto (WhatsApp):", height=250, key="txt_min_v2")
    
    # --- 3. LÓGICA DE PROCESAMIENTO (Fiel al V1) ---
    if st.button("🪄 Adaptar y Organizar", type="primary", use_container_width=True):
        if texto_ministerio:
            with st.spinner('Adaptando y humanizando actividades...'):
                # Intentar detectar fecha con tu lógica de Regex original
                fechas_enc = re.findall(r'\d{1,2}[/-]\d{1,2}', texto_ministerio)
                rango_det = f"Semana {fechas_enc[0]}" if fechas_enc else "Semana Ministerial"
                
                st.session_state.temp_tema = f"Plan Ministerial Adaptado - {rango_det}"
                
                # Tu Prompt Original (El que ya sabes que funciona)
                prompt = f"""
                ERES EXPERTO EN CURRÍCULO. ADAPTA ESTO PARA EDUCACIÓN ESPECIAL / TALLER LABORAL:
                "{texto_ministerio}"
                AULA: {aula_min}.
                
                REGLAS:
                1. ENCABEZADO OBLIGATORIO: "📝 **Planificación del Ministerio (Adaptada)**".
                2. Si hay actividades abstractas, cámbialas a concretas y VIVENCIALES.
                3. Usa competencias técnicas completas (Acción+Objeto+Condición).
                4. FORMATO: Lista vertical con doble espacio entre puntos (1 al 7).
                """
                
                # Llamada al núcleo modular
                # Nota: Pasamos el prompt directamente como un string
                respuesta = generar_respuesta(prompt, temperatura=0.6)
                st.session_state.plan_actual = respuesta
                st.rerun()
        else:
            st.warning("⚠️ Pega el texto primero.")

    # --- 4. BLOQUE DE VISUALIZACIÓN Y GUARDADO (Tu lógica original V1) ---
    if st.session_state.plan_actual:
        st.markdown("---")
        # El cuadro con tu estilo CSS 'plan-box'
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        if st.button("💾 Guardar en Mi Archivo", use_container_width=True):
            try:
                with st.spinner("Guardando en la nube..."):
                    # Leemos la base de datos (ttl=60 para estabilidad)
                    df_archivo = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=60)
                    tema_guardar = st.session_state.get('temp_tema', 'Planificación Ministerial')
                    
                    # Estructura de fila original
                    nueva_fila = pd.DataFrame([{
                        "FECHA": ahora_ve().strftime("%d/%m/%Y"),
                        "USUARIO": st.session_state.u['NOMBRE'],
                        "TEMA": tema_guardar[:50], 
                        "CONTENIDO": st.session_state.plan_actual,
                        "ESTADO": "GUARDADO",
                        "HORA_INICIO": "--", 
                        "HORA_FIN": "--"
                    }])
                    
                    # Actualización en Google Sheets
                    df_final = pd.concat([df_archivo, nueva_fila], ignore_index=True)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_final)
                    
                    st.success("✅ Guardado correctamente en tu archivo pedagógico.")
                    time.sleep(2)
                    st.session_state.plan_actual = "" # Limpiamos memoria
                    st.session_state.pagina_actual = "📂 Mi Archivo Pedagógico" # Redirección
                    st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
