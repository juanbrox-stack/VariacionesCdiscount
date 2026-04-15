import streamlit as st
import pandas as pd
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Generador de Variaciones Cdiscount", layout="wide")

st.title("📦 Procesador de Variaciones: Cdiscount & Amazon")
st.write("Sube los dos ficheros Excel para generar el formato final.")

# 1. Carga de archivos
col1, col2 = st.columns(2)

with col1:
    file_cdiscount = st.file_uploader("Fichero 1: Catálogo Cdiscount (Excel)", type=["xlsx"])
with col2:
    file_amazon = st.file_uploader("Fichero 2: Variaciones Amazon (Excel)", type=["xlsx"])

if file_cdiscount and file_amazon:
    try:
        # Leer los archivos
        # Asumimos que no tienen encabezados extraños y empiezan en la fila 0
        df_cdiscount = pd.read_excel(file_cdiscount)
        df_amazon = pd.read_excel(file_amazon)

        st.success("Archivos cargados correctamente.")

        # Lógica de procesamiento
        # Nota: Las columnas en Pandas empiezan en 0 (A=0, B=1, C=2, etc.)
        # Extraemos las columnas necesarias por índice para evitar errores de nombres
        
        # Fichero 1: B (EAN) es índice 1, C (SKU) es índice 2
        df_cd_clean = df_cdiscount.iloc[:, [1, 2]].copy()
        df_cd_clean.columns = ['EAN', 'Sku']

        # Fichero 2: B (EAN) es índice 1, C (Categoría) es índice 2, F (Atributos) es índice 5
        df_am_clean = df_amazon.iloc[:, [1, 2, 5]].copy()
        df_am_clean.columns = ['EAN', 'Catégorie', 'Attribut 1']

        # Cruzar los datos (Inner Join por EAN)
        df_final = pd.merge(df_cd_clean, df_am_clean, on='EAN', how='inner')

        # Añadir columna 'Nom du GDV' (puedes ajustarla según necesites)
        # Aquí la creamos vacía o basada en la categoría
        df_final['Nom du GDV'] = df_final['Catégorie'] 

        # Reordenar columnas según tu estructura
        resultado = df_final[['Nom du GDV', 'Sku', 'Catégorie', 'Attribut 1']]

        st.subheader("Vista previa del resultado:")
        st.dataframe(resultado.head())

        # 3. Exportar a Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            resultado.to_excel(writer, index=False, sheet_name='Variaciones')
        
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Descargar Excel Final",
            data=processed_data,
            file_name="variaciones_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error al procesar los archivos: {e}")
        st.info("Asegúrate de que las columnas B, C, E y F contienen los datos esperados.")
else:
    st.info("Por favor, sube ambos archivos para comenzar.")