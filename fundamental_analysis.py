# fundamental_analysis.py (Versión con Mejoras de Estilo en Contenido y Documentación Completa)

# --- SECCIÓN 0: IMPORTACIONES ---
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import io

# --- SECCIÓN 1: DICCIONARIOS DE CONFIGURACIÓN ---
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

# --- SECCIÓN 2: LÓGICA DE ANÁLISIS (IA NARRATIVA) ---
def analizar_ratio_por_rango(ratio_name, valor):
    if pd.isna(valor): return f"**{ratio_name}:** No disponible."
    s_valor = f"{valor:.0%}" if ratio_name in ['ROE', 'Razón de Pago de Dividendos (Payout)'] else f"{valor:,.2f}x"
    if ratio_name == 'Razón Deuda a Patrimonio (D/E)':
        if valor <= 0.3: return f"🟢 **Bajo Apalancamiento (D/E = {s_valor}):** Estructura de capital muy conservadora."
        elif 0.3 < valor <= 1.5: return f"✅ **Apalancamiento Óptimo (D/E = {s_valor}):** Equilibrio saludable entre deuda y capital."
        elif 1.5 < valor <= 2.0: return f"🟡 **Apalancamiento Elevado (D/E = {s_valor}):** Requiere vigilancia."
        else: return f"🔴 **Alto Riesgo de Apalancamiento (D/E = {s_valor}):** Nivel de deuda muy alto."
    elif ratio_name == 'ROE':
        adv = "\n\n  *Nota: Un ROE > 30% puede ser señal de apalancamiento excesivo.*" if valor > 0.30 else ""
        if valor > 0.25: return f"🏆 **Excelente Rentabilidad (ROE = {s_valor}):** Generación de valor excepcional." + adv
        elif 0.10 <= valor <= 0.25: return f"🟢 **Rentabilidad Deseable (ROE = {s_valor}):** Empresa competitiva." + adv
        elif 0 <= valor < 0.10: return f"🟡 **Baja Rentabilidad (ROE = {s_valor}):** Retorno pobre."
        else: return f"🔴 **Rentabilidad Negativa (ROE = {s_valor}):** Destrucción de valor."
    elif ratio_name == 'Razón de Pago de Dividendos (Payout)':
        if valor > 1.0: return f"🔴 **Payout Insostenible (Payout = {s_valor}):** Paga más de lo que gana."
        elif 0.7 <= valor <= 1.0: return f"🟡 **Payout Elevado (Payout = {s_valor}):** Poco margen para reinversión."
        elif 0.4 <= valor < 0.7: return f"✅ **Payout Moderado (Payout = {s_valor}):** Balance saludable."
        elif 0 < valor < 0.4: return f"🟢 **Payout de Crecimiento (Payout = {s_valor}):** Prioriza la reinversión."
        else: return f"ℹ️ **Sin Dividendo o Payout Negativo (Payout = {s_valor}):** No paga dividendos o tuvo pérdidas."
    return None

def generar_analisis_ia_por_rangos(df_numeric):
    analisis_individuales, conclusion_general = {}, ""
    for ticker in df_numeric.columns:
        series = df_numeric[ticker]
        analisis_clave = [
            analizar_ratio_por_rango('Razón Deuda a Patrimonio (D/E)', series.get(('Solvencia', 'Razón Deuda a Patrimonio (D/E)'))),
            analizar_ratio_por_rango('ROE', series.get(('Rentabilidad', 'ROE'))),
            analizar_ratio_por_rango('Razón de Pago de Dividendos (Payout)', series.get(('Dividendos', 'Razón de Pago de Dividendos (Payout)')))
        ]
        analisis_individuales[ticker] = "\n\n".join([f"- {a}" for a in analisis_clave if a])
    if len(df_numeric.columns) > 1:
        mejor_valor = df_numeric.min(axis=1); peor_valor = df_numeric.max(axis=1)
        for ratio in HIGHER_IS_BETTER:
            if ratio in mejor_valor.index: mejor_valor.loc[ratio], peor_valor.loc[ratio] = peor_valor.loc[ratio], mejor_valor.loc[ratio]
        perfiles = {t: [] for t in df_numeric.columns}
        for (cat, ratio), best_val in mejor_valor.items():
            if pd.isna(best_val): continue
            ganadores = df_numeric.loc[(cat, ratio)][df_numeric.loc[(cat, ratio)] == best_val].index
            for ganador in ganadores: perfiles[ganador].append(cat)
        resumenes = {}
        for ticker, cats in perfiles.items():
            cats = set(cats)
            if 'Rentabilidad' in cats: resumenes[ticker] = f"**Líder en Rentabilidad:** `{ticker}` destaca por su alta eficiencia y retornos."
            elif 'Valoración' in cats: resumenes[ticker] = f"**Mejor Valoración:** `{ticker}` presenta la relación precio-valor más atractiva."
            elif 'Solvencia' in cats or 'Liquidez' in cats: resumenes[ticker] = f"**Perfil más Sólido/Seguro:** `{ticker}` opera con la estructura financiera más robusta."
        if resumenes:
            conclusion_general = "Al comparar las empresas, se observa el siguiente panorama:\n\n" + "\n".join([f"- {v}" for v in sorted(list(set(resumenes.values())))])
            conclusion_general += "\n\n**Recomendación:** La elección dependerá del perfil del inversor. Los que buscan **calidad** podrían preferir al líder en rentabilidad, mientras que los de **valor** se inclinarán por la mejor valoración. La opción más **segura** suele ser la de mayor solidez financiera."
        else: conclusion_general = "No se encontró un líder claro en las categorías principales."
    else: conclusion_general = "El análisis comparativo requiere al menos dos empresas."
    return analisis_individuales, conclusion_general

# --- SECCIÓN 3: FUNCIONES DE SOPORTE ---
def get_fundamental_data(ticker_str):
    try:
        stock = yf.Ticker(ticker_str); info = stock.info
        if not info or info.get('longName') is None: return None
        data = {"Ticker": ticker_str, "Nombre": info.get('longName')}
        for cat, rats in RATIO_MAP.items():
            for d_name, api_key in rats.items():
                if api_key == 'pegRatio': data[d_name] = info.get(api_key, info.get('trailingPegRatio', np.nan))
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
    if b_val is not None:
        b_idx = vals[vals == b_val].index
        if not b_idx.empty:
            pos = row.index.get_loc(b_idx[0])
            style[pos] = 'background-color: #3b82f6; font-weight: bold; color: white;'
    return style

def create_excel_download(df, filename):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name='Analisis_Fundamental')
    st.download_button(label="📥 Descargar Tabla como Excel", data=output.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- SECCIÓN 4: FUNCIÓN PRINCIPAL DE VISUALIZACIÓN (`display_page`) ---
def display_page(tickers_list):
    if not tickers_list:
        st.warning("Por favor, ingrese al menos un ticker válido.")
        return
    with st.spinner(f"Obteniendo y procesando datos..."):
        successful_data = [d for d in [get_fundamental_data(t) for t in tickers_list] if d is not None]
        if not successful_data:
            st.error("No se pudieron obtener datos para ninguno de los tickers seleccionados.")
            return
    df_numeric = pd.DataFrame(index=pd.MultiIndex.from_tuples([(cat, rat) for cat, rats in RATIO_MAP.items() for rat in rats.keys()], names=['Categoría', 'Ratio']))
    for data in successful_data:
        for cat, rats in RATIO_MAP.items():
            for rat_name in rats.keys():
                df_numeric.loc[(cat, rat_name), data['Ticker']] = data.get(rat_name)
    df_numeric = df_numeric.apply(pd.to_numeric, errors='coerce').dropna(how='all')
    if len(successful_data) > 1:
        st.header("Análisis Fundamental Comparativo")
        st.caption(", ".join([d['Nombre'] for d in successful_data]))
        available_categories = df_numeric.index.get_level_values('Categoría').unique()
        tab_titles = ["📊 Valoración", "🏆 Rentabilidad", "🛡️ Solvencia y Liquidez", "💰 Dividendos y Riesgo"]
        tabs = st.tabs(tab_titles)
        tab_map = {
            "📊 Valoración": ["Valoración"], "🏆 Rentabilidad": ["Rentabilidad"],
            "🛡️ Solvencia y Liquidez": ["Solvencia", "Liquidez"],
            "💰 Dividendos y Riesgo": ["Dividendos", "Riesgo (Volatilidad)"]
        }
        for i, tab in enumerate(tabs):
            with tab:
                cats_to_display = [cat for cat in tab_map[tab_titles[i]] if cat in available_categories]
                if cats_to_display:
                    df_filtered = df_numeric.loc[cats_to_display]
                    formatter = "{:.2%}" if tab_titles[i] == "🏆 Rentabilidad" else "{:.2f}"
                    st.dataframe(df_filtered.style.apply(highlight_best, axis=1).format(formatter, na_rep="N/A"), use_container_width=True)
                else:
                    st.info("No hay datos disponibles para esta categoría para los tickers seleccionados.")
        st.markdown("<small>Nota: El valor óptimo en cada fila está resaltado.</small>", unsafe_allow_html=True)
        create_excel_download(df_numeric, f"comparativa_{'_'.join(df_numeric.columns)}.xlsx")
        
        # --- CAMBIO CLAVE 1: SEPARADOR VISUAL ---
        st.markdown("---")
        
        # --- CAMBIO CLAVE 2: MEJORA DE TÍTULOS EN ANÁLISIS IA ---
        st.subheader("🤖 Análisis IA Individual")
        analisis_individuales, conclusion_general = generar_analisis_ia_por_rangos(df_numeric)
        for ticker in df_numeric.columns:
            with st.expander(f"**🧠 Análisis Detallado para {ticker}**"):
                st.markdown(analisis_individuales[ticker])
                
        # --- CAMBIO CLAVE 3: TÍTULO PROMINENTE PARA LA CONCLUSIÓN ---
        st.markdown("---")
        st.subheader("💡 Conclusión Final y Recomendación")
        st.markdown(conclusion_general)
    elif len(successful_data) == 1:
        st.info("El análisis comparativo por pestañas y la IA solo están disponibles al analizar 2 o más empresas.")