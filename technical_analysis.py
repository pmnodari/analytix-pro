# technical_analysis.py (Versión Corregida y Robusta a Datos Insuficientes)

# --- SECCIÓN 0: IMPORTACIONES ---
import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import numpy as np

# --- SECCIÓN 1: LÓGICA DE INTERPRETACIÓN DE IA ---
def interpretar_indicadores(rsi, sma_50, sma_200, precio_actual):
    if pd.isna(sma_50) or pd.isna(sma_200): tendencia, emoji_tendencia = "Indeterminada", "🤔"
    elif sma_50 > sma_200: tendencia, emoji_tendencia = "Alcista", "📈"
    else: tendencia, emoji_tendencia = "Bajista", "📉"
    
    if pd.isna(rsi): momento, emoji_momento = "Indeterminado", "🤔"
    elif rsi > 70: momento, emoji_momento = "Sobrecompra", "🥵"
    elif rsi < 30: momento, emoji_momento = "Sobreventa", "🥶"
    else: momento, emoji_momento = "Neutral", "😐"
    
    if tendencia == "Alcista":
        if momento == "Sobreventa": veredicto = "🟢 **Señal de Compra Fuerte:** La acción está en una tendencia alcista y parece estar en un punto bajo (sobrevendida), lo que podría representar una excelente oportunidad de entrada."
        elif momento == "Neutral": veredicto = "🟡 **Señal de Acumulación/Mantener:** La acción sigue su tendencia alcista principal sin señales de agotamiento. Es un buen momento para mantener o añadir posiciones de forma gradual."
        else: veredicto = "⚠️ **Señal de Precaución:** Aunque la tendencia principal es fuerte, el activo está sobrecomprado (o su momento es incierto). Existe un riesgo de corrección a corto plazo. Se recomienda esperar un retroceso antes de entrar."
    elif tendencia == "Bajista": veredicto = "🔴 **Señal de Riesgo Elevado:** La acción se encuentra en una tendencia bajista. A pesar de posibles rebotes, el riesgo de que continúe cayendo es alto. Generalmente se recomienda evitar la compra hasta que la tendencia se revierta."
    else: veredicto = "⚪ **Tendencia Indeterminada:** No hay suficientes datos históricos para establecer una tendencia clara a largo plazo. Se recomienda prudencia y un análisis más profundo antes de tomar una decisión."
    
    rsi_text = f"{rsi:.2f}" if pd.notna(rsi) else "N/A"
    resumen = f"**Tendencia:** {emoji_tendencia} {tendencia} | **Momento:** {emoji_momento} {momento} (RSI: {rsi_text})"
    return resumen, veredicto

# --- SECCIÓN 2: FUNCIÓN PRINCIPAL DE VISUALIZACIÓN ---
def display_page(weights_df, prices_df, ticker_names):
    st.header("Análisis Técnico de Punto de Entrada")
    st.info("Este módulo analiza las acciones seleccionadas por el optimizador para evaluar si el **momento actual** es bueno para la compra.")
    acciones_a_analizar = weights_df[weights_df['Peso'] > 0].index
    for ticker in acciones_a_analizar:
        nombre_empresa = ticker_names.get(ticker, ticker)
        with st.expander(f"**Análisis para {nombre_empresa} ({ticker})**"):
            df = pd.DataFrame(prices_df[ticker])
            df.rename(columns={ticker: 'Close'}, inplace=True)
            df.ta.rsi(length=14, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            if df.empty:
                st.warning("No hay datos históricos disponibles para este ticker.")
                continue
            
            ultimo_rsi_series = df.get('RSI_14')
            ultimo_sma50_series = df.get('SMA_50')
            ultimo_sma200_series = df.get('SMA_200')
            
            ultimo_rsi = ultimo_rsi_series.iloc[-1] if ultimo_rsi_series is not None and not ultimo_rsi_series.empty else np.nan
            ultimo_sma50 = ultimo_sma50_series.iloc[-1] if ultimo_sma50_series is not None and not ultimo_sma50_series.empty else np.nan
            ultimo_sma200 = ultimo_sma200_series.iloc[-1] if ultimo_sma200_series is not None and not ultimo_sma200_series.empty else np.nan
            ultimo_precio = df['Close'].iloc[-1]
            
            resumen, veredicto = interpretar_indicadores(ultimo_rsi, ultimo_sma50, ultimo_sma200, ultimo_precio)
            st.markdown(f"##### {resumen}")
            st.markdown(veredicto)
            
            st.write("**Gráfico de Precios y Tendencia:**")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Precio de Cierre', line=dict(color='skyblue', width=2)))
            if ultimo_sma50_series is not None:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50 Días', line=dict(color='orange', width=1.5)))
            if ultimo_sma200_series is not None:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], mode='lines', name='SMA 200 Días', line=dict(color='red', width=1.5)))
            fig.update_layout(
                title=f'Análisis de Tendencia para {nombre_empresa}',
                yaxis_title='Precio',
                xaxis_title='Fecha',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)