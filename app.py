# app.py (Versión Final con Lógica de Sesión para Bienvenida Dinámica)

# --- BLOQUE 1: IMPORTACIONES Y CONFIGURACIÓN ---
import streamlit as st
import yfinance as yf
import pandas as pd
import io
import base64
from pypfopt import expected_returns, risk_models, EfficientFrontier

import fundamental_analysis
import portfolio_optimization
import strategy_analysis
import technical_analysis

st.set_page_config(page_title="Analytix Pro", layout="wide", initial_sidebar_state="expanded")

if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = None

# --- CAMBIO CLAVE 1: INICIALIZACIÓN DE LA BANDERA DE SESIÓN ---
# Si nuestra bandera 'analysis_started' no existe en la memoria, la creamos y la ponemos en False.
if 'analysis_started' not in st.session_state:
    st.session_state.analysis_started = False

# --- BLOQUE 2: BARRA LATERAL (SIDEBAR) ---
# --- BLOQUE 2.1: BANNER DE MARCA Y ESTILOS GLOBALES ---
@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f: data = f.read()
    return base64.b64encode(data).decode()

img = get_img_as_base64("logo.png")

st.sidebar.markdown(f"""
    <style>
    .banner-container {{ text-align: center; margin-bottom: 25px; }}
    .banner-img {{ width: 100%; border-radius: 10px; margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(59, 130, 246, 0.3); }}
    button[data-baseweb="tab"] {{ font-size: 16px !important; font-weight: bold !important; padding: 12px 0px !important; border-bottom-width: 2px !important; border-bottom-color: transparent !important; transition: all 0.3s ease; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ border-bottom-color: #3b82f6 !important; color: #3b82f6 !important; }}
    .cta-container {{ display: flex; justify-content: center; width: 100%; margin-top: 20px; }}
    .cta-container .stButton {{ width: 80% !important; }}
    .cta-container .stButton > button {{ width: 100% !important; background-color: #3b82f6 !important; color: white !important; font-weight: bold !important; font-size: 18px !important; padding: 14px 0px !important; border: none !important; border-radius: 8px !important; transition: all 0.3s ease; box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.39); }}
    .cta-container .stButton > button:hover {{ transform: scale(1.03); box-shadow: 0 6px 20px 0 rgba(59, 130, 246, 0.5); }}
    </style>
    <div class="banner-container"><img src="data:image/png;base64,{img}" class="banner-img"></div>
    """, unsafe_allow_html=True)

st.sidebar.header("Configuración de Análisis")

# --- BLOQUE 2.2: ENTRADAS Y CONTROLES DEL USUARIO ---
tickers_input = st.sidebar.text_input("Ingrese los Tickers (separados por comas)", "AAPL, MSFT, GOOGL, JPM, V")

with st.sidebar.expander("💡 Ayuda: ¿Qué es un Ticker?"):
    st.info("""
    Un "Ticker" es el símbolo único de una empresa en la bolsa. Por ejemplo:
    - **Apple Inc.** es `AAPL`
    - **Microsoft Corp.** es `MSFT`
    - **Coca-Cola Co.** es `KO`
    Puedes encontrar el ticker de cualquier empresa buscándola en **Yahoo Finanzas**.
    """)

periodo = st.sidebar.selectbox("Seleccione el Período", ["1y", "2y", "5y", "10y", "max"], index=2)
frecuencia = st.sidebar.radio("Frecuencia de Datos", ('Diario', 'Mensual'))
intervalo = "1d" if frecuencia == 'Diario' else "1mo"

st.sidebar.subheader("Parámetros de Optimización y Backtesting")
risk_free_rate = st.sidebar.number_input("Tasa Libre de Riesgo Anual (%)", value=2.0, step=0.1)
risk_free_rate_decimal = risk_free_rate / 100.0

st.sidebar.write("**Seleccione una Opción:**")
tipo_analisis = st.sidebar.radio("Tipo de Análisis", 
    ("Análisis Fundamental", "Optimización de Portafolio (Markowitz)", "Análisis y Backtesting de Estrategia", "Análisis Técnico (Post-Optimización)", "Descargar Precios"), 
    label_visibility="collapsed")

if tipo_analisis == "Análisis Fundamental":
    st.sidebar.caption("Evalúa la salud financiera y el valor intrínseco de las empresas para responder: **¿Qué comprar?**")
elif tipo_analisis == "Optimización de Portafolio (Markowitz)":
    st.sidebar.caption("Calcula la combinación ideal de activos para maximizar el retorno ajustado al riesgo y responder: **¿Cuánto comprar?**")
elif tipo_analisis == "Análisis y Backtesting de Estrategia":
    st.sidebar.caption("Analiza la composición de tu portafolio y simula su rendimiento histórico para responder: **¿Por qué funciona esta estrategia?**")
elif tipo_analisis == "Análisis Técnico (Post-Optimización)":
    st.sidebar.caption("Analiza el momento del mercado para los activos de tu portafolio para responder: **¿Cuándo comprar?**")

st.sidebar.markdown('<div class="cta-container">', unsafe_allow_html=True)
run_button = st.sidebar.button("🚀 Ejecutar Análisis")
st.sidebar.markdown('</div>', unsafe_allow_html=True)


# --- BLOQUE 3: ÁREA PRINCIPAL ---

# --- CAMBIO CLAVE 2: DIBUJADO CONDICIONAL DEL MENSAJE ---
# El mensaje de bienvenida ahora solo se dibuja si nuestra bandera 'analysis_started' es False.
if not st.session_state.analysis_started:
    st.title("Bienvenido a Analytix Pro")
    st.markdown("""
    <div style="font-size: 24px;">
    Analytix Pro es su asistente de inversión personal, diseñado para guiarlo a través de un flujo de trabajo profesional para la toma de decisiones.
    <br><br>
    <strong>Siga estos pasos para un análisis completo:</strong>
    <ol>
        <li><strong>📊 Análisis Fundamental:</strong> Comience aquí para evaluar la calidad de las empresas que le interesan. <em>(¿Qué comprar?)</em></li>
        <li><strong>⚖️ Optimización de Portafolio:</strong> Una vez que tenga sus empresas, descubra la mezcla perfecta para su portafolio. <em>(¿Cuánto comprar de cada una?)</em></li>
        <li><strong>🔬 Análisis y Backtesting:</strong> Valide su estrategia. Entienda su composición y compruebe su rendimiento histórico. <em>(¿Es una buena estrategia?)</em></li>
        <li><strong>📈 Análisis Técnico:</strong> Con su estrategia validada, determine el mejor momento para entrar al mercado. <em>(¿Cuándo comprar?)</em></li>
    </ol>
    Use la <strong>barra lateral</strong> para configurar los parámetros y seleccionar un análisis. Luego, presione <strong>'Ejecutar Análisis'</strong>.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # --- BLOQUE 2.3: AVISO DE COPYRIGHT ---
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Analytix Pro. Todos los derechos reservados.")

# --- BLOQUE 4: LÓGICA DE EJECUCIÓN ---
if run_button:
    # --- CAMBIO CLAVE 3: ACTIVACIÓN DE LA BANDERA ---
    # En cuanto se presiona el botón, ponemos la bandera en True.
    # En la siguiente recarga, el bloque de bienvenida ya no se mostrará.
    st.session_state.analysis_started = True
    
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
        if tipo_analisis == "Análisis Fundamental":
            fundamental_analysis.display_page(valid_tickers)
        elif tipo_analisis == "Optimización de Portafolio (Markowitz)":
            with st.spinner("Descargando datos y optimizando portafolio..."):
                all_prices = yf.download(valid_tickers, period=periodo, interval=intervalo, progress=False)
                if not all_prices.empty and 'Close' in all_prices.columns:
                    close_prices = all_prices['Close'].dropna()
                    mu = expected_returns.ema_historical_return(close_prices)
                    S = risk_models.risk_matrix(close_prices, method='ledoit_wolf')
                    ef = EfficientFrontier(mu, S)
                    weights = ef.max_sharpe(risk_free_rate=risk_free_rate_decimal)
                    cleaned_weights = ef.clean_weights()
                    st.session_state.optimization_results = {
                        'all_prices': all_prices, 'ticker_names': ticker_names, 'valid_tickers': valid_tickers,
                        'weights': cleaned_weights, 'periodo': periodo, 'intervalo': intervalo, 
                        'risk_free_rate_decimal': risk_free_rate_decimal
                    }
                    portfolio_optimization.display_page(close_prices, valid_tickers, frecuencia, risk_free_rate_decimal, ticker_names)
                else: st.error("No se pudieron descargar datos de precios.")
        elif tipo_analisis == "Análisis y Backtesting de Estrategia":
            if st.session_state.optimization_results and st.session_state.optimization_results.get('weights'):
                st.info("Mostrando análisis y backtesting para el último portafolio optimizado.")
                strategy_analysis.display_page(st.session_state.optimization_results)
            else:
                st.error("Por favor, primero ejecute una 'Optimización de Portafolio' para poder realizar este análisis.")
        elif tipo_analisis == "Análisis Técnico (Post-Optimización)":
            if st.session_state.optimization_results and st.session_state.optimization_results.get('weights'):
                st.info("Mostrando análisis técnico para el último portafolio optimizado.")
                opt_data = st.session_state.optimization_results
                pesos_df = pd.DataFrame.from_dict(opt_data['weights'], orient='index', columns=['Peso'])
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
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )