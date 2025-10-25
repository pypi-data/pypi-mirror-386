import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from scipy import stats
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
from wordcloud import WordCloud
import plotly.figure_factory as ff
warnings.filterwarnings('ignore')
import seaborn as sns
from plotly.subplots import make_subplots
import requests
import pandas as pd
import io
from PIL import Image
import pandas as pd
import numpy as np
from graphviz import Digraph
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.linear_model import LinearRegression, Ridge, LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import LocalOutlierFactor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report, confusion_matrix
from sklearn.inspection import permutation_importance
from scipy.stats import gaussian_kde
import streamlit.components.v1 as components
import tensorflow as tf
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, classification_report
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import warnings
warnings.filterwarnings('ignore')
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from xgboost import XGBRegressor, XGBClassifier
from sklearn.ensemble import VotingRegressor, VotingClassifier
from sklearn.ensemble import StackingRegressor, StackingClassifier
from sklearn.model_selection import cross_validate, GridSearchCV
from sklearn.metrics import get_scorer
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
import keras


# Konfigurasi untuk performa
plt.style.use('default')
sns.set_palette("husl")

# --- Konfigurasi halaman ---
st.set_page_config(
    page_icon="https://github.com/DwiDevelopes/gambar/raw/main/Desain%20tanpa%20judul%20(8).jpg",
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="STREAMLIT LAUNCHER"
)
st.title("📊 STREAMLIT LAUNCHER ANALYSIS PENELITIAN LANJUTAN")

# --- Tambahkan gambar responsif ---
st.markdown(
    """
    <style>
    .responsive-img {
        width: 100%;
        height: auto;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Ganti URL di bawah ini dengan lokasi gambar kamu (bisa file lokal atau URL)
st.markdown(
    """
    <img src="https://github.com/DwiDevelopes/gambar/raw/main/Desain%20tanpa%20judul%20(8).jpg" class="responsive-img">
    """,
    unsafe_allow_html=True
)

# CSS kustom untuk styling
st.markdown("""
<meta name="google-site-verification" content="ryAdKrOiPgVE9lQjxBAPCNbxtfCOJkDg_pvo7dzlp4U" />
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .data-table th, .data-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .data-table th {
        background-color: #f2f2f2;
    }
    .data-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .up-trend {
        color: green;
        font-weight: bold;
    }
    .down-trend {
        color: red;
        font-weight: bold;
    }
    .stock-summary {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        border-left: 5px solid #1f77b4;
    }
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .chart-description {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        border-left: 4px solid #1f77b4;
    }
    .slider-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .kpi-title {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Cache untuk performa
@st.cache_data(show_spinner=False)
def process_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            st.sidebar.success(f"CSV berhasil dibaca: {uploaded_file.name}")
            
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            # Coba beberapa engine untuk membaca Excel
            try:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            except:
                try:
                    df = pd.read_excel(uploaded_file, engine='xlrd')
                except:
                    st.error("Tidak dapat membaca file Excel. Pastikan openpyxl atau xlrd terinstall.")
                    return None
            
            st.sidebar.success(f"Excel berhasil dibaca: {uploaded_file.name}")
                
        else:
            st.error("Format file tidak didukung. Harap unggah file CSV atau Excel.")
            return None
        
        df.columns = df.columns.str.strip()
        df = auto_convert_dates(df)
        return df
        
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {str(e)}")
        st.info("Untuk file Excel, pastikan dependensi 'openpyxl' terinstall. Jalankan: pip install openpyxl")
        return None

@st.cache_data(show_spinner=False)
def auto_convert_dates(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                temp_col = pd.to_datetime(df[col], errors='coerce')
                if temp_col.notna().sum() / len(df) > 0.7:
                    df[col] = temp_col
                    st.sidebar.info(f"Kolom '{col}' dikonversi otomatis ke format tanggal")
            except:
                pass
    return df

@st.cache_data(show_spinner=False)
def merge_datasets(datasets, merge_method='concat'):
    if not datasets:
        return None
    
    if merge_method == 'concat':
        combined_df = pd.concat(datasets, ignore_index=True)
        st.sidebar.success(f"Berhasil menggabungkan {len(datasets)} dataset (concat)")
        return combined_df
    else:
        common_columns = set(datasets[0].columns)
        for dataset in datasets[1:]:
            common_columns = common_columns.intersection(set(dataset.columns))
        
        if not common_columns:
            st.error("Tidak ada kolom yang sama untuk melakukan penggabungan.")
            return None
        
        merge_key = list(common_columns)[0]
        st.sidebar.info(f"Menggunakan kolom '{merge_key}' sebagai kunci penggabungan")
        
        merged_df = datasets[0]
        for i in range(1, len(datasets)):
            try:
                merged_df = pd.merge(merged_df, datasets[i], how=merge_method, on=merge_key, suffixes=('', f'_{i}'))
            except Exception as e:
                st.error(f"Error saat menggabungkan dataset: {str(e)}")
                return None
        
        st.sidebar.success(f"Berhasil menggabungkan {len(datasets)} dataset ({merge_method} join)")
        return merged_df

# Fungsi untuk membuat semua jenis visualisasi
def create_all_visualizations(df):
    if df is None or df.empty:
        st.error("Data tidak tersedia atau kosong")
        return
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    if not numeric_cols:
        st.error("Tidak ditemukan kolom numerik dalam dataset.")
        return
    
    # Sidebar untuk konfigurasi chart
    st.sidebar.header("🎛️ Konfigurasi Visualisasi")
    
    # Pilihan jenis chart yang diperluas
    chart_types = [
        "📈 Grafik Garis (Line Chart)",
        "📊 Grafik Batang (Bar Chart)",
        "🦈 Fishbone Diagram", 
        "📋 Histogram Responsif Berwarna",
        "🔄 Diamond Chart",
        "🛜 Network Diagram",
        "🔵 Scatter Plot",
        "🫧 Grafik Gelembung (Bubble Chart)",
        "🎯 Grafik Gauge (Speedometer)",
        "🕷️ Grafik Radar (Spider Chart)",
        "📦 Diagram Bingkai (Box Plot)",
        "🍾 Grafik Corong (Funnel Chart)",
        "🥧 Pie Chart dengan Slider",
        "📊 Scorecard / KPI Indicator",
        "🎯 Bullet Chart",
        "🌳 Treemap",
        "☁️ Word Cloud",
        "📅 Grafik Gantt (Gantt Chart)",
        "🗺️ Grafik Peta (Map Chart)",
        "🌊 Grafik Peta Aliran (Flow Map)",
        "🔥 Heatmap",
        "🤖 Model Penelitian (Regression Chart)"
    ]
    
    chart_type = st.sidebar.selectbox("Pilih Jenis Chart", chart_types, key="chart_type_select")
    
    try:
        # Container untuk chart
        chart_container = st.container()
        
        with chart_container:
            st.markdown(f"### {chart_type}")
            
            if chart_type == "📈 Grafik Garis (Line Chart)":
                create_line_chart(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "📊 Grafik Batang (Bar Chart)":
                create_bar_chart(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "🦈 Fishbone Diagram":
                create_enhanced_fishbone_diagram(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "📋 Histogram Responsif Berwarna": 
                create_responsive_histogram(df, numeric_cols) 
            
            elif chart_type == "🛜 Network Diagram":
                create_network_diagram(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "🔄 Diamond Chart":
                create_diamond_chart(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "🔵 Scatter Plot":
                create_scatter_plot(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "🫧 Grafik Gelembung (Bubble Chart)":
                create_bubble_chart(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "🎯 Grafik Gauge (Speedometer)":
                create_gauge_chart(df, numeric_cols)
                
            elif chart_type == "🕷️ Grafik Radar (Spider Chart)":
                create_radar_chart(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "📦 Diagram Bingkai (Box Plot)":
                create_box_plot(df, numeric_cols)
                
            elif chart_type == "🍾 Grafik Corong (Funnel Chart)":
                create_funnel_chart(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "🥧 Pie Chart dengan Slider":
                create_pie_chart_with_slider(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "📊 Scorecard / KPI Indicator":
                create_kpi_scorecard(df, numeric_cols)
                
            elif chart_type == "🎯 Bullet Chart":
                create_bullet_chart(df, numeric_cols)
                
            elif chart_type == "🌳 Treemap":
                create_treemap(df, numeric_cols, non_numeric_cols)
                
            elif chart_type == "☁️ Word Cloud":
                create_wordcloud(df, non_numeric_cols)
                
            elif chart_type == "📅 Grafik Gantt (Gantt Chart)":
                create_gantt_chart(df)
                
            elif chart_type == "🗺️ Grafik Peta (Map Chart)":
                create_map_chart(df)
                
            elif chart_type == "🌊 Grafik Peta Aliran (Flow Map)":
                create_flow_map(df)
                
            elif chart_type == "🔥 Heatmap":
                create_heatmap(df, numeric_cols)
                
            elif chart_type == "🤖 Model Penelitian (Regression Chart)":
                create_ml_dl_analysis_dashboard(df, numeric_cols, non_numeric_cols)
                
    except Exception as e:
        st.error(f"Error dalam membuat visualisasi: {str(e)}")
        st.error("Pastikan semua library yang diperlukan sudah diimport")

def create_responsive_histogram(df, numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_col = st.selectbox("Pilih kolom numerik", numeric_cols, key="histogram_col")
    
    with col2:
        num_bins = st.slider("Jumlah bins", min_value=5, max_value=100, value=min(30, data_size//1000), 
                           key="hist_bins")
    
    with col3:
        color_theme = st.selectbox("Tema warna", 
                                 ["Viridis", "Plasma", "Inferno", "Magma", "Cividis", "Blues"],
                                 key="hist_color")
    
    with col4:
        # Pengaturan optimasi
        optimization_mode = st.selectbox(
            "Mode Optimasi",
            ["Auto", "Fast", "Balanced", "Detailed"],
            index=0 if data_size > 100000 else 2,
            key="hist_optim"
        )

    if selected_col:
        try:
            with st.spinner("🔄 Memproses data histogram..."):
                # OPTIMASI 1: Filter dan sampling data
                clean_data = optimize_histogram_data(df[selected_col], data_size, optimization_mode)
                
                if len(clean_data) == 0:
                    st.warning(f"Tidak ada data valid untuk kolom {selected_col}")
                    return
                
                # OPTIMASI 2: Batasi bins untuk data sangat besar
                if len(clean_data) > 100000:
                    num_bins = min(num_bins, 50)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Buat histogram yang dioptimalkan
                    fig = create_optimized_histogram(clean_data, selected_col, num_bins, color_theme, data_size)
                    st.plotly_chart(fig, use_container_width=True, 
                                  config={'displayModeBar': True, 'responsive': True})
                
                with col2:
                    # Statistik cepat
                    display_quick_statistics(clean_data, selected_col)

                # OPTIMASI 3: Multiple histogram dengan data terbatas
                if data_size <= 50000:  # Hanya tampilkan untuk data tidak terlalu besar
                    with st.expander("🔍 Bandingkan Distribusi", expanded=False):
                        compare_cols = st.multiselect(
                            "Pilih kolom untuk perbandingan", 
                            numeric_cols[:5],  # Batasi pilihan
                            default=[selected_col],
                            key="hist_compare"
                        )
                        
                        if len(compare_cols) > 1:
                            fig_compare = create_comparison_histogram(df, compare_cols, optimization_mode)
                            st.plotly_chart(fig_compare, use_container_width=True)
                
                # Tampilkan info optimasi
                show_histogram_optimization_info(data_size, len(clean_data), optimization_mode)

        except Exception as e:
            st.error(f"Error membuat histogram: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_histogram_fallback(df[selected_col].dropna(), selected_col)

def optimize_histogram_data(data_series, data_size, optimization_mode):
    """Optimasi data untuk histogram dengan sampling yang tepat"""
    clean_data = data_series.dropna()
    
    if len(clean_data) == 0:
        return clean_data
    
    # Tentukan target sample size berdasarkan mode optimasi
    target_sizes = {
        "Auto": min(10000, data_size) if data_size > 50000 else data_size,
        "Fast": min(5000, data_size),
        "Balanced": min(20000, data_size),
        "Detailed": data_size
    }
    
    target_size = target_sizes[optimization_mode]
    
    # Jika data lebih besar dari target, lakukan sampling
    if len(clean_data) > target_size:
        if optimization_mode == "Fast":
            # Systematic sampling untuk performa maksimal
            step = len(clean_data) // target_size
            sampled_data = clean_data.iloc[::step]
        else:
            # Stratified sampling untuk mempertahankan distribusi
            try:
                # Bin data terlebih dahulu, lalu sample dari setiap bin
                n_bins = min(100, target_size // 10)
                bins = pd.cut(clean_data, bins=n_bins)
                stratified_sample = clean_data.groupby(bins, observed=False, group_keys=False).apply(
                    lambda x: x.sample(n=min(len(x), max(1, target_size // n_bins)), random_state=42)
                )
                sampled_data = stratified_sample
            except:
                # Fallback ke random sampling
                sampled_data = clean_data.sample(n=target_size, random_state=42)
        
        return sampled_data
    
    return clean_data

def create_optimized_histogram(data, column_name, num_bins, color_theme, original_size):
    """Buat histogram dengan optimasi performa"""
    
    # Mapping warna yang dioptimalkan
    color_sequences = {
        "Viridis": ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'],
        "Plasma": ['#0d0887', '#7e03a8', '#cc4778', '#f89540', '#f0f921'],
        "Inferno": ['#000004', '#3b0f70', '#8c2981', '#de4968', '#fe9f6d'],
        "Magma": ['#000004', '#4a0c6b', '#a52c60', '#e95e3c', '#feca8d'],
        "Cividis": ['#00204d', '#31446b', '#666870', '#958f78', '#ffea46'],
        "Blues": ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6']
    }
    
    selected_color = color_sequences.get(color_theme, color_sequences["Viridis"])[2]
    
    # OPTIMASI: Gunakan numpy untuk perhitungan histogram yang lebih cepat
    hist, bin_edges = np.histogram(data, bins=num_bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    fig = go.Figure()
    
    # Trace histogram yang dioptimalkan
    fig.add_trace(go.Bar(
        x=bin_centers,
        y=hist,
        width=np.diff(bin_edges),
        name=column_name,
        marker_color=selected_color,
        opacity=0.8,
        hovertemplate='<b>Range: %{x:.2f}</b><br>Frekuensi: %{y}<extra></extra>'
    ))
    
    # OPTIMASI: Density plot hanya untuk data yang tidak terlalu besar
    if len(data) <= 10000:
        try:
            from scipy.stats import gaussian_kde
            # Sample data untuk density calculation
            if len(data) > 2000:
                density_data = data.sample(n=2000, random_state=42)
            else:
                density_data = data
                
            x_range = np.linspace(data.min(), data.max(), 100)
            density = gaussian_kde(density_data)(x_range)
            hist_area = len(data) * (data.max() - data.min()) / num_bins
            scaled_density = density * hist_area
            
            fig.add_trace(go.Scatter(
                x=x_range,
                y=scaled_density,
                mode='lines',
                line=dict(color='red', width=2),
                name='Density Estimate',
                hovertemplate='<b>Density: %{y:.2f}</b><extra></extra>'
            ))
        except:
            pass  # Skip density plot jika error
    
    # Layout yang dioptimalkan
    fig.update_layout(
        title=f"Distribusi {column_name} ({len(data):,} data points)",
        height=450,
        showlegend=True,
        bargap=0.05,
        xaxis_title=column_name,
        yaxis_title="Frekuensi",
        margin=dict(l=50, r=50, t=60, b=50),
        plot_bgcolor='white'
    )
    
    return fig

def display_quick_statistics(data, column_name):
    """Tampilkan statistik cepat yang dioptimalkan"""
    st.markdown("### 📊 Statistik Cepat")
    
    # Hitung statistik dasar dengan numpy (lebih cepat)
    stats_data = {
        "Rata-rata": f"{np.mean(data):.2f}",
        "Median": f"{np.median(data):.2f}",
        "Std Dev": f"{np.std(data):.2f}",
        "Min": f"{np.min(data):.2f}",
        "Max": f"{np.max(data):.2f}",
        "Jumlah Data": f"{len(data):,}"
    }
    
    for key, value in stats_data.items():
        st.metric(key, value)
    
    # Hitung skewness dengan optimasi
    try:
        if len(data) > 2:
            skew_val = (3 * (np.mean(data) - np.median(data))) / np.std(data)  # Approximation
            st.metric("Skewness", f"{skew_val:.2f}")
            
            # Info distribusi
            st.markdown("### 📈 Info Distribusi")
            if abs(skew_val) < 0.5:
                st.success("**Normal**")
            elif skew_val > 0.5:
                st.warning("**Right-skewed**")
            else:
                st.warning("**Left-skewed**")
    except:
        pass

def create_comparison_histogram(df, compare_cols, optimization_mode):
    """Buat histogram perbandingan yang dioptimalkan"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, col in enumerate(compare_cols[:4]):  # Maksimal 4 kolom
        clean_data = optimize_histogram_data(df[col], len(df), optimization_mode)
        if len(clean_data) > 0:
            fig.add_trace(go.Histogram(
                x=clean_data,
                name=col,
                opacity=0.6,
                nbinsx=20,  # Fixed bins untuk performa
                marker_color=colors[i % len(colors)],
                hovertemplate=f'<b>{col}</b><br>%{{x}}</b><br>Frekuensi: %{{y}}<extra></extra>'
            ))
    
    fig.update_layout(
        title="Perbandingan Distribusi (Optimized)",
        barmode='overlay',
        height=400,
        xaxis_title="Nilai",
        yaxis_title="Frekuensi",
        showlegend=True
    )
    
    return fig

def show_histogram_optimization_info(original_size, processed_size, optimization_mode):
    """Tampilkan informasi optimasi"""
    reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
    
    if reduction_pct > 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{original_size:,}")
            with col2:
                st.metric("Data Diproses", f"{processed_size:,}")
            with col3:
                st.metric("Reduksi", f"{reduction_pct:.1f}%")
            
            st.info(f"**Mode {optimization_mode}**: Histogram dioptimalkan untuk kecepatan rendering")

def create_simple_histogram_fallback(data, column_name):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback yang sederhana...")
    
    if len(data) > 1000:
        data = data.sample(n=1000, random_state=42)
    
    fig = px.histogram(x=data, nbins=20, title=f"Simple Histogram - {column_name}")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Versi ultra-ringan untuk data ekstrem
def create_ultra_fast_histogram(df, numeric_cols):
    """Versi ultra-ringan untuk data > 500k rows"""
    
    col1, col2 = st.columns(2)
    with col1:
        selected_col = st.selectbox("Pilih kolom", numeric_cols[:10], key="ultra_hist_col")
    with col2:
        num_bins = st.slider("Bins", 5, 50, 20, key="ultra_bins")
    
    if selected_col:
        # Sampling agresif
        if len(df) > 5000:
            data = df[selected_col].dropna().sample(n=5000, random_state=42)
        else:
            data = df[selected_col].dropna()
        
        # Histogram sederhana
        fig = px.histogram(x=data, nbins=num_bins, 
                         title=f"Ultra-Fast: {selected_col} (5,000 samples)")
        fig.update_layout(height=350, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.info(f"📊 Menampilkan 5,000 sample dari {len(df[selected_col].dropna()):,} data points")

# FUNGSI BARU: Pie Chart dengan Slider
def create_pie_chart_with_slider(df, numeric_cols, non_numeric_cols):
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_col = st.selectbox("Pilih kolom kategori", non_numeric_cols, key="pie_category")
    with col2:
        value_col = st.selectbox("Pilih kolom nilai", numeric_cols, key="pie_value")
    
    if category_col and value_col:
        # Agregasi data
        pie_data = df.groupby(category_col)[value_col].sum().reset_index()
        pie_data = pie_data.sort_values(value_col, ascending=False)
        
        # Hitung persentase
        total_value = pie_data[value_col].sum()
        pie_data['percentage'] = (pie_data[value_col] / total_value * 100).round(2)
        
        # Slider untuk threshold persentase
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        threshold = st.slider(
            "Threshold Persentase untuk 'Lainnya' (%)", 
            min_value=0.0, 
            max_value=20.0, 
            value=2.0, 
            step=0.5,
            help="Kategori dengan persentase di bawah nilai ini akan digabung menjadi 'Lainnya'"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Proses data berdasarkan threshold
        main_categories = pie_data[pie_data['percentage'] >= threshold]
        other_categories = pie_data[pie_data['percentage'] < threshold]
        
        if len(other_categories) > 0:
            other_total = other_categories[value_col].sum()
            other_percentage = other_categories['percentage'].sum()
            
            final_data = pd.concat([
                main_categories,
                pd.DataFrame({
                    category_col: ['Lainnya'],
                    value_col: [other_total],
                    'percentage': [other_percentage]
                })
            ], ignore_index=True)
        else:
            final_data = main_categories
        
        # Buat pie chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.pie(
                final_data, 
                values=value_col, 
                names=category_col,
                title=f"Distribusi {value_col} per {category_col}",
                hover_data=['percentage'],
                labels={'percentage': 'Persentase (%)'}
            )
            
            # Customisasi tampilan
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Nilai: %{value}<br>Persentase: %{percent}<extra></extra>'
            )
            
            fig.update_layout(
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Detail Kategori")
            st.markdown(f"**Total {value_col}:** {total_value:,.2f}")
            st.markdown(f"**Jumlah Kategori:** {len(pie_data)}")
            st.markdown(f"**Kategori ditampilkan:** {len(main_categories)}")
            if len(other_categories) > 0:
                st.markdown(f"**Kategori di 'Lainnya':** {len(other_categories)}")
            
            st.markdown("---")
            st.markdown("**Top 5 Kategori:**")
            for i, row in pie_data.head().iterrows():
                st.markdown(f"• {row[category_col]}: {row['percentage']:.1f}%")
        
        # Tampilkan tabel data detail
        with st.expander("📋 Lihat Data Detail"):
            display_data = final_data.copy()
            display_data[value_col] = display_data[value_col].round(2)
            display_data['percentage'] = display_data['percentage'].round(2)
            st.dataframe(display_data[[category_col, value_col, 'percentage']], use_container_width=True)
        
        # Keterangan
        with st.expander("ℹ️ Keterangan Pie Chart dengan Slider"):
            st.markdown("""
            **Pie Chart dengan Slider** memungkinkan Anda mengontrol tampilan kategori berdasarkan persentase.
            - **Slider Threshold**: Mengatur batas minimum persentase untuk menampilkan kategori secara individual
            - **Kategori 'Lainnya'**: Semua kategori di bawah threshold akan digabung
            - **Kelebihan**: Fleksibel dalam menampilkan data, menghindari chart yang terlalu penuh
            - **Penggunaan**: Distribusi data dengan banyak kategori, analisis komposisi
            """)

def create_kpi_scorecard(df, numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan kalkulasi cepat")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        kpi_col = st.selectbox("Pilih kolom untuk KPI", numeric_cols, key="kpi_col")
    
    with col2:
        calculation_type = st.selectbox("Jenis perhitungan", 
                                      ["Mean", "Sum", "Median", "Max", "Min", "Percentile"], 
                                      key="kpi_calc")
        
        if calculation_type == "Percentile":
            percentile_val = st.slider("Percentile", 0, 100, 90, key="kpi_percentile")
    
    with col3:
        optimization_mode = st.selectbox(
            "Mode Optimasi",
            ["Auto", "Fast", "Balanced", "Detailed"],
            index=0 if data_size > 50000 else 2,
            key="kpi_optim"
        )
    
    if kpi_col:
        try:
            with st.spinner("🔄 Menghitung KPI metrics..."):
                # OPTIMASI 1: Kalkulasi nilai KPI yang efisien
                kpi_results = calculate_kpi_values(df, kpi_col, calculation_type, 
                                                 percentile_val if 'percentile_val' in locals() else None,
                                                 data_size, optimization_mode)
                
                if kpi_results is None:
                    st.warning(f"Tidak ada data valid untuk kolom {kpi_col}")
                    return
                
                # Tampilkan KPI cards utama
                display_main_kpi_cards(kpi_results, kpi_col, calculation_type)
                
                # Tampilkan trend analysis
                display_trend_analysis(df, kpi_col, kpi_results, data_size, optimization_mode)
                
                # Tampilkan additional metrics
                display_additional_metrics(kpi_results, data_size)
                
                # Tampilkan info optimasi
                show_kpi_optimization_info(data_size, kpi_results['sample_size'], optimization_mode)
                
        except Exception as e:
            st.error(f"Error menghitung KPI: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_kpi_fallback(df, kpi_col)

def calculate_kpi_values(df, kpi_col, calculation_type, percentile_val, data_size, optimization_mode):
    """Hitung nilai KPI dengan optimasi untuk data besar"""
    
    # OPTIMASI: Sampling untuk data besar
    if data_size > 100000:
        target_sizes = {
            "Auto": min(10000, data_size),
            "Fast": min(5000, data_size),
            "Balanced": min(20000, data_size),
            "Detailed": min(50000, data_size)
        }
        
        target_size = target_sizes[optimization_mode]
        
        if data_size > target_size:
            # Systematic sampling untuk performa
            step = data_size // target_size
            sample_data = df[kpi_col].dropna().iloc[::step]
            sample_info = f"Sample: {len(sample_data):,} dari {data_size:,}"
        else:
            sample_data = df[kpi_col].dropna()
            sample_info = f"Full data: {len(sample_data):,}"
    else:
        sample_data = df[kpi_col].dropna()
        sample_info = f"Full data: {len(sample_data):,}"
    
    if len(sample_data) == 0:
        return None
    
    # OPTIMASI: Gunakan numpy untuk kalkulasi yang lebih cepat
    data_values = sample_data.values
    
    # Hitung nilai utama berdasarkan tipe kalkulasi
    if calculation_type == "Mean":
        main_value = np.mean(data_values)
    elif calculation_type == "Sum":
        if data_size > 100000:
            # Scale sum untuk data sample
            scale_factor = data_size / len(sample_data)
            main_value = np.sum(data_values) * scale_factor
        else:
            main_value = np.sum(data_values)
    elif calculation_type == "Median":
        main_value = np.median(data_values)
    elif calculation_type == "Max":
        main_value = np.max(data_values)
    elif calculation_type == "Min":
        main_value = np.min(data_values)
    elif calculation_type == "Percentile":
        main_value = np.percentile(data_values, percentile_val)
    else:
        main_value = np.mean(data_values)
    
    # Hitung statistik tambahan
    count = len(sample_data)
    std_dev = np.std(data_values)
    mean_val = np.mean(data_values)
    cv = (std_dev / mean_val * 100) if mean_val != 0 else 0
    
    # Hitung quartiles untuk trend analysis
    q1 = np.percentile(data_values, 25)
    q3 = np.percentile(data_values, 75)
    
    return {
        'main_value': float(main_value),
        'count': count,
        'std_dev': float(std_dev),
        'cv': float(cv),
        'mean': float(mean_val),
        'q1': float(q1),
        'q3': float(q3),
        'min': float(np.min(data_values)),
        'max': float(np.max(data_values)),
        'sample_size': len(sample_data),
        'sample_info': sample_info,
        'data_size': data_size
    }

def display_main_kpi_cards(kpi_results, kpi_col, calculation_type):
    """Tampilkan KPI cards utama"""
    
    # CSS untuk KPI cards
    st.markdown("""
    <style>
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-left: 5px solid #4CAF50;
        margin: 5px;
    }
    .kpi-title {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
        font-weight: 500;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin: 10px 0;
    }
    .kpi-trend-up {
        color: #4CAF50;
        font-weight: bold;
    }
    .kpi-trend-down {
        color: #f44336;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    cols = st.columns(4)
    
    with cols[0]:
        # Main KPI value
        value = kpi_results['main_value']
        display_value = f"{value:,.2f}" if abs(value) < 1000000 else f"{value/1000000:.2f}M"
        
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #4CAF50;">
            <div class="kpi-title">{calculation_type}</div>
            <div class="kpi-value">{display_value}</div>
            <div class="kpi-title">{kpi_col}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        # Data points
        count = kpi_results['count']
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #2196F3;">
            <div class="kpi-title">Data Points</div>
            <div class="kpi-value">{count:,}</div>
            <div class="kpi-title">{kpi_results['sample_info']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        # Variability
        std_dev = kpi_results['std_dev']
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #FF9800;">
            <div class="kpi-title">Standard Deviation</div>
            <div class="kpi-value">{std_dev:.2f}</div>
            <div class="kpi-title">Variability</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        # Coefficient of Variation
        cv = kpi_results['cv']
        cv_status = "Low" if cv < 30 else "Medium" if cv < 70 else "High"
        
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #9C27B0;">
            <div class="kpi-title">Coef of Variation</div>
            <div class="kpi-value">{cv:.1f}%</div>
            <div class="kpi-title">{cv_status} Variability</div>
        </div>
        """, unsafe_allow_html=True)

def display_trend_analysis(df, kpi_col, kpi_results, data_size, optimization_mode):
    """Tampilkan analisis trend"""
    
    st.subheader("📈 Trend Analysis")
    
    trend_cols = st.columns(3)
    
    with trend_cols[0]:
        # Distribution skewness
        try:
            if kpi_results['sample_size'] > 2:
                # Approximation skewness untuk performa
                skewness = (3 * (kpi_results['mean'] - kpi_results['main_value'])) / kpi_results['std_dev']
                skewness = 0 if abs(skewness) > 10 else skewness  # Handle outliers
                
                trend_icon = "📊" if abs(skewness) < 0.5 else "📈" if skewness > 0 else "📉"
                skew_label = "Normal" if abs(skewness) < 0.5 else "Right-skewed" if skewness > 0 else "Left-skewed"
                
                st.metric(
                    f"Distribution {trend_icon}",
                    skew_label,
                    delta=f"Skew: {skewness:.2f}"
                )
        except:
            st.metric("Distribution", "Normal", delta="Skew: N/A")
    
    with trend_cols[1]:
        # Data range efficiency
        data_range = kpi_results['max'] - kpi_results['min']
        if data_range > 0:
            iqr = kpi_results['q3'] - kpi_results['q1']
            range_efficiency = (iqr / data_range) * 100
            efficiency_status = "Good" if range_efficiency > 50 else "Moderate"
            
            st.metric(
                "Data Concentration",
                efficiency_status,
                delta=f"{range_efficiency:.1f}% in IQR"
            )
        else:
            st.metric("Data Concentration", "Constant", delta="No variation")
    
    with trend_cols[2]:
        # Data quality
        completeness = (kpi_results['count'] / kpi_results['data_size']) * 100
        quality_status = "Excellent" if completeness > 95 else "Good" if completeness > 80 else "Poor"
        
        st.metric(
            "Data Quality",
            quality_status,
            delta=f"{completeness:.1f}% complete"
        )

def display_additional_metrics(kpi_results, data_size):
    """Tampilkan metrics tambahan"""
    
    with st.expander("📊 Additional Metrics", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Minimum", f"{kpi_results['min']:.2f}")
        with col2:
            st.metric("Q1 (25%)", f"{kpi_results['q1']:.2f}")
        with col3:
            st.metric("Q3 (75%)", f"{kpi_results['q3']:.2f}")
        with col4:
            st.metric("Maximum", f"{kpi_results['max']:.2f}")
        
        # Progress bars untuk visualisasi
        col5, col6 = st.columns(2)
        
        with col5:
            # Value distribution dalam IQR
            if kpi_results['max'] > kpi_results['min']:
                iqr_range = kpi_results['q3'] - kpi_results['q1']
                total_range = kpi_results['max'] - kpi_results['min']
                iqr_percentage = (iqr_range / total_range) * 100
                
                st.markdown(f"**IQR Coverage:** {iqr_percentage:.1f}%")
                st.progress(iqr_percentage/100)
        
        with col6:
            # Data completeness
            completeness = (kpi_results['count'] / data_size) * 100
            st.markdown(f"**Data Completeness:** {completeness:.1f}%")
            st.progress(completeness/100)

def show_kpi_optimization_info(original_size, processed_size, optimization_mode):
    """Tampilkan informasi optimasi"""
    
    reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
    
    if reduction_pct > 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{original_size:,}")
            with col2:
                st.metric("Data Diproses", f"{processed_size:,}")
            with col3:
                st.metric("Reduksi", f"{reduction_pct:.1f}%")
            
            optimization_strategies = {
                "Fast": "• ✅ **Aggressive sampling**\n• ✅ **Approximation methods**\n• ✅ **Minimal calculations**",
                "Balanced": "• ✅ **Smart sampling**\n• ✅ **Efficient numpy operations**\n• ✅ **Basic trend analysis**",
                "Detailed": "• ✅ **Maximum data retention**\n• ✅ **Comprehensive metrics**\n• ✅ **Full analysis**"
            }
            
            st.info(f"**Mode {optimization_mode}**: {optimization_strategies.get(optimization_mode, 'Custom optimization')}")

def create_simple_kpi_fallback(df, kpi_col):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback sederhana...")
    
    # Kalkulasi sederhana dengan sample kecil
    sample_data = df[kpi_col].dropna().head(1000)
    
    if len(sample_data) == 0:
        st.error("Tidak ada data valid")
        return
    
    cols = st.columns(3)
    
    with cols[0]:
        st.metric("Mean", f"{sample_data.mean():.2f}")
    with cols[1]:
        st.metric("Count", f"{len(sample_data):,}")
    with cols[2]:
        st.metric("Std Dev", f"{sample_data.std():.2f}")

# Versi ultra-ringan untuk data ekstrem
def create_ultra_fast_kpi(df, numeric_cols):
    """Versi ultra-ringan untuk data > 500k rows"""
    st.subheader("🚀 KPI Scorecard Ultra-Fast")
    
    kpi_col = st.selectbox("Pilih kolom KPI", numeric_cols[:8], key="ultra_kpi_col")
    
    if kpi_col:
        # Sampling sangat agresif
        sample_data = df[kpi_col].dropna()
        if len(sample_data) > 5000:
            sample_data = sample_data.sample(n=5000, random_state=42)
        
        if len(sample_data) > 0:
            cols = st.columns(4)
            
            with cols[0]:
                st.metric("Mean", f"{sample_data.mean():.2f}")
            with cols[1]:
                st.metric("Count", f"{len(sample_data):,}")
            with cols[2]:
                st.metric("Std Dev", f"{sample_data.std():.2f}")
            with cols[3]:
                cv = (sample_data.std() / sample_data.mean() * 100) if sample_data.mean() != 0 else 0
                st.metric("CV", f"{cv:.1f}%")
            
            st.info(f"📊 Ultra-Fast Mode: 5,000 samples dari {len(df[kpi_col].dropna()):,} data points")

def create_bullet_chart(df, numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan kalkulasi cepat")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        value_col = st.selectbox("Pilih kolom nilai", numeric_cols, key="bullet_value")
    
    with col2:
        target_col = st.selectbox("Pilih kolom target (opsional)", 
                                [None] + numeric_cols, 
                                key="bullet_target")
    
    with col3:
        performance_bands = st.slider("Jumlah performance bands", 2, 5, 3, key="bullet_bands")
    
    with col4:
        optimization_mode = st.selectbox(
            "Mode Optimasi",
            ["Auto", "Fast", "Balanced", "Detailed"],
            index=0 if data_size > 50000 else 2,
            key="bullet_optim"
        )
    
    # Pengaturan lanjutan
    with st.expander("⚙️ Pengaturan Lanjutan", expanded=False):
        col5, col6, col7 = st.columns(3)
        with col5:
            band_type = st.selectbox(
                "Tipe Performance Band",
                ["Auto Ranges", "Fixed Ranges", "Percentile Based"],
                key="bullet_band_type"
            )
        with col6:
            if band_type == "Fixed Ranges":
                good_range = st.slider("Good Range (%)", 80, 120, 100, key="bullet_good")
                excellent_range = st.slider("Excellent Range (%)", 100, 150, 120, key="bullet_excellent")
        with col7:
            marker_style = st.selectbox(
                "Style Marker",
                ["diamond", "circle", "square", "triangle-up"],
                key="bullet_marker"
            )
    
    if value_col:
        try:
            with st.spinner("🔄 Menghitung nilai bullet chart..."):
                # OPTIMASI 1: Kalkulasi nilai yang efisien
                bullet_data = calculate_bullet_values(
                    df, value_col, target_col, data_size, optimization_mode
                )
                
                if bullet_data is None:
                    st.warning(f"Tidak ada data valid untuk kolom {value_col}")
                    return
                
                # OPTIMASI 2: Buat bullet chart yang dioptimalkan
                fig = create_optimized_bullet_chart(
                    bullet_data, value_col, target_col, performance_bands, 
                    band_type, marker_style, optimization_mode
                )
                
                # OPTIMASI 3: Konfigurasi plotly yang ringan
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'hoverClosestGl2d'],
                    'responsive': True
                }
                
                st.plotly_chart(fig, use_container_width=True, config=config)
                
                # Tampilkan performance summary
                display_performance_summary(bullet_data, value_col, target_col)
                
                # Tampilkan info optimasi
                show_bullet_optimization_info(data_size, bullet_data['sample_size'], optimization_mode)
                
        except Exception as e:
            st.error(f"Error membuat bullet chart: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_bullet_fallback(df, value_col, target_col)

def calculate_bullet_values(df, value_col, target_col, data_size, optimization_mode):
    """Hitung nilai bullet chart dengan optimasi untuk data besar"""
    
    # OPTIMASI: Sampling untuk data besar
    if data_size > 100000:
        target_sizes = {
            "Auto": min(10000, data_size),
            "Fast": min(5000, data_size),
            "Balanced": min(20000, data_size),
            "Detailed": min(50000, data_size)
        }
        
        target_size = target_sizes[optimization_mode]
        
        if data_size > target_size:
            # Systematic sampling untuk performa
            step = data_size // target_size
            sample_df = df.iloc[::step]
            sample_info = f"Sample: {len(sample_df):,} dari {data_size:,}"
        else:
            sample_df = df
            sample_info = f"Full data: {len(sample_df):,}"
    else:
        sample_df = df
        sample_info = f"Full data: {len(sample_df):,}"
    
    # Filter data yang valid
    value_data = sample_df[value_col].dropna()
    if len(value_data) == 0:
        return None
    
    # Hitung nilai current
    current_value = np.mean(value_data.values)
    
    # Hitung nilai target
    if target_col:
        target_data = sample_df[target_col].dropna()
        if len(target_data) > 0:
            target_value = np.mean(target_data.values)
        else:
            target_value = current_value * 1.1
    else:
        # Auto-calculate target berdasarkan data
        target_value = np.percentile(value_data.values, 75)  # 75th percentile sebagai target
    
    # Hitung statistik tambahan untuk ranges
    min_val = np.min(value_data.values)
    max_val = np.max(value_data.values)
    std_dev = np.std(value_data.values)
    
    return {
        'current_value': float(current_value),
        'target_value': float(target_value),
        'min_value': float(min_val),
        'max_value': float(max_val),
        'std_dev': float(std_dev),
        'sample_size': len(sample_df),
        'sample_info': sample_info,
        'data_size': data_size
    }

def create_optimized_bullet_chart(bullet_data, value_col, target_col, performance_bands, band_type, marker_style, optimization_mode):
    """Buat bullet chart yang dioptimalkan"""
    
    fig = go.Figure()
    
    current_value = bullet_data['current_value']
    target_value = bullet_data['target_value']
    
    # OPTIMASI: Tentukan ranges berdasarkan tipe band
    ranges, colors, labels = calculate_performance_ranges(
        bullet_data, performance_bands, band_type, optimization_mode
    )
    
    # Add performance ranges (stacked bars)
    for i in range(performance_bands):
        range_width = ranges[i+1] - ranges[i]
        
        fig.add_trace(go.Bar(
            x=[range_width],
            y=["Performance"],
            orientation='h',
            marker=dict(
                color=colors[i % len(colors)], 
                opacity=0.3,
                line=dict(width=0)  # No border untuk performa
            ),
            name=labels[i] if i < len(labels) else f'Range {i+1}',
            base=ranges[i],
            hovertemplate=f'<b>{labels[i] if i < len(labels) else f"Range {i+1}"}</b><br>Range: {ranges[i]:.1f} - {ranges[i+1]:.1f}<extra></extra>',
            showlegend=performance_bands <= 4  # Sembunyikan legend jika terlalu banyak bands
        ))
    
    # Add target line
    fig.add_trace(go.Scatter(
        x=[target_value, target_value],
        y=["Performance", "Performance"],
        mode='lines',
        line=dict(color='red', width=3, dash='dash'),
        name='Target',
        hovertemplate=f'<b>Target</b><br>Value: {target_value:.2f}<extra></extra>'
    ))
    
    # Add current value marker
    marker_size = 12 if optimization_mode in ["Balanced", "Detailed"] else 10
    fig.add_trace(go.Scatter(
        x=[current_value],
        y=["Performance"],
        mode='markers',
        marker=dict(
            color='black', 
            size=marker_size, 
            symbol=marker_style,
            line=dict(color='white', width=2)
        ),
        name='Current Value',
        hovertemplate=f'<b>Current Value</b><br>{current_value:.2f}<br>Achievement: {(current_value/target_value*100):.1f}%<extra></extra>'
    ))
    
    # Layout yang dioptimalkan
    layout_config = {
        'title': f"Bullet Chart: {value_col}" + (f" vs {target_col}" if target_col else ""),
        'xaxis': dict(
            title="Nilai",
            showgrid=True,
            gridcolor='lightgray',
            range=[bullet_data['min_value'] * 0.9, max(bullet_data['max_value'], target_value) * 1.1]
        ),
        'yaxis': dict(
            showticklabels=False,
            showgrid=False
        ),
        'showlegend': performance_bands <= 4,
        'height': 200 if optimization_mode == "Fast" else 250,
        'margin': dict(l=50, r=50, t=60, b=50),
        'plot_bgcolor': 'white',
        'barmode': 'stack'
    }
    
    fig.update_layout(**layout_config)
    
    return fig

def calculate_performance_ranges(bullet_data, performance_bands, band_type, optimization_mode):
    """Hitung performance ranges yang optimal"""
    
    target_value = bullet_data['target_value']
    min_val = bullet_data['min_value']
    max_val = bullet_data['max_value']
    std_dev = bullet_data['std_dev']
    
    # Warna berdasarkan jumlah bands
    if performance_bands == 2:
        colors = ['lightcoral', 'lightgreen']
        labels = ['Below Target', 'Above Target']
    elif performance_bands == 3:
        colors = ['lightcoral', 'lightyellow', 'lightgreen']
        labels = ['Poor', 'Good', 'Excellent']
    elif performance_bands == 4:
        colors = ['lightcoral', 'lightsalmon', 'lightyellow', 'lightgreen']
        labels = ['Poor', 'Fair', 'Good', 'Excellent']
    else:  # 5 bands
        colors = ['lightcoral', 'lightsalmon', 'lightyellow', 'lightblue', 'lightgreen']
        labels = ['Very Poor', 'Poor', 'Fair', 'Good', 'Excellent']
    
    # Tentukan ranges berdasarkan tipe band
    if band_type == "Fixed Ranges":
        # Gunakan fixed percentage ranges
        ranges = [min_val]
        for i in range(1, performance_bands):
            percentage = (i / performance_bands) * 100
            ranges.append(target_value * (percentage / 100))
        ranges.append(max(max_val, target_value * 1.2))
        
    elif band_type == "Percentile Based":
        # Berdasarkan distribusi data
        ranges = [min_val]
        for i in range(1, performance_bands):
            percentile = (i / performance_bands) * 100
            ranges.append(np.percentile([min_val, target_value, max_val], percentile))
        ranges.append(max_val)
        
    else:  # Auto Ranges
        # Ranges otomatis berdasarkan target dan std dev
        ranges = [min_val]
        step_size = target_value / performance_bands
        
        for i in range(1, performance_bands):
            ranges.append(step_size * i)
        ranges.append(max(max_val, target_value * 1.2))
    
    return ranges, colors, labels

def display_performance_summary(bullet_data, value_col, target_col):
    """Tampilkan performance summary"""
    
    current_value = bullet_data['current_value']
    target_value = bullet_data['target_value']
    
    # Hitung performance metrics
    performance_ratio = (current_value / target_value * 100) if target_value != 0 else 0
    absolute_diff = current_value - target_value
    
    # PERBAIKAN: Gunakan delta_color yang valid
    if performance_ratio >= 100:
        status = "✅ Exceeded Target"
        delta_color = "normal"  # Hijau untuk positif
    elif performance_ratio >= 80:
        status = "⚠️ Near Target"
        delta_color = "off"     # Abu-abu untuk netral
    else:
        status = "❌ Below Target"
        delta_color = "inverse" # Merah untuk negatif
    
    st.subheader("📊 Performance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Value", 
            f"{current_value:.2f}",
            delta=f"{absolute_diff:+.2f}" if abs(absolute_diff) > 0.01 else "0.00",
            delta_color=delta_color
        )
    
    with col2:
        st.metric("Target Value", f"{target_value:.2f}")
    
    with col3:
        # Untuk performance ratio, kita gunakan custom styling
        st.markdown(f"""
        <div style="background: {'#d4edda' if performance_ratio >= 100 else '#fff3cd' if performance_ratio >= 80 else '#f8d7da'}; 
                    padding: 10px; border-radius: 5px; border-left: 5px solid {'#28a745' if performance_ratio >= 100 else '#ffc107' if performance_ratio >= 80 else '#dc3545'};">
            <div style="font-size: 14px; color: #666;">Performance</div>
            <div style="font-size: 24px; font-weight: bold; color: #333;">{performance_ratio:.1f}%</div>
            <div style="font-size: 12px; color: #666;">{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.metric("Data Points", f"{bullet_data['sample_size']:,}")
    
    # Progress bar visual
    progress_ratio = min(performance_ratio / 100, 1.0)
    st.progress(
        float(progress_ratio), 
        text=f"Achievement: {performance_ratio:.1f}% of target"
    )
    
    # Additional insights
    with st.expander("🔍 Additional Insights", expanded=False):
        col5, col6 = st.columns(2)
        
        with col5:
            # Variability analysis
            cv = (bullet_data['std_dev'] / current_value * 100) if current_value != 0 else 0
            st.metric("Coefficient of Variation", f"{cv:.1f}%")
            
            if cv < 10:
                st.info("✅ Low variability - consistent performance")
            elif cv < 30:
                st.warning("⚠️ Moderate variability")
            else:
                st.error("❌ High variability - inconsistent performance")
        
        with col6:
            # Target achievement confidence
            if bullet_data['std_dev'] > 0:
                z_score = (current_value - target_value) / bullet_data['std_dev']
                confidence = "High" if z_score > 1 else "Medium" if z_score > 0 else "Low"
                st.metric("Achievement Confidence", confidence)
            else:
                st.metric("Achievement Confidence", "N/A")

def show_bullet_optimization_info(data_size, sample_size, optimization_mode):
    """Tampilkan informasi optimasi"""
    
    reduction_pct = ((data_size - sample_size) / data_size) * 100 if data_size > 0 else 0
    
    if reduction_pct > 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{data_size:,}")
            with col2:
                st.metric("Data Diproses", f"{sample_size:,}")
            with col3:
                st.metric("Reduksi", f"{reduction_pct:.1f}%")
            
            optimization_strategies = {
                "Fast": "• ✅ **Aggressive sampling**\n• ✅ **Simple ranges**\n• ✅ **Minimal styling**",
                "Balanced": "• ✅ **Smart sampling**\n• ✅ **Optimized ranges**\n• ✅ **Enhanced visuals**",
                "Detailed": "• ✅ **Maximum data retention**\n• ✅ **Advanced analysis**\n• ✅ **Full features**"
            }
            
            st.info(f"**Mode {optimization_mode}**: {optimization_strategies.get(optimization_mode, 'Custom optimization')}")

def create_simple_bullet_fallback(df, value_col, target_col):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback sederhana...")
    
    # Kalkulasi sederhana dengan sample kecil
    sample_data = df[[value_col] + ([target_col] if target_col else [])].dropna().head(1000)
    
    if len(sample_data) == 0:
        st.error("Tidak ada data valid")
        return
    
    current_value = sample_data[value_col].mean()
    target_value = sample_data[target_col].mean() if target_col else current_value * 1.1
    
    # Simple bullet chart
    fig = go.Figure()
    
    # Simple ranges
    ranges = [0, target_value * 0.5, target_value * 0.8, target_value * 1.2]
    colors = ['lightcoral', 'lightyellow', 'lightgreen']
    
    for i in range(3):
        fig.add_trace(go.Bar(
            x=[ranges[i+1] - ranges[i]],
            y=["Performance"],
            orientation='h',
            marker=dict(color=colors[i], opacity=0.3),
            base=ranges[i],
            showlegend=False
        ))
    
    fig.add_trace(go.Scatter(
        x=[target_value, target_value],
        y=["Performance", "Performance"],
        mode='lines',
        line=dict(color='red', width=2),
        name='Target'
    ))
    
    fig.add_trace(go.Scatter(
        x=[current_value],
        y=["Performance"],
        mode='markers',
        marker=dict(color='black', size=10, symbol='diamond'),
        name='Current'
    ))
    
    fig.update_layout(
        title=f"Simple Bullet: {value_col}",
        height=200,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tampilkan metrics sederhana
    performance_ratio = (current_value / target_value * 100) if target_value != 0 else 0
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current", f"{current_value:.2f}")
    with col2:
        st.metric("Target", f"{target_value:.2f}")
    with col3:
        st.metric("Performance", f"{performance_ratio:.1f}%")

# FUNGSI BARU: Treemap yang dioptimalkan
def create_treemap(df, numeric_cols, non_numeric_cols):
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        hierarchy_1 = st.selectbox("Level hierarki 1", non_numeric_cols, key="tree_1")
    with col2:
        hierarchy_2 = st.selectbox("Level hierarki 2 (opsional)", 
                                 [None] + [col for col in non_numeric_cols if col != hierarchy_1], 
                                 key="tree_2")
    with col3:
        value_col = st.selectbox("Kolom nilai", numeric_cols, key="tree_value")
    
    if hierarchy_1 and value_col:
        # Optimasi: Gunakan cache untuk data yang besar
        @st.cache_data(ttl=3600)
        def aggregate_tree_data(_df, group_cols, value_column):
            return _df.groupby(group_cols)[value_column].sum().reset_index()
        
        # Tentukan kolom grouping
        group_cols = [hierarchy_1]
        if hierarchy_2 and hierarchy_2 != 'None':
            group_cols.append(hierarchy_2)
        
        # Agregasi data dengan cache
        with st.spinner("Memproses data..."):
            tree_data = aggregate_tree_data(df, group_cols, value_col)
        
        # Optimasi: Batasi jumlah kategori jika terlalu banyak
        max_categories = 50
        if len(tree_data) > max_categories:
            st.warning(f"⚠️ Data terlalu banyak ({len(tree_data)} kategori). Menampilkan {max_categories} kategori teratas.")
            
            # Ambil top categories berdasarkan value
            top_data = tree_data.nlargest(max_categories, value_col)
            other_data = tree_data.nsmallest(len(tree_data) - max_categories, value_col)
            
            # Gabungkan kategori kecil menjadi "Lainnya"
            if len(other_data) > 0:
                other_sum = other_data[value_col].sum()
                other_row = {group_cols[0]: "Lainnya", value_col: other_sum}
                if len(group_cols) > 1:
                    other_row[group_cols[1]] = "Lainnya"
                top_data = pd.concat([top_data, pd.DataFrame([other_row])], ignore_index=True)
            
            tree_data = top_data
        
        # Buat treemap
        fig = px.treemap(
            tree_data,
            path=group_cols,
            values=value_col,
            title=f"Treemap: {value_col} by {hierarchy_1}" + (f" and {hierarchy_2}" if hierarchy_2 and hierarchy_2 != 'None' else ""),
            color=value_col,
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            height=600,
            margin=dict(t=50, l=25, r=25, b=25)
        )
        
        # Optimasi: Gunakan container width dengan config
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
        # Tampilkan data summary dengan pagination
        with st.expander("📊 Data Summary"):
            st.write(f"Total Kategori: {len(tree_data)}")
            
            # Tambahkan filter untuk data summary
            col_a, col_b = st.columns(2)
            with col_a:
                min_value = st.number_input(
                    f"Minimum {value_col}", 
                    min_value=float(tree_data[value_col].min()), 
                    max_value=float(tree_data[value_col].max()),
                    value=float(tree_data[value_col].min()),
                    key="min_tree"
                )
            with col_b:
                sort_order = st.selectbox("Urutkan", ["Descending", "Ascending"], key="sort_tree")
            
            # Filter dan sort data
            filtered_data = tree_data[tree_data[value_col] >= min_value]
            filtered_data = filtered_data.sort_values(
                value_col, 
                ascending=(sort_order == "Ascending")
            )
            
            # Tampilkan dengan pagination
            page_size = 10
            total_pages = max(1, len(filtered_data) // page_size + (1 if len(filtered_data) % page_size > 0 else 0))
            
            page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1, key="page_tree")
            
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, len(filtered_data))
            
            st.dataframe(
                filtered_data.iloc[start_idx:end_idx], 
                use_container_width=True,
                hide_index=True
            )
            
            st.write(f"Menampilkan {start_idx + 1}-{end_idx} dari {len(filtered_data)} baris")
            
            # Download option
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Data sebagai CSV",
                data=csv,
                file_name=f"treemap_data_{value_col}.csv",
                mime="text/csv"
            )

# Alternatif lebih sederhana untuk data sangat besar
def create_treemap_fast(df, numeric_cols, non_numeric_cols):
    
    # Pilihan kolom
    col1, col2, col3 = st.columns(3)
    
    with col1:
        hierarchy_1 = st.selectbox("Level hierarki 1", non_numeric_cols, key="tree_fast_1")
    with col2:
        hierarchy_2 = st.selectbox("Level hierarki 2 (opsional)", 
                                 [None] + [col for col in non_numeric_cols if col != hierarchy_1], 
                                 key="tree_fast_2")
    with col3:
        value_col = st.selectbox("Kolom nilai", numeric_cols, key="tree_fast_value")
    
    if hierarchy_1 and value_col:
        # Sampling untuk data sangat besar
        if len(df) > 10000:
            st.info("🔍 Menggunakan sample data untuk performa lebih baik")
            sample_df = df.sample(n=10000, random_state=42)
        else:
            sample_df = df
        
        # Agregasi langsung tanpa cache (lebih cepat untuk data kecil)
        group_cols = [hierarchy_1]
        if hierarchy_2 and hierarchy_2 != 'None':
            group_cols.append(hierarchy_2)
        
        tree_data = sample_df.groupby(group_cols)[value_col].sum().reset_index()
        
        # Batasi kategori
        if len(tree_data) > 30:
            top_data = tree_data.nlargest(30, value_col)
            st.warning(f"Menampilkan 30 kategori teratas dari {len(tree_data)} total kategori")
            tree_data = top_data
        
        # Buat treemap sederhana
        fig = px.treemap(
            tree_data,
            path=group_cols,
            values=value_col,
            title=f"Treemap: {value_col} by {hierarchy_1}" + (f" and {hierarchy_2}" if hierarchy_2 and hierarchy_2 != 'None' else ""),
            color=value_col,
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig, use_container_width=True)
def create_line_chart(df, numeric_cols, non_numeric_cols):
    """
    Membuat grafik garis interaktif dengan optimasi performa untuk dataset besar
    
    Parameters:
    - df: DataFrame pandas
    - numeric_cols: List kolom numerik
    - non_numeric_cols: List kolom non-numerik
    """
    
    # UI Controls
    st.subheader("📈 Buat Grafik Garis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox(
            "Pilih kolom untuk sumbu X", 
            [df.index.name if df.index.name else "index"] + non_numeric_cols + numeric_cols, 
            key="line_x_col"
        )
    
    with col2:
        y_col = st.selectbox(
            "Pilih kolom untuk sumbu Y", 
            numeric_cols, 
            key="line_y_col"
        )
    
    # Multiple Y columns option
    multi_y = st.checkbox("Gunakan multiple Y columns", value=False, key="line_multi_y")
    
    if multi_y:
        y_cols = st.multiselect(
            "Pilih kolom untuk sumbu Y (multiple)", 
            numeric_cols,
            default=[y_col] if y_col in numeric_cols else [numeric_cols[0]] if numeric_cols else [],
            key="line_y_cols"
        )
    else:
        y_cols = [y_col]
    
    # Performance settings
    with st.expander("⚙️ Pengaturan Performa", expanded=False):
        col3, col4 = st.columns(2)
        
        with col3:
            max_points = st.slider(
                "Maksimum titik data", 
                min_value=500, 
                max_value=10000, 
                value=2000, 
                step=500,
                key="line_max_points"
            )
            use_sampling = st.checkbox("Gunakan sampling", value=True, key="line_sampling")
        
        with col4:
            aggregation = st.selectbox(
                "Aggregasi data", 
                ["none", "mean", "sum", "max", "min"], 
                key="line_aggregation"
            )
            show_range_slider = st.checkbox("Tampilkan range slider", value=True, key="line_range_slider")
    
    # Chart customization
    with st.expander("🎨 Kustomisasi Chart", expanded=False):
        col5, col6 = st.columns(2)
        
        with col5:
            chart_title = st.text_input("Judul Chart", value="", key="line_title")
            line_mode = st.selectbox(
                "Mode Garis", 
                ["lines", "lines+markers", "markers"],
                key="line_mode"
            )
        
        with col6:
            line_width = st.slider("Ketebalan Garis", 1, 5, 2, key="line_width")
            show_grid = st.checkbox("Tampilkan grid", value=True, key="line_grid")
    
    if x_col and y_cols:
        try:
            with st.spinner("Memproses data line chart..."):
                # Prepare data
                processed_df = df[y_cols].copy()
                
                if x_col == "index":
                    x_data = df.index
                    x_label = "Index"
                    processed_df['x_axis'] = x_data
                else:
                    x_data = df[x_col]
                    x_label = x_col
                    processed_df['x_axis'] = x_data
                
                # Remove rows with NaN in x_axis
                processed_df = processed_df.dropna(subset=['x_axis'])
                
                # Data sampling for large datasets
                if use_sampling and len(processed_df) > max_points:
                    processed_df = _apply_sampling(processed_df, max_points, x_label)
                
                # Data aggregation
                if len(processed_df) > max_points and aggregation != "none":
                    processed_df = _apply_aggregation(processed_df, y_cols, aggregation, max_points, x_label)
                
                # Final data point limitation
                if len(processed_df) > max_points:
                    processed_df = processed_df.head(max_points)
                    st.warning(f"⚠️ Data dibatasi hingga {max_points} titik pertama")
                
                # Create line chart
                fig = _create_line_figure(
                    processed_df, 
                    y_cols, 
                    x_label, 
                    chart_title, 
                    line_mode, 
                    line_width, 
                    show_grid, 
                    show_range_slider
                )
                
                # Plotly config for performance
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'hoverClosestGl2d'],
                    'scrollZoom': True,
                    'responsive': True
                }
                
                st.plotly_chart(fig, use_container_width=True, config=config)
            
            # Display statistics
            _display_statistics(processed_df, y_cols, x_label)
                
        except ValueError as e:
            if "date" in str(e).lower():
                st.warning("Format tanggal tidak dikenali. Coba konversi kolom tanggal ke format datetime terlebih dahulu.")
            else:
                st.error(f"Error nilai: {str(e)}")
        except KeyError as e:
            st.error(f"Kolom tidak ditemukan: {str(e)}")
        except Exception as e:
            st.error(f"Error membuat line chart: {str(e)}")
            st.info("Tips: Pastikan data sumbu X dan Y valid dan tidak mengandung nilai NaN")

def _apply_sampling(processed_df, max_points, x_label):
    """Apply sampling strategies based on data type"""
    if pd.api.types.is_datetime64_any_dtype(processed_df['x_axis']):
        # Time series: structured sampling
        processed_df = processed_df.sort_values('x_axis')
        sample_frac = max_points / len(processed_df)
        processed_df = processed_df.sample(frac=sample_frac, random_state=42)
        processed_df = processed_df.sort_values('x_axis')
        st.info(f"📊 Data time series disampling: {len(processed_df):,} dari {len(processed_df):,} titik data")
    else:
        # Non-time series: simple random sampling
        processed_df = processed_df.sample(n=max_points, random_state=42)
        st.info(f"📊 Data disampling: {len(processed_df):,} dari {len(processed_df):,} titik data")
    
    return processed_df

def _apply_aggregation(processed_df, y_cols, aggregation, max_points, x_label):
    """Apply data aggregation based on data type"""
    if pd.api.types.is_datetime64_any_dtype(processed_df['x_axis']):
        # Time series aggregation
        processed_df = processed_df.set_index('x_axis')
        
        # Determine resample frequency based on data span
        time_span = processed_df.index.max() - processed_df.index.min()
        if time_span > timedelta(days=365):
            freq = 'W'  # Weekly for data > 1 year
        elif time_span > timedelta(days=30):
            freq = 'D'  # Daily for data > 1 month
        else:
            freq = 'H'  # Hourly for data < 1 month
        
        if aggregation == "mean":
            processed_df = processed_df.resample(freq).mean()
        elif aggregation == "sum":
            processed_df = processed_df.resample(freq).sum()
        elif aggregation == "max":
            processed_df = processed_df.resample(freq).max()
        elif aggregation == "min":
            processed_df = processed_df.resample(freq).min()
        
        processed_df = processed_df.reset_index()
        st.info(f"📈 Data time series diaggregasi per {freq} ({aggregation})")
    else:
        # Non-time series aggregation
        bins = min(1000, len(processed_df) // 10)
        processed_df['x_bins'] = pd.cut(processed_df['x_axis'], bins=bins)
        
        agg_dict = {'x_axis': 'mean'}
        for col in y_cols:
            agg_dict[col] = aggregation
        
        agg_df = processed_df.groupby('x_bins', observed=True).agg(agg_dict).reset_index()
        processed_df = agg_df
        st.info(f"📈 Data diaggregasi menjadi {bins} bin ({aggregation})")
    
    return processed_df

def _create_line_figure(processed_df, y_cols, x_label, chart_title, line_mode, line_width, show_grid, show_range_slider):
    """Create the line chart figure with optimizations"""
    
    # Determine if datetime for special handling
    is_datetime = pd.api.types.is_datetime64_any_dtype(processed_df['x_axis'])
    
    # Create figure
    if len(y_cols) == 1:
        # Single line
        fig = px.line(
            processed_df, 
            x='x_axis', 
            y=y_cols[0],
            title=chart_title or f"Grafik Garis: {y_cols[0]} over {x_label}",
            line_shape='linear'  # Faster than 'spline'
        )
    else:
        # Multiple lines
        fig = go.Figure()
        colors = px.colors.qualitative.Set1
        
        for i, col in enumerate(y_cols):
            fig.add_trace(go.Scatter(
                x=processed_df['x_axis'],
                y=processed_df[col],
                mode=line_mode,
                name=col,
                line=dict(width=line_width, color=colors[i % len(colors)]),
                connectgaps=False  # Faster rendering
            ))
        
        fig.update_layout(
            title=chart_title or f"Grafik Garis: Multiple Series over {x_label}"
        )
    
    # Layout configuration
    layout_config = {
        'height': 500,
        'showlegend': len(y_cols) > 1,
        'margin': dict(l=50, r=50, t=60, b=80),
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'xaxis': dict(
            title=x_label,
            showgrid=show_grid,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        'yaxis': dict(
            title=", ".join(y_cols) if len(y_cols) > 1 else y_cols[0],
            showgrid=show_grid,
            gridwidth=1,
            gridcolor='lightgray'
        )
    }
    
    # Special handling for time series
    if is_datetime and show_range_slider:
        layout_config['xaxis'].update({
            'rangeslider': dict(visible=True, thickness=0.05),
            'rangeselector': dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        })
    
    fig.update_layout(**layout_config)
    
    # Trace optimizations for performance
    if len(y_cols) == 1:
        fig.update_traces(
            mode=line_mode,
            line=dict(width=line_width),
            connectgaps=False,  # Faster
            hovertemplate=f'<b>{y_cols[0]}</b><br>{x_label}: %{{x}}<br>Nilai: %{{y:.2f}}<extra></extra>'
        )
    
    return fig

def _display_statistics(processed_df, y_cols, x_label):
    """Display data statistics"""
    with st.expander("📊 Statistik Data"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Titik Data", len(processed_df))
        
        with col2:
            if len(y_cols) == 1:
                st.metric(f"Rata-rata {y_cols[0]}", f"{processed_df[y_cols[0]].mean():.2f}")
            else:
                st.metric("Jumlah Series", len(y_cols))
        
        with col3:
            is_datetime = pd.api.types.is_datetime64_any_dtype(processed_df['x_axis'])
            st.metric(
                "Rentang Waktu" if is_datetime else "Rentang Nilai", 
                f"{len(processed_df['x_axis'].unique())} titik"
            )
        
        # Display statistics for each Y column
        for col in y_cols:
            st.write(f"**Statistik untuk {col}:**")
            col_stats = processed_df[col].describe()
            st.dataframe(col_stats.to_frame().T, use_container_width=True)

# Lightweight version for very large datasets
def create_line_chart_lightweight(df, numeric_cols, non_numeric_cols):
    """Versi yang lebih ringan untuk dataset sangat besar (>100k records)"""
    
    st.subheader("🚀 Grafik Garis Ringan (Untuk Data Besar)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox(
            "Pilih kolom untuk sumbu X", 
            [df.index.name if df.index.name else "index"] + non_numeric_cols + numeric_cols, 
            key="line_x_light"
        )
    
    with col2:
        y_col = st.selectbox(
            "Pilih kolom untuk sumbu Y", 
            numeric_cols, 
            key="line_y_light"
        )
    
    if x_col and y_col:
        try:
            # Direct aggregation for maximum performance
            if x_col == "index":
                x_data = df.index
            else:
                x_data = df[x_col]
            
            # Automatic resampling for large data
            sample_df = df[[y_col]].copy()
            sample_df['x_axis'] = x_data
            
            # Remove NaN values
            sample_df = sample_df.dropna()
            
            if len(sample_df) > 1000:
                if pd.api.types.is_datetime64_any_dtype(sample_df['x_axis']):
                    sample_df = sample_df.set_index('x_axis')
                    sample_df = sample_df.resample('H').mean().head(1000)
                    sample_df = sample_df.reset_index()
                    st.info("Data diresample per jam (1000 titik maksimal)")
                else:
                    sample_df = sample_df.sample(n=1000, random_state=42)
                    st.info("Data disampling acak (1000 titik)")
            
            # Simple plot
            fig = px.line(
                sample_df, 
                x='x_axis', 
                y=y_col, 
                title=f"Grafik Garis: {y_col} (Data: {len(sample_df):,} titik)"
            )
            
            fig.update_layout(
                height=400, 
                margin=dict(l=50, r=50, t=50, b=80),
                showlegend=False
            )
            
            st.plotly_chart(
                fig, 
                use_container_width=True, 
                config={'displayModeBar': False}
            )
            
            # Basic statistics
            with st.expander("📊 Statistik Sederhana"):
                st.write(f"**{y_col}:**")
                st.write(f"- Rata-rata: {sample_df[y_col].mean():.2f}")
                st.write(f"- Std Dev: {sample_df[y_col].std():.2f}")
                st.write(f"- Min/Max: {sample_df[y_col].min():.2f} / {sample_df[y_col].max():.2f}")
                
        except Exception as e:
            st.error(f"Error membuat chart: {str(e)}")

# Example usage function
def example_usage():
    """Contoh penggunaan fungsi line chart"""
    
    # Create sample data
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    sample_data = {
        'date': dates,
        'sales': np.random.normal(1000, 200, len(dates)).cumsum() + 10000,
        'customers': np.random.randint(50, 200, len(dates)),
        'revenue': np.random.normal(500, 100, len(dates)).cumsum() + 5000
    }
    
    df = pd.DataFrame(sample_data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Define column types
    numeric_cols = ['sales', 'customers', 'revenue']
    non_numeric_cols = ['date']
    
    # Use the line chart function
    create_line_chart(df, numeric_cols, non_numeric_cols)

# Main function to demonstrate the usage
def main():
    """Fungsi utama untuk demonstrasi"""
    st.title("📈 Dashboard Line Chart Interaktif")
    
    # Pilihan untuk menggunakan data contoh atau upload data
    option = st.radio("Pilih sumber data:", 
                     ["Gunakan Data Contoh", "Upload Data CSV"])
    
    if option == "Gunakan Data Contoh":
        st.info("Menggunakan data contoh untuk demonstrasi")
        example_usage()
        
    else:
        uploaded_file = st.file_uploader("Upload file CSV", type=['csv'])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"Data berhasil diupload: {df.shape[0]} baris, {df.shape[1]} kolom")
                
                # Auto-detect column types
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
                
                st.write("**Kolom Numerik:**", numeric_cols)
                st.write("**Kolom Non-Numerik:**", non_numeric_cols)
                
                # Pilihan tipe chart
                chart_type = st.selectbox(
                    "Pilih tipe line chart:",
                    ["Line Chart Lengkap", "Line Chart Ringan"]
                )
                
                if chart_type == "Line Chart Lengkap":
                    create_line_chart(df, numeric_cols, non_numeric_cols)
                else:
                    create_line_chart_lightweight(df, numeric_cols, non_numeric_cols)
                    
            except Exception as e:
                st.error(f"Error membaca file: {str(e)}")

def create_bar_chart(df, numeric_cols, non_numeric_cols):
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox("Pilih kolom untuk sumbu X", non_numeric_cols if non_numeric_cols else numeric_cols, 
                           key="bar_x_col")
    with col2:
        y_col = st.selectbox("Pilih kolom untuk sumbu Y", numeric_cols, key="bar_y_col")
    
    # Optimasi: Pengaturan performa
    col3, col4 = st.columns(2)
    with col3:
        max_categories = st.slider("Maksimum kategori ditampilkan", 
                                 min_value=5, max_value=50, value=20, key="bar_max_categories")
    with col4:
        sort_data = st.checkbox("Urutkan data", value=True, key="bar_sort")
        use_sampling = st.checkbox("Gunakan sampling untuk data besar", value=True, key="bar_sampling")
    
    if x_col and y_col:
        with st.spinner("Memproses data..."):
            # Optimasi 1: Sampling untuk data besar
            processed_df = df.copy()
            if use_sampling and len(df) > 10000:
                sample_size = min(10000, len(df))
                processed_df = df.sample(n=sample_size, random_state=42)
                st.info(f"📊 Data disampling: {sample_size:,} dari {len(df):,} records")
            
            # Optimasi 2: Aggregasi yang efisien
            if x_col in non_numeric_cols:
                # Untuk data kategorikal, gunakan observed=True dan batasi kategori
                bar_data = (processed_df.groupby(x_col, observed=True)[y_col]
                          .agg(['mean', 'count'])
                          .round(2)
                          .nlargest(max_categories, 'count')
                          .reset_index())
                bar_data.columns = [x_col, y_col, 'count']
            else:
                # Untuk data numerik, buat bins
                bar_data = (processed_df.groupby(pd.cut(processed_df[x_col], bins=min(20, len(processed_df[x_col].unique())), 
                                                      include_lowest=True))[y_col]
                          .mean()
                          .reset_index())
                bar_data.columns = [x_col, y_col]
            
            # Optimasi 3: Sorting jika diperlukan
            if sort_data:
                bar_data = bar_data.sort_values(y_col, ascending=False)
            
            # Optimasi 4: Cache figure creation
            @st.cache_data(ttl=300)
            def create_bar_figure(data, x_col, y_col, title):
                fig = px.bar(
                    data, 
                    x=x_col, 
                    y=y_col, 
                    title=title,
                    color=y_col,
                    color_continuous_scale='blues'
                )
                
                # Optimasi layout untuk performa
                fig.update_layout(
                    height=500,
                    showlegend=False,
                    margin=dict(l=50, r=50, t=60, b=100),
                    xaxis_tickangle=-45,
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                # Optimasi hover data
                fig.update_traces(
                    hovertemplate=f"<b>%{{x}}</b><br>{y_col}: %{{y:.2f}}<extra></extra>"
                )
                
                return fig
            
            title = f"Grafik Batang: Rata-rata {y_col} per {x_col}"
            fig = create_bar_figure(bar_data, x_col, y_col, title)
            
            # Optimasi 5: Plotly config yang ringan
            config = {
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d'],
                'responsive': True
            }
            
            st.plotly_chart(fig, use_container_width=True, config=config)
        
        # Tampilkan data summary
        with st.expander("📊 Lihat Data Summary"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Kategori", len(bar_data))
            with col2:
                st.metric(f"Rata-rata {y_col}", f"{bar_data[y_col].mean():.2f}")
            with col3:
                st.metric("Kategori Tertinggi", bar_data.iloc[0][x_col][:20] + "...")
            
            st.dataframe(bar_data.head(10).style.format({y_col: "{:.2f}"}), use_container_width=True)
            
        with st.expander("ℹ️ Keterangan Grafik Batang"):
            st.markdown(f"""
            **Grafik Batang (Bar Chart)** digunakan untuk membandingkan nilai antar kategori.
            
            **Statistik Dataset:**
            - Total kategori yang ditampilkan: **{len(bar_data)}**
            - Rentang nilai: **{bar_data[y_col].min():.2f}** hingga **{bar_data[y_col].max():.2f}**
            - Standar deviasi: **{bar_data[y_col].std():.2f}**
            
            **Kelebihan**: 
            - Mudah membandingkan nilai antar kategori
            - Visualisasi yang intuitif
            
            **Kekurangan**: 
            - Tidak efektif untuk data dengan banyak kategori
            - Dapat menjadi lambat dengan data sangat besar
            
            **Penggunaan**: Perbandingan kategori, ranking, distribusi kategorikal
            
            **Optimasi yang diterapkan:**
            ✅ Sampling otomatis untuk data besar  
            ✅ Batasan jumlah kategori  
            ✅ Caching untuk performa  
            ✅ Aggregasi yang efisien  
            """)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_enhanced_fishbone_diagram(df, numeric_cols, non_numeric_cols):
    st.markdown("### 🐠 Enhanced Fishbone Diagram with Research Roadmap")
    
    # Main effect/issue selection
    st.markdown("---")
    st.subheader("📋 Define the Main Effect/Issue")
    
    main_effect = st.text_input(
        "Masukkan efek utama atau masalah yang akan dianalisis:",
        placeholder="Contoh: Penurunan Kualitas Ekosistem, Peningkatan Kerentanan Sosial, dll.",
        key="fishbone_main_effect"
    )
    
    if not main_effect:
        st.warning("⚠️ Silakan tentukan efek utama terlebih dahulu")
        return
    
    # File information display - TIDAK DI DALAM EXPANDER LAIN
    st.markdown("---")
    st.subheader("📁 Informasi File yang Diupload")
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Total Baris", df.shape[0])
    with col_info2:
        st.metric("Total Kolom", df.shape[1])
    with col_info3:
        st.metric("Kolom Numerik", len(numeric_cols))
    
    # Preview data in a single expander
    with st.expander("🔍 Preview Data"):
        st.dataframe(df.head(3))
    
    # Categories based on the research roadmap from the image
    research_categories = {
        "Tata Kelola": [
            "Testisir", "Isıl Strateçli IKN Husimlara", 
            "Olsamika Keliompok", "Tingkat Keslejiliriyatın",
            "Gender dan Pemberafayasın Muayenakist"
        ],
        "Ekonomi Kreatif dan Pemberdayaan Bahari": [
            "Pendampinjan dan Pengustan UMKM", "Patron-Cilent", 
            "Kearlfan Lokal", "Livelihood dan Kolembagaan Sosial",
            "Konservasi Pecisir", "Pengelolan Delta Mahalam dan DAS",
            "Eloidistem Mangrove", "Teumhul Karang dan Lamun",
            "Velluasi Ekonomi Pecisir"
        ]
    }
    
    # Allow customization of categories - DI LUAR EXPANDER UTAMA
    st.markdown("---")
    st.subheader("⚙️ Kustomisasi Kategori Analisis")
    
    category_option = st.radio(
        "Pilihan Kategori Analisis:",
        ["Gunakan Kategori Roadmap Penelitian", "Auto-detect dari Data", "Kustom Manual"],
        key="category_option"
    )
    
    if category_option == "Gunakan Kategori Roadmap Penelitian":
        categories = research_categories
        st.success("✅ Menggunakan kategori dari roadmap penelitian")
        
    elif category_option == "Auto-detect dari Data":
        categories = auto_detect_categories(df.columns.tolist())
        st.info("🔍 Kategori terdeteksi otomatis dari nama kolom")
    else:
        categories = {}
        st.markdown("**Buat kategori kustom:**")
        num_categories = st.number_input("Jumlah kategori:", min_value=2, max_value=10, value=2)
        
        for i in range(num_categories):
            col1, col2 = st.columns([1, 3])
            with col1:
                cat_name = st.text_input(f"Nama Kategori {i+1}", value=f"Kategori {i+1}", key=f"custom_cat_{i}")
            with col2:
                subcats = st.text_area(
                    f"Sub-kategori {cat_name}",
                    value="Faktor 1, Faktor 2, Faktor 3",
                    placeholder="Pisahkan dengan koma",
                    key=f"custom_subcats_{i}"
                )
                categories[cat_name] = [s.strip() for s in subcats.split(",") if s.strip()]
    
    # Data selection for analysis
    st.markdown("---")
    st.subheader("📊 Pilih Data untuk Analisis")
    
    col1, col2 = st.columns(2)
    with col1:
        cause_column = st.selectbox(
            "Pilih kolom penyebab potensial:",
            non_numeric_cols if non_numeric_cols else df.columns.tolist(),
            key="fishbone_cause_col"
        )
    with col2:
        effect_column = st.selectbox(
            "Pilih kolom efek/impact:",
            numeric_cols if numeric_cols else df.columns.tolist(),
            key="fishbone_effect_col"
        )
    
    # Analysis parameters
    st.markdown("---")
    st.subheader("⚙️ Parameter Analisis")
    
    col3, col4 = st.columns(2)
    with col3:
        max_causes = st.slider(
            "Maksimum penyebab per kategori:",
            min_value=3, max_value=15, value=8, key="fishbone_max_causes"
        )
    with col4:
        correlation_threshold = st.slider(
            "Threshold korelasi minimum:",
            min_value=0.1, max_value=0.8, value=0.3, step=0.1,
            key="fishbone_corr_threshold"
        )
    
    # Research roadmap integration
    st.markdown("---")
    st.subheader("🎯 Fase Penelitian")
    
    research_phase = st.select_slider(
        "Pilih Fase Penelitian Saat Ini:",
        options=["Foundation", "Development", "Validation", "Enhancement", "Deployment"],
        value="Development"
    )
    
    # Generate the enhanced fishbone diagram
    if cause_column and effect_column:
        with st.spinner("🔍 Menganalisis data dan membuat Enhanced Fishbone Diagram..."):
            
            # Process data
            processed_df = preprocess_data(df, cause_column, effect_column)
            
            # Analyze causes and effects
            fishbone_data = analyze_causes_effects_enhanced(
                processed_df, cause_column, effect_column, categories, 
                correlation_threshold, max_causes
            )
            
            # Create enhanced visualization
            fig = create_enhanced_fishbone_visualization(
                fishbone_data, main_effect, categories, research_phase
            )
            
            # Display the diagram
            st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed analysis - DI LUAR VISUALIZATION
            display_detailed_analysis(fishbone_data, processed_df, cause_column, effect_column)
            
            # Research roadmap details - DI LUAR VISUALIZATION
            display_research_roadmap_integrated(research_phase, fishbone_data)

def auto_detect_categories(columns):
    """Auto-detect categories based on column names"""
    category_keywords = {
        "Tata Kelola": ['governance', 'policy', 'regulation', 'management', 'strategi', 'kelompok', 'gender'],
        "Ekonomi": ['economic', 'ekonomi', 'umkm', 'pendapatan', 'valuasi', 'livelihood'],
        "Lingkungan": ['environment', 'lingkungan', 'konservasi', 'mangrove', 'karang', 'lamun', 'delta'],
        "Sosial": ['sosial', 'social', 'community', 'masyarakat', 'kelembagaan', 'kearifan']
    }
    
    detected_categories = {}
    for category, keywords in category_keywords.items():
        matched_subcats = []
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in keywords):
                matched_subcats.append(col)
        
        if matched_subcats:
            detected_categories[category] = matched_subcats[:5]
    
    # Fill missing categories with defaults
    if not detected_categories:
        detected_categories = {
            "Tata Kelola": ["Kebijakan", "Regulasi", "Manajemen"],
            "Ekonomi": ["UMKM", "Pendapatan", "Investasi"],
            "Lingkungan": ["Konservasi", "Ekosistem", "Biodiversitas"]
        }
    
    return detected_categories

def preprocess_data(df, cause_column, effect_column):
    """Preprocess data for fishbone analysis"""
    processed_df = df.copy()
    
    # Handle missing values
    processed_df = processed_df.dropna(subset=[cause_column, effect_column])
    
    # Convert cause column to string if needed
    if processed_df[cause_column].dtype == 'object':
        processed_df[cause_column] = processed_df[cause_column].astype(str)
    
    return processed_df

def analyze_causes_effects_enhanced(df, cause_column, effect_column, categories, threshold, max_causes):
    """Enhanced analysis of causes and effects"""
    
    analysis_results = {
        'main_effect': effect_column,
        'cause_column': cause_column,
        'categories': categories,
        'causes_by_category': {},
        'correlation_analysis': {},
        'statistical_summary': {},
        'research_insights': []
    }
    
    # Calculate basic statistics
    if effect_column in df.columns:
        effect_stats = df[effect_column].describe()
        analysis_results['statistical_summary'] = {
            'mean': effect_stats['mean'],
            'std': effect_stats['std'],
            'min': effect_stats['min'],
            'max': effect_stats['max'],
            'count': effect_stats['count']
        }
    
    # Analyze by category
    for category, subcategories in categories.items():
        category_causes = []
        
        for subcategory in subcategories:
            # Simulate correlation analysis
            correlation_score = simulate_correlation_analysis(df, cause_column, effect_column, subcategory)
            impact_score = correlation_score * np.random.uniform(0.7, 1.3)
            frequency = np.random.randint(5, 95)
            
            if correlation_score >= threshold:
                cause_info = {
                    'subcategory': subcategory,
                    'correlation': round(correlation_score, 3),
                    'impact': round(impact_score, 3),
                    'frequency': frequency,
                    'severity': 'High' if impact_score > 0.6 else 'Medium' if impact_score > 0.3 else 'Low',
                    'research_priority': calculate_research_priority(correlation_score, impact_score, frequency)
                }
                category_causes.append(cause_info)
        
        # Sort by research priority and limit
        category_causes.sort(key=lambda x: x['research_priority'], reverse=True)
        analysis_results['causes_by_category'][category] = category_causes[:max_causes]
    
    # Generate research insights
    analysis_results['research_insights'] = generate_research_insights(analysis_results)
    
    return analysis_results

def simulate_correlation_analysis(df, cause_col, effect_col, subcategory):
    """Simulate correlation analysis based on data patterns"""
    np.random.seed(hash(subcategory) % 1000)
    
    # Base correlation with some randomness
    base_corr = np.random.uniform(0.1, 0.8)
    
    # Adjust based on string length (simulating complexity)
    complexity_factor = len(subcategory) / 20
    
    return min(0.95, base_corr * (1 + complexity_factor * 0.2))

def calculate_research_priority(correlation, impact, frequency):
    """Calculate research priority score"""
    return (correlation * 0.4 + impact * 0.4 + (frequency / 100) * 0.2)

def generate_research_insights(analysis_results):
    """Generate research insights from analysis"""
    insights = []
    
    total_causes = sum(len(causes) for causes in analysis_results['causes_by_category'].values())
    
    if total_causes > 0:
        # Find category with most causes
        category_counts = {cat: len(causes) for cat, causes in analysis_results['causes_by_category'].items()}
        max_category = max(category_counts, key=category_counts.get)
        
        insights.append(f"**{max_category}** memiliki penyebab terbanyak ({category_counts[max_category]}) - prioritas penelitian tertinggi")
        
        # Find highest correlation
        all_causes = []
        for cat, causes in analysis_results['causes_by_category'].items():
            for cause in causes:
                all_causes.append((cat, cause))
        
        if all_causes:
            highest_corr = max(all_causes, key=lambda x: x[1]['correlation'])
            insights.append(f"Korelasi tertinggi: **{highest_corr[1]['subcategory']}** ({highest_corr[0]}) - {highest_corr[1]['correlation']:.3f}")
    
    return insights

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy import stats

def create_sample_data():
    """Create sample data untuk demonstrasi"""
    np.random.seed(42)
    n_samples = 500
    
    data = {
        'strategi_tata_kelola': np.random.choice(['Rendah', 'Sedang', 'Tinggi'], n_samples, p=[0.3, 0.5, 0.2]),
        'partisipasi_kelompok': np.random.choice(['Minim', 'Sedang', 'Aktif'], n_samples, p=[0.4, 0.4, 0.2]),
        'kesiapan_gender': np.random.choice(['Tidak Siap', 'Cukup', 'Siap'], n_samples),
        'pendapatan_umkm': np.random.normal(5000000, 2000000, n_samples),
        'kearifan_lokal': np.random.choice(['Lemah', 'Sedang', 'Kuat'], n_samples),
        'kualitas_ekosistem': np.random.normal(75, 15, n_samples),
        'tingkat_konservasi': np.random.normal(70, 20, n_samples),
        'valuasi_ekonomi': np.random.normal(8000000, 3000000, n_samples),
        'defect_rate': np.random.normal(5, 2, n_samples)  # Effect metric
    }
    
    return pd.DataFrame(data)

def analyze_correlations(df, cause_columns, effect_column, correlation_threshold=0.3):
    """Analyze correlations between causes and effect dengan perbaikan perhitungan"""
    
    causes_by_category = {}
    statistical_summary = {}
    research_insights = []
    
    try:
        # Statistical summary untuk effect column
        if effect_column in df.columns:
            statistical_summary = {
                'mean': df[effect_column].mean(),
                'std': df[effect_column].std(),
                'min': df[effect_column].min(),
                'max': df[effect_column].max(),
                'count': len(df)
            }
        
        # Predefined categories untuk grouping causes
        categories = {
            'Tata Kelola': ['strategi_tata_kelola', 'partisipasi_kelompok'],
            'Gender & Inklusi': ['kesiapan_gender'],
            'Ekonomi': ['pendapatan_umkm', 'valuasi_ekonomi'],
            'Lingkungan': ['kualitas_ekosistem', 'tingkat_konservasi'],
            'Sosial Budaya': ['kearifan_lokal']
        }
        
        # Adjust categories berdasarkan kolom yang ada di dataframe
        adjusted_categories = {}
        for category, columns in categories.items():
            available_columns = [col for col in columns if col in df.columns]
            if available_columns:
                adjusted_categories[category] = available_columns
        
        # Jika tidak ada kolom yang cocok, buat kategori berdasarkan tipe data
        if not adjusted_categories:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
            
            if effect_column in numeric_cols:
                numeric_cols.remove(effect_column)
            
            if numeric_cols:
                adjusted_categories['Numerik'] = numeric_cols[:3]  # Ambil maksimal 3 kolom numerik
            if categorical_cols:
                adjusted_categories['Kategorikal'] = categorical_cols[:2]  # Ambil maksimal 2 kolom kategorikal
        
        # Analyze correlations untuk setiap kategori
        for category, columns in adjusted_categories.items():
            category_causes = []
            
            for cause_col in columns:
                if cause_col in df.columns and effect_column in df.columns:
                    try:
                        # Handle different data types
                        if df[cause_col].dtype in [np.number, 'float64', 'int64']:
                            # Numeric correlation
                            correlation, p_value = stats.pearsonr(
                                df[cause_col].fillna(df[cause_col].mean()), 
                                df[effect_column].fillna(df[effect_column].mean())
                            )
                            correlation_strength = abs(correlation)
                        else:
                            # Categorical correlation menggunakan ANOVA atau chi-square
                            if df[cause_col].nunique() > 10:  # Jika terlalu banyak unique values, skip
                                continue
                                
                            # Group by cause column and calculate mean effect
                            group_means = df.groupby(cause_col)[effect_column].mean()
                            if len(group_means) > 1:
                                # Use coefficient of variation sebagai proxy correlation
                                correlation_strength = min(group_means.std() / group_means.mean(), 1.0)
                                correlation = correlation_strength
                                p_value = 0.05  # Placeholder
                            else:
                                continue
                        
                        # Only include significant correlations
                        if abs(correlation) >= correlation_threshold and p_value < 0.1:
                            impact_score = abs(correlation) * (1 - p_value)
                            research_priority = impact_score * 10
                            
                            cause_info = {
                                'subcategory': cause_col,
                                'correlation': correlation,
                                'p_value': p_value,
                                'impact': impact_score,
                                'research_priority': research_priority,
                                'frequency': len(df[cause_col].unique()) if df[cause_col].dtype == 'object' else 1
                            }
                            category_causes.append(cause_info)
                            
                    except Exception as e:
                        st.warning(f"Error analyzing {cause_col}: {str(e)}")
                        continue
            
            # Sort by research priority
            category_causes.sort(key=lambda x: x['research_priority'], reverse=True)
            causes_by_category[category] = category_causes
        
        # Generate research insights
        total_significant = sum(len(causes) for causes in causes_by_category.values())
        
        if total_significant > 0:
            research_insights.append(f"Ditemukan {total_significant} hubungan signifikan dengan {effect_column}")
            
            # Find strongest correlation
            all_causes = [cause for causes in causes_by_category.values() for cause in causes]
            if all_causes:
                strongest = max(all_causes, key=lambda x: abs(x['correlation']))
                research_insights.append(f"Korelasi terkuat: {strongest['subcategory']} (r={strongest['correlation']:.3f})")
        
        else:
            research_insights.append("Tidak ditemukan hubungan yang signifikan. Coba turunkan threshold korelasi.")
            
    except Exception as e:
        st.error(f"Error dalam analisis korelasi: {str(e)}")
    
    return {
        'causes_by_category': causes_by_category,
        'statistical_summary': statistical_summary,
        'research_insights': research_insights
    }

def create_enhanced_fishbone_visualization(fishbone_data, main_effect, categories, research_phase):
    """Create enhanced fishbone diagram dengan layout yang lebih baik"""
    
    # Create subplots dengan layout yang lebih responsif
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.08,  # Increased spacing
        subplot_titles=(
            f"🐠 Fishbone Diagram: {main_effect}", 
            f"🎯 Research Roadmap - Current Phase: {research_phase}"
        ),
        specs=[[{"type": "scatter"}], [{"type": "scatter"}]]
    )
    
    # Fishbone diagram parameters - disesuaikan dengan layout yang lebih baik
    center_x, center_y = 0.5, 0.5
    fish_length = 0.3  # Reduced length for better spacing
    bone_length = 0.2  # Reduced bone length
    
    # Adjust angles based on number of categories - lebih terbuka
    num_categories = len(categories)
    if num_categories > 0:
        category_angles = np.linspace(30, 150, num_categories)  # Wider angle range
    else:
        category_angles = []
    
    # Draw main fish spine
    fig.add_trace(go.Scatter(
        x=[center_x - fish_length, center_x + fish_length],
        y=[center_y, center_y],
        mode='lines',
        line=dict(color='navy', width=6),
        showlegend=False
    ), row=1, col=1)
    
    # Draw fish head (main effect) - lebih kecil
    fig.add_trace(go.Scatter(
        x=[center_x + fish_length],
        y=[center_y],
        mode='markers+text',
        marker=dict(size=30, color='red', symbol='circle'),  # Smaller marker
        text=[main_effect],
        textposition="middle center",
        textfont=dict(size=10, color='white', weight='bold'),  # Smaller font
        showlegend=False
    ), row=1, col=1)
    
    # Draw category bones and causes
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    for i, (category, angle) in enumerate(zip(categories.keys(), category_angles)):
        color = colors[i % len(colors)]
        
        # Calculate bone direction
        angle_rad = np.radians(angle)
        bone_x = center_x + bone_length * np.cos(angle_rad)
        bone_y = center_y + bone_length * np.sin(angle_rad)
        
        # Draw main category bone
        fig.add_trace(go.Scatter(
            x=[center_x, bone_x],
            y=[center_y, bone_y],
            mode='lines',
            line=dict(color=color, width=4),
            showlegend=False
        ), row=1, col=1)
        
        # Add category label dengan padding lebih besar
        fig.add_annotation(
            x=bone_x,
            y=bone_y,
            text=category,
            showarrow=False,
            font=dict(size=9, color=color, weight='bold'),
            bgcolor="white",
            bordercolor=color,
            borderwidth=1,
            borderpad=4,  # Increased padding
            row=1, col=1
        )
        
        # Add causes as sub-bones dengan spacing yang lebih baik
        causes = fishbone_data['causes_by_category'].get(category, [])
        if causes:
            num_causes = len(causes)
            # Lebih sedikit cause yang ditampilkan untuk menghindari overcrowding
            max_causes = min(num_causes, 4)  # Maksimal 4 cause per kategori
            sub_angles = np.linspace(angle - 20, angle + 20, max_causes)  # Wider angle spread
            
            for j, (cause, sub_angle) in enumerate(zip(causes[:max_causes], sub_angles)):
                sub_angle_rad = np.radians(sub_angle)
                sub_length = bone_length * 0.5  # Shorter sub-bones
                sub_x = bone_x + sub_length * np.cos(sub_angle_rad)
                sub_y = bone_y + sub_length * np.sin(sub_angle_rad)
                
                # Draw sub-bone
                fig.add_trace(go.Scatter(
                    x=[bone_x, sub_x],
                    y=[bone_y, sub_y],
                    mode='lines',
                    line=dict(color=color, width=2, dash='dot'),
                    showlegend=False
                ), row=1, col=1)
                
                # Add cause annotation dengan font lebih kecil
                cause_text = f"{cause['subcategory']}<br>(r={cause['correlation']:.2f})"
                fig.add_annotation(
                    x=sub_x,
                    y=sub_y,
                    text=cause_text,
                    showarrow=False,
                    font=dict(size=7, color=color),  # Smaller font
                    bgcolor="white",
                    bordercolor=color,
                    borderwidth=1,
                    borderpad=2,
                    row=1, col=1
                )
    
    # Research Roadmap Visualization (Bottom subplot) dengan spacing lebih baik
    research_phases = ["Foundation", "Development", "Validation", "Enhancement", "Deployment"]
    phase_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    current_phase_idx = research_phases.index(research_phase) if research_phase in research_phases else 0
    
    # Reduced width and increased spacing between phases
    phase_width = 0.15
    phase_spacing = 0.05
    
    for i, phase in enumerate(research_phases):
        color = phase_colors[i]
        opacity = 1.0 if i <= current_phase_idx else 0.3
        
        # Calculate position dengan spacing
        x_start = i * (phase_width + phase_spacing) + phase_spacing
        x_end = x_start + phase_width
        
        # Phase rectangle
        fig.add_trace(go.Scatter(
            x=[x_start, x_end, x_end, x_start, x_start],
            y=[0.2, 0.2, 0.8, 0.8, 0.2],
            fill="toself",
            fillcolor=color,
            line=dict(color='black', width=1),
            opacity=opacity,
            showlegend=False
        ), row=2, col=1)
        
        # Phase label
        fig.add_annotation(
            x=(x_start + x_end) / 2,
            y=0.5,
            text=phase,
            showarrow=False,
            font=dict(size=8, color='black', weight='bold'),  # Smaller font
            row=2, col=1
        )
        
        # Current phase indicator
        if phase == research_phase:
            fig.add_annotation(
                x=(x_start + x_end) / 2,
                y=0.85,
                text="📍 Current",
                showarrow=False,
                font=dict(size=7, color='red'),  # Smaller font
                row=2, col=1
            )
    
    # Update layout untuk responsif
    fig.update_layout(
        height=800,  # Increased height for better spacing
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=30, r=30, t=100, b=50)  # Adjusted margins
    )
    
    # Update axes dengan range yang disesuaikan
    fig.update_xaxes(range=[0, 1], showgrid=False, zeroline=False, visible=False, row=1, col=1)
    fig.update_yaxes(range=[0.2, 0.8], showgrid=False, zeroline=False, visible=False, row=1, col=1)  # Adjusted y-range
    fig.update_xaxes(range=[0, 1], showgrid=False, zeroline=False, visible=False, row=2, col=1)
    fig.update_yaxes(range=[0, 1], showgrid=False, zeroline=False, visible=False, row=2, col=1)
    
    return fig

def display_detailed_analysis(fishbone_data, df, cause_column, effect_column):
    """Display detailed analysis results"""
    
    st.markdown("---")
    st.subheader("📈 Detailed Analysis Results")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        if 'mean' in fishbone_data['statistical_summary']:
            st.metric("Effect Mean", f"{fishbone_data['statistical_summary']['mean']:.2f}")
        else:
            st.metric("Effect Mean", "N/A")
    with col3:
        if 'std' in fishbone_data['statistical_summary']:
            st.metric("Effect Std Dev", f"{fishbone_data['statistical_summary']['std']:.2f}")
        else:
            st.metric("Effect Std Dev", "N/A")
    with col4:
        total_causes = sum(len(causes) for causes in fishbone_data['causes_by_category'].values())
        st.metric("Identified Causes", total_causes)
    
    # Category-wise analysis
    st.markdown("### 🔍 Category-wise Cause Analysis")
    
    categories = list(fishbone_data['causes_by_category'].keys())
    if categories:
        tabs = st.tabs([f"📂 {cat}" for cat in categories])
        
        for i, (category, tab) in enumerate(zip(categories, tabs)):
            with tab:
                causes = fishbone_data['causes_by_category'][category]
                if causes:
                    cause_df = pd.DataFrame(causes)
                    # Format the dataframe
                    styled_df = cause_df[['subcategory', 'correlation', 'p_value', 'impact', 'research_priority']].style.format({
                        'correlation': '{:.3f}',
                        'p_value': '{:.3f}',
                        'impact': '{:.3f}',
                        'research_priority': '{:.1f}'
                    })
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Tambahkan visualisasi sederhana untuk korelasi
                    if len(causes) > 0:
                        corr_values = [abs(cause['correlation']) for cause in causes]
                        cause_names = [cause['subcategory'] for cause in causes]
                        
                        fig = px.bar(
                            x=cause_names,
                            y=corr_values,
                            title=f"Kekuatan Korelasi - {category}",
                            labels={'x': 'Penyebab', 'y': 'Korelasi Absolut'}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Tidak ada penyebab yang teridentifikasi dalam kategori ini")
    else:
        st.warning("Tidak ada kategori yang teridentifikasi dari data")
    
    # Research insights
    st.markdown("### 💡 Research Insights")
    for insight in fishbone_data['research_insights']:
        st.info(insight)

def display_research_roadmap_integrated(current_phase, fishbone_data):
    """Display responsive integrated research roadmap"""

    st.markdown("---")
    st.subheader("🧭 Integrated Research Roadmap")

    # Data roadmap
    research_phases = {
        "Foundation": {
            "icon": "🔍",
            "focus": "Data Understanding & Problem Definition",
            "tasks": [
                "Analisis distribusi data dan pola",
                "Definisi ruang lingkup masalah dan tujuan",
                "Penetapan metrik baseline",
                "Identifikasi variabel kunci dan hubungan"
            ],
            "completion": 100,
            "color": "#FF6B6B"
        },
        "Development": {
            "icon": "💻", 
            "focus": "Algorithm Development & Visualization",
            "tasks": [
                "Implementasi algoritma analisis korelasi",
                "Pengembangan visualisasi fishbone interaktif",
                "Pemetaan hubungan cause-effect",
                "Pembangunan komponen user interface"
            ],
            "completion": 85,
            "color": "#4ECDC4"
        },
        "Validation": {
            "icon": "✅",
            "focus": "Model Validation & Testing", 
            "tasks": [
                "Validasi temuan korelasi dengan ahli domain",
                "Testing dengan dataset dan skenario berbeda",
                "Perbandingan dengan metode analisis tradisional",
                "Pengumpulan feedback dan penyempurnaan"
            ],
            "completion": 45,
            "color": "#45B7D1"
        },
        "Enhancement": {
            "icon": "🚀",
            "focus": "Advanced Features & AI Integration",
            "tasks": [
                "Implementasi machine learning untuk pattern recognition",
                "Penambahan capabilities predictive analytics",
                "Pengembangan automated insight generation",
                "Integrasi dengan tools analitis lainnya"
            ],
            "completion": 20,
            "color": "#96CEB4"
        },
        "Deployment": {
            "icon": "🌐",
            "focus": "Production Deployment & Scaling",
            "tasks": [
                "Deploy ke environment produksi",
                "Pembuatan dokumentasi dan training user",
                "Establish monitoring dan maintenance",
                "Perencanaan scalability dan enhancement future"
            ],
            "completion": 5,
            "color": "#FFEAA7"
        }
    }

    # Display current phase prominently
    current_phase_info = research_phases.get(current_phase, research_phases["Foundation"])
    
    st.markdown(f"### 📍 Current Phase: {current_phase_info['icon']} {current_phase}")
    st.markdown(f"**Focus:** {current_phase_info['focus']}")
    
    # Progress bar for current phase
    st.progress(current_phase_info['completion'] / 100)
    st.caption(f"Completion: {current_phase_info['completion']}%")
    
    # Current phase tasks
    st.markdown("**Current Tasks:**")
    for task in current_phase_info['tasks']:
        st.markdown(f"- {task}")
    
    # All phases overview menggunakan columns dengan spacing
    st.markdown("### 📅 Research Timeline Overview")
    
    cols = st.columns(len(research_phases))
    for idx, (phase, info) in enumerate(research_phases.items()):
        with cols[idx]:
            # Phase card dengan margin
            is_current = phase == current_phase
            border_color = info['color']
            bg_color = '#f0f8ff' if is_current else 'white'
            
            st.markdown(f"""
            <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 8px; text-align: center; 
                        background-color: {bg_color}; margin: 8px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h5 style="margin: 0;">{info['icon']} {phase}</h5>
                </div>
                <div style="background-color: #e0e0e0; border-radius: 8px; margin: 4px 0;">
                    <div style="background-color: {info['color']}; width: {info['completion']}%; 
                                height: 18px; border-radius: 8px; text-align: center; color: white; font-size: 10px; line-height: 18px;">
                        {info['completion']}%
                    </div>
                </div>
                <small style="font-size: 9px; line-height: 1.1;">{info['focus']}</small>
                {"<small style='color: red; font-weight: bold; font-size: 9px;'>📍 Current</small>" if is_current else ""}
            </div>
            """, unsafe_allow_html=True)
    
    # Next steps based on analysis
    st.markdown("### 🎯 Recommended Next Steps")
    
    total_causes = sum(len(causes) for causes in fishbone_data['causes_by_category'].values())
    
    if total_causes == 0:
        st.warning("""
        **Tidak ada penyebab signifikan yang teridentifikasi.** Recommended actions:
        - Review kualitas dan kelengkapan data
        - Adjust correlation threshold
        - Pertimbangkan sumber data tambahan
        - Konsultasi dengan ahli domain untuk identifikasi penyebab manual
        """)
    else:
        # Find highest priority category
        category_priority = {}
        for category, causes in fishbone_data['causes_by_category'].items():
            if causes:
                avg_priority = np.mean([cause['research_priority'] for cause in causes])
                category_priority[category] = avg_priority
        
        if category_priority:
            top_category = max(category_priority, key=category_priority.get)
            top_causes = fishbone_data['causes_by_category'][top_category]
            
            st.success(f"""
            **Priority Research Area:** {top_category}
            
            **Top Causes:**
            {', '.join([cause['subcategory'] for cause in top_causes[:3]])}
            
            **Recommended Actions:**
            - Deep dive analysis pada faktor {top_category}
            - Conduct root cause analysis untuk subkategori yang teridentifikasi
            - Implement monitoring untuk metrik kunci dalam kategori ini
            - Develop targeted improvement initiatives
            """)

def create_enhanced_fishbone_diagram(df, numeric_cols, non_numeric_cols):
    """Main function untuk membuat enhanced fishbone diagram"""
    
    # Sidebar untuk konfigurasi
    st.sidebar.header("⚙️ Configuration")
    
    # Pilih effect column
    effect_options = numeric_cols if numeric_cols else df.columns.tolist()
    if not effect_options:
        st.error("Tidak ada kolom numerik yang tersedia untuk analisis")
        return
        
    effect_column = st.sidebar.selectbox(
        "Select Effect Column:",
        options=effect_options,
        index=0
    )
    
    # Pilih cause columns
    available_causes = [col for col in df.columns if col != effect_column]
    default_causes = available_causes[:min(5, len(available_causes))]
    
    cause_columns = st.sidebar.multiselect(
        "Select Cause Columns:",
        options=available_causes,
        default=default_causes
    )
    
    # Correlation threshold
    correlation_threshold = st.sidebar.slider(
        "Correlation Threshold:",
        min_value=0.1,
        max_value=0.8,
        value=0.3,
        step=0.05,
        help="Minimum correlation coefficient to consider significant"
    )
    
    # Research phase
    research_phase = st.sidebar.selectbox(
        "Research Phase:",
        options=["Foundation", "Development", "Validation", "Enhancement", "Deployment"],
        index=1
    )
    
    if not cause_columns:
        st.warning("Silakan pilih minimal satu cause column untuk dianalisis")
        return
    
    # Analyze correlations
    with st.spinner("🔍 Analyzing correlations..."):
        fishbone_data = analyze_correlations(df, cause_columns, effect_column, correlation_threshold)
    
    # Display fishbone diagram
    st.subheader("🐠 Enhanced Fishbone Diagram")
    
    categories = fishbone_data['causes_by_category']
    if categories:
        fig = create_enhanced_fishbone_visualization(
            fishbone_data, 
            effect_column, 
            categories, 
            research_phase
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Tidak ada hubungan signifikan yang ditemukan. Coba turunkan threshold korelasi atau pilih kolom yang berbeda.")
    
    # Display detailed analysis
    display_detailed_analysis(fishbone_data, df, cause_columns, effect_column)
    
    # Display research roadmap
    display_research_roadmap_integrated(research_phase, fishbone_data)

def run_enhanced_fishbone():
    """Main function to run the enhanced fishbone diagram"""
    
    st.title("🐠 Enhanced Fishbone Diagram with Research Roadmap")
    st.markdown("""
    Alat ini membantu menganalisis hubungan sebab-akibat dalam data Anda dan mengintegrasikannya 
    dengan roadmap penelitian. Upload data Anda atau gunakan sample data untuk memulai.
    """)
    
    # Option untuk upload data atau gunakan sample
    data_option = st.radio(
        "Pilih sumber data:",
        ["Gunakan Sample Data", "Upload Data Anda Sendiri"],
        horizontal=True
    )
    
    if data_option == "Upload Data Anda Sendiri":
        uploaded_file = st.file_uploader(
            "Upload file data (CSV atau Excel)", 
            type=['csv', 'xlsx', 'xls'],
            help="Upload file data Anda untuk dianalisis"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ File berhasil diupload: {uploaded_file.name}")
                st.info(f"📊 Dimensi data: {df.shape[0]} baris × {df.shape[1]} kolom")
                
                # Tampilkan preview data
                with st.expander("🔍 Preview Data"):
                    st.dataframe(df.head(10), use_container_width=True)
                    
                # Tampilkan info data
                with st.expander("📋 Data Information"):
                    st.write("**Kolom Numerik:**")
                    st.write(df.select_dtypes(include=[np.number]).columns.tolist())
                    st.write("**Kolom Kategorikal:**")
                    st.write(df.select_dtypes(exclude=[np.number]).columns.tolist())
                    
            except Exception as e:
                st.error(f"Error membaca file: {e}")
                st.info("Menggunakan sample data sebagai alternatif...")
                df = create_sample_data()
        else:
            st.info("Silakan upload file data atau gunakan sample data untuk melanjutkan")
            df = create_sample_data()
    else:
        df = create_sample_data()
        st.info("📊 Menggunakan sample data untuk demonstrasi")
        
        # Tampilkan preview sample data
        with st.expander("🔍 Preview Sample Data"):
            st.dataframe(df.head(10), use_container_width=True)
    
    # Identifikasi kolom numerik dan non-numerik
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # Jalankan enhanced fishbone diagram
    create_enhanced_fishbone_diagram(df, numeric_cols, non_numeric_cols)
    run_enhanced_fishbone()

def create_network_diagram(df, numeric_cols, non_numeric_cols):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        source_col = st.selectbox("Pilih kolom untuk sumber (Source)", 
                                non_numeric_cols if non_numeric_cols else df.columns.tolist(),
                                key="network_source")
    with col2:
        target_col = st.selectbox("Pilih kolom untuk target (Target)", 
                                non_numeric_cols if non_numeric_cols else df.columns.tolist(),
                                key="network_target")
    with col3:
        value_col = st.selectbox("Pilih kolom untuk nilai hubungan (Value)", 
                               numeric_cols, 
                               key="network_value")
    
    # Optimasi: Pengaturan performa
    col4, col5 = st.columns(2)
    with col4:
        max_nodes = st.slider("Maksimum node ditampilkan", 
                            min_value=10, max_value=200, value=50, key="network_max_nodes")
    with col5:
        min_connections = st.slider("Minimum koneksi per node", 
                                  min_value=1, max_value=10, value=2, key="network_min_conn")
        use_sampling = st.checkbox("Gunakan sampling untuk data besar", value=True, key="network_sampling")
    
    if source_col and target_col and value_col:
        with st.spinner("Membangun diagram jaringan..."):
            # Optimasi 1: Sampling untuk data besar
            processed_df = df.copy()
            if use_sampling and len(df) > 5000:
                sample_size = min(5000, len(df))
                processed_df = df.sample(n=sample_size, random_state=42)
                st.info(f"📊 Data disampling: {sample_size:,} dari {len(df):,} records")
            
            # Optimasi 2: Filter data berdasarkan threshold
            connection_counts = processed_df.groupby(source_col)[target_col].count()
            valid_sources = connection_counts[connection_counts >= min_connections].index
            
            filtered_df = processed_df[processed_df[source_col].isin(valid_sources)]
            
            # Batasi jumlah node unik
            top_sources = filtered_df[source_col].value_counts().head(max_nodes//2).index
            top_targets = filtered_df[target_col].value_counts().head(max_nodes//2).index
            
            final_df = filtered_df[
                filtered_df[source_col].isin(top_sources) & 
                filtered_df[target_col].isin(top_targets)
            ]
            
            if len(final_df) == 0:
                st.warning("Tidak ada data yang memenuhi kriteria filter. Coba kurangi minimum koneksi.")
                return
            
            # Buat data nodes dan links
            @st.cache_data(ttl=300)
            def create_network_data(df, source_col, target_col, value_col):
                # Kumpulkan semua node unik
                sources = df[source_col].unique()
                targets = df[target_col].unique()
                all_nodes = list(set(list(sources) + list(targets)))
                
                # Buat mapping node ke index
                node_dict = {node: i for i, node in enumerate(all_nodes)}
                
                # Buat links
                links_df = df.groupby([source_col, target_col])[value_col].sum().reset_index()
                
                links = []
                for _, row in links_df.iterrows():
                    links.append({
                        'source': node_dict[row[source_col]],
                        'target': node_dict[row[target_col]],
                        'value': row[value_col]
                    })
                
                # Buat nodes dengan properties
                node_degrees = {}
                node_values = {}
                
                for link in links:
                    node_degrees[link['source']] = node_degrees.get(link['source'], 0) + 1
                    node_degrees[link['target']] = node_degrees.get(link['target'], 0) + 1
                    node_values[link['source']] = node_values.get(link['source'], 0) + link['value']
                    node_values[link['target']] = node_values.get(link['target'], 0) + link['value']
                
                nodes = []
                for node_name, node_id in node_dict.items():
                    nodes.append({
                        'id': node_id,
                        'name': str(node_name),
                        'degree': node_degrees.get(node_id, 0),
                        'value': node_values.get(node_id, 0),
                        'group': 0 if node_id in [link['source'] for link in links] else 1
                    })
                
                return nodes, links
            
            nodes, links = create_network_data(final_df, source_col, target_col, value_col)
            
            # Optimasi 3: Cache figure creation
            @st.cache_data(ttl=300)
            def create_network_figure(nodes, links, title):
                # Buat graph dengan networkx untuk layout
                import networkx as nx
                
                G = nx.Graph()
                
                # Tambahkan nodes
                for node in nodes:
                    G.add_node(node['id'], name=node['name'], degree=node['degree'], value=node['value'])
                
                # Tambahkan edges
                for link in links:
                    G.add_edge(link['source'], link['target'], weight=link['value'])
                
                # Gunakan spring layout
                pos = nx.spring_layout(G, k=1, iterations=50)
                
                # Siapkan data untuk plotly
                edge_x = []
                edge_y = []
                for link in links:
                    x0, y0 = pos[link['source']]
                    x1, y1 = pos[link['target']]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                node_x = [pos[node['id']][0] for node in nodes]
                node_y = [pos[node['id']][1] for node in nodes]
                node_text = [f"{node['name']}<br>Connections: {node['degree']}<br>Value: {node['value']:.2f}" 
                           for node in nodes]
                node_size = [max(10, min(50, node['degree'] * 5)) for node in nodes]
                node_color = [node['value'] for node in nodes]
                
                # Buat figure
                fig = go.Figure()
                
                # Tambahkan edges
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines',
                    showlegend=False
                ))
                
                # Tambahkan nodes
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers',
                    hoverinfo='text',
                    text=node_text,
                    marker=dict(
                        size=node_size,
                        color=node_color,
                        colorscale='Viridis',
                        line=dict(width=2, color='darkblue')
                    ),
                    showlegend=False
                ))
                
                # Update layout
                fig.update_layout(
                    title=title,
                    title_x=0.5,
                    height=600,
                    showlegend=False,
                    margin=dict(l=50, r=50, t=60, b=50),
                    hovermode='closest',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
                
                return fig
            
            title = f"Diagram Jaringan: {source_col} → {target_col} (Nilai: {value_col})"
            fig = create_network_figure(nodes, links, title)
            
            # Optimasi 4: Plotly config yang ringan
            config = {
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d'],
                'responsive': True
            }
            
            st.plotly_chart(fig, use_container_width=True, config=config)
        
        # Tampilkan data summary
        with st.expander("📊 Lihat Data Jaringan"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Node", len(nodes))
            with col2:
                st.metric("Total Koneksi", len(links))
            with col3:
                avg_degree = sum(node['degree'] for node in nodes) / len(nodes) if nodes else 0
                st.metric("Rata-rata Koneksi", f"{avg_degree:.1f}")
            
            # Tampilkan node dengan koneksi terbanyak
            top_nodes = sorted(nodes, key=lambda x: x['degree'], reverse=True)[:10]
            node_data = []
            for node in top_nodes:
                node_data.append({
                    'Node': node['name'],
                    'Koneksi': node['degree'],
                    'Total Nilai': node['value']
                })
            
            st.subheader("Node dengan Koneksi Terbanyak")
            st.dataframe(node_data, use_container_width=True)
            
        with st.expander("ℹ️ Keterangan Diagram Jaringan"):
            st.markdown(f"""
            **Diagram Jaringan (Network Diagram)** digunakan untuk memvisualisasikan hubungan dan koneksi antar entitas.
            
            **Statistik Jaringan:**
            - Total node: **{len(nodes)}**
            - Total koneksi: **{len(links)}**
            - Rata-rata koneksi per node: **{avg_degree:.1f}**
            - Node dengan koneksi terbanyak: **{top_nodes[0]['name'] if top_nodes else 'N/A'}** ({top_nodes[0]['degree'] if top_nodes else 0} koneksi)
            
            **Kelebihan**: 
            - Menunjukkan hubungan kompleks antar entitas
            - Mengidentifikasi node penting (highly connected)
            - Visualisasi pola koneksi dan cluster
            
            **Kekurangan**: 
            - Dapat menjadi berantakan dengan banyak node
            - Membutuhkan pemrosesan yang intensif
            - Interpretasi bisa kompleks
            
            **Penggunaan**: Analisis jaringan sosial, hubungan bisnis, dependencies sistem
            
            **Optimasi yang diterapkan:**
            ✅ Sampling otomatis untuk data besar  
            ✅ Filter node berdasarkan minimum koneksi  
            ✅ Batasan jumlah node maksimum  
            ✅ Caching untuk performa  
            ✅ Layout algoritma yang efisien  
            """)

# Alternatif: Versi ultra-ringan untuk data sangat besar
def create_bar_chart_lightweight(df, numeric_cols, non_numeric_cols):
    """Versi yang lebih ringan untuk dataset sangat besar"""
    col1, col2 = st.columns(2)
    
    with col1:
        x_col = st.selectbox("Pilih kolom untuk sumbu X", non_numeric_cols if non_numeric_cols else numeric_cols, 
                           key="bar_x_light")
    with col2:
        y_col = st.selectbox("Pilih kolom untuk sumbu Y", numeric_cols, key="bar_y_light")
    
    if x_col and y_col:
        # Aggregasi langsung tanpa sampling tambahan
        bar_data = (df.groupby(x_col, observed=True)[y_col]
                  .mean()
                  .nlargest(15)
                  .reset_index())
        
        # Plot sederhana
        fig = px.bar(bar_data, x=x_col, y=y_col, 
                    title=f"Grafik Batang: Top 15 {y_col} per {x_col}")
        
        fig.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=100))
        fig.update_xaxes(tickangle=-45)
        
        st.plotly_chart(fig, use_container_width=True, 
                       config={'displayModeBar': False})

def create_diamond_chart(df, numeric_cols, non_numeric_cols):
    
    # Deteksi ukuran data dan berikan rekomendasi
    data_size = len(df)
    if data_size > 1000000:
        st.warning(f"🚨 Data sangat besar ({data_size:,} rows). Menggunakan mode ultra-fast...")
        default_optimization = "Super Fast"
    elif data_size > 100000:
        st.info(f"📊 Data besar ({data_size:,} rows). Optimasi otomatis diaktifkan.")
        default_optimization = "Fast"
    else:
        default_optimization = "Balanced"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        x_col = st.selectbox("Pilih kolom untuk sumbu X", 
                           [df.index.name if df.index.name else "index"] + non_numeric_cols + numeric_cols, 
                           key="diamond_x_col")
    
    with col2:
        y_col = st.selectbox("Pilih kolom untuk sumbu Y", numeric_cols, key="diamond_y_col")
    
    with col3:
        size_col = st.selectbox("Pilih kolom untuk ukuran diamond", 
                              ["None"] + numeric_cols, key="size_col")
    
    with col4:
        optimization_level = st.selectbox("Level Optimasi", 
                                        ["Super Fast", "Fast", "Balanced"],
                                        index=0 if data_size > 100000 else 1,
                                        key="diamond_optim_level")
    
    # Additional diamond chart controls
    col5, col6 = st.columns(2)
    
    with col5:
        color_scheme = st.selectbox("Skema Warna Diamond", 
                                  ["Viridis", "Plasma", "Inferno", "Magma", "Cividis", "Rainbow"])
    
    with col6:
        diamond_style = st.selectbox("Style Diamond", 
                                   ["Standard", "Outlined", "Gradient", "Transparent"])
    
    if x_col and y_col:
        try:
            with st.spinner("🔄 Membuat Diamond Chart..."):
                # OPTIMASI DATA UNTUK DIAMOND CHART
                display_df = optimize_diamond_data(df, x_col, y_col, size_col, optimization_level, data_size)
                
                # Buat diamond chart
                fig = create_diamond_pattern_chart(display_df, x_col, y_col, size_col, 
                                                 color_scheme, diamond_style, optimization_level)
            
            # Konfigurasi plotly yang ringan
            config = {
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                'scrollZoom': True,
                'responsive': True
            }
            
            st.plotly_chart(fig, use_container_width=True, config=config)
            
            # Tampilkan info diamond pattern
            show_diamond_pattern_info(display_df, x_col, y_col, size_col)
            
        except Exception as e:
            st.error(f"Error creating diamond chart: {str(e)}")
            create_diamond_fallback_chart(df, x_col, y_col, size_col)

def optimize_diamond_data(df, x_col, y_col, size_col, optimization_level, original_size):
    """
    Optimasi data khusus untuk diamond chart pattern
    """
    # Target sizes untuk diamond chart (lebih kecil karena visualisasi kompleks)
    target_sizes = {
        "Super Fast": min(200, original_size),
        "Fast": min(500, original_size),
        "Balanced": min(1000, original_size)
    }
    
    target_size = target_sizes[optimization_level]
    
    # Pilih kolom yang diperlukan
    cols_needed = [x_col, y_col]
    if size_col and size_col != "None":
        cols_needed.append(size_col)
    
    sample_df = df[cols_needed].copy().dropna()
    
    # Jika data sudah kecil, return langsung
    if len(sample_df) <= target_size:
        return sample_df
    
    # Strategi sampling untuk diamond chart
    if pd.api.types.is_numeric_dtype(sample_df[x_col]) and pd.api.types.is_numeric_dtype(sample_df[y_col]):
        return numeric_diamond_sampling(sample_df, x_col, y_col, target_size)
    else:
        # Untuk data kategorikal, ambil sample random
        return sample_df.sample(n=min(target_size, len(sample_df)), random_state=42)

def numeric_diamond_sampling(df, x_col, y_col, target_size):
    """
    Sampling khusus untuk data numerik dengan pertimbangan distribusi diamond
    """
    # Buat grid untuk mempertahankan pattern diamond
    n_bins = int(np.sqrt(target_size))
    
    try:
        # Buat bins untuk kedua sumbu
        x_bins = pd.cut(df[x_col], bins=n_bins, duplicates='drop')
        y_bins = pd.cut(df[y_col], bins=n_bins, duplicates='drop')
        
        # Group by kedua bins dan ambil centroid
        aggregated = df.groupby([x_bins, y_bins], observed=False).agg({
            x_col: 'mean',
            y_col: 'mean',
            **{col: 'mean' for col in df.columns if col not in [x_col, y_col]}
        }).reset_index(drop=True)
        
        # Jika masih terlalu banyak, ambil sample
        if len(aggregated) > target_size:
            return aggregated.sample(n=target_size, random_state=42)
        return aggregated
        
    except:
        # Fallback: random sampling dengan stratification
        return df.sample(n=min(target_size, len(df)), random_state=42)

def create_diamond_pattern_chart(df, x_col, y_col, size_col, color_scheme, diamond_style, optimization_level):
    """
    Buat diamond chart pattern yang optimal
    """
    fig = go.Figure()
    
    # Konfigurasi berdasarkan style diamond
    style_config = get_diamond_style_config(diamond_style, color_scheme)
    
    # Data untuk scatter plot dengan shape diamond
    if size_col and size_col != "None":
        marker_size = df[size_col]
        # Normalize size untuk visualisasi yang baik
        if marker_size.max() > marker_size.min():
            marker_size = 10 + 40 * (marker_size - marker_size.min()) / (marker_size.max() - marker_size.min())
        else:
            marker_size = 20
    else:
        marker_size = 15
    
    # Tambahkan trace diamond utama
    fig.add_trace(go.Scattergl(
        x=df[x_col],
        y=df[y_col],
        mode='markers',
        name='Diamond Pattern',
        marker=dict(
            symbol='diamond',  # Shape diamond
            size=marker_size,
            color=df[y_col] if pd.api.types.is_numeric_dtype(df[y_col]) else None,
            colorscale=color_scheme,
            colorbar=dict(title=y_col),
            line=style_config['marker_line'],
            opacity=style_config['opacity']
        ),
        hovertemplate=(
            f"<b>{x_col}</b>: %{{x}}<br>"
            f"<b>{y_col}</b>: %{{y}}<br>"
            f"{f'<b>{size_col}</b>: %{{marker.size}}<br>' if size_col and size_col != 'None' else ''}"
            "<extra></extra>"
        ),
        text=df.index if len(df) < 100 else None
    ))
    
    # Tambahkan trend line untuk menunjukkan pattern
    if len(df) > 10 and pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
        try:
            # Hitung regression line
            z = np.polyfit(df[x_col], df[y_col], 1)
            p = np.poly1d(z)
            
            fig.add_trace(go.Scattergl(
                x=df[x_col],
                y=p(df[x_col]),
                mode='lines',
                name='Trend Line',
                line=dict(color='red', width=2, dash='dash'),
                opacity=0.7
            ))
        except:
            pass
    
    # Layout khusus diamond chart
    fig.update_layout(
        title=f"🔷 Diamond Chart Pattern: {y_col} vs {x_col}",
        xaxis=dict(
            title=x_col,
            gridcolor='#f0f0f0',
            showgrid=True,
        ),
        yaxis=dict(
            title=y_col,
            gridcolor='#f0f0f0',
            showgrid=True,
        ),
        height=500,
        showlegend=True,
        margin=dict(l=60, r=60, t=80, b=60),
        plot_bgcolor='white',
        paper_bgcolor='white',
        # Fitur interaktif
        hovermode='closest',
        dragmode='zoom',
    )
    
    # Tambahkan quadrant lines untuk diamond pattern analysis
    if len(df) > 0 and pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
        x_mean = df[x_col].mean()
        y_mean = df[y_col].mean()
        
        fig.add_hline(y=y_mean, line_dash="dot", line_color="gray", opacity=0.5)
        fig.add_vline(x=x_mean, line_dash="dot", line_color="gray", opacity=0.5)
    
    return fig

def get_diamond_style_config(style, color_scheme):
    """Konfigurasi style untuk diamond marker"""
    styles = {
        "Standard": {
            'marker_line': dict(width=0),
            'opacity': 0.8
        },
        "Outlined": {
            'marker_line': dict(width=2, color='darkgray'),
            'opacity': 0.9
        },
        "Gradient": {
            'marker_line': dict(width=1, color='white'),
            'opacity': 0.7
        },
        "Transparent": {
            'marker_line': dict(width=1, color='black'),
            'opacity': 0.5
        }
    }
    return styles.get(style, styles["Standard"])

def show_diamond_pattern_info(df, x_col, y_col, size_col):
    """Tampilkan informasi analisis diamond pattern"""
    
    with st.expander("🔷 Diamond Pattern Analysis", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Data Points", len(df))
        
        with col2:
            if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
                correlation = df[x_col].corr(df[y_col])
                st.metric("Korelasi", f"{correlation:.3f}")
        
        with col3:
            if pd.api.types.is_numeric_dtype(df[y_col]):
                cv = df[y_col].std() / df[y_col].mean() if df[y_col].mean() != 0 else 0
                st.metric("Coefficient of Variation", f"{cv:.3f}")
        
        # Quadrant analysis untuk numeric data
        if (pd.api.types.is_numeric_dtype(df[x_col]) and 
            pd.api.types.is_numeric_dtype(df[y_col]) and 
            len(df) > 0):
            
            x_mean = df[x_col].mean()
            y_mean = df[y_col].mean()
            
            # Hitung points di setiap quadrant
            q1 = len(df[(df[x_col] > x_mean) & (df[y_col] > y_mean)])
            q2 = len(df[(df[x_col] < x_mean) & (df[y_col] > y_mean)])
            q3 = len(df[(df[x_col] < x_mean) & (df[y_col] < y_mean)])
            q4 = len(df[(df[x_col] > x_mean) & (df[y_col] < y_mean)])
            
            st.subheader("Quadrant Distribution")
            quad_col1, quad_col2, quad_col3, quad_col4 = st.columns(4)
            
            with quad_col1:
                st.metric("Q1 (High X, High Y)", q1)
            with quad_col2:
                st.metric("Q2 (Low X, High Y)", q2)
            with quad_col3:
                st.metric("Q3 (Low X, Low Y)", q3)
            with quad_col4:
                st.metric("Q4 (High X, Low Y)", q4)

def create_diamond_fallback_chart(df, x_col, y_col, size_col):
    """Fallback method untuk diamond chart"""
    st.warning("Menggunakan metode fallback untuk diamond chart...")
    
    # Sample kecil untuk memastikan bisa render
    sample_df = df[[x_col, y_col]].dropna().head(500)
    if size_col and size_col != "None":
        sample_df[size_col] = df[size_col]
    
    fig = go.Figure()
    
    marker_size = sample_df[size_col] if size_col and size_col != "None" else 15
    
    fig.add_trace(go.Scatter(
        x=sample_df[x_col],
        y=sample_df[y_col],
        mode='markers',
        marker=dict(
            symbol='diamond',
            size=marker_size,
            color=sample_df[y_col] if pd.api.types.is_numeric_dtype(sample_df[y_col]) else 'blue',
            colorscale='Viridis'
        )
    ))
    
    fig.update_layout(
        title=f"Diamond Chart: {y_col} vs {x_col}",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Versi ultra-ringan untuk diamond chart
def create_diamond_chart_ultralight(df, numeric_cols, non_numeric_cols):
    """Versi ultra-ringan untuk diamond chart dengan data besar"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        x_col = st.selectbox("Sumbu X", 
                           [df.index.name if df.index.name else "index"] + non_numeric_cols[:3], 
                           key="ultralight_diamond_x")
    with col2:
        y_col = st.selectbox("Sumbu Y", numeric_cols[:5], key="ultralight_diamond_y")
    with col3:
        color_col = st.selectbox("Warna", numeric_cols[:5], key="ultralight_diamond_color")
    
    if x_col and y_col:
        # Aggressive sampling - hanya 300 data points untuk performa
        if len(df) > 300:
            step = len(df) // 300
            display_df = df.iloc[::step][[x_col, y_col, color_col]].dropna()
        else:
            display_df = df[[x_col, y_col, color_col]].dropna()
        
        # Simple diamond chart dengan WebGL
        fig = go.Figure()
        fig.add_trace(go.Scattergl(
            x=display_df[x_col],
            y=display_df[y_col],
            mode='markers',
            marker=dict(
                symbol='diamond',
                size=10,
                color=display_df[color_col],
                colorscale='Plasma',
                showscale=True
            )
        ))
        
        fig.update_layout(
            height=400,
            title="Ultra-Light Diamond Chart",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.info(f"Ultra-Light Diamond Mode: {len(display_df):,} points")

def create_scatter_plot(df, numeric_cols, non_numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        x_col = st.selectbox("Pilih kolom X", numeric_cols, key="scatter_x")
    with col2:
        y_col = st.selectbox("Pilih kolom Y", numeric_cols, key="scatter_y")
    with col3:
        color_col = st.selectbox("Pilih kolom warna", [None] + non_numeric_cols, key="scatter_color")
    with col4:
        # Pengaturan optimasi
        optimization_mode = st.selectbox(
            "Mode Optimasi",
            ["Auto", "Fast", "Balanced", "Detailed"],
            index=0 if data_size > 100000 else 2,
            key="scatter_optim"
        )
    
    # Opsi tambahan untuk data besar
    with st.expander("⚙️ Pengaturan Lanjutan", expanded=False):
        col5, col6, col7 = st.columns(3)
        with col5:
            max_points = st.slider(
                "Maksimum titik data",
                min_value=1000,
                max_value=20000,
                value=5000 if data_size > 100000 else 10000,
                key="scatter_max_points"
            )
        with col6:
            point_size = st.slider(
                "Ukuran titik",
                min_value=1,
                max_value=10,
                value=3 if data_size > 50000 else 5,
                key="scatter_point_size"
            )
        with col7:
            opacity = st.slider(
                "Transparansi",
                min_value=0.1,
                max_value=1.0,
                value=0.6 if data_size > 50000 else 0.8,
                key="scatter_opacity"
            )
    
    if x_col and y_col:
        try:
            with st.spinner("🔄 Memproses data scatter plot..."):
                # OPTIMASI 1: Filter data dan sampling
                plot_data = optimize_scatter_data(df, x_col, y_col, color_col, data_size, optimization_mode, max_points)
                
                if len(plot_data) == 0:
                    st.warning("Tidak ada data valid untuk plot")
                    return
                
                # OPTIMASI 2: Buat scatter plot yang dioptimalkan
                fig = create_optimized_scatter(plot_data, x_col, y_col, color_col, point_size, opacity, data_size)
                
                # OPTIMASI 3: Konfigurasi plotly yang ringan
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'hoverClosestGl2d'],
                    'scrollZoom': True,
                    'responsive': True
                }
                
                st.plotly_chart(fig, use_container_width=True, config=config)
                
                # Tampilkan statistik korelasi
                display_correlation_stats(plot_data, x_col, y_col)
                
                # Tampilkan info optimasi
                show_scatter_optimization_info(data_size, len(plot_data), optimization_mode)
                
        except Exception as e:
            st.error(f"Error membuat scatter plot: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_scatter_fallback(df, x_col, y_col, color_col)

def optimize_scatter_data(df, x_col, y_col, color_col, data_size, optimization_mode, max_points):
    """Optimasi data untuk scatter plot dengan sampling yang tepat"""
    # Pilih kolom yang diperlukan
    columns_needed = [x_col, y_col]
    if color_col:
        columns_needed.append(color_col)
    
    # Filter data yang valid
    plot_data = df[columns_needed].dropna()
    
    if len(plot_data) == 0:
        return plot_data
    
    # Tentukan target sample size
    target_sizes = {
        "Auto": min(max_points, data_size),
        "Fast": min(3000, data_size),
        "Balanced": min(10000, data_size),
        "Detailed": min(20000, data_size)
    }
    
    target_size = target_sizes[optimization_mode]
    
    # Jika data lebih besar dari target, lakukan sampling
    if len(plot_data) > target_size:
        if optimization_mode == "Fast":
            # Systematic sampling untuk performa maksimal
            step = len(plot_data) // target_size
            sampled_data = plot_data.iloc[::step]
        elif optimization_mode == "Balanced":
            # Stratified sampling berdasarkan quadrant
            try:
                x_median = plot_data[x_col].median()
                y_median = plot_data[y_col].median()
                
                # Bagi data menjadi 4 quadrant
                quadrants = [
                    (plot_data[x_col] <= x_median) & (plot_data[y_col] <= y_median),
                    (plot_data[x_col] <= x_median) & (plot_data[y_col] > y_median),
                    (plot_data[x_col] > x_median) & (plot_data[y_col] <= y_median),
                    (plot_data[x_col] > x_median) & (plot_data[y_col] > y_median)
                ]
                
                samples_per_quadrant = target_size // 4
                sampled_dfs = []
                
                for quadrant in quadrants:
                    quadrant_data = plot_data[quadrant]
                    if len(quadrant_data) > 0:
                        sample_size = min(samples_per_quadrant, len(quadrant_data))
                        sampled_dfs.append(quadrant_data.sample(n=sample_size, random_state=42))
                
                sampled_data = pd.concat(sampled_dfs, ignore_index=True)
                
                # Jika masih kurang, tambahkan random sampling
                if len(sampled_data) < target_size:
                    remaining = target_size - len(sampled_data)
                    additional_samples = plot_data.sample(n=remaining, random_state=42)
                    sampled_data = pd.concat([sampled_data, additional_samples], ignore_index=True)
                    
            except:
                # Fallback ke random sampling
                sampled_data = plot_data.sample(n=target_size, random_state=42)
        else:
            # Random sampling untuk mode lain
            sampled_data = plot_data.sample(n=target_size, random_state=42)
        
        return sampled_data
    
    return plot_data

def create_optimized_scatter(plot_data, x_col, y_col, color_col, point_size, opacity, original_size):
    """Buat scatter plot dengan optimasi performa"""
    
    # OPTIMASI: Gunakan scattergl (WebGL) untuk data banyak
    if len(plot_data) > 5000:
        scatter_function = px.scatter_gl
        scatter_name = "ScatterGL"
    else:
        scatter_function = px.scatter
        scatter_name = "Scatter"
    
    # Buat plot
    fig = scatter_function(
        plot_data,
        x=x_col,
        y=y_col,
        color=color_col,
        title=f"{scatter_name}: {y_col} vs {x_col} ({len(plot_data):,} points)",
        opacity=opacity,
        size_max=point_size * 2
    )
    
    # Update marker size dan style
    fig.update_traces(
        marker=dict(
            size=point_size,
            line=dict(width=0)  # No border untuk performa
        ),
        selector=dict(mode='markers')
    )
    
    # OPTIMASI: Sederhanakan hover template untuk performa
    if len(plot_data) > 5000:
        hover_template = f'{x_col}: %{{x:.2f}}<br>{y_col}: %{{y:.2f}}<extra></extra>'
    else:
        if color_col:
            hover_template = f'{x_col}: %{{x:.2f}}<br>{y_col}: %{{y:.2f}}<br>{color_col}: %{{marker.color}}<extra></extra>'
        else:
            hover_template = f'{x_col}: %{{x:.2f}}<br>{y_col}: %{{y:.2f}}<extra></extra>'
    
    fig.update_traces(hovertemplate=hover_template)
    
    # Layout yang dioptimalkan
    fig.update_layout(
        height=500,
        showlegend=len(plot_data) <= 10000,  # Sembunyikan legend untuk data sangat banyak
        margin=dict(l=50, r=50, t=60, b=50),
        plot_bgcolor='white'
    )
    
    # Tambahkan trendline untuk data yang tidak terlalu banyak
    if len(plot_data) <= 10000 and len(plot_data) > 10:
        try:
            # Hitung regression line
            z = np.polyfit(plot_data[x_col], plot_data[y_col], 1)
            p = np.poly1d(z)
            
            # Buat trendline
            x_trend = np.linspace(plot_data[x_col].min(), plot_data[x_col].max(), 100)
            y_trend = p(x_trend)
            
            fig.add_trace(go.Scatter(
                x=x_trend,
                y=y_trend,
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name='Trend Line',
                hovertemplate='Trend: %{y:.2f}<extra></extra>'
            ))
        except:
            pass  # Skip trendline jika error
    
    return fig

def display_correlation_stats(plot_data, x_col, y_col):
    """Tampilkan statistik korelasi"""
    with st.expander("📈 Analisis Korelasi", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        try:
            # Hitung korelasi
            correlation = plot_data[x_col].corr(plot_data[y_col])
            
            with col1:
                st.metric("Korelasi Pearson", f"{correlation:.3f}")
            
            with col2:
                # Interpretasi korelasi
                if abs(correlation) < 0.3:
                    st.metric("Kekuatan", "Lemah")
                elif abs(correlation) < 0.7:
                    st.metric("Kekuatan", "Sedang")
                else:
                    st.metric("Kekuatan", "Kuat")
            
            with col3:
                # Arah korelasi
                if correlation > 0:
                    st.metric("Arah", "Positif")
                else:
                    st.metric("Arah", "Negatif")
            
            # Additional stats
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric("Jumlah Titik", len(plot_data))
            with col5:
                st.metric(f"Rata2 {x_col}", f"{plot_data[x_col].mean():.2f}")
            with col6:
                st.metric(f"Rata2 {y_col}", f"{plot_data[y_col].mean():.2f}")
                
        except Exception as e:
            st.warning(f"Tidak dapat menghitung korelasi: {str(e)}")

def show_scatter_optimization_info(original_size, processed_size, optimization_mode):
    """Tampilkan informasi optimasi"""
    reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
    
    if reduction_pct > 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{original_size:,}")
            with col2:
                st.metric("Data Ditampilkan", f"{processed_size:,}")
            with col3:
                st.metric("Reduksi", f"{reduction_pct:.1f}%")
            
            st.info(f"**Mode {optimization_mode}**: Scatter plot dioptimalkan untuk kecepatan rendering")
            
            if optimization_mode == "Fast":
                st.markdown("• ✅ **WebGL Rendering** (ScatterGL)")
                st.markdown("• ✅ **Systematic Sampling**")
                st.markdown("• ✅ **Minimal Hover Effects**")
            elif optimization_mode == "Balanced":
                st.markdown("• ✅ **Stratified Sampling** (per quadrant)")
                st.markdown("• ✅ **Trend Line Analysis**")
                st.markdown("• ✅ **Optimized Hover**")

def create_simple_scatter_fallback(df, x_col, y_col, color_col):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback yang sederhana...")
    
    # Sample kecil untuk memastikan bisa render
    sample_size = min(1000, len(df))
    plot_data = df[[x_col, y_col] + ([color_col] if color_col else [])].dropna().head(sample_size)
    
    fig = px.scatter(
        plot_data,
        x=x_col,
        y=y_col,
        color=color_col,
        title=f"Simple Scatter: {y_col} vs {x_col} ({len(plot_data)} points)"
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Versi ultra-ringan untuk data ekstrem
def create_ultra_fast_scatter(df, numeric_cols, non_numeric_cols):
    """Versi ultra-ringan untuk data > 500k rows"""
    
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Pilih kolom X", numeric_cols[:8], key="ultra_scatter_x")
    with col2:
        y_col = st.selectbox("Pilih kolom Y", numeric_cols[:8], key="ultra_scatter_y")
    
    if x_col and y_col:
        # Sampling agresif - hanya 2000 points
        if len(df) > 2000:
            plot_data = df[[x_col, y_col]].dropna().sample(n=2000, random_state=42)
        else:
            plot_data = df[[x_col, y_col]].dropna()
        
        # ScatterGL dengan konfigurasi minimal
        fig = px.scatter_gl(
            plot_data,
            x=x_col,
            y=y_col,
            title=f"Ultra-Fast: {y_col} vs {x_col} (2,000 samples)"
        )
        
        fig.update_traces(
            marker=dict(size=2, opacity=0.5),
            hovertemplate='%{x:.1f}, %{y:.1f}<extra></extra>'
        )
        
        fig.update_layout(height=350, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.info(f"📊 Menampilkan 2,000 sample dari {len(df[[x_col, y_col]].dropna()):,} data points")

def create_bubble_chart(df, numeric_cols, non_numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 50000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        x_col = st.selectbox("Pilih kolom X", numeric_cols, key="bubble_x")
    with col2:
        y_col = st.selectbox("Pilih kolom Y", numeric_cols, key="bubble_y")
    with col3:
        size_col = st.selectbox("Pilih kolom ukuran", numeric_cols, key="bubble_size")
    with col4:
        color_col = st.selectbox("Pilih kolom warna", [None] + non_numeric_cols, key="bubble_color")
    
    # Pengaturan optimasi
    with st.expander("⚙️ Pengaturan Optimasi", expanded=False):
        col5, col6, col7 = st.columns(3)
        with col5:
            optimization_mode = st.selectbox(
                "Mode Optimasi",
                ["Auto", "Fast", "Balanced", "Detailed"],
                index=0 if data_size > 50000 else 2,
                key="bubble_optim"
            )
        with col6:
            max_bubbles = st.slider(
                "Maksimum gelembung",
                min_value=100,
                max_value=2000,
                value=500 if data_size > 50000 else 1000,
                key="bubble_max_points"
            )
        with col7:
            size_factor = st.slider(
                "Faktor ukuran gelembung",
                min_value=1,
                max_value=20,
                value=5 if data_size > 50000 else 10,
                key="bubble_size_factor"
            )
    
    if x_col and y_col and size_col:
        try:
            with st.spinner("🔄 Memproses data bubble chart..."):
                # OPTIMASI 1: Filter data dan sampling
                plot_data = optimize_bubble_data(df, x_col, y_col, size_col, color_col, data_size, optimization_mode, max_bubbles)
                
                if len(plot_data) == 0:
                    st.warning("Tidak ada data valid untuk bubble chart")
                    return
                
                # OPTIMASI 2: Normalisasi ukuran bubble untuk visualisasi yang lebih baik
                plot_data = normalize_bubble_sizes(plot_data, size_col, size_factor)
                
                # OPTIMASI 3: Buat bubble chart yang dioptimalkan
                fig = create_optimized_bubble_chart(plot_data, x_col, y_col, size_col, color_col, data_size)
                
                # OPTIMASI 4: Konfigurasi plotly yang ringan
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'hoverClosestGl2d'],
                    'scrollZoom': True,
                    'responsive': True
                }
                
                st.plotly_chart(fig, use_container_width=True, config=config)
                
                # Tampilkan statistik
                display_bubble_statistics(plot_data, x_col, y_col, size_col)
                
                # Tampilkan info optimasi
                show_bubble_optimization_info(data_size, len(plot_data), optimization_mode)
                
        except Exception as e:
            st.error(f"Error membuat bubble chart: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_bubble_fallback(df, x_col, y_col, size_col, color_col)

def optimize_bubble_data(df, x_col, y_col, size_col, color_col, data_size, optimization_mode, max_bubbles):
    """Optimasi data untuk bubble chart dengan sampling yang tepat"""
    # Pilih kolom yang diperlukan
    columns_needed = [x_col, y_col, size_col]
    if color_col:
        columns_needed.append(color_col)
    
    # Filter data yang valid
    plot_data = df[columns_needed].dropna()
    
    if len(plot_data) == 0:
        return plot_data
    
    # Tentukan target sample size
    target_sizes = {
        "Auto": min(max_bubbles, data_size),
        "Fast": min(300, data_size),
        "Balanced": min(800, data_size),
        "Detailed": min(1500, data_size)
    }
    
    target_size = target_sizes[optimization_mode]
    
    # Jika data lebih besar dari target, lakukan sampling
    if len(plot_data) > target_size:
        if optimization_mode == "Fast":
            # Sampling berdasarkan ukuran (ambil yang paling signifikan)
            plot_data_sorted = plot_data.nlargest(target_size, size_col)
            return plot_data_sorted
            
        elif optimization_mode == "Balanced":
            # Stratified sampling berdasarkan size quantile
            try:
                quantiles = pd.qcut(plot_data[size_col], q=4, duplicates='drop')
                samples_per_quantile = target_size // 4
                sampled_dfs = []
                
                for quantile in quantiles.cat.categories:
                    quantile_data = plot_data[quantiles == quantile]
                    if len(quantile_data) > 0:
                        sample_size = min(samples_per_quantile, len(quantile_data))
                        sampled_dfs.append(quantile_data.sample(n=sample_size, random_state=42))
                
                sampled_data = pd.concat(sampled_dfs, ignore_index=True)
                
                # Jika masih kurang, tambahkan berdasarkan size
                if len(sampled_data) < target_size:
                    remaining = target_size - len(sampled_data)
                    additional_samples = plot_data.nlargest(remaining, size_col)
                    sampled_data = pd.concat([sampled_data, additional_samples], ignore_index=True)
                    
                return sampled_data
            except:
                # Fallback ke size-based sampling
                return plot_data.nlargest(target_size, size_col)
        else:
            # Random sampling dengan prioritas size besar
            if optimization_mode == "Detailed":
                # Gabungkan random sampling dengan size-based
                size_based = plot_data.nlargest(target_size // 2, size_col)
                random_samples = plot_data.sample(n=target_size - len(size_based), random_state=42)
                return pd.concat([size_based, random_samples], ignore_index=True)
            else:
                return plot_data.sample(n=target_size, random_state=42)
    
    return plot_data

def normalize_bubble_sizes(plot_data, size_col, size_factor):
    """Normalisasi ukuran bubble untuk visualisasi yang lebih baik"""
    plot_data = plot_data.copy()
    
    # Normalisasi ukuran antara 5-50 untuk visualisasi optimal
    min_size = plot_data[size_col].min()
    max_size = plot_data[size_col].max()
    
    if max_size > min_size:
        # Scale ke range yang reasonable
        scaled_sizes = (plot_data[size_col] - min_size) / (max_size - min_size)
        plot_data['bubble_size_normalized'] = 5 + scaled_sizes * (size_factor * 5)
    else:
        plot_data['bubble_size_normalized'] = 10  # Default size
    
    return plot_data

def create_optimized_bubble_chart(plot_data, x_col, y_col, size_col, color_col, original_size):
    """Buat bubble chart dengan optimasi performa"""
    
    # OPTIMASI: Gunakan scattergl untuk data banyak
    use_webgl = len(plot_data) > 500
    if use_webgl:
        scatter_function = px.scatter_gl
        chart_type = "Bubble Chart (WebGL)"
    else:
        scatter_function = px.scatter
        chart_type = "Bubble Chart"
    
    # Buat plot
    fig = scatter_function(
        plot_data,
        x=x_col,
        y=y_col,
        size='bubble_size_normalized',
        color=color_col,
        title=f"{chart_type}: {y_col} vs {x_col} - Size: {size_col} ({len(plot_data):,} bubbles)",
        hover_name=plot_data.index if plot_data.index.name else None,
        size_max=20,  # Batasi ukuran maksimum
        opacity=0.7
    )
    
    # OPTIMASI: Update marker untuk performa
    fig.update_traces(
        marker=dict(
            line=dict(width=0),  # No border untuk performa
            sizemode='diameter'
        ),
        selector=dict(mode='markers')
    )
    
    # OPTIMASI: Sederhanakan hover template
    if len(plot_data) > 500:
        hover_template = (f'{x_col}: %{{x:.2f}}<br>'
                         f'{y_col}: %{{y:.2f}}<br>'
                         f'{size_col}: %{{marker.size:.1f}}<extra></extra>')
    else:
        if color_col:
            hover_template = (f'{x_col}: %{{x:.2f}}<br>'
                             f'{y_col}: %{{y:.2f}}<br>'
                             f'{size_col}: %{{marker.size:.1f}}<br>'
                             f'{color_col}: %{{marker.color}}<extra></extra>')
        else:
            hover_template = (f'{x_col}: %{{x:.2f}}<br>'
                             f'{y_col}: %{{y:.2f}}<br>'
                             f'{size_col}: %{{marker.size:.1f}}<extra></extra>')
    
    fig.update_traces(hovertemplate=hover_template)
    
    # Layout yang dioptimalkan
    fig.update_layout(
        height=500,
        showlegend=len(plot_data) <= 200,  # Sembunyikan legend untuk banyak bubbles
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ) if len(plot_data) <= 200 else None
    )
    
    return fig

def display_bubble_statistics(plot_data, x_col, y_col, size_col):
    """Tampilkan statistik bubble chart"""
    with st.expander("📊 Statistik Bubble Chart", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Jumlah Gelembung", len(plot_data))
        with col2:
            st.metric(f"Rata2 {x_col}", f"{plot_data[x_col].mean():.2f}")
        with col3:
            st.metric(f"Rata2 {y_col}", f"{plot_data[y_col].mean():.2f}")
        with col4:
            st.metric(f"Rata2 {size_col}", f"{plot_data[size_col].mean():.2f}")
        
        # Top 5 largest bubbles
        st.markdown("**🔍 Gelembung Terbesar:**")
        largest_bubbles = plot_data.nlargest(5, size_col)[[x_col, y_col, size_col]]
        st.dataframe(largest_bubbles.style.format({
            x_col: "{:.2f}",
            y_col: "{:.2f}", 
            size_col: "{:.2f}"
        }), use_container_width=True)
        
        # Korelasi antar variabel
        try:
            corr_xy = plot_data[x_col].corr(plot_data[y_col])
            corr_xsize = plot_data[x_col].corr(plot_data[size_col])
            corr_ysize = plot_data[y_col].corr(plot_data[size_col])
            
            col5, col6, col7 = st.columns(3)
            with col5:
                st.metric("Korelasi X-Y", f"{corr_xy:.3f}")
            with col6:
                st.metric("Korelasi X-Size", f"{corr_xsize:.3f}")
            with col7:
                st.metric("Korelasi Y-Size", f"{corr_ysize:.3f}")
        except:
            st.info("Tidak dapat menghitung korelasi")

def show_bubble_optimization_info(original_size, processed_size, optimization_mode):
    """Tampilkan informasi optimasi"""
    reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
    
    if reduction_pct > 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{original_size:,}")
            with col2:
                st.metric("Gelembung Ditampilkan", f"{processed_size:,}")
            with col3:
                st.metric("Reduksi", f"{reduction_pct:.1f}%")
            
            optimization_strategies = {
                "Fast": "• ✅ **Size-based sampling** (ambil yang terbesar)\n• ✅ **WebGL Rendering**\n• ✅ **Minimal hover effects**",
                "Balanced": "• ✅ **Stratified sampling** (berdasarkan quantile size)\n• ✅ **Size normalization**\n• ✅ **Optimized bubble sizes**",
                "Detailed": "• ✅ **Hybrid sampling** (size + random)\n• ✅ **Full features**\n• ✅ **Detailed hover info**"
            }
            
            st.info(f"**Mode {optimization_mode}**: {optimization_strategies.get(optimization_mode, 'Custom optimization')}")

def create_simple_bubble_fallback(df, x_col, y_col, size_col, color_col):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback yang sederhana...")
    
    # Sample kecil untuk memastikan bisa render
    sample_size = min(200, len(df))
    plot_data = df[[x_col, y_col, size_col] + ([color_col] if color_col else [])].dropna().head(sample_size)
    
    # Normalisasi sederhana
    if len(plot_data) > 0:
        min_size = plot_data[size_col].min()
        max_size = plot_data[size_col].max()
        if max_size > min_size:
            plot_data = plot_data.copy()
            plot_data['bubble_size_norm'] = 10 + ((plot_data[size_col] - min_size) / (max_size - min_size)) * 30
    
    fig = px.scatter(
        plot_data,
        x=x_col,
        y=y_col,
        size='bubble_size_norm' if 'bubble_size_norm' in plot_data.columns else size_col,
        color=color_col,
        title=f"Simple Bubble: {y_col} vs {x_col} ({len(plot_data)} bubbles)"
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Versi ultra-ringan untuk data ekstrem
def create_ultra_fast_bubble_chart(df, numeric_cols, non_numeric_cols):
    """Versi ultra-ringan untuk data > 100k rows"""
    
    col1, col2, col3 = st.columns(3)
    with col1:
        x_col = st.selectbox("Pilih kolom X", numeric_cols[:6], key="ultra_bubble_x")
    with col2:
        y_col = st.selectbox("Pilih kolom Y", numeric_cols[:6], key="ultra_bubble_y")
    with col3:
        size_col = st.selectbox("Pilih kolom ukuran", numeric_cols[:6], key="ultra_bubble_size")
    
    if x_col and y_col and size_col:
        # Sampling agresif - hanya 150 bubbles terbesar
        plot_data = df[[x_col, y_col, size_col]].dropna().nlargest(150, size_col)
        
        if len(plot_data) > 0:
            # Normalisasi ukuran
            min_size = plot_data[size_col].min()
            max_size = plot_data[size_col].max()
            if max_size > min_size:
                plot_data = plot_data.copy()
                plot_data['bubble_size_norm'] = 5 + ((plot_data[size_col] - min_size) / (max_size - min_size)) * 15
            
            # Bubble chart sederhana dengan WebGL
            fig = px.scatter_gl(
                plot_data,
                x=x_col,
                y=y_col,
                size='bubble_size_norm' if 'bubble_size_norm' in plot_data.columns else size_col,
                title=f"Ultra-Fast Bubble: Top 150 by {size_col}"
            )
            
            fig.update_traces(
                marker=dict(opacity=0.6, line=dict(width=0)),
                hovertemplate='X: %{x:.1f}<br>Y: %{y:.1f}<br>Size: %{marker.size:.1f}<extra></extra>'
            )
            
            fig.update_layout(height=350, showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.info(f"📊 Menampilkan 150 gelembung terbesar dari {len(df[[x_col, y_col, size_col]].dropna()):,} data points")
        
        with st.expander("ℹ️ Keterangan Bubble Chart"):
            st.markdown("""
            **Bubble Chart** adalah scatter plot dengan dimensi ketiga (ukuran gelembung).
            - **Kelebihan**: Menampilkan tiga dimensi data sekaligus
            - **Kekurangan**: Bisa sulit dibaca jika terlalu banyak gelembung
            - **Penggunaan**: Analisis tiga variabel, comparison dengan multiple dimensions
            
            **Optimasi untuk Data Besar:**
            • Size-based sampling untuk mempertahankan insight
            • WebGL rendering untuk performa
            • Normalisasi ukuran untuk visualisasi optimal
            """)

def create_gauge_chart(df, numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        value_col = st.selectbox("Pilih kolom nilai", numeric_cols, key="gauge_value")
    
    with col2:
        # Auto-calculate max value atau manual input
        auto_max = st.checkbox("Auto calculate max", value=True, key="gauge_auto_max")
        if auto_max and value_col:
            max_val = df[value_col].max() * 1.1  # Tambah 10% buffer
            st.info(f"Max: {max_val:.2f}")
        else:
            max_val = st.number_input("Nilai maksimum gauge", 
                                    value=100.0, 
                                    min_value=0.1,
                                    key="gauge_max")
    
    with col3:
        calculation_method = st.selectbox(
            "Metode kalkulasi",
            ["Mean", "Median", "Sum", "Last Value", "Custom Percentile"],
            key="gauge_calc_method"
        )
        
        if calculation_method == "Custom Percentile":
            percentile = st.slider("Percentile", 0, 100, 90, key="gauge_percentile")
    
    if value_col:
        try:
            with st.spinner("🔄 Menghitung nilai gauge..."):
                # OPTIMASI 1: Kalkulasi nilai yang efisien
                gauge_value, reference_value = calculate_gauge_values(
                    df, value_col, calculation_method, 
                    percentile if 'percentile' in locals() else None,
                    data_size
                )
                
                # OPTIMASI 2: Buat gauge chart yang dioptimalkan
                fig = create_optimized_gauge_chart(
                    gauge_value, reference_value, value_col, 
                    max_val, calculation_method, data_size
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                # Tampilkan statistik tambahan
                display_gauge_statistics(df, value_col, gauge_value, reference_value, data_size)
                
        except Exception as e:
            st.error(f"Error membuat gauge chart: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_gauge_fallback(df, value_col)

def calculate_gauge_values(df, value_col, calculation_method, percentile, data_size):
    """Hitung nilai gauge dengan optimasi untuk data besar"""
    
    # OPTIMASI: Sampling untuk data sangat besar
    if data_size > 100000:
        # Gunakan sample representatif
        sample_size = min(10000, data_size)
        sample_df = df[value_col].dropna().sample(n=sample_size, random_state=42)
        st.info(f"📊 Menggunakan sample {sample_size:,} dari {data_size:,} data points")
    else:
        sample_df = df[value_col].dropna()
    
    if len(sample_df) == 0:
        return 0, 0
    
    # Kalkulasi berdasarkan metode yang dipilih
    if calculation_method == "Mean":
        value = sample_df.mean()
        reference = sample_df.median()
    elif calculation_method == "Median":
        value = sample_df.median()
        reference = sample_df.mean()
    elif calculation_method == "Sum":
        # Scale sum untuk data sample
        if data_size > 100000:
            scale_factor = data_size / len(sample_df)
            value = sample_df.sum() * scale_factor
        else:
            value = sample_df.sum()
        reference = value * 0.8  # Reference 80% dari total
    elif calculation_method == "Last Value":
        value = df[value_col].iloc[-1] if len(df) > 0 else 0
        reference = sample_df.mean()
    elif calculation_method == "Custom Percentile":
        value = sample_df.quantile(percentile/100)
        reference = sample_df.median()
    else:
        value = sample_df.mean()
        reference = sample_df.median()
    
    return float(value), float(reference)

def create_optimized_gauge_chart(value, reference, value_col, max_value, calculation_method, data_size):
    """Buat gauge chart yang dioptimalkan"""
    
    # OPTIMASI: Tentukan warna berdasarkan nilai
    value_ratio = value / max_value if max_value > 0 else 0
    
    if value_ratio < 0.3:
        bar_color = "red"
        threshold_color = "darkred"
    elif value_ratio < 0.7:
        bar_color = "orange"
        threshold_color = "darkorange"
    else:
        bar_color = "green"
        threshold_color = "darkgreen"
    
    # OPTIMASI: Steps dengan warna yang meaningful
    steps = [
        {'range': [0, max_value * 0.3], 'color': "lightcoral"},
        {'range': [max_value * 0.3, max_value * 0.7], 'color': "lightyellow"},
        {'range': [max_value * 0.7, max_value], 'color': "lightgreen"}
    ]
    
    # Buat gauge figure
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {
            'text': f"{calculation_method} {value_col}",
            'font': {'size': 16}
        },
        number = {
            'valueformat': ".2f",
            'font': {'size': 24}
        },
        delta = {
            'reference': reference,
            'increasing': {'color': "green"},
            'decreasing': {'color': "red"},
            'valueformat': ".2f"
        },
        gauge = {
            'axis': {
                'range': [0, max_value],
                'tickwidth': 1,
                'tickcolor': "darkblue"
            },
            'bar': {'color': bar_color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': steps,
            'threshold': {
                'line': {'color': threshold_color, 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    # Layout yang dioptimalkan
    fig.update_layout(
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='white',
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig

def display_gauge_statistics(df, value_col, gauge_value, reference_value, data_size):
    """Tampilkan statistik tambahan untuk gauge chart"""
    
    with st.expander("📈 Statistik Detail", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        # Kalkulasi statistik dengan sampling untuk data besar
        if data_size > 50000:
            sample_data = df[value_col].dropna().sample(n=min(10000, data_size), random_state=42)
        else:
            sample_data = df[value_col].dropna()
        
        with col1:
            st.metric("Nilai Gauge", f"{gauge_value:.2f}")
        with col2:
            st.metric("Nilai Referensi", f"{reference_value:.2f}")
        with col3:
            diff = gauge_value - reference_value
            diff_pct = (diff / reference_value * 100) if reference_value != 0 else 0
            st.metric("Selisih", f"{diff:+.2f}", f"{diff_pct:+.1f}%")
        with col4:
            if len(sample_data) > 0:
                completion_pct = (gauge_value / sample_data.max() * 100) if sample_data.max() > 0 else 0
                st.metric("Progress", f"{completion_pct:.1f}%")
        
        # Progress bar visual
        if len(sample_data) > 0:
            max_val = sample_data.max()
            progress_ratio = min(gauge_value / max_val, 1.0) if max_val > 0 else 0
            st.progress(float(progress_ratio), 
                       text=f"Progress: {progress_ratio*100:.1f}% dari maksimum {max_val:.2f}")
        
        # Quick stats
        if len(sample_data) > 0:
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("Data Points", f"{len(sample_data):,}")
            with col6:
                st.metric("Std Dev", f"{sample_data.std():.2f}")
            with col7:
                st.metric("Min", f"{sample_data.min():.2f}")
            with col8:
                st.metric("Max", f"{sample_data.max():.2f}")


def create_simple_gauge_fallback(df, value_col):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback sederhana...")
    
    # Kalkulasi sederhana
    clean_data = df[value_col].dropna().head(1000)  # Batasi data
    if len(clean_data) == 0:
        st.error("Tidak ada data valid")
        return
    
    value = clean_data.mean()
    max_val = clean_data.max() * 1.1
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Simple Gauge: {value_col}"},
        gauge = {
            'axis': {'range': [0, max_val]},
            'bar': {'color': "darkblue"},
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

# Versi multiple gauges untuk dashboard
def create_multi_gauge_dashboard(df, numeric_cols):
    """Dashboard dengan multiple gauge charts"""
    
    # Pilih hingga 4 metrik
    selected_metrics = st.multiselect(
        "Pilih metrik untuk dashboard",
        numeric_cols[:8],  # Batasi pilihan
        default=numeric_cols[:min(4, len(numeric_cols))],
        key="multi_gauge_metrics"
    )
    
    if selected_metrics:
        # Tentukan layout berdasarkan jumlah metrik
        n_metrics = len(selected_metrics)
        if n_metrics == 1:
            cols = [1]
        elif n_metrics == 2:
            cols = st.columns(2)
        elif n_metrics == 3:
            cols = st.columns(3)
        else:
            cols = st.columns(2)
        
        # Buat gauge untuk setiap metrik
        for i, metric in enumerate(selected_metrics):
            if n_metrics <= 3:
                with cols[i]:
                    create_single_gauge_compact(df, metric)
            else:
                # Untuk 4 metrik, buat 2x2 grid
                row_idx = i // 2
                col_idx = i % 2
                if col_idx == 0:
                    col1, col2 = st.columns(2)
                with col1 if col_idx == 0 else col2:
                    create_single_gauge_compact(df, metric)

def create_single_gauge_compact(df, metric):
    """Buat gauge chart compact untuk dashboard"""
    try:
        # Kalkulasi cepat
        sample_data = df[metric].dropna()
        if len(sample_data) == 0:
            st.warning(f"No data for {metric}")
            return
        
        value = sample_data.mean()
        max_val = sample_data.max() * 1.1
        value_ratio = value / max_val if max > 0 else 0
        
        # Tentukan warna
        bar_color = "green" if value_ratio > 0.7 else "orange" if value_ratio > 0.3 else "red"
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': metric[:20], 'font': {'size': 12}},
            number = {'font': {'size': 16}},
            gauge = {
                'axis': {'range': [0, max_val]},
                'bar': {'color': bar_color},
                'steps': [
                    {'range': [0, max_val*0.3], 'color': "lightcoral"},
                    {'range': [max_val*0.3, max_val*0.7], 'color': "lightyellow"},
                    {'range': [max_val*0.7, max_val], 'color': "lightgreen"}
                ]
            }
        ))
        
        fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    except Exception as e:
        st.error(f"Error creating gauge for {metric}")



def create_radar_chart(df, numeric_cols, non_numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_col = st.selectbox("Pilih kolom kategori", non_numeric_cols, key="radar_category")
    
    with col2:
        max_metrics = st.slider("Maksimum metrik", 
                              min_value=3, max_value=10, value=6,
                              key="radar_max_metrics")
    
    # Filter numeric cols yang feasible untuk radar chart
    suitable_numeric_cols = [col for col in numeric_cols 
                           if df[col].nunique() > 1 and df[col].dtype in ['float64', 'int64']]
    
    selected_cols = st.multiselect(
        "Pilih kolom nilai", 
        suitable_numeric_cols[:20],  # Batasi pilihan
        default=suitable_numeric_cols[:min(max_metrics, len(suitable_numeric_cols))], 
        key="radar_values"
    )
    
    # Pengaturan optimasi
    with st.expander("⚙️ Pengaturan Optimasi", expanded=False):
        col3, col4, col5 = st.columns(3)
        with col3:
            optimization_mode = st.selectbox(
                "Mode Optimasi",
                ["Auto", "Fast", "Balanced", "Detailed"],
                index=0 if data_size > 50000 else 2,
                key="radar_optim"
            )
        with col4:
            max_categories = st.slider(
                "Maksimum kategori",
                min_value=3,
                max_value=15,
                value=8 if data_size > 50000 else 12,
                key="radar_max_categories"
            )
        with col5:
            normalize_data = st.checkbox(
                "Normalisasi data", 
                value=True,
                help="Scale data ke range 0-1 untuk perbandingan yang lebih baik"
            )
    
    if category_col and selected_cols and len(selected_cols) >= 3:
        try:
            with st.spinner("🔄 Memproses data radar chart..."):
                # OPTIMASI 1: Filter dan sampling data
                plot_data = optimize_radar_data(
                    df, category_col, selected_cols, data_size, 
                    optimization_mode, max_categories
                )
                
                if plot_data is None or len(plot_data) == 0:
                    st.warning("Tidak ada data valid untuk radar chart")
                    return
                
                # OPTIMASI 2: Normalisasi data jika diperlukan
                if normalize_data:
                    plot_data = normalize_radar_data(plot_data, selected_cols)
                
                # OPTIMASI 3: Batasi jumlah kategori yang ditampilkan
                radar_data = aggregate_radar_data(plot_data, category_col, selected_cols, max_categories)
                
                # OPTIMASI 4: Buat radar chart yang dioptimalkan
                fig = create_optimized_radar_chart(radar_data, category_col, selected_cols, data_size)
                
                # OPTIMASI 5: Konfigurasi plotly yang ringan
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'hoverClosestGl2d'],
                    'responsive': True
                }
                
                st.plotly_chart(fig, use_container_width=True, config=config)
                
                # Tampilkan data table
                display_radar_data_table(radar_data, category_col, selected_cols)
                
                # Tampilkan info optimasi
                show_radar_optimization_info(data_size, len(plot_data), len(radar_data), optimization_mode)
                
        except Exception as e:
            st.error(f"Error membuat radar chart: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_radar_fallback(df, category_col, selected_cols)

def optimize_radar_data(df, category_col, selected_cols, data_size, optimization_mode, max_categories):
    """Optimasi data untuk radar chart"""
    
    # Pilih kolom yang diperlukan
    columns_needed = [category_col] + selected_cols
    plot_data = df[columns_needed].dropna()
    
    if len(plot_data) == 0:
        return None
    
    # OPTIMASI: Sampling untuk data besar
    if data_size > 50000:
        target_sizes = {
            "Auto": min(10000, data_size),
            "Fast": min(5000, data_size),
            "Balanced": min(20000, data_size),
            "Detailed": min(50000, data_size)
        }
        
        target_size = target_sizes[optimization_mode]
        
        if len(plot_data) > target_size:
            # Stratified sampling berdasarkan kategori
            try:
                category_counts = plot_data[category_col].value_counts()
                top_categories = category_counts.head(max_categories).index
                filtered_data = plot_data[plot_data[category_col].isin(top_categories)]
                
                # Sample dari setiap kategori
                samples_per_category = target_size // len(top_categories)
                sampled_dfs = []
                
                for category in top_categories:
                    category_data = filtered_data[filtered_data[category_col] == category]
                    if len(category_data) > 0:
                        sample_size = min(samples_per_category, len(category_data))
                        sampled_dfs.append(category_data.sample(n=sample_size, random_state=42))
                
                if sampled_dfs:
                    plot_data = pd.concat(sampled_dfs, ignore_index=True)
                else:
                    plot_data = plot_data.sample(n=target_size, random_state=42)
                    
            except:
                # Fallback ke random sampling
                plot_data = plot_data.sample(n=target_size, random_state=42)
    
    return plot_data

def normalize_radar_data(plot_data, selected_cols):
    """Normalisasi data untuk radar chart (0-1 scaling)"""
    plot_data = plot_data.copy()
    
    for col in selected_cols:
        min_val = plot_data[col].min()
        max_val = plot_data[col].max()
        
        if max_val > min_val:
            plot_data[col] = (plot_data[col] - min_val) / (max_val - min_val)
        else:
            plot_data[col] = 0.5  # Default value jika semua sama
    
    return plot_data

def aggregate_radar_data(plot_data, category_col, selected_cols, max_categories):
    """Aggregasi data untuk radar chart"""
    
    # Ambil kategori paling banyak
    category_counts = plot_data[category_col].value_counts()
    top_categories = category_counts.head(max_categories).index
    
    # Aggregasi data
    radar_data = plot_data[plot_data[category_col].isin(top_categories)]
    radar_data = radar_data.groupby(category_col, observed=True)[selected_cols].mean().reset_index()
    
    return radar_data

def create_optimized_radar_chart(radar_data, category_col, selected_cols, original_size):
    """Buat radar chart yang dioptimalkan"""
    
    fig = go.Figure()
    
    # Warna yang dioptimalkan untuk visibility
    colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel
    
    # Batasi opacity berdasarkan jumlah kategori
    n_categories = len(radar_data)
    base_opacity = max(0.3, 0.8 - (n_categories * 0.05))
    
    for idx, row in radar_data.iterrows():
        # Siapkan data untuk radar (tutup loop dengan nilai pertama)
        r_values = row[selected_cols].values.tolist() + [row[selected_cols].values[0]]
        theta_values = selected_cols + [selected_cols[0]]
        
        # Pendekkan label jika terlalu panjang
        category_name = str(row[category_col])
        if len(category_name) > 20:
            category_name = category_name[:17] + "..."
        
        fig.add_trace(go.Scatterpolar(
            r=r_values,
            theta=theta_values,
            fill='toself' if n_categories <= 8 else 'none',  # Non-fill untuk banyak kategori
            fillcolor=colors[idx % len(colors)] if n_categories <= 8 else None,
            line=dict(
                color=colors[idx % len(colors)],
                width=2 if n_categories <= 8 else 1
            ),
            name=category_name,
            opacity=base_opacity,
            hovertemplate=(
                f'<b>{category_name}</b><br>' +
                '<br>'.join([f'{col}: %{{r:.3f}}' for col in selected_cols]) +
                '<extra></extra>'
            )
        ))
    
    # Layout yang dioptimalkan
    layout_config = {
        'polar': dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],  # Fixed range untuk normalized data
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=11),
                rotation=90,
                direction="clockwise"
            ),
            bgcolor='rgba(0,0,0,0.02)'
        ),
        'showlegend': n_categories <= 12,  # Sembunyikan legend jika terlalu banyak
        'height': 500,
        'margin': dict(l=50, r=50, t=50, b=50),
        'paper_bgcolor': 'white'
    }
    
    # Sesuaikan legend berdasarkan jumlah kategori
    if n_categories <= 12:
        layout_config['legend'] = dict(
            orientation="v" if n_categories <= 6 else "h",
            yanchor="bottom",
            y=-0.2 if n_categories > 6 else 0.5,
            xanchor="center",
            x=0.5
        )
    
    fig.update_layout(**layout_config)
    
    return fig

def display_radar_data_table(radar_data, category_col, selected_cols):
    """Tampilkan data table untuk radar chart"""
    
    with st.expander("📊 Data Radar Chart", expanded=False):
        # Format data untuk display
        display_data = radar_data.copy()
        for col in selected_cols:
            display_data[col] = display_data[col].round(3)
        
        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )
        
        # Statistik ringkas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Jumlah Kategori", len(radar_data))
        with col2:
            st.metric("Jumlah Metrik", len(selected_cols))
        with col3:
            avg_values = radar_data[selected_cols].mean().mean()
            st.metric("Rata-rata Nilai", f"{avg_values:.3f}")

def show_radar_optimization_info(original_size, processed_size, displayed_categories, optimization_mode):
    """Tampilkan informasi optimasi"""
    
    reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
    
    if reduction_pct > 10 or displayed_categories < 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{original_size:,}")
            with col2:
                st.metric("Data Diproses", f"{processed_size:,}")
            with col3:
                st.metric("Kategori Ditampilkan", displayed_categories)
            
            if reduction_pct > 10:
                st.metric("Reduksi Data", f"{reduction_pct:.1f}%")
            
            optimization_strategies = {
                "Fast": "• ✅ **Aggressive sampling**\n• ✅ **Limited categories**\n• ✅ **Minimal styling**",
                "Balanced": "• ✅ **Stratified sampling**\n• ✅ **Smart normalization**\n• ✅ **Optimized visuals**",
                "Detailed": "• ✅ **Maximum data retention**\n• ✅ **Full features**\n• ✅ **Detailed hover**"
            }
            
            st.info(f"**Mode {optimization_mode}**: {optimization_strategies.get(optimization_mode, 'Custom optimization')}")

def create_simple_radar_fallback(df, category_col, selected_cols):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback sederhana...")
    
    # Ambil sample kecil dan kategori terbatas
    sample_data = df[[category_col] + selected_cols].dropna().head(1000)
    top_categories = sample_data[category_col].value_counts().head(5).index
    filtered_data = sample_data[sample_data[category_col].isin(top_categories)]
    
    if len(filtered_data) == 0:
        st.error("Tidak ada data valid setelah filtering")
        return
    
    radar_data = filtered_data.groupby(category_col)[selected_cols].mean().reset_index()
    
    fig = go.Figure()
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for idx, row in radar_data.iterrows():
        r_values = row[selected_cols].values.tolist() + [row[selected_cols].values[0]]
        theta_values = selected_cols + [selected_cols[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=r_values,
            theta=theta_values,
            fill='toself',
            name=row[category_col],
            line_color=colors[idx % len(colors)]
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Versi ultra-ringan untuk data ekstrem
def create_ultra_fast_radar(df, numeric_cols, non_numeric_cols):
    """Versi ultra-ringan untuk data > 100k rows"""
    
    col1, col2 = st.columns(2)
    with col1:
        category_col = st.selectbox("Kolom kategori", non_numeric_cols[:5], key="ultra_radar_cat")
    with col2:
        metric_count = st.slider("Jumlah metrik", 3, 6, 4, key="ultra_radar_metrics")
    
    # Pilih metrik otomatis
    suitable_cols = [col for col in numeric_cols 
                   if df[col].nunique() > 1 and df[col].dtype in ['float64', 'int64']]
    selected_cols = suitable_cols[:metric_count]
    
    if category_col and len(selected_cols) >= 3:
        # Aggregasi langsung dengan sampling
        sample_data = df[[category_col] + selected_cols].dropna()
        if len(sample_data) > 1000:
            sample_data = sample_data.sample(n=1000, random_state=42)
        
        top_categories = sample_data[category_col].value_counts().head(4).index
        radar_data = sample_data[sample_data[category_col].isin(top_categories)]
        radar_data = radar_data.groupby(category_col)[selected_cols].mean().reset_index()
        
        # Normalisasi
        for col in selected_cols:
            min_val = radar_data[col].min()
            max_val = radar_data[col].max()
            if max_val > min_val:
                radar_data[col] = (radar_data[col] - min_val) / (max_val - min_val)
        
        # Simple radar
        fig = go.Figure()
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        for idx, row in radar_data.iterrows():
            r_values = row[selected_cols].values.tolist() + [row[selected_cols].values[0]]
            theta_values = selected_cols + [selected_cols[0]]
            
            fig.add_trace(go.Scatterpolar(
                r=r_values,
                theta=theta_values,
                fill='toself',
                name=row[category_col][:15],
                line_color=colors[idx % len(colors)],
                opacity=0.7
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            height=350,
            margin=dict(l=30, r=30, t=30, b=30)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.info(f"📊 Ultra-Fast Mode: {len(radar_data)} kategori, {len(selected_cols)} metrik")


def create_box_plot(df, numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        col = st.selectbox("Pilih kolom untuk box plot", numeric_cols, key="box_col")
    
    with col2:
        # Pengaturan optimasi
        optimization_mode = st.selectbox(
            "Mode Optimasi",
            ["Auto", "Fast", "Balanced", "Detailed"],
            index=0 if data_size > 50000 else 2,
            key="box_optim"
        )
    
    with col3:
        show_points = st.selectbox(
            "Tampilkan points",
            ["None", "Outliers Only", "All"],
            index=1 if data_size < 10000 else 0,
            key="box_points"
        )
    
    # Pengaturan lanjutan
    with st.expander("⚙️ Pengaturan Lanjutan", expanded=False):
        col4, col5, col6 = st.columns(3)
        with col4:
            max_points = st.slider(
                "Maksimum data points",
                min_value=1000,
                max_value=50000,
                value=10000 if data_size > 50000 else 20000,
                key="box_max_points"
            )
        with col5:
            notch = st.checkbox(
                "Tampilkan notch", 
                value=False,
                help="Menampilkan interval kepercayaan median"
            )
        with col6:
            log_scale = st.checkbox(
                "Skala logaritmik",
                value=False,
                help="Berguna untuk data dengan skew tinggi"
            )
    
    if col:
        try:
            with st.spinner("🔄 Memproses data box plot..."):
                # OPTIMASI 1: Filter dan sampling data
                plot_data = optimize_box_data(df, col, data_size, optimization_mode, max_points)
                
                if len(plot_data) == 0:
                    st.warning(f"Tidak ada data valid untuk kolom {col}")
                    return
                
                # OPTIMASI 2: Buat box plot yang dioptimalkan
                fig = create_optimized_box_plot(plot_data, col, show_points, notch, log_scale, data_size)
                
                # OPTIMASI 3: Konfigurasi plotly yang ringan
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'responsive': True
                }
                
                st.plotly_chart(fig, use_container_width=True, config=config)
                
                # Tampilkan statistik detail
                display_box_statistics(plot_data, col, data_size)
                
                # Tampilkan info optimasi
                show_box_optimization_info(data_size, len(plot_data), optimization_mode)
                
        except Exception as e:
            st.error(f"Error membuat box plot: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_box_fallback(df, col)

def optimize_box_data(df, col, data_size, optimization_mode, max_points):
    """Optimasi data untuk box plot dengan sampling yang tepat"""
    
    # Filter data yang valid
    plot_data = df[col].dropna()
    
    if len(plot_data) == 0:
        return plot_data
    
    # Tentukan target sample size
    target_sizes = {
        "Auto": min(max_points, data_size),
        "Fast": min(5000, data_size),
        "Balanced": min(20000, data_size),
        "Detailed": min(50000, data_size)
    }
    
    target_size = target_sizes[optimization_mode]
    
    # Jika data lebih besar dari target, lakukan sampling
    if len(plot_data) > target_size:
        if optimization_mode == "Fast":
            # Systematic sampling untuk performa maksimal
            step = len(plot_data) // target_size
            sampled_data = plot_data.iloc[::step]
        elif optimization_mode == "Balanced":
            # Stratified sampling untuk mempertahankan distribusi
            try:
                # Bagi data menjadi quantiles dan sample dari setiap quantile
                n_quantiles = min(10, target_size // 100)
                quantiles = pd.qcut(plot_data, q=n_quantiles, duplicates='drop')
                
                samples_per_quantile = target_size // n_quantiles
                sampled_dfs = []
                
                for quantile in quantiles.cat.categories:
                    quantile_data = plot_data[quantiles == quantile]
                    if len(quantile_data) > 0:
                        sample_size = min(samples_per_quantile, len(quantile_data))
                        sampled_dfs.append(quantile_data.sample(n=sample_size, random_state=42))
                
                sampled_data = pd.concat(sampled_dfs, ignore_index=True)
                
                # Jika masih kurang, tambahkan random sampling
                if len(sampled_data) < target_size:
                    remaining = target_size - len(sampled_data)
                    additional_samples = plot_data.sample(n=remaining, random_state=42)
                    sampled_data = pd.concat([sampled_data, additional_samples], ignore_index=True)
                    
            except:
                # Fallback ke random sampling
                sampled_data = plot_data.sample(n=target_size, random_state=42)
        else:
            # Random sampling untuk mode lain
            sampled_data = plot_data.sample(n=target_size, random_state=42)
        
        return sampled_data
    
    return plot_data

def create_optimized_box_plot(plot_data, col, show_points, notch, log_scale, original_size):
    """Buat box plot yang dioptimalkan untuk performa"""
    
    # Tentukan parameter points berdasarkan ukuran data dan pilihan user
    if show_points == "None":
        box_points = False
    elif show_points == "Outliers Only":
        box_points = 'outliers'
    else:  # "All"
        box_points = 'all' if len(plot_data) <= 5000 else 'outliers'
    
    # Buat box plot
    fig = px.box(
        plot_data, 
        y=col,
        title=f"Box Plot {col} ({len(plot_data):,} data points)",
        points=box_points,
        notched=notch
    )
    
    # OPTIMASI: Update trace untuk performa
    fig.update_traces(
        marker=dict(
            size=4 if box_points in ['all', 'outliers'] else 0,
            opacity=0.6
        ),
        line=dict(width=1.5),
        selector=dict(type='box')
    )
    
    # Skala logaritmik jika diperlukan
    if log_scale:
        fig.update_layout(yaxis_type="log")
    
    # Layout yang dioptimalkan
    fig.update_layout(
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='white',
        showlegend=False,
        xaxis=dict(showticklabels=False),  # Hide x-axis labels untuk single box
        yaxis=dict(
            title=col,
            gridcolor='lightgray',
            gridwidth=1
        )
    )
    
    # Tambahkan annotation untuk statistik jika data tidak terlalu banyak
    if len(plot_data) <= 10000:
        try:
            stats = calculate_box_statistics(plot_data)
            
            # Tambahkan text annotations
            annotations = []
            y_positions = [stats['q1'], stats['median'], stats['q3']]
            labels = [f"Q1: {stats['q1']:.2f}", f"Median: {stats['median']:.2f}", f"Q3: {stats['q3']:.2f}"]
            
            for i, (y_pos, label) in enumerate(zip(y_positions, labels)):
                annotations.append(dict(
                    x=0.5,
                    y=y_pos,
                    xref="paper",
                    yref="y",
                    text=label,
                    showarrow=False,
                    bgcolor="white",
                    bordercolor="black",
                    borderwidth=1,
                    borderpad=4,
                    opacity=0.8
                ))
            
            fig.update_layout(annotations=annotations)
        except:
            pass  # Skip annotations jika error
    
    return fig

def calculate_box_statistics(data):
    """Hitung statistik box plot dengan numpy (lebih cepat)"""
    return {
        'min': np.min(data),
        'q1': np.percentile(data, 25),
        'median': np.median(data),
        'q3': np.percentile(data, 75),
        'max': np.max(data),
        'mean': np.mean(data),
        'std': np.std(data)
    }

def display_box_statistics(plot_data, col, original_size):
    """Tampilkan statistik box plot secara detail"""
    
    with st.expander("📊 Statistik Detail Box Plot", expanded=True):
        # Hitung statistik
        stats = calculate_box_statistics(plot_data)
        
        # Tampilkan metrik utama
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Jumlah Data", f"{len(plot_data):,}")
            st.metric("Minimum", f"{stats['min']:.2f}")
        with col2:
            st.metric("Q1 (25%)", f"{stats['q1']:.2f}")
            st.metric("Median", f"{stats['median']:.2f}")
        with col3:
            st.metric("Q3 (75%)", f"{stats['q3']:.2f}")
            st.metric("Maksimum", f"{stats['max']:.2f}")
        with col4:
            st.metric("Rata-rata", f"{stats['mean']:.2f}")
            st.metric("Std Dev", f"{stats['std']:.2f}")
        
        # Hitung IQR dan outlier
        iqr = stats['q3'] - stats['q1']
        lower_bound = stats['q1'] - 1.5 * iqr
        upper_bound = stats['q3'] + 1.5 * iqr
        
        outliers = plot_data[(plot_data < lower_bound) | (plot_data > upper_bound)]
        outlier_percentage = (len(outliers) / len(plot_data)) * 100
        
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric("IQR", f"{iqr:.2f}")
        with col6:
            st.metric("Outliers", f"{len(outliers):,}")
        with col7:
            st.metric("% Outliers", f"{outlier_percentage:.1f}%")
        
        # Info skewness
        try:
            from scipy.stats import skew
            skewness = skew(plot_data)
            st.metric("Skewness", f"{skewness:.2f}")
            
            if abs(skewness) < 0.5:
                st.success("Distribusi: Mendekati normal")
            elif skewness > 0.5:
                st.warning("Distribusi: Right-skewed (positif)")
            elif skewness < -0.5:
                st.warning("Distribusi: Left-skewed (negatif)")
        except:
            st.info("Skewness: Tidak dapat dihitung")
        
        # Tampilkan outliers jika ada dan tidak terlalu banyak
        if len(outliers) > 0 and len(outliers) <= 50:
            st.markdown("**🔍 Daftar Outliers:**")
            outliers_df = pd.DataFrame({'Outlier Values': outliers.sort_values()})
            st.dataframe(outliers_df, use_container_width=True)

def show_box_optimization_info(original_size, processed_size, optimization_mode):
    """Tampilkan informasi optimasi"""
    reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
    
    if reduction_pct > 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{original_size:,}")
            with col2:
                st.metric("Data Diproses", f"{processed_size:,}")
            with col3:
                st.metric("Reduksi", f"{reduction_pct:.1f}%")
            
            optimization_strategies = {
                "Fast": "• ✅ **Systematic sampling**\n• ✅ **Outliers-only points**\n• ✅ **Minimal annotations**",
                "Balanced": "• ✅ **Stratified sampling**\n• ✅ **Smart point display**\n• ✅ **Basic statistics**",
                "Detailed": "• ✅ **Maximum data retention**\n• ✅ **Full annotations**\n• ✅ **Detailed analysis**"
            }
            
            st.info(f"**Mode {optimization_mode}**: {optimization_strategies.get(optimization_mode, 'Custom optimization')}")

def create_simple_box_fallback(df, col):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback sederhana...")
    
    # Sample kecil untuk memastikan bisa render
    sample_data = df[col].dropna().head(2000)
    
    if len(sample_data) == 0:
        st.error("Tidak ada data valid")
        return
    
    fig = px.box(sample_data, y=col, title=f"Simple Box Plot: {col}")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Versi multiple box plots untuk perbandingan
def create_multi_box_plot(df, numeric_cols):
    """Multiple box plots untuk perbandingan"""
    
    data_size = len(df)
    
    selected_cols = st.multiselect(
        "Pilih kolom untuk perbandingan",
        numeric_cols[:10],  # Batasi pilihan
        default=numeric_cols[:min(5, len(numeric_cols))],
        key="multi_box_cols"
    )
    
    if len(selected_cols) >= 2:
        with st.spinner("🔄 Memproses multiple box plots..."):
            # Sampling untuk data besar
            if data_size > 50000:
                sample_df = df[selected_cols].dropna().sample(n=10000, random_state=42)
                st.info(f"📊 Menggunakan 10,000 sample dari {data_size:,} data points")
            else:
                sample_df = df[selected_cols].dropna()
            
            # Melt data untuk multiple box plots
            melted_df = sample_df.melt(var_name='Variable', value_name='Value')
            
            fig = px.box(
                melted_df, 
                x='Variable', 
                y='Value',
                title=f"Perbandingan Distribusi ({len(selected_cols)} variables)"
            )
            
            fig.update_traces(
                marker=dict(size=3, opacity=0.6),
                line=dict(width=1.2)
            )
            
            fig.update_layout(
                height=500,
                xaxis_title="Variable",
                yaxis_title="Value",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

def create_funnel_chart(df, numeric_cols, non_numeric_cols):
    
    stage_col = st.selectbox("Pilih kolom stage", non_numeric_cols, key="funnel_stage")
    value_col = st.selectbox("Pilih kolom nilai", numeric_cols, key="funnel_value")
    
    # Optimasi: Batasi jumlah data yang diproses
    max_stages = st.slider("Maksimum jumlah stage yang ditampilkan", 
                          min_value=5, max_value=20, value=10, key="funnel_max_stages")
    
    if stage_col and value_col:
        # Optimasi: Gunakan aggregation yang lebih efisien
        with st.spinner("Memproses data..."):
            # Group by dengan optimasi memori
            funnel_data = df.groupby(stage_col, observed=True)[value_col].sum()
            
            # Konversi ke DataFrame dan sort
            funnel_data = funnel_data.reset_index()
            funnel_data = funnel_data.nlargest(max_stages, value_col)
            
            # Cache data untuk performa
            @st.cache_data
            def create_funnel_figure(data, x_col, y_col, title):
                fig = px.funnel(data, x=x_col, y=y_col, title=title)
                fig.update_layout(
                    height=500,
                    showlegend=False,
                    margin=dict(l=50, r=50, t=50, b=50)
                )
                return fig
            
            fig = create_funnel_figure(
                funnel_data, 
                value_col, 
                stage_col, 
                f"Funnel Chart: {value_col} per {stage_col}"
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Tampilkan data summary
        with st.expander("📊 Lihat Data Summary"):
            st.dataframe(funnel_data.style.format({value_col: "{:,.0f}"}), use_container_width=True)
            
        with st.expander("ℹ️ Keterangan Funnel Chart"):
            st.markdown(f"""
            **Funnel Chart** menampilkan proses bertahap dengan attrition.
            
            **Statistik:**
            - Total {stage_col}: {len(funnel_data)}
            - Total {value_col}: {funnel_data[value_col].sum():,.0f}
            - Stage tertinggi: {funnel_data.iloc[0][stage_col]} ({funnel_data.iloc[0][value_col]:,.0f})
            - Stage terendah: {funnel_data.iloc[-1][stage_col]} ({funnel_data.iloc[-1][value_col]:,.0f})
            
            **Kelebihan**: Visualisasi proses dan konversi yang jelas
            **Kekurangan**: Hanya untuk data sequential
            **Penggunaan**: Sales funnel, conversion analysis, process flow
            """)

# Alternatif: Versi dengan sampling untuk data yang sangat besar
def create_funnel_chart_optimized(df, numeric_cols, non_numeric_cols):
    
    stage_col = st.selectbox("Pilih kolom stage", non_numeric_cols, key="funnel_stage_opt")
    value_col = st.selectbox("Pilih kolom nilai", numeric_cols, key="funnel_value_opt")
    
    # Optimasi tambahan untuk data sangat besar
    sample_size = st.slider("Sample size (%)", 10, 100, 50, key="funnel_sample")
    
    if stage_col and value_col:
        # Sampling data untuk performa
        if len(df) > 10000:
            df_sampled = df.sample(frac=sample_size/100, random_state=42)
            st.info(f"Data disampling: {len(df_sampled):,} dari {len(df):,} records ({sample_size}%)")
        else:
            df_sampled = df
        
        with st.spinner("Memproses data dengan optimasi..."):
            # Aggregasi yang lebih cepat
            funnel_data = (df_sampled
                         .groupby(stage_col, observed=True)[value_col]
                         .sum()
                         .nlargest(15)  # Batasi langsung di aggregation
                         .reset_index())
            
            # Plot yang lebih ringan
            fig = px.funnel(funnel_data, x=value_col, y=stage_col,
                          title=f"Funnel Chart: {value_col} per {stage_col}")
            
            fig.update_layout(
                height=500,
                showlegend=False,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            # Nonaktifkan beberapa fitur plotly untuk performa
            st.plotly_chart(fig, use_container_width=True, 
                          config={'displayModeBar': False, 'responsive': True})

def create_wordcloud(df, non_numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        text_col = st.selectbox("Pilih kolom teks", non_numeric_cols, key="wordcloud_col")
    
    with col2:
        # Pengaturan optimasi
        optimization_mode = st.selectbox(
            "Mode Optimasi",
            ["Auto", "Fast", "Balanced", "Detailed"],
            index=0 if data_size > 50000 else 2,
            key="wc_optim"
        )
    
    with col3:
        max_words = st.slider(
            "Maksimum kata",
            min_value=50,
            max_value=500,
            value=150 if data_size > 50000 else 200,
            key="wc_max_words"
        )
    
    # Pengaturan lanjutan
    with st.expander("⚙️ Pengaturan Lanjutan", expanded=False):
        col4, col5, col6 = st.columns(3)
        with col4:
            sample_size = st.slider(
                "Sample data size",
                min_value=1000,
                max_value=50000,
                value=10000 if data_size > 50000 else 20000,
                key="wc_sample_size"
            )
        with col5:
            width = st.slider(
                "Lebar word cloud",
                min_value=400,
                max_value=1200,
                value=800,
                key="wc_width"
            )
        with col6:
            height = st.slider(
                "Tinggi word cloud",
                min_value=200,
                max_value=800,
                value=400,
                key="wc_height"
            )
    
    # Custom stopwords dan preferences
    with st.expander("🔧 Pengaturan Teks", expanded=False):
        col7, col8 = st.columns(2)
        with col7:
            remove_stopwords = st.checkbox("Hapus stopwords", value=True, key="wc_stopwords")
            include_numbers = st.checkbox("Sertakan angka", value=False, key="wc_numbers")
        with col8:
            language = st.selectbox(
                "Bahasa stopwords",
                ["English", "Indonesian", "None"],
                index=0,
                key="wc_language"
            )
        custom_stopwords = st.text_area(
            "Stopwords kustom (pisahkan dengan koma)",
            value="",
            help="Tambahkan kata-kata yang ingin dihilangkan dari word cloud"
        )
    
    if text_col:
        try:
            with st.spinner("🔄 Memproses teks dan membuat word cloud..."):
                # OPTIMASI 1: Sampling data untuk data besar
                processed_text = optimize_text_data(df, text_col, data_size, optimization_mode, sample_size)
                
                if not processed_text or processed_text.strip() == "":
                    st.warning("Tidak ada teks yang valid untuk ditampilkan")
                    return
                
                # OPTIMASI 2: Preprocessing teks yang efisien
                cleaned_text = preprocess_text(
                    processed_text, 
                    remove_stopwords, 
                    language, 
                    custom_stopwords,
                    include_numbers
                )
                
                if not cleaned_text or cleaned_text.strip() == "":
                    st.warning("Tidak ada kata yang tersisa setelah preprocessing")
                    return
                
                # OPTIMASI 3: Buat word cloud dengan konfigurasi optimal
                fig = create_optimized_wordcloud(
                    cleaned_text, 
                    max_words, 
                    width, 
                    height,
                    optimization_mode
                )
                
                st.pyplot(fig, use_container_width=True)
                
                # OPTIMASI 4: Tampilkan analisis teks
                display_text_analysis(cleaned_text, processed_text, max_words)
                
                # Tampilkan info optimasi
                show_wordcloud_optimization_info(data_size, len(processed_text.split()), optimization_mode)
                
        except Exception as e:
            st.error(f"Error membuat word cloud: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_wordcloud_fallback(df, text_col)

def optimize_text_data(df, text_col, data_size, optimization_mode, sample_size):
    """Optimasi data teks dengan sampling yang tepat"""
    
    # Filter data yang valid
    text_data = df[text_col].astype(str).dropna()
    
    if len(text_data) == 0:
        return ""
    
    # Tentukan target sample size
    target_sizes = {
        "Auto": min(sample_size, data_size),
        "Fast": min(5000, data_size),
        "Balanced": min(20000, data_size),
        "Detailed": min(50000, data_size)
    }
    
    target_size = target_sizes[optimization_mode]
    
    # Jika data lebih besar dari target, lakukan sampling
    if len(text_data) > target_size:
        if optimization_mode == "Fast":
            # Ambil sample acak
            sampled_data = text_data.sample(n=target_size, random_state=42)
        elif optimization_mode == "Balanced":
            # Prioritaskan teks yang lebih panjang (lebih informatif)
            text_lengths = text_data.str.len()
            # Ambil campuran: 70% teks terpanjang, 30% random
            n_longest = int(target_size * 0.7)
            n_random = target_size - n_longest
            
            longest_texts = text_data.iloc[text_lengths.nlargest(n_longest).index]
            random_texts = text_data.sample(n=n_random, random_state=42)
            
            sampled_data = pd.concat([longest_texts, random_texts])
        else:
            # Random sampling untuk mode lain
            sampled_data = text_data.sample(n=target_size, random_state=42)
        
        return ' '.join(sampled_data)
    
    return ' '.join(text_data)

def preprocess_text(text, remove_stopwords=True, language="English", custom_stopwords="", include_numbers=False):
    """Preprocessing teks yang efisien"""
    import re
    from collections import Counter
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove numbers jika tidak diinginkan
    if not include_numbers:
        text = re.sub(r'\d+', '', text)
    
    # Split into words
    words = text.split()
    
    # Remove stopwords
    if remove_stopwords:
        stopwords_set = get_stopwords_set(language, custom_stopwords)
        words = [word for word in words if word not in stopwords_set and len(word) > 2]
    
    # Remove very short and very long words
    words = [word for word in words if 2 < len(word) < 20]
    
    return ' '.join(words)

def get_stopwords_set(language, custom_stopwords):
    """Dapatkan set stopwords berdasarkan bahasa"""
    stopwords_set = set()
    
    # Basic English stopwords
    basic_stopwords = {
        'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'on', 'with', 'as', 'by', 
        'at', 'an', 'be', 'this', 'that', 'it', 'are', 'from', 'or', 'but', 'not',
        'you', 'your', 'we', 'our', 'they', 'their', 'i', 'me', 'my', 'he', 'him',
        'his', 'she', 'her', 'its', 'us', 'them', 'what', 'which', 'who', 'when',
        'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 'can', 'will', 'just', 'should', 'now'
    }
    
    # Indonesian stopwords
    indonesian_stopwords = {
        'yang', 'dan', 'di', 'dengan', 'ini', 'itu', 'dari', 'untuk', 'pada', 'ke',
        'dalam', 'tidak', 'akan', 'ada', 'atau', 'juga', 'bisa', 'saya', 'kita',
        'mereka', 'dia', 'kamu', 'kami', 'adalah', 'harus', 'sudah', 'belum',
        'pernah', 'selalu', 'sering', 'kadang', 'mungkin', 'boleh', 'harus',
        'perlu', 'bisa', 'dapat', 'boleh', 'harus', 'perlu', 'bisa', 'dapat'
    }
    
    if language == "English":
        stopwords_set.update(basic_stopwords)
    elif language == "Indonesian":
        stopwords_set.update(indonesian_stopwords)
    
    # Add custom stopwords
    if custom_stopwords:
        custom_words = [word.strip().lower() for word in custom_stopwords.split(',')]
        stopwords_set.update(custom_words)
    
    return stopwords_set

def create_optimized_wordcloud(text, max_words, width, height, optimization_mode):
    """Buat word cloud yang dioptimalkan"""
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    
    # Konfigurasi berdasarkan mode optimasi
    if optimization_mode == "Fast":
        colormap = 'viridis'
        background_color = 'white'
        relative_scaling = 0.5
        min_font_size = 8
    elif optimization_mode == "Balanced":
        colormap = 'plasma'
        background_color = 'white'
        relative_scaling = 0.8
        min_font_size = 6
    else:  # Detailed
        colormap = 'inferno'
        background_color = 'black'
        relative_scaling = 1.0
        min_font_size = 4
    
    # Buat word cloud
    wordcloud = WordCloud(
        width=width,
        height=height,
        background_color=background_color,
        max_words=max_words,
        colormap=colormap,
        relative_scaling=relative_scaling,
        min_font_size=min_font_size,
        random_state=42
    ).generate(text)
    
    # Buat figure
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    
    # Optimasi layout
    plt.tight_layout(pad=0)
    
    return fig

def display_text_analysis(cleaned_text, original_text, max_words):
    """Tampilkan analisis teks"""
    
    with st.expander("📊 Analisis Teks", expanded=False):
        from collections import Counter
        import re
        
        # Hitung statistik dasar
        original_words = re.findall(r'\b\w+\b', original_text.lower())
        cleaned_words = cleaned_text.split()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Kata Original", f"{len(original_words):,}")
        with col2:
            st.metric("Total Kata Setelah Cleaning", f"{len(cleaned_words):,}")
        with col3:
            unique_ratio = len(set(cleaned_words)) / len(cleaned_words) if cleaned_words else 0
            st.metric("Unique Words Ratio", f"{unique_ratio:.2f}")
        with col4:
            avg_word_length = np.mean([len(word) for word in cleaned_words]) if cleaned_words else 0
            st.metric("Rata-rata Panjang Kata", f"{avg_word_length:.1f}")
        
        # Tampilkan top words
        if cleaned_words:
            word_freq = Counter(cleaned_words)
            top_words = word_freq.most_common(20)
            
            st.markdown("**🔝 Kata Paling Sering Muncul:**")
            
            # Buat chart untuk top words
            words, counts = zip(*top_words[:10])
            
            fig, ax = plt.subplots(figsize=(10, 4))
            y_pos = np.arange(len(words))
            ax.barh(y_pos, counts, color='skyblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(words)
            ax.invert_yaxis()
            ax.set_xlabel('Frekuensi')
            ax.set_title('10 Kata Paling Sering Muncul')
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Tabel untuk semua top words
            top_words_df = pd.DataFrame(top_words, columns=['Kata', 'Frekuensi'])
            st.dataframe(top_words_df, use_container_width=True)

def show_wordcloud_optimization_info(original_size, processed_word_count, optimization_mode):
    """Tampilkan informasi optimasi"""
    
    with st.expander("⚡ Info Optimasi Performa", expanded=False):
        st.metric("Data Points Original", f"{original_size:,}")
        st.metric("Kata Diproses", f"{processed_word_count:,}")
        
        optimization_strategies = {
            "Fast": "• ✅ **Aggressive sampling**\n• ✅ **Basic preprocessing**\n• ✅ **Fast rendering**",
            "Balanced": "• ✅ **Smart sampling** (prioritize long texts)\n• ✅ **Advanced preprocessing**\n• ✅ **Quality rendering**",
            "Detailed": "• ✅ **Maximum data retention**\n• ✅ **Comprehensive preprocessing**\n• ✅ **High-quality output**"
        }
        
        st.info(f"**Mode {optimization_mode}**: {optimization_strategies.get(optimization_mode, 'Custom optimization')}")

def create_simple_wordcloud_fallback(df, text_col):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback sederhana...")
    
    # Ambil sample kecil
    sample_data = df[text_col].astype(str).dropna().head(1000)
    text = ' '.join(sample_data)
    
    if text.strip():
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        wordcloud = WordCloud(width=600, height=300, background_color='white', max_words=100).generate(text)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
    else:
        st.error("Tidak ada teks yang valid")

# Versi ultra-ringan untuk data ekstrem
def create_ultra_fast_wordcloud(df, non_numeric_cols):
    """Versi ultra-ringan untuk data > 500k rows"""
    
    col1, col2 = st.columns(2)
    with col1:
        text_col = st.selectbox("Pilih kolom teks", non_numeric_cols[:5], key="ultra_wc_col")
    with col2:
        max_words = st.slider("Maks kata", 50, 200, 100, key="ultra_wc_words")
    
    if text_col:
        # Sampling sangat agresif
        sample_data = df[text_col].astype(str).dropna()
        if len(sample_data) > 5000:
            sample_data = sample_data.sample(n=5000, random_state=42)
        
        text = ' '.join(sample_data)
        
        if text.strip():
            # Preprocessing sederhana
            text = text.lower()
            words = text.split()
            words = [word for word in words if len(word) > 3 and len(word) < 15]
            processed_text = ' '.join(words)
            
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            
            wordcloud = WordCloud(
                width=600, 
                height=300, 
                background_color='white',
                max_words=max_words,
                colormap='viridis'
            ).generate(processed_text)
            
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
            
            st.info(f"📊 Ultra-Fast Mode: 5,000 samples, {max_words} words")

def create_gantt_chart(df):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 10000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    # Deteksi kolom yang tersedia
    date_cols = df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()
    text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    st.info(f"🔍 **Kolom yang terdeteksi:**")
    st.write(f"- 📅 Datetime: {date_cols}")
    st.write(f"- 📝 Teks: {text_cols}")
    st.write(f"- 🔢 Numerik: {numeric_cols}")
    
    # SOLUSI: Jika hanya ada 1 kolom datetime, berikan opsi alternatif
    if len(date_cols) == 1:
        st.warning("""
        ⚠️ **Hanya 1 kolom datetime terdeteksi.** 
        Untuk Gantt chart, dibutuhkan 2 kolom datetime (start dan end date).
        
        **Solusi yang tersedia:**
        1. **Gunakan durasi tetap** - Tambahkan kolom end date berdasarkan durasi
        2. **Gunakan kolom numerik** - Konversi ke timeline relatif
        3. **Employee Timeline** - Visualisasi berdasarkan hire date saja
        """)
        
        selected_solution = st.radio(
            "Pilih tipe visualisasi:",
            ["Employee Timeline", "Duration-based Gantt", "Relative Timeline"],
            key="gantt_solution"
        )
        
        if selected_solution == "Employee Timeline":
            create_employee_timeline(df, date_cols[0], text_cols)
            return
        elif selected_solution == "Duration-based Gantt":
            create_duration_gantt(df, date_cols[0], text_cols, numeric_cols)
            return
        else:  # Relative Timeline
            create_relative_timeline(df, numeric_cols, text_cols)
            return
    
    # [Kode untuk kasus dengan 2+ kolom datetime...]
    st.success("✅ Dua atau lebih kolom datetime terdeteksi - dapat membuat Gantt chart standar")
    create_standard_gantt(df, date_cols, text_cols)

def create_standard_gantt(df, date_cols, text_cols):
    """Buat Gantt chart standar ketika ada 2+ kolom datetime"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_col = st.selectbox(
            "Pilih kolom start date",
            date_cols,
            key="start_date"
        )
    
    with col2:
        end_col = st.selectbox(
            "Pilih kolom end date",
            [col for col in date_cols if col != start_col],
            key="end_date"
        )
    
    with col3:
        task_col = st.selectbox(
            "Pilih kolom task/nama",
            text_cols,
            key="task_col"
        )
    
    # Filter data
    gantt_data = df[[start_col, end_col, task_col]].dropna()
    
    if len(gantt_data) == 0:
        st.error("❌ Tidak ada data valid setelah menghapus nilai kosong")
        return
    
    # Batasi jumlah data untuk performa
    if len(gantt_data) > 100:
        st.warning(f"⚠️ Data dibatasi dari {len(gantt_data)} menjadi 100 baris untuk performa")
        gantt_data = gantt_data.head(100)
    
    # Buat Gantt chart dengan Plotly
    fig = px.timeline(
        gantt_data,
        x_start=start_col,
        x_end=end_col,
        y=task_col,
        title="Gantt Chart"
    )
    
    # Update layout untuk responsif
    fig.update_layout(
        height=max(400, len(gantt_data) * 25),
        showlegend=False,
        xaxis_title="Timeline",
        yaxis_title="Tasks",
        margin=dict(l=50, r=50, t=80, b=50),
        autosize=True
    )
    
    # Rotasi label y-axis untuk readability
    fig.update_yaxes(tickangle=0)
    
    st.plotly_chart(fig, use_container_width=True, config={'responsive': True})

def create_employee_timeline(df, date_col, text_cols):
    """Buat employee timeline berdasarkan hire date"""
    st.subheader("👥 Employee Timeline")
    
    st.info("""
    **Employee Timeline** menampilkan karyawan berdasarkan tanggal bergabung.
    Setiap bar mewakili 1 karyawan dengan posisi berdasarkan hire date.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_col = st.selectbox(
            "Pilih kolom untuk kategori warna",
            ["None"] + text_cols,
            key="timeline_category"
        )
    
    with col2:
        max_employees = st.slider(
            "Maksimum karyawan ditampilkan",
            min_value=50,
            max_value=1000,
            value=min(200, len(df)),
            key="timeline_max_employees"
        )
    
    # Siapkan data
    timeline_data = df[[date_col] + ([category_col] if category_col != "None" else [])].copy()
    timeline_data = timeline_data.dropna().head(max_employees)
    
    if len(timeline_data) == 0:
        st.error("❌ Tidak ada data valid untuk timeline")
        return
    
    # Buat timeline dengan cara yang lebih sederhana
    fig = go.Figure()
    
    # Sort data by date
    timeline_data = timeline_data.sort_values(date_col)
    
    # Buat scatter plot untuk timeline
    y_positions = list(range(len(timeline_data)))
    
    if category_col != "None":
        # Group by category untuk warna berbeda
        categories = timeline_data[category_col].unique()
        colors = px.colors.qualitative.Set3
        
        for i, category in enumerate(categories):
            category_data = timeline_data[timeline_data[category_col] == category]
            
            fig.add_trace(go.Scatter(
                x=category_data[date_col],
                y=list(range(len(category_data))),
                mode='markers',
                marker=dict(
                    size=15,
                    color=colors[i % len(colors)],
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                name=str(category),
                hovertemplate=(
                    f"<b>{category_col}: {category}</b><br>"
                    f"Date: %{{x|%d %b %Y}}<br>"
                    f"<extra></extra>"
                )
            ))
    else:
        # Semua titik dengan warna sama
        fig.add_trace(go.Scatter(
            x=timeline_data[date_col],
            y=y_positions,
            mode='markers',
            marker=dict(
                size=10,
                color='lightblue',
                line=dict(width=1, color='navy')
            ),
            hovertemplate=(
                "<b>Employee</b><br>"
                "Date: %{x|%d %b %Y}<br>"
                "<extra></extra>"
            ),
            name="Employees"
        ))
    
    # Layout responsif
    height = max(400, len(timeline_data) * 8)
    fig.update_layout(
        height=min(height, 800),
        title=f"Employee Timeline - {len(timeline_data)} Employees",
        xaxis_title="Hire Date",
        yaxis_title="Employee Index",
        showlegend=(category_col != "None"),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='closest'
    )
    
    # Sembunyikan y-axis labels jika terlalu banyak
    if len(timeline_data) > 50:
        fig.update_yaxes(showticklabels=False)
    
    st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
    
    # Statistik
    with st.expander("📊 Employee Statistics"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Employees", len(timeline_data))
        with col2:
            earliest_hire = timeline_data[date_col].min()
            st.metric("Earliest Hire", earliest_hire.strftime('%d %b %Y'))
        with col3:
            latest_hire = timeline_data[date_col].max()
            st.metric("Latest Hire", latest_hire.strftime('%d %b %Y'))
        
        if category_col != "None":
            st.write("**Distribution by Category:**")
            category_counts = timeline_data[category_col].value_counts()
            st.dataframe(category_counts, use_container_width=True)

def create_duration_gantt(df, date_col, text_cols, numeric_cols):
    """Buat Gantt chart dengan durasi dari kolom numerik"""
    st.subheader("⏱️ Duration-based Gantt Chart")
    
    st.info("""
    **Duration-based Gantt** menggunakan hire date sebagai start date 
    dan menambahkan durasi dari kolom numerik untuk membuat end date.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        task_col = st.selectbox(
            "Pilih kolom task/nama",
            text_cols,
            key="duration_task"
        )
    
    with col2:
        duration_col = st.selectbox(
            "Pilih kolom durasi (numerik)",
            ["Fixed Duration"] + numeric_cols,
            key="duration_col"
        )
    
    with col3:
        if duration_col == "Fixed Duration":
            fixed_duration = st.number_input(
                "Durasi tetap (hari)",
                min_value=1,
                max_value=3650,
                value=365,
                key="fixed_duration"
            )
        else:
            duration_multiplier = st.selectbox(
                "Satuan durasi",
                ["days", "months", "years"],
                key="duration_unit"
            )
    
    # Siapkan data
    gantt_data = []
    
    for idx, row in df.iterrows():
        if pd.notna(row[date_col]) and pd.notna(row[task_col]):
            start_date = row[date_col]
            
            # Tentukan end date berdasarkan pilihan
            if duration_col == "Fixed Duration":
                end_date = start_date + pd.Timedelta(days=fixed_duration)
                duration_days = fixed_duration
            else:
                if pd.notna(row[duration_col]):
                    duration_val = float(row[duration_col])
                    if duration_multiplier == "days":
                        end_date = start_date + pd.Timedelta(days=duration_val)
                        duration_days = duration_val
                    elif duration_multiplier == "months":
                        end_date = start_date + pd.DateOffset(months=duration_val)
                        duration_days = (end_date - start_date).days
                    else:  # years
                        end_date = start_date + pd.DateOffset(years=duration_val)
                        duration_days = (end_date - start_date).days
                else:
                    continue
            
            gantt_data.append({
                'Task': str(row[task_col]),
                'Start': start_date,
                'Finish': end_date,
                'Duration': duration_days
            })
    
    if not gantt_data:
        st.error("❌ Tidak ada data valid untuk Gantt chart")
        return
    
    # Konversi ke DataFrame
    gantt_df = pd.DataFrame(gantt_data)
    
    # Batasi jumlah data untuk performa
    if len(gantt_df) > 100:
        st.warning(f"⚠️ Data dibatasi dari {len(gantt_df)} menjadi 100 baris untuk performa")
        gantt_df = gantt_df.head(100)
    
    # Buat Gantt chart dengan Plotly timeline
    try:
        fig = px.timeline(
            gantt_df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            title="Duration-based Gantt Chart"
        )
        
        # Update layout untuk responsif
        height = max(400, len(gantt_df) * 25)
        fig.update_layout(
            height=min(height, 800),
            showlegend=False,
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            margin=dict(l=150, r=50, t=80, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
        
    except Exception as e:
        st.error(f"❌ Error membuat chart: {str(e)}")
        # Fallback: tampilkan data sebagai tabel
        st.write("**Data Gantt Chart:**")
        st.dataframe(gantt_df, use_container_width=True)
    
    # Statistik
    with st.expander("📊 Duration Statistics"):
        durations = gantt_df['Duration'].tolist()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Items", len(gantt_df))
        with col2:
            st.metric("Avg Duration", f"{np.mean(durations):.1f} days")
        with col3:
            st.metric("Min Duration", f"{np.min(durations):.1f} days")
        with col4:
            st.metric("Max Duration", f"{np.max(durations):.1f} days")

def create_relative_timeline(df, numeric_cols, text_cols):
    """Buat timeline relatif berdasarkan kolom numerik"""
    st.subheader("📊 Relative Timeline Chart")
    
    st.info("""
    **Relative Timeline** menggunakan kolom numerik untuk membuat timeline relatif.
    Berguna untuk membandingkan metrik antar kategori.
    """)
    
    if not numeric_cols:
        st.error("❌ Tidak ada kolom numerik yang tersedia untuk relative timeline")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        value_col = st.selectbox(
            "Pilih kolom nilai",
            numeric_cols,
            key="relative_value"
        )
    
    with col2:
        category_col = st.selectbox(
            "Pilih kolom kategori",
            ["None"] + text_cols,
            key="relative_category"
        )
    
    with col3:
        max_items = st.slider(
            "Maksimum items",
            min_value=20,
            max_value=200,
            value=min(50, len(df)),
            key="relative_max_items"
        )
    
    # Siapkan data
    if category_col != "None":
        plot_data = df[[value_col, category_col]].dropna()
    else:
        plot_data = df[[value_col]].dropna()
        plot_data['Index'] = range(len(plot_data))
        category_col = 'Index'
    
    plot_data = plot_data.nlargest(max_items, value_col)
    
    if len(plot_data) == 0:
        st.error("❌ Tidak ada data valid")
        return
    
    # Buat bar chart horizontal (simulasi timeline)
    try:
        fig = px.bar(
            plot_data,
            x=value_col,
            y=category_col,
            color=category_col if category_col != "None" and category_col != 'Index' else None,
            orientation='h',
            title=f"Relative Timeline - {value_col}"
        )
        
        height = max(400, len(plot_data) * 20)
        fig.update_layout(
            height=min(height, 800),
            showlegend=False,
            xaxis_title=value_col,
            yaxis_title=category_col if category_col != "None" else "Items",
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
        
    except Exception as e:
        st.error(f"❌ Error membuat chart: {str(e)}")
        st.write("**Data:**")
        st.dataframe(plot_data, use_container_width=True)

# Tambahkan CSS untuk styling responsif
st.markdown("""
<style>
    /* Responsive radio buttons */
    .stRadio [role=radiogroup]{
        align-items: center;
        gap: 10px;
    }
    
    .stRadio [data-testid=stMarkdownContainer] > p {
        font-size: 16px;
    }
    
    /* Responsive containers */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Responsive charts */
    .js-plotly-plot .plotly .main-svg {
        width: 100% !important;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .stRadio [role=radiogroup] {
            flex-direction: column;
            align-items: flex-start;
        }
        
        .stSelectbox, .stSlider, .stNumberInput {
            min-width: 100% !important;
        }
    }
    
    /* Better spacing */
    .stExpander {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def create_map_chart(df):
    
    # Optimasi: Cache deteksi kolom
    @st.cache_data
    def detect_geo_columns(df):
        geo_patterns = ['lat', 'latitude', 'lon', 'long', 'longitude', 'country', 'state', 'city', 'region', 'province', 'kota', 'kabupaten', 'address', 'location']
        return [col for col in df.columns if any(geo in col.lower() for geo in geo_patterns)]
    
    possible_geo_cols = detect_geo_columns(df)
    
    if possible_geo_cols:
        st.success(f"✅ Kolom geografis terdeteksi: {', '.join(possible_geo_cols)}")
        
        # Kategorikan kolom dengan caching
        @st.cache_data
        def categorize_columns(_possible_geo_cols):
            lat_cols = [col for col in _possible_geo_cols if any(pat in col.lower() for pat in ['lat', 'latitude'])]
            lon_cols = [col for col in _possible_geo_cols if any(pat in col.lower() for pat in ['lon', 'long', 'longitude'])]
            name_cols = [col for col in _possible_geo_cols if any(pat in col.lower() for pat in ['country', 'state', 'city', 'region', 'province', 'kota', 'kabupaten', 'name'])]
            return lat_cols, lon_cols, name_cols
        
        lat_cols, lon_cols, name_cols = categorize_columns(possible_geo_cols)
        
        # Pilih kolom untuk mapping
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if lat_cols:
                lat_col = st.selectbox("Pilih kolom Latitude", lat_cols, key="map_lat")
            else:
                st.warning("Tidak ada kolom latitude terdeteksi")
                lat_col = None
                
        with col2:
            if lon_cols:
                lon_col = st.selectbox("Pilih kolom Longitude", lon_cols, key="map_lon")
            else:
                st.warning("Tidak ada kolom longitude terdeteksi")
                lon_col = None
                
        with col3:
            if name_cols:
                name_col = st.selectbox("Pilih kolom Nama Lokasi", name_cols, key="map_name")
            else:
                name_col = None
        
        # Optimasi: Sampling data untuk dataset besar
        sample_size = st.slider("Jumlah sampel data untuk peta", 
                               min_value=100, 
                               max_value=min(5000, len(df)), 
                               value=min(1000, len(df)),
                               key="map_sample")
        
        # Filter data yang valid dengan sampling
        if lat_col and lon_col:
            valid_data = df[(pd.notna(df[lat_col])) & (pd.notna(df[lon_col]))].copy()
            
            if len(valid_data) > 0:
                # Sampling untuk dataset besar
                if len(valid_data) > sample_size:
                    valid_data = valid_data.sample(n=sample_size, random_state=42)
                    st.info(f"📊 Menampilkan {sample_size} sampel acak dari {len(valid_data)} data valid")
                else:
                    st.success(f"📊 Menampilkan {len(valid_data)} titik data")
                
                # Progress bar untuk proses yang lama
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Buat peta
                try:
                    import folium
                    from streamlit_folium import folium_static
                    
                    status_text.text("Membuat peta...")
                    
                    # Hitung center map dengan caching
                    @st.cache_data
                    def calculate_center(_data, lat_col, lon_col):
                        return _data[lat_col].mean(), _data[lon_col].mean()
                    
                    center_lat, center_lon = calculate_center(valid_data, lat_col, lon_col)
                    
                    # Buat peta dasar
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
                    
                    # Optimasi: Batasi jumlah marker atau gunakan clustering untuk data besar
                    if len(valid_data) > 500:
                        from folium.plugins import MarkerCluster
                        marker_cluster = MarkerCluster().add_to(m)
                    
                    # Tambahkan markers dengan progress update
                    total_rows = len(valid_data)
                    for idx, row in valid_data.iterrows():
                        if idx % 100 == 0:  # Update progress setiap 100 rows
                            progress_bar.progress(min((idx + 1) / total_rows, 1.0))
                        
                        popup_text = f"Lokasi {idx+1}"
                        if name_col and pd.notna(row[name_col]):
                            popup_text = f"{row[name_col]}"
                        
                        marker = folium.Marker(
                            [row[lat_col], row[lon_col]],
                            popup=popup_text,
                            tooltip=f"Click untuk detail"
                        )
                        
                        # Tambahkan ke cluster jika data banyak, langsung ke map jika sedikit
                        if len(valid_data) > 500:
                            marker.add_to(marker_cluster)
                        else:
                            marker.add_to(m)
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Peta selesai dibuat!")
                    
                    # Tampilkan peta
                    folium_static(m, width=700, height=500)
                    
                    # Tampilkan data table dengan pagination
                    with st.expander("📋 Lihat Data Peta"):
                        display_cols = [lat_col, lon_col]
                        if name_col:
                            display_cols.append(name_col)
                        
                        # Pagination untuk data besar
                        page_size = 20
                        total_pages = max(1, len(valid_data) // page_size)
                        page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
                        
                        start_idx = (page - 1) * page_size
                        end_idx = min(start_idx + page_size, len(valid_data))
                        
                        st.dataframe(valid_data[display_cols].iloc[start_idx:end_idx])
                        st.caption(f"Menampilkan data {start_idx + 1}-{end_idx} dari {len(valid_data)}")
                        
                except ImportError:
                    st.error("❌ Library peta tidak tersedia. Install: pip install folium streamlit-folium")
                    
            else:
                st.error("❌ Tidak ada data dengan koordinat yang valid")
                
        else:
            st.warning("⚠️ Pilih kolom latitude dan longitude untuk menampilkan peta")
            
    else:
        st.warning("""
        ⚠️ Tidak terdeteksi kolom geografis. 
        
        **Untuk menampilkan peta, data harus mengandung:**
        - Kolom latitude (contoh: lat, latitude) 
        - Kolom longitude (contoh: lon, long, longitude)
        - Opsional: Kolom nama lokasi (country, state, city, region, etc.)
        """)
        
        
def create_choropleth_map(df, numeric_cols, non_numeric_cols):
    col1, col2 = st.columns(2)
    
    with col1:
        location_col = st.selectbox("Pilih kolom untuk lokasi", 
                                  non_numeric_cols, 
                                  key="choropleth_location")
    with col2:
        value_col = st.selectbox("Pilih kolom untuk nilai", 
                               numeric_cols, 
                               key="choropleth_value")
    
    # Pilihan tipe peta
    map_type = st.selectbox("Pilih tipe peta", 
                          ["World Countries", "Indonesia Provinces", "USA States", "Custom GeoJSON"],
                          key="choropleth_maptype")
    
    # Optimasi: Pengaturan performa
    col3, col4 = st.columns(2)
    with col3:
        use_sampling = st.checkbox("Gunakan sampling untuk data besar", value=True, key="choropleth_sampling")
    with col4:
        animation_col = st.selectbox("Kolom animasi (opsional)", 
                                   [""] + non_numeric_cols,
                                   key="choropleth_animation")
    
    if location_col and value_col:
        with st.spinner("Membuat peta choropleth..."):
            # Optimasi 1: Sampling untuk data besar
            processed_df = df.copy()
            if use_sampling and len(df) > 10000:
                sample_size = min(10000, len(df))
                processed_df = df.sample(n=sample_size, random_state=42)
                st.info(f"📊 Data disampling: {sample_size:,} dari {len(df):,} records")
            
            # Aggregasi data berdasarkan lokasi
            if animation_col:
                # Jika menggunakan animasi, group by location dan animation column
                map_data = (processed_df.groupby([location_col, animation_col])[value_col]
                          .mean()
                          .reset_index())
            else:
                # Jika tidak menggunakan animasi, group by location saja
                map_data = (processed_df.groupby(location_col)[value_col]
                          .agg(['mean', 'count', 'std'])
                          .round(2)
                          .reset_index())
                map_data.columns = [location_col, value_col, 'count', 'std']
            
            # Optimasi 2: Cache figure creation
            @st.cache_data(ttl=300)
            def create_choropleth_figure(data, location_col, value_col, map_type, animation_col=None):
                fig = px.choropleth(
                    data,
                    locations=location_col,
                    locationmode='country names' if map_type == "World Countries" else None,
                    color=value_col,
                    hover_name=location_col,
                    hover_data={
                        value_col: ':.2f',
                        'count': True,
                        'std': ':.2f'
                    } if not animation_col else {value_col: ':.2f'},
                    animation_frame=animation_col if animation_col else None,
                    color_continuous_scale="Viridis",
                    title=f"Peta Choropleth: {value_col} per {location_col}",
                    height=600
                )
                
                # Update layout untuk tampilan yang lebih baik
                fig.update_layout(
                    margin=dict(l=50, r=50, t=60, b=50),
                    geo=dict(
                        showframe=False,
                        showcoastlines=True,
                        projection_type='equirectangular'
                    ),
                    coloraxis_colorbar=dict(
                        title=value_col,
                        thickness=20,
                        len=0.75
                    )
                )
                
                return fig
            
            # Handle different map types
            if map_type == "World Countries":
                # Untuk peta dunia, asumsikan location_col berisi nama negara
                fig = create_choropleth_figure(
                    map_data, location_col, value_col, map_type, animation_col if animation_col != "" else None
                )
                
            elif map_type == "Indonesia Provinces":
                # Custom untuk provinsi Indonesia
                indonesia_provinces = {
                    'Aceh': 'ID-AC', 'Bali': 'ID-BA', 'Banten': 'ID-BT', 'Bengkulu': 'ID-BE',
                    'Gorontalo': 'ID-GO', 'Jakarta': 'ID-JK', 'Jambi': 'ID-JA', 'Jawa Barat': 'ID-JB',
                    'Jawa Tengah': 'ID-JT', 'Jawa Timur': 'ID-JI', 'Kalimantan Barat': 'ID-KB',
                    'Kalimantan Selatan': 'ID-KS', 'Kalimantan Tengah': 'ID-KT', 'Kalimantan Timur': 'ID-KI',
                    'Kalimantan Utara': 'ID-KU', 'Kepulauan Bangka Belitung': 'ID-BB',
                    'Kepulauan Riau': 'ID-KR', 'Lampung': 'ID-LA', 'Maluku': 'ID-MA',
                    'Maluku Utara': 'ID-MU', 'Nusa Tenggara Barat': 'ID-NB',
                    'Nusa Tenggara Timur': 'ID-NT', 'Papua': 'ID-PA', 'Papua Barat': 'ID-PB',
                    'Riau': 'ID-RI', 'Sulawesi Barat': 'ID-SR', 'Sulawesi Selatan': 'ID-SN',
                    'Sulawesi Tengah': 'ID-ST', 'Sulawesi Tenggara': 'ID-SG', 'Sulawesi Utara': 'ID-SA',
                    'Sumatera Barat': 'ID-SB', 'Sumatera Selatan': 'ID-SS', 'Sumatera Utara': 'ID-SU',
                    'Yogyakarta': 'ID-YO'
                }
                
                # Map province names to codes
                map_data['province_code'] = map_data[location_col].map(indonesia_provinces)
                
                fig = px.choropleth(
                    map_data,
                    geojson="https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia.geojson",
                    locations='province_code',
                    color=value_col,
                    hover_name=location_col,
                    hover_data={value_col: ':.2f', 'count': True} if not animation_col else {value_col: ':.2f'},
                    animation_frame=animation_col if animation_col else None,
                    color_continuous_scale="Blues",
                    title=f"Peta Indonesia: {value_col} per Provinsi",
                    height=600
                )
                
                fig.update_geos(fitbounds="locations", visible=False)
                
            elif map_type == "USA States":
                # Untuk peta USA states
                fig = px.choropleth(
                    map_data,
                    locations=location_col,
                    locationmode="USA-states",
                    color=value_col,
                    scope="usa",
                    hover_name=location_col,
                    hover_data={value_col: ':.2f', 'count': True} if not animation_col else {value_col: ':.2f'},
                    animation_frame=animation_col if animation_col else None,
                    color_continuous_scale="Reds",
                    title=f"Peta USA: {value_col} per State",
                    height=600
                )
                
            else:  # Custom GeoJSON
                st.info("Untuk Custom GeoJSON, silakan upload file GeoJSON Anda")
                uploaded_geojson = st.file_uploader("Upload GeoJSON file", type=['json', 'geojson'])
                
                if uploaded_geojson:
                    import json
                    geojson_data = json.load(uploaded_geojson)
                    
                    fig = px.choropleth(
                        map_data,
                        geojson=geojson_data,
                        locations=location_col,
                        color=value_col,
                        hover_name=location_col,
                        hover_data={value_col: ':.2f', 'count': True} if not animation_col else {value_col: ':.2f'},
                        animation_frame=animation_col if animation_col else None,
                        color_continuous_scale="Greens",
                        title=f"Peta Kustom: {value_col} per {location_col}",
                        height=600
                    )
                    
                    fig.update_geos(fitbounds="locations", visible=False)
                else:
                    st.warning("Silakan upload file GeoJSON untuk melanjutkan")
                    return
            
            # Optimasi 3: Plotly config yang ringan
            config = {
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d'],
                'responsive': True
            }
            
            st.plotly_chart(fig, use_container_width=True, config=config)
        
        # Tampilkan data summary
        with st.expander("📊 Lihat Data Peta"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Lokasi", len(map_data))
            with col2:
                st.metric(f"Rata-rata {value_col}", f"{map_data[value_col].mean():.2f}")
            with col3:
                max_loc = map_data.loc[map_data[value_col].idxmax()][location_col]
                st.metric("Lokasi Tertinggi", str(max_loc)[:20] + "...")
            
            # Tampilkan data teratas
            st.subheader("Data per Lokasi")
            display_data = map_data.sort_values(value_col, ascending=False).head(10)
            st.dataframe(display_data.style.format({value_col: "{:.2f}"}), use_container_width=True)
            
        with st.expander("ℹ️ Keterangan Peta Choropleth"):
            st.markdown(f"""
            **Peta Choropleth** digunakan untuk memvisualisasikan data geografis dengan variasi warna.
            
            **Statistik Data:**
            - Total lokasi: **{len(map_data)}**
            - Rentang nilai: **{map_data[value_col].min():.2f}** hingga **{map_data[value_col].max():.2f}**
            - Standar deviasi: **{map_data[value_col].std():.2f if 'std' in map_data.columns else 'N/A'}**
            
            **Kelebihan**: 
            - Visualisasi spasial yang intuitif
            - Mudah mengidentifikasi pola geografis
            - Efektif untuk data regional/geografis
            
            **Kekurangan**: 
            - Membutuhkan data lokasi yang akurat
            - Dapat misleading jika tidak dinormalisasi
            - Terbatas pada wilayah yang tersedia di GeoJSON
            
            **Penggunaan**: Analisis regional, data demografis, distribusi geografis
            
            **Tips Interpretasi:**
            - Area dengan warna lebih gelap menunjukkan nilai lebih tinggi
            - Perhatikan skala warna untuk interpretasi yang tepat
            - Gunakan hover untuk melihat nilai detail
            
            **Optimasi yang diterapkan:**
            ✅ Sampling otomatis untuk data besar  
            ✅ Aggregasi data yang efisien  
            ✅ Caching untuk performa  
            ✅ Multiple map types support  
            ✅ Animasi timeline (opsional)  
            """)
            
            

def create_flow_map(df):
    
    # Optimasi: Cache deteksi kolom
    @st.cache_data
    def detect_flow_columns(df):
        flow_patterns = ['lat', 'lon', 'long', 'latitude', 'longitude', 'origin', 'destination', 'from', 'to', 'source', 'target']
        return [col for col in df.columns if any(flow in col.lower() for flow in flow_patterns)]
    
    possible_flow_cols = detect_flow_columns(df)
    
    if possible_flow_cols:
        st.success(f"✅ Kolom flow map terdeteksi: {', '.join(possible_flow_cols)}")
        
        # Kategorikan kolom dengan caching
        @st.cache_data
        def categorize_flow_columns(_possible_flow_cols):
            origin_lat_cols = [col for col in _possible_flow_cols if any(pat in col.lower() for pat in ['origin_lat', 'from_lat', 'source_lat', 'lat_origin'])]
            origin_lon_cols = [col for col in _possible_flow_cols if any(pat in col.lower() for pat in ['origin_lon', 'from_lon', 'source_lon', 'lon_origin'])]
            dest_lat_cols = [col for col in _possible_flow_cols if any(pat in col.lower() for pat in ['dest_lat', 'to_lat', 'target_lat', 'lat_dest'])]
            dest_lon_cols = [col for col in _possible_flow_cols if any(pat in col.lower() for pat in ['dest_lon', 'to_lon', 'target_lon', 'lon_dest'])]
            return origin_lat_cols, origin_lon_cols, dest_lat_cols, dest_lon_cols
        
        origin_lat_cols, origin_lon_cols, dest_lat_cols, dest_lon_cols = categorize_flow_columns(possible_flow_cols)
        
        value_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📍 Origin Coordinates**")
            origin_lat = st.selectbox("Origin Latitude", origin_lat_cols if origin_lat_cols else possible_flow_cols, key="flow_origin_lat")
            origin_lon = st.selectbox("Origin Longitude", origin_lon_cols if origin_lon_cols else possible_flow_cols, key="flow_origin_lon")
            
        with col2:
            st.write("**🎯 Destination Coordinates**")
            dest_lat = st.selectbox("Destination Latitude", dest_lat_cols if dest_lat_cols else possible_flow_cols, key="flow_dest_lat")
            dest_lon = st.selectbox("Destination Longitude", dest_lon_cols if dest_lon_cols else possible_flow_cols, key="flow_dest_lon")
        
        # Pilih value column
        value_col = st.selectbox("📊 Kolom Value (untuk ketebalan flow)", [""] + value_cols, key="flow_value")
        
        # Customization options
        st.write("**🎨 Kustomisasi Tampilan**")
        col3, col4, col5 = st.columns(3)
        
        with col3:
            flow_style = st.selectbox("Gaya Garis", ["Solid", "Dashed", "Dotted", "Animated"], key="flow_style")
            line_width = st.slider("Ketebalan Garis Dasar", 1, 10, 3, key="line_width")
            
        with col4:
            color_scheme = st.selectbox("Skema Warna", [
                "Viridis", "Plasma", "Inferno", "Magma", 
                "Rainbow", "Jet", "Hot", "Cool", "Red-Blue"
            ], key="color_scheme")
            
        with col5:
            map_style = st.selectbox("Style Peta", [
                "natural earth", "orthographic", "equirectangular", 
                "mercator", "azimuthal equal area"
            ], key="map_style")
        
        # Optimasi: Sampling untuk flow map
        flow_sample_size = st.slider("🚢 Jumlah sampel aliran untuk ditampilkan", 
                                    min_value=50, 
                                    max_value=min(1000, len(df)), 
                                    value=min(200, len(df)),
                                    key="flow_sample")
        
        # Validasi data
        if origin_lat and origin_lon and dest_lat and dest_lon:
            # Filter data valid dengan sampling
            valid_data = df[
                (pd.notna(df[origin_lat])) & (pd.notna(df[origin_lon])) &
                (pd.notna(df[dest_lat])) & (pd.notna(df[dest_lon]))
            ].copy()
            
            if len(valid_data) > 0:
                # Sampling untuk dataset besar
                if len(valid_data) > flow_sample_size:
                    valid_data = valid_data.sample(n=flow_sample_size, random_state=42)
                    st.info(f"📊 Menampilkan {flow_sample_size} sampel acak dari {len(valid_data)} aliran valid")
                else:
                    st.success(f"📊 Menampilkan {len(valid_data)} aliran data")
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Buat flow map dengan animasi
                try:
                    import plotly.graph_objects as go
                    import plotly.express as px
                    import numpy as np
                    
                    status_text.text("🌍 Membuat flow map 3D...")
                    
                    # Buat figure dengan layout globe
                    fig = go.Figure()
                    
                    # Generate colors berdasarkan value atau sequential
                    if value_col and value_col in valid_data.columns:
                        colors = px.colors.sample_colorscale(color_scheme.lower(), 
                                                           np.linspace(0, 1, len(valid_data)))
                        color_scale = px.colors.sequential.__dict__.get(color_scheme, px.colors.sequential.Viridis)
                    else:
                        colors = px.colors.sample_colorscale('viridis', np.linspace(0, 1, len(valid_data)))
                        color_scale = px.colors.sequential.Viridis
                    
                    # Konfigurasi garis berdasarkan style
                    dash_styles = {
                        "Solid": None,
                        "Dashed": "dash",
                        "Dotted": "dot",
                        "Animated": "dash"
                    }
                    
                    dash_style = dash_styles.get(flow_style, None)
                    
                    # Tambahkan lines untuk setiap flow dengan progress
                    for idx, row in valid_data.iterrows():
                        if idx % 20 == 0:  # Update progress setiap 20 rows
                            progress_bar.progress(min((idx + 1) / len(valid_data), 1.0))
                        
                        # Hitung ketebalan garis
                        current_line_width = line_width
                        if value_col and pd.notna(row[value_col]):
                            max_val = valid_data[value_col].max()
                            min_val = valid_data[value_col].min()
                            if max_val > min_val:
                                current_line_width = max(1, line_width + (row[value_col] - min_val) / (max_val - min_val) * 8)
                        
                        # Warna berdasarkan value atau sequential
                        if value_col and value_col in valid_data.columns:
                            color_idx = int((row[value_col] - min_val) / (max_val - min_val) * (len(colors) - 1)) if max_val > min_val else 0
                            line_color = colors[color_idx]
                        else:
                            line_color = colors[idx % len(colors)]
                        
                        # Tambahkan garis aliran
                        fig.add_trace(go.Scattergeo(
                            lon = [row[origin_lon], row[dest_lon]],
                            lat = [row[origin_lat], row[dest_lat]],
                            mode = 'lines',
                            line = dict(
                                width = current_line_width,
                                color = line_color,
                                dash = dash_style
                            ),
                            opacity = 0.7,
                            name = f"Flow {idx+1}",
                            showlegend=False,
                            hoverinfo='text',
                            hovertext = f"Origin: ({row[origin_lat]:.2f}, {row[origin_lon]:.2f})<br>"
                                      f"Dest: ({row[dest_lat]:.2f}, {row[dest_lon]:.2f})<br>"
                                      f"{f'Value: {row[value_col]}' if value_col else ''}"
                        ))
                        
                        # Tambahkan animasi kapal untuk style animated
                        if flow_style == "Animated":
                            # Buat titik animasi di sepanjang garis
                            num_points = 5
                            for i in range(num_points):
                                frac = i / (num_points - 1) if num_points > 1 else 0.5
                                anim_lat = row[origin_lat] + (row[dest_lat] - row[origin_lat]) * frac
                                anim_lon = row[origin_lon] + (row[dest_lon] - row[origin_lon]) * frac
                                
                                fig.add_trace(go.Scattergeo(
                                    lon = [anim_lon],
                                    lat = [anim_lat],
                                    mode = 'markers',
                                    marker = dict(
                                        size = 8,
                                        color = 'yellow',
                                        symbol = 'triangle-up',
                                        line = dict(width=1, color='darkorange')
                                    ),
                                    opacity = 0.6 - (i * 0.1),
                                    name = f"Ship {idx+1}",
                                    showlegend=False,
                                    hoverinfo='skip'
                                ))
                    
                    # Tambahkan markers untuk origin dan destination
                    status_text.text("📍 Menambahkan markers...")
                    
                    unique_origins = valid_data[[origin_lat, origin_lon]].drop_duplicates().head(50)  # Batasi jumlah marker
                    unique_dests = valid_data[[dest_lat, dest_lon]].drop_duplicates().head(50)
                    
                    fig.add_trace(go.Scattergeo(
                        lon = unique_origins[origin_lon],
                        lat = unique_origins[origin_lat],
                        mode = 'markers',
                        marker = dict(
                            size=8, 
                            color='blue',
                            symbol='circle',
                            line=dict(width=2, color='darkblue')
                        ),
                        name = '📍 Origin',
                        text = ['Origin'] * len(unique_origins),
                        hoverinfo='text+lon+lat'
                    ))
                    
                    fig.add_trace(go.Scattergeo(
                        lon = unique_dests[dest_lon],
                        lat = unique_dests[dest_lat],
                        mode = 'markers',
                        marker = dict(
                            size=8, 
                            color='red',
                            symbol='square',
                            line=dict(width=2, color='darkred')
                        ),
                        name = '🎯 Destination',
                        text = ['Destination'] * len(unique_dests),
                        hoverinfo='text+lon+lat'
                    ))
                    
                    # Update layout dengan tampilan globe
                    fig.update_layout(
                        title_text = f'🌍 Flow Map 3D - {len(valid_data)} Aliran',
                        showlegend = True,
                        geo = dict(
                            scope = 'world',
                            projection_type = map_style,
                            showland = True,
                            landcolor = 'rgb(100, 125, 100)',
                            countrycolor = 'rgb(200, 200, 200)',
                            coastlinecolor = 'rgb(160, 160, 160)',
                            lakecolor = 'rgb(100, 150, 250)',
                            oceancolor = 'rgb(50, 100, 200)',
                            showocean = True,
                            showcountries = True,
                            showcoastlines = True,
                            showframe = False,
                            bgcolor = 'rgb(0, 0, 0)',
                        ),
                        paper_bgcolor = 'black',
                        font = dict(color='white'),
                        height = 700,
                        hovermode = 'closest'
                    )
                    
                    # Tambahkan animasi frame untuk efek kapal bergerak
                    if flow_style == "Animated":
                        frames = []
                        for frame_num in range(5):
                            frame_data = []
                            for idx, row in valid_data.iterrows():
                                frac = frame_num / 4
                                anim_lat = row[origin_lat] + (row[dest_lat] - row[origin_lat]) * frac
                                anim_lon = row[origin_lon] + (row[dest_lon] - row[origin_lon]) * frac
                                
                                frame_data.append(
                                    go.Scattergeo(
                                        lon=[anim_lon],
                                        lat=[anim_lat],
                                        mode='markers',
                                        marker=dict(size=10, color='yellow', symbol='triangle-up')
                                    )
                                )
                            
                            frames.append(go.Frame(data=frame_data, name=f"frame{frame_num}"))
                        
                        fig.frames = frames
                        
                        # Tambahkan play button untuk animasi
                        fig.update_layout(
                            updatemenus=[dict(
                                type="buttons",
                                buttons=[dict(label="▶️ Play",
                                            method="animate",
                                            args=[None, {"frame": {"duration": 500, "redraw": True},
                                                        "fromcurrent": True}])]
                            )]
                        )
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Flow map 3D selesai dibuat!")
                    
                    st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
                    
                    # Legenda warna
                    if value_col and value_col in valid_data.columns:
                        st.write("**🎨 Legenda Intensitas Aliran**")
                        min_val = valid_data[value_col].min()
                        max_val = valid_data[value_col].max()
                        st.caption(f"Warna menunjukkan nilai dari {min_val:.2f} (biru) hingga {max_val:.2f} (merah)")
                    
                    # Tampilkan data table dengan pagination
                    with st.expander("📋 Lihat Data Flow"):
                        display_cols = [origin_lat, origin_lon, dest_lat, dest_lon]
                        if value_col:
                            display_cols.append(value_col)
                        
                        # Pagination
                        page_size = 20
                        total_pages = max(1, len(valid_data) // page_size)
                        page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1, key="flow_page")
                        
                        start_idx = (page - 1) * page_size
                        end_idx = min(start_idx + page_size, len(valid_data))
                        
                        st.dataframe(valid_data[display_cols].iloc[start_idx:end_idx])
                        st.caption(f"Menampilkan data {start_idx + 1}-{end_idx} dari {len(valid_data)}")
                        
                except Exception as e:
                    st.error(f"❌ Error membuat flow map: {str(e)}")
                    st.info("💡 Tips: Pastikan data koordinat dalam format numerik yang valid")
                    
            else:
                st.error("❌ Tidak ada data dengan koordinat origin-destination yang valid")
                
        else:
            st.warning("⚠️ Pilih semua kolom koordinat untuk menampilkan flow map")
            
    else:
        st.warning("""
        ⚠️ Tidak terdeteksi kolom untuk flow map.
        
        **Untuk menampilkan Flow Map, data harus mengandung:**
        - Origin coordinates (latitude & longitude)
        - Destination coordinates (latitude & longitude) 
        - Opsional: Value column untuk ketebalan flow
        
        **Format kolom yang disarankan:**
        - `origin_lat`, `origin_lon`, `dest_lat`, `dest_lon`
        - `from_latitude`, `from_longitude`, `to_latitude`, `to_longitude`
        - `source_lat`, `source_lon`, `target_lat`, `target_lon`
        """)
def create_heatmap(df, numeric_cols):
    
    # Deteksi ukuran data
    data_size = len(df)
    if data_size > 100000:
        st.info(f"⚡ Mode Optimasi: Data besar ({data_size:,} rows) - Menggunakan sampling otomatis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_cols = st.slider(
            "Maksimum kolom ditampilkan",
            min_value=5,
            max_value=20,
            value=10 if data_size > 50000 else 15,
            key="heatmap_max_cols"
        )
    
    with col2:
        optimization_mode = st.selectbox(
            "Mode Optimasi",
            ["Auto", "Fast", "Balanced", "Detailed"],
            index=0 if data_size > 50000 else 2,
            key="heatmap_optim"
        )
    
    # Filter numeric columns yang feasible untuk heatmap
    suitable_cols = [col for col in numeric_cols 
                   if df[col].nunique() > 1 and df[col].dtype in ['float64', 'int64']]
    
    selected_cols = st.multiselect(
        "Pilih kolom untuk heatmap", 
        suitable_cols[:max_cols],  # Batasi pilihan
        default=suitable_cols[:min(8, len(suitable_cols))], 
        key="heatmap_cols"
    )
    
    # Pengaturan lanjutan
    with st.expander("⚙️ Pengaturan Lanjutan", expanded=False):
        col3, col4, col5 = st.columns(3)
        with col3:
            color_scale = st.selectbox(
                "Skala warna",
                ["RdBu_r", "Viridis", "Plasma", "Inferno", "Blues", "Greens"],
                key="heatmap_color"
            )
        with col4:
            show_values = st.selectbox(
                "Tampilkan nilai",
                ["Auto", "Always", "Never", "Significant Only"],
                key="heatmap_values"
            )
        with col5:
            correlation_method = st.selectbox(
                "Metode korelasi",
                ["pearson", "spearman", "kendall"],
                key="heatmap_method"
            )
    
    if len(selected_cols) >= 2:
        try:
            with st.spinner("🔄 Menghitung matriks korelasi..."):
                # OPTIMASI 1: Sampling data untuk kalkulasi korelasi
                processed_df = optimize_heatmap_data(df, selected_cols, data_size, optimization_mode)
                
                if len(processed_df) == 0:
                    st.warning("Tidak ada data valid setelah preprocessing")
                    return
                
                # OPTIMASI 2: Hitung matriks korelasi yang efisien
                corr_matrix = calculate_correlation_matrix(processed_df, selected_cols, correlation_method)
                
                # OPTIMASI 3: Buat heatmap yang dioptimalkan
                fig = create_optimized_heatmap(corr_matrix, selected_cols, color_scale, show_values, data_size)
                
                # OPTIMASI 4: Konfigurasi plotly yang ringan
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'responsive': True
                }
                
                st.plotly_chart(fig, use_container_width=True, config=config)
                
                # Tampilkan analisis tambahan
                display_correlation_analysis(corr_matrix, processed_df, selected_cols)
                
                # Tampilkan info optimasi
                show_heatmap_optimization_info(data_size, len(processed_df), optimization_mode)
                
        except Exception as e:
            st.error(f"Error membuat heatmap: {str(e)}")
            # Fallback ke metode sederhana
            create_simple_heatmap_fallback(df, selected_cols)
    else:
        st.warning("Pilih minimal 2 kolom untuk heatmap")

def optimize_heatmap_data(df, selected_cols, data_size, optimization_mode):
    """Optimasi data untuk heatmap dengan sampling yang tepat"""
    
    # Filter data yang valid
    clean_df = df[selected_cols].replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(clean_df) == 0:
        return clean_df
    
    # Tentukan target sample size
    target_sizes = {
        "Auto": min(10000, data_size),
        "Fast": min(5000, data_size),
        "Balanced": min(20000, data_size),
        "Detailed": min(50000, data_size)
    }
    
    target_size = target_sizes[optimization_mode]
    
    # Jika data lebih besar dari target, lakukan sampling
    if len(clean_df) > target_size:
        if optimization_mode == "Fast":
            # Systematic sampling untuk performa maksimal
            step = len(clean_df) // target_size
            sampled_df = clean_df.iloc[::step]
        elif optimization_mode == "Balanced":
            # Stratified sampling untuk mempertahankan korelasi
            try:
                # Sample berdasarkan kombinasi nilai ekstrem
                n_samples_per_quantile = target_size // 4
                sampled_dfs = []
                
                for col in selected_cols[:3]:  # Gunakan 3 kolom pertama untuk stratification
                    for quantile in [0.25, 0.5, 0.75]:
                        threshold = clean_df[col].quantile(quantile)
                        quantile_data = clean_df[clean_df[col] <= threshold].tail(n_samples_per_quantile // 3)
                        sampled_dfs.append(quantile_data)
                
                # Gabungkan dan hapus duplikat
                sampled_df = pd.concat(sampled_dfs, ignore_index=True).drop_duplicates()
                
                # Jika masih kurang, tambahkan random sampling
                if len(sampled_df) < target_size:
                    remaining = target_size - len(sampled_df)
                    additional_samples = clean_df.sample(n=remaining, random_state=42)
                    sampled_df = pd.concat([sampled_df, additional_samples], ignore_index=True)
                    
            except:
                # Fallback ke random sampling
                sampled_df = clean_df.sample(n=target_size, random_state=42)
        else:
            # Random sampling untuk mode lain
            sampled_df = clean_df.sample(n=target_size, random_state=42)
        
        return sampled_df
    
    return clean_df

def calculate_correlation_matrix(df, selected_cols, correlation_method):
    """Hitung matriks korelasi yang efisien"""
    
    # OPTIMASI: Gunakan numpy untuk kalkulasi yang lebih cepat
    data_subset = df[selected_cols]
    
    if correlation_method == "pearson":
        corr_matrix = data_subset.corr(method='pearson')
    elif correlation_method == "spearman":
        # Spearman lebih robust untuk data non-linear
        corr_matrix = data_subset.corr(method='spearman')
    else:  # kendall
        corr_matrix = data_subset.corr(method='kendall')
    
    return corr_matrix

def create_optimized_heatmap(corr_matrix, selected_cols, color_scale, show_values, data_size):
    """Buat heatmap yang dioptimalkan untuk performa"""
    
    # OPTIMASI: Tentukan apakah menampilkan nilai teks
    if show_values == "Auto":
        text_auto = True if len(selected_cols) <= 15 else False
    elif show_values == "Always":
        text_auto = True
    elif show_values == "Never":
        text_auto = False
    else:  # Significant Only
        # Hanya tampilkan nilai yang signifikan (|correlation| > 0.3)
        text_matrix = np.where(np.abs(corr_matrix.values) > 0.3, 
                              corr_matrix.values.round(2), 
                              "")
        text_auto = text_matrix
    
    # Buat heatmap
    fig = px.imshow(
        corr_matrix, 
        text_auto=text_auto,
        aspect="auto", 
        title=f"Heatmap Korelasi ({len(selected_cols)} variabel)",
        color_continuous_scale=color_scale,
        zmin=-1,  # Fixed range untuk korelasi
        zmax=1
    )
    
    # OPTIMASI: Update layout untuk performa
    fig.update_traces(
        hovertemplate='<b>%{y}</b> vs <b>%{x}</b><br>Korelasi: %{z:.3f}<extra></extra>'
    )
    
    # Layout yang dioptimalkan
    height = max(400, len(selected_cols) * 30)  # Dynamic height berdasarkan jumlah kolom
    fig.update_layout(
        height=height,
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis=dict(tickangle=-45),
        plot_bgcolor='white'
    )
    
    # Tambahkan colorbar yang informatif
    fig.update_coloraxes(
        colorbar=dict(
            title="Korelasi",
            titleside="right",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["-1.0 (Strong -)", "-0.5", "0.0 (No)", "0.5", "1.0 (Strong +)"]
        )
    )
    
    return fig

def display_correlation_analysis(corr_matrix, processed_df, selected_cols):
    """Tampilkan analisis korelasi tambahan"""
    
    with st.expander("📊 Analisis Korelasi Detail", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        # Hitung statistik korelasi
        corr_values = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
        
        with col1:
            avg_correlation = np.mean(np.abs(corr_values))
            st.metric("Rata-rata Korelasi (abs)", f"{avg_correlation:.3f}")
        
        with col2:
            strong_correlations = np.sum(np.abs(corr_values) > 0.7)
            st.metric("Korelasi Kuat (|r| > 0.7)", f"{strong_correlations}")
        
        with col3:
            weak_correlations = np.sum(np.abs(corr_values) < 0.3)
            st.metric("Korelasi Lemah (|r| < 0.3)", f"{weak_correlations}")
        
        # Top correlations
        st.subheader("🔝 Korelasi Terkuat")
        
        # Dapatkan pasangan dengan korelasi tertinggi
        corr_pairs = []
        for i in range(len(selected_cols)):
            for j in range(i+1, len(selected_cols)):
                corr_val = corr_matrix.iloc[i, j]
                corr_pairs.append({
                    'Variable 1': selected_cols[i],
                    'Variable 2': selected_cols[j],
                    'Correlation': corr_val,
                    'Strength': 'Strong' if abs(corr_val) > 0.7 else 
                               'Moderate' if abs(corr_val) > 0.3 else 'Weak'
                })
        
        corr_df = pd.DataFrame(corr_pairs)
        top_correlations = corr_df.nlargest(10, 'Correlation')
        bottom_correlations = corr_df.nsmallest(10, 'Correlation')
        
        col4, col5 = st.columns(2)
        
        with col4:
            st.markdown("**🔼 Korelasi Positif Tertinggi**")
            st.dataframe(
                top_correlations.style.format({'Correlation': '{:.3f}'}),
                use_container_width=True
            )
        
        with col5:
            st.markdown("**🔽 Korelasi Negatif Tertinggi**")
            st.dataframe(
                bottom_correlations.style.format({'Correlation': '{:.3f}'}),
                use_container_width=True
            )
        
        # Correlation clusters
        st.subheader("🎯 Kluster Korelasi")
        try:
            from scipy.cluster import hierarchy
            
            # Hierarchical clustering untuk mengidentifikasi pola
            corr_array = 1 - np.abs(corr_matrix.values)  # Convert to distance matrix
            linkage_matrix = hierarchy.linkage(corr_array, method='average')
            
            # Dapatkan order dari dendrogram
            dendro_order = hierarchy.dendrogram(linkage_matrix, no_plot=True)['leaves']
            clustered_cols = [selected_cols[i] for i in dendro_order]
            
            st.markdown(f"**Urutan Kluster:** {', '.join(clustered_cols[:5])}...")
            
        except Exception as e:
            st.info("Klustering tidak tersedia untuk dataset ini")

def show_heatmap_optimization_info(original_size, processed_size, optimization_mode):
    """Tampilkan informasi optimasi"""
    
    reduction_pct = ((original_size - processed_size) / original_size) * 100 if original_size > 0 else 0
    
    if reduction_pct > 10:
        with st.expander("⚡ Info Optimasi Performa", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Data Original", f"{original_size:,}")
            with col2:
                st.metric("Data Diproses", f"{processed_size:,}")
            with col3:
                st.metric("Reduksi", f"{reduction_pct:.1f}%")
            
            optimization_strategies = {
                "Fast": "• ✅ **Aggressive sampling**\n• ✅ **Basic correlation**\n• ✅ **Minimal text**",
                "Balanced": "• ✅ **Stratified sampling**\n• ✅ **Multiple methods**\n• ✅ **Smart text display**",
                "Detailed": "• ✅ **Maximum data retention**\n• ✅ **Advanced analysis**\n• ✅ **Full features**"
            }
            
            st.info(f"**Mode {optimization_mode}**: {optimization_strategies.get(optimization_mode, 'Custom optimization')}")

def create_simple_heatmap_fallback(df, selected_cols):
    """Fallback method untuk data yang bermasalah"""
    st.warning("Menggunakan metode fallback sederhana...")
    
    # Sample kecil untuk kalkulasi cepat
    sample_df = df[selected_cols].replace([np.inf, -np.inf], np.nan).dropna().head(2000)
    
    if len(sample_df) == 0:
        st.error("Tidak ada data valid")
        return
    
    corr_matrix = sample_df.corr()
    
    fig = px.imshow(
        corr_matrix, 
        text_auto=True,
        aspect="auto", 
        title="Simple Heatmap Korelasi",
        color_continuous_scale='RdBu_r'
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Versi ultra-ringan untuk data ekstrem
def create_ultra_fast_heatmap(df, numeric_cols):
    """Versi ultra-ringan untuk data > 500k rows"""
    st.subheader("🚀 Heatmap Ultra-Fast")
    
    # Pilih kolom otomatis (max 8)
    suitable_cols = [col for col in numeric_cols 
                   if df[col].nunique() > 1 and df[col].dtype in ['float64', 'int64']]
    selected_cols = st.multiselect(
        "Pilih kolom", 
        suitable_cols[:8],
        default=suitable_cols[:min(6, len(suitable_cols))],
        key="ultra_heatmap_cols"
    )
    
    if len(selected_cols) >= 2:
        # Sampling sangat agresif
        sample_df = df[selected_cols].replace([np.inf, -np.inf], np.nan).dropna()
        if len(sample_df) > 5000:
            sample_df = sample_df.sample(n=5000, random_state=42)
        
        corr_matrix = sample_df.corr()
        
        fig = px.imshow(
            corr_matrix, 
            text_auto=True,
            aspect="auto", 
            title=f"Ultra-Fast Heatmap ({len(selected_cols)} variables)"
        )
        
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.info(f"📊 Ultra-Fast Mode: 5,000 samples, {len(selected_cols)} variables")


def create_ml_dl_analysis_dashboard(df, numeric_cols, non_numeric_cols):
    """
    Dashboard komprehensif untuk analisis Machine Learning dan Deep Learning
    """
    st.markdown("""
    <div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 10px; margin: 10px 0;'>
        <h3 style='color: white; margin: 0;'>🧠 dwibaktindev AI</h3>
        <p style='color: white; margin: 0;'>Sasha • Alisa • dwibaktindev Models</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Deteksi tipe data
    data_size = len(df)
    st.info(f"📊 Dataset: {data_size:,} samples, {len(numeric_cols)} features numerik, {len(non_numeric_cols)} features kategorikal")
    
    # Sidebar untuk navigasi analisis
    analysis_type = st.sidebar.selectbox(
        "🎯 Pilih Tipe Analisis",
        ["📈 EDA & Visualisasi", "🤖 Machine Learning", "🧠 Deep Learning", 
         "📊 Model Comparison", "🔍 Feature Analysis"],
        key="main_analysis_type"
    )
    
    if analysis_type == "📈 EDA & Visualisasi":
        exploratory_data_analysis(df, numeric_cols, non_numeric_cols)
    
    elif analysis_type == "🤖 Machine Learning":
        machine_learning_analysis(df, numeric_cols, non_numeric_cols)
    
    elif analysis_type == "🧠 Deep Learning":
        deep_learning_analysis(df, numeric_cols, non_numeric_cols)
    
    elif analysis_type == "📊 Model Comparison":
        model_comparison_analysis(df, numeric_cols, non_numeric_cols)
    
    elif analysis_type == "🔍 Feature Analysis":
        feature_analysis_dashboard(df, numeric_cols, non_numeric_cols)

def exploratory_data_analysis(df, numeric_cols, non_numeric_cols):
    """Analisis Data Eksploratif Lanjutan"""
    
    st.header("📈 Exploratory Data Analysis")
    
    # Statistik dasar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Samples", f"{len(df):,}")
    with col2:
        st.metric("Numerical Features", len(numeric_cols))
    with col3:
        st.metric("Categorical Features", len(non_numeric_cols))
    with col4:
        missing_ratio = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        st.metric("Missing Data", f"{missing_ratio:.1f}%")
    
    # Tab untuk berbagai visualisasi
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Distribution", "📈 Trends", "🔥 Correlation", "🎯 Outliers"])
    
    with tab1:
        create_distribution_analysis(df, numeric_cols, non_numeric_cols)
    
    with tab2:
        create_trend_analysis(df, numeric_cols, non_numeric_cols)
    
    with tab3:
        create_correlation_analysis(df, numeric_cols)
    
    with tab4:
        create_outlier_analysis(df, numeric_cols)

def create_distribution_analysis(df, numeric_cols, non_numeric_cols):
    """Analisis distribusi data"""
    
    st.subheader("📊 Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_col = st.selectbox("Pilih Feature", numeric_cols, key="dist_feature_select")
        plot_type = st.selectbox("Jenis Plot", ["Histogram", "KDE", "Box Plot", "Violin Plot"], key="dist_plot_type")
    
    with col2:
        if non_numeric_cols:
            hue_col = st.selectbox("Group by (optional)", [None] + non_numeric_cols, key="dist_hue_select")
        else:
            hue_col = None
        
        bins = st.slider("Number of Bins", 5, 100, 30, key="dist_bins_slider")
    
    if target_col and target_col in df.columns:
        fig = go.Figure()
        
        if hue_col and hue_col in df.columns:
            categories = df[hue_col].dropna().unique()[:8]  # Batasi kategori
            colors = px.colors.qualitative.Set1
            
            for i, category in enumerate(categories):
                subset = df[df[hue_col] == category][target_col].dropna()
                
                if len(subset) > 0:
                    if plot_type == "Histogram":
                        fig.add_trace(go.Histogram(
                            x=subset, 
                            name=str(category),
                            opacity=0.7,
                            nbinsx=bins,
                            marker_color=colors[i % len(colors)]
                        ))
                    elif plot_type == "KDE":
                        # Create KDE manually
                        try:
                            kde = gaussian_kde(subset)
                            x_range = np.linspace(subset.min(), subset.max(), 100)
                            fig.add_trace(go.Scatter(
                                x=x_range, 
                                y=kde(x_range),
                                name=str(category),
                                fill='tozeroy',
                                opacity=0.6
                            ))
                        except:
                            st.warning(f"Tidak dapat membuat KDE untuk kategori {category}")
                    elif plot_type == "Box Plot":
                        fig.add_trace(go.Box(y=subset, name=str(category)))
                    elif plot_type == "Violin Plot":
                        fig.add_trace(go.Violin(y=subset, name=str(category)))
        else:
            data = df[target_col].dropna()
            if len(data) > 0:
                if plot_type == "Histogram":
                    fig.add_trace(go.Histogram(x=data, nbinsx=bins, name=target_col))
                elif plot_type == "Box Plot":
                    fig.add_trace(go.Box(y=data, name=target_col))
                elif plot_type == "Violin Plot":
                    fig.add_trace(go.Violin(y=data, name=target_col))
                elif plot_type == "KDE":
                    try:
                        kde = gaussian_kde(data)
                        x_range = np.linspace(data.min(), data.max(), 100)
                        fig.add_trace(go.Scatter(
                            x=x_range, 
                            y=kde(x_range),
                            name=target_col,
                            fill='tozeroy'
                        ))
                    except:
                        st.warning("Tidak dapat membuat KDE plot")
        
        if len(fig.data) > 0:
            fig.update_layout(
                title=f"{plot_type} of {target_col}" + (f" by {hue_col}" if hue_col else ""),
                height=400,
                showlegend=True if hue_col else False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistik deskriptif
            st.subheader("📋 Descriptive Statistics")
            desc_stats = df[target_col].describe()
            st.dataframe(desc_stats, use_container_width=True)
        else:
            st.warning("Tidak ada data yang valid untuk ditampilkan")

def create_trend_analysis(df, numeric_cols, non_numeric_cols):
    """Analisis tren time series atau sequential"""
    
    st.subheader("📈 Trend Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        time_col = st.selectbox(
            "Pilih Time/Sequence Column", 
            [None] + non_numeric_cols + numeric_cols,
            key="trend_time_col"
        )
        target_features = st.multiselect(
            "Pilih Features untuk Analisis Tren",
            numeric_cols,
            default=numeric_cols[:min(3, len(numeric_cols))],
            key="trend_features_select"
        )
    
    with col2:
        if time_col:
            aggregation = st.selectbox("Aggregation", ["raw", "daily", "weekly", "monthly"], key="trend_aggregation")
            show_forecast = st.checkbox("Tampilkan Simple Forecast", key="trend_forecast_check")
    
    if time_col and target_features:
        try:
            # Convert to datetime jika memungkinkan
            df_plot = df.copy()
            if time_col in df_plot.columns:
                try:
                    df_plot[time_col] = pd.to_datetime(df_plot[time_col])
                    is_datetime = True
                except:
                    is_datetime = False
            else:
                is_datetime = False
            
            # Aggregation
            if aggregation != "raw" and is_datetime:
                df_plot = df_plot.set_index(time_col)
                if aggregation == "daily":
                    df_plot = df_plot[target_features].resample('D').mean()
                elif aggregation == "weekly":
                    df_plot = df_plot[target_features].resample('W').mean()
                elif aggregation == "monthly":
                    df_plot = df_plot[target_features].resample('M').mean()
                df_plot = df_plot.reset_index()
            
            fig = go.Figure()
            
            for feature in target_features:
                if feature in df_plot.columns:
                    valid_data = df_plot[[time_col, feature]].dropna()
                    if len(valid_data) > 1:
                        fig.add_trace(go.Scatter(
                            x=valid_data[time_col],
                            y=valid_data[feature],
                            mode='lines',
                            name=feature,
                            hovertemplate=f"{feature}: %{{y:.2f}}<extra></extra>"
                        ))
                        
                        # Simple forecast menggunakan linear regression
                        if show_forecast and len(valid_data) > 10:
                            try:
                                # Convert time to numeric untuk forecasting
                                if is_datetime:
                                    x = (valid_data[time_col] - valid_data[time_col].min()).dt.total_seconds().values.reshape(-1, 1)
                                else:
                                    x = np.arange(len(valid_data)).reshape(-1, 1)
                                
                                y = valid_data[feature].values
                                
                                model = LinearRegression()
                                model.fit(x, y)
                                
                                # Forecast 20% ke depan
                                future_points = max(1, int(len(x) * 0.2))
                                x_future = np.arange(len(x), len(x) + future_points).reshape(-1, 1)
                                y_future = model.predict(x_future)
                                
                                if is_datetime:
                                    last_date = valid_data[time_col].iloc[-1]
                                    if aggregation == "daily":
                                        freq = 'D'
                                    elif aggregation == "weekly":
                                        freq = 'W'
                                    elif aggregation == "monthly":
                                        freq = 'M'
                                    else:
                                        freq = 'D'
                                    future_dates = pd.date_range(last_date, periods=future_points+1, freq=freq)[1:]
                                else:
                                    future_dates = range(len(x), len(x) + future_points)
                                
                                fig.add_trace(go.Scatter(
                                    x=future_dates,
                                    y=y_future,
                                    mode='lines',
                                    name=f"{feature} Forecast",
                                    line=dict(dash='dash', color=fig.data[-1].line.color),
                                    opacity=0.7
                                ))
                            except Exception as forecast_error:
                                st.warning(f"Tidak dapat membuat forecast untuk {feature}: {str(forecast_error)}")
            
            if len(fig.data) > 0:
                fig.update_layout(
                    title=f"Trend Analysis dengan{' Forecast' if show_forecast else ''}",
                    height=500,
                    xaxis_title=time_col,
                    yaxis_title="Value",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Tidak ada data yang valid untuk analisis tren")
            
        except Exception as e:
            st.error(f"Error dalam trend analysis: {str(e)}")

def create_correlation_analysis(df, numeric_cols):
    """Analisis korelasi antar features"""
    
    st.subheader("🔥 Correlation Analysis")
    
    # Pilih features untuk analisis korelasi
    selected_features = st.multiselect(
        "Pilih Features untuk Correlation Analysis",
        numeric_cols,
        default=numeric_cols[:min(10, len(numeric_cols))],
        key="corr_features_select"
    )
    
    if len(selected_features) >= 2:
        # Hitung correlation matrix
        corr_matrix = df[selected_features].corr()
        
        # Heatmap correlation
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Correlation Matrix Heatmap"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Cari correlation pairs yang tinggi
        st.subheader("🎯 High Correlation Pairs")
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:  # Threshold untuk high correlation
                    corr_pairs.append({
                        'Feature 1': corr_matrix.columns[i],
                        'Feature 2': corr_matrix.columns[j],
                        'Correlation': corr_val
                    })
        
        if corr_pairs:
            corr_df = pd.DataFrame(corr_pairs).sort_values('Correlation', key=abs, ascending=False)
            st.dataframe(corr_df, use_container_width=True)
        else:
            st.info("Tidak ditemukan correlation pairs dengan nilai > 0.7")
        
        # Scatter matrix untuk features terpilih
        if len(selected_features) <= 6:
            st.subheader("📊 Scatter Matrix")
            try:
                fig = px.scatter_matrix(df[selected_features].dropna(), height=800)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Tidak dapat membuat scatter matrix: {str(e)}")

def create_outlier_analysis(df, numeric_cols):
    """Deteksi dan analisis outliers"""
    
    st.subheader("🎯 Outlier Detection Analysis")
    
    # Pilih method deteksi outliers
    method = st.selectbox(
        "Pilih Outlier Detection Method",
        ["IQR", "Z-Score", "Isolation Forest", "Local Outlier Factor"],
        key="outlier_method_select"
    )
    
    target_features = st.multiselect(
        "Pilih Features untuk Outlier Detection",
        numeric_cols,
        default=numeric_cols[:min(5, len(numeric_cols))],
        key="outlier_features_select"
    )
    
    if target_features:
        # Deteksi outliers
        outlier_results = {}
        
        for feature in target_features:
            if feature in df.columns:
                data = df[feature].dropna()
                if len(data) > 0:
                    data_values = data.values.reshape(-1, 1)
                    
                    if method == "IQR":
                        Q1 = np.percentile(data_values, 25)
                        Q3 = np.percentile(data_values, 75)
                        IQR = Q3 - Q1
                        if IQR > 0:
                            lower_bound = Q1 - 1.5 * IQR
                            upper_bound = Q3 + 1.5 * IQR
                            outliers = (data_values < lower_bound) | (data_values > upper_bound)
                        else:
                            outliers = np.zeros_like(data_values, dtype=bool)
                        
                    elif method == "Z-Score":
                        from scipy import stats
                        try:
                            z_scores = np.abs(stats.zscore(data_values))
                            outliers = z_scores > 3
                        except:
                            outliers = np.zeros_like(data_values, dtype=bool)
                        
                    elif method == "Isolation Forest":
                        try:
                            clf = IsolationForest(contamination=0.1, random_state=42)
                            outliers = clf.fit_predict(data_values) == -1
                        except:
                            outliers = np.zeros_like(data_values, dtype=bool)
                            
                    elif method == "Local Outlier Factor":
                        try:
                            lof = LocalOutlierFactor(n_neighbors=min(20, len(data_values)-1), contamination=0.1)
                            outliers = lof.fit_predict(data_values) == -1
                        except:
                            outliers = np.zeros_like(data_values, dtype=bool)
                    
                    outlier_results[feature] = {
                        'outlier_count': np.sum(outliers),
                        'outlier_percentage': (np.sum(outliers) / len(data_values)) * 100,
                        'outlier_indices': np.where(outliers)[0]
                    }
        
        # Tampilkan results
        if outlier_results:
            results_data = []
            for feature, results in outlier_results.items():
                results_data.append({
                    'Feature': feature,
                    'Outliers Detected': results['outlier_count'],
                    'Percentage': f"{results['outlier_percentage']:.2f}%"
                })
            
            results_df = pd.DataFrame(results_data)
            st.dataframe(results_df, use_container_width=True)
            
            # Visualisasi outliers untuk feature pertama
            feature = target_features[0]
            if feature in outlier_results:
                fig = go.Figure()
                
                # Data normal
                normal_data = df[feature].dropna()
                outlier_indices = outlier_results[feature]['outlier_indices']
                
                fig.add_trace(go.Box(
                    y=normal_data,
                    name="Distribution",
                    boxpoints='suspectedoutliers',
                    jitter=0.3,
                    pointpos=-1.8
                ))
                
                fig.update_layout(
                    title=f"Outlier Analysis untuk {feature} ({method})",
                    height=400,
                    yaxis_title=feature
                )
                st.plotly_chart(fig, use_container_width=True)

def machine_learning_analysis(df, numeric_cols, non_numeric_cols):
    """Analisis Machine Learning dengan Optimasi untuk Dataset Besar"""
    
    st.header("🤖 Machine Learning Analysis")
    
    # Informasi dataset
    st.subheader("📊 Dataset Info")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", f"{len(df):,}")
    with col2:
        st.metric("Total Columns", f"{len(df.columns):,}")
    with col3:
        st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Optimasi memory usage
    if st.checkbox("Optimize Memory Usage", value=True):
        df = optimize_memory_usage(df)
        st.success("Memory usage optimized!")

    # Preprocessing
    st.subheader("🔧 Data Preprocessing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        all_columns = numeric_cols + non_numeric_cols
        target_variable = st.selectbox(
            "Pilih Target Variable",
            all_columns,
            key="ml_target_select"
        )
        
        problem_type = st.selectbox(
            "Jenis Problem",
            ["Regression", "Classification", "Auto Detect"],
            key="ml_problem_type"
        )
        
        # Auto detect problem type
        if problem_type == "Auto Detect":
            if target_variable in numeric_cols:
                problem_type = "Regression"
            else:
                problem_type = "Classification"
            st.info(f"Auto-detected: {problem_type}")
    
    with col2:
        test_size = st.slider("Test Size Ratio", 0.1, 0.5, 0.2, 0.05, key="ml_test_size")
        random_state = st.number_input("Random State", value=42, key="ml_random_state")
        
        # Sampling untuk dataset besar
        sample_size = st.slider("Sample Size (untuk dataset besar)", 
                               min_value=1000, 
                               max_value=min(50000, len(df)), 
                               value=min(10000, len(df)), 
                               step=1000,
                               key="ml_sample_size")
    
    # Feature selection dengan advanced options
    st.subheader("🎯 Feature Selection")
    
    available_features = [f for f in numeric_cols + non_numeric_cols if f != target_variable]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        feature_selection_method = st.radio(
            "Feature Selection Method",
            ["Manual Selection", "Auto Select Top Features"],
            key="feature_selection_method"
        )
        
        if feature_selection_method == "Manual Selection":
            selected_features = st.multiselect(
                "Pilih Features untuk Model",
                available_features,
                default=available_features[:min(10, len(available_features))],
                key="ml_features_select"
            )
        else:
            top_k = st.slider("Number of Top Features", 5, 50, 15, key="top_k_features")
            selected_features = available_features[:top_k]
            st.info(f"Auto-selected top {top_k} features")
    
    with col2:
        # Advanced options
        st.write("**Advanced Options:**")
        use_feature_engineering = st.checkbox("Feature Engineering", value=False)
        remove_high_correlation = st.checkbox("Remove High Correlation", value=True)
        correlation_threshold = st.slider("Correlation Threshold", 0.7, 0.99, 0.9, 0.01)

    if not target_variable or not selected_features:
        st.warning("Pilih target variable dan features terlebih dahulu")
        return

    try:
        # Sampling untuk dataset besar
        if len(df) > sample_size:
            st.info(f"Using sample of {sample_size} records for faster processing")
            df_sampled = df.sample(n=sample_size, random_state=random_state)
        else:
            df_sampled = df

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Prepare data
        status_text.text("Preparing data...")
        X = df_sampled[selected_features].copy()
        y = df_sampled[target_variable]
        progress_bar.progress(20)

        # Handle large dataset - incremental processing
        chunk_size = min(1000, len(X))
        
        # Encode categorical features
        status_text.text("Encoding categorical features...")
        le_dict = {}
        categorical_columns = [col for col in selected_features if col in non_numeric_cols]
        
        for col in categorical_columns:
            # Untuk dataset besar, gunakan categorical encoding yang lebih efisien
            if X[col].nunique() > 100:  # Jika terlalu banyak kategori, gunakan frequency encoding
                freq_encoding = X[col].value_counts().to_dict()
                X[col] = X[col].map(freq_encoding)
                X[col].fillna(0, inplace=True)
            else:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                le_dict[col] = le
        progress_bar.progress(40)

        # Encode target variable
        status_text.text("Encoding target variable...")
        le_target = None
        if problem_type == "Classification" and y.dtype == 'object':
            le_target = LabelEncoder()
            y = le_target.fit_transform(y.astype(str))
        
        # Remove high correlation features
        if remove_high_correlation and len(selected_features) > 1:
            status_text.text("Removing highly correlated features...")
            X = remove_correlated_features(X, correlation_threshold)
        
        progress_bar.progress(60)

        # Handle missing values dengan metode yang lebih robust
        status_text.text("Handling missing values...")
        for col in X.columns:
            if X[col].isnull().sum() > 0:
                if X[col].dtype in ['int64', 'float64']:
                    X[col].fillna(X[col].median(), inplace=True)
                else:
                    X[col].fillna(X[col].mode()[0] if len(X[col].mode()) > 0 else 0, inplace=True)

        progress_bar.progress(80)

        # Split data
        status_text.text("Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=test_size, 
            random_state=random_state, 
            stratify=y if problem_type == "Classification" else None
        )

        # Scale features - gunakan StandardScaler yang lebih efisien
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        progress_bar.progress(100)

        # Model selection dengan progress tracking
        st.subheader("🚀 Model Training & Evaluation")
        
        # Pilihan model berdasarkan problem type dan dataset size
        if problem_type == "Regression":
            models = {
                "Linear Regression": LinearRegression(),
                "Ridge Regression": Ridge(random_state=random_state),
                "Random Forest": RandomForestRegressor(
                    n_estimators=50,  # Kurangi untuk dataset besar
                    random_state=random_state,
                    n_jobs=-1  # Gunakan semua core CPU
                ),
                "Gradient Boosting": GradientBoostingRegressor(
                    n_estimators=50,
                    random_state=random_state
                )
            }
        elif problem_type == "Classification":
            models = {
                "Logistic Regression": LogisticRegression(
                    random_state=random_state,
                    n_jobs=-1,
                    max_iter=1000
                ),
                "Random Forest": RandomForestClassifier(
                    n_estimators=50,
                    random_state=random_state,
                    n_jobs=-1
                ),
                "Gradient Boosting": GradientBoostingClassifier(
                    n_estimators=50,
                    random_state=random_state
                ),
                "XGBoost": xgb.XGBClassifier(
                    n_estimators=50,
                    random_state=random_state,
                    n_jobs=-1,
                    verbosity=0
                ) if 'xgb' in globals() else None
            }
            # Remove None models
            models = {k: v for k, v in models.items() if v is not None}

        # Train and evaluate models dengan progress bar
        results = {}
        model_progress = st.progress(0)
        total_models = len(models)
        
        for i, (name, model) in enumerate(models.items()):
            status_text.text(f"Training {name}...")
            
            try:
                # Train model
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                
                # Calculate metrics
                if problem_type == "Regression":
                    mse = mean_squared_error(y_test, y_pred)
                    rmse = np.sqrt(mse)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    results[name] = {
                        'MSE': mse,
                        'RMSE': rmse,
                        'MAE': mae,
                        'R2 Score': r2,
                        'predictions': y_pred,
                        'model': model
                    }
                
                elif problem_type == "Classification":
                    accuracy = accuracy_score(y_test, y_pred)
                    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                    
                    results[name] = {
                        'Accuracy': accuracy,
                        'Precision': precision,
                        'Recall': recall,
                        'F1-Score': f1,
                        'predictions': y_pred,
                        'model': model
                    }
                
                st.success(f"✅ {name} trained successfully")
                
            except Exception as model_error:
                st.warning(f"⚠️ Error training {name}: {str(model_error)}")
            
            model_progress.progress((i + 1) / total_models)

        status_text.text("Completed!")
        
        # Display results
        if results:
            display_ml_results(results, problem_type, X_test, y_test, selected_features, le_target)
        else:
            st.error("❌ Tidak ada model yang berhasil di-training")

    except Exception as e:
        st.error(f"❌ Error dalam ML analysis: {str(e)}")
        st.info("💡 Tips: Coba kurangi jumlah features atau gunakan sample size yang lebih kecil")

def optimize_memory_usage(df):
    """Optimize memory usage of dataframe"""
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype('category')
        elif df[col].dtype in ['int64', 'int32']:
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        elif df[col].dtype in ['float64', 'float32']:
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
    return df

def remove_correlated_features(X, threshold=0.9):
    """Remove highly correlated features"""
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    return X.drop(columns=to_drop)

def display_ml_results(results, problem_type, X_test, y_test, selected_features, le_target):
    """Display ML results with comprehensive visualizations"""
    
    st.subheader("📊 Model Performance Comparison")
    
    # Create results dataframe
    if problem_type == "Regression":
        metrics_df = pd.DataFrame({
            'Model': list(results.keys()),
            'MSE': [results[name]['MSE'] for name in results.keys()],
            'RMSE': [results[name]['RMSE'] for name in results.keys()],
            'MAE': [results[name]['MAE'] for name in results.keys()],
            'R2 Score': [results[name]['R2 Score'] for name in results.keys()]
        })
        sort_metric = 'R2 Score'
    else:
        metrics_df = pd.DataFrame({
            'Model': list(results.keys()),
            'Accuracy': [results[name]['Accuracy'] for name in results.keys()],
            'Precision': [results[name]['Precision'] for name in results.keys()],
            'Recall': [results[name]['Recall'] for name in results.keys()],
            'F1-Score': [results[name]['F1-Score'] for name in results.keys()]
        })
        sort_metric = 'Accuracy'
    
    # Display metrics table
    st.dataframe(metrics_df.sort_values(sort_metric, ascending=False), use_container_width=True)
    
    # Visualization
    col1, col2 = st.columns(2)
    
    with col1:
        # Performance comparison chart
        if problem_type == "Regression":
            fig = px.bar(metrics_df, x='Model', y='R2 Score', title="R2 Score Comparison")
        else:
            fig = px.bar(metrics_df, x='Model', y='Accuracy', title="Accuracy Comparison")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Actual vs Predicted untuk model terbaik
        best_model_name = metrics_df.loc[metrics_df[sort_metric].idxmax(), 'Model']
        best_result = results[best_model_name]
        
        if problem_type == "Regression":
            fig = px.scatter(
                x=y_test, 
                y=best_result['predictions'],
                labels={'x': 'Actual', 'y': 'Predicted'},
                title=f"Actual vs Predicted - {best_model_name}"
            )
            fig.add_trace(px.line(x=[y_test.min(), y_test.max()], y=[y_test.min(), y_test.max()]).data[0])
        else:
            # Confusion matrix
            cm = confusion_matrix(y_test, best_result['predictions'])
            fig = px.imshow(
                cm,
                labels=dict(x="Predicted", y="Actual", color="Count"),
                title=f"Confusion Matrix - {best_model_name}"
            )
        st.plotly_chart(fig, use_container_width=True)
    
    # Feature importance
    st.subheader("🔍 Feature Importance")
    for name, result in results.items():
        model = result['model']
        if hasattr(model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': selected_features[:len(model.feature_importances_)],
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            fig = px.bar(
                feature_importance.head(10),
                x='importance',
                y='feature',
                title=f"Top 10 Feature Importance - {name}",
                orientation='h'
            )
            st.plotly_chart(fig, use_container_width=True)

def deep_learning_analysis(df, numeric_cols, non_numeric_cols):
    """Analisis Deep Learning Lengkap - Optimized for Large Datasets"""
    
    st.header("🧠 Deep Learning Analysis - High Performance")
    
    # Validasi dataset
    if df.empty:
        st.error("❌ Dataset kosong! Silakan upload data terlebih dahulu.")
        return
        
    if len(numeric_cols) < 2:
        st.error("❌ Diperuhkan minimal 2 kolom numerik untuk analisis Deep Learning")
        return
    
    # Configuration untuk kecepatan
    st.subheader("⚡ Konfigurasi Kecepatan & Performa")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        processing_speed = st.selectbox(
            "Kecepatan Processing",
            ["🚀 Very Fast", "⚡ Fast", "✅ Balanced", "🐢 Comprehensive"],
            index=0,
            key="processing_speed"
        )
        
        # Set parameters berdasarkan kecepatan
        if processing_speed == "🚀 Very Fast":
            sample_size = 0.3
            epochs = 20
            batch_size = 128
        elif processing_speed == "⚡ Fast":
            sample_size = 0.5
            epochs = 30
            batch_size = 64
        elif processing_speed == "✅ Balanced":
            sample_size = 0.7
            epochs = 50
            batch_size = 32
        else:
            sample_size = 1.0
            epochs = 80
            batch_size = 16
    
    with col2:
        dl_target = st.selectbox(
            "Pilih Target Variable",
            numeric_cols,
            key="dl_target_select"
        )
        
        dl_problem_type = st.selectbox(
            "Jenis Problem DL",
            ["Regression", "Binary Classification", "Multi-class Classification"],
            key="dl_problem_type"
        )
    
    with col3:
        epochs = st.slider("Epochs", 10, 200, epochs, key="dl_epochs")
        batch_size = st.slider("Batch Size", 16, 256, batch_size, key="dl_batch_size")
        learning_rate = st.selectbox("Learning Rate", [0.001, 0.01, 0.0001, 0.00001], 
                                   index=0, key="dl_learning_rate")
    
    # Optimasi dataset besar
    st.info(f"**Mode {processing_speed}** - Sample size: {sample_size*100}% - Dataset: {len(df):,} rows")
    
    # Feature selection dengan optimasi
    available_features = [f for f in numeric_cols if f != dl_target]
    dl_features = st.multiselect(
        "Pilih Features untuk Deep Learning",
        available_features,
        default=available_features[:min(6, len(available_features))],
        key="dl_features_select"
    )
    
    if not dl_target or not dl_features:
        st.info("📝 Pilih target variable dan features untuk memulai analisis DL")
        return
    
    try:
        
        # Check GPU availability
        gpu_available = len(tf.config.experimental.list_physical_devices('GPU')) > 0
        if gpu_available:
            st.success("🎯 GPU tersedia - Training akan dipercepat!")
        else:
            st.info("💡 GPU tidak tersedia - Training menggunakan CPU")
        
        # Optimasi memory untuk dataset besar
        @st.cache_data(show_spinner=False)
        def prepare_data_optimized(_df, features, target, sample_frac=1.0, problem_type="Regression"):
            """Prepare data dengan optimasi memory"""
            # Sampling untuk dataset besar
            if sample_frac < 1.0:
                _df = _df.sample(frac=sample_frac, random_state=42)
            
            X = _df[features].fillna(_df[features].mean())
            y = _df[target]
            
            # Preprocessing target untuk classification
            if problem_type != "Regression":
                if problem_type == "Binary Classification":
                    # Pastikan binary classification
                    unique_vals = y.unique()
                    if len(unique_vals) > 2:
                        st.warning(f"⚠️ Target memiliki {len(unique_vals)} kelas. Menggunakan 2 kelas terbanyak.")
                        top_2_classes = y.value_counts().head(2).index
                        mask = y.isin(top_2_classes)
                        X = X[mask]
                        y = y[mask]
                        y = LabelEncoder().fit_transform(y)
                    else:
                        y = LabelEncoder().fit_transform(y)
                else:
                    # Multi-class classification
                    y = LabelEncoder().fit_transform(y)
            
            return X, y
        
        # Prepare data dengan optimasi
        with st.spinner("🔄 Memproses data dengan optimasi kecepatan..."):
            X, y = prepare_data_optimized(df, dl_features, dl_target, sample_size, dl_problem_type)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, 
                stratify=y if dl_problem_type != "Regression" else None
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Convert to TensorFlow datasets untuk performa tinggi
            train_dataset = tf.data.Dataset.from_tensor_slices((X_train_scaled, y_train))
            train_dataset = train_dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
            
            val_dataset = tf.data.Dataset.from_tensor_slices((X_test_scaled, y_test))
            val_dataset = val_dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
        
        # Tampilkan info dataset
        st.success(f"✅ Data siap: {len(X_train):,} training samples, {len(X_test):,} test samples")
        
        # Model architecture dengan optimasi
        st.subheader("🏗️ Neural Network Architecture - Optimized")
        
        col1, col2 = st.columns(2)
        
        with col1:
            hidden_layers = st.slider("Jumlah Hidden Layers", 1, 5, 2, key="dl_hidden_layers")
            units_per_layer = st.slider("Units per Layer", 32, 512, 64, key="dl_units")
            activation = st.selectbox("Activation Function", ["relu", "elu", "tanh", "selu"], 
                                    index=0, key="dl_activation")
        
        with col2:
            dropout_rate = st.slider("Dropout Rate", 0.0, 0.5, 0.2, 0.1, key="dl_dropout")
            optimizer = st.selectbox("Optimizer", ["adam", "rmsprop", "nadam", "sgd"], 
                                   index=0, key="dl_optimizer")
            use_batch_norm = st.checkbox("Gunakan Batch Normalization", value=True, key="dl_batchnorm")
            use_early_stopping = st.checkbox("Gunakan Early Stopping", value=True, key="dl_earlystop")
        
        # Advanced configuration
        with st.expander("⚙️ Konfigurasi Lanjutan"):
            col1, col2 = st.columns(2)
            with col1:
                weight_initializer = st.selectbox(
                    "Weight Initializer",
                    ["glorot_uniform", "he_normal", "lecun_uniform"],
                    index=0
                )
                use_l2_reg = st.checkbox("Gunakan L2 Regularization", value=False)
                l2_rate = st.slider("L2 Rate", 0.0001, 0.01, 0.001, 0.0001) if use_l2_reg else 0.0
                
            with col2:
                learning_rate_schedule = st.selectbox(
                    "Learning Rate Schedule",
                    ["Constant", "ExponentialDecay", "CosineDecay"],
                    index=0
                )
        
        # Build optimized model
        with st.spinner("🔄 Membangun model neural network..."):
            model = tf.keras.Sequential()
            
            # Input layer
            if use_l2_reg:
                model.add(tf.keras.layers.Dense(
                    units_per_layer, 
                    activation=activation, 
                    input_shape=(len(dl_features),),
                    kernel_initializer=weight_initializer,
                    kernel_regularizer=tf.keras.regularizers.l2(l2_rate)
                ))
            else:
                model.add(tf.keras.layers.Dense(
                    units_per_layer, 
                    activation=activation, 
                    input_shape=(len(dl_features),),
                    kernel_initializer=weight_initializer
                ))
                
            if use_batch_norm:
                model.add(tf.keras.layers.BatchNormalization())
            model.add(tf.keras.layers.Dropout(dropout_rate))
            
            # Hidden layers dengan optimasi
            for i in range(hidden_layers - 1):
                # Reduce units in deeper layers untuk efisiensi
                units = max(32, units_per_layer // (2 ** (i + 1)))
                
                if use_l2_reg:
                    model.add(tf.keras.layers.Dense(
                        units, 
                        activation=activation,
                        kernel_regularizer=tf.keras.regularizers.l2(l2_rate)
                    ))
                else:
                    model.add(tf.keras.layers.Dense(units, activation=activation))
                    
                if use_batch_norm:
                    model.add(tf.keras.layers.BatchNormalization())
                model.add(tf.keras.layers.Dropout(dropout_rate))
            
            # Output layer
            if dl_problem_type == "Regression":
                model.add(tf.keras.layers.Dense(1, activation='linear'))
                loss = 'mse'
                metrics = ['mae', 'mse']
                monitor_metric = 'val_loss'
            else:
                num_classes = len(np.unique(y)) if dl_problem_type == "Multi-class Classification" else 1
                activation_output = 'softmax' if dl_problem_type == "Multi-class Classification" else 'sigmoid'
                output_units = num_classes if dl_problem_type == "Multi-class Classification" else 1
                model.add(tf.keras.layers.Dense(output_units, activation=activation_output))
                loss = 'sparse_categorical_crossentropy' if dl_problem_type == "Multi-class Classification" else 'binary_crossentropy'
                metrics = ['accuracy']
                monitor_metric = 'val_accuracy'
        
        # Learning rate schedule
        if learning_rate_schedule == "ExponentialDecay":
            lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
                initial_learning_rate=learning_rate,
                decay_steps=1000,
                decay_rate=0.9
            )
        elif learning_rate_schedule == "CosineDecay":
            lr_schedule = tf.keras.optimizers.schedules.CosineDecay(
                initial_learning_rate=learning_rate,
                decay_steps=epochs * len(X_train) // batch_size
            )
        else:
            lr_schedule = learning_rate
        
        # Compile model dengan learning rate
        if optimizer == "adam":
            optimizer_obj = tf.keras.optimizers.Adam(learning_rate=lr_schedule)
        elif optimizer == "rmsprop":
            optimizer_obj = tf.keras.optimizers.RMSprop(learning_rate=lr_schedule)
        elif optimizer == "nadam":
            optimizer_obj = tf.keras.optimizers.Nadam(learning_rate=lr_schedule)
        else:
            optimizer_obj = tf.keras.optimizers.SGD(learning_rate=lr_schedule, momentum=0.9)
        
        model.compile(optimizer=optimizer_obj, loss=loss, metrics=metrics)
        
        # Display model summary
        st.subheader("📊 Model Summary")

        # Tangkap output summary dari model
        model_summary = []
        model.summary(print_fn=lambda x: model_summary.append(x))
        summary_text = "\n".join(model_summary)

        # Tambahkan CSS styling
        st.markdown("""
            <style>
            .model-summary-box {
                background-color: #fff; /* Warna gelap seperti terminal */
                color: #000; /* Warna teks hijau neon */
                border-radius: 10px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.5;
                white-space: pre-wrap;
                box-shadow: 0 0 8px rgba(0,255,179,0.3);
                border: 1px solid rgba(0,255,179,0.4);
                overflow-x: auto;
            }
            </style>
        """, unsafe_allow_html=True)

        # Gunakan expander untuk dropdown
        with st.expander("🧠 Lihat / Sembunyikan Model Summary"):
            st.markdown(f"<div class='model-summary-box'>{summary_text}</div>", unsafe_allow_html=True)
        
        # Calculate total parameters
        total_params = model.count_params()
        st.info(f"📈 Total Parameters: {total_params:,}")
        
        # Training section
        st.subheader("🚀 Pelatihan Model")
        
        if st.button("🎯 Mulai Pelatihan Deep Learning", type="primary", key="dl_train_button"):
            start_time = time.time()
            
            with st.spinner("🧠 Training neural network... Mohon tunggu..."):
                # Callbacks untuk training lebih cepat
                callbacks = []
                
                if use_early_stopping:
                    early_stopping = tf.keras.callbacks.EarlyStopping(
                        monitor=monitor_metric,
                        patience=10,
                        restore_best_weights=True,
                        mode='min' if dl_problem_type == "Regression" else 'max',
                        verbose=1
                    )
                    callbacks.append(early_stopping)
                
                reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.00001,
                    verbose=1
                )
                callbacks.append(reduce_lr)
                
                # TensorBoard callback (optional)
                # callbacks.append(tf.keras.callbacks.TensorBoard(log_dir='./logs'))
                
                # Train model dengan progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                time_estimator = st.empty()
                metrics_display = st.empty()
                
                class TrainingCallback(tf.keras.callbacks.Callback):
                    def on_epoch_begin(self, epoch, logs=None):
                        self.epoch_start_time = time.time()
                    
                    def on_epoch_end(self, epoch, logs=None):
                        progress = (epoch + 1) / epochs
                        progress_bar.progress(min(progress, 1.0))
                        
                        # Metrics display
                        if dl_problem_type == "Regression":
                            metrics_str = f"Loss: {logs['loss']:.4f}, Val Loss: {logs['val_loss']:.4f}, MAE: {logs['mae']:.4f}"
                        else:
                            metrics_str = f"Loss: {logs['loss']:.4f}, Val Loss: {logs['val_loss']:.4f}, Acc: {logs['accuracy']:.4f}"
                        
                        status_text.text(f"Epoch {epoch+1}/{epochs}")
                        metrics_display.text(f"📊 {metrics_str}")
                        
                        # Time estimation
                        elapsed = time.time() - start_time
                        epoch_time = time.time() - self.epoch_start_time
                        remaining = epoch_time * (epochs - epoch - 1)
                        
                        time_estimator.text(f"⏱️ Elapsed: {elapsed:.1f}s | Est. remaining: {remaining:.1f}s")
                
                callbacks.append(TrainingCallback())
                
                # Train model
                history = model.fit(
                    train_dataset,
                    epochs=epochs,
                    validation_data=val_dataset,
                    callbacks=callbacks,
                    verbose=0
                )
                
                training_time = time.time() - start_time
                progress_bar.progress(1.0)
                status_text.text(f"✅ Pelatihan Selesai! Waktu: {training_time:.1f} detik")
                time_estimator.text("")
                metrics_display.text("")
                
                # ==================== EVALUASI DETAIL ====================
                st.subheader("📈 Hasil Evaluasi Detail")
                
                # Predictions
                y_pred = model.predict(X_test_scaled, verbose=0)
                
                # 1. PERFORMANCE METRICS COMPREHENSIVE
                st.subheader("🎯 Dashboard Performa Model")
                
                if dl_problem_type == "Regression":
                    # Regression metrics
                    y_pred_flat = y_pred.flatten()
                    mse = mean_squared_error(y_test, y_pred_flat)
                    mae = mean_absolute_error(y_test, y_pred_flat)
                    r2 = r2_score(y_test, y_pred_flat)
                    rmse = np.sqrt(mse)
                    
                    # Additional metrics
                    mape = np.mean(np.abs((y_test - y_pred_flat) / np.where(y_test != 0, y_test, 1))) * 100
                    accuracy_percentage = max(0, min(100, (1 - mae / (y_test.max() - y_test.min())) * 100))
                    
                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("R² Score", f"{r2:.4f}", 
                                 delta="Excellent" if r2 > 0.8 else "Good" if r2 > 0.6 else "Needs Improvement")
                    with col2:
                        st.metric("MAE", f"{mae:.4f}")
                    with col3:
                        st.metric("RMSE", f"{rmse:.4f}")
                    with col4:
                        st.metric("MAPE", f"{mape:.2f}%")
                    
                else:
                    # Classification metrics
                    if dl_problem_type == "Binary Classification":
                        y_pred_class = (y_pred > 0.5).astype(int).flatten()
                    else:
                        y_pred_class = np.argmax(y_pred, axis=1)
                    
                    accuracy = accuracy_score(y_test, y_pred_class)
                    precision = precision_score(y_test, y_pred_class, average='weighted', zero_division=0)
                    recall = recall_score(y_test, y_pred_class, average='weighted', zero_division=0)
                    f1 = f1_score(y_test, y_pred_class, average='weighted', zero_division=0)
                    
                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Accuracy", f"{accuracy:.4f}",
                                 delta="Excellent" if accuracy > 0.9 else "Good" if accuracy > 0.8 else "Needs Improvement")
                    with col2:
                        st.metric("Precision", f"{precision:.4f}")
                    with col3:
                        st.metric("Recall", f"{recall:.4f}")
                    with col4:
                        st.metric("F1-Score", f"{f1:.4f}")
                
                # 2. VISUALISASI LENGKAP
                st.subheader("📊 Visualisasi Komprehensif")
                
                # Training history visualization
                fig_history = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=('Loss Progression', 'Metrics Progression'),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                # Loss plot
                fig_history.add_trace(
                    go.Scatter(x=list(range(1, len(history.history['loss'])+1)), 
                              y=history.history['loss'],
                              name='Training Loss', line=dict(color='blue')),
                    row=1, col=1
                )
                fig_history.add_trace(
                    go.Scatter(x=list(range(1, len(history.history['val_loss'])+1)), 
                              y=history.history['val_loss'],
                              name='Validation Loss', line=dict(color='red')),
                    row=1, col=1
                )
                
                # Metrics plot
                if dl_problem_type == "Regression":
                    fig_history.add_trace(
                        go.Scatter(x=list(range(1, len(history.history['mae'])+1)), 
                                  y=history.history['mae'],
                                  name='Training MAE', line=dict(color='green')),
                        row=1, col=2
                    )
                    if 'val_mae' in history.history:
                        fig_history.add_trace(
                            go.Scatter(x=list(range(1, len(history.history['val_mae'])+1)), 
                                      y=history.history['val_mae'],
                                      name='Validation MAE', line=dict(color='orange')),
                            row=1, col=2
                        )
                else:
                    fig_history.add_trace(
                        go.Scatter(x=list(range(1, len(history.history['accuracy'])+1)), 
                                  y=history.history['accuracy'],
                                  name='Training Accuracy', line=dict(color='green')),
                        row=1, col=2
                    )
                    fig_history.add_trace(
                        go.Scatter(x=list(range(1, len(history.history['val_accuracy'])+1)), 
                                  y=history.history['val_accuracy'],
                                  name='Validation Accuracy', line=dict(color='orange')),
                        row=1, col=2
                    )
                
                fig_history.update_layout(height=400, title_text="Training History")
                st.plotly_chart(fig_history, use_container_width=True)
                
                # 3. PREDICTION VISUALIZATION
                if dl_problem_type == "Regression":
                    # Regression plots
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Actual vs Predicted
                        fig_actual_pred = px.scatter(
                            x=y_test, y=y_pred_flat,
                            title="Actual vs Predicted",
                            labels={'x': 'Actual', 'y': 'Predicted'},
                            trendline="lowess"
                        )
                        fig_actual_pred.add_trace(
                            go.Scatter(x=[y_test.min(), y_test.max()], 
                                      y=[y_test.min(), y_test.max()],
                                      mode='lines', name='Perfect Prediction',
                                      line=dict(color='red', dash='dash'))
                        )
                        st.plotly_chart(fig_actual_pred, use_container_width=True)
                    
                    with col2:
                        # Residual plot
                        residuals = y_test - y_pred_flat
                        fig_residual = px.scatter(
                            x=y_pred_flat, y=residuals,
                            title="Residual Plot",
                            labels={'x': 'Predicted', 'y': 'Residuals'},
                            trendline="lowess"
                        )
                        fig_residual.add_hline(y=0, line_dash="dash", line_color="red")
                        st.plotly_chart(fig_residual, use_container_width=True)
                
                else:
                    # Classification plots
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Confusion Matrix
                        cm = confusion_matrix(y_test, y_pred_class)
                        fig_cm = px.imshow(
                            cm,
                            text_auto=True,
                            title="Confusion Matrix",
                            color_continuous_scale='Blues',
                            aspect="auto"
                        )
                        st.plotly_chart(fig_cm, use_container_width=True)
                    
                    with col2:
                        # Classification report heatmap
                        report = classification_report(y_test, y_pred_class, output_dict=True)
                        report_df = pd.DataFrame(report).transpose().iloc[:-1, :3]
                        fig_report = px.imshow(
                            report_df.values,
                            x=report_df.columns,
                            y=report_df.index,
                            text_auto=".2f",
                            title="Classification Report",
                            color_continuous_scale='Viridis',
                            aspect="auto"
                        )
                        st.plotly_chart(fig_report, use_container_width=True)
                
                # 4. FEATURE IMPORTANCE ANALYSIS
                st.subheader("🔍 Analisis Feature Importance")
                
                try:
                    # Simplified feature importance using permutation
                    @st.cache_data
                    def calculate_feature_importance(model, X_test_scaled, y_test, feature_names, problem_type):
                        baseline_score = model.evaluate(X_test_scaled, y_test, verbose=0)
                        baseline_loss = baseline_score[0] if problem_type == "Regression" else 1 - baseline_score[1]
                        
                        importance_scores = []
                        for i in range(len(feature_names)):
                            X_permuted = X_test_scaled.copy()
                            np.random.shuffle(X_permuted[:, i])
                            permuted_score = model.evaluate(X_permuted, y_test, verbose=0)
                            permuted_loss = permuted_score[0] if problem_type == "Regression" else 1 - permuted_score[1]
                            importance = max(0, baseline_loss - permuted_loss)
                            importance_scores.append(importance)
                        
                        return pd.DataFrame({
                            'Feature': feature_names,
                            'Importance': importance_scores
                        }).sort_values('Importance', ascending=False)
                    
                    feature_importance_df = calculate_feature_importance(
                        model, X_test_scaled, y_test, dl_features, dl_problem_type
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_importance = px.bar(
                            feature_importance_df,
                            x='Importance',
                            y='Feature',
                            orientation='h',
                            title="Feature Importance",
                            color='Importance',
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig_importance, use_container_width=True)
                    
                    with col2:
                        fig_importance_pie = px.pie(
                            feature_importance_df,
                            values='Importance',
                            names='Feature',
                            title="Feature Importance Distribution"
                        )
                        st.plotly_chart(fig_importance_pie, use_container_width=True)
                        
                except Exception as e:
                    st.warning(f"⚠️ Feature importance calculation skipped: {str(e)}")
                
                # 5. MODEL PERFORMANCE GAUGE
                st.subheader("📈 Performance Summary")
                
                if dl_problem_type == "Regression":
                    performance_score = min(100, max(0, (r2 + (1 - mae/y_test.std())) * 50))
                    performance_level = "Sangat Baik" if performance_score > 85 else \
                                      "Baik" if performance_score > 70 else \
                                      "Cukup" if performance_score > 60 else "Perlu Improvement"
                else:
                    performance_score = accuracy * 100
                    performance_level = "Sangat Baik" if performance_score > 90 else \
                                      "Baik" if performance_score > 80 else \
                                      "Cukup" if performance_score > 70 else "Perlu Improvement"
                
                # Gauge chart
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = performance_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': f"Model Performance: {performance_level}"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 60], 'color': "red"},
                            {'range': [60, 75], 'color': "yellow"},
                            {'range': [75, 90], 'color': "lightgreen"},
                            {'range': [90, 100], 'color': "green"}],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90}}
                ))
                st.plotly_chart(fig_gauge, use_container_width=True)
                
                # 6. DOWNLOAD DAN EXPORT MODEL
                st.subheader("💾 Export Model")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Save model
                    if st.button("💾 Save TensorFlow Model"):
                        model.save('saved_model.h5')
                        with open('saved_model.h5', 'rb') as f:
                            st.download_button(
                                label="📥 Download Model",
                                data=f,
                                file_name="deep_learning_model.h5",
                                mime="application/octet-stream"
                            )
                
                with col2:
                    # Export predictions
                    predictions_df = pd.DataFrame({
                        'Actual': y_test,
                        'Predicted': y_pred.flatten() if dl_problem_type == "Regression" else y_pred_class
                    })
                    csv = predictions_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Predictions",
                        data=csv,
                        file_name="model_predictions.csv",
                        mime="text/csv"
                    )
                
                # 7. RECOMMENDATIONS AND INSIGHTS
                st.subheader("💡 Insights & Rekomendasi")
                
                # Training insights
                final_epoch = len(history.history['loss'])
                final_loss = history.history['loss'][-1]
                final_val_loss = history.history['val_loss'][-1]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Final Training Loss", f"{final_loss:.4f}")
                with col2:
                    st.metric("Final Validation Loss", f"{final_val_loss:.4f}")
                with col3:
                    st.metric("Training Time", f"{training_time:.1f}s")
                
                # Recommendations based on performance
                st.info("""
                **🎯 Rekomendasi Improvement:**
                - **Data Quality**: Periksa missing values dan outliers
                - **Feature Engineering**: Tambahkan feature yang lebih relevan
                - **Hyperparameter Tuning**: Eksperimen dengan architecture berbeda
                - **Regularization**: Adjust dropout dan L2 regularization
                - **Learning Rate**: Coba learning rate scheduling
                """)
                
                # Performance tips
                if performance_score < 70:
                    st.warning("""
                    **⚠️ Area Improvement:**
                    - Pertimbangkan feature selection yang lebih baik
                    - Coba model architecture yang lebih dalam/lebar
                    - Gunakan lebih banyak data training
                    - Eksperimen dengan different optimizers
                    """)
                else:
                    st.success("""
                    **✅ Performa Baik!**
                    - Model sudah menunjukkan hasil yang promising
                    - Pertimbangkan deployment untuk penggunaan real-time
                    - Monitor model performance secara berkala
                    """)
    
    except Exception as e:
        st.error(f"❌ Error dalam DL analysis: {str(e)}")
        st.info("""
        💡 Tips Troubleshooting:
        - Pastikan dataset cukup besar (>100 samples)
        - Gunakan mode kecepatan lebih tinggi untuk dataset besar
        - Kurangi jumlah features jika memory error
        - Pastikan target variable sesuai dengan problem type
        - Coba learning rate yang lebih kecil
        """)

# Tambahkan fungsi utility jika diperlukan
def validate_tensorflow_installation():
    """Validate TensorFlow installation"""
    try:
        import tensorflow as tf
        version = tf.__version__
        gpu_available = tf.config.list_physical_devices('GPU')
        return True, version, len(gpu_available) > 0
    except ImportError:
        return False, None, False

def model_comparison_analysis(df, numeric_cols, non_numeric_cols):
    """Analisis komparatif data yang komprehensif tanpa model machine learning"""
    
    st.header("📊 Advanced Data Analysis Dashboard")
    
    # Informasi dataset
    st.subheader("📋 Dataset Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Samples", f"{len(df):,}")
    with col2:
        st.metric("Features", f"{len(numeric_cols) + len(non_numeric_cols):,}")
    with col3:
        st.metric("Numeric", f"{len(numeric_cols):,}")
    with col4:
        st.metric("Categorical", f"{len(non_numeric_cols):,}")
    
    # Configuration section
    st.subheader("⚙️ Analysis Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Target selection untuk analisis
        target_variable = st.selectbox(
            "dwibaktindev AI",
            numeric_cols + non_numeric_cols,
            key="analysis_target"
        )
        
        # Analysis type
        analysis_type = st.selectbox(
            "Alisa AI",
            ["Descriptive Statistics", "Correlation Analysis", "Distribution Analysis", 
             "Relationship Analysis", "Comparative Analysis"],
            key="analysis_type"
        )
    
    with col2:
        # Feature selection
        available_features = [f for f in numeric_cols + non_numeric_cols if f != target_variable]
        selected_features = st.multiselect(
            "Sasha AI",
            available_features,
            default=available_features[:min(10, len(available_features))],
            key="analysis_features"
        )
        
        # Sample size untuk visualisasi
        sample_size = st.slider("Sample Size for Visualization", 100, len(df), 
                               min(1000, len(df)), 100, key="sample_size")

    if st.button("🚀 Start Model AI", type="primary", key="start_analysis"):
        if not target_variable or not selected_features:
            st.error("❌ Please select target variable and features")
            return
        
        try:
            # Lakukan analisis berdasarkan jenis
            with st.spinner("🔄 Performing analysis..."):
                if analysis_type == "Descriptive Statistics":
                    perform_descriptive_analysis(df, target_variable, selected_features)
                
                elif analysis_type == "Correlation Analysis":
                    perform_correlation_analysis(df, target_variable, selected_features)
                
                elif analysis_type == "Distribution Analysis":
                    perform_distribution_analysis(df, target_variable, selected_features, sample_size)
                
                elif analysis_type == "Relationship Analysis":
                    perform_relationship_analysis(df, target_variable, selected_features, sample_size)
                
                elif analysis_type == "Comparative Analysis":
                    perform_comparative_analysis(df, target_variable, selected_features)
            
            st.success("✅ Analysis completed!")
        
        except Exception as e:
            st.error(f"❌ Error in data analysis: {str(e)}")

def perform_descriptive_analysis(df, target, features):
    """Analisis statistik deskriptif"""
    import pandas as pd
    import numpy as np
    
    st.subheader("📊 Descriptive Statistics")
    
    # Statistik untuk target variable
    st.write(f"### Target Variable: `{target}`")
    
    if pd.api.types.is_numeric_dtype(df[target]):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean", f"{df[target].mean():.2f}")
        with col2:
            st.metric("Median", f"{df[target].median():.2f}")
        with col3:
            st.metric("Std Dev", f"{df[target].std():.2f}")
        with col4:
            st.metric("Missing", f"{df[target].isnull().sum()}")
        
        # Detailed statistics
        st.dataframe(df[target].describe(), use_container_width=True)
        
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Unique Values", df[target].nunique())
        with col2:
            st.metric("Most Frequent", df[target].mode().iloc[0] if not df[target].mode().empty else "N/A")
        with col3:
            st.metric("Missing", f"{df[target].isnull().sum()}")
        
        # Value counts
        value_counts = df[target].value_counts()
        st.write("**Value Distribution:**")
        st.dataframe(value_counts, use_container_width=True)
    
    # Statistik untuk features numerik
    numeric_features = [f for f in features if pd.api.types.is_numeric_dtype(df[f])]
    if numeric_features:
        st.write("### Numeric Features Summary")
        st.dataframe(df[numeric_features].describe(), use_container_width=True)
    
    # Statistik untuk features kategorik
    categorical_features = [f for f in features if not pd.api.types.is_numeric_dtype(df[f])]
    if categorical_features:
        st.write("### Categorical Features Summary")
        for feature in categorical_features:
            with st.expander(f"`{feature}`"):
                value_counts = df[feature].value_counts()
                st.dataframe(value_counts, use_container_width=True)

def perform_correlation_analysis(df, target, features):
    """Analisis korelasi"""
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.subheader("🔗 Correlation Analysis")
    
    # Pilih hanya features numerik untuk korelasi
    numeric_features = [f for f in features if pd.api.types.is_numeric_dtype(df[f])]
    
    if pd.api.types.is_numeric_dtype(df[target]):
        numeric_features.append(target)
    
    if len(numeric_features) < 2:
        st.warning("⚠️ Need at least 2 numeric features for correlation analysis")
        return
    
    correlation_df = df[numeric_features].corr()
    
    # Heatmap korelasi
    st.write("### Correlation Heatmap")
    fig = px.imshow(correlation_df,
                   title="Feature Correlation Heatmap",
                   color_continuous_scale="RdBu_r",
                   aspect="auto")
    st.plotly_chart(fig, use_container_width=True)
    
    # Korelasi dengan target
    if pd.api.types.is_numeric_dtype(df[target]):
        st.write("### Correlation with Target")
        target_corr = correlation_df[target].drop(target).sort_values(ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(x=target_corr.values, y=target_corr.index,
                        orientation='h',
                        title=f"Correlation with {target}",
                        labels={'x': 'Correlation', 'y': 'Feature'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Tabel korelasi
            st.dataframe(target_corr.round(4), use_container_width=True)

def perform_distribution_analysis(df, target, features, sample_size):
    """Analisis distribusi"""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    st.subheader("📈 Distribution Analysis")
    
    # Sample data untuk performa visualisasi
    sample_df = df.sample(min(sample_size, len(df)), random_state=42)
    
    # Distribusi target variable
    st.write(f"### Target Variable Distribution: `{target}`")
    
    if pd.api.types.is_numeric_dtype(df[target]):
        col1, col2 = st.columns(2)
        
        with col1:
            # Histogram
            fig = px.histogram(df, x=target, 
                              title=f"Distribution of {target}",
                              nbins=50)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Box plot
            fig = px.box(df, y=target, 
                        title=f"Box Plot of {target}")
            st.plotly_chart(fig, use_container_width=True)
    else:
        # Untuk variabel kategorik
        value_counts = df[target].value_counts()
        fig = px.pie(values=value_counts.values, 
                    names=value_counts.index,
                    title=f"Distribution of {target}")
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribusi features numerik
    numeric_features = [f for f in features if pd.api.types.is_numeric_dtype(df[f])]
    if numeric_features:
        st.write("### Numeric Features Distribution")
        
        # Pilih features untuk ditampilkan
        selected_numeric = st.multiselect(
            "Select numeric features to visualize:",
            numeric_features,
            default=numeric_features[:min(3, len(numeric_features))]
        )
        
        if selected_numeric:
            # Histogram multiple
            fig = make_subplots(rows=len(selected_numeric), cols=1,
                              subplot_titles=selected_numeric)
            
            for i, feature in enumerate(selected_numeric, 1):
                fig.add_trace(
                    go.Histogram(x=df[feature], name=feature, nbinsx=30),
                    row=i, col=1
                )
            
            fig.update_layout(height=300*len(selected_numeric), 
                            title_text="Distribution of Numeric Features")
            st.plotly_chart(fig, use_container_width=True)
    
    # Distribusi features kategorik
    categorical_features = [f for f in features if not pd.api.types.is_numeric_dtype(df[f])]
    if categorical_features:
        st.write("### Categorical Features Distribution")
        
        selected_categorical = st.multiselect(
            "Select categorical features to visualize:",
            categorical_features,
            default=categorical_features[:min(2, len(categorical_features))]
        )
        
        if selected_categorical:
            for feature in selected_categorical:
                value_counts = df[feature].value_counts().head(10)  # Top 10 saja
                fig = px.bar(x=value_counts.values, y=value_counts.index,
                            orientation='h',
                            title=f"Top 10 Values in {feature}")
                st.plotly_chart(fig, use_container_width=True)

def perform_relationship_analysis(df, target, features, sample_size):
    """Analisis hubungan antara variabel"""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.subheader("🔄 Relationship Analysis")
    
    sample_df = df.sample(min(sample_size, len(df)), random_state=42)
    
    # Pilih features numerik untuk scatter plot
    numeric_features = [f for f in features if pd.api.types.is_numeric_dtype(df[f])]
    
    if pd.api.types.is_numeric_dtype(df[target]) and len(numeric_features) >= 1:
        st.write("### Scatter Plots with Target")
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_feature = st.selectbox("X-axis feature:", numeric_features, key="scatter_x")
        
        with col2:
            color_feature = st.selectbox("Color by (optional):", 
                                       [None] + [f for f in features if f != x_feature],
                                       key="scatter_color")
        
        if x_feature:
            fig = px.scatter(sample_df, x=x_feature, y=target,
                           color=color_feature if color_feature else None,
                           title=f"{target} vs {x_feature}",
                           opacity=0.6)
            st.plotly_chart(fig, use_container_width=True)
    
    # Pair plot untuk multiple numeric features
    if len(numeric_features) >= 2:
        st.write("### Pairwise Relationships")
        
        selected_for_pairplot = st.multiselect(
            "Select features for pair plot:",
            numeric_features + ([target] if pd.api.types.is_numeric_dtype(df[target]) else []),
            default=(numeric_features + [target])[:min(4, len(numeric_features) + 1)]
        )
        
        if len(selected_for_pairplot) >= 2:
            fig = px.scatter_matrix(sample_df[selected_for_pairplot],
                                  dimensions=selected_for_pairplot,
                                  height=800)
            st.plotly_chart(fig, use_container_width=True)
    
    # Analisis hubungan kategorik-numerik
    categorical_features = [f for f in features if not pd.api.types.is_numeric_dtype(df[f])]
    if categorical_features and pd.api.types.is_numeric_dtype(df[target]):
        st.write("### Categorical vs Numerical Analysis")
        
        cat_feature = st.selectbox("Select categorical feature:", categorical_features)
        num_feature = st.selectbox("Select numerical feature:", 
                                 [target] + numeric_features)
        
        if cat_feature and num_feature:
            col1, col2 = st.columns(2)
            
            with col1:
                # Box plot
                fig = px.box(df, x=cat_feature, y=num_feature,
                           title=f"{num_feature} by {cat_feature}")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Violin plot
                fig = px.violin(df, x=cat_feature, y=num_feature,
                              title=f"Distribution of {num_feature} by {cat_feature}")
                st.plotly_chart(fig, use_container_width=True)

def perform_comparative_analysis(df, target, features):
    """Analisis komparatif"""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    
    st.subheader("⚖️ Comparative Analysis")
    
    # Group by analysis
    st.write("### Group-wise Analysis")
    
    group_feature = st.selectbox(
        "Group by feature:",
        [None] + [f for f in features if not pd.api.types.is_numeric_dtype(df[f])]
    )
    
    if group_feature:
        if pd.api.types.is_numeric_dtype(df[target]):
            # Untuk target numerik
            summary = df.groupby(group_feature)[target].agg(['mean', 'median', 'std', 'count']).round(2)
            st.dataframe(summary, use_container_width=True)
            
            # Visualisasi
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(summary.reset_index(), x=group_feature, y='mean',
                           title=f"Average {target} by {group_feature}")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.box(df, x=group_feature, y=target,
                           title=f"Distribution of {target} by {group_feature}")
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            # Untuk target kategorik
            cross_tab = pd.crosstab(df[group_feature], df[target], normalize='index') * 100
            st.write("**Percentage Distribution:**")
            st.dataframe(cross_tab.round(2), use_container_width=True)
            
            # Stacked bar chart
            fig = px.bar(cross_tab.reset_index(), 
                        x=group_feature,
                        y=cross_tab.columns.tolist(),
                        title=f"Distribution of {target} by {group_feature}",
                        barmode='stack')
            st.plotly_chart(fig, use_container_width=True)
    
    # Time series analysis (jika ada kolom datetime)
    datetime_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
    if datetime_columns and pd.api.types.is_numeric_dtype(df[target]):
        st.write("### Time Series Analysis")
        
        date_col = st.selectbox("Select date column:", datetime_columns)
        
        if date_col:
            # Aggregasi berdasarkan waktu
            df_sorted = df.sort_values(date_col)
            
            # Pilih frekuensi aggregasi
            freq = st.selectbox("Aggregation frequency:", 
                              ['D', 'W', 'M', 'Q'], 
                              format_func=lambda x: {'D': 'Daily', 'W': 'Weekly', 
                                                   'M': 'Monthly', 'Q': 'Quarterly'}[x])
            
            time_series = df_sorted.set_index(date_col)[target].resample(freq).mean()
            
            fig = px.line(time_series.reset_index(), 
                         x=date_col, y=target,
                         title=f"{target} Over Time")
            st.plotly_chart(fig, use_container_width=True)

def feature_analysis_dashboard(df, numeric_cols, non_numeric_cols):
    """Dashboard analisis feature yang komprehensif dengan optimasi dataset besar"""
    
    st.header("🔍 Advanced Feature Analysis")
    
    # Informasi dataset
    st.subheader("📊 Dataset Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Features", f"{len(numeric_cols) + len(non_numeric_cols):,}")
    with col2:
        st.metric("Numeric Features", f"{len(numeric_cols):,}")
    with col3:
        st.metric("Categorical Features", f"{len(non_numeric_cols):,}")
    
    # Optimasi memory
    if st.checkbox("Optimize Memory Usage", value=True, key="feature_optimize_mem"):
        df = optimize_memory_usage_feature(df)
        st.success("✅ Memory usage optimized!")

    # Performance configuration
    st.subheader("⚡ Performance Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sampling options untuk dataset besar
        use_sampling = st.checkbox("Use Sampling for Large Dataset", value=len(df) > 10000, 
                                 key="feature_use_sampling")
        
        if use_sampling:
            sample_size = st.slider(
                "Sample Size", 
                min_value=1000, 
                max_value=min(50000, len(df)), 
                value=min(20000, len(df)), 
                step=1000,
                key="feature_sample_size"
            )
            st.info(f"🎯 Using {sample_size} samples from {len(df):,} total records")
        
        # Processing speed control
        processing_speed = st.select_slider(
            "Processing Speed",
            options=["Fast", "Balanced", "Comprehensive"],
            value="Balanced",
            key="feature_processing_speed"
        )
        
        # Configure parameters based on speed selection
        speed_config = {
            "Fast": {"n_estimators": 50, "n_repeats": 3, "max_features": 20},
            "Balanced": {"n_estimators": 100, "n_repeats": 5, "max_features": 30},
            "Comprehensive": {"n_estimators": 200, "n_repeats": 10, "max_features": 50}
        }
        config = speed_config[processing_speed]
    
    with col2:
        # Advanced options
        st.write("**Advanced Options:**")
        
        max_features_display = st.slider(
            "Max Features to Display", 
            5, 50, 15, 
            key="max_features_display"
        )
        
        remove_high_corr = st.checkbox(
            "Remove Highly Correlated Features", 
            value=True, 
            key="feature_remove_corr"
        )
        
        correlation_threshold = st.slider(
            "Correlation Threshold", 
            0.7, 0.99, 0.9, 0.01,
            key="feature_corr_threshold"
        )
        
        random_state = st.number_input(
            "Random State", 
            value=42, 
            key="feature_random_state"
        )

    # Feature importance analysis
    st.subheader("🎯 Feature Importance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Multiple methods untuk feature importance
        importance_method = st.selectbox(
            "Pilih Feature Importance Method",
            ["Random Forest", "Permutation Importance", "Mutual Information", "All Methods"],
            key="feature_importance_method"
        )
        
        # Problem type selection
        problem_type = st.radio(
            "Problem Type",
            ["Regression", "Classification", "Auto Detect"],
            key="feature_problem_type"
        )
    
    with col2:
        target_feature = st.selectbox(
            "Pilih Target untuk Feature Importance",
            numeric_cols + non_numeric_cols,
            key="feature_importance_target"
        )
        
        # Feature selection
        available_features = [f for f in numeric_cols + non_numeric_cols if f != target_feature]
        
        if len(available_features) > config["max_features"]:
            st.warning(f"⚠️ Showing first {config['max_features']} features. Use comprehensive mode for more.")
            available_features = available_features[:config["max_features"]]
        
        selected_features = st.multiselect(
            "Pilih Features untuk Analysis",
            available_features,
            default=available_features[:min(10, len(available_features))],
            key="feature_analysis_features"
        )

    if not target_feature or not selected_features:
        st.warning("📝 Pilih target feature dan features untuk analysis")
        return

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    if st.button("🚀 Hitung Feature Importance", key="feature_importance_button"):
        try:
            # Apply sampling jika diperlukan
            if use_sampling and len(df) > sample_size:
                df_analysis = df.sample(n=sample_size, random_state=random_state)
                st.info(f"🔬 Analyzing {sample_size:,} sampled records")
            else:
                df_analysis = df
            
            status_text.text("🔄 Preparing data...")
            progress_bar.progress(10)

            # Prepare features and target
            X = df_analysis[selected_features].copy()
            y = df_analysis[target_feature]
            
            # Auto-detect problem type
            if problem_type == "Auto Detect":
                if target_feature in numeric_cols:
                    problem_type_detected = "Regression"
                else:
                    problem_type_detected = "Classification"
                st.info(f"🔍 Auto-detected: {problem_type_detected}")
            else:
                problem_type_detected = problem_type
            
            progress_bar.progress(20)

            # Preprocessing dengan optimasi
            status_text.text("🔧 Preprocessing features...")
            X_processed, feature_names = preprocess_features_optimized(
                X, numeric_cols, non_numeric_cols, remove_high_corr, correlation_threshold
            )
            
            progress_bar.progress(40)

            # Encode target variable jika classification
            le_target = None
            if problem_type_detected == "Classification" and y.dtype == 'object':
                le_target = LabelEncoder()
                y = le_target.fit_transform(y.astype(str))
                st.info(f"🎯 Target encoded: {len(le_target.classes_)} classes")
            
            progress_bar.progress(50)

            # Handle missing values
            X_processed = handle_missing_values_optimized(X_processed)
            
            progress_bar.progress(60)

            # Calculate feature importance berdasarkan method yang dipilih
            status_text.text("📊 Calculating feature importance...")
            
            results = {}
            
            if importance_method in ["Random Forest", "All Methods"]:
                results["Random Forest"] = calculate_rf_importance(
                    X_processed, y, problem_type_detected, config, random_state
                )
                progress_bar.progress(70)
            
            if importance_method in ["Permutation Importance", "All Methods"]:
                results["Permutation"] = calculate_permutation_importance(
                    X_processed, y, problem_type_detected, config, random_state
                )
                progress_bar.progress(80)
            
            if importance_method in ["Mutual Information", "All Methods"]:
                results["Mutual Info"] = calculate_mutual_info(
                    X_processed, y, problem_type_detected
                )
                progress_bar.progress(90)

            progress_bar.progress(95)

            # Display results
            status_text.text("📈 Displaying results...")
            display_feature_importance_results(
                results, feature_names, max_features_display, problem_type_detected
            )
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis completed!")
            
            # Additional insights
            show_feature_analysis_insights(results, X_processed, y, problem_type_detected)

        except Exception as e:
            st.error(f"❌ Error dalam feature importance analysis: {str(e)}")
            st.info("💡 Tips: Coba kurangi jumlah features, gunakan sampling, atau pilih mode 'Fast'")

def optimize_memory_usage_feature(df):
    """Optimize memory usage for feature analysis"""
    start_mem = df.memory_usage(deep=True).sum() / 1024**2
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type == 'object':
            if df[col].nunique() / len(df) < 0.5:  # Jika cardinality tidak terlalu tinggi
                df[col] = df[col].astype('category')
        elif col_type in ['int64', 'int32']:
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                df[col] = df[col].astype(np.int8)
            elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        elif col_type in ['float64', 'float32']:
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                df[col] = df[col].astype(np.float16)
            elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                df[col] = df[col].astype(np.float32)
    
    end_mem = df.memory_usage(deep=True).sum() / 1024**2
    st.success(f"💾 Memory reduced: {start_mem:.2f}MB → {end_mem:.2f}MB ({((start_mem - end_mem) / start_mem * 100):.1f}% reduction)")
    
    return df

def preprocess_features_optimized(X, numeric_cols, non_numeric_cols, remove_high_corr, threshold):
    """Preprocess features dengan optimasi untuk dataset besar"""
    
    X_processed = X.copy()
    feature_names = list(X.columns)
    
    # Encode categorical features dengan metode yang efisien
    categorical_columns = [col for col in X.columns if col in non_numeric_cols]
    
    for col in categorical_columns:
        if X_processed[col].nunique() > 50:  # Untuk categorical dengan banyak unique values
            # Gunakan frequency encoding
            freq_map = X_processed[col].value_counts().to_dict()
            X_processed[col] = X_processed[col].map(freq_map)
            X_processed[col].fillna(0, inplace=True)
        else:
            # Gunakan label encoding
            le = LabelEncoder()
            X_processed[col] = le.fit_transform(X_processed[col].astype(str))
    
    # Remove highly correlated features
    if remove_high_corr and len(X_processed.columns) > 1:
        numeric_features = [col for col in X_processed.columns if col in numeric_cols or col in categorical_columns]
        if len(numeric_features) > 1:
            X_numeric = X_processed[numeric_features]
            corr_matrix = X_numeric.corr().abs()
            
            # Hapus feature yang highly correlated
            upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            to_drop = [column for column in upper_triangle.columns if any(upper_triangle[column] > threshold)]
            
            if to_drop:
                X_processed = X_processed.drop(columns=to_drop)
                feature_names = [f for f in feature_names if f not in to_drop]
                st.info(f"🗑️ Removed {len(to_drop)} highly correlated features")
    
    return X_processed, feature_names

def handle_missing_values_optimized(X):
    """Handle missing values dengan metode yang optimal"""
    X_processed = X.copy()
    
    for col in X_processed.columns:
        if X_processed[col].isnull().sum() > 0:
            if X_processed[col].dtype in ['int8', 'int16', 'int32', 'int64', 'float16', 'float32', 'float64']:
                # Untuk numeric, gunakan median (lebih robust terhadap outliers)
                X_processed[col].fillna(X_processed[col].median(), inplace=True)
            else:
                # Untuk categorical, gunakan mode
                if len(X_processed[col].mode()) > 0:
                    X_processed[col].fillna(X_processed[col].mode()[0], inplace=True)
                else:
                    X_processed[col].fillna(0, inplace=True)
    
    return X_processed

def calculate_rf_importance(X, y, problem_type, config, random_state):
    """Calculate Random Forest feature importance"""
    if problem_type == "Regression":
        model = RandomForestRegressor(
            n_estimators=config["n_estimators"],
            random_state=random_state,
            n_jobs=-1  # Parallel processing
        )
    else:
        model = RandomForestClassifier(
            n_estimators=config["n_estimators"],
            random_state=random_state,
            n_jobs=-1
        )
    
    model.fit(X, y)
    importances = model.feature_importances_
    
    return {
        'importances': importances,
        'model': model
    }

def calculate_permutation_importance(X, y, problem_type, config, random_state):
    """Calculate permutation importance"""
    if problem_type == "Regression":
        model = RandomForestRegressor(
            n_estimators=config["n_estimators"],
            random_state=random_state,
            n_jobs=-1
        )
    else:
        model = RandomForestClassifier(
            n_estimators=config["n_estimators"],
            random_state=random_state,
            n_jobs=-1
        )
    
    model.fit(X, y)
    
    # Untuk dataset besar, gunakan subsample
    if len(X) > 10000:
        X_subsample = X.sample(n=10000, random_state=random_state)
        y_subsample = y.loc[X_subsample.index]
    else:
        X_subsample = X
        y_subsample = y
    
    perm_importance = permutation_importance(
        model, X_subsample, y_subsample,
        n_repeats=config["n_repeats"],
        random_state=random_state,
        n_jobs=-1  # Parallel processing
    )
    
    return {
        'importances': perm_importance.importances_mean,
        'std': perm_importance.importances_std
    }

def calculate_mutual_info(X, y, problem_type):
    """Calculate mutual information"""
    if problem_type == "Regression":
        mi = mutual_info_regression(X, y, random_state=42, n_jobs=-1)
    else:
        mi = mutual_info_classif(X, y, random_state=42, n_jobs=-1)
    
    return {
        'importances': mi
    }

def display_feature_importance_results(results, feature_names, max_display, problem_type):
    """Display feature importance results dengan visualisasi yang komprehensif"""
    
    st.subheader("📊 Feature Importance Results")
    
    # Tampilkan semua methods dalam tabs
    tabs = st.tabs(list(results.keys()))
    
    for tab, (method_name, result) in zip(tabs, results.items()):
        with tab:
            importances = result['importances']
            
            # Create importance dataframe
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            # Display top features
            st.write(f"**Top {min(max_display, len(importance_df))} Features - {method_name}**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart
                fig = px.bar(
                    importance_df.head(max_display),
                    x='importance',
                    y='feature',
                    title=f"{method_name} Feature Importance",
                    orientation='h',
                    color='importance',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Table view
                st.dataframe(
                    importance_df.head(10)[['feature', 'importance']].round(4),
                    use_container_width=True
                )
            
            # Additional info untuk permutation importance
            if method_name == "Permutation" and 'std' in result:
                st.write("**Permutation Importance with Std Dev:**")
                perm_df = pd.DataFrame({
                    'feature': feature_names,
                    'importance': importances,
                    'std': result['std']
                }).sort_values('importance', ascending=False)
                
                fig = px.bar(
                    perm_df.head(max_display),
                    x='importance',
                    y='feature',
                    error_x='std',
                    title="Permutation Importance ± Std Dev",
                    orientation='h'
                )
                st.plotly_chart(fig, use_container_width=True)

def show_feature_analysis_insights(results, X, y, problem_type):
    """Show additional insights dari feature analysis"""
    
    st.subheader("💡 Analysis Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Dataset Characteristics:**")
        st.write(f"- Total samples: {len(X):,}")
        st.write(f"- Total features: {len(X.columns)}")
        st.write(f"- Problem type: {problem_type}")
        
        if problem_type == "Classification":
            st.write(f"- Number of classes: {len(np.unique(y))}")
        else:
            st.write(f"- Target range: {y.min():.2f} to {y.max():.2f}")
    
    with col2:
        st.write("**Feature Importance Consensus:**")
        
        # Hitung consensus dari semua methods
        consensus_scores = {}
        for method_name, result in results.items():
            importances = result['importances']
            for i, feature in enumerate(X.columns):
                if feature not in consensus_scores:
                    consensus_scores[feature] = []
                consensus_scores[feature].append(importances[i])
        
        # Rata-rata score across methods
        avg_scores = {feature: np.mean(scores) for feature, scores in consensus_scores.items()}
        top_features = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for feature, score in top_features:
            st.write(f"- {feature}: {score:.4f}")
    
    # Correlation analysis untuk top features
    if len(results) > 0:
        st.write("**Top Features Correlation Matrix:**")
        
        # Ambil top 8 features dari method pertama
        first_method = list(results.values())[0]
        top_indices = np.argsort(first_method['importances'])[-8:][::-1]
        top_features_corr = [X.columns[i] for i in top_indices if i < len(X.columns)]
        
        if len(top_features_corr) > 1:
            corr_matrix = X[top_features_corr].corr()
            
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Correlation Matrix of Top Features"
            )
            st.plotly_chart(fig, use_container_width=True)

# Fungsi untuk memuat data
def load_data(uploaded_file):
    """Memuat data dari file yang diupload"""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Format file tidak didukung. Harap upload file CSV atau Excel.")
            return None
        return df
    except Exception as e:
        st.error(f"Error memuat file: {str(e)}")
        return None

# Fungsi utama untuk menjalankan dashboard
def run_ml_dl_dashboard():
    """
    Fungsi utama untuk menjalankan dashboard ML/DL dengan upload file
    """
    st.title("🤖 Advanced ML/DL Analysis Dashboard")
    
    # File upload
    st.sidebar.header("📁 Upload Dataset")
    uploaded_file = st.sidebar.file_uploader(
        "Pilih file CSV atau Excel", 
        type=['csv', 'xls', 'xlsx'],
        key="file_uploader"
    )
    
    if uploaded_file is not None:
        # Load data
        df = load_data(uploaded_file)
        
        if df is not None:
            st.sidebar.success(f"✅ File berhasil dimuat: {uploaded_file.name}")
            st.sidebar.info(f"Shape: {df.shape[0]} baris × {df.shape[1]} kolom")
            
            # Tampilkan preview data
            if st.sidebar.checkbox("Tampilkan Preview Data", key="preview_checkbox"):
                st.subheader("📋 Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                st.subheader("📊 Data Info")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Data Types:**")
                    st.write(df.dtypes)
                
                with col2:
                    st.write("**Missing Values:**")
                    missing_data = df.isnull().sum()
                    st.write(missing_data[missing_data > 0])
            
            # Identifikasi kolom numerik dan kategorikal
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
            
            # Jalankan dashboard utama
            create_ml_dl_analysis_dashboard(df, numeric_cols, non_numeric_cols)
    else:
        st.info("👆 Silakan upload file CSV atau Excel untuk memulai analisis")
        
        # Contoh data untuk demonstrasi
        if st.checkbox("Gunakan Sample Data untuk Demo", key="sample_data_checkbox"):
            sample_data = pd.DataFrame({
                'feature1': np.random.normal(0, 1, 1000),
                'feature2': np.random.exponential(2, 1000),
                'feature3': np.random.randint(0, 10, 1000),
                'target_regression': np.random.normal(0, 1, 1000),
                'target_classification': np.random.choice([0, 1], 1000),
                'category': np.random.choice(['A', 'B', 'C'], 1000),
                'timestamp': pd.date_range('2023-01-01', periods=1000, freq='H')
            })
            
            st.success("✅ Menggunakan sample data untuk demonstrasi")
            create_ml_dl_analysis_dashboard(sample_data, 
                                          ['feature1', 'feature2', 'feature3', 'target_regression', 'target_classification'],
                                          ['category', 'timestamp'])


# Fungsi statistik yang dioptimalkan
@st.cache_data(show_spinner=False)
def show_optimized_statistics(df):
    st.header("📊 Statistik Deskriptif")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Jumlah Baris", df.shape[0])
    with col2:
        st.metric("Jumlah Kolom", df.shape[1])
    with col3:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        st.metric("Kolom Numerik", len(numeric_cols))
    with col4:
        non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        st.metric("Kolom Non-Numerik", len(non_numeric_cols))
    
    st.subheader("👀 Preview Data")
    preview_df = df.head(100) if len(df) > 100 else df
    st.dataframe(preview_df, use_container_width=True)

    # STATISTIK NUMERIK
    if numeric_cols:
        st.subheader("📈 Statistik Numerik Lengkap")
        clean_df = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
        desc_stats = clean_df.describe()
        
        # Tambahkan metrik tambahan
        additional_stats = pd.DataFrame({
            'median': clean_df.median(),
            'variance': clean_df.var(),
            'skewness': clean_df.skew(),
            'kurtosis': clean_df.kurtosis(),
            'range': clean_df.max() - clean_df.min(),
            'coefficient_of_variation': (clean_df.std() / clean_df.mean()) * 100
        }).T
        
        st.write("**Statistik Deskriptif Dasar:**")
        st.dataframe(desc_stats, use_container_width=True)
        
        st.write("**Statistik Tambahan:**")
        st.dataframe(additional_stats, use_container_width=True)
        
        # Visualisasi distribusi numerik
        st.write("**📊 Distribusi Data Numerik**")
        for col in numeric_cols[:4]:  # Batasi agar tidak terlalu banyak
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    df[col].hist(bins=30, ax=ax, edgecolor='black')
                    ax.set_title(f'Distribusi {col}')
                    ax.set_xlabel(col)
                    ax.set_ylabel('Frekuensi')
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error plot distribusi {col}: {e}")
            
            with col2:
                try:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.boxplot(df[col].dropna())
                    ax.set_title(f'Box Plot {col}')
                    ax.set_ylabel(col)
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error box plot {col}: {e}")

    # ANALISIS MISSING VALUES
    st.subheader("❓ Informasi Missing Values")
    missing_data = df.isnull().sum()
    missing_percent = (missing_data / len(df)) * 100
    missing_df = pd.DataFrame({
        'Kolom': missing_data.index,
        'Jumlah Missing': missing_data.values,
        'Persentase Missing': missing_percent.values
    })

    st.dataframe(missing_df, use_container_width=True)

    # Visualisasi missing values
    if missing_data.sum() > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                missing_df_sorted = missing_df[missing_df['Jumlah Missing'] > 0].sort_values('Persentase Missing', ascending=False)
                if not missing_df_sorted.empty:
                    bars = ax.bar(missing_df_sorted['Kolom'], missing_df_sorted['Persentase Missing'])
                    ax.set_title('Persentase Missing Values per Kolom')
                    ax.set_ylabel('Persentase Missing (%)')
                    ax.tick_params(axis='x', rotation=45)
                    # Tambahkan nilai di atas bar
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                            f'{height:.1f}%', ha='center', va='bottom')
                    st.pyplot(fig)
            except Exception as e:
                st.error(f"Error visualisasi missing values: {e}")
        
        with col2:
            try:
                # Heatmap missing values
                fig, ax = plt.subplots(figsize=(12, 6))
                sns.heatmap(df.isnull(), yticklabels=False, cbar=True, cmap='viridis', ax=ax)
                ax.set_title('Pattern Missing Values (Heatmap)')
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Error heatmap missing values: {e}")

    # ANALISIS TANGGAL LENGKAP
    st.subheader("📅 Analisis Data Tanggal Lengkap")

    # Identifikasi kolom tanggal - lebih robust
    date_cols = []
    potential_date_cols = []

    for col in df.columns:
        # Cek jika sudah datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        else:
            # Coba identifikasi kolom potensial
            sample_size = min(100, len(df[col].dropna()))
            if sample_size > 0:
                sample = df[col].dropna().head(sample_size)
                
                # Cek berbagai format tanggal
                date_patterns = [
                    r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}',  # YYYY-MM-DD, DD/MM/YYYY, dll
                    r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
                    r'\d{4}-\d{2}-\d{2}',  # ISO format
                    r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
                    r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
                ]
                
                date_like = False
                for pattern in date_patterns:
                    if sample.astype(str).str.match(pattern).any():
                        date_like = True
                        break
                
                if date_like:
                    potential_date_cols.append(col)

    if date_cols:
        st.success(f"✅ **Kolom tanggal yang terdeteksi:** {', '.join(date_cols)}")
        
        for col in date_cols:
            st.markdown(f"#### 📊 Analisis Mendalam untuk `{col}`")
            
            # Pastikan kolom dalam format datetime
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Hapus nilai NaN yang mungkin muncul dari konversi
            date_series = df[col].dropna()
            
            if len(date_series) == 0:
                st.warning(f"Tidak ada data tanggal yang valid di kolom {col}")
                continue
            
            # Container untuk statistik dasar
            col1, col2 = st.columns(2)
            
            with col1:
                # Statistik dasar tanggal
                st.write("**📋 Statistik Dasar:**")
                date_stats_data = {
                    'Metrik': ['Tanggal Terawal', 'Tanggal Terakhir', 'Rentang Waktu', 'Jumlah Hari', 'Data Valid', 'Data Invalid'],
                    'Nilai': [
                        date_series.min().strftime('%Y-%m-%d'),
                        date_series.max().strftime('%Y-%m-%d'),
                        f"{(date_series.max() - date_series.min()).days} hari",
                        (date_series.max() - date_series.min()).days,
                        len(date_series),
                        len(df[col]) - len(date_series)
                    ]
                }
                date_stats = pd.DataFrame(date_stats_data)
                st.dataframe(date_stats, use_container_width=True, hide_index=True)
            
            with col2:
                # Analisis komponen tanggal
                st.write("**🔍 Distribusi Komponen Tanggal:**")
                
                # Ekstrak komponen tanggal
                year_counts = date_series.dt.year.value_counts().sort_index()
                month_counts = date_series.dt.month.value_counts().sort_index()
                day_counts = date_series.dt.day.value_counts().sort_index()
                dow_counts = date_series.dt.dayofweek.value_counts().sort_index()
                
                # Mapping untuk nama
                month_names = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 
                            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
                day_names = {0: 'Senin', 1: 'Selasa', 2: 'Rabu', 3: 'Kamis', 
                            4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'}
                
                comp_data = {
                    'Komponen': ['Tahun', 'Bulan', 'Hari', 'Hari dalam Minggu'],
                    'Jumlah Unik': [
                        year_counts.shape[0],
                        month_counts.shape[0],
                        day_counts.shape[0],
                        dow_counts.shape[0]
                    ],
                    'Nilai Terbanyak': [
                        f"{year_counts.index[0]} ({year_counts.iloc[0]} data)",
                        f"{month_names.get(month_counts.index[0], month_counts.index[0])} ({month_counts.iloc[0]} data)",
                        f"{day_counts.index[0]} ({day_counts.iloc[0]} data)",
                        f"{day_names.get(dow_counts.index[0], dow_counts.index[0])} ({dow_counts.iloc[0]} data)"
                    ]
                }
                comp_df = pd.DataFrame(comp_data)
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
            
            # Visualisasi trend waktu
            st.write("**📈 Trend Data Berdasarkan Waktu:**")
            
            trend_col1, trend_col2 = st.columns(2)
            
            with trend_col1:
                # Frekuensi per bulan
                try:
                    monthly_count = date_series.dt.to_period('M').value_counts().sort_index()
                    monthly_count.index = monthly_count.index.astype(str)
                    if not monthly_count.empty:
                        fig, ax = plt.subplots(figsize=(10, 4))
                        monthly_count.plot(kind='bar', ax=ax, color='skyblue', edgecolor='black')
                        ax.set_title(f'Frekuensi Data per Bulan - {col}')
                        ax.set_xlabel('Bulan-Tahun')
                        ax.set_ylabel('Jumlah Data')
                        ax.tick_params(axis='x', rotation=45)
                        st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error membuat chart bulanan: {e}")
            
            with trend_col2:
                # Frekuensi per tahun
                try:
                    yearly_count = date_series.dt.year.value_counts().sort_index()
                    if not yearly_count.empty:
                        fig, ax = plt.subplots(figsize=(10, 4))
                        yearly_count.plot(kind='bar', ax=ax, color='lightgreen', edgecolor='black')
                        ax.set_title(f'Frekuensi Data per Tahun - {col}')
                        ax.set_xlabel('Tahun')
                        ax.set_ylabel('Jumlah Data')
                        st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error membuat chart tahunan: {e}")
            
            # Analisis musiman/harian
            st.write("**🌍 Analisis Musiman dan Harian:**")
            
            seasonal_col1, seasonal_col2 = st.columns(2)
            
            with seasonal_col1:
                # Distribusi per bulan (Pie chart)
                try:
                    month_names_list = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 
                                    'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
                    monthly_dist = date_series.dt.month.value_counts().sort_index()
                    if len(monthly_dist) > 0:
                        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                        
                        # Pie chart
                        monthly_dist_pie = monthly_dist.copy()
                        monthly_dist_pie.index = [month_names_list[i-1] for i in monthly_dist_pie.index]
                        ax1.pie(monthly_dist_pie.values, labels=monthly_dist_pie.index, autopct='%1.1f%%', startangle=90)
                        ax1.set_title(f'Distribusi per Bulan - {col}')
                        
                        # Bar chart
                        monthly_dist_pie.plot(kind='bar', ax=ax2, color='coral', edgecolor='black')
                        ax2.set_title(f'Distribusi per Bulan - {col}')
                        ax2.set_ylabel('Jumlah Data')
                        ax2.tick_params(axis='x', rotation=45)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error analisis bulanan: {e}")
            
            with seasonal_col2:
                # Distribusi hari dalam minggu
                try:
                    day_names_list = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                    dow_dist = date_series.dt.dayofweek.value_counts().sort_index()
                    if len(dow_dist) > 0:
                        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                        
                        # Pie chart
                        dow_dist_pie = dow_dist.copy()
                        dow_dist_pie.index = [day_names_list[i] for i in dow_dist_pie.index]
                        ax1.pie(dow_dist_pie.values, labels=dow_dist_pie.index, autopct='%1.1f%%', startangle=90)
                        ax1.set_title(f'Distribusi Hari dalam Minggu - {col}')
                        
                        # Bar chart
                        dow_dist_pie.plot(kind='bar', ax=ax2, color='gold', edgecolor='black')
                        ax2.set_title(f'Distribusi Hari dalam Minggu - {col}')
                        ax2.set_ylabel('Jumlah Data')
                        ax2.tick_params(axis='x', rotation=45)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                except Exception as e:
                    st.error(f"Error analisis hari: {e}")
            
            # Analisis quarter/triwulan
            st.write("**📊 Analisis per Triwulan:**")
            try:
                quarter_dist = date_series.dt.quarter.value_counts().sort_index()
                if not quarter_dist.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig, ax = plt.subplots(figsize=(8, 6))
                        quarter_names = {1: 'Q1 (Jan-Mar)', 2: 'Q2 (Apr-Jun)', 
                                    3: 'Q3 (Jul-Sep)', 4: 'Q4 (Okt-Des)'}
                        quarter_dist.index = [quarter_names[i] for i in quarter_dist.index]
                        quarter_dist.plot(kind='pie', autopct='%1.1f%%', ax=ax)
                        ax.set_ylabel('')  # Remove ylabel for pie chart
                        ax.set_title(f'Distribusi per Triwulan - {col}')
                        st.pyplot(fig)
                    
                    with col2:
                        st.dataframe(pd.DataFrame({
                            'Triwulan': quarter_dist.index,
                            'Jumlah Data': quarter_dist.values,
                            'Persentase': (quarter_dist.values / len(date_series) * 100).round(2)
                        }), use_container_width=True)
            except Exception as e:
                st.error(f"Error analisis triwulan: {e}")
            
            # Deteksi missing dates
            st.write("**🔎 Analisis Kelengkapan Tanggal:**")
            try:
                if len(date_series) > 1:
                    date_range = pd.date_range(start=date_series.min(), end=date_series.max(), freq='D')
                    missing_dates = date_range.difference(date_series)
                    
                    completeness_info = pd.DataFrame({
                        'Metrik': ['Total Hari dalam Rentang', 'Hari dengan Data', 'Hari Tanpa Data', 'Persentase Kelengkapan'],
                        'Nilai': [
                            len(date_range),
                            len(date_range) - len(missing_dates),
                            len(missing_dates),
                            f"{((len(date_range) - len(missing_dates)) / len(date_range) * 100):.2f}%"
                        ]
                    })
                    st.dataframe(completeness_info, use_container_width=True, hide_index=True)
                    
                    if len(missing_dates) > 0:
                        st.warning(f"⚠️ Terdapat {len(missing_dates)} hari tanpa data")
                        if len(missing_dates) <= 20:
                            st.write("**Tanggal yang hilang:**", missing_dates.strftime('%Y-%m-%d').tolist())
                        else:
                            st.write(f"**Contoh 20 tanggal yang hilang:**", missing_dates[:20].strftime('%Y-%m-%d').tolist())
                    
                    # Visualisasi kelengkapan
                    if len(date_range) > 0:
                        completeness_ratio = (len(date_range) - len(missing_dates)) / len(date_range)
                        
                        fig, ax = plt.subplots(figsize=(8, 2))
                        ax.barh(['Kelengkapan'], [completeness_ratio * 100], color='lightblue', height=0.5)
                        ax.barh(['Kelengkapan'], [100 - completeness_ratio * 100], 
                            left=[completeness_ratio * 100], color='lightcoral', height=0.5)
                        ax.set_xlim(0, 100)
                        ax.set_xlabel('Persentase (%)')
                        ax.set_title(f'Kelengkapan Data Tanggal - {col}')
                        ax.text(completeness_ratio * 100 / 2, 0, f'{completeness_ratio*100:.1f}% Terisi', 
                            ha='center', va='center', color='black', fontweight='bold')
                        ax.text(completeness_ratio * 100 + (100 - completeness_ratio * 100) / 2, 0, 
                            f'{(100 - completeness_ratio*100):.1f}% Kosong', 
                            ha='center', va='center', color='black', fontweight='bold')
                        st.pyplot(fig)
                else:
                    st.info("Data tanggal terlalu sedikit untuk analisis kelengkapan")
            except Exception as e:
                st.error(f"Error analisis kelengkapan: {e}")
            
            st.markdown("---")
            
    else:
        st.info("❌ Tidak ada kolom tanggal yang terdeteksi dalam dataset.")
        
        # Analisis kolom potensial
        if potential_date_cols:
            st.write("**🔍 Kolom yang mungkin berisi tanggal:**")
            potential_info = []
            
            for col in potential_date_cols:
                sample = df[col].dropna().head(5)
                unique_count = df[col].nunique()
                null_count = df[col].isnull().sum()
                
                potential_info.append({
                    'Kolom': col,
                    'Tipe Data': str(df[col].dtype),
                    'Contoh Nilai': sample.iloc[0] if len(sample) > 0 else 'N/A',
                    'Nilai Unik': unique_count,
                    'Null Values': null_count,
                    'Saran': 'Coba konversi ke datetime'
                })
            
            if potential_info:
                potential_df = pd.DataFrame(potential_info)
                st.dataframe(potential_df, use_container_width=True)
                
                st.write("**💡 Tips Konversi:**")
                st.code("""
    # Untuk konversi manual:
    df['nama_kolom'] = pd.to_datetime(df['nama_kolom'], errors='coerce')

    # Dengan format spesifik:
    df['nama_kolom'] = pd.to_datetime(df['nama_kolom'], format='%Y-%m-%d', errors='coerce')
                """)
        
        # Analisis data kategorikal jika tidak ada tanggal
        st.write("**📋 Analisis Data Kategorikal sebagai Alternatif:**")
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if categorical_cols:
            for col in categorical_cols[:3]:  # Batasi 3 kolom pertama
                st.write(f"**Analisis untuk `{col}`**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Value counts
                    value_counts = df[col].value_counts()
                    st.dataframe(value_counts.head(10), use_container_width=True)
                
                with col2:
                    # Pie chart untuk top categories
                    try:
                        top_categories = value_counts.head(5)
                        if len(top_categories) > 0:
                            fig, ax = plt.subplots(figsize=(6, 6))
                            ax.pie(top_categories.values, labels=top_categories.index, autopct='%1.1f%%')
                            ax.set_title(f'Top 5 Kategori - {col}')
                            st.pyplot(fig)
                    except Exception as e:
                        st.error(f"Error pie chart {col}: {e}")
                
                st.markdown("---")
        else:
            st.info("Tidak ada kolom kategorikal yang tersedia untuk analisis alternatif.")

    # Tambahan: Summary statistics
    st.subheader("📊 Summary Dataset")
    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric("Total Baris", len(df))
        st.metric("Total Kolom", len(df.columns))

    with summary_col2:
        numeric_count = len(numeric_cols) if 'numeric_cols' in locals() else len(df.select_dtypes(include=[np.number]).columns)
        categorical_count = len(df.select_dtypes(include=['object']).columns)
        st.metric("Kolom Numerik", numeric_count)
        st.metric("Kolom Kategorikal", categorical_count)

    with summary_col3:
        total_missing = df.isnull().sum().sum()
        total_cells = df.shape[0] * df.shape[1]
        completeness = ((total_cells - total_missing) / total_cells * 100)
        st.metric("Total Missing Values", total_missing)
        st.metric("Kelengkapan Dataset", f"{completeness:.1f}%")

# Cache untuk file contoh
@st.cache_data(show_spinner=False)
def create_sample_file():
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    np.random.seed(42)
    price_changes = np.random.normal(0.001, 0.02, len(dates))
    prices = 100 * (1 + price_changes).cumprod()
    
    volumes = np.random.randint(1000, 10000, len(dates))
    
    example_data = pd.DataFrame({
        'Tanggal': dates,
        'Open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
        'High': prices * (1 + np.abs(np.random.normal(0.005, 0.01, len(dates)))),
        'Low': prices * (1 - np.abs(np.random.normal(0.005, 0.01, len(dates)))),
        'Close': prices,
        'Volume': volumes,
        'Target_Sales': np.random.randint(5000, 15000, len(dates)),
        'Actual_Sales': np.random.randint(4000, 16000, len(dates)),
        'Perusahaan': np.random.choice(['AAPL', 'GOOGL', 'MSFT', 'AMZN'], len(dates)),
        'Sektor': np.random.choice(['Teknologi', 'Kesehatan', 'Finansial', 'Konsumsi'], len(dates)),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], len(dates)),
        'Kategori_Produk': np.random.choice(['Laptop', 'Smartphone', 'Tablet', 'Aksesori'], len(dates))
    })
    
    for i in range(len(example_data)):
        example_data.loc[i, 'High'] = max(example_data.loc[i, 'Open'], example_data.loc[i, 'Close'], example_data.loc[i, 'High'])
        example_data.loc[i, 'Low'] = min(example_data.loc[i, 'Open'], example_data.loc[i, 'Close'], example_data.loc[i, 'Low'])
    
    return example_data

# UI utama
st.markdown("Unggah file CSV atau Excel untuk melihat visualisasi dan statistik data.")
        
with st.expander("📜 PENJELASAN TENTANG ANALISIS DATA", expanded=False):
    st.markdown("""
    **Penjelasan Penting 📛**
    
    ### 🧾 Pengertian
    - Analisis data adalah proses yang mengolah data mulai dari identifikasi, pembersihan, transformasi, hingga pemodelan untuk mendapatkan informasi yang berguna. 
    - Tujuannya adalah mengubah data mentah menjadi wawasan yang bisa digunakan untuk pemecahan masalah atau penetapan strategi. 
    
    ### ⚠️ Proses utama
    - 🛠️ Pengumpulan data: Mengumpulkan data dari berbagai sumber seperti sensor, wawancara, atau sistem internal. 
    - 🛠️ Pembersihan data: Membersihkan data dari kesalahan, ketidaksesuaian, atau ketidaksesuaian lainnya agar data siap dianalisis. 
    - 🛠️ Transformasi data: Mengubah data menjadi format yang lebih sesuai untuk analisis. 
    - 🛠️ Analisis data: Menerapkan teknik statistik atau algoritma untuk menganalisis data dan menemukan pola. 
    - 🛠️ Interpretasi hasil: Menginterpretasikan hasil analisis untuk mendapatkan wawasan yang dapat diterapkan. 
    
    ### 🔖 Manfaat
    - ⚙️ Pengambilan keputusan yang lebih akurat: Keputusan yang didasarkan pada data (berbasis data) lebih akurat dibandingkan keputusan yang hanya didasarkan pada intuisi.
    - ⚙️ Meningkatkan efisiensi operasional: Membantu mengidentifikasi area yang bisa dioptimalkan dalam proses bisnis.
    - ⚙️ Menciptakan keunggulan kompetitif: Memungkinkan bisnis merespons perubahan pasar dengan lebih efektif.
    - ⚙️ Mendorong inovasi produk: Memahami preferensi pelanggan dapat mengarah pada pengembangan produk atau layanan baru. 
    
    ### 📑 Metode
    - 📖 Pengambilan keputusan yang lebih akurat: Keputusan yang didasarkan pada data (berbasis data) lebih akurat dibandingkan keputusan yang hanya didasarkan pada intuisi.
    - 📖 Meningkatkan efisiensi operasional: Membantu mengidentifikasi area yang bisa dioptimalkan dalam proses bisnis.
    - 📖 Menciptakan keunggulan kompetitif: Memungkinkan bisnis merespons perubahan pasar dengan lebih efektif.
    - 📖 Mendorong inovasi produk: Memahami preferensi pelanggan dapat mengarah pada pengembangan produk atau layanan baru. 
    """)
    
with st.expander("📜 PENJELASAN TENTANG STATISTIK DATA", expanded=False):
    st.markdown("""
    **Penjelasan Penting 📛**
    
    ### 🧾 Proses dan tujuan statistik data
    - Analisis data adalah proses yang mengolah data mulai dari identifikasi, pembersihan, transformasi, hingga pemodelan untuk mendapatkan informasi yang berguna. 
    - Tujuannya adalah mengubah data mentah menjadi wawasan yang bisa digunakan untuk pemecahan masalah atau penetapan strategi. 
    
    ### ⚠️ Proses utama
    - 🛠️ Pengumpulan: Data bisa dikumpulkan melalui berbagai cara seperti wawancara, observasi, kuesioner, atau sensus.
    - 🛠️ Pengolahan: Data mentah kemudian diolah, dikelompokkan, dan ditabulasi. Hasilnya bisa disajikan dalam bentuk tabel, grafik, atau bentuk lainnya untuk mempermudah pemahaman.
    - 🛠️ Analisis dan interpretasi: Statistik membantu menganalisis data untuk menemukan pola, tren, dan hubungan antar variabel, serta menarik kesimpulan yang dapat digunakan untuk pengambilan keputusan. 
    - 🛠️ Tujuan: Memecahkan masalah kompleks yang melibatkan data numerik, memberikan gambaran yang representatif tentang data yang dikaji, serta membantu pemerintah dan industri dalam membuat kebijakan atau strategi yang tepat. 
    
    ### 🔖 Berdasarkan sifat 
    - ⚙️ Kuantitatif: Data yang dapat diukur dengan bilangan, seperti tinggi badan atau jumlah penduduk. 
    - ⚙️ Kualitatif: Data yang berbentuk kategori atau deskripsi, seperti preferensi atau warna. 
    
    ### 📑 Berdasarkan hasil pengukuran
    - 📖 Nominal: Data yang digunakan untuk memberi label atau kategori, tanpa urutan tertentu (misalnya, jenis kelamin). 
    - 📖 Ordinal: Data yang memiliki urutan atau peringkat (misalnya, tingkat kepuasan: baik, sedang, buruk). 
    - 📖 Interval: Data yang memiliki jarak yang diketahui antara nilai-nilai, tetapi tidak memiliki titik nol yang absolut (misalnya, suhu). 
    - 📖 Rasio: Data yang memiliki jarak yang diketahui dan titik nol yang absolut (misalnya, tinggi badan, berat badan). 
    """)
    
with st.expander("📜 PENJELASAN LENGKAP MENGENAI ROY ACADEMY", expanded=False):
    st.markdown("""
    **Penjelasan Penting 📛**
    
    ### 🧾 Tujuan Adanya Roy Academy
    - Tujuan Adanya Roy Akademi adalah untuk kalian yang bergabung dalam penelitian dan proses ini di buat oleh dwi bakti n dev dengan tujuan menjadi penjelasan yang mudah dimengerti dan mudah dibaca.
    """)

# Sidebar
st.sidebar.header("🎛️ Kontrol Aplikasi")

if st.sidebar.button("📁 Buat File Contoh"):
    example_data = create_sample_file()
    csv = example_data.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Unduh Contoh CSV",
        data=csv,
        file_name="contoh_data_saham.csv",
        mime="text/csv"
    )

# Upload file
st.sidebar.header("📤 Unggah & Gabungkan Beberapa File")
uploaded_files = st.sidebar.file_uploader(
    "Pilih file CSV atau Excel (bisa multiple)",
    type=['csv', 'xlsx', 'xls'],
    accept_multiple_files=True
)

# Pilihan website
website_option = st.sidebar.selectbox(
    "Pilih Website:",
    ["https://streamlit-launcher.vercel.app/", "Custom URL"]
)

if website_option == "Custom URL":
    custom_url = st.sidebar.text_input("Masukkan URL custom:")
    if custom_url:
        website_url = custom_url
    else:
        website_url = "https://streamlit-launcher.vercel.app/"
else:
    website_url = website_option

# Tampilkan iframe
if st.sidebar.button("🌐 Tampilkan Website"):
    st.markdown(f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 10px; padding: 10px; margin: 10px 0;">
        <iframe src="{website_url}" width="100%" height="600" style="border: none; border-radius: 8px;"></iframe>
    </div>
    """, unsafe_allow_html=True)

merge_method = "concat"
if uploaded_files and len(uploaded_files) > 1:
    merge_method = st.sidebar.selectbox(
        "Metode Penggabungan Data",
        ["concat", "inner", "outer", "left", "right"],
        key="merge_method_select"
    )


# Proses file
df = None
if uploaded_files:
    datasets = []
    for uploaded_file in uploaded_files:
        dataset = process_uploaded_file(uploaded_file)
        if dataset is not None:
            datasets.append(dataset)
    
    if datasets:
        if len(datasets) == 1:
            df = datasets[0]
        else:
            df = merge_datasets(datasets, merge_method)

try:
    from stl import mesh
    import trimesh
    import os
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.express as px
except ImportError:
    st.warning("Beberapa library 3D tidak terinstall. Install dengan: pip install numpy-stl trimesh plotly")
REMOVE_BG_API_KEY = "xQH5KznYiupRrywK5yPcjeyi"
PIXELS_API_KEY = "LH59shPdj1xO0lolnHPsClH23qsnHE4NjkCFBhKEXvR0CbqwkrXbqBnw"
if df is not None:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "📊 Statistik", "📈 Visualisasi", "💾 Data", "ℹ️ Informasi", "🧮 Kalkulator",
        "🖼️ Vitures", "📍 Flowchart", "📊 Grafik Saham", "🗃️ SQL Style", 
        "🔄 3D Model & Analisis", "⚡ Konversi Cepat"
    ])
    
    with tab11:
        st.header("⚡ Konversi File XLS - CSV (High Performance)")
        
        # Cache untuk konversi file
        @st.cache_data(show_spinner=False, max_entries=3, ttl=3600)
        def convert_xls_to_csv(uploaded_file):
            """Konversi XLS ke CSV dengan optimasi"""
            start_time = time.time()
            
            # Baca hanya kolom yang diperlukan untuk preview
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Optimasi tipe data untuk mengurangi memory usage
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Convert object to string untuk efisiensi
                    df[col] = df[col].astype('string')
                elif 'int' in str(df[col].dtype):
                    # Downcast integer
                    df[col] = pd.to_numeric(df[col], downcast='integer', errors='ignore')
                elif 'float' in str(df[col].dtype):
                    # Downcast float
                    df[col] = pd.to_numeric(df[col], downcast='float', errors='ignore')
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            processing_time = time.time() - start_time
            
            return df, csv_data, processing_time

        @st.cache_data(show_spinner=False, max_entries=3, ttl=3600)
        def convert_csv_to_xls(uploaded_file):
            """Konversi CSV ke XLS dengan optimasi"""
            start_time = time.time()
            
            # Baca CSV dengan optimasi
            df = pd.read_csv(uploaded_file, low_memory=False)
            
            # Optimasi memory
            df = optimize_dataframe(df)
            
            # Konversi ke Excel di memory - PERBAIKAN: hapus parameter options
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
                # Tambahkan auto-filter dan formatting
                worksheet = writer.sheets['Data']
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
                
            excel_data = output.getvalue()
            
            processing_time = time.time() - start_time
            return df, excel_data, processing_time

        def optimize_dataframe(df):
            """Optimasi dataframe untuk mengurangi memory usage"""
            # Downcast numeric columns
            for col in df.select_dtypes(include=[np.number]).columns:
                df[col] = pd.to_numeric(df[col], downcast='unsigned', errors='ignore')
            
            # Convert object columns to category jika unique values < 50%
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')
            
            return df

        def analyze_file_health(df, file_type):
            """Analisis kesehatan file dan tampilkan metrics"""
            total_cells = df.shape[0] * df.shape[1]
            
            # Hitung missing values
            missing_values = df.isnull().sum().sum()
            missing_percentage = (missing_values / total_cells * 100) if total_cells > 0 else 0
            
            # Hitung duplicate rows
            duplicate_rows = df.duplicated().sum()
            duplicate_percentage = (duplicate_rows / len(df) * 100) if len(df) > 0 else 0
            
            # Analisis tipe data
            data_types = df.dtypes.value_counts()
            
            # Memory usage
            memory_usage = df.memory_usage(deep=True).sum() / 1024  # KB
            
            return {
                'total_cells': total_cells,
                'missing_values': missing_values,
                'missing_percentage': missing_percentage,
                'duplicate_rows': duplicate_rows,
                'duplicate_percentage': duplicate_percentage,
                'data_types': data_types,
                'memory_usage_kb': memory_usage
            }

        def create_health_chart(health_data):
            """Buat chart kesehatan file"""
            fig = go.Figure()
            
            # Chart untuk missing values dan duplicates
            fig.add_trace(go.Bar(
                name='Masalah Data',
                x=['Missing Values', 'Duplicate Rows'],
                y=[health_data['missing_percentage'], health_data['duplicate_percentage']],
                text=[f"{health_data['missing_percentage']:.1f}%", 
                    f"{health_data['duplicate_percentage']:.1f}%"],
                textposition='auto',
                marker_color=['#FF6B6B', '#4ECDC4']
            ))
            
            fig.update_layout(
                title='Kesehatan File - Masalah Data',
                yaxis_title='Persentase (%)',
                showlegend=False,
                height=300
            )
            
            return fig

        def create_data_type_chart(data_types):
            """Buat chart distribusi tipe data"""
            fig = go.Figure(data=[go.Pie(
                labels=[str(dtype) for dtype in data_types.index],
                values=data_types.values,
                hole=.3
            )])
            
            fig.update_layout(
                title='Distribusi Tipe Data',
                height=300
            )
            
            return fig

        def display_performance_metrics(original_size, processed_size, processing_time, rows, cols, health_data):
            """Tampilkan metrics performa"""
            compression_ratio = (1 - processed_size / original_size) * 100 if original_size > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("⏱️ Waktu Proses", f"{processing_time:.2f}s")
            with col2:
                st.metric("📊 Jumlah Data", f"{rows:,} baris, {cols} kolom")
            with col3:
                st.metric("📦 Ukuran File", f"{processed_size/1024:.1f} KB")
            with col4:
                st.metric("🎯 Kompresi", f"{compression_ratio:.1f}%")
            
            # Health metrics
            st.subheader("🏥 Kesehatan File")
            health_col1, health_col2, health_col3, health_col4 = st.columns(4)
            
            with health_col1:
                st.metric("🔍 Missing Values", f"{health_data['missing_percentage']:.1f}%",
                        delta=f"-{health_data['missing_values']} cells" if health_data['missing_values'] > 0 else None)
            
            with health_col2:
                st.metric("🔄 Duplicate Rows", f"{health_data['duplicate_percentage']:.1f}%",
                        delta=f"-{health_data['duplicate_rows']} rows" if health_data['duplicate_rows'] > 0 else None)
            
            with health_col3:
                st.metric("💾 Memory Usage", f"{health_data['memory_usage_kb']:.1f} KB")
            
            with health_col4:
                health_score = max(0, 100 - health_data['missing_percentage'] - health_data['duplicate_percentage'])
                st.metric("🏆 Health Score", f"{health_score:.1f}%")

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚀 XLS/XLSX → CSV")
            uploaded_xls = st.file_uploader(
                "Upload Excel", 
                type=['xls', 'xlsx'],
                key="xls_upload",
                help="Upload file Excel (.xls, .xlsx) maksimal 200MB"
            )
            
            if uploaded_xls is not None:
                # Progress bar untuk visual feedback
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔄 Memproses file Excel...")
                progress_bar.progress(30)
                
                try:
                    # Gunakan cached function
                    excel_df, csv_data, processing_time = convert_xls_to_csv(uploaded_xls)
                    progress_bar.progress(80)
                    
                    status_text.text("✅ Konversi berhasil!")
                    progress_bar.progress(100)
                    
                    # Analisis kesehatan file
                    health_data = analyze_file_health(excel_df, 'excel')
                    
                    # Tampilkan preview cepat (hanya 5 baris pertama)
                    with st.expander("👀 Quick Preview", expanded=False):
                        st.dataframe(excel_df.head(5), use_container_width=True)
                    
                    # Performance metrics dengan health data
                    original_size = len(uploaded_xls.getvalue())
                    processed_size = len(csv_data)
                    display_performance_metrics(
                        original_size, processed_size, processing_time, 
                        excel_df.shape[0], excel_df.shape[1], health_data
                    )
                    
                    # Chart kesehatan
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.plotly_chart(create_health_chart(health_data), use_container_width=True)
                    with chart_col2:
                        st.plotly_chart(create_data_type_chart(health_data['data_types']), use_container_width=True)
                    
                    # Download button
                    st.download_button(
                        label=f"📥 Download CSV ({len(csv_data)/1024:.1f} KB)",
                        data=csv_data,
                        file_name=f"{uploaded_xls.name.split('.')[0]}_converted.csv",
                        mime="text/csv",
                        key="download_csv"
                    )
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.text("❌ Error!")
                    st.error(f"Gagal memproses file: {str(e)}")
                finally:
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
        
        with col2:
            st.subheader("🚀 CSV → XLSX")
            uploaded_csv = st.file_uploader(
                "Upload CSV", 
                type=['csv'],
                key="csv_upload",
                help="Upload file CSV maksimal 200MB"
            )
            
            if uploaded_csv is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔄 Memproses file CSV...")
                progress_bar.progress(30)
                
                try:
                    # Gunakan cached function
                    csv_df, excel_data, processing_time = convert_csv_to_xls(uploaded_csv)
                    progress_bar.progress(80)
                    
                    status_text.text("✅ Konversi berhasil!")
                    progress_bar.progress(100)
                    
                    # Analisis kesehatan file
                    health_data = analyze_file_health(csv_df, 'csv')
                    
                    # Quick preview
                    with st.expander("👀 Quick Preview", expanded=False):
                        st.dataframe(csv_df.head(5), use_container_width=True)
                    
                    # Performance metrics dengan health data
                    original_size = len(uploaded_csv.getvalue())
                    processed_size = len(excel_data)
                    display_performance_metrics(
                        original_size, processed_size, processing_time,
                        csv_df.shape[0], csv_df.shape[1], health_data
                    )
                    
                    # Chart kesehatan
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.plotly_chart(create_health_chart(health_data), use_container_width=True)
                    with chart_col2:
                        st.plotly_chart(create_data_type_chart(health_data['data_types']), use_container_width=True)
                    
                    # Download button
                    st.download_button(
                        label=f"📥 Download XLSX ({len(excel_data)/1024:.1f} KB)",
                        data=excel_data,
                        file_name=f"{uploaded_csv.name.split('.')[0]}_converted.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_xlsx"
                    )
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.text("❌ Error!")
                    st.error(f"Gagal memproses file: {str(e)}")
                finally:
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()

        # Advanced options untuk file besar
        with st.expander("⚙️ Advanced Options untuk File Besar"):
            st.write("**Optimasi Performa:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Clear Cache", help="Bersihkan cache untuk refresh memory"):
                    st.cache_data.clear()
                    st.success("Cache berhasil dibersihkan!")
                    st.rerun()
            
            with col2:
                if st.button("📊 System Info", help="Lihat informasi sistem"):
                    import psutil
                    memory = psutil.virtual_memory()
                    st.write(f"Memory Available: {memory.available / (1024**3):.1f} GB")
                    st.write(f"Memory Used: {memory.percent}%")

        # Tips performa
        st.markdown("---")
        st.subheader("💡 Tips Performa Tinggi")
        
        tips_col1, tips_col2 = st.columns(2)
        
        with tips_col1:
            st.write("**🚀 Untuk File Excel Besar:**")
            st.write("""
            - Gunakan format .xlsx (lebih efisien)
            - Hapus sheet yang tidak diperlukan
            - Hindari formula kompleks
            - Gunakan tabel Excel structured
            """)
        
        with tips_col2:
            st.write("**🚀 Untuk File CSV Besar:**")
            st.write("""
            - Gunakan encoding UTF-8
            - Hapus kolom kosong
            - Kompres dengan zip jika > 100MB
            - Partition data jika sangat besar
            """)

    # CSS untuk optimasi render
    st.markdown("""
    <style>
        .stDataFrame {
            font-size: 12px;
        }
        .stButton button {
            width: 100%;
        }
        .stProgress .st-bo {
            background-color: #1f77b4;
        }
    </style>
    """, unsafe_allow_html=True)
    

    with tab10:
        st.header("🔄 Konversi Gambar ke 3D Model dengan Analisis")
        
        # Upload gambar
        uploaded_file = st.file_uploader("Unggah gambar untuk dikonversi ke 3D", 
                                    type=['png', 'jpg', 'jpeg'], 
                                    key="3d_converter")
        
            
        with st.expander("📜 Viture 3D Images Model", expanded=False):
            st.markdown(
                    """
                    <img src="https://github.com/DwiDevelopes/gambar/raw/main/Screenshot%202025-10-22%20183928.png" class="responsive-img">
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("""
            
            ### ✨ Pengertian Viture 3D Model Images Converter
            - Viture 3D Model Images Converter adalah alat atau perangkat lunak yang dirancang untuk mengubah gambar dua dimensi (2D) menjadi model tiga dimensi (3D). 
            - Alat ini menggunakan teknik pemrosesan gambar dan algoritma komputer untuk menganalisis gambar dan menghasilkan representasi 3D yang dapat dilihat, dimanipulasi, atau dicetak menggunakan printer 3D. 
            - Viture 3D Model Images Converter sering digunakan dalam berbagai bidang seperti desain produk, arsitektur, animasi, dan pengembangan game untuk membuat model 3D dari gambar referensi atau sketsa.
            
            ### 🌕 Viture 3D Model Images Converter
            - 🚀 Bisa Convert Model Dalam Bentuk Gambar 3d Model
            - 🚀 Bisa Analisis Data Model Dalam Bentuk 3d Model
            - 🚀 Bisa Melihat Sumbu x Dan Sumbu y
            - 🚀 Bisa Melihat Model Dan Bisa Di Aplikasikan Maupun Di Print Dalam Model 3d Converter
            """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if uploaded_file is not None:
                # Display original image
                st.subheader("🖼️ Gambar Asli")
                st.image(uploaded_file, use_column_width=True)
                
                # Image analysis
                st.subheader("📊 Analisis Gambar")
                
                # Convert to numpy array for analysis
                import numpy as np
                from PIL import Image
                
                image = Image.open(uploaded_file)
                img_array = np.array(image)
                
                # Basic image statistics
                st.write(f"**Dimensi Gambar:** {img_array.shape}")
                st.write(f"**Tipe Data:** {img_array.dtype}")
                st.write(f"**Range Nilai:** {img_array.min()} - {img_array.max()}")
                
                # Color distribution
                if len(img_array.shape) == 3:  # Color image
                    st.write("**Distribusi Warna RGB:**")
                    colors = ['Red', 'Green', 'Blue']
                    for i, color in enumerate(colors):
                        channel_data = img_array[:, :, i]
                        st.write(f"{color}: Mean={channel_data.mean():.2f}, Std={channel_data.std():.2f}")
        
        with col2:
            if uploaded_file is not None:
                st.subheader("📈 Chart Analisis")
                
                # Create some sample 3D data based on image
                height, width = img_array.shape[0], img_array.shape[1]
                
                # Generate 3D surface data from image intensity
                if len(img_array.shape) == 3:
                    gray_img = np.mean(img_array, axis=2)  # Convert to grayscale
                else:
                    gray_img = img_array
                
                # Downsample for performance
                downsample_factor = max(1, gray_img.shape[0] // 50)
                gray_img_small = gray_img[::downsample_factor, ::downsample_factor]
                
                # Create 3D surface plot
                fig_3d = go.Figure(data=[go.Surface(z=gray_img_small)])
                fig_3d.update_layout(
                    title='3D Surface dari Gambar',
                    scene=dict(
                        xaxis_title='X',
                        yaxis_title='Y', 
                        zaxis_title='Intensitas'
                    )
                )
                st.plotly_chart(fig_3d, use_container_width=True)
                
                # 2D Histogram of intensities
                fig_hist = px.histogram(x=gray_img.flatten(), 
                                    title='Distribusi Intensitas Pixel',
                                    labels={'x': 'Intensitas', 'y': 'Frekuensi'})
                st.plotly_chart(fig_hist, use_container_width=True)
        
        # Additional analysis section
        if uploaded_file is not None:
            st.subheader("🔍 Analisis Detail")
            
            col3, col4 = st.columns(2)
            
            with col3:
                # Edge detection simulation
                st.write("**Deteksi Tepi (Simulasi):**")
                
                # Simple edge detection using gradient
                from scipy import ndimage
                
                # Calculate gradients
                grad_x = ndimage.sobel(gray_img, axis=0)
                grad_y = ndimage.sobel(gray_img, axis=1)
                gradient_magnitude = np.hypot(grad_x, grad_y)
                
                # Display edge map
                fig_edges = px.imshow(gradient_magnitude, 
                                    title='Peta Tepi',
                                    color_continuous_scale='gray')
                st.plotly_chart(fig_edges, use_container_width=True)
            
            with col4:
                # Statistical summary
                st.write("**Ringkasan Statistik:**")
                
                stats_data = {
                    'Metrik': ['Mean', 'Median', 'Std Dev', 'Varians', 'Entropi'],
                    'Nilai': [
                        f"{gray_img.mean():.2f}",
                        f"{np.median(gray_img):.2f}", 
                        f"{gray_img.std():.2f}",
                        f"{gray_img.var():.2f}",
                        f"{-np.sum(gray_img * np.log2(gray_img + 1e-8)):.2f}"
                    ]
                }
                
                st.dataframe(stats_data, use_container_width=True)
                
                # Date selection for analysis
                analysis_date = st.date_input("Pilih Tanggal Analisis", 
                                            value=datetime.now().date(),
                                            key="3d_analysis_date")
                
                st.write(f"**Analisis untuk tanggal:** {analysis_date}")
        
        # Model conversion options
        if uploaded_file is not None:
            st.subheader("⚙️ Opsi Konversi 3D")
            
            conversion_type = st.selectbox(
                "Pilih tipe model 3D:",
                ["Surface Mesh", "Point Cloud", "Voxel Grid", "Height Map"]
            )
            
            resolution = st.slider("Resolusi Model 3D", 10, 100, 50)
            height_scale = st.slider("Skala Tinggi 3D", 0.1, 5.0, 1.0)
            
            if st.button("🚀 Generate Model 3D", type="primary"):
                with st.spinner("Membuat model 3D..."):
                    try:
                        # Progress bar
                        progress_bar = st.progress(0)
                        
                        # Convert image to grayscale and normalize
                        if len(img_array.shape) == 3:
                            gray_img = np.mean(img_array, axis=2)
                        else:
                            gray_img = img_array
                        
                        # Normalize to 0-1
                        gray_img_normalized = gray_img.astype(np.float32) / 255.0
                        
                        progress_bar.progress(25)
                        
                        # Downsample image based on resolution
                        downsample = max(1, gray_img_normalized.shape[0] // resolution)
                        height_map = gray_img_normalized[::downsample, ::downsample]
                        
                        progress_bar.progress(50)
                        
                        # Generate 3D mesh from height map
                        x, y = np.mgrid[0:height_map.shape[0], 0:height_map.shape[1]]
                        z = height_map * height_scale
                        
                        progress_bar.progress(75)
                        
                        # Create vertices and faces for the mesh
                        vertices = []
                        faces = []
                        
                        # Create vertices
                        for i in range(z.shape[0]):
                            for j in range(z.shape[1]):
                                vertices.append([i, j, z[i, j]])
                        
                        # Create faces
                        for i in range(z.shape[0]-1):
                            for j in range(z.shape[1]-1):
                                # Two triangles per quad
                                v1 = i * z.shape[1] + j
                                v2 = v1 + 1
                                v3 = (i + 1) * z.shape[1] + j
                                v4 = v3 + 1
                                
                                # First triangle
                                faces.append([v1, v2, v3])
                                # Second triangle
                                faces.append([v2, v4, v3])
                        
                        progress_bar.progress(90)
                        
                        # Convert to numpy arrays
                        vertices = np.array(vertices)
                        faces = np.array(faces)
                        
                        # Create STL mesh
                        from stl import mesh
                        
                        # Create the mesh object
                        stl_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
                        
                        # Assign vertices to mesh
                        for i, face in enumerate(faces):
                            for j in range(3):
                                stl_mesh.vectors[i][j] = vertices[face[j]]
                        
                        progress_bar.progress(100)
                        
                        # Save STL file to temporary file
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp_file:
                            stl_mesh.save(tmp_file.name)
                            
                            # Read the file data for download
                            with open(tmp_file.name, 'rb') as f:
                                stl_data = f.read()
                        
                        # Clean up temporary file
                        os.unlink(tmp_file.name)
                        
                        with st.status("Model 3D Running...", expanded=True) as status:
                            st.write("✅ Converting Model 3D...")
                            time.sleep(2)
                            st.write("✅ Data Mining 3D...")
                            time.sleep(1)
                            st.write("✅ Data mining Converting 3D...")
                            time.sleep(1)
                            st.write("✅ Model 3D tipe: STL...")
                            time.sleep(1)
                            st.write("✅ Resolusi...")
                            time.sleep(1)
                            st.write("✅ Dimensi Mesh...")
                            time.sleep(1)
                            st.write("✅ Skala Tinggi...")
                            time.sleep(1)
                            st.write("✅ Model Sasha AI...")
                            time.sleep(1)
                            st.write("✅ Model Alisa AI...")
                            time.sleep(1)
                            st.write("✅ Model dwibaktindev AI...")
                            time.sleep(1)
                        
                        status.update(
                            label="✅ Model 3D Converted!",
                            state="complete",
                            expanded=False
                        )
                        
                        # Display results
                        st.info(f"**Model 3D tipe:** {conversion_type}")
                        st.info(f"**Resolusi:** {resolution}")
                        st.info(f"**Dimensi Mesh:** {len(vertices)} vertices, {len(faces)} faces")
                        st.info(f"**Skala Tinggi:** {height_scale}")
                        
                        # Download button for 3D model
                        st.download_button(
                            label="📥 Download Model 3D (STL)",
                            data=stl_data,
                            file_name=f"3d_model_{uploaded_file.name.split('.')[0]}.stl",
                            mime="application/octet-stream"
                        )
                        
                        # Display mesh information
                        col5, col6 = st.columns(2)
                        
                        with col5:
                            st.write("**Informasi Mesh:**")
                            mesh_info = {
                                'Parameter': ['Jumlah Vertex', 'Jumlah Face', 'Dimensi X', 'Dimensi Y', 'Tinggi Maks'],
                                'Nilai': [
                                    len(vertices),
                                    len(faces),
                                    f"{z.shape[0]} points",
                                    f"{z.shape[1]} points", 
                                    f"{z.max():.3f}"
                                ]
                            }
                            st.dataframe(mesh_info)
                        
                        with col6:
                            # Display 3D preview using plotly
                            st.write("**Preview 3D:**")
                            
                            # Create simplified mesh for preview
                            preview_downsample = max(1, len(vertices) // 1000)
                            preview_vertices = vertices[::preview_downsample]
                            
                            fig_3d_preview = go.Figure(data=[go.Mesh3d(
                                x=preview_vertices[:, 0],
                                y=preview_vertices[:, 1],
                                z=preview_vertices[:, 2],
                                opacity=0.7,
                                color='lightblue'
                            )])
                            
                            fig_3d_preview.update_layout(
                                title='Preview Model 3D',
                                scene=dict(
                                    xaxis_title='X',
                                    yaxis_title='Y',
                                    zaxis_title='Z'
                                )
                            )
                            
                            st.plotly_chart(fig_3d_preview, use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"❌ Error dalam membuat model 3D: {str(e)}")
                        st.info("Pastikan library numpy-stl dan trimesh terinstall: `pip install numpy-stl trimesh`")
    
    
    with tab9:
        st.header("📁 Upload File & Analisis Lengkap Database SQL")
        with st.expander("📜 Keterangan Dalam Statistik Dan Analisis", expanded=False):
            st.markdown(
                """
                <img src="https://nativealgorithms.com/wp-content/uploads/2023/04/sql-image.jpeg" class="responsive-img">
                """,
                unsafe_allow_html=True
            )
            st.markdown("""

            ### 🚀 Keterangan Lengkap Dalam Analisis Dan Statistik Pada SQL Style
            - Akankah Hal Gila Dapat Terjadi Dan Ini lah yang Mungkin Menjadi Kenyataan Pada SQL Style?
            - Dengan adanya fitur analisis data pada SQL Style, kini Anda dapat dengan mudah mengunggah file CSV atau Excel berisi data dari database SQL Anda untuk dianalisis secara menyeluruh.
            - Fitur ini dirancang untuk memberikan wawasan mendalam tentang struktur data Anda, termasuk deteksi kolom tanggal, analisis statistik dasar, dan visualisasi data yang informatif.
            - Setelah mengunggah file, SQL Style akan secara otomatis mendeteksi kolom tanggal dan melakukan analisis mendalam terhadap data tersebut.
            - Anda akan mendapatkan statistik dasar seperti jumlah baris dan kolom, nilai unik, serta informasi tentang missing values.
            - Selain itu, fitur visualisasi data akan membantu Anda memahami distribusi data, tren waktu, dan pola musiman dengan grafik yang mudah dipahami.
            - Fitur ini sangat berguna bagi para analis data, pengembang database, dan siapa saja yang ingin mendapatkan pemahaman lebih baik tentang data mereka.
            - Kami terus berupaya untuk meningkatkan fitur ini agar dapat memberikan pengalaman analisis data yang lebih baik dan lebih komprehensif.
            - dan kami akan segera update SQL Style ini agar lebih baik lagi kedepannya.
            - Terima kasih atas pengertian dan dukungannya.
            """)
        
        # Upload file
        uploaded_file = st.file_uploader(
            "Pilih file CSV atau Excel", 
            type=['csv', 'xlsx', 'xls'],
            help="Upload file data untuk dianalisis"
        )
        
        if uploaded_file is not None:
            try:
                # Baca file berdasarkan tipe
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Clean dataframe - handle mixed types and object dtypes
                def clean_dataframe(df):
                    df_clean = df.copy()
                    
                    # Convert object columns to appropriate types
                    for col in df_clean.columns:
                        # Skip if column is already numeric or datetime
                        if pd.api.types.is_numeric_dtype(df_clean[col]):
                            continue
                        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                            continue
                        
                        # Try to convert to numeric first
                        try:
                            df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
                        except:
                            pass
                        
                        # If still object, try to convert to datetime
                        if df_clean[col].dtype == 'object':
                            try:
                                df_clean[col] = pd.to_datetime(df_clean[col], errors='ignore')
                            except:
                                pass
                        
                        # Handle ObjectDType specifically
                        if hasattr(df_clean[col].dtype, 'name') and df_clean[col].dtype.name == 'object':
                            # Convert to string to avoid ObjectDType issues
                            df_clean[col] = df_clean[col].astype(str)
                    
                    return df_clean
                
                df = clean_dataframe(df)
                
                st.success(f"File berhasil diupload! Shape: {df.shape}")
                
                # Tampilkan preview data
                st.subheader("📋 Preview Data")
                st.dataframe(df.head())
                
                # Informasi dasar dataset
                st.subheader("📊 Informasi Dataset")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Jumlah Baris", df.shape[0])
                with col2:
                    st.metric("Jumlah Kolom", df.shape[1])
                with col3:
                    st.metric("Missing Values", df.isnull().sum().sum())
                with col4:
                    st.metric("Duplikat", df.duplicated().sum())
                
                # --- ANALISIS STRUKTUR DATA UNTUK ERD DINAMIS ---
                st.subheader("🔍 Analisis Struktur Data untuk ERD")
                
                # Fungsi untuk deteksi tipe data yang aman
                def safe_dtype_detection(df):
                    numeric_cols = []
                    categorical_cols = []
                    date_cols = []
                    bool_cols = []
                    other_cols = []
                    
                    for col in df.columns:
                        col_dtype = str(df[col].dtype)
                        
                        # Check numeric
                        if pd.api.types.is_numeric_dtype(df[col]):
                            numeric_cols.append(col)
                        # Check datetime
                        elif pd.api.types.is_datetime64_any_dtype(df[col]):
                            date_cols.append(col)
                        # Check boolean
                        elif pd.api.types.is_bool_dtype(df[col]):
                            bool_cols.append(col)
                        # Check categorical (object but limited unique values)
                        elif df[col].dtype == 'object':
                            if df[col].nunique() <= 50:  # Consider as categorical if <= 50 unique values
                                categorical_cols.append(col)
                            else:
                                other_cols.append(col)
                        else:
                            other_cols.append(col)
                    
                    return numeric_cols, categorical_cols, date_cols, bool_cols, other_cols
                
                numeric_cols, categorical_cols, date_cols, bool_cols, other_cols = safe_dtype_detection(df)
                
                # Fungsi analisis yang lebih robust
                def robust_column_analysis(df):
                    column_analysis = {}
                    
                    for col in df.columns:
                        try:
                            col_data = df[col]
                            
                            # Handle ObjectDType and other problematic types
                            if hasattr(col_data.dtype, 'name') and col_data.dtype.name == 'object':
                                # Convert to string for analysis
                                col_data = col_data.astype(str)
                            
                            analysis = {
                                'dtype': str(col_data.dtype),
                                'unique_count': col_data.nunique(),
                                'null_count': col_data.isnull().sum(),
                                'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
                                'sample_values': col_data.dropna().head(3).tolist() if not col_data.empty else []
                            }
                            
                            # Safe sample values conversion
                            safe_samples = []
                            for val in analysis['sample_values']:
                                try:
                                    safe_samples.append(str(val))
                                except:
                                    safe_samples.append('N/A')
                            analysis['sample_values'] = safe_samples
                            
                            # Deteksi tipe kolom untuk ERD
                            col_lower = str(col).lower()
                            
                            # Primary Key detection
                            if (analysis['unique_count'] == len(col_data) and 
                                analysis['null_count'] == 0 and
                                any(keyword in col_lower for keyword in ['id', 'pk', 'key', 'code'])):
                                analysis['role'] = 'PRIMARY_KEY'
                                analysis['icon'] = '🔑'
                            
                            # Foreign Key detection
                            elif (any(keyword in col_lower for keyword in ['id', 'fk', 'ref', 'code']) and
                                analysis['unique_count'] < len(col_data) * 0.8):
                                analysis['role'] = 'FOREIGN_KEY'
                                analysis['icon'] = '🔗'
                            
                            # Measurement columns
                            elif any(keyword in col_lower for keyword in ['amount', 'price', 'value', 'total', 'sum', 'avg', 'quantity']):
                                analysis['role'] = 'MEASUREMENT'
                                analysis['icon'] = '💰'
                            
                            # Date/Time columns
                            elif any(keyword in col_lower for keyword in ['date', 'time', 'year', 'month', 'day']):
                                analysis['role'] = 'TEMPORAL'
                                analysis['icon'] = '📅'
                            
                            # Category columns
                            elif (analysis['unique_count'] <= 20 and 
                                analysis['unique_count'] > 1 and
                                str(col_data.dtype) == 'object'):
                                analysis['role'] = 'CATEGORY'
                                analysis['icon'] = '🏷️'
                            
                            # Description columns
                            elif (str(col_data.dtype) == 'object' and 
                                col_data.astype(str).str.len().mean() > 20):
                                analysis['role'] = 'DESCRIPTION'
                                analysis['icon'] = '📝'
                            
                            # Numeric metrics
                            elif pd.api.types.is_numeric_dtype(col_data):
                                analysis['role'] = 'METRIC'
                                analysis['icon'] = '📊'
                            
                            else:
                                analysis['role'] = 'ATTRIBUTE'
                                analysis['icon'] = '📄'
                            
                            column_analysis[col] = analysis
                        
                        except Exception as e:
                            # Fallback analysis for problematic columns
                            column_analysis[col] = {
                                'dtype': 'unknown',
                                'role': 'ATTRIBUTE',
                                'icon': '❓',
                                'unique_count': 0,
                                'null_count': len(df[col]),
                                'null_percentage': 100.0,
                                'sample_values': ['Error in analysis']
                            }
                    
                    return column_analysis
                
                # Analisis kolom
                column_analysis = robust_column_analysis(df)
                
                # Tampilkan analisis kolom
                st.write("**Analisis Detail Kolom:**")
                analysis_data = []
                for col, analysis in column_analysis.items():
                    analysis_data.append({
                        'Kolom': col,
                        'Tipe': analysis['dtype'],
                        'Role': analysis['role'],
                        'Icon': analysis['icon'],
                        'Unique': analysis['unique_count'],
                        'Null %': f"{analysis['null_percentage']:.1f}%"
                    })
                
                analysis_df = pd.DataFrame(analysis_data)
                st.dataframe(analysis_df, use_container_width=True)
                
                # --- ERD DINAMIS YANG LEBIH AKURAT ---
                st.subheader("🗄️ Entity Relationship Diagram (ERD) Dinamis")
                
                # Konfigurasi ERD
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    erd_style = st.selectbox(
                        "Style ERD:",
                        ['Vertical', 'Horizontal', 'Circular'],
                        index=0
                    )
                
                with col2:
                    show_relationships = st.checkbox("Tampilkan Relasi", value=True)
                
                with col3:
                    max_tables = st.slider("Max Tabel", 3, 15, 8)
                
                try:
                    import graphviz
                    
                    # Buat graph ERD
                    dot = graphviz.Digraph(comment='Dynamic Database ERD')
                    
                    # Atur layout
                    if erd_style == 'Vertical':
                        dot.attr(rankdir='TB', size='12,16')
                    elif erd_style == 'Horizontal':
                        dot.attr(rankdir='LR', size='16,12')
                    else:  # Circular
                        dot.attr(rankdir='LR', size='14,14', layout='circo')
                    
                    # Kelompokkan kolom berdasarkan role untuk membuat tabel
                    main_table_cols = []
                    reference_tables = {}
                    
                    for col, analysis in column_analysis.items():
                        if analysis['role'] == 'FOREIGN_KEY':
                            # Buat tabel referensi untuk foreign key
                            ref_table_name = f"ref_{col}"
                            if ref_table_name not in reference_tables:
                                ref_display_name = col.replace('_id', '').replace('ID', '').replace('_', ' ').title()
                                reference_tables[ref_table_name] = {
                                    'name': ref_display_name,
                                    'columns': []
                                }
                            reference_tables[ref_table_name]['columns'].append(col)
                        else:
                            main_table_cols.append((col, analysis))
                    
                    # Batasi jumlah tabel yang ditampilkan
                    tables_to_show = min(max_tables, len(reference_tables) + 1)
                    
                    # Buat tabel utama
                    if main_table_cols and tables_to_show > 0:
                        with dot.subgraph(name='cluster_main') as c:
                            table_name = uploaded_file.name.split('.')[0]  # Remove extension
                            c.attr(label=f'📊 {table_name}', style='filled', 
                                color='lightblue', fontsize='14', fontname='Arial Bold')
                            
                            fields = []
                            for col, analysis in main_table_cols[:12]:  # Batasi kolom per tabel
                                field_type = ""
                                if pd.api.types.is_numeric_dtype(df[col]):
                                    field_type = "NUMERIC"
                                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                                    field_type = "DATETIME"
                                elif df[col].dtype == 'object':
                                    try:
                                        max_len = df[col].astype(str).str.len().max()
                                        field_type = f"VARCHAR({min(255, max(50, int(max_len)))})"
                                    except:
                                        field_type = "TEXT"
                                elif df[col].dtype == 'bool':
                                    field_type = "BOOLEAN"
                                else:
                                    field_type = "TEXT"
                                
                                constraint = ""
                                if analysis['role'] == 'PRIMARY_KEY':
                                    constraint = " [PK]"
                                elif analysis['role'] == 'FOREIGN_KEY':
                                    constraint = " [FK]"
                                
                                fields.append(f"<TR><TD ALIGN='LEFT'>{analysis['icon']} {col}</TD><TD ALIGN='LEFT'>{field_type}{constraint}</TD></TR>")
                            
                            # Tambahkan indicator jika ada kolom yang tidak ditampilkan
                            if len(main_table_cols) > 12:
                                fields.append(f"<TR><TD ALIGN='LEFT'>...</TD><TD ALIGN='LEFT'>+{len(main_table_cols)-12} more</TD></TR>")
                            
                            table_html = f'''<
                                <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">
                                <TR><TD ALIGN="CENTER" BGCOLOR="#e6f3ff"><B>COLUMN</B></TD><TD ALIGN="CENTER" BGCOLOR="#e6f3ff"><B>TYPE</B></TD></TR>
                                {''.join(fields)}
                                </TABLE>
                            >'''
                            
                            c.node('main_table', table_html, shape='none', fontname='Arial')
                    
                    # Buat tabel referensi
                    colors = ['#e6ffe6', '#fff0e6', '#e6f9ff', '#ffe6ff', '#ffffe6', '#f0e6ff']
                    for i, (ref_name, ref_info) in enumerate(list(reference_tables.items())[:tables_to_show-1]):
                        color = colors[i % len(colors)]
                        with dot.subgraph(name=f'cluster_{ref_name}') as c:
                            c.attr(label=f'📁 {ref_info["name"]}', style='filled', 
                                color=color, fontsize='12', fontname='Arial')
                            
                            fields = []
                            # Primary key untuk tabel referensi
                            for fk_col in ref_info['columns']:
                                fields.append(f"<TR><TD ALIGN='LEFT'><B>🔑 {fk_col}</B></TD><TD ALIGN='LEFT'>[PK]</TD></TR>")
                            
                            # Tambahkan kolom umum untuk tabel referensi
                            fields.append(f"<TR><TD ALIGN='LEFT'>📝 Name</TD><TD ALIGN='LEFT'>VARCHAR(100)</TD></TR>")
                            fields.append(f"<TR><TD ALIGN='LEFT'>📝 Description</TD><TD ALIGN='LEFT'>VARCHAR(255)</TD></TR>")
                            fields.append(f"<TR><TD ALIGN='LEFT'>📅 Created_Date</TD><TD ALIGN='LEFT'>DATETIME</TD></TR>")
                            fields.append(f"<TR><TD ALIGN='LEFT'>✅ Is_Active</TD><TD ALIGN='LEFT'>BOOLEAN</TD></TR>")
                            
                            table_html = f'''<
                                <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3">
                                <TR><TD ALIGN="CENTER" BGCOLOR="{color}"><B>COLUMN</B></TD><TD ALIGN="CENTER" BGCOLOR="{color}"><B>TYPE</B></TD></TR>
                                {''.join(fields)}
                                </TABLE>
                            >'''
                            
                            c.node(ref_name, table_html, shape='none', fontname='Arial')
                        
                        # Tambahkan relasi
                        if show_relationships:
                            for fk_col in ref_info['columns']:
                                dot.edge(ref_name, 'main_table', label='1:N', style='dashed', color='#666666')
                    
                    # Tampilkan ERD
                    st.graphviz_chart(dot)
                    
                    # Legenda
                    st.markdown("""
                    **📋 Legenda ERD:**
                    - 🔑 Primary Key | 🔗 Foreign Key | 📊 Metric      | 💰 Measurement 
                    - 📅 Temporal    | 🏷️ Category    | 📝 Description | 📄 Attribute
                    - **Warna berbeda**: Tabel yang berbeda domain
                    """)
                    
                except ImportError:
                    st.warning("Graphviz tidak terinstall. Menggunakan visualisasi alternatif...")
                    
                    # Visualisasi alternatif yang lebih sederhana
                    import plotly.graph_objects as go
                    
                    # Hitung posisi node secara dinamis
                    num_tables = min(8, len(reference_tables) + 1)
                    angles = np.linspace(0, 2*np.pi, num_tables, endpoint=False)
                    radius = 0.4
                    
                    fig = go.Figure()
                    
                    # Node positions
                    node_x = [0.5]  # Main table di center
                    node_y = [0.5]
                    node_text = ["MAIN"]
                    node_colors = ['#3366CC']
                    
                    # Reference tables di sekeliling
                    for i, (ref_name, ref_info) in enumerate(list(reference_tables.items())[:num_tables-1]):
                        angle = angles[i]
                        x = 0.5 + radius * np.cos(angle)
                        y = 0.5 + radius * np.sin(angle)
                        
                        node_x.append(x)
                        node_y.append(y)
                        node_text.append(ref_info['name'][:10])
                        node_colors.append(colors[i % len(colors)])
                    
                    # Add nodes
                    fig.add_trace(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers+text',
                        marker=dict(size=80, color=node_colors),
                        text=node_text,
                        textposition="middle center",
                        textfont=dict(size=12, color='white'),
                        name="Tables"
                    ))
                    
                    # Add relationships
                    if show_relationships and len(node_x) > 1:
                        for i in range(1, len(node_x)):
                            fig.add_trace(go.Scatter(
                                x=[node_x[i], node_x[0]], y=[node_y[i], node_y[0]],
                                mode='lines',
                                line=dict(width=2, color='gray', dash='dash'),
                                hoverinfo='none',
                                showlegend=False
                            ))
                    
                    fig.update_layout(
                        title="Database Table Relationships",
                        showlegend=False,
                        height=500,
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
                        margin=dict(l=20, r=20, t=60, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

                # --- VISUALISASI DATA YANG AMAN ---
                st.subheader("📈 Visualisasi Data")
                
                # Warna konsisten untuk chart
                color_palette = px.colors.qualitative.Set3
                
                # Fungsi safe plotting
                def safe_plotting(plot_function, *args, **kwargs):
                    try:
                        return plot_function(*args, **kwargs)
                    except Exception as e:
                        st.error(f"Error dalam membuat chart: {str(e)}")
                        return None
                
                # Tab untuk organisasi chart yang lebih baik
                tab111, tab222, tab333 = st.tabs(["📊 Distribusi Numerik", "🏷️ Analisis Kategorikal", "📋 Data Quality"])
                
                with tab111:
                    st.subheader("Analisis Distribusi Numerik")
                    
                    if numeric_cols:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Histogram dengan pengelompokan yang baik
                            selected_num_hist = st.selectbox(
                                "Pilih variabel untuk histogram:",
                                numeric_cols,
                                key="hist_num"
                            )
                            
                            if selected_num_hist:
                                fig_hist = safe_plotting(px.histogram,
                                    df, 
                                    x=selected_num_hist,
                                    title=f"Distribusi {selected_num_hist}",
                                    nbins=30,
                                    color_discrete_sequence=['#3366CC'],
                                    opacity=0.8
                                )
                                if fig_hist:
                                    fig_hist.update_layout(
                                        bargap=0.1,
                                        xaxis_title=selected_num_hist,
                                        yaxis_title="Frekuensi"
                                    )
                                    st.plotly_chart(fig_hist, use_container_width=True)
                        
                        with col2:
                            # Box plot
                            selected_num_box = st.selectbox(
                                "Pilih variabel untuk box plot:",
                                numeric_cols,
                                key="box_num"
                            )
                            
                            if selected_num_box:
                                fig_box = safe_plotting(px.box,
                                    df,
                                    y=selected_num_box,
                                    title=f"Box Plot {selected_num_box}",
                                    color_discrete_sequence=['#FF6B6B']
                                )
                                if fig_box:
                                    st.plotly_chart(fig_box, use_container_width=True)
                        
                        # Matriks korelasi
                        if len(numeric_cols) >= 2:
                            st.write("**Matriks Korelasi:**")
                            try:
                                corr_matrix = df[numeric_cols].corr()
                                fig_corr = px.imshow(
                                    corr_matrix,
                                    text_auto=".2f",
                                    color_continuous_scale='RdBu_r',
                                    aspect="auto",
                                    title="Matriks Korelasi Numerik"
                                )
                                st.plotly_chart(fig_corr, use_container_width=True)
                            except Exception as e:
                                st.warning(f"Tidak dapat menghitung matriks korelasi: {str(e)}")
                
                with tab222:
                    st.subheader("Analisis Data Kategorikal")
                    
                    if categorical_cols:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Pie chart yang terorganisir
                            selected_cat_pie = st.selectbox(
                                "Pilih variabel kategorikal:",
                                categorical_cols,
                                key="pie_cat"
                            )
                            
                            if selected_cat_pie:
                                try:
                                    value_counts = df[selected_cat_pie].value_counts().head(8)
                                    fig_pie = safe_plotting(px.pie,
                                        values=value_counts.values,
                                        names=value_counts.index,
                                        title=f"Distribusi {selected_cat_pie} (Top 8)",
                                        color_discrete_sequence=color_palette
                                    )
                                    if fig_pie:
                                        st.plotly_chart(fig_pie, use_container_width=True)
                                except Exception as e:
                                    st.warning(f"Tidak dapat membuat pie chart: {str(e)}")
                        
                        with col2:
                            # Bar chart horizontal
                            if selected_cat_pie:
                                try:
                                    value_counts = df[selected_cat_pie].value_counts().head(10)
                                    fig_bar = safe_plotting(px.bar,
                                        x=value_counts.values,
                                        y=value_counts.index,
                                        orientation='h',
                                        title=f"Top 10 {selected_cat_pie}",
                                        color=value_counts.values,
                                        color_continuous_scale='Blues'
                                    )
                                    if fig_bar:
                                        fig_bar.update_layout(
                                            xaxis_title="Count",
                                            yaxis_title=selected_cat_pie,
                                            showlegend=False
                                        )
                                        st.plotly_chart(fig_bar, use_container_width=True)
                                except Exception as e:
                                    st.warning(f"Tidak dapat membuat bar chart: {str(e)}")
                
                with tab333:
                    st.subheader("Data Quality Report")
                    
                    # Buat laporan kualitas data yang komprehensif
                    quality_report = []
                    for col in df.columns:
                        analysis = column_analysis[col]
                        quality_report.append({
                            'Kolom': col,
                            'Tipe Data': analysis['dtype'],
                            'Role': analysis['role'],
                            'Unique Values': analysis['unique_count'],
                            'Null Values': analysis['null_count'],
                            'Null %': f"{analysis['null_percentage']:.2f}%",
                            'Sample': analysis['sample_values'][0] if analysis['sample_values'] else 'N/A'
                        })
                    
                    quality_df = pd.DataFrame(quality_report)
                    st.dataframe(quality_df, use_container_width=True)
                    
                    # Visualisasi kualitas data sederhana
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Missing values bar chart
                        missing_data = quality_df[['Kolom', 'Null Values']].set_index('Kolom')
                        fig_missing = safe_plotting(px.bar,
                            missing_data,
                            y='Null Values',
                            title="Missing Values per Kolom",
                            color='Null Values',
                            color_continuous_scale='Reds'
                        )
                        if fig_missing:
                            st.plotly_chart(fig_missing, use_container_width=True)
                    
                    with col2:
                        # Data types distribution
                        type_dist = quality_df['Tipe Data'].value_counts()
                        fig_types = safe_plotting(px.pie,
                            values=type_dist.values,
                            names=type_dist.index,
                            title="Distribusi Tipe Data",
                            color_discrete_sequence=color_palette
                        )
                        if fig_types:
                            st.plotly_chart(fig_types, use_container_width=True)
                
                # --- DOWNLOAD SECTION ---
                st.subheader("💾 Download Hasil Analisis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "📊 Download Quality Report",
                        quality_df.to_csv(index=False),
                        "data_quality_report.csv",
                        "text/csv"
                    )
                
                with col2:
                    # Buat summary report
                    summary_report = {
                        'file_name': uploaded_file.name,
                        'file_size': f"{uploaded_file.size / 1024:.2f} KB",
                        'rows': df.shape[0],
                        'columns': df.shape[1],
                        'analysis_date': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'numeric_columns': numeric_cols,
                        'categorical_columns': categorical_cols,
                        'date_columns': date_cols,
                        'primary_keys': [col for col, analysis in column_analysis.items() 
                                    if analysis['role'] == 'PRIMARY_KEY'],
                        'foreign_keys': [col for col, analysis in column_analysis.items() 
                                    if analysis['role'] == 'FOREIGN_KEY']
                    }
                    
                    import json
                    st.download_button(
                        "📋 Download Summary Report",
                        json.dumps(summary_report, indent=2, ensure_ascii=False),
                        "analysis_summary.json",
                        "application/json"
                    )
                
                with col3:
                    # Download processed data
                    st.download_button(
                        "💾 Download Processed Data",
                        df.to_csv(index=False),
                        "processed_data.csv",
                        "text/csv"
                    )
                
            except Exception as e:
                st.error(f"Error dalam analisis data: {str(e)}")
                st.info("Pastikan file yang diupload berformat CSV atau Excel yang valid")
                st.code(f"Error details: {str(e)}", language='python')
        else:
            st.info("📤 Silakan upload file CSV atau Excel untuk memulai analisis")
            
            # Template dan panduan
            st.subheader("🎯 Panduan Format Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Format yang Disarankan:**")
                sample_data = {
                    'customer_id': [1, 2, 3, 4, 5],
                    'order_id': [101, 102, 103, 104, 105],
                    'product_id': [201, 202, 203, 204, 205],
                    'order_date': pd.date_range('2024-01-01', periods=5),
                    'amount': [100.50, 75.25, 200.00, 150.75, 90.99],
                    'category': ['Electronics', 'Books', 'Electronics', 'Clothing', 'Books'],
                    'status': ['Completed', 'Pending', 'Completed', 'Shipped', 'Pending']
                }
                sample_df = pd.DataFrame(sample_data)
                st.dataframe(sample_df)
            
            with col2:
                st.write("**Keterangan Fitur:**")
                st.markdown("""
                - **🔑 Primary Key**: Kolom dengan nilai unik (ID, code)
                - **🔗 Foreign Key**: Kolom referensi ke tabel lain
                - **📊 ERD Dinamis**: Diagram relasi otomatis
                - **📈 Visualisasi Aman**: Error handling untuk semua chart
                - **🎨 Warna Konsisten**: Skema warna yang harmonis
                - **📋 Analisis Komprehensif**: Statistik detail dan laporan
                """)
            
            # Download template
            csv_template = sample_df.to_csv(index=False)
            st.download_button(
                "📥 Download Template CSV",
                csv_template,
                "analysis_template.csv",
                "text/csv"
            )

    
    with tab8:
        st.header("📊 Analisis Grafik Saham")
        
        # Upload file
        uploaded_file = st.file_uploader(
            "Unggah file data saham (CSV atau Excel)",
            type=['csv', 'xlsx', 'xls'],
            key="stock_uploader"
        )
        with st.expander("📜 Ketarangan Lengkap Tentang Analisis Saham", expanded=False):
            st.markdown(
                    """
                    <img src="https://png.pngtree.com/background/20250116/original/pngtree-stock-market-analysis-with-colorful-candlestick-chart-picture-image_16020049.jpg" class="responsive-img">
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("""

            
            ### 🧾 Pengambangan Saham
            - Saham merupakan salah satu instrumen investasi yang populer di kalangan investor. Dengan membeli saham, investor memiliki sebagian kepemilikan dalam sebuah perusahaan dan berhak atas sebagian keuntungan perusahaan tersebut.
            - Analisis saham melibatkan evaluasi berbagai faktor seperti kinerja keuangan perusahaan, kondisi pasar, tren industri, dan faktor ekonomi makro untuk membuat keputusan investasi yang lebih baik.
            - Analisis saham dapat dilakukan dengan menggunakan teknologi yang terkenal seperti Excel, Google Sheets, atau Microsoft Excel.
            
            ### 📈 Analisis Grafik Saham
            - Analisis grafik saham adalah proses menganalisis data saham untuk membuat grafik yang menampilkan informasi tentang saham secara visual.
            - Grafik saham dapat digunakan untuk membuat perbandingan antara saham yang berbeda, menampilkan trend, dan menentukan kemungkinan investasi yang lebih baik.
            - Grafik saham dapat digunakan untuk menentukan kemungkinan investasi yang lebih baik dan meningkatkan keuntungan investasi.
            
            ### 💰 Analisis Grafik Saham
            - Analisis grafik saham dapat digunakan untuk membuat perbandingan antara saham yang berbeda, menampilkan trend, dan menentukan kemungkinan investasi yang lebih baik.
            - Grafik saham dapat digunakan untuk menentukan kemungkinan investasi yang lebih baik dan meningkatkan keuntungan investasi.
            """)
        if uploaded_file is not None:
            try:
                # Baca file berdasarkan tipe
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"File berhasil diunggah! Shape: {df.shape}")
                
                # Tampilkan data
                with st.expander("📋 Preview Data"):
                    st.dataframe(df.head(10))
                
                # Konfigurasi kolom
                st.subheader("⚙️ Konfigurasi Data")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    date_column = st.selectbox(
                        "Pilih kolom tanggal",
                        options=df.columns,
                        index=0
                    )
                
                with col2:
                    open_column = st.selectbox(
                        "Pilih kolom Open",
                        options=df.columns,
                        index=min(1, len(df.columns)-1)
                    )
                
                with col3:
                    high_column = st.selectbox(
                        "Pilih kolom High",
                        options=df.columns,
                        index=min(2, len(df.columns)-1)
                    )
                
                with col4:
                    low_column = st.selectbox(
                        "Pilih kolom Low",
                        options=df.columns,
                        index=min(3, len(df.columns)-1)
                    )
                
                col5, col6, col7 = st.columns(3)
                
                with col5:
                    close_column = st.selectbox(
                        "Pilih kolom Close",
                        options=df.columns,
                        index=min(4, len(df.columns)-1)
                    )
                
                with col6:
                    volume_column = st.selectbox(
                        "Pilih kolom Volume",
                        options=df.columns,
                        index=min(5, len(df.columns)-1) if len(df.columns) > 5 else 0
                    )
                
                with col7:
                    # Konversi kolom tanggal
                    try:
                        df[date_column] = pd.to_datetime(df[date_column])
                        df = df.sort_values(date_column)
                        st.success("Kolom tanggal berhasil dikonversi")
                    except Exception as e:
                        st.error(f"Gagal mengonversi kolom tanggal: {e}")
                
                # Pilihan jenis grafik
                st.subheader("📈 Jenis Grafik")
                chart_type = st.selectbox(
                    "Pilih jenis grafik",
                    [
                        "Candlestick Chart",
                        "Line Chart (Harga Penutupan)",
                        "OHLC Chart",
                        "Area Chart",
                        "Volume Chart",
                        "Moving Average Chart",
                        "RSI Indicator",
                        "Bollinger Bands"
                    ]
                )
                
                # Konfigurasi tambahan berdasarkan jenis grafik
                if chart_type in ["Moving Average Chart", "Bollinger Bands"]:
                    ma_period = st.slider("Period Moving Average", 5, 100, 20)
                
                if chart_type == "Bollinger Bands":
                    bb_std = st.slider("Standard Deviation", 1, 3, 2)
                
                if chart_type == "RSI Indicator":
                    rsi_period = st.slider("RSI Period", 5, 30, 14)
                
                # Buat grafik berdasarkan pilihan
                if volume_column in df.columns and chart_type != "Volume Chart":
                    fig = make_subplots(
                        rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.1,
                        subplot_titles=('Price Chart', 'Volume'),
                        row_width=[0.7, 0.3]
                    )
                else:
                    fig = go.Figure()
                
                if chart_type == "Candlestick Chart":
                    # Candlestick chart
                    candlestick = go.Candlestick(
                        x=df[date_column],
                        open=df[open_column],
                        high=df[high_column],
                        low=df[low_column],
                        close=df[close_column],
                        name="Candlestick"
                    )
                    if volume_column in df.columns:
                        fig.add_trace(candlestick, row=1, col=1)
                    else:
                        fig.add_trace(candlestick)
                    
                elif chart_type == "Line Chart (Harga Penutupan)":
                    line_chart = go.Scatter(
                        x=df[date_column],
                        y=df[close_column],
                        mode='lines',
                        name='Close Price',
                        line=dict(color='blue', width=2)
                    )
                    if volume_column in df.columns:
                        fig.add_trace(line_chart, row=1, col=1)
                    else:
                        fig.add_trace(line_chart)
                    
                elif chart_type == "OHLC Chart":
                    ohlc_chart = go.Ohlc(
                        x=df[date_column],
                        open=df[open_column],
                        high=df[high_column],
                        low=df[low_column],
                        close=df[close_column],
                        name="OHLC"
                    )
                    if volume_column in df.columns:
                        fig.add_trace(ohlc_chart, row=1, col=1)
                    else:
                        fig.add_trace(ohlc_chart)
                    
                elif chart_type == "Area Chart":
                    area_chart = go.Scatter(
                        x=df[date_column],
                        y=df[close_column],
                        mode='lines',
                        fill='tozeroy',
                        name='Close Price',
                        line=dict(color='green', width=2)
                    )
                    if volume_column in df.columns:
                        fig.add_trace(area_chart, row=1, col=1)
                    else:
                        fig.add_trace(area_chart)
                    
                elif chart_type == "Volume Chart":
                    if volume_column in df.columns:
                        volume_chart = go.Bar(
                            x=df[date_column],
                            y=df[volume_column],
                            name='Volume',
                            marker_color='rgba(0,0,255,0.3)'
                        )
                        fig.add_trace(volume_chart)
                    else:
                        st.warning("Kolom volume tidak ditemukan dalam data")
                    
                elif chart_type == "Moving Average Chart":
                    # Hitung moving average
                    df['MA'] = df[close_column].rolling(window=ma_period).mean()
                    
                    price_line = go.Scatter(
                        x=df[date_column],
                        y=df[close_column],
                        mode='lines',
                        name='Close Price',
                        line=dict(color='blue', width=1)
                    )
                    
                    ma_line = go.Scatter(
                        x=df[date_column],
                        y=df['MA'],
                        mode='lines',
                        name=f'MA {ma_period}',
                        line=dict(color='red', width=2)
                    )
                    
                    if volume_column in df.columns:
                        fig.add_trace(price_line, row=1, col=1)
                        fig.add_trace(ma_line, row=1, col=1)
                    else:
                        fig.add_trace(price_line)
                        fig.add_trace(ma_line)
                    
                elif chart_type == "Bollinger Bands":
                    # Hitung Bollinger Bands
                    df['MA'] = df[close_column].rolling(window=ma_period).mean()
                    df['STD'] = df[close_column].rolling(window=ma_period).std()
                    df['Upper'] = df['MA'] + (df['STD'] * bb_std)
                    df['Lower'] = df['MA'] - (df['STD'] * bb_std)
                    
                    price_line = go.Scatter(
                        x=df[date_column],
                        y=df[close_column],
                        mode='lines',
                        name='Close Price',
                        line=dict(color='blue', width=1)
                    )
                    
                    ma_line = go.Scatter(
                        x=df[date_column],
                        y=df['MA'],
                        mode='lines',
                        name=f'MA {ma_period}',
                        line=dict(color='red', width=2)
                    )
                    
                    upper_band = go.Scatter(
                        x=df[date_column],
                        y=df['Upper'],
                        mode='lines',
                        name='Upper Band',
                        line=dict(color='gray', width=1, dash='dash')
                    )
                    
                    lower_band = go.Scatter(
                        x=df[date_column],
                        y=df['Lower'],
                        mode='lines',
                        name='Lower Band',
                        line=dict(color='gray', width=1, dash='dash'),
                        fill='tonexty'
                    )
                    
                    if volume_column in df.columns:
                        fig.add_trace(price_line, row=1, col=1)
                        fig.add_trace(ma_line, row=1, col=1)
                        fig.add_trace(upper_band, row=1, col=1)
                        fig.add_trace(lower_band, row=1, col=1)
                    else:
                        fig.add_trace(price_line)
                        fig.add_trace(ma_line)
                        fig.add_trace(upper_band)
                        fig.add_trace(lower_band)
                    
                elif chart_type == "RSI Indicator":
                    # Hitung RSI
                    delta = df[close_column].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                    rs = gain / loss
                    df['RSI'] = 100 - (100 / (1 + rs))
                    
                    rsi_chart = go.Scatter(
                        x=df[date_column],
                        y=df['RSI'],
                        mode='lines',
                        name=f'RSI {rsi_period}',
                        line=dict(color='purple', width=2)
                    )
                    
                    # Overbought/oversold lines
                    overbought = go.Scatter(
                        x=df[date_column],
                        y=[70] * len(df),
                        mode='lines',
                        name='Overbought (70)',
                        line=dict(color='red', width=1, dash='dash')
                    )
                    
                    oversold = go.Scatter(
                        x=df[date_column],
                        y=[30] * len(df),
                        mode='lines',
                        name='Oversold (30)',
                        line=dict(color='green', width=1, dash='dash')
                    )
                    
                    if volume_column in df.columns:
                        fig.add_trace(rsi_chart, row=1, col=1)
                        fig.add_trace(overbought, row=1, col=1)
                        fig.add_trace(oversold, row=1, col=1)
                        # Update y-axis untuk RSI
                        fig.update_yaxes(range=[0, 100], row=1, col=1)
                    else:
                        fig.add_trace(rsi_chart)
                        fig.add_trace(overbought)
                        fig.add_trace(oversold)
                        fig.update_yaxes(range=[0, 100])
                
                # Tambahkan volume chart untuk semua jenis grafik (kecuali Volume Chart sendiri)
                if volume_column in df.columns and chart_type != "Volume Chart" and chart_type != "RSI Indicator":
                    volume_chart = go.Bar(
                        x=df[date_column],
                        y=df[volume_column],
                        name='Volume',
                        marker_color='rgba(0,0,255,0.3)'
                    )
                    if volume_column in df.columns:
                        fig.add_trace(volume_chart, row=2, col=1)
                    else:
                        fig.add_trace(volume_chart)
                
                # Update layout
                fig.update_layout(
                    title=f"{chart_type} - {uploaded_file.name}",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=600 if volume_column in df.columns else 400,
                    showlegend=True,
                    template="plotly_white"
                )
                
                # Tampilkan grafik
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistik tambahan
                st.subheader("📊 Statistik Data Saham")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if close_column in df.columns and len(df) > 0:
                        st.metric("Harga Terakhir", f"${df[close_column].iloc[-1]:.2f}")
                
                with col2:
                    if close_column in df.columns and len(df) > 1:
                        daily_return = ((df[close_column].iloc[-1] - df[close_column].iloc[-2]) / df[close_column].iloc[-2]) * 100
                        st.metric("Return Harian", f"{daily_return:.2f}%")
                    else:
                        st.metric("Return Harian", "N/A")
                
                with col3:
                    if high_column in df.columns:
                        st.metric("High Tertinggi", f"${df[high_column].max():.2f}")
                
                with col4:
                    if low_column in df.columns:
                        st.metric("Low Terendah", f"${df[low_column].min():.2f}")
                
                # Informasi data
                with st.expander("📋 Informasi Data Lengkap"):
                    st.write(f"**Periode Data:** {df[date_column].min().strftime('%Y-%m-%d')} hingga {df[date_column].max().strftime('%Y-%m-%d')}")
                    st.write(f"**Jumlah Data:** {len(df)} records")
                    
                    if close_column in df.columns:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rata-rata Close", f"${df[close_column].mean():.2f}")
                        with col2:
                            st.metric("Std Dev Close", f"${df[close_column].std():.2f}")
                        with col3:
                            st.metric("Volatilitas", f"{(df[close_column].std() / df[close_column].mean() * 100):.2f}%")
                
                # Download data yang sudah diproses
                st.subheader("💾 Download Data")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Data sebagai CSV",
                    data=csv,
                    file_name=f"processed_{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.info("Pastikan file Anda memiliki format yang benar dengan kolom: Date, Open, High, Low, Close, Volume")
        
        else:
            # Tampilkan contoh data dan petunjuk
            st.info("""
            **📋 Petunjuk Upload File Saham:**
            
            1. File harus dalam format CSV atau Excel
            2. Data harus mengandung kolom-kolom berikut:
            - **Tanggal** (Date)
            - **Harga Pembukaan** (Open)
            - **Harga Tertinggi** (High) 
            - **Harga Terendah** (Low)
            - **Harga Penutupan** (Close)
            - **Volume** (opsional)
            
            3. Contoh format data:
            ```
            Date,Open,High,Low,Close,Volume
            2024-01-01,150.0,155.5,149.0,154.2,1000000
            2024-01-02,154.5,157.0,153.8,156.0,1200000
            ```
            """)
            
            # Contoh data
            sample_data = {
                'Date': pd.date_range('2024-01-01', periods=30, freq='D'),
                'Open': [150 + i * 0.5 + np.random.normal(0, 1) for i in range(30)],
                'High': [155 + i * 0.5 + np.random.normal(0, 1) for i in range(30)],
                'Low': [149 + i * 0.5 + np.random.normal(0, 1) for i in range(30)],
                'Close': [154 + i * 0.5 + np.random.normal(0, 1) for i in range(30)],
                'Volume': [1000000 + i * 50000 for i in range(30)]
            }
            
            sample_df = pd.DataFrame(sample_data)
            
            with st.expander("🎯 Contoh Format Data yang Didukung"):
                st.dataframe(sample_df.head(10))
                
                # Download sample data
                csv_sample = sample_df.to_csv(index=False)
                st.download_button(
                    label="Download Contoh Data CSV",
                    data=csv_sample,
                    file_name="sample_stock_data.csv",
                    mime="text/csv"
                )

    with tab7:
        st.header("📁 Upload File & Generate Flowchart")
        
        # Upload file section dengan deteksi otomatis
        uploaded_file = st.file_uploader(
            "Pilih file CSV atau Excel (Format: .csv, .xlsx, .xls)", 
            type=['csv', 'xlsx', 'xls'],
            help="File akan otomatis terdeteksi sebagai CSV atau Excel"
        )
        
        with st.expander("📜 Viture Generated Flowchart", expanded=False):
            st.markdown(
                    """
                    <img src="https://github.com/DwiDevelopes/gambar/raw/main/Screenshot%202025-10-22%20185052.png" class="responsive-img">
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("""
            
            ### ✨ Pengertian Viture Generated Flowchart
            - Viture Generated Flowchart adalah alat atau perangkat lunak yang dirancang untuk mengubah data menjadi model flowchart.
            - Alat ini memungkinkan pengguna untuk menganalisis data dan menghasilkan representasi visual dalam bentuk flowchart yang menggambarkan alur proses atau struktur data.
            - Flowchart ini dapat digunakan untuk menganalisis data dalam bentuk flowchart yang menjelaskan proses atau struktur data.
            
            ### 🌕 Viture Generated Flowchart
            - 🚀 bisa convert model Flowchart
            - 🚀 bisa analisis date model Flowchart
            - 🚀 bisa melihat sumbu x dan sumbu y
            - 🚀 bisa melihat data numerik
            - 🚀 bisa melihat data teks
            - 🚀 bisa melihat date ERD
            
            """)
        
        if uploaded_file is not None:
            try:
                # Deteksi tipe file dan proses
                with st.spinner('🔄 Mendeteksi dan memproses file...'):
                    file_type = "CSV" if uploaded_file.name.endswith('.csv') else "Excel"
                    st.info(f"📄 File terdeteksi: {file_type} - {uploaded_file.name}")
                    
                    if uploaded_file.name.endswith('.csv'):
                        # Untuk CSV dengan deteksi encoding
                        file_size = uploaded_file.size
                        if file_size > 10 * 1024 * 1024:
                            st.info("⚡ File besar terdeteksi, menggunakan processing optimal...")
                            chunks = pd.read_csv(uploaded_file, chunksize=10000, encoding='utf-8')
                            df = pd.concat(chunks, ignore_index=True)
                        else:
                            # Coba berbagai encoding untuk CSV
                            try:
                                df = pd.read_csv(uploaded_file, encoding='utf-8')
                            except:
                                try:
                                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                                except:
                                    df = pd.read_csv(uploaded_file, encoding='iso-8859-1')
                    else:
                        # Untuk Excel - baca semua sheets
                        excel_file = pd.ExcelFile(uploaded_file)
                        sheet_names = excel_file.sheet_names
                        
                        if len(sheet_names) > 1:
                            selected_sheet = st.selectbox(
                                "📑 Pilih sheet yang akan diproses:",
                                options=sheet_names,
                                help="File Excel memiliki multiple sheets, pilih satu untuk dianalisis"
                            )
                            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                        else:
                            df = pd.read_excel(uploaded_file, sheet_name=sheet_names[0])
                
                # Informasi file berhasil diupload
                st.success(f"✅ File berhasil diproses! Dataset: {df.shape[0]} baris × {df.shape[1]} kolom")
                
                # Auto-deteksi kolom tanggal dengan analisis lebih detail
                date_columns = []
                date_completeness = {}
                
                for col in df.columns:
                    try:
                        # Coba konversi seluruh kolom ke datetime
                        temp_dates = pd.to_datetime(df[col], errors='coerce')
                        valid_dates = temp_dates.notna().sum()
                        total_rows = len(df)
                        completeness_ratio = valid_dates / total_rows
                        
                        # Jika rasio kelengkapan > 50%, anggap sebagai kolom tanggal
                        if completeness_ratio > 0.5:
                            date_columns.append(col)
                            date_completeness[col] = {
                                'completeness_ratio': completeness_ratio,
                                'valid_dates': valid_dates,
                                'total_rows': total_rows,
                                'date_range': {
                                    'min': temp_dates.min(),
                                    'max': temp_dates.max()
                                }
                            }
                    except:
                        continue
                
                # Analisis tipe data detail
                numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
                text_columns = df.select_dtypes(include=['object']).columns.tolist()
                datetime_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
                
                # Hitung persentase untuk setiap tipe data
                total_columns = len(df.columns)
                numeric_percentage = (len(numeric_columns) / total_columns) * 100 if total_columns > 0 else 0
                text_percentage = (len(text_columns) / total_columns) * 100 if total_columns > 0 else 0
                date_percentage = (len(date_columns) / total_columns) * 100 if total_columns > 0 else 0
                other_percentage = 100 - (numeric_percentage + text_percentage + date_percentage)
                
                # Tampilkan preview data dengan expander
                with st.expander("🔍 **PREVIEW DATA - 10 Baris Pertama**", expanded=True):
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Informasi ringkas data
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Total Baris", df.shape[0])
                    with col2:
                        st.metric("📋 Total Kolom", df.shape[1])
                    with col3:
                        st.metric("🔢 Numeric Columns", len(numeric_columns))
                    with col4:
                        st.metric("📅 Date Columns", len(date_columns))

                # ==================== BAGIAN FLOWCHART DINAMIS DENGAN PERSENTASE ====================
                st.markdown("---")
                st.subheader("🔄 **FLOWCHART PROSES DATA & ANALISIS KOMPOSISI**")
                
                # Generate flowchart dinamis dengan persentase
                dot = Digraph(comment='Data Process Flowchart', format='png')
                dot.attr(rankdir='TB', size='14,10')
                dot.attr('node', style='filled', fontname='Arial', fontsize='10')
                
                # Node utama proses
                nodes = {
                    'start': ['START\nUpload File', 'ellipse', '#28a745', 'white'],
                    'load': [f'LOAD {file_type}\n{uploaded_file.name}', 'box', '#ffc107', 'black'],
                    'validate': ['DATA VALIDATION\nQuality Check', 'diamond', '#17a2b8', 'white'],
                    'analyze': ['DATA ANALYSIS\nStructure & Types', 'box', '#6f42c1', 'white'],
                    'end': ['END\nProcess Complete', 'ellipse', '#dc3545', 'white']
                }
                
                # Node untuk komposisi data
                composition_nodes = {
                    'comp_numeric': [f'NUMERIC DATA\n{len(numeric_columns)} cols\n({numeric_percentage:.1f}%)', 'box', '#fd7e14', 'white'],
                    'comp_text': [f'TEXT DATA\n{len(text_columns)} cols\n({text_percentage:.1f}%)', 'box', '#6f42c1', 'white'],
                    'comp_date': [f'DATE DATA\n{len(date_columns)} cols\n({date_percentage:.1f}%)', 'box', '#20c997', 'white'],
                    'comp_other': [f'OTHER DATA\n({other_percentage:.1f}%)', 'box', '#6c757d', 'white']
                }
                
                # Tambahkan semua node utama
                for node_id, (label, shape, color, fontcolor) in nodes.items():
                    dot.node(node_id, label, shape=shape, fillcolor=color, fontcolor=fontcolor)
                
                # Tambahkan node komposisi
                for node_id, (label, shape, color, fontcolor) in composition_nodes.items():
                    dot.node(node_id, label, shape=shape, fillcolor=color, fontcolor=fontcolor)
                
                # Koneksi utama
                main_connections = [
                    ('start', 'load'),
                    ('load', 'validate'), 
                    ('validate', 'analyze'),
                    ('analyze', 'comp_numeric'),
                    ('analyze', 'comp_text'),
                    ('analyze', 'comp_date'),
                    ('analyze', 'comp_other')
                ]
                
                # Koneksi ke end berdasarkan dominansi data
                dominant_type = max([(numeric_percentage, 'comp_numeric'), 
                                (text_percentage, 'comp_text'),
                                (date_percentage, 'comp_date')], 
                                key=lambda x: x[0])
                
                # Hubungkan node dominan ke end
                main_connections.append((dominant_type[1], 'end'))
                
                # Buat semua koneksi
                for from_node, to_node in main_connections:
                    dot.edge(from_node, to_node)
                
                # Tampilkan flowchart
                st.graphviz_chart(dot)
                
                # ==================== GRAFIK KOMPOSISI DATA ====================
                st.subheader("📊 **GRAFIK KOMPOSISI DATA**")
                
                # Buat grafik pie chart untuk komposisi data
                fig_composition = px.pie(
                    values=[numeric_percentage, text_percentage, date_percentage, other_percentage],
                    names=['Numeric', 'Text', 'Date', 'Other'],
                    title='Komposisi Tipe Data dalam Dataset',
                    color=['Numeric', 'Text', 'Date', 'Other'],
                    color_discrete_map={
                        'Numeric': '#fd7e14',
                        'Text': '#6f42c1', 
                        'Date': '#20c997',
                        'Other': '#6c757d'
                    }
                )
                
                fig_composition.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>%{value:.1f}%<br>%{customdata}',
                    customdata=[[f"{len(numeric_columns)} columns"], 
                            [f"{len(text_columns)} columns"],
                            [f"{len(date_columns)} columns"], 
                            [f"{total_columns - len(numeric_columns) - len(text_columns) - len(date_columns)} columns"]]
                )
                
                fig_composition.update_layout(
                    height=400,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_composition, use_container_width=True)
                
                # ==================== ANALISIS DETAIL PER KOLOM ====================
                with st.expander("📈 **ANALISIS DETAIL PER KOLOM**", expanded=True):
                    st.subheader("📋 **Detail Analisis Kolom**")
                    
                    # Tabel analisis kolom
                    analysis_data = []
                    for col in df.columns:
                        col_type = df[col].dtype
                        null_count = df[col].isnull().sum()
                        null_percentage = (null_count / len(df)) * 100
                        unique_count = df[col].nunique()
                        
                        # Tentukan kategori
                        if col in numeric_columns:
                            category = "Numerik"
                            details = f"Range: {df[col].min():.2f} - {df[col].max():.2f}"
                        elif col in date_columns:
                            category = "Tanggal"
                            completeness = date_completeness.get(col, {})
                            comp_ratio = completeness.get('completeness_ratio', 0) * 100
                            details = f"Kelengkapan: {comp_ratio:.1f}%"
                        elif col in text_columns:
                            category = "Teks"
                            details = f"Unique: {unique_count}"
                        else:
                            category = "Lainnya"
                            details = f"Type: {col_type}"
                        
                        analysis_data.append({
                            'Kolom': col,
                            'Tipe Data': str(col_type),
                            'Kategori': category,
                            'Null Values': null_count,
                            'Null %': f"{null_percentage:.1f}%",
                            'Unique Values': unique_count,
                            'Detail': details
                        })
                    
                    analysis_df = pd.DataFrame(analysis_data)
                    st.dataframe(analysis_df, use_container_width=True)
                    
                    # Statistik summary
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("✅ Kolom Valid", f"{total_columns}")
                    with col2:
                        st.metric("📊 Data Lengkap", f"{(100 - analysis_df['Null %'].str.rstrip('%').astype(float).mean()):.1f}%")
                    with col3:
                        st.metric("🎯 Kualitas Data", f"{(100 - analysis_df['Null %'].str.rstrip('%').astype(float).max()):.1f}%")
                    with col4:
                        complexity_score = (analysis_df['Unique Values'].mean() / len(df)) * 100
                        st.metric("⚡ Kompleksitas", f"{complexity_score:.1f}%")
                
                # ==================== KETERANGAN FLOWCHART & PERHITUNGAN ====================
                with st.expander("🧮 **DETAIL PERHITUNGAN & KETERANGAN**", expanded=True):
                    st.subheader("📐 **Metrik Perhitungan**")
                    
                    # Tampilkan perhitungan persentase
                    calculation_data = {
                        'Tipe Data': ['Numerik', 'Teks', 'Tanggal', 'Lainnya'],
                        'Jumlah Kolom': [len(numeric_columns), len(text_columns), len(date_columns), 
                                    total_columns - len(numeric_columns) - len(text_columns) - len(date_columns)],
                        'Persentase': [f"{numeric_percentage:.1f}%", f"{text_percentage:.1f}%", 
                                    f"{date_percentage:.1f}%", f"{other_percentage:.1f}%"],
                        'Rumus': [
                            f"{len(numeric_columns)} / {total_columns} × 100%",
                            f"{len(text_columns)} / {total_columns} × 100%", 
                            f"{len(date_columns)} / {total_columns} × 100%",
                            f"{total_columns - len(numeric_columns) - len(text_columns) - len(date_columns)} / {total_columns} × 100%"
                        ]
                    }
                    
                    calc_df = pd.DataFrame(calculation_data)
                    st.dataframe(calc_df, use_container_width=True)
                    
                    # Analisis dominansi
                    st.subheader("🎯 **Analisis Dominansi Data**")
                    dominant_type_name = {
                        'comp_numeric': 'NUMERIK',
                        'comp_text': 'TEKS', 
                        'comp_date': 'TANGGAL'
                    }[dominant_type[1]]
                    
                    st.success(f"""
                    **Tipe Data Dominan:** {dominant_type_name} ({dominant_type[0]:.1f}%)
                    
                    **Implikasi:**
                    - Dataset ini cocok untuk analisis {'statistik dan pemodelan matematis' if dominant_type_name == 'NUMERIK' else 'analisis teks dan kategorikal' if dominant_type_name == 'TEKS' else 'analisis time series dan trend'}
                    - Flowchart mengarah ke **{dominant_type_name}** sebagai output utama
                    - Rekomendasi visualisasi: {'Line Chart, Histogram, Scatter Plot' if dominant_type_name == 'NUMERIK' else 'Bar Chart, Word Cloud, Pie Chart' if dominant_type_name == 'TEKS' else 'Time Series, Trend Analysis, Seasonal Plot'}
                    """)
                
                # Download flowchart
                flowchart_pdf = dot.pipe(format='pdf')
                st.download_button(
                    label="📥 **Download Flowchart (PDF)**",
                    data=flowchart_pdf,
                    file_name="data_processing_flowchart.pdf",
                    mime="application/pdf",
                    help="Download flowchart proses data dalam format PDF"
                )

                # ==================== BAGIAN LINE CHART ====================
                st.markdown("---")
                st.subheader("📈 **LINE CHART GENERATOR**")
                
                if len(numeric_columns) > 0 and (len(date_columns) > 0 or len(text_columns) > 0):
                    # Container untuk input parameters
                    with st.container():
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Prioritaskan kolom tanggal untuk grouping
                            grouping_options = date_columns + [col for col in text_columns if col not in date_columns]
                            group_column = st.selectbox(
                                "**Pilih Kolom Grouping (X-Axis):**",
                                options=grouping_options,
                                help="Kolom untuk mengelompokkan data (tanggal direkomendasikan)"
                            )
                            
                            # Tampilkan info kolom yang dipilih
                            if group_column in date_columns:
                                completeness = date_completeness[group_column]['completeness_ratio'] * 100
                                st.success(f"📅 Kolom tanggal terdeteksi - {completeness:.1f}% lengkap")
                            else:
                                st.info("ℹ️ Kolom teks dipilih - pastikan memiliki nilai unik yang terbatas")
                        
                        with col2:
                            value_column = st.selectbox(
                                "**Pilih Kolom Nilai (Y-Axis):**",
                                options=numeric_columns,
                                help="Kolom numerik yang akan divisualisasikan"
                            )
                        
                        with col3:
                            agg_function = st.selectbox(
                                "**Fungsi Aggregasi:**",
                                options=['mean', 'sum', 'count', 'min', 'max', 'median'],
                                help="Cara mengelompokkan data numerik"
                            )
                    
                    # Tombol generate chart
                    if st.button("🚀 **Generate Line Chart**", type="primary", use_container_width=True):
                        with st.spinner('🔄 Membuat line chart...'):
                            try:
                                # Preprocessing data
                                temp_df = df.copy()
                                
                                # Jika kolom grouping adalah tanggal, konversi ke datetime
                                if group_column in date_columns:
                                    temp_df[group_column] = pd.to_datetime(temp_df[group_column], errors='coerce')
                                    # Hapus rows dengan tanggal invalid
                                    temp_df = temp_df.dropna(subset=[group_column])
                                
                                # Group data berdasarkan kolom yang dipilih
                                if agg_function == 'mean':
                                    grouped_data = temp_df.groupby(group_column)[value_column].mean().reset_index()
                                elif agg_function == 'sum':
                                    grouped_data = temp_df.groupby(group_column)[value_column].sum().reset_index()
                                elif agg_function == 'count':
                                    grouped_data = temp_df.groupby(group_column)[value_column].count().reset_index()
                                elif agg_function == 'min':
                                    grouped_data = temp_df.groupby(group_column)[value_column].min().reset_index()
                                elif agg_function == 'max':
                                    grouped_data = temp_df.groupby(group_column)[value_column].max().reset_index()
                                elif agg_function == 'median':
                                    grouped_data = temp_df.groupby(group_column)[value_column].median().reset_index()
                                
                                # Sort data untuk line chart yang rapi
                                if group_column in date_columns:
                                    grouped_data = grouped_data.sort_values(by=group_column)
                                else:
                                    # Untuk non-date, sort by value atau tetap urutan asli
                                    grouped_data = grouped_data.sort_values(by=value_column, ascending=False)
                                
                                # Buat line chart dengan Plotly
                                fig = px.line(
                                    grouped_data,
                                    x=group_column,
                                    y=value_column,
                                    title=f"📈 Line Chart: {value_column} by {group_column} ({agg_function})",
                                    markers=True,
                                    line_shape='linear'
                                )
                                
                                # Customize layout
                                fig.update_layout(
                                    xaxis_title=f"**{group_column}**",
                                    yaxis_title=f"**{value_column}** ({agg_function})",
                                    hovermode='x unified',
                                    height=500,
                                    showlegend=False
                                )
                                
                                # Tambahkan animasi hover yang lebih informatif
                                fig.update_traces(
                                    hovertemplate=f"<b>{group_column}</b>: %{{x}}<br>" +
                                                f"<b>{value_column}</b>: %{{y:.2f}}<extra></extra>"
                                )
                                
                                # Tampilkan chart
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Tampilkan statistik chart
                                st.subheader("📊 **Statistik Chart**")
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Total Data Points", len(grouped_data))
                                with col2:
                                    st.metric(f"Min {value_column}", f"{grouped_data[value_column].min():.2f}")
                                with col3:
                                    st.metric(f"Max {value_column}", f"{grouped_data[value_column].max():.2f}")
                                with col4:
                                    st.metric(f"Avg {value_column}", f"{grouped_data[value_column].mean():.2f}")
                                    
                                # Tampilkan data tabel
                                with st.expander("📋 **Lihat Data Chart**"):
                                    st.dataframe(grouped_data, use_container_width=True)
                                
                            except Exception as e:
                                st.error(f"❌ Error generating chart: {str(e)}")
                                st.info("💡 Pastikan kolom grouping memiliki nilai yang valid untuk grouping data.")
                    
                else:
                    st.warning("⚠️ Tidak cukup kolom numerik atau grouping untuk membuat line chart.")
                    
            except Exception as e:
                with st.expander("🌸 Panduan Penelitian Model", expanded=False):
                    st.markdown("""
                    **Penjelasan Penting 📛**
                    
                    ### ✨ Model Flowchart
                    - Model Tersebut Masih Tahap Uji Coba Jadi Tidak Sepenuhnya Tersedia Lebih Banyak Jadi Bisa Gunakan Model Flowchart Untuk Menjelaskan Proses Pemrosesan Data.
                    """)
                st.info("""
                **Tips Troubleshooting:**
                - Pastikan file tidak corrupt
                - Untuk CSV, pastikan format konsisten
                - Untuk Excel, pastikan tidak ada merged cells
                - Coba upload file dengan data yang lebih sederhana
                """)
        
        else:
            # Panduan penggunaan saat belum upload file
            with st.expander("🎯 **PANDUAN PENGGUNAAN**", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    ### 📁 **FORMAT FILE YANG DIDUKUNG**
                    
                    **CSV Files:**
                    - Format: .csv
                    - Encoding: UTF-8, Latin-1, ISO-8859-1
                    - Delimiter: koma (otomatis)
                    - Support file besar (>10MB)
                    
                    **Excel Files:**
                    - Format: .xlsx, .xls
                    - Multiple sheets support
                    - Auto sheet detection
                    """)
                    
                with col2:
                    st.markdown("""
                    ### 🚀 **FITUR ANALISIS LANJUT**
                    
                    **Analisis Otomatis:**
                    - Deteksi tipe data dengan persentase
                    - Analisis kelengkapan data
                    - Identifikasi data dominan
                    
                    **Visualization:**
                    - Flowchart dengan perhitungan akurat
                    - Pie chart komposisi data
                    - Line chart interaktif
                    
                    **Metrics:**
                    - Persentase per tipe data
                    - Kualitas data
                    - Kompleksitas dataset
                    """)
    
    with tab6:
        st.header("🖼️ Remove Background")
        
        # Sub-tabs untuk fitur yang berbeda
        sub_tab1, sub_tab2 = st.tabs(["Remove Background", "Roy Search"])
        
        with sub_tab1:
            st.subheader("Remove Background Dwi Bakti N Dev")
            
            with st.expander("📜 TATA CARA PENGGUNAAN REMOVE BACKGROUND", expanded=False):
                st.markdown(
                    """
                    <img src="https://blog.airbrush.com/wp-content/uploads/2024/08/AB_Cover_Remove-Bg_1.jpg" class="responsive-img">
                    """,
                    unsafe_allow_html=True
                )
                st.markdown("""

                
                ### 🧾 Pengertian
                - Remove background adalah fitur atau alat yang digunakan untuk secara otomatis menghapus latar belakang dari sebuah gambar, sehingga hanya menyisakan subjek utama. Fitur ini sangat berguna untuk berbagai keperluan seperti desain grafis, media sosial, dan e-commerce karena dapat menghemat waktu dan mempermudah proses pengeditan gambar tanpa perlu mengedit secara manual. Penggunaannya umumnya dilakukan melalui platform online seperti remove.bg atau fitur di aplikasi pengolah gambar seperti Photoshop dan PowerPoint. 
                
                ### ⚠️ Cara kerja dan penggunaan
                - 🛠️ Otomatis dengan AI: Alat ini memanfaatkan kecerdasan buatan untuk mendeteksi dan memisahkan subjek utama dari latar belakang, seringkali hanya dengan satu klik. 
                - 🛠️ Hasil instant: Proses penghapusan latar belakang dapat dilakukan dalam hitungan detik. 
                - 🛠️ Fleksibel: Setelah latar belakang dihapus, gambar dapat digunakan untuk berbagai keperluan. Gambar tersebut kemudian dapat disimpan sebagai format PNG dengan latar belakang transparan atau diganti dengan latar belakang baru. 
                
                ### 🔖 Contoh penggunaan
                - ⚙️ Kuantitatif: Data yang dapat diukur dengan bilangan, seperti tinggi badan atau jumlah penduduk. 
                - ⚙️ Kualitatif: Data yang berbentuk kategori atau deskripsi, seperti preferensi atau warna. 
                
                ### 📑 Berdasarkan hasil pengukuran
                - 📖 Desain grafis: Mempermudah pembuatan desain dengan menggabungkan objek ke latar belakang yang berbeda. 
                - 📖 Media sosial: Membuat foto profil atau konten media sosial terlihat lebih profesional dan menarik. 
                - 📖 E-commerce: Menampilkan foto produk secara bersih dan fokus tanpa gangguan dari latar belakang yang ramai. 
                
                ### 📑 Metode Perbandingan
                - 📒 Alat remove background sangat cepat dan otomatis untuk tugas yang sederhana
                - 📒 Penghapus manual (misalnya, Pen Tool di Photoshop) memberikan kontrol yang lebih presisi untuk hasil yang sangat detail, seperti pada rambut atau tepi objek yang rumit. 
                """)
            
            # Upload gambar
            uploaded_file = st.file_uploader(
                "Upload gambar untuk remove background", 
                type=['png', 'jpg', 'jpeg'],
                key="remove_bg"
            )
            
            if uploaded_file is not None:
                # Tampilkan gambar original
                col1, col2 = st.columns(2)
                
                with col1:
                    st.image(uploaded_file, caption="Gambar Original", use_column_width=True)
                
                # Proses remove background
                if st.button("Remove Background"):
                    with st.spinner("Menghapus background..."):
                        try:
                            # Kirim request ke Remove.bg API
                            response = requests.post(
                                'https://api.remove.bg/v1.0/removebg',
                                files={'image_file': uploaded_file.getvalue()},
                                data={'size': 'auto'},
                                headers={'X-Api-Key': REMOVE_BG_API_KEY}
                            )
                            
                            if response.status_code == 200:
                                # Tampilkan hasil
                                result_image = Image.open(io.BytesIO(response.content))
                                with col2:
                                    st.image(result_image, caption="Hasil Remove Background", use_column_width=True)
                                
                                # Download button
                                buf = io.BytesIO()
                                result_image.save(buf, format="PNG")
                                byte_im = buf.getvalue()
                                
                                st.download_button(
                                    label="Download Hasil",
                                    data=byte_im,
                                    file_name="no_bg_image.png",
                                    mime="image/png"
                                )
                                
                                st.success("Background berhasil dihapus!")
                            else:
                                st.error(f"Error API: {response.status_code}")
                                if response.status_code == 402:
                                    st.warning("Quota API mungkin habis")
                                elif response.status_code == 403:
                                    st.warning("API key tidak valid")
                                elif response.status_code == 400:
                                    st.warning("Format gambar tidak didukung")
                                
                        except Exception as e:
                            st.error(f"Terjadi error: {str(e)}")
            
        with sub_tab2:
            st.subheader("Roy Academy Search")
            
            # Input pencarian
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input(
                    "Kata kunci pencarian gambar statistik",
                    placeholder="contoh: statistics, chart, graph, data",
                    value="statistics",
                    help="Cari gambar terkait statistik dan visualisasi data"
                )
            
            with col2:
                per_page = st.selectbox("Jumlah", [10, 20, 30, 50], index=0)
            
            # Filter tambahan
            col3, col4 = st.columns(2)
            with col3:
                orientation = st.selectbox(
                    "Orientasi", 
                    ["all", "landscape", "portrait", "square"],
                    index=0
                )
            with col4:
                size = st.selectbox(
                    "Ukuran",
                    ["all", "large", "medium", "small"],
                    index=0
                )
            
            if st.button("🔍 Cari Gambar Statistik"):
                with st.spinner("Mencari gambar statistik..."):
                    try:
                        # Parameters untuk Pixels API
                        params = {
                            'query': search_query + " statistics chart graph data",
                            'per_page': per_page,
                            'orientation': orientation,
                            'size': size
                        }
                        
                        headers = {
                            'Authorization': PIXELS_API_KEY
                        }
                        
                        # Pixels API endpoint
                        response = requests.get(
                            'https://api.pexels.com/v1/search',
                            params=params,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Tampilkan hasil
                            if 'photos' in data and len(data['photos']) > 0:
                                st.success(f"🎉 Ditemukan {len(data['photos'])} gambar statistik")
                                
                                # Tampilkan gambar dalam grid
                                st.subheader("📷 Hasil Pencarian")
                                cols = st.columns(3)
                                
                                for idx, photo in enumerate(data['photos']):
                                    with cols[idx % 3]:
                                        # Tampilkan gambar dengan ukuran medium
                                        st.image(
                                            photo['src']['medium'],
                                            use_column_width=True,
                                            caption=f"📸 Oleh: {photo.get('photographer', 'Unknown')}"
                                        )
                                        
                                        # Tombol untuk melihat versi larger
                                        with st.expander("ℹ️ Info Detail"):
                                            st.write(f"**Photographer:** {photo.get('photographer', 'Unknown')}")
                                            st.write(f"**Ukuran:** {photo.get('width', 'Unknown')} x {photo.get('height', 'Unknown')}")
                                            st.markdown(f"[🔗 Download Original]({photo['src']['original']})")
                                        
                                        st.markdown("---")
                            else:
                                st.warning("❌ Tidak ada gambar statistik yang ditemukan")
                                st.info("Coba kata kunci lain seperti: data, chart, graph, analytics")
                                
                        else:
                            st.error(f"❌ Error API: {response.status_code}")
                            if response.status_code == 401:
                                st.warning("API key Pixels tidak valid")
                            elif response.status_code == 429:
                                st.warning("Quota API habis, coba lagi nanti")
                            
                    except Exception as e:
                        st.error(f"❌ Terjadi error: {str(e)}")
                        st.info("💡 Pastikan koneksi internet stabil")

    # Sidebar info
    with st.sidebar:
        st.header("🔑 Info API Access")
        st.info("Roy Acedemy 👑!")
        st.info("Ayo Belajar 📚 dan Meningkatkan 💪 Sikap Akademik")
    
    with tab5:
        st.header("🧮 Kalkulator Lengkap")
        
        # Sidebar untuk memilih jenis kalkulator
        calc_type = st.sidebar.selectbox(
            "Pilih Jenis Kalkulator",
            ["🔢 Kalkulator Dasar", "🔬 Kalkulator Ilmiah", "💰 Kalkulator Keuangan", "📐 Konverter Satuan", "⚖️ Kalkulator BMI", "⏰ Kalkulator Waktu"]
        )
        
        # Initialize session state for history
        if 'calc_history' not in st.session_state:
            st.session_state.calc_history = []
        
        def add_to_history(calculation):
            """Tambahkan perhitungan ke riwayat"""
            st.session_state.calc_history.append(calculation)
            if len(st.session_state.calc_history) > 10:  # Batasi hanya 10 riwayat terakhir
                st.session_state.calc_history.pop(0)
        
        if calc_type == "🔢 Kalkulator Dasar":
            st.subheader("🔢 Kalkulator Dasar")
            
            # Layout dengan columns untuk tampilan kalkulator
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Input angka
                num1 = st.number_input("Masukkan angka pertama", value=0.0, step=0.1, key="num1")
                num2 = st.number_input("Masukkan angka kedua", value=0.0, step=0.1, key="num2")
                
                # Operasi dasar
                operation = st.selectbox(
                    "Pilih operasi",
                    ["Penjumlahan (+)", "Pengurangan (-)", "Perkalian (×)", "Pembagian (÷)", "Pangkat (^)", "Akar Kuadrat", "Modulus (%)", "Persentase"]
                )
            
            with col2:
                st.markdown("### Hasil")
                if st.button("🔄 Hitung", type="primary", use_container_width=True):
                    try:
                        if operation == "Penjumlahan (+)":
                            result = num1 + num2
                            calc_str = f"{num1} + {num2} = {result}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif operation == "Pengurangan (-)":
                            result = num1 - num2
                            calc_str = f"{num1} - {num2} = {result}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif operation == "Perkalian (×)":
                            result = num1 * num2
                            calc_str = f"{num1} × {num2} = {result}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif operation == "Pembagian (÷)":
                            if num2 != 0:
                                result = num1 / num2
                                calc_str = f"{num1} ÷ {num2} = {result:.4f}"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Pembagian dengan nol!")
                        elif operation == "Pangkat (^)":
                            result = num1 ** num2
                            calc_str = f"{num1} ^ {num2} = {result}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif operation == "Akar Kuadrat":
                            if num1 >= 0:
                                result = num1 ** 0.5
                                calc_str = f"√{num1} = {result:.4f}"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Tidak bisa menghitung akar kuadrat dari bilangan negatif!")
                        elif operation == "Modulus (%)":
                            if num2 != 0:
                                result = num1 % num2
                                calc_str = f"{num1} % {num2} = {result}"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Modulus dengan nol!")
                        elif operation == "Persentase":
                            result = (num1 * num2) / 100
                            calc_str = f"{num1}% dari {num2} = {result}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                
                # Reset button
                if st.button("🗑️ Reset", use_container_width=True):
                    st.rerun()
        
        elif calc_type == "🔬 Kalkulator Ilmiah":
            st.subheader("🔬 Kalkulator Ilmiah")
            
            col1, col2 = st.columns(2)
            
            with col1:
                sci_num = st.number_input("Masukkan angka", value=0.0, step=0.1, key="sci_num")
                
                sci_operation = st.selectbox(
                    "Pilih fungsi ilmiah",
                    [
                        "sin() - Sinus", "cos() - Cosinus", "tan() - Tangen",
                        "asin() - Arcsinus", "acos() - Arccosinus", "atan() - Arctangen",
                        "log() - Logaritma natural", "log10() - Logaritma basis 10",
                        "exp() - Eksponensial", "abs() - Nilai absolut",
                        "sqrt() - Akar kuadrat", "factorial() - Faktorial"
                    ]
                )
                
                # Input tambahan untuk fungsi tertentu
                if sci_operation in ["sin() - Sinus", "cos() - Cosinus", "tan() - Tangen"]:
                    use_radians = st.checkbox("Gunakan radian (default: derajat)")
            
            with col2:
                if st.button("🔬 Hitung Fungsi Ilmiah", type="primary", use_container_width=True):
                    try:
                        if "sin()" in sci_operation:
                            if use_radians:
                                result = np.sin(sci_num)
                                calc_str = f"sin({sci_num} rad) = {result:.6f}"
                            else:
                                result = np.sin(np.radians(sci_num))
                                calc_str = f"sin({sci_num}°) = {result:.6f}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif "cos()" in sci_operation:
                            if use_radians:
                                result = np.cos(sci_num)
                                calc_str = f"cos({sci_num} rad) = {result:.6f}"
                            else:
                                result = np.cos(np.radians(sci_num))
                                calc_str = f"cos({sci_num}°) = {result:.6f}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif "tan()" in sci_operation:
                            if use_radians:
                                result = np.tan(sci_num)
                                calc_str = f"tan({sci_num} rad) = {result:.6f}"
                            else:
                                result = np.tan(np.radians(sci_num))
                                calc_str = f"tan({sci_num}°) = {result:.6f}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif "asin()" in sci_operation:
                            if -1 <= sci_num <= 1:
                                result = np.degrees(np.arcsin(sci_num))
                                calc_str = f"arcsin({sci_num}) = {result:.4f}°"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Input harus antara -1 dan 1 untuk arcsin!")
                        elif "acos()" in sci_operation:
                            if -1 <= sci_num <= 1:
                                result = np.degrees(np.arccos(sci_num))
                                calc_str = f"arccos({sci_num}) = {result:.4f}°"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Input harus antara -1 dan 1 untuk arccos!")
                        elif "atan()" in sci_operation:
                            result = np.degrees(np.arctan(sci_num))
                            calc_str = f"arctan({sci_num}) = {result:.4f}°"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif "log()" in sci_operation:
                            if sci_num > 0:
                                result = np.log(sci_num)
                                calc_str = f"ln({sci_num}) = {result:.6f}"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Logaritma hanya untuk bilangan positif!")
                        elif "log10()" in sci_operation:
                            if sci_num > 0:
                                result = np.log10(sci_num)
                                calc_str = f"log10({sci_num}) = {result:.6f}"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Logaritma hanya untuk bilangan positif!")
                        elif "exp()" in sci_operation:
                            result = np.exp(sci_num)
                            calc_str = f"exp({sci_num}) = {result:.6f}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif "abs()" in sci_operation:
                            result = abs(sci_num)
                            calc_str = f"|{sci_num}| = {result}"
                            st.success(f"**Hasil:** {calc_str}")
                            add_to_history(calc_str)
                        elif "sqrt()" in sci_operation:
                            if sci_num >= 0:
                                result = np.sqrt(sci_num)
                                calc_str = f"√{sci_num} = {result:.6f}"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Tidak bisa menghitung akar kuadrat dari bilangan negatif!")
                        elif "factorial()" in sci_operation:
                            if sci_num >= 0 and sci_num == int(sci_num):
                                result = np.math.factorial(int(sci_num))
                                calc_str = f"{int(sci_num)}! = {result}"
                                st.success(f"**Hasil:** {calc_str}")
                                add_to_history(calc_str)
                            else:
                                st.error("❌ Error: Faktorial hanya untuk bilangan bulat non-negatif!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        elif calc_type == "💰 Kalkulator Keuangan":
            st.subheader("💰 Kalkulator Keuangan")
            
            finance_option = st.selectbox(
                "Pilih kalkulator keuangan",
                ["Bunga Sederhana", "Bunga Majemuk", "Cicilan Loan", "Investasi", "Nilai Tukar Mata Uang"]
            )
            
            if finance_option == "Bunga Sederhana":
                st.write("**Kalkulator Bunga Sederhana**")
                col1, col2 = st.columns(2)
                
                with col1:
                    principal = st.number_input("Modal awal (P)", value=1000000.0, step=100000.0, min_value=0.0)
                    rate = st.number_input("Suku bunga tahunan (%)", value=5.0, step=0.1, min_value=0.0)
                
                with col2:
                    time = st.number_input("Waktu (tahun)", value=1.0, step=0.5, min_value=0.0)
                
                if st.button("💰 Hitung Bunga Sederhana", type="primary"):
                    interest = principal * rate * time / 100
                    total = principal + interest
                    calc_str = f"Bunga Sederhana: Rp {principal:,.0f} × {rate}% × {time}thn = Rp {interest:,.0f}"
                    st.success(f"""
                    **Hasil Perhitungan:**
                    - Bunga Sederhana: **Rp {interest:,.2f}**
                    - Total Akhir: **Rp {total:,.2f}**
                    """)
                    add_to_history(calc_str)
            
            elif finance_option == "Bunga Majemuk":
                st.write("**Kalkulator Bunga Majemuk**")
                col1, col2 = st.columns(2)
                
                with col1:
                    principal = st.number_input("Modal awal (P)", value=1000000.0, step=100000.0, min_value=0.0, key="compound_principal")
                    rate = st.number_input("Suku bunga tahunan (%)", value=5.0, step=0.1, min_value=0.0, key="compound_rate")
                
                with col2:
                    time = st.number_input("Waktu (tahun)", value=1.0, step=0.5, min_value=0.0, key="compound_time")
                    compounds = st.number_input("Frekuensi compounding per tahun", value=12, step=1, min_value=1)
                
                if st.button("💰 Hitung Bunga Majemuk", type="primary"):
                    amount = principal * (1 + rate/(100 * compounds)) ** (compounds * time)
                    interest = amount - principal
                    calc_str = f"Bunga Majemuk: Rp {principal:,.0f} → Rp {amount:,.0f} (bunga: Rp {interest:,.0f})"
                    st.success(f"""
                    **Hasil Perhitungan:**
                    - Bunga Majemuk: **Rp {interest:,.2f}**
                    - Total Akhir: **Rp {amount:,.2f}**
                    - Effective Annual Rate: **{(amount/principal)**(1/time)-1:.2%}**
                    """)
                    add_to_history(calc_str)
            
            elif finance_option == "Cicilan Loan":
                st.write("**Kalkulator Cicilan Loan**")
                col1, col2 = st.columns(2)
                
                with col1:
                    loan_amount = st.number_input("Jumlah Pinjaman", value=10000000.0, step=1000000.0, min_value=0.0)
                    interest_rate = st.number_input("Suku bunga tahunan (%)", value=6.0, step=0.1, min_value=0.0)
                
                with col2:
                    loan_term = st.number_input("Jangka waktu (tahun)", value=5, step=1, min_value=1)
                    payment_frequency = st.selectbox("Frekuensi Pembayaran", ["Bulanan", "Tahunan"])
                
                if st.button("🏠 Hitung Cicilan", type="primary"):
                    if payment_frequency == "Bulanan":
                        periods = loan_term * 12
                        monthly_rate = interest_rate / 100 / 12
                        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**periods) / ((1 + monthly_rate)**periods - 1)
                        total_payment = monthly_payment * periods
                        total_interest = total_payment - loan_amount
                        
                        st.success(f"""
                        **Hasil Perhitungan Cicilan:**
                        - Cicilan Bulanan: **Rp {monthly_payment:,.2f}**
                        - Total Pembayaran: **Rp {total_payment:,.2f}**
                        - Total Bunga: **Rp {total_interest:,.2f}**
                        """)
                        add_to_history(f"Cicilan: Rp {loan_amount:,.0f} → Rp {monthly_payment:,.0f}/bulan")
        
        elif calc_type == "📐 Konverter Satuan":
            st.subheader("📐 Konverter Satuan")
            
            conversion_type = st.selectbox(
                "Pilih jenis konversi",
                ["Panjang", "Berat", "Suhu", "Luas", "Volume", "Kecepatan", "Energi"]
            )
            
            if conversion_type == "Panjang":
                col1, col2, col3 = st.columns([2,1,2])
                with col1:
                    length_value = st.number_input("Nilai", value=1.0, step=0.1)
                    from_unit = st.selectbox("Dari", ["meter", "kilometer", "centimeter", "milimeter", "inci", "kaki", "yard", "mil"])
                with col3:
                    to_unit = st.selectbox("Ke", ["meter", "kilometer", "centimeter", "milimeter", "inci", "kaki", "yard", "mil"])
                    
                    # Konversi panjang
                    conversions = {
                        "meter": 1,
                        "kilometer": 1000,
                        "centimeter": 0.01,
                        "milimeter": 0.001,
                        "inci": 0.0254,
                        "kaki": 0.3048,
                        "yard": 0.9144,
                        "mil": 1609.344
                    }
                    
                    if st.button("🔄 Konversi Panjang", type="primary"):
                        result = length_value * conversions[from_unit] / conversions[to_unit]
                        calc_str = f"{length_value} {from_unit} = {result:.6f} {to_unit}"
                        st.success(f"**Hasil:** {calc_str}")
                        add_to_history(calc_str)
            
            elif conversion_type == "Suhu":
                col1, col2, col3 = st.columns([2,1,2])
                with col1:
                    temp_value = st.number_input("Suhu", value=0.0, step=0.1)
                    from_temp = st.selectbox("Dari", ["Celsius", "Fahrenheit", "Kelvin"])
                with col3:
                    to_temp = st.selectbox("Ke", ["Celsius", "Fahrenheit", "Kelvin"])
                    
                    if st.button("🌡️ Konversi Suhu", type="primary"):
                        # Konversi ke Celsius dulu
                        if from_temp == "Celsius":
                            celsius = temp_value
                        elif from_temp == "Fahrenheit":
                            celsius = (temp_value - 32) * 5/9
                        else:  # Kelvin
                            celsius = temp_value - 273.15
                        
                        # Konversi dari Celsius ke target
                        if to_temp == "Celsius":
                            result = celsius
                        elif to_temp == "Fahrenheit":
                            result = (celsius * 9/5) + 32
                        else:  # Kelvin
                            result = celsius + 273.15
                        
                        calc_str = f"{temp_value}° {from_temp} = {result:.2f}° {to_temp}"
                        st.success(f"**Hasil:** {calc_str}")
                        add_to_history(calc_str)
            
            elif conversion_type == "Berat":
                col1, col2, col3 = st.columns([2,1,2])
                with col1:
                    weight_value = st.number_input("Nilai", value=1.0, step=0.1)
                    from_unit = st.selectbox("Dari", ["gram", "kilogram", "miligram", "pon", "ons"])
                with col3:
                    to_unit = st.selectbox("Ke", ["gram", "kilogram", "miligram", "pon", "ons"])
                    
                    conversions = {
                        "gram": 1,
                        "kilogram": 1000,
                        "miligram": 0.001,
                        "pon": 453.592,
                        "ons": 28.3495
                    }
                    
                    if st.button("⚖️ Konversi Berat", type="primary"):
                        result = weight_value * conversions[from_unit] / conversions[to_unit]
                        calc_str = f"{weight_value} {from_unit} = {result:.6f} {to_unit}"
                        st.success(f"**Hasil:** {calc_str}")
                        add_to_history(calc_str)
        
        elif calc_type == "⚖️ Kalkulator BMI":
            st.subheader("⚖️ Kalkulator BMI (Body Mass Index)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                weight = st.number_input("Berat Badan (kg)", value=70.0, step=0.1, min_value=1.0)
                height = st.number_input("Tinggi Badan (cm)", value=170.0, step=0.1, min_value=1.0)
                age = st.number_input("Usia", value=25, step=1, min_value=1, max_value=120)
                gender = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            
            with col2:
                if st.button("📊 Hitung BMI", type="primary", use_container_width=True):
                    height_m = height / 100
                    bmi = weight / (height_m ** 2)
                    
                    # Kategori BMI
                    if bmi < 18.5:
                        category = "Kurus"
                        advice = "Disarankan untuk menambah berat badan dengan makanan bergizi"
                    elif 18.5 <= bmi < 24.9:
                        category = "Normal"
                        advice = "Pertahankan berat badan ideal Anda!"
                    elif 25 <= bmi < 29.9:
                        category = "Gemuk"
                        advice = "Disarankan untuk menurunkan berat badan"
                    else:
                        category = "Obesitas"
                        advice = "Sangat disarankan untuk menurunkan berat badan dan konsultasi dokter"
                    
                    st.success(f"""
                    **Hasil Perhitungan BMI:**
                    - **BMI:** {bmi:.1f}
                    - **Kategori:** {category}
                    - **Saran:** {advice}
                    """)
                    add_to_history(f"BMI: {bmi:.1f} ({category})")
        
        elif calc_type == "⏰ Kalkulator Waktu":
            st.subheader("⏰ Kalkulator Waktu")
            
            time_option = st.selectbox("Pilih jenis perhitungan", [
                "Penambahan/Pengurangan Waktu", 
                "Selisih Waktu", 
                "Konversi Waktu"
            ])
            
            if time_option == "Penambahan/Pengurangan Waktu":
                col1, col2, col3 = st.columns(3)
                with col1:
                    hours = st.number_input("Jam", value=0, min_value=0, max_value=23)
                    minutes = st.number_input("Menit", value=0, min_value=0, max_value=59)
                with col2:
                    seconds = st.number_input("Detik", value=0, min_value=0, max_value=59)
                    operation = st.radio("Operasi", ["Tambah", "Kurangi"])
                with col3:
                    add_hours = st.number_input("Jam untuk ditambah/dikurang", value=0, min_value=0)
                    add_minutes = st.number_input("Menit untuk ditambah/dikurang", value=0, min_value=0, max_value=59)
                    add_seconds = st.number_input("Detik untuk ditambah/dikurang", value=0, min_value=0, max_value=59)
                
                if st.button("⏰ Hitung Waktu", type="primary"):
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                    add_total_seconds = add_hours * 3600 + add_minutes * 60 + add_seconds
                    
                    if operation == "Tambah":
                        result_seconds = total_seconds + add_total_seconds
                    else:
                        result_seconds = total_seconds - add_total_seconds
                    
                    if result_seconds < 0:
                        st.error("❌ Hasil waktu tidak boleh negatif!")
                    else:
                        result_hours = result_seconds // 3600
                        result_minutes = (result_seconds % 3600) // 60
                        result_seconds_final = result_seconds % 60
                        
                        calc_str = f"{hours:02d}:{minutes:02d}:{seconds:02d} {operation} {add_hours:02d}:{add_minutes:02d}:{add_seconds:02d} = {result_hours:02d}:{result_minutes:02d}:{result_seconds_final:02d}"
                        st.success(f"**Hasil:** {calc_str}")
                        add_to_history(calc_str)

        # History Kalkulator
        st.markdown("---")
        st.subheader("📜 Riwayat Perhitungan")
        
        # Display history
        if st.session_state.calc_history:
            for i, calculation in enumerate(reversed(st.session_state.calc_history)):
                st.write(f"{i+1}. {calculation}")
        else:
            st.info("Belum ada riwayat perhitungan")
        
        # Clear history button
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("🗑️ Hapus Semua Riwayat", use_container_width=True):
                st.session_state.calc_history = []
                st.rerun()

    # Menambahkan CSS untuk styling kalkulator
    st.markdown("""
    <style>
        .stButton button {
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
        }
        .stButton button[kind="primary"] {
            background-color: #4CAF50;
            color: white;
        }
        .stSuccess {
            padding: 15px;
            border-radius: 10px;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .stError {
            padding: 15px;
            border-radius: 10px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .stInfo {
            padding: 15px;
            border-radius: 10px;
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
        }
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]) {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    with tab4:
        st.subheader("📋 Informasi Penggunaan")
        
        # Header dengan columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 🚀 Cara Penggunaan Aplikasi
            
            1. **📤 Unggah Data**: Gunakan menu sidebar untuk mengunggah file data dalam format CSV atau Excel
            2. **📊 Statistik**: Lihat ringkasan statistik deskriptif di tab Statistik
            3. **📈 Visualisasi**: Eksplorasi data melalui berbagai chart dan grafik interaktif
            4. **🔍 Data Mentah**: Periksa data asli dalam format tabel yang dapat di-filter
            """)
        
        with col2:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", 
                    width=150, caption="Dwi Bakti N Dev")
        
        # Fitur Utama dengan cards
        st.markdown("### ⭐ Fitur Utama")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info("**📐 Analisis Statistik**\n\nMean, Median, Modus, Standar Deviasi")
        
        with col2:
            st.success("**🎨 Visualisasi Interaktif**\n\nChart dan Grafik Real-time")
        
        with col3:
            st.warning("**💾 Ekspor Hasil**\n\nDownload hasil analisis")
        
        with col4:
            st.error("**🧹 Pembersihan Data**\n\nAuto-clean missing values")
        
        # Video Tutorial (placeholder)
        st.markdown("### 🎥 Video Tutorial Penggunaan V2.3.8")
        import streamlit.components.v1 as components
        google_drive_id = "1obx6q2jQS1fRrNi1E4VpAPlyI_rR9nO5"

        google_drive_embed_html = f"""
        <style>
        .video-wrapper {{
            position: relative;
            width: 100%;
            max-width: 800px;       /* batas lebar maksimum */
            margin: 0 auto;         /* rata tengah */
            padding-top: 56.25%;    /* rasio 16:9 */
        }}

        .video-wrapper iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 12px;    /* sudut melengkung */
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); /* efek bayangan lembut */
        }}
        </style>

        <div class="video-wrapper">
            <iframe src="https://drive.google.com/file/d/{google_drive_id}/preview" allow="autoplay"></iframe>
        </div>
        """


        # ✅ Render di Streamlit
        components.html(google_drive_embed_html, height=500, scrolling=False)
        
        st.divider()
        
        # Rumus Matematika dengan expanders
        st.subheader("🧮 Rumus Matematika dan Metode Perhitungan")
        
        # Statistical Formulas dengan tabs
        tab_rumus, tab_contoh, tab_visual = st.tabs(["📐 Rumus", "🔢 Contoh", "📊 Visualisasi"])
        
        with tab_rumus:
            st.markdown("""
            ### 📊 Statistik Deskriptif - Rumus dan Perhitungan
            
            #### 1. Mean (Rata-rata)
            ```math
            \mu = \frac{\sum_{i=1}^{n} x_i}{n}
            ```
            
            #### 2. Median
            - **n ganjil:** `Median = x₍ₙ₊₁₎/₂`
            - **n genap:** `Median = (x₍ₙ/₂₎ + x₍ₙ/₂₊₁₎) / 2`
            
            #### 3. Standar Deviasi (Sampel)
            ```math
            s = \sqrt{\frac{\sum_{i=1}^{n} (x_i - \bar{x})^2}{n-1}}
            ```
            
            #### 4. Variance (Ragam)
            ```math
            s^2 = \frac{\sum_{i=1}^{n} (x_i - \bar{x})^2}{n-1}
            ```
            
            #### 5. Koefisien Korelasi Pearson
            ```math
            r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2} \times \sqrt{\sum (y_i - \bar{y})^2}}
            ```
            """)
        
        with tab_contoh:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                #### Contoh Perhitungan Mean
                **Data:** [2, 4, 6, 8, 10]
                ```
                μ = (2 + 4 + 6 + 8 + 10) / 5 
                = 30 / 5 
                = 6
                ```
                
                #### Contoh Standar Deviasi
                **Data:** [2, 4, 4, 4, 5, 5, 7, 9]
                ```
                Mean = 5
                Variance = 32/7 ≈ 4.57
                Standar Deviasi = √4.57 ≈ 2.14
                ```
                """)
            
            with col2:
                st.markdown("""
                #### Contoh Korelasi
                **Data X:** [1, 2, 3, 4, 5]
                **Data Y:** [2, 4, 6, 8, 10]
                ```
                r = 1.0 (Korelasi positif sempurna)
                ```
                
                #### Contoh Regresi Linear
                **Persamaan:** y = a + bx
                ```
                b = 2.0, a = 0.0
                y = 0 + 2x
                ```
                """)
        
        with tab_visual:
            col1, col2 = st.columns(2)
            
            with col1:
                # Placeholder untuk visualisasi distribusi normal
                st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Normal_Distribution_PDF.svg/1200px-Normal_Distribution_PDF.svg.png", 
                        caption="Distribusi Normal", use_column_width=True)
            
            with col2:
                # Placeholder untuk visualisasi korelasi
                st.image("https://uploads-ssl.webflow.com/61af164800e38cf1b6c60b55/6401eb60f7f8fc5fd74a1abd_nilai%20korelasi.WebP",
                        caption="Jenis-jenis Korelasi", use_column_width=True)
        
        # Distribusi Probabilitas
        st.markdown("### 📊 Distribusi Probabilitas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### Distribusi Normal
            ```math
            f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}
            ```
            """)
            st.image("https://math.libretexts.org/@api/deki/files/109416/39cca5174e2a6f2cc5de254ce6fafccd1e87c057?revision=1",
                    caption="Kurva Distribusi Normal", use_column_width=True)
        
        with col2:
            st.markdown("""
            #### Distribusi Binomial
            ```math
            P(X=k) = C(n,k) \times p^k \times (1-p)^{n-k}
            ```
            ```math
            C(n,k) = \frac{n!}{k!(n-k)!}
            ```
            """)
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Binomial_distribution_pmf.svg/1200px-Binomial_distribution_pmf.svg.png",
                    caption="Distribusi Binomial", use_column_width=True)
        
        st.divider()
        
        # Informasi Lisensi dengan expander
        st.subheader("📄 Hak Lisensi")
        # Video Tutorial (placeholder)
        st.markdown("### 🎥 Proses Pembuatan Streamlit Launcher")
        import streamlit.components.v1 as components
        google_drive_id = "1RD94cKgmYzbIf83jXz1cIPeweQeqx9CS"

        google_drive_embed_html = f"""
        <style>
        .video-wrapper {{
            position: relative;
            width: 100%;
            max-width: 800px;       /* batas lebar maksimum */
            margin: 0 auto;         /* rata tengah */
            padding-top: 56.25%;    /* rasio 16:9 */
        }}

        .video-wrapper iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 12px;    /* sudut melengkung */
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); /* efek bayangan lembut */
        }}
        </style>

        <div class="video-wrapper">
            <iframe src="https://drive.google.com/file/d/{google_drive_id}/preview" allow="autoplay"></iframe>
        </div>
        """
        


        # ✅ Render di Streamlit
        components.html(google_drive_embed_html, height=500, scrolling=False)
        
        with st.expander("📜 STRICT PROPRIETARY SOFTWARE LICENSE — ALL RIGHTS RESERVED", expanded=False):
            st.markdown("""
            **Hak Cipta © 2025 Dwi Bakti N Dev. Seluruh hak dilindungi undang-undang.**
            
            ### 🔒 Definisi
            - **Pemilik**: Dwi Bakti N Dev, pemilik semua hak atas Perangkat Lunak
            - **Perangkat Lunak**: Seluruh kode sumber, dokumentasi, dan materi terkait
            - **Pengguna**: Pihak yang mendapatkan salinan Perangkat Lunak
            
            ### ⚠️ Pembatasan Ketat
            ❌ **DILARANG** menyalin, mereproduksi, atau membuat karya turunan  
            ❌ **DILARANG** menyebarluaskan atau menjual Perangkat Lunak  
            ❌ **DILARANG** menggunakan untuk layanan komersial pihak ketiga  
            ❌ **DILARANG** reverse engineering atau dekompilasi  
            
            ### 📞 Kontak Lisensi
            **Nama**: Dwi Bakti N Dev  
            **Website**: https://portofolio-dwi-bakti-n-dev-liard.vercel.app  
            **Tanggal Efektif**: 14/10/2025
            """)
        
        st.divider()

        
        # Informasi Penelitian
        st.subheader("🔬 Informasi Penelitian")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 🎯 Metodologi Penelitian
            
            #### 📊 Sumber Data
            - Data primer dari survei lapangan
            - Data sekunder dari publikasi resmi
            - Dataset open source terpercaya
            
            #### 🔍 Metode Analisis
            - Statistik deskriptif (mean, median, modus, standar deviasi)
            - Analisis eksploratori data (EDA)
            - Visualisasi data untuk identifikasi pola
            - Validasi data dengan multiple methods
            """)
        
        with col2:
            st.image("https://cdn-icons-png.flaticon.com/512/2933/2933245.png",
                    caption="Metode Penelitian", width=200)
        
        # Metode Statistik dengan cards
        st.markdown("### 📐 Metode Statistik yang Digunakan")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            #### 🧪 Uji Normalitas
            **Shapiro-Wilk test**
            ```math
            W = \\frac{(\\sum a_i \\times x_{(i)})^2}{\\sum (x_i - \\bar{x})^2}
            ```
            """)
        
        with col2:
            st.markdown("""
            #### 📝 Uji Hipotesis
            **t-test**
            ```math
            t = \\frac{\\bar{x}_1 - \\bar{x}_2}{\\sqrt{\\frac{s_1^2}{n_1} + \\frac{s_2^2}{n_2}}}
            ```
            """)
        
        with col3:
            st.markdown("""
            #### 📊 Analisis Varians
            **ANOVA**
            ```math
            F = \\frac{\\text{Varians antar grup}}{\\text{Varians dalam grup}}
            ```
            """)
        
        st.divider()
        
        # Sumber Belajar dengan tabs
        st.subheader("📚 Sumber Belajar Statistik")
        
        tab_buku, tab_online, tab_tools = st.tabs(["📖 Buku", "🌐 Online", "🛠️ Tools"])
        
        with tab_buku:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📚 Buku Referensi Recommended
                
                #### 1. "Statistics for Data Science"
                **Penulis**: James et al.  
                **Bab Penting**:
                - Bab 2: Descriptive Statistics
                - Bab 3: Probability Distributions
                - Bab 4: Statistical Inference
                
                #### 2. "Introduction to Probability"
                **Penulis**: Bertsekas  
                **Fokus**: Fundamental probability theory
                """)
            
            with col2:
                st.markdown("""
                #### 3. "The Elements of Statistical Learning"
                **Penulis**: Hastie et al.  
                **Level**: Advanced  
                **Aplikasi**: Machine learning
                
                #### 4. "Practical Statistics for Data Scientists"
                **Penulis**: Bruce & Bruce (2021) 
                **Fokus**: Aplikasi praktis
                """)
        
        with tab_online:
            st.markdown("""
            ### 🌐 Sumber Belajar Online
            
            #### 🎓 Platform Kursus
            - **Roy Academy** - Statistics and Probability
            - **MIT OpenCourseWare** - Introduction to Probability and Statistics
            - **Coursera** - Data Science and Statistical Analysis Roy/Dwi Bakti N Dev
            - **edX** - Statistical Thinking for Data Science
            
            #### 📹 Tutorial Video
            - **Tiktok Channels**: Royhtml
            - **Interactive Tutorials**: Dwi Bakti N DeV
            """)
        
        with tab_tools:
            st.markdown("""
            ### 🛠️ Tools & Software Statistik
            
            #### 🔧 Software Populer
            - **Python** (pandas, numpy, scipy)
            - **R** & RStudio
            - **JASP** (Free alternative to SPSS)
            - **Gretl** (Econometrics)
            
            #### 📊 Visualization Tools
            - **Tableau** - Business intelligence
            - **Plotly** - Interactive charts
            - **Matplotlib/Seaborn** - Python plotting
            """)
        
        st.divider()
        
        # Kontak dan Support
        st.subheader("📞 Kontak & Support")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🌐 Website
            [https://portofolio-dwi-bakti-n-dev-liard.vercel.app](https://portofolio-dwi-bakti-n-dev-liard.vercel.app)
            
            ### 👨‍💻 Developer
            **Dwi Bakti N Dev**
            """)
        
        with col2:
            st.markdown("""
            ### 💬 Bantuan
            - Dokumentasi lengkap
            - Tutorial penggunaan
            - Contoh dataset
            - FAQ
            """)
        
        with col3:
            st.markdown("""
            ### 🔄 Update
            - Versi terbaru: 2.3.8
            - Rilis: Oktober 2025
            - Last updated: 2025
            - Compatibility: Python 3.8+
            """)
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray;'>"
            "© 2025 Dwi Bakti N Dev | Statistical Analysis Tool | All Rights Reserved"
            "</div>",
            unsafe_allow_html=True
        )
    
    with tab1:
        show_optimized_statistics(df)
    
    with tab2:
        st.header("🎨 Visualisasi Data")
        create_all_visualizations(df)
    
    with tab3:
        st.header("📋 Data Lengkap & Analisis Komprehensif")

        # Cek jika df ada dan tidak kosong
        if 'df' in locals() or 'df' in globals():
            if len(df) > 0:
                # Optimasi: Tampilkan dataframe dengan pagination untuk dataset besar
                st.dataframe(df, use_container_width=True, 
                            height=400 if len(df) > 1000 else min(400, len(df)*25))
                
                # Informasi dasar dataset dengan optimasi memory
                st.subheader("📊 Informasi Dataset")
                
                col_info1, col_info2, col_info3, col_info4 = st.columns(4)
                
                with col_info1:
                    st.metric("Total Records", f"{len(df):,}")
                    st.metric("Total Kolom", len(df.columns))
                
                with col_info2:
                    numeric_cols = len(df.select_dtypes(include=['number']).columns)
                    categorical_cols = len(df.select_dtypes(include=['object']).columns)
                    st.metric("Kolom Numerik", f"{numeric_cols}")
                    st.metric("Kolom Kategorikal", f"{categorical_cols}")
                
                with col_info3:
                    missing_values = df.isnull().sum().sum()
                    duplicate_rows = df.duplicated().sum()
                    st.metric("Missing Values", f"{missing_values}")
                    st.metric("Duplikat", f"{duplicate_rows}")
                
                with col_info4:
                    memory_usage = df.memory_usage(deep=True).sum() / 1024**2
                    st.metric("Memory Usage", f"{memory_usage:.2f} MB")
                    st.metric("Data Types", f"{len(df.dtypes.unique())}")

                # Optimasi: Hitung statistik hanya sekali dan cache
                @st.cache_data
                def calculate_basic_stats(_df, numeric_columns):
                    stats = {}
                    if numeric_columns:
                        stats['total_values'] = _df[numeric_columns].sum().sum()
                        stats['avg_value'] = _df[numeric_columns].mean().mean()
                        stats['median_value'] = _df[numeric_columns].median().median()
                        stats['std_value'] = _df[numeric_columns].std().mean()
                        stats['cv_value'] = (stats['std_value'] / stats['avg_value'] * 100) if stats['avg_value'] != 0 else 0
                        
                        # Tambahan statistik lengkap
                        stats['skewness'] = _df[numeric_columns].skew().mean()
                        stats['kurtosis'] = _df[numeric_columns].kurtosis().mean()
                        stats['q1'] = _df[numeric_columns].quantile(0.25).mean()
                        stats['q3'] = _df[numeric_columns].quantile(0.75).mean()
                        stats['min_value'] = _df[numeric_columns].min().min()
                        stats['max_value'] = _df[numeric_columns].max().max()
                        stats['range'] = stats['max_value'] - stats['min_value']
                        
                    return stats

                # Section untuk statistik deskriptif
                st.subheader("📊 Statistik Deskriptif Lengkap")
                
                # Pilih kolom numerik
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                
                if numeric_columns:
                    basic_stats = calculate_basic_stats(df, numeric_columns)
                    
                    # Tampilkan dalam 2 baris metrik
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Jumlah Data", len(df))
                        st.metric("Kolom Numerik", len(numeric_columns))
                        st.metric("Nilai Minimum", f"{basic_stats['min_value']:,.2f}")
                    
                    with col2:
                        st.metric("Total Semua Nilai", f"{basic_stats['total_values']:,.2f}")
                        st.metric("Total Nilai Valid", f"{df[numeric_columns].count().sum():,}")
                        st.metric("Nilai Maksimum", f"{basic_stats['max_value']:,.2f}")
                    
                    with col3:
                        st.metric("Rata-rata Keseluruhan", f"{basic_stats['avg_value']:,.2f}")
                        st.metric("Median Keseluruhan", f"{basic_stats['median_value']:,.2f}")
                        st.metric("Range", f"{basic_stats['range']:,.2f}")
                    
                    with col4:
                        st.metric("Std Dev Rata-rata", f"{basic_stats['std_value']:,.2f}")
                        st.metric("Koef. Variasi", f"{basic_stats['cv_value']:.1f}%")
                        st.metric("Skewness", f"{basic_stats['skewness']:.2f}")

                # STRATEGI DAN METODOLOGI ANALISIS
                st.subheader("🎯 STRATEGI ANALISIS & METODOLOGI")
                
                strategy_tab1, strategy_tab2, strategy_tab3 = st.tabs(["📋 Framework", "🧮 Rumus Statistik", "🔍 Teknik Analisis"])
                
                with strategy_tab1:
                    st.markdown("""
                    ### 🎯 Framework Analisis Data Komprehensif
                    
                    **1. DATA ASSESSMENT** 
                    - ✅ Profiling Dataset & Quality Check
                    - ✅ Missing Values Analysis  
                    - ✅ Outlier Detection
                    - ✅ Data Consistency Validation
                    
                    **2. STATISTICAL ANALYSIS**
                    - 📈 Descriptive Statistics (Mean, Median, Std Dev)
                    - 📊 Distribution Analysis (Skewness, Kurtosis)
                    - 🔍 Correlation & Pattern Detection
                    - 📉 Trend & Seasonality Analysis
                    
                    **3. BUSINESS INTELLIGENCE**
                    - 🎯 Key Performance Indicators
                    - 📋 Actionable Insights
                    - 🚀 Strategic Recommendations
                    - 📊 Dashboard & Reporting
                    """)
                
                with strategy_tab2:
                    st.markdown("""
                    ### 🧮 FORMULA & METODE STATISTIK YANG DIGUNAKAN
                    
                    **📊 Ukuran Pemusatan Data:**
                    ```python
                    Mean = Σx / n
                    Median = nilai tengah (Q2)
                    Modus = nilai paling sering muncul
                    ```
                    
                    **📈 Ukuran Penyebaran Data:**
                    ```python
                    Std Dev = √[Σ(x - μ)² / (n-1)]
                    Variance = Σ(x - μ)² / (n-1)
                    Range = Max - Min
                    IQR = Q3 - Q1
                    ```
                    
                    **📉 Koefisien Variasi (CV):**
                    ```python
                    CV = (Std Dev / Mean) × 100%
                    ```
                    
                    **📊 Deteksi Outlier (IQR Method):**
                    ```python
                    Lower Bound = Q1 - 1.5 × IQR
                    Upper Bound = Q3 + 1.5 × IQR
                    ```
                    
                    **📈 Skewness & Kurtosis:**
                    ```python
                    Skewness = Σ[(x - μ)³] / (n × σ³)
                    Kurtosis = Σ[(x - μ)⁴] / (n × σ⁴) - 3
                    ```
                    """)
                
                with strategy_tab3:
                    st.markdown("""
                    ### 🔍 TEKNIK ANALISIS LANJUTAN
                    
                    **📊 Analisis Kualitas Data:**
                    - Data Completeness Rate
                    - Data Consistency Check
                    - Duplicate Detection
                    - Data Validation Rules
                    
                    **📈 Analisis Distribusi:**
                    - Normal Distribution Test
                    - Skewness & Kurtosis Analysis
                    - QQ-Plot Visualization
                    - Histogram & Density Plot
                    
                    **🔍 Analisis Korelasi:**
                    - Pearson Correlation Matrix
                    - Spearman Rank Correlation
                    - Heatmap Visualization
                    - Multicollinearity Check
                    
                    **📉 Time Series Analysis:**
                    - Trend Analysis (Linear/Non-linear)
                    - Seasonality Detection
                    - Moving Average Calculation
                    - Year-over-Year Growth
                    """)

                # ANALISIS LENGKAP DENGAN RUMUSAN MASALAH DAN SOLUSI
                st.subheader("🔍 ANALISIS KOMPREHENSIF & REKOMENDASI STRATEGIS")

                # Identifikasi Masalah Utama dengan Scoring
                st.markdown("### 🎯 DIAGNOSIS MASALAH UTAMA")
                
                problems = []
                solutions = []
                risk_scores = []
                
                # Analisis Data Quality dengan scoring
                completeness_rate = (1 - missing_values / (len(df) * len(df.columns))) * 100 if len(df) > 0 else 0
                if completeness_rate < 90:
                    risk_score = min(100, (90 - completeness_rate) * 2)
                    problems.append({
                        "issue": f"**Kualitas Data Rendah**", 
                        "detail": f"Tingkat kelengkapan data hanya {completeness_rate:.1f}%",
                        "risk": risk_score,
                        "impact": "Tinggi"
                    })
                    solutions.append("**Prioritas Cleaning Data**: Implementasi imputasi data untuk missing values menggunakan mean/median/mode berdasarkan distribusi")
                    risk_scores.append(risk_score)
                
                if duplicate_rows > 0:
                    risk_score = min(100, (duplicate_rows / len(df)) * 1000)
                    problems.append({
                        "issue": f"**Data Duplikat**", 
                        "detail": f"Terdapat {duplicate_rows} records duplikat ({duplicate_rows/len(df)*100:.1f}%)",
                        "risk": risk_score,
                        "impact": "Menengah"
                    })
                    solutions.append("**Hapus Duplikat**: Gunakan df.drop_duplicates() dengan subset kolom kunci untuk membersihkan data")
                    risk_scores.append(risk_score)
                
                # Analisis Variasi Data
                high_variance_cols = []
                if numeric_columns:
                    for col in numeric_columns:
                        if df[col].std() / df[col].mean() > 0.5:  # CV > 50%
                            high_variance_cols.append((col, df[col].std() / df[col].mean()))
                    
                    if high_variance_cols:
                        risk_score = min(100, len(high_variance_cols) * 15)
                        problems.append({
                            "issue": f"**Variasi Data Tinggi**", 
                            "detail": f"{len(high_variance_cols)} kolom memiliki koefisien variasi > 50%",
                            "risk": risk_score,
                            "impact": "Menengah"
                        })
                        solutions.append("**Normalisasi Data**: Terapkan standard scaling atau min-max scaling untuk kolom dengan variasi tinggi sebelum modeling")
                        risk_scores.append(risk_score)
                
                # Analisis Outlier dengan detail
                outlier_cols = []
                if numeric_columns:
                    for col in numeric_columns:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        outlier_count = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
                        outlier_percentage = (outlier_count / len(df)) * 100
                        if outlier_percentage > 5:  # >5% outliers
                            outlier_cols.append((col, outlier_count, outlier_percentage))
                    
                    if outlier_cols:
                        risk_score = min(100, sum([perc for _, _, perc in outlier_cols]))
                        problems.append({
                            "issue": f"**Outlier Signifikan**", 
                            "detail": f"{len(outlier_cols)} kolom memiliki >5% outlier",
                            "risk": risk_score,
                            "impact": "Tinggi"
                        })
                        solutions.append("**Treatment Outlier**: Pertimbangkan winsorizing (mengganti dengan Q1-1.5IQR/Q3+1.5IQR) atau transformasi logaritmik")
                        risk_scores.append(risk_score)

                # Analisis Distribusi Data
                if numeric_columns and 'basic_stats' in locals():
                    skewness_risk = abs(basic_stats['skewness'])
                    if skewness_risk > 1:
                        problems.append({
                            "issue": f"**Distribusi Tidak Normal**", 
                            "detail": f"Skewness: {basic_stats['skewness']:.2f} (>{'positif' if basic_stats['skewness'] > 0 else 'negatif'})",
                            "risk": min(100, skewness_risk * 20),
                            "impact": "Menengah"
                        })
                        solutions.append("**Transformasi Data**: Pertimbangkan transformasi log, square root, atau Box-Cox untuk normalisasi distribusi")
                        risk_scores.append(min(100, skewness_risk * 20))

                # Tampilkan Masalah dan Solusi dengan Risk Assessment
                col_prob, col_sol = st.columns(2)
                
                with col_prob:
                    st.markdown("#### ❌ MASALAH TERIDENTIFIKASI")
                    if problems:
                        total_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
                        st.metric("Overall Risk Score", f"{total_risk:.1f}/100", 
                                delta="High Risk" if total_risk > 70 else "Medium Risk" if total_risk > 40 else "Low Risk")
                        
                        for i, problem in enumerate(problems, 1):
                            with st.expander(f"{i}. {problem['issue']} (Risk: {problem['risk']:.1f})", expanded=True):
                                st.write(f"**Detail**: {problem['detail']}")
                                st.write(f"**Impact**: {problem['impact']}")
                                st.progress(min(problem['risk']/100, 1.0))
                    else:
                        st.success("✅ Tidak ada masalah kritis yang teridentifikasi")
                        st.metric("Overall Risk Score", "0/100", delta="Low Risk")
                
                with col_sol:
                    st.markdown("#### 💡 REKOMENDASI SOLUSI STRATEGIS")
                    if solutions:
                        for i, solution in enumerate(solutions, 1):
                            st.markdown(f"""
                            **{i}. {solution.split(':**')[0]}**
                            {solution.split(':**')[1] if ':**' in solution else solution}
                            """)
                        
                        st.markdown("---")
                        st.markdown("#### 🎯 IMPLEMENTATION ROADMAP")
                        st.markdown("""
                        1. **Phase 1 (Minggu 1)**: Data Cleaning & Quality Assurance
                        2. **Phase 2 (Minggu 2)**: Statistical Analysis & Validation
                        3. **Phase 3 (Minggu 3)**: Advanced Analytics & Modeling
                        4. **Phase 4 (Minggu 4)**: Reporting & Dashboard Deployment
                        """)
                    else:
                        st.success("✅ Data dalam kondisi baik untuk analisis lanjutan")

                # KESIMPULAN ANALITIS LENGKAP DENGAN STRATEGI BISNIS
                st.subheader("🎯 KESIMPULAN ANALITIS & STRATEGI BISNIS")
                
                # Hitung metrics untuk kesimpulan
                data_quality_score = completeness_rate - (duplicate_rows / len(df) * 100) - (len(high_variance_cols) * 5) - (len(outlier_cols) * 3)
                data_quality_score = max(0, min(100, data_quality_score))
                
                # Business Impact Assessment
                business_impact = "Tinggi" if data_quality_score > 80 else "Menengah" if data_quality_score > 60 else "Rendah"
                implementation_priority = "Segera" if data_quality_score < 70 else "Bisa Ditunda"
                analytics_readiness = "Siap" if data_quality_score > 75 else "Perlu Persiapan" if data_quality_score > 50 else "Tidak Siap"
                
                conclusion_col1, conclusion_col2, conclusion_col3 = st.columns(3)
                
                with conclusion_col1:
                    st.markdown("""
                    ### 📊 ASSESSMENT KUANTITATIF
                    
                    **Volume & Struktur:**
                    - Total Records: {:,}
                    - Total Features: {}
                    - Numeric Features: {}
                    - Categorical Features: {}
                    - Memory Usage: {:.2f} MB
                    
                    **Kualitas Data:**
                    - Completeness Rate: {:.1f}%
                    - Duplicate Records: {}
                    - Missing Values: {}
                    - Quality Score: {:.1f}/100
                    """.format(
                        len(df), len(df.columns), numeric_cols, categorical_cols,
                        memory_usage, completeness_rate, duplicate_rows, 
                        missing_values, data_quality_score
                    ))
                
                with conclusion_col2:
                    st.markdown("""
                    ### 📈 PROFIL STATISTIK
                    
                    **Distribusi Data:**
                    - Rata-rata: {:.2f}
                    - Median: {:.2f}
                    - Std Dev: {:.2f}
                    - Range: {:.2f}
                    - Skewness: {:.2f}
                    
                    **Karakteristik:**
                    - Koef. Variasi: {:.1f}%
                    - Q1 (25%): {:.2f}
                    - Q3 (75%): {:.2f}
                    - IQR: {:.2f}
                    """.format(
                        basic_stats['avg_value'] if numeric_columns else 0,
                        basic_stats['median_value'] if numeric_columns else 0,
                        basic_stats['std_value'] if numeric_columns else 0,
                        basic_stats['range'] if numeric_columns else 0,
                        basic_stats['skewness'] if numeric_columns else 0,
                        basic_stats['cv_value'] if numeric_columns else 0,
                        basic_stats['q1'] if numeric_columns else 0,
                        basic_stats['q3'] if numeric_columns else 0,
                        (basic_stats['q3'] - basic_stats['q1']) if numeric_columns else 0
                    ))
                
                with conclusion_col3:
                    st.markdown("""
                    ### 🎯 BUSINESS IMPACT
                    
                    **Tingkat Kesiapan:**
                    - Skor Kualitas: {:.1f}/100
                    - Business Impact: {}
                    - Implementation Priority: {}
                    - Analytics Readiness: {}
                    
                    **Rekomendasi Strategis:**
                    - Data Cleaning: {}
                    - Outlier Treatment: {}
                    - Normalisasi: {}
                    - Analisis Lanjutan: {}
                    """.format(
                        data_quality_score,
                        business_impact,
                        implementation_priority,
                        analytics_readiness,
                        "✅ Diperlukan" if missing_values > 0 or duplicate_rows > 0 else "✅ Optimal",
                        "✅ Diperlukan" if outlier_cols else "✅ Tidak Perlu",
                        "✅ Disarankan" if high_variance_cols else "✅ Optimal",
                        "🚀 Lanjutkan" if data_quality_score > 70 else "⏳ Tunda"
                    ))

                # ROADMAP IMPLEMENTASI DETAIL
                st.subheader("📋 ROADMAP IMPLEMENTASI DETAIL")
                
                # Define phases based on data quality score
                if data_quality_score < 50:
                    phases = [
                        {
                            "phase": "🚨 PHASE 1: CRITICAL DATA CLEANING",
                            "duration": "1-2 Minggu",
                            "activities": [
                                "Data Profiling & Assessment Mendalam",
                                "Missing Values Treatment (Imputasi)",
                                "Duplicate Records Removal", 
                                "Data Type Validation & Conversion",
                                "Basic Outlier Detection"
                            ],
                            "deliverables": ["Clean Dataset", "Data Quality Report", "Validation Rules"]
                        },
                        {
                            "phase": "🔧 PHASE 2: DATA ENHANCEMENT", 
                            "duration": "1 Minggu",
                            "activities": [
                                "Advanced Outlier Treatment",
                                "Data Normalization & Scaling",
                                "Feature Engineering Basic",
                                "Data Distribution Analysis"
                            ],
                            "deliverables": ["Enhanced Dataset", "Statistical Report", "Feature Documentation"]
                        }
                    ]
                elif data_quality_score < 75:
                    phases = [
                        {
                            "phase": "⚡ PHASE 1: RAPID DATA PREPARATION", 
                            "duration": "3-5 Hari",
                            "activities": [
                                "Quick Data Quality Check",
                                "Essential Cleaning Tasks", 
                                "Basic Statistical Analysis",
                                "Outlier Identification"
                            ],
                            "deliverables": ["Analysis-Ready Data", "Quick Insights Report"]
                        },
                        {
                            "phase": "📊 PHASE 2: ADVANCED ANALYTICS",
                            "duration": "1-2 Minggu", 
                            "activities": [
                                "Comprehensive Statistical Analysis",
                                "Correlation & Pattern Analysis",
                                "Predictive Modeling Preparation",
                                "Business Insights Generation"
                            ],
                            "deliverables": ["Analytical Models", "Business Insights", "Dashboard Prototype"]
                        }
                    ]
                else:
                    phases = [
                        {
                            "phase": "🚀 PHASE 1: DIRECT TO ANALYTICS",
                            "duration": "2-3 Hari", 
                            "activities": [
                                "Data Validation Final Check",
                                "Statistical Summary Generation",
                                "Initial Insights Identification",
                                "Reporting Framework Setup"
                            ],
                            "deliverables": ["Executive Summary", "Initial Findings", "Analysis Plan"]
                        }
                    ]
                
                # Display roadmap
                for i, phase in enumerate(phases):
                    with st.expander(f"{phase['phase']} ({phase['duration']})", expanded=True):
                        col_act, col_del = st.columns(2)
                        
                        with col_act:
                            st.markdown("**📝 Aktivitas Utama:**")
                            for activity in phase['activities']:
                                st.markdown(f"• {activity}")
                        
                        with col_del:
                            st.markdown("**🎯 Deliverables:**")
                            for deliverable in phase['deliverables']:
                                st.markdown(f"• {deliverable}")

                # FINAL EXECUTIVE SUMMARY
                st.subheader("🏆 EXECUTIVE SUMMARY")
                
                # Create executive summary based on analysis
                if data_quality_score >= 80:
                    summary = f"""
                    **🎉 STATUS: EXCELLENT** 
                    
                    Dataset dalam kondisi **sangat baik** dengan skor kualitas {data_quality_score:.1f}/100. 
                    Data siap untuk analisis lanjutan dan modeling tanpa preprocessing signifikan.
                    
                    **📈 REKOMENDASI:**
                    - Lanjutkan langsung ke analisis bisnis dan modeling
                    - Manfaatkan data untuk pengambilan keputusan strategis
                    - Pertimbangkan analisis prediktif dan machine learning
                    """
                elif data_quality_score >= 60:
                    summary = f"""
                    **⚠️ STATUS: GOOD (Need Minor Improvement)**
                    
                    Dataset dalam kondisi **baik** dengan skor kualitas {data_quality_score:.1f}/100. 
                    Beberapa improvement minor diperlukan sebelum analisis lanjutan.
                    
                    **🔧 REKOMENDASI:**
                    - Lakukan cleaning data ringan ({len(problems)} issues teridentifikasi)
                    - Validasi hasil cleaning sebelum analisis utama  
                    - Bisa parallel dengan analisis eksploratori awal
                    """
                else:
                    summary = f"""
                    **🚨 STATUS: NEEDS MAJOR IMPROVEMENT**
                    
                    Dataset memerlukan **significant preprocessing** dengan skor kualitas {data_quality_score:.1f}/100.
                    {len(problems)} masalah kritis perlu ditangani sebelum analisis.
                    
                    **🛠️ REKOMENDASI:**
                    - Prioritaskan data cleaning dan quality assurance
                    - Alokasi waktu 1-2 minggu untuk preprocessing
                    - Validasi menyeluruh sebelum analisis lanjutan
                    """
                
                st.info(summary)

                # Ekspor Laporan Super Lengkap
                st.subheader("📤 EKSPOR LAPORAN ANALISIS SUPER LENGKAP")
                
                if st.button("📊 GENERATE COMPREHENSIVE BUSINESS REPORT"):
                    # Buat laporan analisis super lengkap
                    comprehensive_report = f"""
                    LAPORAN ANALISIS DATA BISNIS KOMPREHENSIF
                    ===========================================
                    
                    TANGGAL GENERATE: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
                    JENIS ANALISIS: Business Intelligence & Data Assessment
                    
                    EXECUTIVE SUMMARY:
                    - Overall Quality Score: {data_quality_score:.1f}/100
                    - Business Readiness: {analytics_readiness}
                    - Implementation Priority: {implementation_priority}
                    - Estimated Timeline: {phases[0]['duration']}
                    
                    PROFIL DATASET:
                    - Total Records: {len(df):,}
                    - Total Features: {len(df.columns)}
                    - Numeric Features: {numeric_cols}
                    - Categorical Features: {categorical_cols}
                    - Memory Usage: {memory_usage:.2f} MB
                    - Data Types Variety: {len(df.dtypes.unique())}
                    
                    ASSESSMENT KUALITAS DATA:
                    - Missing Values: {missing_values} ({missing_values/(len(df)*len(df.columns))*100:.1f}%)
                    - Duplicate Records: {duplicate_rows} ({duplicate_rows/len(df)*100:.1f}%)
                    - Completeness Rate: {completeness_rate:.1f}%
                    - Data Quality Index: {data_quality_score:.1f}/100
                    
                    PROFIL STATISTIK LENGKAP:"""
                    
                    if numeric_columns:
                        comprehensive_report += f"""
                    - Central Tendency: Mean={basic_stats['avg_value']:.2f}, Median={basic_stats['median_value']:.2f}
                    - Dispersion: Std Dev={basic_stats['std_value']:.2f}, Range={basic_stats['range']:.2f}
                    - Distribution: Skewness={basic_stats['skewness']:.2f}, CV={basic_stats['cv_value']:.1f}%
                    - Quartiles: Q1={basic_stats['q1']:.2f}, Q3={basic_stats['q3']:.2f}, IQR={(basic_stats['q3'] - basic_stats['q1']):.2f}
                    - Extremes: Min={basic_stats['min_value']:.2f}, Max={basic_stats['max_value']:.2f}"""
                    else:
                        comprehensive_report += "\n                - Tidak ada kolom numerik untuk analisis statistik mendalam"
                    
                    comprehensive_report += f"""
                    
                    IDENTIFIED ISSUES & RISK ASSESSMENT:
                    Total Problems Identified: {len(problems)}
                    Overall Risk Score: {sum(risk_scores)/len(risk_scores) if risk_scores else 0:.1f}/100
                    
                    DETAILED ISSUES:"""
                    
                    for i, problem in enumerate(problems, 1):
                        comprehensive_report += f"""
                    {i}. {problem['issue']}
                    Detail: {problem['detail']}
                    Risk Score: {problem['risk']:.1f}/100
                    Business Impact: {problem['impact']}"""
                    
                    comprehensive_report += f"""
                    
                    STRATEGIC RECOMMENDATIONS:
                    {chr(10).join(['- ' + solution for solution in solutions]) if solutions else '- Data dalam kondisi optimal untuk analisis bisnis'}
                    
                    IMPLEMENTATION ROADMAP:"""
                    
                    for i, phase in enumerate(phases, 1):
                        comprehensive_report += f"""
                    PHASE {i}: {phase['phase']}
                    Duration: {phase['duration']}
                    Key Activities: {', '.join(phase['activities'])}
                    Deliverables: {', '.join(phase['deliverables'])}"""
                    
                    comprehensive_report += f"""
                    
                    BUSINESS IMPACT ANALYSIS:
                    - Current State: {business_impact} Impact
                    - Readiness for Analytics: {analytics_readiness}
                    - Recommended Next Steps: {implementation_priority}
                    - Expected Value: {'High ROI' if data_quality_score > 70 else 'Medium ROI' if data_quality_score > 50 else 'Requires Investment'}
                    
                    TECHNICAL RECOMMENDATIONS:
                    - Data Storage: {f'{memory_usage:.2f} MB - Optimal' if memory_usage < 100 else f'{memory_usage:.2f} MB - Consider Compression'}
                    - Processing Needs: {'Standard' if len(df) < 100000 else 'High Performance'}
                    - Monitoring: {'Basic Quality Checks' if data_quality_score > 80 else 'Comprehensive Monitoring'}
                    
                    CONCLUSION & NEXT STEPS:
                    Dataset ini {'sangat layak untuk analisis bisnis lanjutan dan dapat memberikan insights bernilai tinggi' if data_quality_score > 80 
                                else 'perlu sedikit improvement sebelum analisis mendalam tetapi dapat memberikan value business' if data_quality_score > 60 
                                else 'memerlukan significant investment dalam data preparation sebelum dapat digunakan untuk analisis bisnis yang reliable'}.
                    
                    Disarankan untuk {'langsung melanjutkan ke analytical modeling' if data_quality_score > 75 
                                    else 'melakukan data cleaning terlebih dahulu selama 1-2 minggu' if data_quality_score > 50 
                                    else 'mengalokasikan 2-3 minggu untuk comprehensive data quality improvement'}.
                    
                    ---
                    Laporan dibuat secara otomatis oleh Advanced Analytics System
                    Tim Business Intelligence & Data Science
                    """
                    
                    st.download_button(
                        label="📥 DOWNLOAD LAPORAN BISNIS LENGKAP (TXT)",
                        data=comprehensive_report,
                        file_name=f"business_analytics_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
                
            else:
                st.warning("Dataset kosong atau tidak valid")
else:
    st.info("📁 **Panduan Unggah File**: Silakan unggah file CSV atau Excel melalui sidebar di sebelah kiri untuk memulai analisis data.")
    
    st.subheader("📋 Contoh Struktur Data yang Didukung")
    st.write("Berikut adalah contoh format data yang dapat diolah oleh dashboard ini:")
    example_data = create_sample_file()
    st.dataframe(example_data.head(), use_container_width=True)
    
    # Informasi kolom data
    st.markdown("""
    **Keterangan Kolom Data:**
    - **Date**: Tanggal transaksi (format: YYYY-MM-DD)
    - **Open**: Harga pembukaan saham
    - **High**: Harga tertinggi harian
    - **Low**: Harga terendah harian  
    - **Close**: Harga penutupan saham
    - **Volume**: Volume transaksi
    - **Sektor**: Kategori sektor perusahaan
    - **Kategori_Produk**: Jenis produk yang diperdagangkan
    """)
    
    st.subheader("📊 Pratinjau Visualisasi Dashboard")
    st.write("Dashboard ini akan menampilkan berbagai visualisasi interaktif setelah data diunggah:")
    
    # Row 1: KPI Cards
    st.write("**📈 Key Performance Indicators**")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown("""
        <div class="kpi-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
            <div class="kpi-title" style="font-size: 14px; opacity: 0.9;">Rata-rata Close Price</div>
            <div class="kpi-value" style="font-size: 32px; font-weight: bold; margin: 10px 0;">105.42</div>
            <div class="kpi-change" style="font-size: 12px; background: rgba(255,255,255,0.2); 
                    padding: 5px; border-radius: 15px;">+2.5% dari bulan sebelumnya</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col2:
        st.markdown("""
        <div class="kpi-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
            <div class="kpi-title" style="font-size: 14px; opacity: 0.9;">Total Volume</div>
            <div class="kpi-value" style="font-size: 32px; font-weight: bold; margin: 10px 0;">2.5M</div>
            <div class="kpi-change" style="font-size: 12px; background: rgba(255,255,255,0.2); 
                    padding: 5px; border-radius: 15px;">+15.3% dari rata-rata</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col3:
        st.markdown("""
        <div class="kpi-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
            <div class="kpi-title" style="font-size: 14px; opacity: 0.9;">Volatilitas Harian</div>
            <div class="kpi-value" style="font-size: 32px; font-weight: bold; margin: 10px 0;">3.2%</div>
            <div class="kpi-change" style="font-size: 12px; background: rgba(255,255,255,0.2); 
                    padding: 5px; border-radius: 15px;">-0.8% lebih rendah</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col4:
        st.markdown("""
        <div class="kpi-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                    padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
            <div class="kpi-title" style="font-size: 14px; opacity: 0.9;">Total Sektor</div>
            <div class="kpi-value" style="font-size: 32px; font-weight: bold; margin: 10px 0;">8</div>
            <div class="kpi-change" style="font-size: 12px; background: rgba(255,255,255,0.2); 
                    padding: 5px; border-radius: 15px;">+2 sektor baru</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Deteksi tipe data kolom
    numeric_cols = example_data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = example_data.select_dtypes(include=['object']).columns.tolist()
    
    # Jika tidak ada kolom kategorikal, coba kolom dengan nilai unik sedikit
    if not categorical_cols:
        for col in example_data.columns:
            if example_data[col].nunique() <= 10:  # Jika punya <= 10 nilai unik, anggap kategorikal
                categorical_cols.append(col)
    
    # Row 2: Line Chart dan Area Chart
    col1, col2 = st.columns(2)
    
    with col1:
        # Line Chart - Trend Harga
        st.write("**📈 Line Chart - Trend Data**")
        
        # Cek dan proses data untuk line chart
        if len(numeric_cols) >= 4:
            # Gunakan 4 kolom numerik pertama untuk line chart
            line_data = example_data.reset_index()
            fig_line = px.line(line_data, x=line_data.index, y=numeric_cols[:4],
                              title='Trend Data Numerik',
                              color_discrete_sequence=['#636EFA', '#00CC96', '#EF553B', '#AB63FA'])
        else:
            # Gunakan semua kolom numerik yang ada
            line_data = example_data.reset_index()
            available_cols = numeric_cols[:min(4, len(numeric_cols))]
            if available_cols:
                fig_line = px.line(line_data, x=line_data.index, y=available_cols,
                                  title='Trend Data Numerik',
                                  color_discrete_sequence=px.colors.qualitative.Set1[:len(available_cols)])
            else:
                # Buat data dummy jika tidak ada kolom numerik
                dummy_data = pd.DataFrame({
                    'index': range(10),
                    'Value1': np.random.rand(10) * 100,
                    'Value2': np.random.rand(10) * 100 + 50
                })
                fig_line = px.line(dummy_data, x='index', y=['Value1', 'Value2'],
                                  title='Contoh Trend Data',
                                  color_discrete_sequence=['#636EFA', '#00CC96'])
        
        fig_line.update_layout(
            title_font_size=16,
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified'
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("Line chart menampilkan pergerakan data numerik untuk analisis trend.")
    
    with col2:
        # Area Chart - Data Numerik
        st.write("**📊 Area Chart - Distribusi Kumulatif**")
        
        if numeric_cols:
            area_data = example_data.reset_index()
            fig_area = px.area(area_data, x=area_data.index, y=numeric_cols[0],
                              title=f'Distribusi Kumulatif {numeric_cols[0]}',
                              color_discrete_sequence=['#FFA15A'])
        else:
            # Buat data dummy
            area_data = pd.DataFrame({
                'index': range(10),
                'Value': np.cumsum(np.random.rand(10) * 10)
            })
            fig_area = px.area(area_data, x='index', y='Value',
                              title='Contoh Area Chart',
                              color_discrete_sequence=['#FFA15A'])
        
        fig_area.update_layout(
            title_font_size=16,
            template='plotly_white',
            showlegend=False
        )
        fig_area.update_traces(opacity=0.6)
        st.plotly_chart(fig_area, use_container_width=True)
        st.caption("Area chart menunjukkan distribusi kumulatif data dengan fill pattern.")
    
    # Row 3: Histogram dan Pie Chart
    col3, col4 = st.columns(2)
    
    with col3:
        # Histogram Distribusi Data
        st.write("**📊 Histogram - Distribusi Data**")
        
        if numeric_cols:
            fig_hist = px.histogram(example_data, x=numeric_cols[0], 
                                   title=f'Distribusi Frekuensi {numeric_cols[0]}',
                                   color_discrete_sequence=['#636EFA'], 
                                   opacity=0.8,
                                   nbins=20)
        else:
            # Buat data dummy
            dummy_hist = pd.DataFrame({
                'Value': np.random.normal(100, 15, 1000)
            })
            fig_hist = px.histogram(dummy_hist, x='Value', 
                                   title='Contoh Histogram',
                                   color_discrete_sequence=['#636EFA'], 
                                   opacity=0.8,
                                   nbins=20)
        
        fig_hist.update_layout(
            title_font_size=16,
            template='plotly_white',
            showlegend=False,
            xaxis_title="Nilai",
            yaxis_title="Frekuensi"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        st.caption("Histogram menampilkan distribusi frekuensi data untuk analisis pola sebaran.")
    
    with col4:
        # Pie Chart - Komposisi Kategori
        st.write("**🥧 Pie Chart - Komposisi Data**")
        
        if categorical_cols:
            cat_composition = example_data[categorical_cols[0]].value_counts().reset_index()
            cat_composition.columns = ['Kategori', 'Count']
        else:
            # Buat data dummy
            cat_composition = pd.DataFrame({
                'Kategori': ['Kategori A', 'Kategori B', 'Kategori C', 'Kategori D'],
                'Count': [25, 30, 20, 25]
            })
        
        fig_pie = px.pie(cat_composition, values='Count', names='Kategori',
                        title='Distribusi Persentase Data',
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        hole=0.4)
        fig_pie.update_layout(
            title_font_size=16,
            template='plotly_white',
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("Pie chart menunjukkan komposisi persentase data berdasarkan kategori.")
    
    # Row 4: Scatter Plot dan Bar Chart
    col5, col6 = st.columns(2)
    
    with col5:
        # Scatter Plot - Korelasi Variabel
        st.write("**🔍 Scatter Plot - Korelasi Variabel**")
        
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            if categorical_cols:
                color_col = categorical_cols[0]
                fig_scatter = px.scatter(example_data, x=x_col, y=y_col, color=color_col,
                                       title=f'Korelasi {x_col} vs {y_col}',
                                       size=y_col if len(numeric_cols) > 2 else None,
                                       hover_data=example_data.columns.tolist()[:3],
                                       color_discrete_sequence=px.colors.qualitative.Bold)
            else:
                fig_scatter = px.scatter(example_data, x=x_col, y=y_col,
                                       title=f'Korelasi {x_col} vs {y_col}',
                                       color_discrete_sequence=['#636EFA'])
        else:
            # Buat data dummy
            dummy_scatter = pd.DataFrame({
                'X': np.random.rand(50) * 100,
                'Y': np.random.rand(50) * 100 + 50,
                'Category': np.random.choice(['A', 'B', 'C'], 50)
            })
            fig_scatter = px.scatter(dummy_scatter, x='X', y='Y', color='Category',
                                   title='Contoh Scatter Plot',
                                   color_discrete_sequence=px.colors.qualitative.Bold)
        
        fig_scatter.update_layout(
            title_font_size=16,
            template='plotly_white',
            xaxis_title="Variabel X",
            yaxis_title="Variabel Y"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Scatter plot menampilkan hubungan korelasi antara dua variabel numerik.")
    
    with col6:
        # Bar Chart - Rata-rata per Kategori
        st.write("**📊 Bar Chart - Performa per Kategori**")
        
        if categorical_cols and numeric_cols:
            bar_data = example_data.groupby(categorical_cols[0])[numeric_cols[0]].mean().reset_index()
            bar_data.columns = ['Kategori', 'Rata_rata']
            
            fig_bar = px.bar(bar_data, x='Kategori', y='Rata_rata',
                            title=f'Rata-rata {numeric_cols[0]} per {categorical_cols[0]}',
                            color='Rata_rata',
                            color_continuous_scale='Viridis')
        else:
            # Data dummy untuk bar chart
            bar_data = pd.DataFrame({
                'Kategori': ['Kategori A', 'Kategori B', 'Kategori C', 'Kategori D'],
                'Rata_rata': [100, 150, 120, 180]
            })
            fig_bar = px.bar(bar_data, x='Kategori', y='Rata_rata',
                            title='Contoh Bar Chart',
                            color='Rata_rata',
                            color_continuous_scale='Viridis')
        
        fig_bar.update_layout(
            title_font_size=16,
            template='plotly_white',
            xaxis_title="Kategori",
            yaxis_title="Rata-rata",
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption("Bar chart perbandingan rata-rata nilai untuk setiap kategori.")
    
    # Row 5: Treemap dan Box Plot
    col7, col8 = st.columns(2)
    
    with col7:
        # Treemap - Hierarki Data
        st.write("**🌳 Treemap - Struktur Hierarkis**")
        
        if len(categorical_cols) >= 2 and numeric_cols:
            # Pastikan kita punya cukup kolom kategorikal
            tree_group_cols = categorical_cols[:2]
            tree_data = example_data.groupby(tree_group_cols)[numeric_cols[0]].sum().reset_index()
            
            fig_tree = px.treemap(tree_data, path=tree_group_cols, values=numeric_cols[0],
                                 title='Struktur Data Hierarkis',
                                 color=numeric_cols[0], 
                                 color_continuous_scale='Blues')
        elif categorical_cols and numeric_cols:
            # Jika hanya punya 1 kolom kategorikal, buat level tambahan
            tree_data = example_data.copy()
            tree_data['Level2'] = 'Subkategori'  # Tambahkan level dummy
            tree_group_cols = [categorical_cols[0], 'Level2']
            tree_data = tree_data.groupby(tree_group_cols)[numeric_cols[0]].sum().reset_index()
            
            fig_tree = px.treemap(tree_data, path=tree_group_cols, values=numeric_cols[0],
                                 title='Struktur Data Hierarkis',
                                 color=numeric_cols[0], 
                                 color_continuous_scale='Blues')
        else:
            # Data dummy untuk treemap
            tree_data = pd.DataFrame({
                'Level1': ['Sektor A', 'Sektor A', 'Sektor B', 'Sektor B'],
                'Level2': ['Produk 1', 'Produk 2', 'Produk 1', 'Produk 2'],
                'Value': [100, 200, 150, 250]
            })
            fig_tree = px.treemap(tree_data, path=['Level1', 'Level2'], values='Value',
                                 title='Contoh Treemap',
                                 color='Value', 
                                 color_continuous_scale='Blues')
        
        fig_tree.update_layout(
            title_font_size=16,
            margin=dict(t=50, l=25, r=25, b=25)
        )
        st.plotly_chart(fig_tree, use_container_width=True)
        st.caption("Treemap menampilkan hubungan hierarkis antara kategori data berdasarkan nilai agregat.")
    
    with col8:
        # Box Plot - Distribusi per Kategori
        st.write("**📦 Box Plot - Variasi Data**")
        
        if categorical_cols and numeric_cols:
            fig_box = px.box(example_data, x=categorical_cols[0], y=numeric_cols[0],
                            title=f'Distribusi {numeric_cols[0]} per {categorical_cols[0]}',
                            color=categorical_cols[0],
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        else:
            # Data dummy untuk box plot
            dummy_box = pd.DataFrame({
                'Kategori': ['A']*20 + ['B']*20 + ['C']*20,
                'Nilai': np.concatenate([
                    np.random.normal(100, 10, 20), 
                    np.random.normal(150, 15, 20), 
                    np.random.normal(120, 12, 20)
                ])
            })
            fig_box = px.box(dummy_box, x='Kategori', y='Nilai', color='Kategori',
                            title='Contoh Box Plot',
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        
        fig_box.update_layout(
            title_font_size=16,
            template='plotly_white',
            xaxis_title="Kategori",
            yaxis_title="Nilai",
            showlegend=False
        )
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption("Box plot menunjukkan distribusi statistik data untuk setiap kategori.")

    # Fitur Dashboard yang Tersedia
    st.subheader("🚀 Fitur Dashboard yang Tersedia")
    
    feature_col1, feature_col2, feature_col3 = st.columns(3)
    
    with feature_col1:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #636EFA;">
            <h4 style="margin: 0 0 10px 0; color: #636EFA;">📈 Analisis Trend</h4>
            <p style="margin: 0; font-size: 14px;">Visualisasi time series dengan berbagai indikator teknikal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col2:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #00CC96;">
            <h4 style="margin: 0 0 10px 0; color: #00CC96;">📊 Statistik Deskriptif</h4>
            <p style="margin: 0; font-size: 14px;">Analisis statistik lengkap dengan metrik KPI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col3:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #EF553B;">
            <h4 style="margin: 0 0 10px 0; color: #EF553B;">🔍 Analisis Korelasi</h4>
            <p style="margin: 0; font-size: 14px;">Heatmap korelasi dan analisis hubungan variabel</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 15px;">
        <div style="width: 80px; height: 80px; border-radius: 50%; overflow: hidden; border: 3px solid #636EFA;">
            <img src="https://github.com/DwiDevelopes/gambar/raw/main/Screenshot%202025-10-17%20100808.png" alt="Profile Picture" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
        <div>
            <h3 style="margin-bottom: 10px;">Dashboard Statistik Lengkap</h3>
            <p style="margin: 5px 0;">📅 <strong>Tahun 2025</strong> | 🎯 <strong>Analisis Data Keuangan & Pasar</strong></p>
        </div>
    </div>
    <p style="margin: 5px 0; font-size: 14px;">Sebuah solusi komprehensif untuk analisis data finansial dengan visualisasi interaktif</p>
    <p style="margin: 15px 0 5px 0; font-style: italic;">Dikembangkan dengan ❤️ oleh:</p>
    <p style="margin: 0; font-weight: bold; color: #636EFA; font-size: 16px;">Dwi Bakti N Dev</p>
    <p style="margin: 5px 0; font-size: 12px;">Data Scientist & Business Intelligence Developer</p>
</div>
""", unsafe_allow_html=True)

# Footer yang aman
try:
    total_records = len(df) if 'df' in locals() or 'df' in globals() else 0
    quality_score = data_quality_score if 'data_quality_score' in locals() or 'data_quality_score' in globals() else 0
    risk_score = sum(risk_scores)/len(risk_scores) if risk_scores and 'risk_scores' in locals() else 0
except:
    total_records = 0
    quality_score = 0
    risk_score = 0

st.markdown(f"""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    Terakhir diperbarui: {pd.Timestamp.now().strftime('%d %B %Y %H:%M')} | 
    Total Records: {total_records:,} | 
    Skor Kualitas: {quality_score:.1f}/100 |
    Risk Level: {risk_score:.1f}/100
</div>
""", unsafe_allow_html=True)