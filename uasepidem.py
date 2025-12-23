# =========================
# DASHBOARD TBC INDONESIA — STREAMLIT (DEPLOY-SAFE)
# =========================

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import folium
from streamlit_folium import st_folium

import plotly.express as px

import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import chi2


# =========================
# CONFIG (WAJIB PALING ATAS)
# =========================
st.set_page_config(
    page_title="Dashboard Epidemiologi TBC",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================
# PATH (DEPLOY SAFE)
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

PATH_EPI2 = DATA_DIR / "epi2_ukuran.xlsx"
PATH_MODEL = DATA_DIR / "epi1_modeling.xlsx"
PATH_GEO = DATA_DIR / "indonesia.geojson"


# =========================
# HELPERS
# =========================
def fmt_int(x):
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return "-"

def fmt_float(x, d=1):
    try:
        return f"{float(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"

def fmt_p(x):
    try:
        x = float(x)
        return "< 0.001" if x < 0.001 else f"{x:.4f}"
    except Exception:
        return "-"

def clean_colnames(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.lower()
    return df

def clean_prov(s: str) -> str:
    s = str(s).strip().upper()
    s = s.replace(".", "").replace(",", "")
    s = " ".join(s.split())
    s = s.replace("DI YOGYAKARTA", "DAERAH ISTIMEWA YOGYAKARTA")
    s = s.replace("KEP BANGKA BELITUNG", "KEPULAUAN BANGKA BELITUNG")
    s = s.replace("BANGKA BELITUNG", "KEPULAUAN BANGKA BELITUNG")
    s = s.replace("KEP RIAU", "KEPULAUAN RIAU")
    return s


# =========================
# LOADERS (ANTI RUSAK)
# =========================
@st.cache_data(show_spinner=False)
def load_epi2(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")

    df = pd.read_excel(path)
    df = clean_colnames(df)

    # rename paling umum
    rename_map = {
        "provinsii": "provinsi",
        "provinsi": "provinsi",
        "populasi": "populasi",
        "jumlah_tbc": "jumlah_tbc",
        "jumlah tbc": "jumlah_tbc",
        "jumlah_tbc ": "jumlah_tbc",
        "jumlah_tbc\t": "jumlah_tbc",
        "jumlah_tbc\n": "jumlah_tbc",
        "jumlah_tbc\r": "jumlah_tbc",
        "jumlah_kasus_tbc": "jumlah_tbc",
        "jumlah kasus tbc": "jumlah_tbc",
        "kepadatan": "kepadatan",
        "kelompok_kep": "kelompok_kep",
        "kelompok kep": "kelompok_kep",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    required = ["provinsi", "populasi", "jumlah_tbc", "kepadatan"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {missing}. Kolom terbaca: {list(df.columns)}")

    df["provinsi"] = df["provinsi"].astype(str).str.strip()

    for c in ["populasi", "jumlah_tbc", "kepadatan"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["provinsi", "populasi", "jumlah_tbc", "kepadatan"]).copy()
    df["non_tbc"] = df["populasi"] - df["jumlah_tbc"]
    df["rate_100k"] = (df["jumlah_tbc"] / df["populasi"]) * 100000
    df["prov_clean"] = df["provinsi"].map(clean_prov)

    return df

@st.cache_data(show_spinner=False)
def load_model(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")

    df = pd.read_excel(path)
    df = df.copy()

    # standar kolom
    rename = {
        "Provinsi": "provinsi",
        "provinsi": "provinsi",
        "Y": "y",
        "X1": "x1",
        "X2": "x2",
        "X3": "x3",
        "X4": "x4",
        "X5": "x5",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    required = ["provinsi", "y", "x1", "x2", "x3", "x4", "x5"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        # coba “lower” kalau excel-nya lowercase
        df2 = clean_colnames(df)
        df2 = df2.rename(columns={"provinsi": "provinsi", "y": "y", "x1":"x1","x2":"x2","x3":"x3","x4":"x4","x5":"x5"})
        missing2 = [c for c in required if c not in df2.columns]
        if missing2:
            raise ValueError(f"Kolom wajib model tidak ditemukan: {missing}. Kolom terbaca: {list(df.columns)}")
        df = df2

    df["provinsi"] = df["provinsi"].astype(str).str.strip()
    for c in ["y", "x1", "x2", "x3", "x4", "x5"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["y", "x1", "x2", "x3", "x4", "x5"]).copy()

    return df

@st.cache_data(show_spinner=False)
def load_geojson(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    with open(path, "r", encoding="utf-8") as f:
        geo = json.load(f)
    return geo


# =========================
# LOAD DATA (GLOBAL)
# =========================
try:
    epi2 = load_epi2(PATH_EPI2)
except Exception as e:
    st.error("Gagal load epi2_ukuran.xlsx. Pastikan file ada di folder data/ dan kolomnya sesuai.")
    st.exception(e)
    st.stop()

# =========================
# STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Home"

def go(page_name: str):
    st.session_state.page = page_name


# =========================
# CSS (CLEAN + TERANG + HITAM)
# =========================
st.markdown("""
<style>
[data-testid="stHeader"] { background: transparent !important; height: 0px !important; }
[data-testid="stToolbar"] { visibility: hidden !important; height: 0px !important; }
footer { visibility: hidden !important; }
[data-testid="stSidebar"], [data-testid="stSidebarNav"] { display:none !important; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], main, section {
  background:#f2f4f7 !important;
  color:#111111 !important;
}

.block-container{
  max-width: 1400px !important;
  padding-top: 0.8rem !important;
  padding-bottom: 2rem !important;
  padding-left: 1.2rem !important;
  padding-right: 1.2rem !important;
}

.card{
  background:#ffffff !important;
  border:1px solid #e5e7eb !important;
  border-radius:18px !important;
  padding:16px 18px !important;
  box-sizing:border-box;
}
.kpi{
  background:#ffffff !important;
  border:1px solid #e5e7eb !important;
  border-radius:18px !important;
  padding:14px 16px !important;
}
.kpi .label{ color:#6b7280 !important; font-size:0.9rem !important; font-weight:600 !important; }
.kpi .value{ color:#111111 !important; font-size:34px !important; font-weight:800 !important; line-height:1.1 !important; }
.muted{ color:#374151 !important; }

.stButton>button{
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111111 !important;
  padding: 9px 10px;
  font-size: 0.95rem;
  width: 100%;
  white-space: nowrap;
}
.stButton>button:hover{ background:#f3f4f6; }

h1,h2,h3,h4,h5,h6,p,span,div,label,li { color:#111111 !important; }
</style>
""", unsafe_allow_html=True)


# =========================
# TOP TITLE (BIAR GAK KE-POTONG)
# =========================
st.markdown(
    """
    <div class="card">
      <div style="font-size:22px;font-weight:800;line-height:1.1;">Dashboard Epidemiologi TBC</div>
      <div class="muted" style="margin-top:4px;">Indonesia • tingkat provinsi • 2024</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")


# =========================
# NAV 5 SEJAJAR
# =========================
c1, c2, c3, c4, c5 = st.columns(5, gap="small")
with c1:
    st.button("Home", use_container_width=True, on_click=go, args=("Home",))
with c2:
    st.button("Peta Sebaran", use_container_width=True, on_click=go, args=("Peta",))
with c3:
    st.button("Ukuran Epidemiologi", use_container_width=True, on_click=go, args=("Epi",))
with c4:
    st.button("Modeling", use_container_width=True, on_click=go, args=("Model",))
with c5:
    st.button("About", use_container_width=True, on_click=go, args=("About",))

st.write("")


# =========================
# ROUTER
# =========================
page = st.session_state.page


# =========================
# HOME
# =========================
if page == "Home":
    df = epi2.copy()

    total_kasus = float(df["jumlah_tbc"].sum())
    rata_kasus  = float(df["jumlah_tbc"].mean())
    median_kasus = float(df["jumlah_tbc"].median())
    min_kasus = float(df["jumlah_tbc"].min())
    max_kasus = float(df["jumlah_tbc"].max())

    left, right = st.columns([1.4, 1], gap="large")

    with left:
        st.markdown(
            """
            <div class="card">
              <div style="font-size:26px;font-weight:800;margin-bottom:4px;">
                Ringkasan Kasus TBC — Indonesia (2024)
              </div>
              <div class="muted" style="font-size:13px;">
                Analisis agregat tingkat provinsi (cross-sectional). Ukuran frekuensi menggunakan rate per 100.000 penduduk.
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")

        st.markdown(
            f"""
            <div class="card">
              <div class="muted">Total Kasus TBC (2024)</div>
              <div style="font-size:42px;font-weight:900;line-height:1.1;">
                {fmt_int(total_kasus)}
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")
        k1, k2, k3 = st.columns(3, gap="medium")
        with k1:
            st.markdown(
                f"""
                <div class="card">
                  <div class="muted">Rata-rata per Provinsi</div>
                  <div style="font-size:32px;font-weight:800;">{fmt_int(rata_kasus)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with k2:
            st.markdown(
                f"""
                <div class="card">
                  <div class="muted">Median Kasus</div>
                  <div style="font-size:32px;font-weight:800;">{fmt_int(median_kasus)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with k3:
            st.markdown(
                f"""
                <div class="card">
                  <div class="muted">Rentang Kasus</div>
                  <div style="font-size:26px;font-weight:800;">{fmt_int(min_kasus)} – {fmt_int(max_kasus)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")
        top10 = (
            df.sort_values("jumlah_tbc", ascending=False)
              .head(10)
              .sort_values("jumlah_tbc")
        )
        st.markdown(
            """
            <div class="card">
              <div style="font-size:18px;font-weight:700;">Top 10 Provinsi — Kasus TBC Tertinggi</div>
              <div class="muted" style="font-size:13px;">Grafik cepat untuk melihat provinsi dengan beban kasus tertinggi.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.bar_chart(top10.set_index("provinsi")["jumlah_tbc"], height=360)

    with right:
        total_pop = float(df["populasi"].sum())
        rate_indo = (total_kasus / total_pop) * 100000 if total_pop > 0 else np.nan

        st.markdown(
            f"""
            <div class="card">
              <div style="font-size:18px;font-weight:800;margin-bottom:6px;">Catatan Analisis</div>
              <div class="muted" style="font-size:13px;line-height:1.6;">
                <b>Desain:</b> cross-sectional (ekologis, agregat provinsi).<br/>
                <b>Ukuran frekuensi:</b> rate TBC per 100.000 penduduk.<br/>
                <b>Ukuran asosiasi:</b> PR &amp; POR berdasarkan pengelompokan kepadatan penduduk.<br/>
                <b>Modeling:</b> regresi binomial negatif untuk data cacah dengan potensi overdispersi.<br/><br/>
                <b>Ringkasan nasional:</b><br/>
                Total populasi: {fmt_int(total_pop)}<br/>
                Rate nasional: {fmt_float(rate_indo, 1)} per 100.000
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================
# PETA SEBARAN
# =========================
elif page == "Peta":
    df = epi2.copy()

    try:
        geo = load_geojson(PATH_GEO)
    except Exception as e:
        st.error("Gagal load indonesia.geojson. Pastikan file ada di folder data/")
        st.exception(e)
        st.stop()

    # deteksi field nama provinsi di geojson
    props0 = geo["features"][0]["properties"]
    candidate_keys = ["Propinsi", "propinsi", "Provinsi", "provinsi", "NAME_1", "name", "Name", "nama", "NAMA"]
    name_key = next((k for k in candidate_keys if k in props0), None)
    if name_key is None:
        st.error(f"Gak nemu kolom nama provinsi di geojson. Keys contoh: {list(props0.keys())[:25]}")
        st.stop()

    # inject prov_clean ke feature geojson
    for ft in geo["features"]:
        raw_name = ft["properties"].get(name_key, "")
        ft["properties"]["prov_clean"] = clean_prov(raw_name)

    # debug match
    geo_names = {ft["properties"].get("prov_clean", "") for ft in geo["features"]}
    df_names = set(df["prov_clean"])
    match_n = len(df_names & geo_names)
    st.caption(f"Match provinsi: {match_n}/{len(df_names)} (data) | name_key geojson: {name_key}")

    metric = st.selectbox(
        "Tampilkan peta berdasarkan:",
        ["Rate/Prevalensi per 100.000", "Jumlah TBC", "Populasi"],
        index=0
    )

    if metric == "Rate/Prevalensi per 100.000":
        value_col = "rate_100k"
        legend = "TBC per 100.000 penduduk"
    elif metric == "Jumlah TBC":
        value_col = "jumlah_tbc"
        legend = "Jumlah kasus TBC"
    else:
        value_col = "populasi"
        legend = "Populasi"

    map_df = df[["prov_clean", "provinsi", "populasi", "jumlah_tbc", "rate_100k"]].copy()

    m = folium.Map(location=[-2.5, 118.0], zoom_start=5, tiles="cartodbpositron")

    folium.Choropleth(
        geo_data=geo,
        data=map_df,
        columns=["prov_clean", value_col],
        key_on="feature.properties.prov_clean",
        fill_color="YlOrRd",
        fill_opacity=0.85,
        line_opacity=0.35,
        legend_name=legend,
        highlight=True
    ).add_to(m)

    # tooltip
    lookup = map_df.set_index("prov_clean").to_dict(orient="index")
    for ft in geo["features"]:
        p = ft["properties"].get("prov_clean", "")
        row = lookup.get(p)
        if row:
            pop_txt = fmt_int(row["populasi"])
            tbc_txt = fmt_int(row["jumlah_tbc"])
            rate_txt = fmt_float(row["rate_100k"], 1)
            tooltip_html = (
                f"<b>{row['provinsi']}</b><br/>"
                f"Populasi: {pop_txt}<br/>"
                f"Jumlah TBC: {tbc_txt}<br/>"
                f"Rate/100k: {rate_txt}"
            )
        else:
            tooltip_html = f"<b>{ft['properties'].get(name_key,'')}</b><br/>Data tidak tersedia"

        folium.GeoJson(
            ft,
            style_function=lambda x: {"fillOpacity": 0, "weight": 0},
            tooltip=folium.Tooltip(tooltip_html, sticky=True)
        ).add_to(m)

    st_folium(m, use_container_width=True, height=560)


# =========================
# UKURAN EPIDEMIOLOGI
# =========================
elif page == "Epi":
    df = epi2.copy()

    st.markdown(
        """
        <div class="card">
          <div style="font-size:22px;font-weight:900;line-height:1.1;">Ukuran Epidemiologi</div>
          <div class="muted" style="margin-top:4px;">Rate per 100.000 • PR • POR (cross-sectional)</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    # KPI nasional + max/min rate
    total_pop = float(df["populasi"].sum())
    total_cases = float(df["jumlah_tbc"].sum())
    rate_indo = (total_cases / total_pop) * 100000 if total_pop > 0 else np.nan

    idx_max = df["rate_100k"].idxmax()
    idx_min = df["rate_100k"].idxmin()

    a1, a2, a3 = st.columns(3, gap="small")
    with a1:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Rate Indonesia</div>
          <div class="value">{fmt_float(rate_indo, 1)}</div>
          <div class="muted">per 100.000</div>
        </div>
        """, unsafe_allow_html=True)

    with a2:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Tertinggi</div>
          <div class="value">{df.loc[idx_max,'provinsi']}</div>
          <div class="muted">{fmt_float(df.loc[idx_max,'rate_100k'], 1)} per 100.000</div>
        </div>
        """, unsafe_allow_html=True)

    with a3:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Terendah</div>
          <div class="value">{df.loc[idx_min,'provinsi']}</div>
          <div class="muted">{fmt_float(df.loc[idx_min,'rate_100k'], 1)} per 100.000</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Tabel rate
    freq_tbl = df[["provinsi", "populasi", "jumlah_tbc", "rate_100k"]].sort_values("rate_100k", ascending=False).copy()

    st.markdown("""<div class="card"><div style="font-size:16px;font-weight:800;">Rate per Provinsi</div></div>""", unsafe_allow_html=True)
    view_mode = st.segmented_control("Tampilan", options=["Top 10", "Bottom 10", "Semua"], default="Top 10")

    if view_mode == "Top 10":
        show_tbl = freq_tbl.head(10).copy()
    elif view_mode == "Bottom 10":
        show_tbl = freq_tbl.tail(10).sort_values("rate_100k", ascending=True).copy()
    else:
        show_tbl = freq_tbl.copy()

    show_tbl_disp = show_tbl.rename(columns={
        "provinsi": "Provinsi",
        "populasi": "Populasi",
        "jumlah_tbc": "Jumlah TBC",
        "rate_100k": "Rate per 100.000"
    })
    show_tbl_disp["Populasi"] = show_tbl_disp["Populasi"].map(fmt_int)
    show_tbl_disp["Jumlah TBC"] = show_tbl_disp["Jumlah TBC"].map(fmt_int)
    show_tbl_disp["Rate per 100.000"] = show_tbl_disp["Rate per 100.000"].map(lambda x: fmt_float(x, 1))

    st.dataframe(show_tbl_disp, use_container_width=True, hide_index=True, height=360 if view_mode == "Semua" else 280)

    st.write("")
    top10 = freq_tbl.head(10).sort_values("rate_100k", ascending=True)
    fig = px.bar(
        top10,
        x="rate_100k",
        y="provinsi",
        orientation="h",
        text=top10["rate_100k"].round(1),
        labels={"rate_100k": "per 100.000", "provinsi": ""}
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # =========================
    # PR & POR (MEAN SPLIT)
    # =========================
    mean_kepadatan = float(df["kepadatan"].mean())
    df["kelompok_kepadatan"] = np.where(df["kepadatan"] >= mean_kepadatan, "High (≥ mean)", "Low (< mean)")

    agg = (
        df.groupby("kelompok_kepadatan", as_index=False)
          .agg(kasus=("jumlah_tbc", "sum"), non_kasus=("non_tbc", "sum"))
          .set_index("kelompok_kepadatan")
          .reindex(["High (≥ mean)", "Low (< mean)"])
          .reset_index()
    )

    a = float(agg.loc[agg["kelompok_kepadatan"] == "High (≥ mean)", "kasus"].iloc[0])
    b = float(agg.loc[agg["kelompok_kepadatan"] == "High (≥ mean)", "non_kasus"].iloc[0])
    c = float(agg.loc[agg["kelompok_kepadatan"] == "Low (< mean)", "kasus"].iloc[0])
    d = float(agg.loc[agg["kelompok_kepadatan"] == "Low (< mean)", "non_kasus"].iloc[0])

    PR = (a / (a + b)) / (c / (c + d))
    SE_logPR = np.sqrt((1/a) - (1/(a+b)) + (1/c) - (1/(c+d)))
    CI_PR = (np.exp(np.log(PR) - 1.96*SE_logPR), np.exp(np.log(PR) + 1.96*SE_logPR))

    POR = (a * d) / (b * c)
    SE_logPOR = np.sqrt((1/a) + (1/b) + (1/c) + (1/d))
    CI_POR = (np.exp(np.log(POR) - 1.96*SE_logPOR), np.exp(np.log(POR) + 1.96*SE_logPOR))

    st.markdown("""<div class="card"><div style="font-size:16px;font-weight:800;">PR & POR (Paparan: Kepadatan Penduduk)</div></div>""", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1, 1, 1], gap="small")
    with b1:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Mean Kepadatan</div>
          <div class="value">{fmt_float(mean_kepadatan, 1)}</div>
          <div class="muted">jiwa/km²</div>
        </div>
        """, unsafe_allow_html=True)
    with b2:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">PR</div>
          <div class="value">{fmt_float(PR, 3)}</div>
          <div class="muted">CI 95% {fmt_float(CI_PR[0],3)}–{fmt_float(CI_PR[1],3)}</div>
        </div>
        """, unsafe_allow_html=True)
    with b3:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">POR</div>
          <div class="value">{fmt_float(POR, 3)}</div>
          <div class="muted">CI 95% {fmt_float(CI_POR[0],3)}–{fmt_float(CI_POR[1],3)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    st.markdown(
        f"""
        <div class="card">
          <div style="font-size:16px;font-weight:900;">Interpretasi singkat</div>
          <div class="muted" style="margin-top:6px; line-height:1.6;">
            Rate TBC Indonesia tahun 2024 sebesar <b>{fmt_float(rate_indo,1)}</b> per 100.000 penduduk.
            Pengelompokan kepadatan menggunakan <b>mean</b> ({fmt_float(mean_kepadatan,1)} jiwa/km²) menghasilkan
            <b>PR={fmt_float(PR,3)}</b> dan <b>POR={fmt_float(POR,3)}</b> (CI 95% tertera pada panel).
            Interpretasi bersifat asosiasi (bukan kausal) karena desain cross-sectional dan unit analisis agregat provinsi.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# MODELING — NEGATIVE BINOMIAL
# =========================
elif page == "Model":
    try:
        dfm = load_model(PATH_MODEL)
    except Exception as e:
        st.error("Gagal load epi1_modeling.xlsx. Pastikan file ada di folder data/ dan kolomnya sesuai (Provinsi, Y, X1..X5).")
        st.exception(e)
        st.stop()

    st.markdown(
        """
        <div class="card">
          <div style="font-size:22px;font-weight:900;line-height:1.1;">Modeling — Regresi Binomial Negatif</div>
          <div class="muted" style="margin-top:4px;">Poisson baseline • uji overdispersi • NegBin • IRR</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    # Poisson baseline
    pois = smf.glm("y ~ x1 + x2 + x3 + x4 + x5", data=dfm, family=sm.families.Poisson()).fit()
    pearson_chi2 = float(np.sum(pois.resid_pearson**2))
    df_resid = float(pois.df_resid)
    disp_pearson = pearson_chi2 / df_resid
    p_overdisp = 1 - chi2.cdf(pearson_chi2, df_resid)
    aic_pois = float(pois.aic)

    # NegBin (alpha dari MLE NB)
    X = sm.add_constant(dfm[["x1","x2","x3","x4","x5"]])
    nb_mle = sm.NegativeBinomial(dfm["y"], X).fit(disp=False)

    if "alpha" in getattr(nb_mle, "params", pd.Series()).index:
        alpha_hat = float(nb_mle.params["alpha"])
    else:
        alpha_hat = float(getattr(nb_mle, "scale", 1.0))

    nb_glm = smf.glm("y ~ x1 + x2 + x3 + x4 + x5", data=dfm,
                     family=sm.families.NegativeBinomial(alpha=alpha_hat)).fit()
    aic_nb = float(nb_glm.aic)

    # Tabel output + CI95% (biar rapi & akademik)
    params = nb_glm.params
    se = nb_glm.bse
    pvals = nb_glm.pvalues

    out = pd.DataFrame({
        "Variabel": params.index,
        "β": params.values,
        "SE": se.values,
        "p-value": pvals.values
    })

    out["IRR"] = np.exp(out["β"])
    out["CI95_low"] = np.exp(out["β"] - 1.96*out["SE"])
    out["CI95_high"] = np.exp(out["β"] + 1.96*out["SE"])

    out["Variabel"] = out["Variabel"].replace({
        "Intercept": "Intersep",
        "x1": "X₁ Merokok usia 15–24 tahun",
        "x2": "X₂ Penduduk miskin",
        "x3": "X₃ Sanitasi layak",
        "x4": "X₄ Kepadatan penduduk",
        "x5": "X₅ Indeks kualitas udara"
    })

    out["β"] = out["β"].map(lambda x: f"{float(x):.6f}")
    out["SE"] = out["SE"].map(lambda x: f"{float(x):.6f}")
    out["IRR"] = out["IRR"].map(lambda x: f"{float(x):.3f}")
    out["CI95_low"] = out["CI95_low"].map(lambda x: f"{float(x):.3f}")
    out["CI95_high"] = out["CI95_high"].map(lambda x: f"{float(x):.3f}")
    out["p-value"] = out["p-value"].map(fmt_p)

    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Pearson/df (Poisson)</div>
          <div class="value">{disp_pearson:.3f}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">p-value Overdispersi</div>
          <div class="value">{fmt_p(p_overdisp)}</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">AIC Poisson</div>
          <div class="value">{aic_pois:.2f}</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">AIC NegBin</div>
          <div class="value">{aic_nb:.2f}</div>
        </div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown("""<div class="card"><div style="font-size:16px;font-weight:800;">Estimasi Parameter (β, IRR, CI95%)</div></div>""", unsafe_allow_html=True)
    st.dataframe(out[["Variabel","β","SE","IRR","CI95_low","CI95_high","p-value"]], use_container_width=True, hide_index=True)

    st.write("")
    b0 = float(nb_glm.params.get("Intercept", np.nan))
    b1 = float(nb_glm.params.get("x1", np.nan))
    b2 = float(nb_glm.params.get("x2", np.nan))
    b3 = float(nb_glm.params.get("x3", np.nan))
    b4 = float(nb_glm.params.get("x4", np.nan))
    b5 = float(nb_glm.params.get("x5", np.nan))

    eq = (
        f"log(μᵢ) = {b0:.3f}"
        f" + ({b1:.4f})X1ᵢ"
        f" + ({b2:.4f})X2ᵢ"
        f" + ({b3:.4f})X3ᵢ"
        f" + ({b4:.6f})X4ᵢ"
        f" + ({b5:.4f})X5ᵢ"
    )

    st.markdown(
        f"""
        <div class="card">
          <div style="font-size:16px;font-weight:900;">Model Akhir</div>
          <div class="muted" style="margin-top:6px;font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">
            {eq}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# ABOUT
# =========================
elif page == "About":
    st.markdown(
        """
        <div class="card">
          <div style="font-size:22px;font-weight:900;line-height:1.1;">About</div>

          <div class="muted" style="margin-top:8px; line-height:1.6;">
            Dashboard Epidemiologi Tuberkulosis (TBC) ini menyajikan visualisasi dan analisis
            data pada tingkat provinsi di Indonesia. Aplikasi dirancang sebagai media eksplorasi
            data epidemiologi yang menggabungkan ringkasan deskriptif, ukuran epidemiologi,
            dan pemodelan statistik dalam satu tampilan interaktif.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:800;">
            Data dan Sumber
          </div>
          <div class="muted" style="line-height:1.6;">
            Data yang digunakan merupakan data sekunder tahun 2024. Informasi populasi dan indikator sosial-ekonomi
            bersumber dari BPS. Data Indeks Kualitas Udara bersumber dari KLHK, sedangkan data jumlah kasus TBC
            bersumber dari Kementerian Kesehatan Republik Indonesia.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:800;">
            Pendekatan Analisis
          </div>
          <div class="muted" style="line-height:1.6;">
            Analisis mencakup perhitungan rate TBC per 100.000 penduduk, analisis asosiasi menggunakan
            PR dan POR berdasarkan pengelompokan kepadatan penduduk, serta pemodelan lanjutan menggunakan
            regresi binomial negatif untuk data cacah dengan potensi overdispersi.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:800;">
            Pengembang
          </div>
          <div class="muted" style="line-height:1.6;">
            Dashboard ini disusun oleh <b>Ghaitsa Shafiyyah</b>, Program Studi Statistika, Universitas Padjadjaran,
            untuk tugas mata kuliah Epidemiologi.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:800;">
            Catatan
          </div>
          <div class="muted" style="line-height:1.6;">
            Hasil ditujukan untuk keperluan akademik. Interpretasi bergantung pada kualitas data sumber
            dan tidak dimaksudkan sebagai dasar kebijakan kesehatan publik.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
