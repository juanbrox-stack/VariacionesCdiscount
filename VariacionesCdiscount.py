import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Cdiscount Variaciones - Setup", layout="wide")

# --- INTERFAZ DE AYUDA ---
st.title("📦 Generador de Variaciones (Mínimo 2 variantes)")

with st.expander("📢 Requisitos de los ficheros (Haz clic para ver)"):
    st.markdown("""
    ### 1. Catálogo Cdiscount
    Debe contener al menos:
    * **`SKU CDISCOUNT`**: El SKU de destino.
    * **`EAN`**: Para cruzar con Amazon.

    ### 2. Variaciones Amazon
    Debe contener al menos:
    * **`EAN`**: Para cruzar con el catálogo.
    * **`ASIN Padre`**: Para agrupar las familias.
    * **`Categorías: Subcategoría`**: Se usará para la columna 'Catégorie'.
    * **`Atributos de variación`**: Se usará para 'Attribut 1'.
    """)

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1:
    file_cat = st.file_uploader("1. Subir Catálogo Cdiscount", type=["csv", "xlsx"])
with col2:
    file_var = st.file_uploader("2. Subir Variaciones Amazon", type=["csv", "xlsx"])

if file_cat and file_var:
    try:
        def load_data(file):
            if file.name.endswith('.csv'):
                return pd.read_csv(file)
            return pd.read_excel(file)

        df_cat = load_data(file_cat)
        df_var = load_data(file_var)

        # Limpiar y normalizar nombres de columnas
        df_cat.columns = df_cat.columns.str.strip()
        df_var.columns = df_var.columns.str.strip()

        # Validación de existencia de columnas
        req_cat = ['EAN', 'SKU CDISCOUNT']
        req_var = ['EAN', 'ASIN Padre', 'Categorías: Subcategoría', 'Atributos de variación']
        
        if all(col in df_cat.columns for col in req_cat) and all(col in df_var.columns for col in req_var):
            
            df_cat['EAN'] = df_cat['EAN'].astype(str).str.strip()
            df_var['EAN'] = df_var['EAN'].astype(str).str.strip()

            # 1. Unir datos
            df_merged = pd.merge(
                df_var[req_var], 
                df_cat[['EAN', 'SKU CDISCOUNT']], 
                on='EAN', 
                how='inner'
            )

            # 2. Filtrar familias (Mínimo 2)
            df_merged = df_merged[df_merged.groupby('ASIN Padre')['ASIN Padre'].transform('count') > 1]
            
            if df_merged.empty:
                st.warning("⚠️ No hay productos con variaciones múltiples tras el cruce.")
            else:
                df_merged = df_merged.sort_values(by='ASIN Padre')

                # 3. Estructura final
                df_final = pd.DataFrame()
                df_final['Nom du GDV'] = df_merged['ASIN Padre']
                df_final['Sku'] = df_merged['SKU CDISCOUNT']
                df_final['Catégorie'] = df_merged['Categorías: Subcategoría']
                df_final['Attribut 1'] = df_merged['Atributos de variación']

                st.success(f"✅ ¡Éxito! {len(df_final)} filas listas para descargar.")
                st.dataframe(df_final.head(10))

                # --- Excel con Celdas Combinadas ---
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
                        if j - i > 1:
                            worksheet.merge_range(i + 1, 0, j, 0, data[i], merge_format)
                        else:
                            worksheet.write(i + 1, 0, data[i], merge_format)
                        i = j

                st.download_button(
                    label="📥 Descargar Excel de Variaciones",
                    data=output.getvalue(),
                    file_name="Cdiscount_Variaciones_Final.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("Error: Las columnas no coinciden. Revisa el apartado de 'Requisitos' arriba.")

    except Exception as e:
        st.error(f"Error inesperado: {e}")