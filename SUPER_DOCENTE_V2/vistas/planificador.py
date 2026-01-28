import streamlit as st
import pandas as pd
import time
from utils.comunes import ahora_ve
from cerebros.nucleo import generar_respuesta, seleccionar_cerebro_modalidad

def render_planificador(conn):
    try:
        URL_HOJA = st.secrets["GSHEETS_URL"]
    except:
        st.error("Error de configuración.")
        return

    st.markdown("**Generación de Planificación Pedagógica Especializada**")
    
    # 1. INTERFAZ DE USUARIO
    col1, col2 = st.columns(2)
    with col1:
        rango = st.text_input("Lapso (Fechas):", placeholder="Ej: 26 al 30 de Enero")
    with col2:
        modalidad = st.selectbox("Modalidad / Servicio:", [
            "Taller de Educación Laboral (T.E.L.)",
            "Instituto de Educación Especial (I.E.E.B.)",
            "Centro de Atención Integral para Personas con Autismo (C.A.I.P.A.)",
            "Aula Integrada (Escuela Regular)",
            "Unidad Psico-Educativa (U.P.E.)",
            "Educación Inicial (Preescolar)"
        ])
    
    aula_especifica = ""
    if "Taller" in modalidad:
        aula_especifica = st.text_input("Especifique el Taller / Aula:", placeholder="Ej: Carpintería, Cocina...")
    
    is_pei = st.checkbox("🎯 ¿Planificación Individualizada (P.E.I.)?")
    perfil_alumno = ""
    if is_pei:
        perfil_alumno = st.text_area("Perfil del Alumno (Potencialidades y Necesidades):", placeholder="Describa al estudiante...")
    
    notas = st.text_area("Tema Generador / Referente Ético / Notas:", height=100)

    # 2. BOTÓN DE GENERACIÓN
    if st.button("🚀 Generar Planificación Estructurada", type="primary"):
        if not rango or not notas:
            st.error("⚠️ Por favor ingrese el Lapso y el Tema.")
        else:
            with st.spinner('Super Docente 1.0 alineando estrategias y léxico...'):
                
                # --- A. RECOLECCIÓN DE CONTEXTO (PENSUM Y PROYECTOS) ---
                
                # 1. Buscar Proyectos (P.A. / P.S.P.)
                texto_proyectos = "Usa el Tema Generador como eje central."
                try:
                    df_p = conn.read(spreadsheet=URL_HOJA, worksheet="CONFIG_PROYECTO", ttl=0)
                    user_p = df_p[df_p['USUARIO'] == st.session_state.u['NOMBRE']]
                    if not user_p.empty:
                        fila = user_p.iloc[0]
                        if fila['ESTADO'] == 'ACTIVO':
                            pa = fila.get('TITULO_PA', 'Valores')
                            psp = fila.get('TITULO_PSP', 'Productivo')
                            dias_pa = str(fila.get('DIAS_PA', ''))
                            dias_psp = str(fila.get('DIAS_PSP', ''))
                            texto_proyectos = f"""
                            CONTEXTO DE PROYECTOS ACTIVOS:
                            1. P.A. (Aula/Teoría): "{pa}" (Días sugeridos: {dias_pa}).
                            2. P.S.P. (Taller/Práctica): "{psp}" (Días sugeridos: {dias_psp}).
                            """
                except: pass

                # 2. Buscar Pensum Activo (Bloque Temático)
                texto_pensum = ""
                nombre_bloque = ""
                try:
                    df_bib = conn.read(spreadsheet=URL_HOJA, worksheet="BIBLIOTECA_PENSUMS", ttl=0)
                    pensum_act = df_bib[(df_bib['USUARIO'] == st.session_state.u['NOMBRE']) & (df_bib['ESTADO'] == "ACTIVO")]
                    if not pensum_act.empty:
                        fila_pen = pensum_act.iloc[0]
                        nombre_bloque = fila_pen.get('BLOQUE_ACTUAL', "Contenido General")
                        full_txt = fila_pen['CONTENIDO_FULL']
                        # Extraer solo el bloque actual
                        inicio = full_txt.find(nombre_bloque)
                        if inicio != -1:
                            fin = full_txt.find("BLOQUE:", inicio + 20)
                            texto_pensum = full_txt[inicio:fin] if fin != -1 else full_txt[inicio:]
                        else:
                            texto_pensum = full_txt[:2000] # Fallback
                        
                        texto_pensum = f"""
                        💎 **INSUMO TÉCNICO (PENSUM ACTIVO):**
                        BLOQUE: "{nombre_bloque}"
                        CONTENIDO: {texto_pensum}
                        (Usa este contenido técnico para las actividades).
                        """
                except: pass

                # --- B. LLAMADA AL CEREBRO MODULAR ---
                
                # Obtenemos el System Prompt del especialista (TEL, CAIPA, etc.)
                instrucciones_sistema = seleccionar_cerebro_modalidad(modalidad)
                
                # Construimos el Prompt del Usuario con toda la data recolectada
                prompt_usuario = f"""
                CONTEXTO: {modalidad} {aula_especifica}.
                LAPSO: {rango}.
                TEMA: {notas}.
                ALUMNO: {perfil_alumno if is_pei else "Grupo General"}.
                
                {texto_proyectos}
                
                {texto_pensum}
                
                GENERA UNA PLANIFICACIÓN SEMANAL (Lunes a Viernes).
                
                REGLAS DE REDACCIÓN OBLIGATORIAS:
                1. COMPETENCIA TÉCNICA: Verbo (Infinitivo) + Objeto + Condición.
                2. ESTRATEGIAS: Solo menciona el nombre (Ej: Lluvia de ideas). NO expliques.
                3. INICIOS: No repitas el mismo verbo dos días seguidos.
                4. FORMATO: Usa Negritas y saltos de línea.
                
                ESTRUCTURA DE SALIDA (Repetir para cada día):
                ### [DÍA]
                **1. TÍTULO:** (Corto)
                **2. COMPETENCIA TÉCNICA:**
                **3. EXPLORACIÓN (Inicio):**
                **4. DESARROLLO (Proceso):**
                **5. REFLEXIÓN (Cierre):**
                **6. ESTRATEGIAS:**
                **7. RECURSOS:**
                _______________________
                """
                
                respuesta_raw = generar_respuesta([
                    {"role": "system", "content": instrucciones_sistema},
                    {"role": "user", "content": prompt_usuario}
                ], 0.7)
                
                # Limpieza visual básica
                st.session_state.plan_actual = respuesta_raw.replace("**1.", "\n\n**1.").replace("### ", "\n\n### ")
                st.rerun()

    # 3. VISUALIZACIÓN Y GUARDADO (Mantiene lógica original)
    if 'plan_actual' in st.session_state and st.session_state.plan_actual:
        st.divider()
        st.success("✅ **Planificación Generada Exitosamente**")
        st.markdown(f'<div style="border:1px solid #ddd; padding:20px; border-radius:10px;">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        st.divider()
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("💾 Guardar en Mi Archivo"):
                try:
                    with st.spinner("Guardando..."):
                        df = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                        nuevo = pd.DataFrame([{
                            "FECHA": ahora_ve().strftime("%d/%m/%Y"),
                            "USUARIO": st.session_state.u['NOMBRE'],
                            "TEMA": f"{modalidad} - {notas}"[:50],
                            "CONTENIDO": st.session_state.plan_actual,
                            "ESTADO": "GUARDADO"
                        }])
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=pd.concat([df, nuevo], ignore_index=True))
                        st.success("¡Guardado!")
                        time.sleep(1)
                        st.session_state.plan_actual = ""
                        st.rerun()
                except Exception as e: st.error(f"Error: {e}")
        
        with c2:
            if st.button("🗑️ Descartar"):
                st.session_state.plan_actual = ""
                st.rerun()
