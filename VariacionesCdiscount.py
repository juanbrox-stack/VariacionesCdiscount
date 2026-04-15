import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Cdiscount Variation Generator", layout="wide")

st.title("🚀 Generador de Variaciones Cdiscount")
st.markdown("""
Esta herramienta cruza el catálogo de Cdiscount con las variaciones de Amazon mediante el **EAN**.
""")

# Carga de archivos
col1, col2 = st.columns(2)
with col1:
    file_cat = st.file_uploader("Subir Catálogo Cdiscount (SKUs Pendientes)", type=["csv", "xlsx"])
with col2:
    file_var = st.file_uploader("Subir Variaciones Amazon (Fichero VariacionesCdiscount)", type=["csv", "xlsx"])

if file_cat and file_var:
    try:
        # Carga de datos manejando CSV o Excel
        def load_data(file):
            if file.name.endswith('.csv'):
                return pd.read_csv(file)
            return pd.read_excel(file)

        df_catalogo = load_data(file_cat)
        df_variaciones = load_data(file_var)

        # Limpieza de nombres de columnas (quitar espacios en blanco)
        df_catalogo.columns = df_catalogo.columns.str.strip()
        df_variaciones.columns = df_variaciones.columns.str.strip()

        # Verificamos que existan las columnas clave
        if 'EAN' in df_catalogo.columns and 'EAN' in df_variaciones.columns:
            
            # 1. Seleccionamos solo lo necesario de cada tabla
            # Del catálogo nos interesa el EAN y el SKU
            df_cat_min = df_catalogo[['EAN', 'SKU']].copy()
            
            # De variaciones nos interesa EAN, Atributos y Subcategoría
            # Usamos los nombres exactos de tus archivos
            df_var_min = df_variaciones[['EAN', 'Categorías: Subcategoría', 'Atributos de variación']].copy()

            # 2. Realizamos el cruce (Merge)
            # Aseguramos que el EAN sea tratado como string para evitar errores de formato
            df_cat_min['EAN'] = df_cat_min['EAN'].astype(str).str.strip()
            df_var_min['EAN'] = df_var_min['EAN'].astype(str).str.strip()

            df_merged = pd.merge(df_cat_min, df_var_min, on='EAN', how='inner')

            # 3. Construimos el DataFrame final con la estructura solicitada
            df_final = pd.DataFrame()
            df_final['Nom du GDV'] = df_merged['Categorías: Subcategoría'] # O el nombre que prefieras
            df_final['Sku'] = df_merged['SKU']
            df_final['Catégorie'] = df_merged['Categorías: Subcategoría']
            df_final['Attribut 1'] = df_merged['Atributos de variación']

            # Eliminar duplicados si existieran
            df_final = df_final.drop_duplicates()

            st.success(f"¡Cruce finalizado! Se han generado {len(df_final)} filas.")
            st.dataframe(df_final.head(10))

            # 4. Botón de descarga
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Variaciones')
            
            st.download_button(
                label="📥 Descargar Fichero Final Excel",
                data=output.getvalue(),
                file_name="Cdiscount_Variaciones_Final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No se encontró la columna 'EAN' en uno de los archivos. Revisa los encabezados.")

    except Exception as e:
        st.error(f"Ocurrió un error al procesar: {e}")

else:
    st.info("Esperando a que subas ambos archivos...")