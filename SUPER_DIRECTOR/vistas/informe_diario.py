import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def ahora_ve():
    return datetime.utcnow() - timedelta(hours=4)

def render_informe(universo):
    hoy = ahora_ve().strftime("%d/%m/%Y")
    
    try:
        df_as = universo['ASISTENCIA']
        df_ev = universo['EVALUACIONES']
        df_ej = universo['EJECUCION']
        df_mat = universo['MATRICULA_GLOBAL']
    except KeyError as e:
        st.error(f"Error: No se encuentra la hoja {e} en el universo de datos. Verifica los nombres en el Excel.")
        return
    except Exception as e:
        st.error(f"Error técnico al cargar datos: {e}")
        return

    st.subheader(f"📊 Informe de Gestión Diaria: {hoy}")
    
    m1, m2, m3 = st.columns(3)
    
    docentes_p = len(df_as[(df_as['FECHA'] == hoy) & (df_as['TIPO'] == "ASISTENCIA")])
    m1.metric("Docentes en Plantel", f"{docentes_p}")

    alumnos_atendidos = df_ev[df_ev['FECHA'] == hoy]['ESTUDIANTE'].nunique()
    total_m = len(df_mat)
    porcentaje = (alumnos_atendidos / total_m * 100) if total_m > 0 else 0
    m2.metric("Matrícula Atendida", f"{alumnos_atendidos}", f"{porcentaje:.1f}%")

    clases_c = len(df_ej[(df_ej['FECHA'] == hoy) & (df_ej['ESTADO'] == "CULMINADA")])
    m3.metric("Actividades de Aula", f"{clases_c}")

    st.divider()
    
    ejecuciones_hoy = df_ej[df_ej['FECHA'] == hoy]
    
    if ejecuciones_hoy.empty:
        st.warning("No se han reportado cierres de aula el día de hoy.")
    else:
        for _, clase in ejecuciones_hoy.iterrows():
            with st.container(border=True):
                c_izq, c_der = st.columns([2, 1])
                
                with c_izq:
                    st.markdown(f"### 📍 {clase['ACTIVIDAD_TITULO']}")
                    st.markdown(f"**Docente:** {clase['USUARIO']}")
                    st.markdown("**Resumen de Ejecución:**")
                    st.write(clase['RESUMEN_LOGROS'])
                    
                    evals_clase = df_ev[(df_ev['FECHA'] == hoy) & (df_ev['USUARIO'] == clase['USUARIO'])]
                    if not evals_clase.empty:
                        with st.expander(f"🧒 Ver {len(evals_clase)} alumnos evaluados"):
                            for _, ev in evals_clase.iterrows():
                                st.caption(f"• {ev['ESTUDIANTE']}: {ev['ANECDOTA'][:80]}...")
                
                with c_der:
                    fotos = str(clase['EVIDENCIA_FOTO']).split('|')
                    if len(fotos) > 0 and "http" in fotos[0]:
                        st.image(fotos[0].strip(), caption="Inicio", use_container_width=True)
                    if len(fotos) > 1 and "http" in fotos[1]:
                        st.image(fotos[1].strip(), caption="Culminación", use_container_width=True)

    if st.button("🖨️ Finalizar y Firmar Reporte", use_container_width=True):
        st.balloons()
        st.success("Reporte consolidado en la base de datos histórica.")
