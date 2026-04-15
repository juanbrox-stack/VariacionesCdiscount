import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Cdiscount Variaciones - Solo Familias", layout="wide")

st.title("📦 Generador de Variaciones (Mínimo 2 variantes)")
st.markdown("""
Esta herramienta solo incluirá en el Excel final aquellos productos que tengan **al menos 2 variaciones** bajo el mismo ASIN Padre.
""")

col1, col2 = st.columns(2)
with col1:
    file_cat = st.file_uploader("1. Catálogo Cdiscount", type=["csv", "xlsx"])
with col2:
    file_var = st.file_uploader("2. Variaciones Amazon", type=["csv", "xlsx"])

if file_cat and file_var:
    try:
        def load_data(file):
            if file.name.endswith('.csv'):
                return pd.read_csv(file)
            return pd.read_excel(file)

        df_cat = load_data(file_cat)
        df_var = load_data(file_var)

        # Limpiar y preparar
        df_cat.columns = df_cat.columns.str.strip()
        df_var.columns = df_var.columns.str.strip()
        df_cat['EAN'] = df_cat['EAN'].astype(str).str.strip()
        df_var['EAN'] = df_var['EAN'].astype(str).str.strip()

        # 1. Unir datos
        df_merged = pd.merge(
            df_var[['EAN', 'ASIN Padre', 'Categorías: Subcategoría', 'Atributos de variación']], 
            df_cat[['EAN', 'SKU CDISCOUNT']], 
            on='EAN', 
            how='inner'
        )

        # --- NUEVO PASO: Filtrar por cantidad de variaciones ---
        # Contamos cuántas filas hay por cada ASIN Padre y filtramos las que tengan > 1
        df_merged = df_merged[df_merged.groupby('ASIN Padre')['ASIN Padre'].transform('count') > 1]
        
        if df_merged.empty:
            st.warning("⚠️ No se encontraron productos con 2 o más variaciones tras el cruce.")
        else:
            # Ordenar por ASIN Padre
            df_merged = df_merged.sort_values(by='ASIN Padre')

            # Estructura final
            df_final = pd.DataFrame()
            df_final['Nom du GDV'] = df_merged['ASIN Padre']
            df_final['Sku'] = df_merged['SKU CDISCOUNT']
            df_final['Catégorie'] = df_merged['Categorías: Subcategoría']
            df_final['Attribut 1'] = df_merged['Atributos de variación']

            st.success(f"✅ Se han generado {len(df_final)} filas pertenecientes a familias de productos.")
            st.dataframe(df_final.head(10))

            # --- Lógica de Excel con Celdas Combinadas ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Variaciones')
                
                workbook  = writer.book
                worksheet = writer.sheets['Variaciones']
                merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})

                data = df_final['Nom du GDV'].tolist()
                i = 0
                while i < len(data):
                    j = i
                    while j < len(data) and data[j] == data[i]:
                        j += 1
                    # Al haber filtrado antes, aquí j-i siempre debería ser > 1
                    if j - i > 1:
                        worksheet.merge_range(i + 1, 0, j, 0, data[i], merge_format)
                    else:
                        worksheet.write(i + 1, 0, data[i], merge_format)
                    i = j

            st.download_button(
                label="📥 Descargar Excel de Variaciones",
                data=output.getvalue(),
                file_name="Cdiscount_Familias_Variaciones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Sube los archivos para procesar solo las familias con múltiples variantes.")