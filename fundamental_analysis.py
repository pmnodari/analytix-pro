# fundamental_analysis.py (Versión Final con Análisis por Rangos y Narrativa Mejorada)

import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import io

# --- CONFIGURACIÓN DE RATIOS Y REGLAS (sin cambios) ---
RATIO_MAP = {
    "Valoración": {"P/E": "trailingPE", "PEG (esperado 5 años)": "pegRatio", "P/S": "priceToSalesTrailing12Months", "P/B": "priceToBook", "EV/Revenue": "enterpriseToRevenue", "EV/EBITDA": "enterpriseToEbitda"},
    "Rentabilidad": {"ROA": "returnOnAssets", "ROE": "returnOnEquity", "Margen de Utilidad": "profitMargins"},
    "Solvencia": {"Razón Deuda a Patrimonio (D/E)": "debtToEquity", "Cobertura de Intereses": "interestCoverage"},
    "Liquidez": {"Razón Corriente": "currentRatio", "Prueba Ácida": "quickRatio"},
    "Dividendos": {"Rendimiento del Dividendo (Yield)": "dividendYield", "Razón de Pago de Dividendos (Payout)": "payoutRatio"},
    "Riesgo (Volatilidad)": {"Beta (5 años, mensual)": "beta"}
}
LOWER_IS_BETTER = {"P/E", "PEG (esperado 5 años)", "P/S", "P/B", "EV/Revenue", "EV/EBITDA", "Razón Deuda a Patrimonio (D/E)", "Beta (5 años, mensual)"}
HIGHER_IS_BETTER = {"ROA", "ROE", "Margen de Utilidad", "Cobertura de Intereses", "Razón Corriente", "Prueba Ácida", "Rendimiento del Dividendo (Yield)"}


# --- NUEVA LÓGICA: ANÁLISIS IA POR RANGOS ---

def analizar_ratio_por_rango(ratio_name, valor):
    """
    Analiza un ratio específico según los rangos y criterios definidos por el usuario.
    Devuelve un string formateado con el análisis.
    """
    if pd.isna(valor):
        return f"**{ratio_name}:** No disponible."

    # Formatear el valor para mostrarlo en el texto
    s_valor = f"{valor:.0%}" if ratio_name == 'ROE' or ratio_name == 'Razón de Pago de Dividendos (Payout)' else f"{valor:,.2f}x"
    
    if ratio_name == 'Razón Deuda a Patrimonio (D/E)':
        if valor <= 0.3:
            return f"🟢 **Bajo Apalancamiento (D/E = {s_valor}):** Estructura de capital muy conservadora, común en sectores estables. Riesgo financiero mínimo."
        elif 0.3 < valor <= 1.5:
            return f"✅ **Apalancamiento Óptimo (D/E = {s_valor}):** Rango saludable que muestra un buen equilibrio entre financiación con deuda y capital propio."
        elif 1.5 < valor <= 2.0:
            return f"🟡 **Apalancamiento Elevado (D/E = {s_valor}):** Requiere vigilancia. La deuda es considerable y podría ser un riesgo si las ganancias caen."
        else: # valor > 2.0
            return f"🔴 **Alto Riesgo de Apalancamiento (D/E = {s_valor}):** Nivel de deuda muy alto que puede dificultar el acceso a nuevo financiamiento. Común en utilities, pero peligroso en otros sectores."

    elif ratio_name == 'ROE':
        advertencia = ""
        if valor > 0.30: # Advertencia por ROE excesivo
            advertencia = "\n\n  *Nota: Un ROE tan alto puede ser señal de apalancamiento excesivo más que de eficiencia pura.*"
        
        if valor > 0.25:
            return f"🏆 **Excelente Rentabilidad (ROE = {s_valor}):** Generación de valor excepcional para el accionista, típico de líderes de mercado." + advertencia
        elif 0.10 <= valor <= 0.25:
            return f"🟢 **Rentabilidad Deseable (ROE = {s_valor}):** La empresa es competitiva y está bien gestionada, generando retornos sólidos." + advertencia
        elif 0 <= valor < 0.10:
            return f"🟡 **Baja Rentabilidad (ROE = {s_valor}):** El retorno es pobre y podría no cubrir el costo de capital, indicando ineficiencia o un sector difícil."
        else: # valor < 0
            return f"🔴 **Rentabilidad Negativa (ROE = {s_valor}):** La empresa está destruyendo valor para el accionista."

    elif ratio_name == 'Razón de Pago de Dividendos (Payout)':
        # Excepción para payout > 100%
        if valor > 1.0:
            return f"🔴 **Payout Insostenible (Payout = {s_valor}):** La empresa paga más en dividendos de lo que gana, financiándolo con deuda o reservas. No es viable a largo plazo."
        elif 0.7 <= valor <= 1.0:
            return f"🟡 **Payout Elevado (Payout = {s_valor}):** Proporciona un alto rendimiento al inversor, pero deja poco margen para la reinversión y el crecimiento. Común en sectores maduros como utilities o REITs."
        elif 0.4 <= valor < 0.7:
            return f"✅ **Payout Moderado (Payout = {s_valor}):** Representa un balance saludable entre recompensar a los accionistas y reinvertir para el crecimiento futuro."
        elif 0 < valor < 0.4:
            return f"🟢 **Payout de Crecimiento (Payout = {s_valor}):** La empresa prioriza la reinversión de sus ganancias para impulsar el crecimiento futuro, típico de empresas tecnológicas o en expansión."
        else: # valor <= 0
            return f"ℹ️ **Sin Dividendo o Payout Negativo (Payout = {s_valor}):** La empresa no paga dividendos, reinvierte todas sus ganancias o tuvo pérdidas."
    
    return None

def generar_analisis_ia_por_rangos(df_numeric):
    """Orquesta el análisis completo: individual por rangos y luego comparativo."""
    
    # 1. Análisis Individual para cada empresa
    analisis_individuales = {}
    for ticker in df_numeric.columns:
        series = df_numeric[ticker]
        analisis_clave = []
        
        # Analizar los 3 ratios clave con la nueva lógica por rangos
        analisis_clave.append(analizar_ratio_por_rango('Razón Deuda a Patrimonio (D/E)', series.get(('Solvencia', 'Razón Deuda a Patrimonio (D/E)'))))
        analisis_clave.append(analizar_ratio_por_rango('ROE', series.get(('Rentabilidad', 'ROE'))))
        analisis_clave.append(analizar_ratio_por_rango('Razón de Pago de Dividendos (Payout)', series.get(('Dividendos', 'Razón de Pago de Dividendos (Payout)'))))
        
        # Filtrar resultados nulos si un ratio no fue analizado
        analisis_clave = [a for a in analisis_clave if a is not None]
        
        texto = "#### Análisis Intrínseco de Ratios Clave\n\n"
        texto += "\n\n".join([f"- {a}" for a in analisis_clave])
        analisis_individuales[ticker] = texto

    # 2. Análisis Comparativo Global (sin cambios, sigue siendo útil)
    conclusion_general = "#### Análisis Comparativo y Conclusión Final\n\n"
    if len(df_numeric.columns) > 1:
        mejor_valor = df_numeric.min(axis=1); peor_valor = df_numeric.max(axis=1)
        for ratio in HIGHER_IS_BETTER:
            if ratio in mejor_valor.index:
                mejor_valor.loc[ratio], peor_valor.loc[ratio] = peor_valor.loc[ratio], mejor_valor.loc[ratio]

        perfiles = {}
        for (cat, ratio), best_val in mejor_valor.items():
            if pd.isna(best_val): continue
            ganadores = df_numeric.loc[(cat, ratio)][df_numeric.loc[(cat, ratio)] == best_val].index
            for ganador in ganadores:
                if ganador not in perfiles: perfiles[ganador] = []
                # Solo nos interesan las categorías principales para el resumen
                if cat in ['Valoración', 'Rentabilidad', 'Solvencia', 'Liquidez']:
                    perfiles[ganador].append(cat) 

        resumenes = {}
        for ticker, cats in perfiles.items():
            cats = set(cats) # Eliminar duplicados
            if 'Rentabilidad' in cats: resumenes[ticker] = f"**Líder en Rentabilidad:** `{ticker}` destaca por su alta eficiencia y retornos."
            elif 'Valoración' in cats: resumenes[ticker] = f"**Mejor Valoración:** `{ticker}` presenta la relación precio-valor más atractiva del grupo."
            elif 'Solvencia' in cats or 'Liquidez' in cats: resumenes[ticker] = f"**Perfil más Sólido/Seguro:** `{ticker}` opera con la estructura financiera más robusta."

        if resumenes:
            conclusion_general += "Al comparar las empresas, se observa el siguiente panorama:\n\n" + "\n".join([f"- {v}" for v in sorted(list(set(resumenes.values())))])
            conclusion_general += "\n\n**Recomendación:** La elección dependerá del perfil del inversor. Aquellos que buscan **calidad y eficiencia** podrían preferir al líder en rentabilidad, mientras que los inversores de **valor** se inclinarán por la empresa con la mejor valoración. La opción más **segura** suele ser la de mayor solidez financiera."
        else:
            conclusion_general += "No se encontró un líder claro en las categorías principales dentro del grupo analizado."
    else:
        conclusion_general += "El análisis comparativo requiere al menos dos empresas."
        
    return analisis_individuales, conclusion_general


# --- FUNCIONES DE OBTENCIÓN DE DATOS Y VISUALIZACIÓN (sin cambios) ---
def get_fundamental_data(ticker_str):
    try:
        stock = yf.Ticker(ticker_str); info = stock.info
        if not info or info.get('longName') is None: return None
        data = {"Ticker": ticker_str, "Nombre": info.get('longName')}
        for cat, rats in RATIO_MAP.items():
            for d_name, api_key in rats.items():
                if api_key == 'pegRatio': data[d_name] = info.get('pegRatio', info.get('trailingPegRatio', np.nan))
                elif api_key == 'interestCoverage':
                    try:
                        fin = stock.financials; ebit = fin.loc['Ebit'].iloc[0]; ie = fin.loc['Interest Expense'].iloc[0]
                        data[d_name] = abs(ebit / ie) if pd.notna(ebit) and pd.notna(ie) and ie != 0 else np.nan
                    except (KeyError, IndexError): data[d_name] = np.nan
                else: data[d_name] = info.get(api_key, np.nan)
        return data
    except Exception: return None

def highlight_best(row):
    style = [''] * len(row)
    r_name = row.name[1]; vals = row.dropna().astype(float)
    if vals.empty: return style
    b_val = vals.min() if r_name in LOWER_IS_BETTER else vals.max() if r_name in HIGHER_IS_BETTER else None
    if b_val is None: return style
    b_idx = vals[vals == b_val].index
    if not b_idx.empty:
        pos = row.index.get_loc(b_idx[0])
        style[pos] = 'background-color: #a8e6cf; font-weight: bold; color: black;'
    return style

def create_excel_download(df, filename):
    output = io.BytesIO();
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=True, sheet_name='Analisis_Fundamental')
        st.download_button(label="📥 Descargar Tabla como Excel", data=output.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception: pass

def display_page(tickers_list):
    if not tickers_list: st.warning("Por favor, ingrese al menos un ticker válido."); return
    with st.spinner(f"Obteniendo y procesando datos..."):
        successful_data = [d for d in [get_fundamental_data(t) for t in tickers_list] if d is not None]
        if not successful_data: st.error("No se pudieron obtener datos para ninguno de los tickers seleccionados."); return

    df_numeric = pd.DataFrame(index=pd.MultiIndex.from_tuples([(cat, rat) for cat, rats in RATIO_MAP.items() for rat in rats.keys()], names=['Categoría', 'Ratio']))
    for data in successful_data:
        for cat, rats in RATIO_MAP.items():
            for rat_name in rats.keys():
                df_numeric.loc[(cat, rat_name), data['Ticker']] = data.get(rat_name)
    df_numeric = df_numeric.apply(pd.to_numeric, errors='coerce')
    
    if len(successful_data) > 1:
        st.header("Análisis Fundamental Comparativo")
        st.caption(", ".join([d['Nombre'] for d in successful_data]))
        st.dataframe(df_numeric.style.apply(highlight_best, axis=1).format("{:.2f}", na_rep="N/A"), use_container_width=True)
        st.markdown("<small>Nota: El valor óptimo en cada fila está resaltado.</small>", unsafe_allow_html=True)
        create_excel_download(df_numeric, f"comparativa_{'_'.join(df_numeric.columns)}.xlsx")
        
        st.subheader("Análisis IA")
        with st.spinner("Generando análisis por rangos..."):
            analisis_individuales, conclusion_general = generar_analisis_ia_por_rangos(df_numeric)
            for ticker in df_numeric.columns:
                with st.expander(f"**Análisis Detallado para {ticker}**"):
                    st.markdown(analisis_individuales[ticker])
            st.markdown("---"); st.markdown(conclusion_general)
    elif len(successful_data) == 1:
        st.info("El análisis por rangos y comparativo solo está disponible al analizar 2 o más empresas.")