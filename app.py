# app.py (Versión con la Solución Definitiva de CSS para el Botón)

# --- BLOQUE 1: IMPORTACIONES Y CONFIGURACIÓN ---
# Se importan las librerías necesarias para el funcionamiento de la aplicación.
import streamlit as st
import yfinance as yf
import pandas as pd
import io
import base64

# Se importan los módulos personalizados que contienen la lógica de cada tipo de análisis.
from pypfopt import expected_returns, risk_models, EfficientFrontier
import fundamental_analysis
import portfolio_optimization
import technical_analysis

# Se configura el título de la pestaña del navegador, el layout y el estado inicial de la barra lateral.
st.set_page_config(page_title="Analytix Pro", layout="wide", initial_sidebar_state="expanded")

# Se inicializa una variable en el 'estado de la sesión' de Streamlit.
if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = None

# --- BLOQUE 2: BARRA LATERAL (SIDEBAR) ---
# En esta sección se define todo el contenido de la barra lateral izquierda.

# --- BLOQUE 2.1: BANNER DE MARCA Y ESTILOS GLOBALES ---
# Este bloque se encarga de la identidad visual de la aplicación.

@st.cache_data
def get_img_as_base64(file):
    """Función para leer una imagen local y convertirla a un string en base64."""
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Se lee el logo y se convierte. Asume que hay un archivo 'logo.png' en la misma carpeta.
img = get_img_as_base64("logo.png")

# Se utiliza st.markdown con HTML y CSS para inyectar estilos personalizados.
st.sidebar.markdown(f"""
    <style>
    /* Estilos del banner de la marca (sin cambios) */
    .banner-container {{ text-align: center; margin-bottom: 25px; }}
    .banner-img {{ width: 100%; border-radius: 10px; margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(59, 130, 246, 0.3); }}
    
    /* Estilos para las pestañas mejoradas (sin cambios) */
    button[data-baseweb="tab"] {{
        font-size: 16px !important;
        font-weight: bold !important;
        padding-top: 12px !important;
        padding-bottom: 12px !important;
        border-bottom-width: 2px !important;
        border-bottom-color: transparent !important;
        transition: all 0.3s ease;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        border-bottom-color: #3b82f6 !important;
        color: #3b82f6 !important;
    }}

    /* --- INICIO DE LA SOLUCIÓN DEFINITIVA DE CSS --- */
    
    /* 1. Contenedor para el botón: Lo usamos para centrar todo su contenido. */
    .cta-container {{
        display: flex;
        justify-content: center;
        width: 100%; /* Asegura que el contenedor ocupe todo el ancho de la barra lateral */
        margin-top: 20px;
    }}
    
    /* 2. Contenedor del botón de Streamlit: Streamlit envuelve cada botón en un div con la clase 'stButton'.
          Controlamos el ANCHO del botón a través de este div. */
    .cta-container .stButton {{
        width: 80% !important; /* El botón ocupará el 80% del ancho de la barra lateral. */
    }}
    
    /* 3. El elemento <button> real: Ahora que su contenedor tiene el tamaño correcto, hacemos que el
          botón interno ocupe el 100% de ese contenedor y le aplicamos todos los estilos. */
    .cta-container .stButton > button {{
        width: 100% !important; /* El botón llena su contenedor del 80% */
        background-color: #3b82f6 !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 18px !important;        
        padding: 14px 0px !important;      
        border: none !important;
        border-radius: 8px !important; /* Esquinas un poco más redondeadas */
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.39);
    }}

    /* Efecto hover: Sin cambios, pero ahora se aplicará correctamente */
    .cta-container .stButton > button:hover {{
        transform: scale(1.03);
        box-shadow: 0 6px 20px 0 rgba(59, 130, 246, 0.5);
    }}
    
    /* --- FIN DE LA SOLUCIÓN DEFINITIVA DE CSS --- */
    </style>
    
    <div class="banner-container">
        <img src="data:image/png;base64,{img}" class="banner-img">
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.header("Configuración de Análisis")

# --- BLOQUE 2.2: ENTRADAS Y CONTROLES DEL USUARIO ---
tickers_input = st.sidebar.text_input("Ingrese los Tickers (separados por comas)", "AAPL, MSFT, GOOGL")
periodo = st.sidebar.selectbox("Seleccione el Período", ["1y", "2y", "5y", "10y", "max"])
frecuencia = st.sidebar.radio("Frecuencia de Datos", ('Diario', 'Mensual'))
intervalo = "1d" if frecuencia == 'Diario' else "1mo"

st.sidebar.subheader("Parámetros de Optimización")
risk_free_rate = st.sidebar.number_input("Tasa Libre de Riesgo Anual (%)", value=2.0, step=0.1)
risk_free_rate_decimal = risk_free_rate / 100.0

tipo_analisis = st.sidebar.radio("Seleccione una Opción", 
    ("Análisis Fundamental", "Optimización de Portafolio (Markowitz)", "Análisis Técnico (Post-Optimización)", "Descargar Precios"))

# Envolvemos el botón en nuestro div 'cta-container' para activar los estilos.
st.sidebar.markdown('<div class="cta-container">', unsafe_allow_html=True)
run_button = st.sidebar.button("🚀 Ejecutar Análisis")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# --- BLOQUE 3: ÁREA PRINCIPAL ---
st.write("### Use la barra lateral para configurar su análisis y presione 'Ejecutar Análisis'.")

# --- BLOQUE 4: LÓGICA DE EJECUCIÓN ---
if run_button:
    # --- BLOQUE 4.1: VALIDACIÓN DE TICKERS ---
    tickers_original = [ticker.strip().upper() for ticker in tickers_input.split(",")]
    valid_tickers, invalid_tickers, ticker_names = [], [], {}
    with st.spinner(f"Validando tickers..."):
        for ticker in tickers_original:
            if not ticker: continue
            try:
                info = yf.Ticker(ticker).info
                if info.get('longName') is None and yf.Ticker(ticker).history(period="1d").empty: raise ValueError("Inválido")
                valid_tickers.append(ticker)
                ticker_names[ticker] = info.get('longName', ticker)
            except Exception:
                invalid_tickers.append(ticker)
    if invalid_tickers: st.warning(f"Tickers no encontrados o sin datos: {', '.join(invalid_tickers)}")
    if not valid_tickers:
        st.error("No hay tickers válidos para analizar.")
    else:
        st.success(f"Tickers válidos encontrados: {', '.join(valid_tickers)}")
        # --- BLOQUE 4.2: ENRUTAMIENTO DE ANÁLISIS ---
        if tipo_analisis == "Análisis Fundamental":
            fundamental_analysis.display_page(valid_tickers)
        elif tipo_analisis == "Optimización de Portafolio (Markowitz)":
            with st.spinner("Descargando datos y optimizando portafolio..."):
                all_prices = yf.download(valid_tickers, period=periodo, interval=intervalo, progress=False)
                if not all_prices.empty and 'Close' in all_prices.columns:
                    close_prices = all_prices['Close']
                    st.session_state.optimization_results = {
                        'all_prices': all_prices, 'ticker_names': ticker_names, 'valid_tickers': valid_tickers,
                        'periodo': periodo, 'intervalo': intervalo, 'risk_free_rate_decimal': risk_free_rate_decimal
                    }
                    portfolio_optimization.display_page(close_prices, valid_tickers, frecuencia, risk_free_rate_decimal, ticker_names)
                else: st.error("No se pudieron descargar datos de precios.")
        elif tipo_analisis == "Análisis Técnico (Post-Optimización)":
            if st.session_state.optimization_results:
                st.info("Mostrando análisis técnico para el último portafolio optimizado.")
                opt_data = st.session_state.optimization_results
                close_prices = opt_data['all_prices']['Close']
                mu = expected_returns.ema_historical_return(close_prices)
                S = risk_models.risk_matrix(close_prices, method='ledoit_wolf')
                ef = EfficientFrontier(mu, S)
                weights = ef.max_sharpe(risk_free_rate=opt_data['risk_free_rate_decimal'])
                cleaned_weights = ef.clean_weights()
                pesos_df = pd.DataFrame.from_dict(cleaned_weights, orient='index', columns=['Peso'])
                technical_analysis.display_page(pesos_df, opt_data['all_prices']['Close'], opt_data['ticker_names'])
            else: st.error("Primero ejecute una 'Optimización de Portafolio'.")
        elif tipo_analisis == "Descargar Precios":
            st.header(f"Precios Históricos de Cierre")
            with st.spinner("Descargando datos de precios..."):
                data = yf.download(valid_tickers, period=periodo, interval=intervalo, progress=False)
            if data.empty or 'Close' not in data.columns:
                st.error("No se pudieron descargar los datos de precios.")
            else:
                precios_df = data['Close'].copy()
                if len(valid_tickers) == 1: precios_df = precios_df.to_frame(name=valid_tickers[0])
                st.dataframe(precios_df)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    precios_df.reset_index().to_excel(writer, index=False, sheet_name='Precios_Historicos')
                st.download_button(
                    label="📥 Descargar Precios como Excel", data=output.getvalue(),
                    file_name=f"precios_{'_'.join(valid_tickers)}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")