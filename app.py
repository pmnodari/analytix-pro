# app.py (Versión con orden de análisis lógico)

import streamlit as st
import yfinance as yf
import pandas as pd
import io

# --- Importaciones de PyPortfolioOpt ---
from pypfopt import expected_returns, risk_models, EfficientFrontier

# Importar todos los módulos de análisis
import fundamental_analysis
import portfolio_optimization
import technical_analysis


# --- 1. CONFIGURACIÓN DE LA PÁGINA Y ESTADO DE SESIÓN ---
st.set_page_config(page_title="Analytix Pro", layout="wide", initial_sidebar_state="expanded")

if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = None

# --- 2. BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("Configuración de Análisis")

tickers_input = st.sidebar.text_input("Ingrese los Tickers (separados por comas)", "AAPL, MSFT, GOOGL")
periodo = st.sidebar.selectbox("Seleccione el Período", ["1y", "2y", "5y", "10y", "max"])
frecuencia = st.sidebar.radio("Frecuencia de Datos", ('Diario', 'Mensual'))
intervalo = "1d" if frecuencia == 'Diario' else "1mo"

st.sidebar.subheader("Parámetros de Optimización")
risk_free_rate = st.sidebar.number_input("Tasa Libre de Riesgo Anual (%)", value=2.0, step=0.1)
risk_free_rate_decimal = risk_free_rate / 100.0

# --- CAMBIO CLAVE: Orden lógico de análisis ---
# Se reordenan las opciones para seguir el flujo: Qué -> Cuánto -> Cuándo.
tipo_analisis = st.sidebar.radio("Seleccione una Opción", 
    (
        "Análisis Fundamental",                           # 1. ¿Qué comprar?
        "Optimización de Portafolio (Markowitz)",       # 2. ¿Cuánto comprar?
        "Análisis Técnico (Post-Optimización)",           # 3. ¿Cuándo comprar?
        "Descargar Precios"                               # 4. Utilidad extra
    ))

run_button = st.sidebar.button("Ejecutar Análisis")

# --- 3. ÁREA PRINCIPAL ---
st.title("Analytix Pro")
st.write("Use la barra lateral para configurar su análisis y presione 'Ejecutar Análisis'.")

if run_button:
    tickers_original = [ticker.strip().upper() for ticker in tickers_input.split(",")]
    valid_tickers = []
    invalid_tickers = []
    ticker_names = {}
    
    with st.spinner(f"Validando tickers..."):
        for ticker in tickers_original:
            if not ticker: continue
            try:
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                if info.get('longName') is None and ticker_obj.history(period="1d").empty:
                    raise ValueError("Ticker inválido.")
                valid_tickers.append(ticker)
                ticker_names[ticker] = info.get('longName', ticker)
            except Exception:
                invalid_tickers.append(ticker)

    if invalid_tickers: st.warning(f"Tickers no encontrados o sin datos: {', '.join(invalid_tickers)}")
    
    if not valid_tickers:
        st.error("No hay tickers válidos para analizar. Por favor, ingrese tickers correctos.")
    else:
        st.success(f"Tickers válidos encontrados: {', '.join(valid_tickers)}")
        
        # --- Lógica de Enrutamiento (sin cambios en la lógica, solo en el orden de los if/elif) ---
        
        if tipo_analisis == "Análisis Fundamental":
            fundamental_analysis.display_page(valid_tickers)
            
        elif tipo_analisis == "Optimización de Portafolio (Markowitz)":
            with st.spinner("Descargando datos y optimizando portafolio..."):
                all_prices = yf.download(valid_tickers, period=periodo, interval=intervalo, progress=False)
                if not all_prices.empty and 'Close' in all_prices.columns:
                    close_prices = all_prices['Close']
                    st.session_state.optimization_results = {
                        'all_prices': all_prices,
                        'ticker_names': ticker_names,
                        'valid_tickers': valid_tickers,
                        'periodo': periodo,
                        'intervalo': intervalo,
                        'risk_free_rate_decimal': risk_free_rate_decimal
                    }
                    portfolio_optimization.display_page(close_prices, valid_tickers, frecuencia, risk_free_rate_decimal, ticker_names)
                else:
                    st.error("No se pudieron descargar los datos de precios para la configuración seleccionada.")
        
        elif tipo_analisis == "Análisis Técnico (Post-Optimización)":
            if st.session_state.optimization_results and st.session_state.optimization_results['all_prices'] is not None:
                st.info("Mostrando análisis técnico para el último portafolio optimizado.")
                
                with st.spinner("Recalculando pesos para análisis técnico..."):
                    opt_data = st.session_state.optimization_results
                    close_prices = opt_data['all_prices']['Close']
                    mu = expected_returns.ema_historical_return(close_prices)
                    S = risk_models.risk_matrix(close_prices, method='ledoit_wolf')
                    ef = EfficientFrontier(mu, S)
                    weights = ef.max_sharpe(risk_free_rate=opt_data['risk_free_rate_decimal'])
                    cleaned_weights = ef.clean_weights()
                    pesos_df = pd.DataFrame.from_dict(cleaned_weights, orient='index', columns=['Peso'])
                
                technical_analysis.display_page(
                    pesos_df,
                    opt_data['all_prices']['Close'],
                    opt_data['ticker_names']
                )
            else:
                st.error("Por favor, primero ejecute una 'Optimización de Portafolio' para poder realizar el análisis técnico.")

        elif tipo_analisis == "Descargar Precios":
            st.header(f"Precios Históricos de Cierre")
            with st.spinner("Descargando datos de precios..."):
                data = yf.download(valid_tickers, period=periodo, interval=intervalo, progress=False)

            if data.empty or 'Close' not in data.columns:
                st.error("No se pudieron descargar los datos de precios.")
            else:
                precios_df = data['Close'].copy()
                if len(valid_tickers) == 1:
                    precios_df = precios_df.to_frame(name=valid_tickers[0])
                
                st.dataframe(precios_df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    precios_df.reset_index().to_excel(writer, index=False, sheet_name='Precios_Historicos')
                
                st.download_button(
                    label="📥 Descargar Precios como Excel",
                    data=output.getvalue(),
                    file_name=f"precios_{'_'.join(valid_tickers)}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )