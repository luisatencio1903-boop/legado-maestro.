import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Diagnóstico", page_icon="🚑")
st.title("🚑 Diagnóstico Médico de la App")

# 1. VERIFICAR VERSIÓN DE LA HERRAMIENTA
try:
    version = genai.__version__
    st.subheader(f"1. Versión de Google AI: {version}")
    
    # Si la versión es vieja (menor a 0.5.0), Streamlit no hizo caso al requirements.txt
    if version < "0.5.0":
        st.error("❌ LA VERSIÓN ES MUY VIEJA. Streamlit no actualizó.")
        st.info("Solución: Borrar la app en Streamlit y volverla a crear.")
    else:
        st.success("✅ La versión está actualizada.")
except:
    st.error("⚠️ No se pudo leer la versión.")

# 2. PROBAR LA LLAVE Y VER QUÉ MODELOS PERMITE
st.subheader("2. Lista de Modelos Disponibles para tu Llave:")
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # Le pedimos a Google que nos diga qué modelos nos deja usar
        encontrados = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                st.code(m.name) # Muestra el nombre exacto
                encontrados.append(m.name)
        
        if not encontrados:
            st.error("❌ Tu llave funciona, pero Google dice que NO tienes acceso a ningún modelo.")
            st.warning("Posible causa: El proyecto en Google Cloud no tiene la API activada o es una llave limitada.")
        else:
            st.success(f"✅ ¡Google nos respondió! Tienes acceso a {len(encontrados)} modelos.")
            st.info("Copia uno de los nombres de arriba (ej: 'models/gemini-pro') para usarlo en la app.")
            
    else:
        st.error("❌ No encontré la GOOGLE_API_KEY en los Secrets.")

except Exception as e:
    st.error(f"❌ Error grave conectando con Google: {e}")
