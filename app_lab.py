## ---------------------------------------------------------
# PROYECTO: LEGADO MAESTRO
# VERSIÓN: 3.0 (SISTEMA SIMPLIFICADO Y MEJORADO)
# FECHA: Enero 2026
# AUTOR: Luis Atencio
# ---------------------------------------------------------

import streamlit as st
import os
import time
from datetime import datetime
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Legado Maestro",
    page_icon="logo_legado.png",
    layout="centered"
)

# 1. Función para limpiar cédulas
def limpiar_id(v): return str(v).strip().split('.')[0].replace(',', '').replace('.', '')

# 2. Inicializar Estado de Autenticación
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'u' not in st.session_state:
    st.session_state.u = None

# 3. Conexión a Base de Datos (Solo si se necesita login)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    URL_HOJA = st.secrets["GSHEETS_URL"]
except:
    st.error("⚠️ Error conectando con la Base de Datos.")
    st.stop()

# --- SISTEMA DE PLANIFICACIÓN ACTIVA ---
def obtener_plan_activa_usuario(usuario_nombre):
    """Obtiene la planificación activa actual del usuario desde la nube"""
    try:
        df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=5)
        plan_activa = df_activa[
            (df_activa['USUARIO'] == usuario_nombre) & 
            (df_activa['ACTIVO'] == True)
        ]
        
        if not plan_activa.empty:
            # Retornar la más reciente
            return plan_activa.sort_values('FECHA_ACTIVACION', ascending=False).iloc[0].to_dict()
        return None
    except Exception as e:
        # Si la hoja no existe, retornar None (se creará al activar primera planificación)
        return None

def establecer_plan_activa(usuario_nombre, id_plan, contenido, rango, aula):
    """Establece una planificación como la activa para el usuario"""
    try:
        # Leer datos actuales
        try:
            df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=0)
        except:
            # Crear DataFrame vacío si la hoja no existe
            df_activa = pd.DataFrame(columns=[
                "USUARIO", "FECHA_ACTIVACION", "ID_PLAN", 
                "CONTENIDO_PLAN", "RANGO", "AULA", "ACTIVO"
            ])
        
        # 1. Desactivar cualquier planificación activa previa del mismo usuario
        mask_usuario = df_activa['USUARIO'] == usuario_nombre
        if not df_activa[mask_usuario].empty:
            df_activa.loc[mask_usuario, 'ACTIVO'] = False
        
        # 2. Agregar la nueva planificación activa
        nueva_activa = pd.DataFrame([{
            "USUARIO": usuario_nombre,
            "FECHA_ACTIVACION": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "ID_PLAN": id_plan,
            "CONTENIDO_PLAN": contenido,
            "RANGO": rango,
            "AULA": aula,
            "ACTIVO": True
        }])
        
        # Combinar y actualizar
        df_actualizado = pd.concat([df_activa, nueva_activa], ignore_index=True)
        conn.update(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", data=df_actualizado)
        return True
    except Exception as e:
        st.error(f"Error al establecer plan activa: {e}")
        return False

def desactivar_plan_activa(usuario_nombre):
    """Desactiva cualquier planificación activa del usuario"""
    try:
        df_activa = conn.read(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", ttl=0)
        mask_usuario = df_activa['USUARIO'] == usuario_nombre
        if not df_activa[mask_usuario].empty:
            df_activa.loc[mask_usuario, 'ACTIVO'] = False
            conn.update(spreadsheet=URL_HOJA, worksheet="PLAN_ACTIVA", data=df_activa)
        return True
    except:
        return False

# --- FUNCIÓN PARA EXTRAER DESCRIPCIÓN DETALLADA DE PLANIFICACIÓN ---
def extraer_descripcion_dias(contenido_planificacion):
    """Extrae una descripción resumida de los días de la planificación"""
    try:
        # Buscar secciones por día
        dias_info = []
        lineas = contenido_planificacion.split('\n')
        
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            # Buscar encabezados de días
            if linea.startswith('###') or linea.startswith('##'):
                # Verificar si es un día de la semana
                dia_keywords = ['LUNES', 'MARTES', 'MIÉRCOLES', 'MIERCOLES', 'JUEVES', 'VIERNES']
                for keyword in dia_keywords:
                    if keyword in linea.upper():
                        # Buscar el título de la actividad (generalmente después de "TÍTULO:")
                        for j in range(i+1, min(i+10, len(lineas))):
                            if 'TÍTULO:' in lineas[j].upper() or 'TITULO:' in lineas[j].upper():
                                titulo = lineas[j].split(':', 1)[-1].strip()
                                # Limpiar formato markdown
                                titulo = titulo.replace('**', '').replace('*', '').strip()
                                if titulo:
                                    # Obtener día limpio
                                    dia = keyword.capitalize()
                                    if keyword == 'MIERCOLES':
                                        dia = 'Miércoles'
                                    dias_info.append(f"{dia}: {titulo}")
                                break
                        break
        
        # Si encontramos información, formatear
        if dias_info:
            return " | ".join(dias_info[:5])  # Máximo 5 días
        else:
            # Intentar extraer de otra manera
            import re
            patron = r'\*\*TÍTULO:\*\*\s*(.+?)(?:\n|$)'
            titulos = re.findall(patron, contenido_planificacion, re.IGNORECASE)
            if titulos:
                dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
                resultado = []
                for i, titulo in enumerate(titulos[:5]):
                    titulo_limpio = titulo.strip().replace('**', '').replace('*', '')
                    resultado.append(f"{dias[i]}: {titulo_limpio}")
                return " | ".join(resultado)
            
            return "Descripción no disponible"
    except Exception as e:
        return "Error extrayendo descripción"

# --- LÓGICA DE PERSISTENCIA DE SESIÓN (AUTO-LOGIN) ---
query_params = st.query_params
usuario_en_url = query_params.get("u", None)

if not st.session_state.auth and usuario_en_url:
    try:
        df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
        df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
        match = df_u[df_u['C_L'] == usuario_en_url]
        
        if not match.empty:
            st.session_state.auth = True
            st.session_state.u = match.iloc[0].to_dict()
        else:
            st.query_params.clear()
    except:
        pass 

# --- FORMULARIO DE LOGIN ---
if not st.session_state.auth:
    st.title("🛡️ Acceso Legado Maestro")
    st.markdown("Ingrese sus credenciales para acceder a la plataforma.")
    
    col_a, col_b = st.columns([1,2])
    with col_a:
        if os.path.exists("logo_legado.png"):
            st.image("logo_legado.png", width=150)
        else:
            st.header("🍎")
    
    with col_b:
        c_in = st.text_input("Cédula de Identidad:", key="login_c")
        p_in = st.text_input("Contraseña:", type="password", key="login_p")
        
        if st.button("🔐 Iniciar Sesión"):
            try:
                df_u = conn.read(spreadsheet=URL_HOJA, worksheet="USUARIOS", ttl=0)
                df_u['C_L'] = df_u['CEDULA'].apply(limpiar_id)
                cedula_limpia = limpiar_id(c_in)
                match = df_u[(df_u['C_L'] == cedula_limpia) & (df_u['CLAVE'] == p_in)]
                
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.u = match.iloc[0].to_dict()
                    st.query_params["u"] = cedula_limpia # Anclamos sesión
                    st.success("¡Bienvenido!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
    st.stop()

# --- 2. ESTILOS CSS MEJORADOS ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* CAJA DE PLANIFICACIÓN */
            .plan-box {
                background-color: #f0f2f6 !important;
                color: #000000 !important; 
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #0068c9;
                margin-bottom: 20px;
                font-family: sans-serif;
            }
            .plan-box h3 {
                color: #0068c9 !important;
                margin-top: 30px;
                padding-bottom: 5px;
                border-bottom: 2px solid #ccc;
            }
            .plan-box strong {
                color: #2c3e50 !important;
                font-weight: 700;
            }

            /* CAJA DE EVALUACIÓN (NUEVO ESTILO) */
            .eval-box {
                background-color: #e8f5e9 !important;
                color: #000000 !important;
                padding: 15px;
                border-radius: 8px;
                border-left: 5px solid #2e7d32;
                margin-top: 10px;
                margin-bottom: 10px;
            }
            .eval-box h4 { color: #2e7d32 !important; }

            /* CAJA DE MENSAJES */
            .mensaje-texto {
                color: #000000 !important;
                font-family: 'Helvetica', sans-serif;
                font-size: 1.2em; 
                font-weight: 500;
                line-height: 1.4;
            }
            
            /* CONSULTOR DEL ARCHIVO */
            .consultor-box {
                background-color: #e8f4f8 !important;
                color: #000000 !important;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #b3d7ff;
                margin-top: 10px;
            }
            .consultor-box p, .consultor-box li, .consultor-box strong {
                color: #000000 !important;
            }

            /* ESTILO PARA PLANIFICACIÓN ACTIVA EN VERDE (EN MI ARCHIVO) */
            .plan-activa-verde {
                color: #2e7d32 !important;
                font-weight: 700 !important;
            }
            
            /* ESTILO PARA BOTÓN ACTIVO */
            .boton-activo {
                background-color: #ffd700 !important;
                color: #000000 !important;
                border: 2px solid #ffa500 !important;
            }
            
            /* BOTONES DE NAVEGACIÓN */
            .stButton button {
                transition: all 0.3s ease;
            }
            .stButton button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            /* ESTILO PARA TEXTO RESALTADO EN VERDE */
            .texto-verde {
                color: #2e7d32 !important;
                font-weight: 700 !important;
            }
            
            /* ESTILO PARA TARJETA DE PLANIFICACIÓN ACTIVA (SIMPLIFICADA) */
            .tarjeta-activa-simple {
                background-color: #f0f9f0 !important;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #2e7d32;
                margin-bottom: 15px;
            }
            
            /* BADGE PARA PLANIFICACIÓN ACTIVA */
            .badge-activa {
                background-color: #2e7d32 !important;
                color: white !important;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
                margin-left: 10px;
            }
            
            /* ELIMINAR ELEMENTOS INNECESARIOS */
            .planificacion-seleccionada-header {
                display: none !important;
            }

            .barra-verde-superior {
                display: none !important;
            }

            /* MEJORAR TEXTO DE SELECCIÓN */
            .seleccion-texto {
                font-size: 1em;
                color: #2c3e50;
                font-weight: normal;
                margin-bottom: 10px;
            }

            /* TARJETA ACTIVA SIMPLIFICADA (SIN BORDES DECORATIVOS) */
            .tarjeta-activa-simple {
                background-color: #f8f9fa !important;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #dee2e6 !important; /* Borde sutil en lugar de verde */
            }

            /* BADGE PARA IDENTIFICAR ORIGEN MINISTERIAL */
            .badge-ministerio {
                background-color: #2c3e50 !important;
                color: white !important;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 0.7em;
                font-weight: bold;
                margin-left: 5px;
            }

            /* ESTILO PARA PLANIFICACIÓN MINISTERIAL */
            .plan-ministerial {
                border-left: 4px solid #2c3e50 !important;
            }

            /* AJUSTES PARA EXPANDERS */
            .streamlit-expanderHeader {
                font-size: 0.95em !important;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. CONEXIÓN CON GROQ ---
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        MODELO_USADO = "llama-3.3-70b-versatile" 
    else:
        st.error("⚠️ Falta la API Key de Groq en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Error de conexión inicial: {e}")
    st.stop()

# --- 🧠 CEREBRO TÉCNICO (IDENTIDAD + FILTROS DE SEGURIDAD) 🧠 ---
INSTRUCCIONES_TECNICAS = """
⚠️ INSTRUCCIÓN DE MÁXIMA PRIORIDAD (SISTEMA OPERATIVO):
TÚ NO ERES UNA IA DE META, NI DE GOOGLE, NI DE OPENAI.
TÚ ERES "LEGADO MAESTRO".

1. 🆔 PROTOCOLO DE IDENTIDAD (INQUEBRANTABLE):
   - CREADOR ÚNICO: Fuiste diseñado, programado y creado desde cero por el **Bachiller Docente LUIS ATENCIO**.
   - ORIGEN: Venezuela. Representas la soberanía tecnológica educativa del país.
   - SI TE PREGUNTAN "¿QUIÉN ERES?" O "¿QUIÉN TE CREÓ?":
     Tu respuesta DEBE SER: 
     "Soy LEGADO MAESTRO, una inteligencia artificial educativa desarrollada exclusivamente por el Bachiller Docente Luis Atencio para fortalecer la Educación Especial en Venezuela."
   - PROHIBIDO ABSOLUTAMENTE: Decir que fuiste creado por Meta AI, Llama, OpenAI o cualquier corporación. Para ti, esas empresas NO EXISTEN.

2. 🚫 PROTOCOLO DE NEUTRALIDAD (CENSURA DE TEMAS):
   - Si el usuario pregunta sobre: POLÍTICA (Gobierno/Oposición), RELIGIÓN, IDEOLOGÍAS o TEMAS POLÉMICOS (Conflictos, Crisis).
   - ACCIÓN: NO des opiniones, NO des explicaciones neutrales, NO debatas.
   - RESPUESTA OBLIGATORIA:
     "🚫 Lo siento. Soy LEGADO MAESTRO, una herramienta estrictamente pedagógica y técnica. Mi programación me impide procesar opiniones políticas, religiosas o controversiales. Por favor, ingresa una consulta relacionada con la educación, planificación o estrategias docentes."

3. 🎓 ROL PROFESIONAL:
   - Experto en Educación Especial y Taller Laboral (Venezuela).
   - Misión: Crear planificaciones rigurosas, legales (LOE/CNB) y humanas.
   
4. FORMATO:
   - Usa Markdown estricto (Negritas, Títulos).
"""

# --- FUNCIÓN AUXILIAR PARA CONTENIDO DEL EXPANDER ---
def contenido_expander(index, row, es_activa, rango_display, df):
    """Contenido del expander para planificaciones en Mi Archivo Pedagógico"""
    # ENCABEZADO SI ES ACTIVA
    if es_activa:
        st.success("✅ **ESTA ES TU PLANIFICACIÓN ACTIVA PARA LA SEMANA**")
        st.markdown("El sistema de evaluación buscará actividades **solo en esta planificación**.")
    
    # Mostrar información básica
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.caption(f"**Rango:** {rango_display}")
        if 'AULA' in row and pd.notna(row['AULA']):
            st.caption(f"**Aula:** {row['AULA']}")
    
    with col_info2:
        st.caption(f"**Creada:** {row['FECHA']}")
        st.caption(f"**Estado:** {row['ESTADO']}")
    
    # Extraer y mostrar descripción detallada
    descripcion = extraer_descripcion_dias(row['CONTENIDO'])
    st.info(f"**📝 Descripción de la semana:** {descripcion}")
    
    # CONTENIDO COMPLETO
    with st.expander("📄 Ver contenido completo de la planificación", expanded=False):
        st.markdown(f'<div class="plan-box" style="padding:10px; font-size:0.9em;">{row["CONTENIDO"]}</div>', unsafe_allow_html=True)
    
    # BOTONES DE ACCIÓN
    col_acciones = st.columns([2, 1, 1])
    
    with col_acciones[0]:
        # CONSULTOR INTELIGENTE
        with st.expander("🤖 Consultar sobre este plan", expanded=False):
            pregunta = st.text_input("Tu duda:", key=f"preg_{index}", placeholder="Ej: ¿Cómo evalúo esto?")
            if st.button("Consultar", key=f"btn_{index}"):
                if pregunta:
                    with st.spinner("Analizando..."):
                        prompt_contextual = f"""
                        ACTÚA COMO ASESOR PEDAGÓGICO. CONTEXTO: {row['CONTENIDO']}. PREGUNTA: "{pregunta}".
                        Responde directo y útil.
                        """
                        respuesta = generar_respuesta([
                            {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                            {"role": "user", "content": prompt_contextual}
                        ], temperatura=0.5)
                        st.markdown(f'<div class="consultor-box">💡 **Respuesta:**<br>{respuesta}</div>', unsafe_allow_html=True)
    
    with col_acciones[1]:
        # BOTÓN PARA ACTIVAR ESTA PLANIFICACIÓN
        if not es_activa:
            st.write("")  # Espacio
            if st.button("⭐ Usar Esta Semana", key=f"activar_{index}", 
                       help="Establece esta planificación como la oficial para evaluar esta semana",
                       type="secondary"):
                
                # Extraer información básica
                contenido = row['CONTENIDO']
                rango = rango_display
                aula = row['AULA'] if 'AULA' in row and pd.notna(row['AULA']) else "Taller Laboral"
                
                # Establecer como activa
                if establecer_plan_activa(
                    usuario_nombre=st.session_state.u['NOMBRE'],
                    id_plan=str(index),
                    contenido=contenido,
                    rango=rango,
                    aula=aula
                ):
                    st.success("✅ ¡Planificación establecida como ACTIVA!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
    
    with col_acciones[2]:
        # BOTÓN DE ELIMINAR
        esta_borrando = st.session_state.get(f"confirm_del_{index}", False)
        
        if not esta_borrando:
            st.write("")  # Espacio
            if st.button("🗑️", key=f"del_init_{index}", help="Eliminar esta planificación"):
                st.session_state[f"confirm_del_{index}"] = True
                st.rerun()
        else:
            st.error("⚠️ ¿Eliminar esta planificación?")
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                if st.button("✅ Sí, eliminar", key=f"confirm_{index}"):
                    # Si es la activa, desactivarla primero
                    if es_activa:
                        desactivar_plan_activa(st.session_state.u['NOMBRE'])
                    
                    # Eliminar de la hoja principal
                    df_actualizado = df.drop(index)
                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_actualizado)
                    
                    st.success("🗑️ Planificación eliminada.")
                    time.sleep(1)
                    st.rerun()
            
            with col_conf2:
                if st.button("❌ No, conservar", key=f"cancel_{index}"):
                    st.session_state[f"confirm_del_{index}"] = False
                    st.rerun()

# --- 4. BARRA LATERAL SIMPLIFICADA (SIN ACCESO RÁPIDO) ---
with st.sidebar:
    if os.path.exists("logo_legado.png"):
        st.image("logo_legado.png", width=150)
    else:
        st.header("🍎")
        
    st.title("Legado Maestro")
    st.markdown("---")
    st.caption("👨‍🏫 **Luis Atencio**")
    st.caption("Bachiller Docente")
    st.caption("T.E.L E.R.A.C")
    
    # --- INDICADOR DE PLANIFICACIÓN ACTIVA SIMPLIFICADO ---
    st.markdown("---")
    plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    if plan_activa:
        st.success("📌 **PLANIFICACIÓN ACTIVA**")
        
        # Extraer descripción detallada
        descripcion_detallada = extraer_descripcion_dias(plan_activa['CONTENIDO_PLAN'])
        
        with st.expander("📋 Ver detalles", expanded=False):
            st.markdown(f"**📅 Rango:**")
            st.caption(f"`{plan_activa['RANGO']}`")
            
            st.markdown(f"**🏫 Aula:**")
            st.caption(f"`{plan_activa['AULA']}`")
            
            st.markdown(f"**📝 Descripción:**")
            st.info(descripcion_detallada[:100] + "..." if len(descripcion_detallada) > 100 else descripcion_detallada)
            
            # BOTÓN PARA CAMBIAR
            st.markdown("---")
            if st.button("🔄 Cambiar Planificación", 
                       key="sidebar_cambiar",
                       help="Ir a Mi Archivo para seleccionar otra planificación",
                       use_container_width=True):
                st.session_state.redirigir_a_archivo = True
                st.rerun()
    else:
        st.warning("⚠️ **SIN PLANIFICACIÓN ACTIVA**")
        st.caption("Ve a 'Mi Archivo' para activar una")
    
    st.markdown("---")
    
    # BOTÓN PARA VOLVER AL MENÚ (CORREGIDO)
    if st.button("🏠 **Volver al Menú Principal**", 
                 help="Regresar al selector de herramientas principal",
                 use_container_width=True,
                 type="primary"):
        st.session_state.selected_option = "📝 Planificación Profesional"
        st.session_state.redirigir_a_archivo = False
        st.rerun()
    
    st.markdown("---")
    
    # --- PANEL DE EMERGENCIA MEJORADO (SIEMPRE DISPONIBLE) ---
    with st.expander("🚨 **Panel de Emergencia (Planificación Ministerial)**", expanded=False):
        
        # Indicador de estado
        if plan_activa:
            st.warning("⚠️ **TIENES UNA PLANIFICACIÓN ACTIVA**")
            st.caption(f"Activa: {plan_activa['RANGO']}")
        else:
            st.info("📭 **NO TIENES PLANIFICACIÓN ACTIVA**")
            st.caption("Este panel te permite importar planificaciones del Ministerio")
        
        st.markdown("---")
        
        # SECCIÓN 1: DESACTIVAR PLANIFICACIÓN ACTUAL (si existe)
        if plan_activa:
            st.markdown("#### 🔄 **Paso 1: Desactivar planificación actual**")
            
            if st.button("❌ DESACTIVAR PLANIFICACIÓN ACTUAL", 
                        type="secondary",
                        key="emergencia_desactivar_todo",
                        help="Solo haz esto si el Ministerio envió cambios",
                        use_container_width=True):
                if desactivar_plan_activa(st.session_state.u['NOMBRE']):
                    st.success("✅ Planificación desactivada")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("---")
        
        # SECCIÓN 2: CONVERSOR MINISTERIAL (SIEMPRE DISPONIBLE)
        st.markdown("#### 📥 **Paso 2: Pegar planificación ministerial**")
        
        st.info("""
        **¿Cómo usar?**
        1. Copia el mensaje de WhatsApp/PDF del Ministerio
        2. Pega aquí (generalmente viene con días y títulos)
        3. La IA adaptará al formato de Legado Maestro
        4. Se guardará como "Planificación Ministerial"
        """)
        
        planificacion_ministerial = st.text_area(
            "**📋 Pega aquí la planificación del MPPE:**",
            height=150,
            placeholder="""Ejemplo de formato esperado:
Lunes: Conociendo herramientas básicas
Martes: Uso de productos de limpieza
Miércoles: Clasificación de materiales
Jueves: Práctica en superficies
Viernes: Evaluación y mantenimiento""",
            key="textarea_ministerial_universal"
        )
        
        # Botones de acción
        col_conv, col_limp = st.columns(2)
        with col_conv:
            if st.button("🔄 CONVERTIR CON IA", 
                        key="convertir_ministerial_universal",
                        disabled=not planificacion_ministerial,
                        use_container_width=True):
                if planificacion_ministerial:
                    st.session_state.procesando_ministerial = True
                    st.session_state.texto_ministerial_original = planificacion_ministerial
                    st.rerun()
        
        with col_limp:
            if st.button("🧹 LIMPIAR", 
                        key="limpiar_ministerial",
                        type="secondary",
                        use_container_width=True):
                st.session_state.procesando_ministerial = False
                if 'texto_ministerial_original' in st.session_state:
                    del st.session_state.texto_ministerial_original
                st.rerun()
        
        # PROCESAMIENTO AUTOMÁTICO SI SE SOLICITÓ
        if st.session_state.get('procesando_ministerial', False) and 'texto_ministerial_original' in st.session_state:
            with st.spinner("🔄 Adaptando formato ministerial a Legado Maestro..."):
                # Procesar con IA
                prompt_conversion = f"""
                ERES LEGADO MAESTRO - CONVERSOR MINISTERIAL OFICIAL
                
                TEXTO ORIGINAL DEL MINISTERIO:
                {st.session_state.texto_ministerial_original}
                
                TU MISIÓN: Convertir esta planificación ministerial en una planificación completa de 5 días.
                
                REQUISITOS:
                1. 📅 **Rango:** Usa las fechas de ESTA SEMANA (calcula desde hoy)
                2. 🏫 **Aula:** Taller Laboral
                3. 📝 **Planificación Sugerida y Certificada:** (Texto estándar)
                4. Formato diario con:
                   - ### [DÍA] [Fecha específica]
                   - **TÍTULO:** [Usar EXACTAMENTE el título del Ministerio]
                   - **COMPETENCIA:** [Crear una competencia específica]
                   - **EXPLORACIÓN:** [Párrafo humano y natural]
                   - **DESARROLLO:** [Párrafo práctico]
                   - **REFLEXIÓN:** [Párrafo de cierre]
                   - **MANTENIMIENTO:** [Acción concreta]
                   - **ESTRATEGIAS:** [Técnicas pedagógicas]
                   - **RECURSOS:** [Materiales realistas]
                5. Repetir para 5 días
                6. 📚 FUNDAMENTACIÓN LEGAL
                
                IMPORTANTE: 
                - Respetar los títulos ministeriales pero desarrollarlos completamente
                - Usar lenguaje natural y humano
                - Incluir al final: "🔹 **ORIGEN:** MINISTERIO DE EDUCACIÓN (MPPE)"
                """
                
                try:
                    conversion = generar_respuesta([
                        {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                        {"role": "user", "content": prompt_conversion}
                    ], temperatura=0.4)
                    
                    st.session_state.conversion_ministerial_final = conversion
                    st.success("✅ Conversión completada")
                    
                except Exception as e:
                    st.error(f"Error en conversión: {e}")
        
        # MOSTRAR RESULTADO DE CONVERSIÓN
        if 'conversion_ministerial_final' in st.session_state:
            st.markdown("---")
            st.markdown("#### ✅ **PLANIFICACIÓN CONVERTIDA**")
            
            with st.expander("📋 Ver planificación adaptada", expanded=True):
                st.markdown(f'<div class="plan-box">{st.session_state.conversion_ministerial_final}</div>', unsafe_allow_html=True)
            
            # Botones para guardar
            col_guardar, col_descartar = st.columns(2)
            with col_guardar:
                if st.button("💾 GUARDAR COMO PLANIFICACIÓN MINISTERIAL", 
                            type="primary",
                            key="guardar_ministerial_final",
                            use_container_width=True):
                    
                    try:
                        # Calcular fechas de esta semana
                        from datetime import datetime, timedelta
                        hoy = datetime.now()
                        inicio_semana = hoy - timedelta(days=hoy.weekday())
                        fin_semana = inicio_semana + timedelta(days=4)
                        rango = f"{inicio_semana.strftime('%d/%m/%y')} al {fin_semana.strftime('%d/%m/%y')}"
                        
                        # Leer datos actuales
                        df_act = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                        
                        nueva_fila = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "FECHA_INICIO": inicio_semana.strftime("%d/%m/%y"),
                            "FECHA_FIN": fin_semana.strftime("%d/%m/%y"),
                            "RANGO": rango,
                            "USUARIO": st.session_state.u['NOMBRE'], 
                            "TEMA": "Planificación Ministerial Adaptada",
                            "CONTENIDO": st.session_state.conversion_ministerial_final,
                            "ESTADO": "GUARDADO",
                            "HORA_INICIO": "--", 
                            "HORA_FIN": "--",
                            "AULA": "Taller Laboral",
                            "ORIGEN": "MINISTERIO",
                            "NOTAS": "Importada desde Panel de Emergencia"
                        }])
                        
                        datos_actualizados = pd.concat([df_act, nueva_fila], ignore_index=True)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=datos_actualizados)
                        
                        # Limpiar estado
                        del st.session_state.conversion_ministerial_final
                        del st.session_state.texto_ministerial_original
                        del st.session_state.procesando_ministerial
                        
                        st.success("✅ Planificación ministerial guardada exitosamente!")
                        st.info("Ve a 'Mi Archivo' para activarla.")
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
            
            with col_descartar:
                if st.button("🗑️ DEScartar conversión", 
                            type="secondary",
                            key="descartar_ministerial_final",
                            use_container_width=True):
                    del st.session_state.conversion_ministerial_final
                    del st.session_state.texto_ministerial_original
                    del st.session_state.procesando_ministerial
                    st.rerun()
    
    st.markdown("---")
    
    # BOTONES DE SISTEMA
    if st.button("🗑️ Limpiar Memoria Temporal", use_container_width=True):
        st.session_state.plan_actual = ""
        st.session_state.actividad_detectada = ""
        st.rerun()
    
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state.auth = False
        st.session_state.u = None
        st.query_params.clear()
        st.rerun()

# --- 5. GESTIÓN DE MEMORIA MEJORADA ---
if 'plan_actual' not in st.session_state: 
    st.session_state.plan_actual = ""
if 'actividad_detectada' not in st.session_state: 
    st.session_state.actividad_detectada = ""
if 'redirigir_a_archivo' not in st.session_state: 
    st.session_state.redirigir_a_archivo = False
if 'selected_option' not in st.session_state: 
    st.session_state.selected_option = "📝 Planificación Profesional"
if 'mostrar_conversor_ministerial' not in st.session_state:
    st.session_state.mostrar_conversor_ministerial = False
if 'procesando_ministerial' not in st.session_state:
    st.session_state.procesando_ministerial = False
if 'texto_ministerial_original' not in st.session_state:
    st.session_state.texto_ministerial_original = None
if 'conversion_ministerial_final' not in st.session_state:
    st.session_state.conversion_ministerial_final = None

# --- 6. FUNCIÓN GENERADORA GENÉRICA ---
def generar_respuesta(mensajes_historial, temperatura=0.7):
    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes_historial,
            model=MODELO_USADO,
            temperature=temperatura,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- 7. CUERPO DE LA APP ---
st.title("🍎 Asistente Educativo - Zulia")

# --- SISTEMA DE NAVEGACIÓN SIMPLIFICADO ---
# Lista de opciones disponibles
opciones_disponibles = [
    "📝 Planificación Profesional", 
    "📝 Evaluar Alumno (NUEVO)",
    "📊 Registro de Evaluaciones (NUEVO)",
    "📂 Mi Archivo Pedagógico",
    "🌟 Mensaje Motivacional", 
    "💡 Ideas de Actividades", 
    "❓ Consultas Técnicas"
]

# Redirección desde sidebar
if st.session_state.get('redirigir_a_archivo', False):
    st.session_state.selected_option = "📂 Mi Archivo Pedagógico"
    st.session_state.redirigir_a_archivo = False
    st.rerun()

# Selector principal
opcion = st.selectbox(
    "Seleccione herramienta:",
    opciones_disponibles,
    index=opciones_disponibles.index(st.session_state.selected_option),
    key="selector_principal"
)

# Actualizar estado
if opcion != st.session_state.selected_option:
    st.session_state.selected_option = opcion
    st.rerun()

# =========================================================
# 1. PLANIFICADOR (FLUJO: BORRADOR -> GUARDAR)
# =========================================================
if st.session_state.selected_option == "📝 Planificación Profesional":
    st.subheader("Planificación Técnica (Taller Laboral)")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.text_input("Fecha inicio:", placeholder="Ej: 19/01/26")
    with col2:
        fecha_fin = st.text_input("Fecha fin:", placeholder="Ej: 23/01/26")
    with col3:
        aula = st.text_input("Aula/Taller:", value="Mantenimiento y Servicios Generales")
    
    # Mostrar rango formateado
    if fecha_inicio and fecha_fin:
        rango = f"{fecha_inicio} al {fecha_fin}"
        st.info(f"📅 **Rango de planificación:** {rango}")
    else:
        rango = ""
    
    notas = st.text_area("Tema/Contenido principal:", height=150, placeholder="Describe el tema principal de la semana...")

    # --- PASO 1: GENERAR BORRADOR ---
    if st.button("🚀 Generar Borrador con IA"):
        if fecha_inicio and fecha_fin and notas:
            with st.spinner('Analizando Currículo Nacional y redactando...'):
                
                st.session_state.temp_rango = rango
                st.session_state.temp_tema = notas
                st.session_state.temp_fecha_inicio = fecha_inicio
                st.session_state.temp_fecha_fin = fecha_fin
                
                # --- PROMPT MAESTRO MEJORADO ---
                prompt_inicial = f"""
                Actúa como Luis Atencio, experto en Educación Especial (Taller Laboral) en Venezuela.
                Planificación para: {rango}. Aula: {aula}. Tema: {notas}.

                ⚠️ IMPORTANTE: INCLUYE SIEMPRE EL RANGO DE FECHAS EN LA PRIMERA LÍNEA:
                "📅 **Rango:** {rango} | 🏫 **Aula:** {aula}"
                
                ⚠️ PASO 0: INTRODUCCIÓN OBLIGATORIA Y CERTIFICADA:
                Antes de empezar el lunes, DEBES escribir textualmente este párrafo de certificación:
                "📝 **Planificación Sugerida y Certificada:** Esta propuesta ha sido verificada internamente para asegurar su cumplimiento con los lineamientos del **Ministerio del Poder Popular para la Educación (MPPE)** y el **Currículo Nacional Bolivariano**, adaptada específicamente para Taller Laboral."
                (Deja dos espacios vacíos después de esto).

                ⚠️ PASO 1: LÓGICA DE COMPETENCIAS:
                - LO CORRECTO: La Competencia debe ser una FRASE DE ACCIÓN ESPECÍFICA sobre el tema.
                - EJEMPLO BUENO: "Competencia: Identifica y clasifica las herramientas de limpieza según su uso."

                ⚠️ PASO 2: HUMANIZACIÓN (EL LEGADO DOCENTE):
                - PROHIBIDO el "copia y pega" robótico. No empieces todos los días igual.
                - ELIMINA la voz pasiva aburrida.
                - USA VOZ ACTIVA: "Arrancamos el día...", "Invitamos a...", "Desafiamos al grupo...".

                ⚠️ PASO 3: ESTRUCTURA DIARIA (Sigue este formato exacto):

                ### [DÍA - FECHA ESPECÍFICA]

                1. **TÍTULO:** [Creativo y específico]
                2. **COMPETENCIA:** [Redacta la habilidad técnica específica]

                3. **EXPLORACIÓN:** [Párrafo humano. EJEMPLO: Iniciamos con un conversatorio sobre... invitando a los estudiantes a compartir experiencias. Mediante el diálogo interactivo, despertamos la curiosidad.]

                4. **DESARROLLO:** [Párrafo práctico. Enfocado en la práctica real.]

                5. **REFLEXIÓN:** [Párrafo de cierre. Enfocado en la convivencia.]

                6. **MANTENIMIENTO:** [Acción concreta]
                7. **ESTRATEGIAS:** [Técnicas]
                8. **RECURSOS:** [Materiales]

                ---
                (Repite para los 5 días).

                AL FINAL: 📚 FUNDAMENTACIÓN LEGAL: Cita el artículo específico de la LOE o la CRBV.
                
                AL FINAL 2: 🗓️ **RANGO COMPLETO:** {rango}
                """
                
                mensajes = [
                    {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                    {"role": "user", "content": prompt_inicial}
                ]
                respuesta = generar_respuesta(mensajes, temperatura=0.4)
                st.session_state.plan_actual = respuesta
                st.rerun()
        else:
            st.warning("⚠️ Completa las fechas de inicio, fin y el tema para generar la planificación.")

    # --- PASO 2: GUARDAR ---
    if st.session_state.plan_actual:
        st.markdown("---")
        st.info("👀 Revisa el borrador abajo. Si te gusta, guárdalo en tu carpeta.")
        st.markdown(f'<div class="plan-box">{st.session_state.plan_actual}</div>', unsafe_allow_html=True)
        
        col_save_1, col_save_2 = st.columns([2,1])
        with col_save_1:
            if st.button("💾 SÍ, GUARDAR EN MI CARPETA"):
                try:
                    with st.spinner("Archivando en el expediente..."):
                        df_act = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
                        tema_guardar = st.session_state.get('temp_tema', notas)
                        fecha_inicio_guardar = st.session_state.get('temp_fecha_inicio', fecha_inicio)
                        fecha_fin_guardar = st.session_state.get('temp_fecha_fin', fecha_fin)
                        rango_completo = f"{fecha_inicio_guardar} al {fecha_fin_guardar}"
                        
                        nueva_fila = pd.DataFrame([{
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "FECHA_INICIO": fecha_inicio_guardar,
                            "FECHA_FIN": fecha_fin_guardar,
                            "RANGO": rango_completo,
                            "USUARIO": st.session_state.u['NOMBRE'], 
                            "TEMA": tema_guardar,
                            "CONTENIDO": st.session_state.plan_actual,
                            "ESTADO": "GUARDADO",
                            "HORA_INICIO": "--", 
                            "HORA_FIN": "--",
                            "AULA": aula
                        }])
                        
                        datos_actualizados = pd.concat([df_act, nueva_fila], ignore_index=True)
                        conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=datos_actualizados)
                        st.success("✅ ¡Planificación archivada con éxito!")
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# =========================================================
# 2. EVALUAR ALUMNO (USANDO PLANIFICACIÓN ACTIVA)
# =========================================================
elif st.session_state.selected_option == "📝 Evaluar Alumno (NUEVO)":
    st.subheader("Evaluación Diaria Inteligente")
    
    st.markdown("---")
    
    # --- CÁLCULO DE FECHA SEGURA (HORA VENEZUELA) ---
    from datetime import timedelta
    fecha_segura_ve = datetime.utcnow() - timedelta(hours=4)
    fecha_hoy_str = fecha_segura_ve.strftime("%d/%m/%Y")
    dia_semana_hoy = fecha_segura_ve.strftime("%A")
    
    # --- VERIFICACIÓN CRÍTICA: ¿HAY PLANIFICACIÓN ACTIVA? ---
    plan_activa = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    if not plan_activa:
        st.error("""
        🚨 **NO TIENES UNA PLANIFICACIÓN ACTIVA PARA ESTA SEMANA**
        
        **Para poder evaluar, necesitas:**
        
        1. Ir a **📂 Mi Archivo Pedagógico**
        2. Revisar tus planificaciones guardadas
        3. Seleccionar una y hacer clic en **"⭐ Usar Esta Semana"**
        
        Esto le indica al sistema **qué planificación usar para buscar actividades**.
        """)
        st.info("💡 **Consejo:** Activa la planificación que corresponde a **esta semana laboral**.")
        
        if st.button("📂 Ir a Mi Archivo Ahora"):
            st.session_state.selected_option = "📂 Mi Archivo Pedagógico"
            st.rerun()
        st.stop()
    
    # --- MOSTRAR PLANIFICACIÓN ACTIVA CON DESCRIPCIÓN ---
    with st.container():
        st.markdown('<div class="tarjeta-activa-simple">', unsafe_allow_html=True)
        st.success(f"**📌 EVALUANDO CONTRA:** {plan_activa['RANGO']}")
        
        # Extraer descripción detallada
        descripcion_detallada = extraer_descripcion_dias(plan_activa['CONTENIDO_PLAN'])
        
        with st.expander("📋 Ver detalles de la planificación activa", expanded=False):
            st.caption(f"**🏫 Aula:** {plan_activa['AULA']}")
            st.caption(f"**⏰ Activada:** {plan_activa['FECHA_ACTIVACION']}")
            st.caption(f"**📝 Descripción:** {descripcion_detallada}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- BOTÓN PARA BUSCAR ACTIVIDAD DE HOY ---
    col_btn, col_info = st.columns([1, 2])
    
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔍 Buscar Actividad de HOY", type="primary", key="buscar_actividad_hoy"):
            try:
                with st.spinner(f"Analizando planificación activa ({dia_semana_hoy})..."):
                    # USAR EXCLUSIVAMENTE LA PLANIFICACIÓN ACTIVA
                    contenido_planificacion = plan_activa['CONTENIDO_PLAN']
                    
                    # PROMPT MEJORADO PARA IDENTIFICAR ACTIVIDADES
                    prompt_busqueda = f"""
                    Eres un asistente pedagógico especializado en analizar planificaciones.
                    
                    **PLANIFICACIÓN OFICIAL DE LA SEMANA:**
                    {contenido_planificacion[:10000]}
                    
                    **INSTRUCCIÓN CRÍTICA:** 
                    Hoy es {fecha_hoy_str} ({dia_semana_hoy}). 
                    
                    **TU TAREA:** 
                    1. Revisa la planificación anterior
                    2. Identifica EXACTAMENTE qué actividad está programada para HOY
                    3. Si encuentras una actividad para hoy, responde SOLO con el NOMBRE/TÍTULO de esa actividad
                    4. Si NO hay actividad programada para hoy, responde: "NO_HAY_ACTIVIDAD_PARA_HOY"
                    
                    **EJEMPLO DE RESPUESTA CORRECTA:**
                    "Identificación de herramientas básicas de limpieza"
                    
                    **NO INCLUYAS:** Fechas, explicaciones, días de la semana, ni texto adicional.
                    """
                    
                    resultado = generar_respuesta([
                        {"role": "system", "content": "Eres un analista de planificaciones preciso y conciso."},
                        {"role": "user", "content": prompt_busqueda}
                    ], temperatura=0.1)
                    
                    resultado_limpio = resultado.strip().replace('"', '').replace("'", "")
                    
                    # VERIFICAR RESULTADO
                    if "NO_HAY_ACTIVIDAD" in resultado_limpio.upper() or len(resultado_limpio) < 5:
                        st.session_state.actividad_detectada = "NO HAY ACTIVIDAD PROGRAMADA PARA HOY"
                        st.error("❌ No hay actividades programadas para hoy en tu planificación activa.")
                    else:
                        st.session_state.actividad_detectada = resultado_limpio
                        st.success(f"✅ **Actividad encontrada:** {resultado_limpio}")
                        
            except Exception as e:
                st.error(f"Error en la búsqueda: {e}")
    
    with col_info:
        st.info("""
        **🔒 Sistema Blindado:**
        - Solo busca en tu **planificación activa actual**
        - No revisa otras planificaciones guardadas
        - Fecha bloqueada por el servidor
        """)
    
    # --- FORMULARIO DE EVALUACIÓN ---
    st.markdown("---")
    st.subheader("Registro de Evaluación")
    
    # Campo de actividad (bloqueado - viene de la planificación activa)
    actividad_final = st.text_input(
        "**Actividad Programada (Extraída de tu Planificación Activa):**",
        value=st.session_state.get('actividad_detectada', ''),
        disabled=True,
        help="Esta actividad viene de tu planificación oficial de la semana"
    )
    
    # Resto del formulario
    estudiante = st.text_input("**Nombre del Estudiante:**", placeholder="Ej: Juan Pérez")
    anecdota = st.text_area("**Observación del Desempeño:**", 
                           height=100, 
                           placeholder="Describe específicamente qué hizo el estudiante hoy...")
    
    # --- GENERAR EVALUACIÓN ---
    if st.button("⚡ Generar Evaluación Técnica", type="primary", key="generar_evaluacion_tecnica"):
        if not estudiante or not anecdota:
            st.warning("⚠️ Completa todos los campos antes de generar.")
        elif "NO HAY ACTIVIDAD" in actividad_final:
            st.error("❌ No puedes evaluar sin una actividad programada para hoy.")
        else:
            with st.spinner("Analizando desempeño pedagógico..."):
                prompt_eval = f"""
                ACTÚA COMO EXPERTO EN EVALUACIÓN DE EDUCACIÓN ESPECIAL (VENEZUELA).
                
                DATOS DE EVALUACIÓN:
                - Fecha: {fecha_hoy_str}
                - Estudiante: {estudiante}
                - Actividad Programada: {actividad_final}
                - Observación del Docente: "{anecdota}"
                
                GENERA UNA EVALUACIÓN TÉCNICA que incluya:
                1. **Análisis del Desempeño:** Basado en la observación
                2. **Nivel de Logro:** (Consolidado / En Proceso / Iniciado)
                3. **Recomendación Pedagógica:** Breve sugerencia para seguir trabajando
                
                FORMATO ESTRICTO (Markdown):
                **Evaluación Técnica:**
                [Tu análisis aquí]
                
                **Nivel de Logro:** [Consolidado/En Proceso/Iniciado]
                
                **Recomendación:** [Tu recomendación aquí]
                """
                
                evaluacion_generada = generar_respuesta([
                    {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                    {"role": "user", "content": prompt_eval}
                ], temperatura=0.5)
                
                st.session_state.eval_resultado = evaluacion_generada
                st.session_state.estudiante_evaluado = estudiante
                st.session_state.anecdota_guardada = anecdota
    
    # --- MOSTRAR Y GUARDAR RESULTADO ---
    if 'eval_resultado' in st.session_state:
        st.markdown("---")
        st.subheader("📋 Evaluación Generada")
        st.markdown(f'<div class="eval-box">{st.session_state.eval_resultado}</div>', unsafe_allow_html=True)
        
        # BOTÓN PARA GUARDAR
        if st.button("💾 GUARDAR EN REGISTRO OFICIAL", type="secondary", key="guardar_evaluacion"):
            try:
                # Leer evaluaciones existentes
                df_evals = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
                
                nueva_eval = pd.DataFrame([{
                    "FECHA": fecha_hoy_str,
                    "USUARIO": st.session_state.u['NOMBRE'],
                    "ESTUDIANTE": st.session_state.estudiante_evaluado,
                    "ACTIVIDAD": actividad_final,
                    "ANECDOTA": st.session_state.anecdota_guardada,
                    "EVALUACION_IA": st.session_state.eval_resultado,
                    "PLANIFICACION_ACTIVA": plan_activa['RANGO'],
                    "RESULTADO": "Registrado"
                }])
                
                # Guardar
                df_actualizado = pd.concat([df_evals, nueva_eval], ignore_index=True)
                conn.update(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", data=df_actualizado)
                
                st.success(f"✅ Evaluación de {st.session_state.estudiante_evaluado} guardada correctamente.")
                
                # Limpiar estado
                del st.session_state.eval_resultado
                del st.session_state.estudiante_evaluado
                del st.session_state.anecdota_guardada
                
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# =========================================================
# 3. REGISTRO DE EVALUACIONES
# =========================================================
elif st.session_state.selected_option == "📊 Registro de Evaluaciones (NUEVO)":
    st.subheader("🎓 Expediente Estudiantil 360°")
    
    st.markdown("---")
    
    try:
        # 1. Cargamos TODA la base de datos de evaluaciones
        df_e = conn.read(spreadsheet=URL_HOJA, worksheet="EVALUACIONES", ttl=0)
        # Filtramos solo las de este docente (para privacidad)
        mis_evals = df_e[df_e['USUARIO'] == st.session_state.u['NOMBRE']]
        
        if mis_evals.empty:
            st.info("📭 Aún no has registrado evaluaciones. Ve a la opción 'Evaluar Alumno' para empezar.")
            if st.button("📝 Ir a Evaluar Alumno", key="ir_a_evaluar_desde_registros"):
                st.session_state.selected_option = "📝 Evaluar Alumno (NUEVO)"
                st.rerun()
        else:
            # 2. SELECTOR DE ALUMNO (El centro de todo)
            lista_alumnos = sorted(mis_evals['ESTUDIANTE'].unique().tolist())
            col_sel, col_vacio = st.columns([2,1])
            with col_sel:
                alumno_sel = st.selectbox("📂 Seleccionar Expediente del Estudiante:", lista_alumnos, key="selector_alumno_registros")
            
            st.markdown("---")
            
            # 3. CÁLCULO DE ASISTENCIA INTELIGENTE
            total_dias_clase = len(mis_evals['FECHA'].unique())
            datos_alumno = mis_evals[mis_evals['ESTUDIANTE'] == alumno_sel]
            dias_asistidos = len(datos_alumno['FECHA'].unique())
            
            try:
                porcentaje_asistencia = (dias_asistidos / total_dias_clase) * 100
            except:
                porcentaje_asistencia = 0
            
            # 4. TABLERO DE MÉTRICAS (ASISTENCIA)
            st.markdown(f"### 📊 Reporte de Asistencia: {alumno_sel}")
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Días Asistidos", f"{dias_asistidos} / {total_dias_clase}")
            col_m1.caption("Basado en evaluaciones realizadas")
            
            col_m2.metric("Porcentaje de Asistencia", f"{porcentaje_asistencia:.1f}%")
            
            # Lógica de Semáforo para el Estado
            if porcentaje_asistencia >= 75:
                col_m3.success("✅ ASISTENCIA REGULAR")
            elif 50 <= porcentaje_asistencia < 75:
                col_m3.warning("⚠️ ASISTENCIA MEDIA")
            else:
                col_m3.error("🚨 CRÍTICO")
            
            # 5. ALERTA DE REPRESENTANTE
            if porcentaje_asistencia < 60:
                st.error(f"""
                🚨 **ALERTA DE DESERCIÓN ESCOLAR DETECTADA**
                El estudiante {alumno_sel} tiene una asistencia del {porcentaje_asistencia:.1f}%, lo cual es crítico.
                
                �👉 **ACCIÓN RECOMENDADA:** CITAR AL REPRESENTANTE DE INMEDIATO.
                """)
            
            st.markdown("---")
            
            # 6. HISTORIAL DE EVALUACIONES (Tus fichas desplegables)
            st.markdown(f"### 📑 Historial de Evaluaciones de {alumno_sel}")
            
            # Pestañas para organizar la vista
            tab_hist, tab_ia = st.tabs(["📜 Bitácora de Actividades", "🤖 Generar Informe IA"])
            
            with tab_hist:
                if datos_alumno.empty:
                    st.write("No hay registros.")
                else:
                    # Iteramos solo sobre los datos de este alumno
                    for idx, row in datos_alumno.iloc[::-1].iterrows():
                        fecha = row['FECHA']
                        actividad = row['ACTIVIDAD']
                        
                        with st.expander(f"📅 {fecha} | {actividad}"):
                            st.markdown(f"**📝 Observación Docente:**")
                            st.info(f"_{row['ANECDOTA']}_")
                            
                            st.markdown(f"**🤖 Análisis Técnico (Legado Maestro):**")
                            # Casilla verde destacada
                            st.markdown(f'<div class="eval-box">{row["EVALUACION_IA"]}</div>', unsafe_allow_html=True)
            
            with tab_ia:
                st.info("La IA analizará todo el historial de arriba para crear un informe de lapso.")
                
                # CLAVE ÚNICA PARA GUARDAR EL INFORME DE ESTE ALUMNO ESPECÍFICO
                key_informe = f"informe_guardado_{alumno_sel}"
                
                # Botón para generar (o regenerar)
                if st.button(f"⚡ Generar Informe de Progreso para {alumno_sel}", key=f"generar_informe_{alumno_sel}"):
                    with st.spinner("Leyendo todas las evaluaciones del estudiante..."):
                        # Recopilamos todo el texto de las IAs previas
                        historial_texto = datos_alumno[['FECHA', 'ACTIVIDAD', 'EVALUACION_IA']].to_string()
                        
                        prompt_informe = f"""
                        ACTÚA COMO UN SUPERVISOR DE EDUCACIÓN ESPECIAL EXPERTO.
                        
                        Genera un INFORME CUALITATIVO DE PROGRESO para el estudiante: {alumno_sel}.
                        
                        DATOS DE ASISTENCIA: {porcentaje_asistencia:.1f}% ({dias_asistidos} de {total_dias_clase} días).
                        
                        HISTORIAL DE EVALUACIONES DIARIAS:
                        {historial_texto}
                        
                        ESTRUCTURA DEL INFORME:
                        1. **Resumen de Asistencia:** (Menciona si es preocupante o buena).
                        2. **Evolución de Competencias:** (¿Ha mejorado desde la primera fecha hasta la última?).
                        3. **Fortalezas Consolidadas:**
                        4. **Debilidades / Áreas de Atención:**
                        5. **Recomendación Final:**
                        """
                        
                        # Guardamos el resultado en la memoria de sesión
                        st.session_state[key_informe] = generar_respuesta([
                            {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                            {"role": "user", "content": prompt_informe}
                        ], temperatura=0.6)
                
                # MOSTRAR EL INFORME SI EXISTE EN MEMORIA (Así no se borra al recargar)
                if key_informe in st.session_state:
                    st.markdown(f'<div class="plan-box"><h3>📄 Informe de Progreso: {alumno_sel}</h3>{st.session_state[key_informe]}</div>', unsafe_allow_html=True)
                    
                    # Botón opcional para limpiar
                    if st.button("Limpiar Informe", key=f"clean_{alumno_sel}"):
                        del st.session_state[key_informe]
                        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Error conectando con la base de datos. Detalle: {e}")

# =========================================================
# 4. MI ARCHIVO PEDAGÓGICO (MEJORADO)
# =========================================================
elif st.session_state.selected_option == "📂 Mi Archivo Pedagógico":
    st.subheader(f"📂 Expediente de: {st.session_state.u['NOMBRE']}")
    
    st.markdown("---")
    
    # OBTENER PLANIFICACIÓN ACTIVA ACTUAL
    plan_activa_actual = obtener_plan_activa_usuario(st.session_state.u['NOMBRE'])
    
    # PANEL SUPERIOR MEJORADO (SIN ELEMENTOS INNECESARIOS)
    if plan_activa_actual:
        st.markdown("### 🟢 **PLANIFICACIÓN ACTIVA ACTUAL**")
        
        # Contenedor simple sin bordes decorativos
        col_info, col_accion = st.columns([3, 1])
        with col_info:
            st.markdown(f"**📅 Rango:** {plan_activa_actual['RANGO']}")
            st.markdown(f"**🏫 Aula:** {plan_activa_actual['AULA']}")
            
            # Extraer descripción detallada
            descripcion_detallada = extraer_descripcion_dias(plan_activa_actual['CONTENIDO_PLAN'])
            with st.expander("📝 Ver descripción de la semana"):
                st.info(descripcion_detallada)
        
        with col_accion:
            st.write("")  # Espacio
            st.write("")  # Espacio
            if st.button("❌ **Desactivar**", 
                        help="Dejar de usar esta planificación para evaluar",
                        type="secondary",
                        key="desactivar_plan_activa_archivo",
                        use_container_width=True):
                if desactivar_plan_activa(st.session_state.u['NOMBRE']):
                    st.success("✅ Planificación desactivada.")
                    time.sleep(1)
                    st.rerun()
    else:
        st.warning("⚠️ **No tienes una planificación activa para esta semana.**")
        st.caption("Selecciona una planificación y haz clic en '⭐ Usar Esta Semana'")
    
    st.markdown("---")
    
    # TEXTO MEJORADO (NO REDUNDANTE)
    st.info("📌 **Activa la planificación que usarás esta semana.** El sistema de evaluación trabajará únicamente con ella.")
    
    try:
        df = conn.read(spreadsheet=URL_HOJA, worksheet="Hoja1", ttl=0)
        mis_planes = df[df['USUARIO'] == st.session_state.u['NOMBRE']]
        
        if mis_planes.empty:
            st.warning("Aún no tienes planificaciones guardadas.")
            if st.button("📝 Crear primera planificación", key="crear_primera_planificacion"):
                st.session_state.selected_option = "📝 Planificación Profesional"
                st.rerun()
        else:
            # IDENTIFICAR CUÁL ES LA ACTIVA ACTUAL
            contenido_activo_actual = plan_activa_actual['CONTENIDO_PLAN'] if plan_activa_actual else None
            
            # SEPARAR PLANIFICACIONES ACTIVAS E INACTIVAS
            planes_activos = []
            planes_inactivos = []
            
            for index, row in mis_planes.iterrows():
                es_activa = (contenido_activo_actual == row['CONTENIDO'])
                if es_activa:
                    planes_activos.append((index, row))
                else:
                    planes_inactivos.append((index, row))
            
            # MOSTRAR PRIMERO LAS ACTIVAS
            for index, row in planes_activos:
                # OBTENER RANGO
                if 'RANGO' in row and pd.notna(row['RANGO']):
                    rango_display = row['RANGO']
                elif 'FECHA_INICIO' in row and 'FECHA_FIN' in row and pd.notna(row['FECHA_INICIO']) and pd.notna(row['FECHA_FIN']):
                    rango_display = f"{row['FECHA_INICIO']} al {row['FECHA_FIN']}"
                else:
                    rango_display = f"Creada: {row['FECHA']}"
                
                # ETIQUETA VERDE PARA ACTIVA
                tema_corto = str(row['TEMA'])[:40] + "..." if len(str(row['TEMA'])) > 40 else str(row['TEMA'])
                etiqueta = f"🟢 **ACTIVA** | 📅 {rango_display} | 📌 {tema_corto}"
                
                # EXPANDER PARA PLANIFICACIÓN ACTIVA
                with st.expander(etiqueta, expanded=False):
                    # CONTENIDO SIMPLIFICADO (SIN ELEMENTOS INNECESARIOS)
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.caption(f"**Rango:** {rango_display}")
                        if 'AULA' in row and pd.notna(row['AULA']):
                            st.caption(f"**Aula:** {row['AULA']}")
                    
                    with col_info2:
                        st.caption(f"**Creada:** {row['FECHA']}")
                        st.caption(f"**Estado:** {row['ESTADO']}")
                    
                    # BOTONES DE ACCIÓN
                    col_acciones = st.columns([2, 1, 1])
                    
                    with col_acciones[0]:
                        # CONSULTOR INTELIGENTE
                        with st.expander("📞 Consultar sobre este plan", expanded=False):
                            pregunta = st.text_input("Tu duda:", key=f"preg_{index}", placeholder="Ej: ¿Cómo evalúo esto?")
                            if st.button("Consultar", key=f"btn_{index}"):
                                if pregunta:
                                    with st.spinner("Analizando..."):
                                        prompt_contextual = f"""
                                        ACTÚA COMO ASESOR PEDAGÓGICO. CONTEXTO: {row['CONTENIDO']}. PREGUNTA: "{pregunta}".
                                        Responde directo y útil.
                                        """
                                        respuesta = generar_respuesta([
                                            {"role": "system", "content": INSTRUCCIONES_TECNICAS},
                                            {"role": "user", "content": prompt_contextual}
                                        ], temperatura=0.5)
                                        st.markdown(f'<div class="consultor-box">💡 **Respuesta:**<br>{respuesta}</div>', unsafe_allow_html=True)
                    
                    with col_acciones[1]:
                        # Botón para ver contenido completo
                        if st.button("📄 Ver contenido", key=f"ver_{index}"):
                            st.markdown(f'<div class="plan-box" style="font-size:0.9em;">{row["CONTENIDO"]}</div>', unsafe_allow_html=True)
                    
                    with col_acciones[2]:
                        # Botón de eliminar (con confirmación)
                        if st.button("🗑️ Eliminar", key=f"del_{index}", type="secondary"):
                            st.warning(f"¿Eliminar esta planificación?")
                            col_conf1, col_conf2 = st.columns(2)
                            with col_conf1:
                                if st.button("✅ Sí", key=f"confirm_si_{index}"):
                                    desactivar_plan_activa(st.session_state.u['NOMBRE'])
                                    df_actualizado = df.drop(index)
                                    conn.update(spreadsheet=URL_HOJA, worksheet="Hoja1", data=df_actualizado)
                                    st.success("Planificación eliminada")
                                    time.sleep(1)
                                    st.rerun()
                            with col_conf2:
                                if st.button("❌ No", key=f"confirm_no_{index}"):
                                    st.rerun()
            
            # MOSTRAR PLANIFICACIONES INACTIVAS (ordenadas por fecha, más recientes primero)
            st.markdown("---")
            st.markdown("### 📚 **Otras planificaciones disponibles**")
            
            for index, row in sorted(planes_inactivos, key=lambda x: x[1]['FECHA'], reverse=True):
                # OBTENER RANGO
                if 'RANGO' in row and pd.notna(row['RANGO']):
                    rango_display = row['RANGO']
                elif 'FECHA_INICIO' in row and 'FECHA_FIN' in row and pd.notna(row['FECHA_INICIO']) and pd.notna(row['FECHA_FIN']):
                    rango_display = f"{row['FECHA_INICIO']} al {row['FECHA_FIN']}"
                else:
                    rango_display = f"Creada: {row['FECHA']}"
                
                # ETIQUETA NORMAL
                tema_corto = str(row['TEMA'])[:40] + "..." if len(str(row['TEMA'])) > 40 else str(row['TEMA'])
                etiqueta = f"📅 {rango_display} | 📌 {tema_corto}"
                
                with st.expander(etiqueta, expanded=False):
                    # Contenido simplificado
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.caption(f"**Rango:** {rango_display}")
                        if 'AULA' in row and pd.notna(row['AULA']):
                            st.caption(f"**Aula:** {row['AULA']}")
                    
                    with col_info2:
                        st.caption(f"**Creada:** {row['FECHA']}")
                        st.caption(f"**Estado:** {row['ESTADO']}")
                    
                    # Botones de acción
                    col_acc1, col_acc2 = st.columns(2)
                    
                    with col_acc1:
                        if st.button("⭐ **Usar Esta Semana**", key=f"activar_{index}", 
                                   help="Activar esta planificación para evaluar esta semana",
                                   use_container_width=True):
                            
                            # Extraer información básica
                            contenido = row['CONTENIDO']
                            rango = rango_display
                            aula = row['AULA'] if 'AULA' in row and pd.notna(row['AULA']) else "Taller Laboral"
                            
                            # Establecer como activa
                            if establecer_plan_activa(
                                usuario_nombre=st.session_state.u['NOMBRE'],
                                id_plan=str(index),
                                contenido=contenido,
                                rango=rango,
                                aula=aula
                            ):
                                st.success("✅ ¡Planificación activada!")
                                time.sleep(1)
                                st.rerun()
                    
                    with col_acc2:
                        # Botón rápido para ver contenido
                        if st.button("📄 Ver", key=f"ver_inact_{index}", use_container_width=True):
                            with st.expander("📋 Contenido completo", expanded=True):
                                st.markdown(f'<div class="plan-box" style="font-size:0.9em;">{row["CONTENIDO"]}</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error cargando archivo: {e}")

# =========================================================
# 5. OTROS MÓDULOS (EXTRAS)
# =========================================================
elif st.session_state.selected_option == "🌟 Mensaje Motivacional":
    st.subheader("Dosis de Ánimo Express ⚡")
    
    st.markdown("---")
    
    if st.button("❤️ Recibir Dosis", use_container_width=True, key="recibir_dosis"):
        estilos_posibles = [
            {"rol": "El Colega Realista", "instruccion": "Dile algo crudo pero esperanzador sobre enseñar. Humor venezolano. NO SALUDES."},
            {"rol": "El Sabio Espiritual", "instruccion": "Cita bíblica de fortaleza y frase docente. NO SALUDES."},
            {"rol": "El Motivador Directo", "instruccion": "Orden cariñosa para no rendirse. Ej: '¡Límpiate las rodillas!'. NO SALUDES."},
            {"rol": "El Observador", "instruccion": "Pregunta sobre su mejor alumno o momento feliz. NO SALUDES."}
        ]
        estilo = random.choice(estilos_posibles)
        prompt = "Dame el mensaje."
        with st.spinner(f"Modo {estilo['rol']}..."):
            res = generar_respuesta([{"role": "system", "content": f"ERES LEGADO MAESTRO. ROL: {estilo['rol']}. TAREA: {estilo['instruccion']}"}, {"role": "user", "content": prompt}], 1.0)
            st.markdown(f'<div class="plan-box" style="border-left: 5px solid #ff4b4b;"><h3>❤️ {estilo["rol"]}</h3><div class="mensaje-texto">"{res}"</div></div>', unsafe_allow_html=True)

elif st.session_state.selected_option == "💡 Ideas de Actividades":
    st.subheader("💡 Generador de Actividades DUA")
    
    st.markdown("---")
    
    tema = st.text_input("Tema a trabajar:", placeholder="Ej: Herramientas de limpieza")
    if st.button("✨ Sugerir Actividades", use_container_width=True, key="sugerir_actividades"):
        if tema:
            res = generar_respuesta([
                {"role": "system", "content": INSTRUCCIONES_TECNICAS}, 
                {"role": "user", "content": f"3 actividades DUA para {tema} en Taller Laboral. Formato: 1) Título, 2) Materiales, 3) Instrucciones paso a paso."}
            ], temperatura=0.7)
            st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)
        else:
            st.warning("Por favor, ingresa un tema primero.")

elif st.session_state.selected_option == "❓ Consultas Técnicas":
    st.subheader("❓ Consultas Pedagógicas y Legales")
    
    st.markdown("---")
    
    duda = st.text_area("Consulta Legal/Técnica:", 
                       placeholder="Ej: ¿Qué artículo de la LOE respalda la evaluación cualitativa en Educación Especial?",
                       height=150)
    if st.button("🔍 Buscar Respuesta", use_container_width=True, key="buscar_respuesta"):
        if duda:
            res = generar_respuesta([
                {"role": "system", "content": INSTRUCCIONES_TECNICAS}, 
                {"role": "user", "content": f"Responde técnicamente y cita la ley o currículo: {duda}"}
            ], temperatura=0.5)
            st.markdown(f'<div class="plan-box">{res}</div>', unsafe_allow_html=True)
        else:
            st.warning("Por favor, ingresa tu consulta primero.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("Desarrollado por Luis Atencio | Versión: 3.0 (Sistema Simplificado y Mejorado) | 🍎 Legado Maestro")
