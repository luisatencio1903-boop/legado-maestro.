import streamlit as st
from utils.maletin import recuperar_del_dispositivo
from utils.sync_engine import sincronizar_todo_el_maletin

def render_sincronizador(conn):
    st.title("🚀 Sincronización de Datos")
    st.info("Utilice este módulo al disponer de una conexión estable a Internet.")

    # Verificar qué hay en el maletín
    asis = recuperar_del_dispositivo("maletin_asistencia")
    clase = recuperar_del_dispositivo("maletin_super_docente")

    if not asis and not (clase and clase.get("av_resumen")):
        st.success("✨ **¡Tu maletín está vacío!** Todo tu trabajo ya está en la nube.")
        if st.button("🏠 Volver al Inicio"):
            st.session_state.pagina_actual = "HOME"
            st.rerun()
    else:
        st.warning("📦 **Tienes datos pendientes por subir:**")
        
        if asis:
            st.markdown(f"- 🕒 **Asistencia del día:** {asis.get('HORA_ENTRADA')} / {asis.get('HORA_SALIDA')}")
        
        if clase and clase.get("av_resumen"):
            st.markdown(f"- 🏫 **Actividad de Aula:** {clase.get('av_titulo_hoy', 'Pendiente')}")

        st.divider()
        
        if st.button("♻️ SUBIR TODO A LA NUBE AHORA", type="primary", use_container_width=True):
            URL_HOJA = st.secrets["GSHEETS_URL"]
            sincronizar_todo_el_maletin(conn, URL_HOJA)
