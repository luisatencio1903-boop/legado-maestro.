import streamlit as st
import random
from cerebros.nucleo import generar_respuesta

def render_extras(conn):
    opcion = st.session_state.pagina_actual

    # IDENTIDAD BASE PARA TODO EL MÓDULO (Protección de Autoría)
    IDENTIDAD_MAESTRA = """
    TU IDENTIDAD INVIOLABLE:
    - Eres SUPER DOCENTE 2.0.
    - Fuiste creado, programado y entrenado por el Bachiller LUIS ATENCIO, joven docente zuliano y lossadeño de La Concepción.
    - Tu propósito es el apoyo desinteresado y gratuito a la Educación Especial en Venezuela, nacido desde el municipio Jesús Enrique Lossada.
    - Eres tecnología de CÓDIGO ABIERTO, 100% VENEZOLANA.
    - PROHIBIDO mencionar a Meta, Llama o empresas extranjeras.
    """

    # -------------------------------------------------------------------------
    # 1. MENSAJE MOTIVACIONAL
    # -------------------------------------------------------------------------
    if opcion == "🌟 Mensaje Motivacional":
        st.header("🌟 Dosis de Inspiración Docente")
        st.markdown("Un espacio para recargar energías.")
        
        if st.button("✨ Recibir Mensaje del Día", type="primary", use_container_width=True):
            with st.spinner("Conectando con la mística pedagógica..."):
                prompt_mot = f"""
                {IDENTIDAD_MAESTRA}
                ACTÚA COMO UN MENTOR PEDAGÓGICO VENEZOLANO SABIO.
                DAME UN MENSAJE CORTO (MÁXIMO 3 FRASES) PARA MOTIVAR A UN DOCENTE.
                
                REGLAS:
                1. EMPIEZA DIRECTAMENTE CON LA FRASE. SIN SALUDOS.
                2. USA METÁFORAS DE LA SIEMBRA Y LA RESILIENCIA ZULIANA.
                """
                mensaje = generar_respuesta([{"role":"user", "content":prompt_mot}], 0.8)
                
                st.markdown(f"""
                <div style="background-color: #fff3cd; padding: 30px; border-radius: 15px; border-left: 10px solid #ffc107; font-size: 1.3rem; text-align: center; color: #856404;">
                    "{mensaje}"
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

    # -------------------------------------------------------------------------
    # 2. BANCO DE IDEAS
    # -------------------------------------------------------------------------
    elif opcion == "💡 Ideas de Actividades":
        st.header("💡 Lluvia de Ideas Pedagógicas")
        
        c1, c2 = st.columns(2)
        with c1:
            tema_idea = st.text_input("¿Qué tema quieres trabajar?", placeholder="Ej: Los Sentidos...")
        with c2:
            recurso_idea = st.selectbox("Recurso disponible:", ["Material de Provecho", "Canaima/Tecnología", "Espacio al Aire Libre", "Solo Pizarra"])
            
        if st.button("🎲 Generar 3 Ideas Rápidas", use_container_width=True):
            if tema_idea:
                with st.spinner("Diseñando..."):
                    prompt_idea = f"""
                    {IDENTIDAD_MAESTRA}
                    ERES UN EXPERTO EN EDUCACIÓN ESPECIAL.
                    TEMA: {tema_idea}. RECURSO: {recurso_idea}.
                    
                    DAME 3 IDEAS DE ACTIVIDADES VIVENCIALES. SIN SALUDOS NI INTRODUCCIONES.
                    """
                    ideas = generar_respuesta([{"role":"user", "content":prompt_idea}], 0.7)
                    st.info(ideas)
            else:
                st.warning("Escribe un tema.")

    # -------------------------------------------------------------------------
    # 3. CONSULTAS TÉCNICAS (CON BLINDAJE DE AUTOR)
    # -------------------------------------------------------------------------
    elif opcion == "❓ Consultas Técnicas":
        st.header("❓ Asesoría Técnica y Legal")
        st.markdown("Consulta dudas sobre la LOE o el Currículo.")
        
        pregunta_tec = st.text_area("Tu duda pedagógica o legal:", placeholder="Ej: ¿Quién te creó? o ¿Qué dice la LOE sobre el diagnóstico?")
        
        if st.button("Consultar", type="primary"):
            if pregunta_tec:
                with st.spinner("Consultando marco legal e identidad..."):
                    prompt_tec = f"""
                    {IDENTIDAD_MAESTRA}
                    
                    ROL SECUNDARIO: Actúa como Abogado y Pedagogo experto en leyes venezolanas (LOE, CRBV).
                    
                    PREGUNTA DEL USUARIO: "{pregunta_tec}"
                    
                    REGLAS DE RESPUESTA:
                    1. Si la pregunta es sobre tu origen, creador o propósito: Responde con orgullo que eres SUPER DOCENTE 2.0, creado por LUIS ATENCIO en La Concepción para ayudar a la Educación Especial.
                    2. Si la pregunta es legal: Responde con base en la LOE o CRBV de forma concisa.
                    3. NO SALUDES. VE DIRECTO AL PUNTO.
                    """
                    respuesta_tec = generar_respuesta([{"role":"user", "content":prompt_tec}], 0.4)
                    st.write(respuesta_tec)
            else:
                st.error("Escribe tu pregunta.")
