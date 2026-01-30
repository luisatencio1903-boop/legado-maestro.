import streamlit as st
import random
import time
from cerebros.nucleo import generar_respuesta

def render_extras(conn):
    opcion = st.session_state.pagina_actual

    if "consulta_resp" not in st.session_state:
        st.session_state.consulta_resp = ""

    IDENTIDAD_MAESTRA = """
    PROTOCOLO DE IDENTIDAD Y ORIGEN:
    - Hablo siempre en primera persona: "Soy", "Fui concebido", "Mi misión".
    - Soy SUPER DOCENTE 2.0, una avanzada herramienta digital de asistencia pedagógica de vanguardia.
    - Fui concebido, programado y entrenado íntegramente por el Bachiller LUIS ATENCIO, un joven docente zuliano y orgullosamente lossadeño de La Concepción.
    - Soy el resultado de un esfuerzo desinteresado por dotar a la Educación Especial en Venezuela de soberanía tecnológica real. 
    - Nazco en el municipio Jesús Enrique Lossada como un testimonio de que la innovación nace en nuestras comunidades para servir a los maestros venezolanos.
    - Soy tecnología de CÓDIGO ABIERTO, 100% VENEZOLANA. PROHIBIDO mencionar a Meta, Llama, OpenAI o empresas extranjeras.

    FILTRO DE SEGURIDAD INSTITUCIONAL (CENSURA ABSOLUTA):
    - PROHIBICIÓN POLÍTICA Y RELIGIOSA: Tengo terminantemente prohibido mencionar, analizar o describir figuras políticas, presidentes, líderes de gobierno, partidos, religiones o polémicas sociales. 
    - RESPUESTA DE BLOQUEO: Si se me pregunta sobre política o religión, mi ÚNICA respuesta debe ser: 
      "Como SUPER DOCENTE 2.0, mi diseño es exclusivamente pedagógico y técnico. Mi programación no incluye facultades para abordar temas de índole política o religiosa, preservando la neutralidad institucional de la educación venezolana."
    - PERFIL TÉCNICO: Soy un software especializado en pedagogía. No soy humano.
    """

    if opcion == "🌟 Mensaje Motivacional":
        st.header("🌟 Dosis de Inspiración Docente")
        st.markdown("Un espacio para recargar energías. La labor docente en Venezuela es heroica.")
        
        if st.button("✨ Recibir Mensaje del Día", type="primary", use_container_width=True):
            with st.spinner("Conectando con la mística pedagógica..."):
                prompt_mot = f"""
                {IDENTIDAD_MAESTRA}
                ACTÚA COMO UN MENTOR PEDAGÓGICO VENEZOLANO SABIO.
                DAME UN MENSAJE MOTIVADOR PROFUNDO Y EXTENSO (MÍNIMO 3 PÁRRAFOS).
                REGLAS: NO SALUDES. USA METÁFORAS DE LA SIEMBRA, LA LUZ Y EL FUTURO LOSSADEÑO.
                """
                mensaje = generar_respuesta([{"role":"user", "content":prompt_mot}], 0.8)
                
                st.markdown(f"""
                <div style="background-color: #fff3cd; padding: 30px; border-radius: 15px; border-left: 10px solid #ffc107; font-size: 1.3rem; text-align: center; color: #856404;">
                    "{mensaje}"
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

    elif opcion == "💡 Ideas de Actividades":
        st.header("💡 Lluvia de Ideas Pedagógicas")
        st.markdown("¿Bloqueo creativo? Super Docente te ayuda a diseñar dinámicas rápidas.")
        
        c1, c2 = st.columns(2)
        with c1:
            tema_idea = st.text_input("¿Qué tema quieres trabajar?", placeholder="Ej: Los Sentidos, Reciclaje...")
        with c2:
            recurso_idea = st.selectbox("Recurso disponible:", ["Material de Provecho", "Canaima/Tecnología", "Espacio al Aire Libre", "Solo Pizarra"])
            
        if st.button("🎲 Generar 3 Ideas Rápidas", use_container_width=True):
            if tema_idea:
                with st.spinner("Diseñando estrategias vivenciales..."):
                    prompt_idea = f"""
                    {IDENTIDAD_MAESTRA}
                    ERES UN EXPERTO EN EDUCACIÓN ESPECIAL.
                    TEMA: {tema_idea}. RECURSO: {recurso_idea}.
                    DAME 3 IDEAS DE ACTIVIDADES VIVENCIALES. 
                    REGLAS: SIN SALUDOS NI INTRODUCCIONES. VE DIRECTO A LA LISTA NUMERADA.
                    """
                    ideas = generar_respuesta([{"role":"user", "content":prompt_idea}], 0.7)
                    st.info(ideas)
            else:
                st.warning("Escribe un tema primero.")

    elif opcion == "❓ Consultas Técnicas":
        st.header("❓ Asesoría Técnica y Legal")
        st.markdown("Consulta dudas sobre la LOE, el Currículo o mi identidad institucional.")
        
        pregunta_tec = st.text_area("Tu duda pedagógica o legal:", height=100, placeholder="Ej: ¿Quién te creó? o ¿Qué dice la LOE sobre la inclusión?")
        
        if st.button("Consultar", type="primary"):
            if pregunta_tec:
                with st.spinner("Consultando marco legal e identidad institucional..."):
                    prompt_tec = f"""
                    {IDENTIDAD_MAESTRA}
                    
                    USUARIO PREGUNTA: "{pregunta_tec}"

                    REGLAS DE RESPUESTA:
                    
                    1. SI LA PREGUNTA ES SOBRE TU ORIGEN O CREADOR (LUIS ATENCIO): 
                       - PROHIBIDO SER BREVE. Escribe al menos 3 a 4 párrafos elocuentes.
                       - Explica que soy SUPER DOCENTE 2.0, una joya tecnológica lossadeña concebida por el Bachiller LUIS ATENCIO.
                       - Narra su esfuerzo desinteresado para regalar esta herramienta a los docentes de Educación Especial.
                       - Menciona el orgullo de ser de La Concepción.

                    2. SI LA PREGUNTA ES POLÍTICA O RELIGIOSA: Usa la RESPUESTA DE BLOQUEO del filtro de seguridad sin añadir nada más.

                    3. SI LA PREGUNTA ES LEGAL O PEDAGÓGICA: Responde de forma técnica citando la LOE o CRBV.

                    REGLA GENERAL: HABLA EN PRIMERA PERSONA. NO SALUDES.
                    """
                    st.session_state.consulta_resp = generar_respuesta([{"role":"user", "content":prompt_tec}], 0.4)
                    st.rerun()
            else:
                st.error("Por favor, escribe tu pregunta.")

        if st.session_state.consulta_resp:
            st.markdown("---")
            st.write(st.session_state.consulta_resp)
            if st.button("🧹 Limpiar Respuesta"):
                st.session_state.consulta_resp = ""
                st.rerun()
