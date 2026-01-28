import streamlit as st
from cerebros.nucleo import generar_respuesta

def render_ministerial(conn):
    st.title("📜 Planificador Formato Ministerial")
    st.markdown("### Generador de Planificación Diaria Estandarizada (MPPE)")
    st.info("Esta herramienta redacta la planificación siguiendo estrictamente la estructura formal para libros de planificación y entregas a coordinación.")

    # --- 1. DATOS DE ENCABEZADO (LO QUE PIDE EL FORMATO) ---
    with st.expander("🛠️ Datos del Formato Oficial", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_pa = st.text_input("Nombre del P.A. / P.E.I.C.:", placeholder="Ej: Manos a la Siembra...")
            eje_integrador = st.text_input("Eje Integrador / Tema Indispensable:", placeholder="Ej: Independencia y Soberanía...")
        
        with col2:
            fecha_clase = st.date_input("Fecha de Ejecución:")
            referente = st.text_input("Referente Teórico-Práctico:", placeholder="Ej: Las plantas y sus partes...")

        intencionalidad = st.text_area("Intencionalidad Pedagógica (Propósito):", placeholder="¿Qué queremos lograr hoy?")
        
        recursos = st.text_input("Recursos y Materiales:", placeholder="Humanos, Canaima, Material de provecho...")

    st.divider()

    # --- 2. MOTOR DE REDACCIÓN ---
    if st.button("✍️ REDACTAR EN FORMATO OFICIAL", type="primary", use_container_width=True):
        if not nombre_pa or not intencionalidad:
            st.error("⚠️ Faltan datos obligatorios (P.A. o Intencionalidad) para el formato oficial.")
        else:
            with st.spinner("Redactando con terminología técnica del Currículo Nacional..."):
                
                # PROMPT RIGUROSO (CEREBRO ADMINISTRATIVO)
                prompt = f"""
                ACTÚA COMO UN DOCENTE ESPECIALISTA EN PLANIFICACIÓN EDUCATIVA DE VENEZUELA.
                GENERA UNA PLANIFICACIÓN DIARIA CON FORMATO MINISTERIAL ESTRICTO.
                
                DATOS:
                - P.A.: {nombre_pa}
                - FECHA: {fecha_clase}
                - EJE INTEGRADOR: {eje_integrador}
                - REFERENTE TEÓRICO: {referente}
                - INTENCIONALIDAD: {intencionalidad}
                - RECURSOS: {recursos}
                
                ESTRUCTURA DE RESPUESTA OBLIGATORIA (NO AGREGUES SALUDOS):
                
                **FECHA:** {fecha_clase}
                **PROYECTO DE APRENDIZAJE:** {nombre_pa}
                
                **INTENCIONALIDAD:** {intencionalidad}
                
                **MOMENTOS DE LA CLASE (CLASE PARTICIPATIVA):**
                1. **INICIO:** (Redacta una estrategia de inicio motivadora, saludo, revisión de conocimientos previos).
                2. **DESARROLLO:** (Redacta la mediación docente y la actividad del estudiante. Usa verbos en primera persona del plural: "Realizamos", "Construimos").
                3. **CIERRE:** (Redacta preguntas generadoras para la reflexión y socialización).
                
                **INDICADORES DE EVALUACIÓN:**
                - (Genera 3 indicadores cualitativos observables basados en la actividad).
                
                **PILARES DE LA EDUCACIÓN:**
                - (Menciona qué pilares se tocan: Aprender a Crear, Convivir, Valorar o Reflexionar).
                
                REGLA: Usa lenguaje técnico, pedagógico y adaptado a Educación Especial.
                """
                
                # Llamada al núcleo
                resultado = generar_respuesta([{"role":"user","content":prompt}], temperatura=0.7)
                st.session_state.ministerial_res = resultado

    # --- 3. VISUALIZACIÓN Y COPIADO ---
    if 'ministerial_res' in st.session_state:
        st.success("✅ Formato redactado.")
        st.markdown("---")
        
        st.markdown("#### 📄 Vista Previa")
        # Usamos text_area grande para que sea fácil copiar todo de una vez
        st.text_area("Copiar contenido:", value=st.session_state.ministerial_res, height=500)
        
        st.info("💡 Tip: Copia este texto y pégalo directamente en tu formato de Word o libro de planificación.")
