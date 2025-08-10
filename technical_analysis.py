# technical_analysis.py (Módulo de Análisis de Punto de Entrada)

import streamlit as st
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

def interpretar_indicadores(rsi, sma_50, sma_200, precio_actual):
    """Genera un veredicto y una recomendación basada en los indicadores técnicos."""
    
    # 1. Determinar la Tendencia
    if sma_50 > sma_200:
        tendencia = "Alcista"
        emoji_tendencia = "📈"
    else:
        tendencia = "Bajista"
        emoji_tendencia = "📉"
        
    # 2. Determinar el Momento (RSI)
    if rsi > 70:
        momento = "Sobrecompra"
        emoji_momento = "🥵"
    elif rsi < 30:
        momento = "Sobreventa"
        emoji_momento = "🥶"
    else:
        momento = "Neutral"
        emoji_momento = "😐"
        
    # 3. Generar Veredicto Final
    if tendencia == "Alcista":
        if momento == "Sobreventa":
            veredicto = "🟢 **Señal de Compra Fuerte:** La acción está en una tendencia alcista y parece estar en un punto bajo (sobrevendida), lo que podría representar una excelente oportunidad de entrada."
        elif momento == "Neutral":
            veredicto = "🟡 **Señal de Acumulación/Mantener:** La acción sigue su tendencia alcista principal sin señales de agotamiento. Es un buen momento para mantener o añadir posiciones de forma gradual."
        else: # Sobrecompra
            veredicto = "⚠️ **Señal de Precaución:** Aunque la tendencia principal es fuerte, el activo está sobrecomprado. Existe un riesgo de corrección a corto plazo. Se recomienda esperar un retroceso antes de entrar."
    else: # Tendencia Bajista
        veredicto = "🔴 **Señal de Riesgo Elevado:** La acción se encuentra en una tendencia bajista. A pesar de posibles rebotes, el riesgo de que continúe cayendo es alto. Generalmente se recomienda evitar la compra hasta que la tendencia se revierta."

    resumen = f"**Tendencia:** {emoji_tendencia} {tendencia} (SMA50 vs SMA200) | **Momento:** {emoji_momento} {momento} (RSI: {rsi:.2f})"
    
    return resumen, veredicto


def display_page(weights_df, prices_df, ticker_names):
    """
    Muestra la página de análisis técnico para las acciones del portafolio optimizado.
    """
    st.header("Análisis Técnico de Punto de Entrada")
    st.info("Este módulo analiza las acciones seleccionadas por el optimizador para evaluar si el **momento actual** es bueno para la compra.")

    # Analizar solo las acciones con un peso asignado en el portafolio
    acciones_a_analizar = weights_df[weights_df['Peso'] > 0].index

    for ticker in acciones_a_analizar:
        nombre_empresa = ticker_names.get(ticker, ticker)
        
        with st.expander(f"**Análisis para {nombre_empresa} ({ticker})**"):
            
            # Crear un DataFrame específico para este ticker
            df = pd.DataFrame(prices_df[ticker])
            df.rename(columns={ticker: 'Close'}, inplace=True)

            # --- 1. Cálculo de Indicadores ---
            df.ta.rsi(length=14, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            df.dropna(inplace=True) # Eliminar filas sin datos de indicadores

            if df.empty:
                st.warning("No hay suficientes datos históricos para realizar el análisis técnico.")
                continue

            # --- 2. Obtener los últimos valores ---
            ultimo_rsi = df['RSI_14'].iloc[-1]
            ultimo_sma50 = df['SMA_50'].iloc[-1]
            ultimo_sma200 = df['SMA_200'].iloc[-1]
            ultimo_precio = df['Close'].iloc[-1]
            
            # --- 3. Generar Veredicto de la IA ---
            resumen, veredicto = interpretar_indicadores(ultimo_rsi, ultimo_sma50, ultimo_sma200, ultimo_precio)
            
            st.markdown(f"##### {resumen}")
            st.markdown(veredicto)
            
            # --- 4. Crear Gráfico ---
            st.write("**Gráfico de Precios y Tendencia:**")
            
            fig = go.Figure()
            # Añadir línea de precio
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Precio de Cierre', line=dict(color='skyblue', width=2)))
            # Añadir Medias Móviles
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50 Días', line=dict(color='orange', width=1.5)))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], mode='lines', name='SMA 200 Días', line=dict(color='red', width=1.5)))

            fig.update_layout(
                title=f'Análisis de Tendencia para {nombre_empresa}',
                yaxis_title='Precio',
                xaxis_title='Fecha',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)