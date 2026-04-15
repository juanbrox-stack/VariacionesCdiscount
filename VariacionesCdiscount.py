import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Agrupador de Variaciones Cdiscount", layout="wide")

st.title("📦 Generador de Variaciones por ASIN Padre")
st.write("Esta versión agrupa los resultados para que las variantes de un mismo producto aparezcan juntas.")

# Carga de archivos
col1, col2 = st.columns(2)
with col1:
    file_cat = st.file_uploader("1. Catálogo Cdiscount (SKUs Pendientes)", type=["csv", "xlsx"])
with col2:
    file_var = st.file_uploader("2. Variaciones Amazon (Fichero VariacionesCdiscount)", type=["csv", "xlsx"])

if file_cat and file_var:
    try:
        # Función para leer archivos (CSV o Excel)
        def load_data(file):
            if file.name.endswith('.csv'):
                return pd.read_csv(file)
            return pd.read_excel(file)

        df_cat = load_data(file_cat)
        df_var = load_data(file_var)

        # Limpiar nombres de columnas
        df_cat.columns = df_cat.columns.str.strip()
        df_var.columns = df_var.columns.str.strip()

        # Validación de columnas necesarias
        cols_cat_nec = ['EAN', 'SKU CDISCOUNT']
        cols_var_nec = ['EAN', 'ASIN Padre', 'Categorías: Subcategoría', 'Atributos de variación']
        
        missing_cat = [c for c in cols_cat_nec if c not in df_cat.columns]
        missing_var = [c for c in cols_var_nec if c not in df_var.columns]

        if not missing_cat and not missing_var:
            # Asegurar formato de EAN como string para el cruce
            df_cat['EAN'] = df_cat['EAN'].astype(str).str.strip()
            df_var['EAN'] = df_var['EAN'].astype(str).str.strip()

            # 1. Cruzar datos (Merge)
            # Solo traemos SKU CDISCOUNT del catálogo y lo unimos a la tabla de Amazon
            df_merged = pd.merge(
                df_var[cols_var_nec], 
                df_cat[['EAN', 'SKU CDISCOUNT']], 
                on='EAN', 
                how='inner'
            )

            # 2. Agrupación/Ordenación por ASIN Padre
            # Al ordenar por ASIN Padre, las variantes quedan juntas en el Excel
            df_merged = df_merged.sort_values(by='ASIN Padre')

            # 3. Mapeo a la estructura final solicitada
            df_final = pd.DataFrame()
            df_final['Nom du GDV'] = df_merged['Categorías: Subcategoría']
            df_final['Sku'] = df_merged['SKU CDISCOUNT']
            df_final['Catégorie'] = df_merged['Categorías: Subcategoría']
            df_final['Attribut 1'] = df_merged['Atributos de variación']

            st.success(f"✅ Se han procesado {len(df_final)} variaciones agrupadas por ASIN Padre.")
            
            # Vista previa
            st.subheader("Vista previa del fichero generado")
            st.dataframe(df_final.head(15))

            # 4. Generar Excel para descarga
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Variaciones Cdiscount')
            
            st.download_button(
                label="📥 Descargar Excel con Agrupación",
                data=output.getvalue(),
                file_name="Variaciones_Agrupadas_Cdiscount.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            if missing_cat: st.error(f"Faltan columnas en Catálogo: {missing_cat}")
            if missing_var: st.error(f"Faltan columnas en Variaciones: {missing_var}")

    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.info("Sube ambos ficheros para generar la agrupación por ASIN Padre.")