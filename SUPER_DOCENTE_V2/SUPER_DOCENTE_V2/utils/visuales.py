import streamlit as st

def cargar_css():
    hide_streamlit_style = """
    <style>
        /* Ocultar elementos nativos de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* CAJAS DE PLANIFICACIÓN */
        .plan-box {
            background-color: #f8f9fa !important;
            color: #212529 !important; 
            padding: 25px;
            border-radius: 12px;
            border-left: 6px solid #0068c9;
            margin-bottom: 25px;
            font-family: 'Helvetica', sans-serif;
            font-size: 1.05rem;
            line-height: 1.6;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .plan-box h3 {
            color: #0068c9 !important;
            margin-top: 25px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
            font-weight: 700;
        }
        
        .plan-box strong {
            color: #2c3e50 !important;
            font-weight: 700;
        }

        /* CAJAS DE EVALUACIÓN (Resultados IA) */
        .eval-box {
            background-color: #e8f5e9 !important;
            color: #1b5e20 !important;
            padding: 20px;
            border-radius: 10px;
            border-left: 6px solid #2e7d32;
            margin-top: 15px;
            margin-bottom: 15px;
            font-family: 'Arial', sans-serif;
        }
        
        .eval-box h4 { 
            color: #2e7d32 !important; 
            font-weight: bold;
        }

        /* ESTILOS PARA ELEMENTOS DE FORMULARIO (MÓVIL) */
        .stSelectbox label {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            color: #0d47a1 !important;
            margin-bottom: 8px;
        }
        
        /* Botones más altos y fáciles de tocar */
        .stButton button {
            width: 100%;
            border-radius: 8px;
            height: 3.5em;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Separadores visuales */
        hr {
            margin-top: 2rem;
            margin-bottom: 2rem;
            border: 0;
            border-top: 1px solid #dee2e6;
        }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
