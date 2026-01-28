import streamlit as st
from cerebros.nucleo import generar_respuesta

def render_extras(conn):
    opcion = st.session_state.pagina_actual

    # -------------------------------------------------------------------------
    # 1. MENSAJE MOTIVACIONAL (DIRECTO AL GRANO)
    # -------------------------------------------------------------------------
    if opcion == "🌟 Mensaje Motivacional":
        st.header("🌟 Dosis de Inspiración Docente")
        st.markdown("Un espacio para recargar energías.")
        
        if st.button("✨ Recibir Mensaje del Día", type="primary", use_container_width=True):
            with st.spinner("Conectando con la mística pedagógica..."):
                prompt_mot = """
                ACTÚA COMO UN MENTOR PEDAGÓGICO VENEZOLANO SABIO.
                DAME UN MENSAJE CORTO (MÁXIMO 3 FRASES) PARA MOTIVAR A UN DOCENTE.
                
                REGLAS DE ORO:
                1. PROHIBIDO SALUDAR. NO EMPIECES CON "QUERIDO DOCENTE", "HOLA COLEGA", NI NADA PARECIDO.
                2. EMPIEZA DIRECTAMENTE CON LA FRASE.
                3. USA METÁFORAS DE LA SIEMBRA, LA LUZ Y EL FUTURO.
                4. TIENE QUE TENER "ALMA" VENEZOLANA PERO SER SERIO Y PROFUNDO.
                """
                mensaje = generar_respuesta([{"role":"user", "content":prompt_mot}], 0.8)
                
                st.markdown(f"""
                <div style="background-color: #fff3cd; padding: 30px; border-radius: 15px; border-left: 10px solid #ffc107; font-size: 1.3rem; text-align: center; color: #856404;">
                    "{mensaje}"
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

    # -------------------------------------------------------------------------
    # 2. BANCO DE IDEAS (SIN RODEOS)
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
                    ERES UN EXPERTO EN EDUCACIÓN ESPECIAL.
                    TEMA: {tema_idea}. RECURSO: {recurso_idea}.
                    
                    DAME 3 IDEAS DE ACTIVIDADES.
                    
                    REGLAS:
                    1. NO SALUDES NI DES INTRODUCCIONES TIPO "AQUÍ TIENES IDEAS".
                    2. SOLO DAME LA LISTA NUMERADA.
                    
                    FORMATO:
                    1. [Nombre]: [Instrucción directa].
                    2. [Nombre]: [Instrucción directa].
                    3. [Nombre]: [Instrucción directa].
                    """
                    ideas = generar_respuesta([{"role":"user", "content":prompt_idea}], 0.7)
                    st.info(ideas)
            else:
                st.warning("Escribe un tema.")

    # -------------------------------------------------------------------------
    # 3. CONSULTAS TÉCNICAS (SOLO RESPUESTA)
    # -------------------------------------------------------------------------
    elif opcion == "❓ Consultas Técnicas":
        st.header("❓ Asesoría Técnica y Legal")
        st.markdown("Consulta dudas sobre la LOE o el Currículo.")
        
        pregunta_tec = st.text_area("Tu duda pedagógica o legal:", height=100)
        
        if st.button("Consultar", type="primary"):
            if pregunta_tec:
                with st.spinner("Consultando marco legal..."):
                    prompt_tec = f"""
                    ACTÚA COMO ABOGADO Y PEDAGOGO EXPERTO EN LEYES VENEZOLANAS (LOE, CRBV).
                    PREGUNTA: "{pregunta_tec}"
                    
                    REGLA: NO SALUDES. RESPONDE DIRECTAMENTE A LA PREGUNTA CON BASE LEGAL.
                    SE PRECISO Y CONCISO.
                    """
                    respuesta_tec = generar_respuesta([{"role":"user", "content":prompt_tec}], 0.5)
                    st.write(respuesta_tec)
            else:
                st.error("Escribe tu pregunta.")
