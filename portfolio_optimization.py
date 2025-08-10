# portfolio_optimization.py (Versión Final con Jerarquía Visual Mejorada)

import streamlit as st
import pandas as pd
import plotly.express as px
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt import plotting
import matplotlib.pyplot as plt

def generar_conclusion_optimizacion(pesos, rendimiento, volatilidad, sharpe, ticker_names):
    # ... (código de esta función sin cambios) ...
    if pesos.empty: return "No se pudo generar un portafolio con asignaciones positivas."
    activo_principal_ticker = pesos['Peso'].idxmax(); activo_principal_nombre = ticker_names.get(activo_principal_ticker, activo_principal_ticker)
    peso_principal = pesos['Peso'].max(); activos_relevantes = pesos[pesos['Peso'] > 0.05]; num_activos_relevantes = len(activos_relevantes)
    texto_conclusion = f"El portafolio óptimo, con un Ratio de Sharpe de **{sharpe:.2f}**, proyecta un rendimiento anual del **{rendimiento:.2%}** y una volatilidad del **{volatilidad:.2%}**.\n\n"
    if peso_principal > 0.5:
        texto_conclusion += f"**Estrategia Enfocada:** El modelo asigna la mayor parte del capital (**{peso_principal:.2%}**) a **{activo_principal_nombre} ({activo_principal_ticker})**. Esto sugiere que este activo presenta el mejor perfil de riesgo-retorno ajustado del grupo."
    elif num_activos_relevantes > 2:
        texto_conclusion += f"**Estrategia Diversificada:** El portafolio distribuye el riesgo entre **{num_activos_relevantes} activos clave**. **{activo_principal_nombre} ({activo_principal_ticker})** lidera la asignación con un **{peso_principal:.2%}**, pero está balanceado por otros activos para mitigar la volatilidad."
    activos_descartados = pesos[pesos['Peso'] == 0].index.tolist()
    if activos_descartados:
        nombres_descartados = [f"{ticker_names.get(t, t)} ({t})" for t in activos_descartados]
        texto_conclusion += f"\n\n**Activos Excluidos:** Las empresas `{', '.join(nombres_descartados)}` no fueron incluidas, ya que su inclusión no mejoraba el rendimiento ajustado por riesgo del portafolio global en el período analizado."
    return texto_conclusion


def display_page(close_prices, valid_tickers, frecuencia, risk_free_rate, ticker_names):
    st.header("Optimización de Portafolio - Teoría de Markowitz")
    st.info(f"Cálculos realizados con una Tasa Libre de Riesgo del **{risk_free_rate:.2%}**.")

    # ... (validaciones de frecuencia, etc.) ...

    try:
        close_prices = close_prices.dropna(how='all').fillna(method='ffill')
        if len(close_prices) < 60:
             raise ValueError("Datos históricos comunes insuficientes. Intente con un período más largo.")

        mu = expected_returns.ema_historical_return(close_prices)
        S = risk_models.risk_matrix(close_prices, method='ledoit_wolf')
        
        ef_calculo = EfficientFrontier(mu, S)
        weights = ef_calculo.max_sharpe(risk_free_rate=risk_free_rate)
        cleaned_weights = ef_calculo.clean_weights()
        rendimiento, volatilidad, sharpe = ef_calculo.portfolio_performance(verbose=False, risk_free_rate=risk_free_rate)

        st.subheader("Portafolio Óptimo (Máximo Ratio de Sharpe)")
        pesos_df = pd.DataFrame.from_dict(cleaned_weights, orient='index', columns=['Peso'])
        pesos_df.index.name = 'Ticker'; pesos_df['Empresa'] = pesos_df.index.map(ticker_names); pesos_df = pesos_df[['Empresa', 'Peso']]
        
        # --- CAMBIO CLAVE 1: ALINEACIÓN HORIZONTAL ---
        # Se usan dos columnas de igual tamaño para un balance perfecto.
        col1, col2 = st.columns(2, gap="large") 
        with col1:
            st.write("**Pesos Asignados:**"); st.dataframe(pesos_df.style.format({'Peso': "{:.2%}"}), use_container_width=True)
        with col2:
            st.write("**Distribución del Portafolio:**")
            pesos_filtrados_df = pesos_df[pesos_df['Peso'] > 0.001].copy()
            if not pesos_filtrados_df.empty:
                fig_pie = px.pie(pesos_filtrados_df, values='Peso', names='Empresa', hover_data={'Empresa': False, 'Peso': ':.2%'})
                fig_pie.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05] * len(pesos_filtrados_df))
                fig_pie.update_layout(showlegend=True, legend_title_text='Activos', margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Rendimiento y Riesgo Esperado del Portafolio (Anualizado)")
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        with col_metric1: st.metric(label="Rendimiento Anual Esperado", value=f"{rendimiento:.2%}")
        with col_metric2: st.metric(label="Volatilidad Anual (Riesgo)", value=f"{volatilidad:.2%}")
        with col_metric3: st.metric(label="Ratio de Sharpe", value=f"{sharpe:.2f}")

        st.markdown("---")
        
        # --- CAMBIO CLAVE 2 y 3: REDUCIR Y OCULTAR GRÁFICO DE FRONTERA ---
        # Se coloca toda la sección del gráfico dentro de un expander para de-enfatizarla.
        with st.expander("Ver Análisis Gráfico de la Frontera Eficiente"):
            ef_grafico = EfficientFrontier(mu, S)

            # Se reduce el tamaño del gráfico a 7x4 para hacerlo más compacto.
            fig_frontier, ax = plt.subplots(figsize=(7, 4))
            
            plotting.plot_efficient_frontier(ef_grafico, ax=ax, show_assets=True, show_tickers=True)
            ax.scatter(volatilidad, rendimiento, marker="*", s=150, c="red", label="Portafolio Óptimo")
            ax.set_title("Frontera Eficiente y CML", fontsize=12)
            ax.legend(); plt.tight_layout()
            st.pyplot(fig_frontier)
            
            st.info("""
            **Interpretación Rápida:** La **estrella roja** representa su portafolio, ubicado en el punto óptimo de la **curva azul** (la Frontera Eficiente). Este punto ofrece el máximo retorno posible para el menor riesgo asumido.
            """)
        
        st.markdown("---")
        
        # El Análisis IA ahora tiene mayor prominencia al final de la página.
        st.subheader("Análisis IA de la Estrategia")
        with st.spinner("Generando interpretación..."):
            conclusion = generar_conclusion_optimizacion(pesos_df, rendimiento, volatilidad, sharpe, ticker_names)
            st.markdown(conclusion)

    except Exception as e:
        st.error("🔴 **Error en el cálculo de la optimización.**")
        st.warning(str(e))