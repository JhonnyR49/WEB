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
    
    if "model" in df.columns:
        df["manufacturer"] = df["model"].str.split().str[0]
    return df

car_data = load_data()

if car_data.empty:
    st.stop()

st.sidebar.header("⚙️ Controles de Visualización")

if st.sidebar.checkbox("Mostrar datos crudos"):
    st.subheader("📄 Vista previa de los datos")
    st.dataframe(car_data.head())

numeric_cols = car_data.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = car_data.select_dtypes(include=[object]).columns.tolist()

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

if "manufacturer" in car_data.columns:
    manufacturer_choices = sorted(car_data["manufacturer"].dropna().unique())
    selected_manufacturers = st.sidebar.multiselect("Fabricante:", manufacturer_choices, default=None)
else:
    selected_manufacturers = None

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

if selected_manufacturers:
    filtered_data = filtered_data[filtered_data["manufacturer"].isin(selected_manufacturers)]

st.sidebar.write(f"📊 Vehículos filtrados: {len(filtered_data)}")

csv_bytes = filtered_data.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("📥 Descargar CSV filtrado", data=csv_bytes, file_name="vehicles_filtered.csv")

st.header("📋 Data Viewer")
if st.checkbox("Mostrar Data Viewer completo"):
    st.subheader("Datos filtrados")
    st.dataframe(filtered_data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total vehículos", len(filtered_data))
    with col2:
        st.metric("Precio promedio", f"${filtered_data['price'].mean():,.0f}")
    with col3:
        st.metric("Año promedio", f"{filtered_data['model_year'].mean():.0f}" if "model_year" in filtered_data.columns else "N/A")

st.header("🏭 Vehículos por Tipo y Fabricante")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cantidad por Tipo de Vehículo")
    if "type" in filtered_data.columns:
        type_counts = filtered_data["type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig_type = px.bar(type_counts, x="type", y="count", 
                         title="Vehículos por Tipo",
                         color="type", color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_type, use_container_width=True)

with col2:
    st.subheader("Cantidad por Fabricante")
    if "manufacturer" in filtered_data.columns:
        manufacturer_counts = filtered_data["manufacturer"].value_counts().reset_index().head(15)
        manufacturer_counts.columns = ["manufacturer", "count"]
        fig_manufacturer = px.bar(manufacturer_counts, x="manufacturer", y="count",
                                 title="Top 15 Fabricantes",
                                 color="manufacturer", color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig_manufacturer, use_container_width=True)

st.header("📅 Condición vs Año del Modelo")

if "condition" in filtered_data.columns and "model_year" in filtered_data.columns:
    condition_year_data = filtered_data.dropna(subset=["condition", "model_year"])
    
    viz_type = st.radio("Tipo de visualización:", 
                       ["Histograma apilado", "Gráfico de dispersión", "Box plot"],
                       horizontal=True)
    
    if viz_type == "Histograma apilado":
        fig_condition_year = px.histogram(condition_year_data, x="model_year", color="condition",
                                         title="Distribución de Años por Condición",
                                         labels={'model_year': 'Año del Modelo', 'count': 'Cantidad'},
                                         barmode="stack", nbins=30)
        st.plotly_chart(fig_condition_year, use_container_width=True)
        
    elif viz_type == "Gráfico de dispersión":
        fig_condition_year = px.scatter(condition_year_data, x="model_year", y="condition",
                                       title="Relación Condición vs Año",
                                       labels={'model_year': 'Año del Modelo', 'condition': 'Condición'},
                                       color="condition", opacity=0.6)
        st.plotly_chart(fig_condition_year, use_container_width=True)
        
    else:
        fig_condition_year = px.box(condition_year_data, x="condition", y="model_year",
                                   title="Distribución de Años por Condición",
                                   labels={'condition': 'Condición', 'model_year': 'Año del Modelo'},
                                   color="condition")
        st.plotly_chart(fig_condition_year, use_container_width=True)
else:
    st.warning("No hay datos de condición o año del modelo para mostrar.")

st.header("💰 Comparación de Precios entre Fabricantes")

if "manufacturer" in filtered_data.columns:
    manufacturer_price_data = filtered_data.dropna(subset=["manufacturer", "price"])
    manufacturer_counts = manufacturer_price_data["manufacturer"].value_counts()
    top_manufacturers = manufacturer_counts[manufacturer_counts > 10].index.tolist()
    
    if len(top_manufacturers) > 0:
        manufacturer_price_data = manufacturer_price_data[manufacturer_price_data["manufacturer"].isin(top_manufacturers)]
        
        viz_type_price = st.radio("Tipo de gráfico:", 
                                 ["Box plot", "Histograma", "Violín"],
                                 horizontal=True, key="price_viz")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Opciones")
            if viz_type_price == "Histograma":
                nbins_price = st.slider("Número de bins:", 10, 100, 30, key="nbins_price")
                log_scale = st.checkbox("Escala logarítmica en precio")
            else:
                nbins_price = 30
                log_scale = False
            
            show_all = st.checkbox("Mostrar todos los fabricantes", value=False)
            if not show_all:
                selected_manufacturers_price = st.multiselect(
                    "Seleccionar fabricantes:",
                    sorted(top_manufacturers),
                    default=sorted(top_manufacturers)[:5] if len(top_manufacturers) > 5 else top_manufacturers
                )
                plot_data = manufacturer_price_data[manufacturer_price_data["manufacturer"].isin(selected_manufacturers_price)]
            else:
                plot_data = manufacturer_price_data
        
        with col2:
            if viz_type_price == "Box plot":
                fig_price_compare = px.box(plot_data, x="manufacturer", y="price",
                                         title="Distribución de Precios por Fabricante",
                                         labels={'manufacturer': 'Fabricante', 'price': 'Precio ($)'},
                                         color="manufacturer", points="all")
                st.plotly_chart(fig_price_compare, use_container_width=True)
                
            elif viz_type_price == "Histograma":
                fig_price_compare = px.histogram(plot_data, x="price", color="manufacturer",
                                                title="Distribución de Precios por Fabricante",
                                                labels={'price': 'Precio ($)', 'count': 'Cantidad'},
                                                nbins=nbins_price, barmode="overlay",
                                                log_y=log_scale, opacity=0.7)
                st.plotly_chart(fig_price_compare, use_container_width=True)
                
            else:
                fig_price_compare = px.violin(plot_data, x="manufacturer", y="price",
                                             title="Distribución de Precios por Fabricante (Violín)",
                                             labels={'manufacturer': 'Fabricante', 'price': 'Precio ($)'},
                                             color="manufacturer", box=True)
                st.plotly_chart(fig_price_compare, use_container_width=True)
    else:
        st.warning("No hay suficientes datos por fabricante para mostrar comparaciones.")
else:
    st.warning("No hay datos de fabricante para mostrar.")

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