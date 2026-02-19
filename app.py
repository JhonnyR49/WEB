import sys
import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np

st.set_page_config(page_title="Dashboard de Vehículos", layout="wide")

st.title("🚗 Dashboard de Análisis de Vehículos en Venta")
st.markdown("Explora datos de anuncios de vehículos mediante visualizaciones interactivas.")

@st.cache_data
def load_data(path: str = "vehicles_us.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo {path}. Coloca `vehicles_us.csv` en el directorio del proyecto.")
        return pd.DataFrame()
    df.columns = df.columns.str.strip()
    for col in ["price", "odometer", "model_year"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

car_data = load_data()

if car_data.empty:
    st.stop()

st.sidebar.header("⚙️ Controles de Visualización")

if st.sidebar.checkbox("Mostrar datos crudos"):
    st.subheader("📄 Vista previa de los datos")
    st.dataframe(car_data.head())

numeric_cols = car_data.select_dtypes(include=[np.number]).columns.tolist()

st.sidebar.header("🔍 Filtrar datos")

price_min = int(car_data["price"].min(skipna=True))
price_max = int(car_data["price"].max(skipna=True))
price_range = st.sidebar.slider("Rango de precio:", price_min, price_max, (price_min, price_max))

if "odometer" in car_data.columns:
    od_min = int(car_data["odometer"].min(skipna=True))
    od_max = int(car_data["odometer"].max(skipna=True))
    odometer_range = st.sidebar.slider("Rango de odómetro:", od_min, od_max, (od_min, od_max))
else:
    odometer_range = None

if "model_year" in car_data.columns:
    year_min = int(car_data["model_year"].min(skipna=True))
    year_max = int(car_data["model_year"].max(skipna=True))
    year_range = st.sidebar.slider("Rango de año:", year_min, year_max, (year_min, year_max))
else:
    year_range = None

if "condition" in car_data.columns:
    condition_choices = sorted(car_data["condition"].dropna().unique())
    selected_conditions = st.sidebar.multiselect("Condición:", condition_choices, default=condition_choices)
else:
    selected_conditions = None

filtered_data = car_data.copy()
filtered_data = filtered_data[
    (filtered_data["price"] >= price_range[0]) & 
    (filtered_data["price"] <= price_range[1])
]

if odometer_range is not None:
    filtered_data = filtered_data[
        (filtered_data["odometer"] >= odometer_range[0]) & 
        (filtered_data["odometer"] <= odometer_range[1])
    ]

if year_range is not None:
    filtered_data = filtered_data[
        (filtered_data["model_year"] >= year_range[0]) & 
        (filtered_data["model_year"] <= year_range[1])
    ]

if selected_conditions:
    filtered_data = filtered_data[filtered_data["condition"].isin(selected_conditions)]

st.sidebar.write(f"📊 Vehículos filtrados: {len(filtered_data)}")

csv_bytes = filtered_data.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("📥 Descargar CSV filtrado", data=csv_bytes, file_name="vehicles_filtered.csv")

st.header("📊 Histogramas")

build_histogram = st.checkbox('Construir histograma del odómetro')

if build_histogram and "odometer" in filtered_data.columns:
    st.write('Construyendo histograma para la columna odómetro')
    fig_odometer = px.histogram(filtered_data, x="odometer", nbins=50,
                               title="Distribución del Odómetro",
                               labels={'odometer': 'Kilometraje', 'count': 'Cantidad'})
    st.plotly_chart(fig_odometer, use_container_width=True)

st.subheader("Histograma personalizado")
if numeric_cols:
    hist_col = st.selectbox(
        "Selecciona una columna para el histograma:",
        numeric_cols,
        index=numeric_cols.index("odometer") if "odometer" in numeric_cols else 0
    )
    nbins = st.slider("Número de bins:", 10, 200, 50)
    
    if st.button("Generar histograma", key="hist_btn"):
        fig = px.histogram(filtered_data, x=hist_col, nbins=nbins,
                          title=f'Distribución de {hist_col}')
        st.plotly_chart(fig, use_container_width=True)

st.header("📈 Gráficos de Dispersión")

st.subheader("Relación Odómetro vs Precio")
if "odometer" in filtered_data.columns and st.button("Generar gráfico de dispersión básico", key="scatter_basic"):
    fig_scatter = px.scatter(filtered_data, x="odometer", y="price",
                            title="Odómetro vs Precio", opacity=0.6,
                            labels={'odometer': 'Kilometraje', 'price': 'Precio ($)'})
    st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("Gráfico de dispersión personalizado")
if len(numeric_cols) >= 2:
    x_col = st.selectbox(
        "Eje X:",
        numeric_cols,
        index=numeric_cols.index("odometer") if "odometer" in numeric_cols else 0,
        key="x_col"
    )
    y_col = st.selectbox(
        "Eje Y:",
        numeric_cols,
        index=numeric_cols.index("price") if "price" in numeric_cols else 1,
        key="y_col"
    )
    
    categorical_cols = car_data.select_dtypes(include=[object]).columns.tolist()
    color_col = st.selectbox("Color por (opcional):", [None] + categorical_cols, index=0)
    
    if st.button("Generar gráfico de dispersión personalizado", key="scatter_custom"):
        fig_custom = px.scatter(filtered_data, x=x_col, y=y_col, 
                               color=color_col if color_col else None,
                               opacity=0.6, title=f'{x_col} vs {y_col}')
        st.plotly_chart(fig_custom, use_container_width=True)

st.header("📌 Vehículos por Condición")
if "condition" in car_data.columns:
    show_condition = st.checkbox("Mostrar gráfico de barras de condición")
    if show_condition:
        condition_counts = filtered_data["condition"].value_counts().reset_index()
        condition_counts.columns = ["condition", "count"]
        fig_condition = px.bar(condition_counts, x="condition", y="count",
                              title="Cantidad de Vehículos por Condición",
                              color="condition")
        st.plotly_chart(fig_condition, use_container_width=True)

if st.sidebar.checkbox("Mostrar estadísticas descriptivas"):
    st.sidebar.subheader("📊 Estadísticas de precio")
    st.sidebar.write(filtered_data["price"].describe())
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Precio promedio", f"${filtered_data['price'].mean():,.0f}")
    with col2:
        st.metric("Mediana", f"${filtered_data['price'].median():,.0f}")

st.markdown("---")
st.markdown("Dashboard creado con Streamlit, Plotly Express, Pandas y NumPy — incluye workaround temporal para protobuf.")