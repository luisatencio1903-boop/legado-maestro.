# --- FUNCIÓN DE LIMPIEZA PARA EVITAR EL ERROR DEL .0 ---
def limpiar_cedula(valor):
    # Convierte a texto, quita espacios y elimina el ".0" si Google lo agregó
    return str(valor).strip().split('.')[0]

# --- MODIFICACIÓN EN LA PESTAÑA DE REGISTRO ---
with tab_registro:
    st.subheader("Validación de Nómina")
    r_cedula = st.text_input("Ingrese su Cédula para validar (Solo números)").strip()
    r_clave = st.text_input("Cree una contraseña segura", type="password")
    
    if st.button("REGISTRAR CUENTA"):
        if r_cedula:
            df_u = obtener_usuarios()
            # Limpiamos todas las cédulas de la lista de Excel para comparar
            cedulas_autorizadas = [limpiar_cedula(c) for c in df_u['CEDULA'].values]
            
            if r_cedula in cedulas_autorizadas:
                # Buscamos la posición exacta ignorando el formato
                idx = -1
                for i, c in enumerate(df_u['CEDULA'].values):
                    if limpiar_cedula(c) == r_cedula:
                        idx = i
                        break
                
                if pd.notna(df_u.loc[idx, 'CLAVE']) and str(df_u.loc[idx, 'CLAVE']).strip() != "":
                    st.warning("⚠️ Ya estás registrado. Ve a Iniciar Sesión.")
                else:
                    df_u.loc[idx, 'CLAVE'] = r_clave
                    df_u.loc[idx, 'ESTADO'] = "ACTIVO"
                    actualizar_usuarios(df_u)
                    st.success("✅ ¡Registro exitoso, Luis! Ya puedes iniciar sesión.")
            else:
                st.error(f"🚫 La cédula {r_cedula} no está en la nómina. Verifica en tu Excel que no tenga espacios.")
