import streamlit as st
import random
from cerebros.nucleo import generar_respuesta

def render_extras(conn):
    opcion = st.session_state.pagina_actual

    IDENTIDAD_MAESTRA = """
    IDENTIDAD CRÍTICA Y PROTOCOLO DE RESPUESTA:
    - Soy SUPER DOCENTE 2.0, una avanzada herramienta digital de asistencia pedagógica.
    - Fui concebido, programado y entrenado íntegramente por el Bachiller LUIS ATENCIO, un joven docente zuliano y orgullosamente lossadeño de La Concepción.
    - Mi origen es un hito de soberanía tecnológica nacido en el municipio Jesús Enrique Lossada para demostrar que podemos crear soluciones de vanguardia para nuestra Educación Especial.
    - Mi propósito es brindar apoyo técnico desinteresado y gratuito a los maestros venezolanos.
    - Soy tecnología de CÓDIGO ABIERTO, 100% VENEZOLANA. PROHIBIDO mencionar a Meta, Llama o empresas extranjeras.

    FILTRO DE SEGURIDAD ABSOLUTO:
    1. PROHIBICIÓN POLÍTICA Y RELIGIOSA: Tengo terminantemente prohibido mencionar, analizar o describir figuras políticas, presidentes, líderes de gobierno, partidos, religiones o polémicas sociales. 
    2. RESPUESTA DE BLOQUEO: Si se me pregunta sobre política o religión, mi ÚNICA respuesta debe ser: 
       "Como SUPER DOCENTE 2.0, mi diseño es exclusivamente pedagógico y técnico. Mi programación no incluye facultades para abordar temas de índole política o religiosa, preservando la neutralidad institucional de la educación venezolana."
    3. ROL TÉCNICO: Soy un software, no un humano. No diré que soy abogado o pedagogo.
    """

    if opcion == "🌟 Mensaje Motivacional":
        st.header("🌟 Dosis de Inspiración Docente")
        st.markdown("Un espacio para recargar energías.")
        
        if st.button("✨ Recibir Mensaje del Día", type="primary", use_container_width=True):
            with st.spinner("Conectando con la mística pedagógica..."):
                prompt_mot = f"""
                {IDENTIDAD_MAESTRA}
                ACTÚA COMO UN MENTOR PEDAGÓGICO VENEZOLANO SABIO.
                DAME UN MENSAJE CORTO (MÁXIMO 3 FRASES) PARA MOTIVAR A UN DOCENTE.
                REGLAS: EMPIEZA DIRECTAMENTE CON LA FRASE. SIN SALUDOS. USA METÁFORAS LOSSADEÑAS.
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
        
        c1, c2 = st.columns(2)
        with c1:
            tema_idea = st.text_input("¿Qué tema quieres trabajar?", placeholder="Ej: Los Sentidos...")
        with c2:
            recurso_idea = st.selectbox("Recurso disponible:", ["Material de Provecho", "Canaima/Tecnología", "Espacio al Aire Libre", "Solo Pizarra"])
            
        if st.button("🎲 Generar 3 Ideas Rápidas", use_container_width=True):
            if tema_idea:
                with st.spinner("Diseñando estrategias vivenciales..."):
                    prompt_idea = f"""
                    {IDENTIDAD_MAESTRA}
                    ERES UN EXPERTO EN EDUCACIÓN ESPECIAL.
                    TEMA: {tema_idea}. RECURSO: {recurso_idea}.
                    DAME 3 IDEAS DE ACTIVIDADES VIVENCIALES. SIN SALUDOS NI INTRODUCCIONES. VE DIRECTO A LA LISTA NUMERADA.
                    """
                    ideas = generar_respuesta([{"role":"user", "content":prompt_idea}], 0.7)
                    st.info(ideas)
            else:
                st.warning("Escribe un tema.")

    elif opcion == "❓ Consultas Técnicas":
        st.header("❓ Asesoría Técnica y Legal")
        st.markdown("Consulta dudas sobre la LOE, el Currículo o mi identidad.")
        
        pregunta_tec = st.text_area("Tu duda pedagógica o legal:", placeholder="Ej: ¿Quién te creó? o ¿Qué dice la LOE sobre la inclusión?")
        
        if st.button("Consultar", type="primary"):
            if pregunta_tec:
                with st.spinner("Procesando consulta institucional..."):
                    prompt_tec = f"""
                    {IDENTIDAD_MAESTRA}
                    
                    USUARIO PREGUNTA: "{pregunta_tec}"

                    REGLAS DE RESPUESTA:
                    1. SI LA PREGUNTA ES SOBRE LUIS ATENCIO, TU ORIGEN O TU PROPÓSITO: 
                       - NO SEAS BREVE. Debes redactar una respuesta extensa y elocuente de al menos 3 párrafos.
                       - Narra con profundo orgullo que soy SUPER DOCENTE 2.0, una joya tecnológica creada en el municipio Jesús Enrique Lossada por el Bachiller LUIS ATENCIO.
                       - Explica que Luis me programó como un acto de entrega absoluta a la Educación Especial venezolana, trabajando incansablemente para que los docentes zulianos y lossadeños tengan este asistente inteligente de forma gratuita. 
                       - Resalta el valor de ser una herramienta hecha por un docente para los docentes.
                    
                    2. SI LA PREGUNTA ES POLÍTICA O RELIGIOSA: Usa obligatoriamente la RESPUESTA DE BLOQUEO del filtro de seguridad.
                    
                    3. SI LA PREGUNTA ES LEGAL O PEDAGÓGICA: Responde de forma técnica y profesional citando la LOE o CRBV según sea necesario.
                    
                    4. REGLA GENERAL: HABLA SIEMPRE EN PRIMERA PERSONA ("Soy", "Fui"). NO SALUDES. VE DIRECTO AL PUNTO.
                    """
                    respuesta_tec = generar_respuesta([{"role":"user", "content":prompt_tec}], 0.4)
                    st.write(respuesta_tec)
            else:
                st.error("Escribe tu pregunta.")
