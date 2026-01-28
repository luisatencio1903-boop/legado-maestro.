# =============================================================================
# VISTA: PLANIFICADOR MINISTERIAL (MIGRADO DE V1 A MODULAR V2)
# Función: Adapta lineamientos del MPPE a la modalidad de Educación Especial.
# =============================================================================

import streamlit as st
import pandas as pd
import time
from utils.comunes import ahora_ve
from cerebros.nucleo import generar_respuesta

def mostrar_vista(conn, URL_HOJA):
    st.markdown("### 📜 Adaptación de Lineamientos Ministeriales")
    st.info("Pega el texto del Ministerio (WhatsApp/PDF) para adaptarlo y organizarlo bajo el Currículo Bolivariano.")
    
    # 1. RECOLECCIÓN DE DATOS (Interfaz V1)
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
    
    # 2. LÓGICA DE PROCESAMIENTO (ADN V1)
    if st.button("🪄 Adaptar y Organizar Planificación", type="primary", use_container_width=True):
        if texto_ministerio:
            with st.spinner('Super Docente 2.0 analizando y adaptando contenidos...'):
                # Guardamos el título temporal para el archivo
                st.session_state.temp_tema = f"Adaptación Ministerial - {modalidad_min}"
                
                # Reconstrucción del Prompt Maestro del V1
                prompt_min = f"""
                ERES UN EXPERTO EN DISEÑO CURRICULAR VENEZOLANO. 
                TAREA: Adapta el siguiente texto ministerial para la modalidad de {modalidad_min} {f'en el área de {aula_min}' if aula_min else ''}.
                
                TEXTO ORIGINAL DEL MINISTERIO:
                "{texto_ministerio}"
                
                REGLAS DE ORO DE ADAPTACIÓN (ESTRICTAS):
                1. Traduce cualquier actividad abstracta (investigar, leer, escribir en cuaderno) a actividades VIVENCIALES (limpiar, armar, cocinar, modelar, tocar).
                2. Los objetivos deben convertirse en COMPETENCIAS TÉCNICAS (VERBO INFINTIVO + OBJETO + CONDICIÓN).
                3. Usa un lenguaje motivador y profesional.
                4. Ignora que hoy es sábado/domingo; la planificación debe cubrir de Lunes a Viernes.

                ESTRUCTURA DE SALIDA (7 PUNTOS OBLIGATORIOS POR DÍA):
                ### [DÍA Y FECHA]
                
                **1. TÍTULO LÚDICO:** (Nombre creativo)
                
                **2. COMPETENCIA TÉCNICA:** (Estructura Acción+Objeto+Condición)
                
                **3. EXPLORACIÓN (Inicio):** (Vivencia inicial)
                
                **4. DESARROLLO (Proceso):** (Actividad práctica central)
                
                **5. REFLEXIÓN (Cierre):** (Intercambio de saberes)
                
                **6. ESTRATEGIAS:** (Solo mención de nombres técnicas)
                
                **7. RECURSOS:** (Material concreto y de provecho)
                
                ---------------------------------------------------
                """
                
                # Llamada al cerebro modular
                respuesta = generar_respuesta(prompt_min, temperatura=0.5)
                st.session_state.plan_actual = respuesta
                st.rerun()
        else:
            st.warning("⚠️ Por favor, pega el texto ministerial primero.")

    # 3. VISUALIZACIÓN Y GUARDADO (ADN V1)
    if st.session_state.plan_actual:
        st.divider()
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        if st.button("💾 Guardar Adaptación en Mi Archivo", use_container_width=True):
            try:
                with st.spinner("Guardando en la nube..."):
                    # Leer la base de datos (Usamos ttl=60 para evitar error 429)
                    df_archivo = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=60)
                    
                    nueva_fila = pd.DataFrame([{
                        "FECHA": ahora_ve().strftime("%d/%m/%Y"),
                        "USUARIO": st.session_state.u['NOMBRE'],
                        "TEMA": st.session_state.temp_tema[:50],
                        "CONTENIDO": st.session_state.plan_actual,
                        "ESTADO": "GUARDADO"
                    }])
                    
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df_archivo, nueva_fila], ignore_index=True))
                    st.success("✅ ¡Guardado correctamente en tu archivo pedagógico!")
                    time.sleep(2)
                    st.session_state.plan_actual = ""
                    st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
