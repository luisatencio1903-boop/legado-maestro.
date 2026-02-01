import streamlit as st
from streamlit_local_storage import LocalStorage
import json

def inicializar_maletin():
    return LocalStorage()

def persistir_en_dispositivo(llave, valor):
    local_storage = inicializar_maletin()
    try:
        # Convertimos los datos a texto JSON para el navegador
        dato_serializado = json.dumps(valor)
        local_storage.set(llave, dato_serializado)
    except Exception as e:
        st.error(f"Error de persistencia local: {e}")

def recuperar_del_dispositivo(llave):
    local_storage = inicializar_maletin()
    try:
        dato_serializado = local_storage.get(llave)
        if dato_serializado:
            return json.loads(dato_serializado)
        return None
    except:
        return None

def borrar_del_dispositivo(llave):
    local_storage = inicializar_maletin()
    local_storage.delete(llave)

def limpiar_todo_el_maletin():
    local_storage = inicializar_maletin()
    local_storage.deleteAll()
