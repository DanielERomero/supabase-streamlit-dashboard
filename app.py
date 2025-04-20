import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
# Aunque usamos Codespaces secrets, dotenv no daña y permite usar .env si se prefiere
from dotenv import load_dotenv

# Carga variables desde .env si existe (útil para desarrollo local o alternativa)
load_dotenv()

# Configuración de Supabase (obtener desde variables de entorno - ¡prioriza secrets!)
# os.environ.get buscará las variables inyectadas por Codespaces Secrets
# o las cargadas desde .env por load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Verificar si las variables de entorno están cargadas
if not url or not key:
    st.error("Error: Las variables de entorno SUPABASE_URL y SUPABASE_KEY no están configuradas.")
    st.info("Asegúrate de haber configurado los 'Codespaces secrets' en los ajustes del repositorio de GitHub y recargado el Codespace (F1 -> Reload Window).")
    st.stop()

# Intentar crear cliente Supabase
try:
    supabase: Client = create_client(url, key)
    st.sidebar.success("Conectado a Supabase!")
except Exception as e:
    st.sidebar.error(f"Error al conectar a Supabase: {e}")
    st.stop() # Detiene la ejecución si no se puede conectar

# --- Funciones Auxiliares ---
@st.cache_data(ttl=600) # Cache para no recargar datos constantemente
def fetch_data(table_name: str):
    """Obtiene todos los datos de una tabla específica de Supabase."""
    try:
        response = supabase.table(table_name).select("*").execute()
        if hasattr(response, 'data') and response.data:
            df = pd.DataFrame(response.data)
            return df
        else:
            st.warning(f"No se encontraron datos en la tabla '{table_name}' o la respuesta no tiene el formato esperado.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al obtener datos de la tabla '{table_name}': {e}")
        return pd.DataFrame()

# --- Interfaz de Streamlit ---
st.title("📊 Dashboard Básico de Supabase (Codespaces)")

table_name = st.text_input("Nombre de la tabla en Supabase:", "compras") # CAMBIA ESTO

if table_name:
    st.header(f"Análisis de la tabla: `{table_name}`")

    data_load_state = st.text(f"Cargando datos de la tabla '{table_name}'...")
    df = fetch_data(table_name)
    data_load_state.text(f"¡Datos de '{table_name}' cargados!")

    if not df.empty:
        st.subheader("Muestra de Datos")
        st.dataframe(df.head())

        st.subheader("Estadísticas Descriptivas")
        try:
            numeric_df = df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                 st.write(numeric_df.describe())
            else:
                 st.info("No hay columnas numéricas.")

            non_numeric_df = df.select_dtypes(exclude=['number'])
            if not non_numeric_df.empty:
                 st.write(non_numeric_df.describe())
            else:
                 st.info("No hay columnas no numéricas.")

        except Exception as e:
            st.error(f"Error al calcular estadísticas: {e}")

        st.subheader("Filas Duplicadas")
        duplicates = df[df.duplicated(keep=False)]
        if not duplicates.empty:
            st.warning(f"Se encontraron {len(duplicates)} filas que tienen al menos una duplicada.")
            st.dataframe(duplicates.sort_values(by=list(duplicates.columns)))
            st.write(f"Número total de filas exactamente iguales (excluyendo la primera ocurrencia): {df.duplicated().sum()}")
        else:
            st.success("¡No se encontraron filas duplicadas!")

        st.subheader("Buscar duplicados por columnas específicas (Opcional)")
        all_columns = df.columns.tolist()
        selected_columns = st.multiselect("Selecciona columnas para verificar duplicados:", all_columns)
        if selected_columns:
            duplicates_subset = df[df.duplicated(subset=selected_columns, keep=False)]
            if not duplicates_subset.empty:
                st.warning(f"Se encontraron {len(duplicates_subset)} filas duplicadas basadas en: {', '.join(selected_columns)}")
                st.dataframe(duplicates_subset.sort_values(by=selected_columns))
            else:
                st.success(f"No se encontraron filas duplicadas basadas en las columnas seleccionadas.")
    else:
        st.warning(f"No se pudieron cargar datos de la tabla '{table_name}' o está vacía.")
else:
    st.info("Por favor, ingresa el nombre de una tabla para comenzar.")