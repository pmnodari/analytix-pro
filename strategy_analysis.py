# strategy_analysis.py (Versión FINAL con la Narrativa del Backtesting Restaurada)

# --- SECCIÓN 0: IMPORTACIONES ---
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import bt
import matplotlib.pyplot as plt

# --- SECCIÓN 1: ANÁLISIS ESTRATÉGICO (SECTORES) ---
@st.cache_data
def get_sector_data(tickers):
    sectors = {}
    for ticker in tickers:
        try:
            sectors[ticker] = yf.Ticker(ticker).info.get('sector', 'Desconocido')
        except Exception:
            sectors[ticker] = 'Desconocido'
    return sectors

def display_sector_analysis(weights, tickers):
    st.subheader("🔬 Acto I: El ADN del Portafolio")
    sectors = get_sector_data(tickers)
    df_sectors = pd.DataFrame.from_dict(sectors, orient='index', columns=['Sector'])
    df_weights = pd.DataFrame.from_dict(weights, orient='index', columns=['Peso'])
    df_portfolio = df_weights.join(df_sectors)
    sector_allocation = df_portfolio.groupby('Sector')['Peso'].sum().reset_index()
    sector_allocation = sector_allocation[sector_allocation['Peso'] > 0.001]
    col1, col2 = st.columns([1, 1.5], gap="large")
    with col1:
        st.write("**Composición Sectorial:**")
        fig = px.pie(sector_allocation, values='Peso', names='Sector', title='Distribución de Pesos por Sector', color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05]*len(sector_allocation))
        fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10), title_x=0.5)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.write("**Análisis IA de la Composición:**")
        sector_allocation = sector_allocation.sort_values(by='Peso', ascending=False)
        if not sector_allocation.empty:
            lider = sector_allocation.iloc[0]
            narrativa = f"Su portafolio muestra una estrategia con una asignación principal en el sector **{lider['Sector']}**, que representa un **{lider['Peso']:.1%}** del total. "
            if lider['Peso'] > 0.5: narrativa += "Esta es una **alta concentración**, que puede generar mayores retornos si el sector tiene un buen desempeño, pero también incrementa el riesgo específico del sector. "
            elif lider['Peso'] > 0.3: narrativa += "Esta es una **concentración significativa**, indicando una fuerte convicción en el potencial de este sector. "
            if len(sector_allocation) > 2:
                secundario = sector_allocation.iloc[1]
                narrativa += f"La exposición se diversifica con una asignación del **{secundario['Peso']:.1%}** al sector **{secundario['Sector']}**, que actúa como un contrapeso y ayuda a mitigar la volatilidad."
            elif len(sector_allocation) == 2:
                secundario = sector_allocation.iloc[1]
                narrativa += f"El resto del portafolio se asigna al sector **{secundario['Sector']}** ({secundario['Peso']:.1%}), creando un portafolio enfocado en dos áreas principales."
            st.markdown(f'<div style="font-size: 16px; text-align: justify;">{narrativa}</div>', unsafe_allow_html=True)
        else:
            st.info("No hay asignaciones sectoriales para mostrar.")

# --- SECCIÓN 2: SIMULACIÓN HISTÓRICA (BACKTESTING CON `bt`) ---
def run_backtest_bt(close_prices, weights):
    strategy = bt.Strategy('RebalanceoMensual', [
        bt.algos.RunMonthly(),
        bt.algos.SelectAll(),
        bt.algos.WeighSpecified(**weights),
        bt.algos.Rebalance()
    ])
    backtest = bt.Backtest(strategy, close_prices, initial_capital=10000.0)
    results = bt.run(backtest)
    return results

def display_backtesting_analysis(all_prices, weights):
    st.subheader("🎭 Acto II: El Viaje en el Tiempo (Backtesting)")
    with st.spinner("Ejecutando simulación histórica... Esto puede tardar unos segundos..."):
        close_prices = all_prices['Close'].dropna()
        results = run_backtest_bt(close_prices, weights)
        stats = results.stats
        strategy_name = stats.columns[0]
        
        st.write("**Métricas Clave de la Simulación:**")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Retorno Total [%]", f"{stats.loc['total_return', strategy_name] * 100:.2f}%")
        col2.metric("Volatilidad Anual [%]", f"{stats.loc['monthly_vol', strategy_name] * (12**0.5) * 100:.2f}%")
        col3.metric("Max. Drawdown [%]", f"{stats.loc['max_drawdown', strategy_name] * 100:.2f}%", delta_color="inverse")
        col4.metric("Ratio de Sharpe Anual", f"{stats.loc['monthly_sharpe', strategy_name] * (12**0.5):.2f}")
        
        # --- INICIO DEL CAMBIO: RESTAURACIÓN DE LA NARRATIVA ---
        
        # 1. Se extraen los datos necesarios para la narrativa desde el DataFrame de estadísticas.
        retorno_total = stats.loc['total_return', strategy_name]
        max_drawdown = stats.loc['max_drawdown', strategy_name]
        capital_inicial = 10000
        valor_final = capital_inicial * (1 + retorno_total)
        
        # 2. Se construye el texto principal que traduce el retorno a dinero.
        texto_principal = f"Si hubieras invertido **${capital_inicial:,.0f}** en esta estrategia, tu capital se habría convertido en **${valor_final:,.2f}**, obteniendo un retorno total del **{retorno_total:.2%}**."
        
        # 3. Se construye un texto contextual sobre el riesgo, adaptado al nivel de Max Drawdown.
        if max_drawdown > -0.10: # Caída menor al 10%
            texto_riesgo = f"El riesgo asumido fue muy bajo, con una caída máxima desde el pico de solo un **{max_drawdown:.2%}**."
        elif max_drawdown > -0.25: # Caída entre 10% y 25%
            texto_riesgo = f"Es importante notar que en el camino, tu portafolio habría experimentado una caída máxima desde su punto más alto de un **{max_drawdown:.2%}**, lo cual se considera un nivel de riesgo moderado."
        else: # Caída mayor al 25%
            texto_riesgo = f"Esta estrategia no estuvo exenta de riesgo. En su peor momento, el portafolio llegó a caer un **{max_drawdown:.2%}** desde su punto más alto, lo que representa un nivel de riesgo significativo que el inversor debe estar dispuesto a tolerar."
        
        # 4. Se muestra la narrativa en una caja de información personalizada usando HTML/CSS.
        st.markdown(f"""
        <div style="background-color: #1a202c; border-left: 5px solid #3b82f6; padding: 15px; border-radius: 5px; margin: 20px 0px;">
            <p style="margin-bottom: 10px; font-size: 16px;">{texto_principal}</p>
            <p style="margin-bottom: 0; font-size: 16px;">{texto_riesgo}</p>
        </div>
        """, unsafe_allow_html=True)
        # --- FIN DEL CAMBIO ---

        st.write("**Gráfico de Crecimiento del Capital:**")
        plt.rcParams.update({'font.size': 10, 'figure.figsize': (12, 6)})
        fig = results.plot()
        fig.grid(False)
        st.pyplot(plt.gcf())
        plt.clf()

# --- SECCIÓN 3: FUNCIÓN PRINCIPAL DE VISUALIZACIÓN ---
def display_page(opt_results):
    st.header("Análisis y Backtesting de Estrategia")
    weights = opt_results['weights']
    tickers = opt_results['valid_tickers']
    all_prices = opt_results['all_prices']
    
    display_sector_analysis(weights, tickers)
    st.markdown("---")
    
    try:
        display_backtesting_analysis(all_prices, weights)
    except Exception as e:
        st.error("🔴 Ocurrió un error durante la simulación de backtesting.")
        st.warning("Esto puede suceder si el período de tiempo es muy corto o si no hay suficientes datos históricos para los activos seleccionados.")
        st.code(f"Detalle del error: {e}")