import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json


@st.cache_data
def load_data():
    df = pd.read_excel(epi2_ukuran.xlsx)

    # ==== BERSIHKAN NAMA KOLOM DULU ====
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # ==== RENAME KE NAMA STANDAR ====
    rename_map = {
        "provinsii": "provinsi",
        "provinsi": "provinsi",
        "jumlah_tbc": "jumlah_tbc",
        "jumlah tbc": "jumlah_tbc"
    }
    df = df.rename(columns=rename_map)

    # ==== VALIDASI KOLOM WAJIB ====
    required_cols = ["provinsi", "populasi", "jumlah_tbc"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")

    # ==== PASTIKAN NUMERIK ====
    for c in ["populasi", "jumlah_tbc", "kepadatan"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # ==== BERSIHKAN ISI PROVINSI ====
    df["provinsi"] = df["provinsi"].astype(str).str.strip()

    return df


epi2 = load_epi2(PATH_EPI2)

# =========================
# CONFIG (WAJIB PALING ATAS)
# =========================
st.set_page_config(
    page_title="Dashboard Epidemiologi TBC",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Home"

def go(page_name: str):
    st.session_state.page = page_name

# =========================
# CLEAN UI CSS (LIGHT GRAY BG + BLACK TEXT + FIX LAYOUT)
# =========================
st.markdown("""
<style>
/* Hide Streamlit header/toolbar/footer biar clean */
[data-testid="stHeader"] { background: transparent !important; height: 0px !important; }
[data-testid="stToolbar"] { visibility: hidden !important; height: 0px !important; }
footer { visibility: hidden !important; }

/* Hide sidebar */
[data-testid="stSidebar"], [data-testid="stSidebarNav"] { display:none !important; }

/* ====== FIX: background & text (target yang BENER) ====== */
html, body {
  background:#f2f4f7 !important;
  color:#111111 !important;
}
[data-testid="stAppViewContainer"]{
  background:#f2f4f7 !important;
  color:#111111 !important;
}
[data-testid="stApp"]{
  background:#f2f4f7 !important;
  color:#111111 !important;
}
main, section {
  background:#f2f4f7 !important;
  color:#111111 !important;
}

/* Lebarin container & padding */
.block-container{
  max-width: 1400px !important;
  padding-top: 0.8rem !important;
  padding-bottom: 2rem !important;
  padding-left: 1.2rem !important;
  padding-right: 1.2rem !important;
}

/* ===== Topbar ===== */
.topbar{
  display:flex; align-items:center; gap:12px;
  padding: 14px 18px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  border-radius: 18px;
  width:100%;
  box-sizing:border-box;
}
.logo{
  width:34px; height:34px; border-radius:12px;
  background:#111827;
  display:flex; align-items:center; justify-content:center;
  color:#ffffff !important; font-weight:800;
  flex:0 0 auto;
}
.brand-text{ display:flex; flex-direction:column; min-width:0; }
.brand-title{
  font-weight:800; font-size: 20px; line-height:1.15;
  color:#111111 !important;
}
.brand-sub{
  margin-top:2px;
  color:#374151 !important;
  font-size:0.95rem; line-height:1.2;
}

/* ===== Buttons ===== */
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

/* ====== Tambahan: class yang kamu pakai di HTML ====== */
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
.kpi .label{
  color:#6b7280 !important;
  font-size:0.9rem !important;
  font-weight:600 !important;
}
.kpi .value{
  color:#111111 !important;
  font-size:34px !important;
  font-weight:800 !important;
  line-height:1.1 !important;
}
.muted{
  color:#374151 !important;
}

/* ====== Paksa semua teks jadi gelap (termasuk widget label) ====== */
h1,h2,h3,h4,h5,h6,p,span,div,label,li {
  color:#111111 !important;
}

/* ====== Dataframe/Table biar ga kebawa theme gelap ====== */
[data-testid="stDataFrame"]{
  background:#ffffff !important;
  border:1px solid #e5e7eb !important;
  border-radius:16px !important;
  overflow:hidden !important;
}

/* ====== Plotly: pastiin background transparan & font gelap ====== */
.js-plotly-plot, .plotly, .main-svg{
  background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


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
# PAGES (UI ONLY / PLACEHOLDER)
# =========================
page = st.session_state.page

if page == "Home":

    df = epi2.dropna(subset=["provinsi", "populasi", "jumlah_tbc"]).copy()

    total_kasus = int(df["jumlah_tbc"].sum())
    rata_kasus  = int(df["jumlah_tbc"].mean())
    median_kasus = int(df["jumlah_tbc"].median())

    min_kasus = int(df["jumlah_tbc"].min())
    max_kasus = int(df["jumlah_tbc"].max())

    fmt = lambda x: f"{x:,}".replace(",", ".")

    left, right = st.columns([1.4, 1], gap="large")

    # ================= LEFT =================
    with left:
        # ---- Judul besar
        st.markdown(
            f"""
            <div class="card">
              <div style="font-size:26px;font-weight:700;margin-bottom:4px;">
                Dashboard Kasus TBC — Indonesia (2024)
              </div>
              <div class="muted" style="font-size:13px;">
                Sumber data: Kementerian Kesehatan & BPS 2024 | Analisis tingkat provinsi
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        # ---- KPI BLOK (angka jadi fokus)
        st.markdown(
            f"""
            <div class="card">
              <div class="muted">Total Kasus TBC (2024)</div>
              <div style="font-size:42px;font-weight:800;line-height:1.1;">
                {fmt(total_kasus)}
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
                  <div class="muted">Rata-rata Kasus per Provinsi</div>
                  <div style="font-size:32px;font-weight:700;">
                    {fmt(rata_kasus)}
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with k2:
            st.markdown(
                f"""
                <div class="card">
                  <div class="muted">Median Kasus</div>
                  <div style="font-size:32px;font-weight:700;">
                    {fmt(median_kasus)}
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with k3:
            st.markdown(
                f"""
                <div class="card">
                  <div class="muted">Rentang Kasus</div>
                  <div style="font-size:26px;font-weight:700;">
                    {fmt(min_kasus)} – {fmt(max_kasus)}
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("")

        # ---- Top 10 chart (lebih elegan)
        top10 = (
            df.sort_values("jumlah_tbc", ascending=False)
              .head(10)
              .sort_values("jumlah_tbc")
        )

        st.markdown(
            """
            <div class="card">
              <div style="font-size:18px;font-weight:600;">
                Top 10 Provinsi dengan Kasus TBC Tertinggi (2024)
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.bar_chart(
            top10.set_index("provinsi")["jumlah_tbc"],
            height=360
        )

    # ================= RIGHT =================
    with right:
        st.markdown(
            """
            
            <div class="card">
              <div style="font-size:18px;font-weight:600;margin-bottom:6px;">
                Catatan Analisis
              </div>
              <div class="muted" style="font-size:13px;line-height:1.6;">
                Dashboard ini menyajikan analisis epidemiologi Tuberkulosis (TBC) pada tingkat provinsi
                menggunakan pendekatan deskriptif dan analitik. Analisis deskriptif mencakup
                <b>prevalensi TBC per 100.000 penduduk</b> sebagai ukuran frekuensi kejadian.
                Selanjutnya, dilakukan analisis asosiasi melalui perhitungan
                <b>Prevalence Ratio (PR)</b> dan <b>Prevalence Odds Ratio (POR)</b>
                berdasarkan kategori kepadatan penduduk.
                <br/><br/>
                Untuk analisis lanjutan, dashboard menerapkan
                <b>regresi binomial negatif</b> guna memodelkan jumlah kasus TBC
                dengan mempertimbangkan variasi populasi dan potensi overdispersi pada data cacah.
                Hasil pemodelan disajikan dalam bentuk estimasi parameter dan interpretasi risiko relatif
                antar kelompok.
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    pass

elif page == "Peta Sebaran":
    import json
    import numpy as np
    import pandas as pd
    import folium
    from streamlit_folium import st_folium

    # =========================
    # 0) LOAD DATA EPI2 (pakai epi2 yang sudah kamu load di atas sebenarnya boleh)
    # =========================
    df = epi2.copy()

    # pastikan kolom standar
    df.columns = df.columns.astype(str).str.strip().str.lower()
    df = df.rename(columns={"provinsii": "provinsi"})
    for c in ["populasi", "jumlah_tbc", "kepadatan"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["provinsi"] = df["provinsi"].astype(str).str.strip()
    df = df.dropna(subset=["provinsi", "populasi", "jumlah_tbc"]).copy()

    df["rate_100k"] = (df["jumlah_tbc"] / df["populasi"]) * 100000

    # =========================
    # 1) CLEAN NAMA PROVINSI
    # =========================
    def clean_prov(s: str) -> str:
        s = str(s).strip().upper()
        s = s.replace(".", "").replace(",", "")
        s = " ".join(s.split())
        s = s.replace("DI YOGYAKARTA", "DAERAH ISTIMEWA YOGYAKARTA")
        s = s.replace("KEP BANGKA BELITUNG", "KEPULAUAN BANGKA BELITUNG")
        s = s.replace("BANGKA BELITUNG", "KEPULAUAN BANGKA BELITUNG")
        s = s.replace("KEP RIAU", "KEPULAUAN RIAU")
        return s

    df["prov_clean"] = df["provinsi"].map(clean_prov)

    # =========================
    # 2) LOAD GEOJSON LOKAL
    # =========================
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent
    GEO_PATH = BASE_DIR / "indonesia.geojson"

    @st.cache_data(show_spinner=False)
    def load_geojson_local(path: str):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    geo = load_geojson_local(GEO_PATH)

    # ===== Cari field nama provinsi yang benar (auto) =====
    # Lihat key apa yang ada di properties feature pertama
    props0 = geo["features"][0]["properties"]
    candidate_keys = ["Propinsi", "propinsi", "Provinsi", "provinsi", "NAME_1", "name", "Name", "nama", "NAMA"]
    name_key = next((k for k in candidate_keys if k in props0), None)

    if name_key is None:
        st.error(f"Gak nemu kolom nama provinsi di geojson. Keys contoh: {list(props0.keys())[:20]}")
        st.stop()

    # inject prov_clean ke setiap feature
    for ft in geo["features"]:
        raw_name = ft["properties"].get(name_key, "")
        ft["properties"]["prov_clean"] = clean_prov(raw_name)

    # =========================
    # 3) DEBUG MATCH (biar tau kalau kosong kenapa)
    # =========================
    geo_names = {ft["properties"].get("prov_clean", "") for ft in geo["features"]}
    df_names = set(df["prov_clean"])

    match_n = len(df_names & geo_names)
    st.caption(f"Match provinsi: {match_n}/{len(df_names)} (data) vs {len(geo_names)} (peta) | name_key geojson: {name_key}")

    missing_in_geo = sorted(df_names - geo_names)
    if missing_in_geo:
        st.warning(f"Tidak ketemu di peta (cek ejaan/format): {missing_in_geo}")

    # =========================
    # 4) PILIH METRIK
    # =========================
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

    # =========================
    # 5) PETA FOLIUM
    # =========================
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

    # Tooltip (simple + aman)
    lookup = map_df.set_index("prov_clean").to_dict(orient="index")

    for ft in geo["features"]:
        p = ft["properties"].get("prov_clean", "")
        row = lookup.get(p)

        if row:
            pop_txt = f"{int(row['populasi']):,}".replace(",", ".")
            tbc_txt = f"{int(row['jumlah_tbc']):,}".replace(",", ".")
            rate_txt = f"{row['rate_100k']:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

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


    pass

elif page == "Epi":
    import numpy as np
    import pandas as pd
    import plotly.express as px

    # =========================
    # 0) PREP DATA
    # =========================
    df = epi2.copy()

    rename_map = {
        "Provinsii": "provinsi", "provinsii": "provinsi",
        "Populasi": "populasi", "populasi": "populasi",
        "jumlah_TBC": "jumlah_tbc", "jumlah_tbc": "jumlah_tbc",
        "Kepadatan": "kepadatan", "kepadatan": "kepadatan"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df = df.dropna(subset=["provinsi", "populasi", "jumlah_tbc", "kepadatan"]).copy()
    df["populasi"] = pd.to_numeric(df["populasi"], errors="coerce")
    df["jumlah_tbc"] = pd.to_numeric(df["jumlah_tbc"], errors="coerce")
    df["kepadatan"] = pd.to_numeric(df["kepadatan"], errors="coerce")
    df = df.dropna(subset=["populasi", "jumlah_tbc", "kepadatan"]).copy()

    df["non_tbc"] = df["populasi"] - df["jumlah_tbc"]
    df["rate_100k"] = (df["jumlah_tbc"] / df["populasi"]) * 100000

    fmt_int = lambda x: f"{int(round(x)):,}".replace(",", ".")
    fmt_float = lambda x, d=1: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # =========================
    # 1) HEADER (MINIM TEKS)
    # =========================
    st.markdown(
        """
        <div class="card">
          <div style="font-size:22px;font-weight:800;line-height:1.1;">Ukuran Epidemiologi</div>
          <div class="muted" style="margin-top:4px;">Prevalensi per 100.000 • PR • POR </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    # =========================
    # 2) KPI UTAMA (INDO + MAX + MIN)
    # =========================
    total_pop = float(df["populasi"].sum())
    total_cases = float(df["jumlah_tbc"].sum())
    rate_indo = (total_cases / total_pop) * 100000 if total_pop > 0 else np.nan

    idx_max = df["rate_100k"].idxmax()
    idx_min = df["rate_100k"].idxmin()
    prov_max = df.loc[idx_max, "provinsi"]
    prov_min = df.loc[idx_min, "provinsi"]
    rate_max = float(df.loc[idx_max, "rate_100k"])
    rate_min = float(df.loc[idx_min, "rate_100k"])

    a1, a2, a3 = st.columns(3, gap="small")
    with a1:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Prevalensi/Rate Indonesia</div>
          <div class="value">{fmt_float(rate_indo, 1)}</div>
          <div class="muted">per 100.000</div>
        </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Tertinggi</div>
          <div class="value">{prov_max}</div>
          <div class="muted">{fmt_float(rate_max, 1)} per 100.000</div>
        </div>
        """, unsafe_allow_html=True)
    with a3:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Terendah</div>
          <div class="value">{prov_min}</div>
          <div class="muted">{fmt_float(rate_min, 1)} per 100.000</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # =========================
    # 3) TABEL PREVALENSI PER PROVINSI (RAPI + FILTER)
    # =========================
    freq_tbl = (
        df[["provinsi", "populasi", "jumlah_tbc", "rate_100k"]]
        .sort_values("rate_100k", ascending=False)
        .copy()
    )

    st.markdown(
        """
        <div class="card">
          <div style="font-size:16px;font-weight:700;">Prevalensi/Rate per Provinsi (per 100.000)</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    view_mode = st.segmented_control(
        "Tampilan",
        options=["Top 10", "Bottom 10", "Semua"],
        default="Top 10"
    )

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

    # format kolom
    show_tbl_disp["Populasi"] = show_tbl_disp["Populasi"].map(fmt_int)
    show_tbl_disp["Jumlah TBC"] = show_tbl_disp["Jumlah TBC"].map(fmt_int)
    show_tbl_disp["Rate per 100.000"] = show_tbl_disp["Rate per 100.000"].map(lambda x: fmt_float(float(x), 1))

    st.dataframe(
        show_tbl_disp,
        use_container_width=True,
        hide_index=True,
        height=360 if view_mode == "Semua" else 280
    )

    st.write("")

    # =========================
    # 4) CHART RINGKAS (TOP 10 AJA) - BIAR GA RAMAI
    # =========================
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
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # =========================
    # 5) PR & POR (MEDIAN SPLIT)
    # =========================
    med_kepadatan = float(df["kepadatan"].median())
    df["kelompok_kepadatan"] = np.where(df["kepadatan"] >= med_kepadatan, "High (≥ median)", "Low (< median)")

    agg = (
        df.groupby("kelompok_kepadatan", as_index=False)
          .agg(kasus=("jumlah_tbc", "sum"), non_kasus=("non_tbc", "sum"))
          .set_index("kelompok_kepadatan")
          .reindex(["High (≥ median)", "Low (< median)"])
          .reset_index()
    )

    a = float(agg.loc[agg["kelompok_kepadatan"] == "High (≥ median)", "kasus"].iloc[0])
    b = float(agg.loc[agg["kelompok_kepadatan"] == "High (≥ median)", "non_kasus"].iloc[0])
    c = float(agg.loc[agg["kelompok_kepadatan"] == "Low (< median)", "kasus"].iloc[0])
    d = float(agg.loc[agg["kelompok_kepadatan"] == "Low (< median)", "non_kasus"].iloc[0])

    PR = (a / (a + b)) / (c / (c + d))
    SE_logPR = np.sqrt((1/a) - (1/(a+b)) + (1/c) - (1/(c+d)))
    CI_PR = (np.exp(np.log(PR) - 1.96*SE_logPR), np.exp(np.log(PR) + 1.96*SE_logPR))

    POR = (a * d) / (b * c)
    SE_logPOR = np.sqrt((1/a) + (1/b) + (1/c) + (1/d))
    CI_POR = (np.exp(np.log(POR) - 1.96*SE_logPOR), np.exp(np.log(POR) + 1.96*SE_logPOR))

    st.markdown(
        """
        <div class="card">
          <div style="font-size:16px;font-weight:700;">PR & POR (Paparan: Kepadatan Penduduk)</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    b1, b2, b3 = st.columns([1, 1, 1], gap="small")
    with b1:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Median Kepadatan</div>
          <div class="value">{fmt_float(med_kepadatan, 1)}</div>
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

  

    # =========================
    # 7) INTERPRETASI (1 CARD SAJA)
    # =========================
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Interpretasi</div>
          <div class="muted">
            Prevalensi/Rate TBC Indonesia tahun 2024 sebesar <b>{fmt_float(rate_indo,1)}</b> per 100.000 penduduk.
            Provinsi dengan rate tertinggi adalah <b>{prov_max}</b> ({fmt_float(rate_max,1)} per 100.000) dan terendah
            <b>{prov_min}</b> ({fmt_float(rate_min,1)} per 100.000).
            Berdasarkan median split kepadatan ({fmt_float(med_kepadatan,1)} jiwa/km²), diperoleh
            <b>PR={fmt_float(PR,3)}</b> dan <b>POR={fmt_float(POR,3)}</b> (CI 95% ditampilkan pada panel PR/POR).
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    pass

elif page == "Model":
    import numpy as np
    import pandas as pd
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from scipy.stats import chi2

    # =========================
    # 0) LOAD DATA (MODEL)
    # =========================
@st.cache_data
def load_data():
    df = pd.read_excel(epi1_modeling.xlsx)

    df = df.rename(columns={
        "Provinsi": "provinsi",
        "Y": "y",
        "X1": "x1",
        "X2": "x2",
        "X3": "x3",
        "X4": "x4",
        "X5": "x5",
    })

    for c in ["y","x1","x2","x3","x4","x5"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["y","x1","x2","x3","x4","x5"]).copy()

    # =========================
    # 1) POISSON baseline + overdisp (Pearson)
    # =========================
    pois = smf.glm(
        "y ~ x1 + x2 + x3 + x4 + x5",
        data=df,
        family=sm.families.Poisson()
    ).fit()

    pearson_chi2 = float(np.sum(pois.resid_pearson**2))
    df_resid = float(pois.df_resid)
    disp_pearson = pearson_chi2 / df_resid
    p_overdisp = 1 - chi2.cdf(pearson_chi2, df_resid)  # approx

    aic_pois = float(pois.aic)

    # =========================
    # 2) NEG BIN: estimasi alpha via MLE, lalu fit NB-GLM pakai alpha tsb
    # =========================
    X = sm.add_constant(df[["x1","x2","x3","x4","x5"]])

    nb_mle = sm.NegativeBinomial(df["y"], X).fit(disp=False)

    # ambil alpha dari params (ini yang valid di statsmodels)
    if "alpha" in nb_mle.params.index:
        alpha_hat = float(nb_mle.params["alpha"])
    else:
        # fallback aman (jarang kejadian)
        alpha_hat = float(getattr(nb_mle, "scale", 1.0))

    nb_glm = smf.glm(
        "y ~ x1 + x2 + x3 + x4 + x5",
        data=df,
        family=sm.families.NegativeBinomial(alpha=alpha_hat)
    ).fit()

    aic_nb = float(nb_glm.aic)

    # =========================
    # 3) TABEL OUTPUT (β, IRR, p-value) — TANPA CI
    # =========================
    params = nb_glm.params
    pvals = nb_glm.pvalues
    irr = np.exp(params)

    out = pd.DataFrame({
        "Variabel": params.index,
        "β": params.values,
        "IRR": irr.values,
        "p-value": pvals.values
    })

    out["Variabel"] = out["Variabel"].replace({
        "Intercept": "Intersep",
        "x1": "X₁ Merokok usia 15–24 tahun",
        "x2": "X₂ Penduduk miskin",
        "x3": "X₃ Sanitasi layak",
        "x4": "X₄ Kepadatan penduduk",
        "x5": "X₅ Indeks kualitas udara"
    })

    def fmt_p(x):
        x = float(x)
        return "< 0.001" if x < 0.001 else f"{x:.4f}"

    out["β"] = out["β"].map(lambda x: f"{float(x):.6f}")
    out["IRR"] = out["IRR"].map(lambda x: f"{float(x):.3f}")
    out["p-value"] = out["p-value"].map(fmt_p)

    # =========================
    # 4) PERSAMAAN MODEL AKHIR
    # =========================
    b0 = float(nb_glm.params.get("Intercept", np.nan))
    b1 = float(nb_glm.params.get("x1", np.nan))
    b2 = float(nb_glm.params.get("x2", np.nan))
    b3 = float(nb_glm.params.get("x3", np.nan))
    b4 = float(nb_glm.params.get("x4", np.nan))
    b5 = float(nb_glm.params.get("x5", np.nan))

    eq = (
        f"log(μᵢ) = {b0:.2f}"
        f" + ({b1:.4f})X1ᵢ"
        f" + ({b2:.4f})X2ᵢ"
        f" + ({b3:.4f})X3ᵢ"
        f" + ({b4:.6f})X4ᵢ"
        f" + ({b5:.4f})X5ᵢ"
    )

    # =========================
    # 5) UI
    # =========================
    st.markdown(
        """
        <div class="card">
          <div style="font-size:22px;font-weight:800;line-height:1.1;">Modeling — Regresi Binomial Negatif</div>
          <div class="muted">Overdispersion • AIC • Koefisien + IRR</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">Pearson/df</div>
          <div class="value">{disp_pearson:.3f}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi">
          <div class="label">p-value Overdispersion</div>
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

    st.markdown(
        """
        <div class="card">
          <div style="font-size:16px;font-weight:700;">Tabel Estimasi (β, IRR, p-value)</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.dataframe(out, use_container_width=True, hide_index=True)

    st.write("")

    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Model Akhir</div>
          <div class="muted" style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">
            {eq}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    pass

if page == "About":
    st.markdown(
        """
        <div class="card">
          <div style="font-size:22px;font-weight:800;line-height:1.1;">About</div>

          <div class="muted" style="margin-top:8px; line-height:1.6;">
            Dashboard Epidemiologi Tuberkulosis (TBC) ini menyajikan visualisasi dan analisis
            data pada tingkat provinsi di Indonesia. Aplikasi dirancang sebagai media eksplorasi
            data epidemiologi yang menggabungkan ringkasan deskriptif, ukuran epidemiologi,
            dan pemodelan statistik dalam satu tampilan interaktif.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:600;">
            Data dan Sumber
          </div>
          <div class="muted" style="line-height:1.6;">
            Data yang digunakan merupakan data sekunder tahun 2024. Informasi populasi dan
            indikator sosial-ekonomi bersumber dari Badan Pusat Statistik. Data Indeks Kualitas
            Udara diperoleh dari Kementerian Lingkungan Hidup dan Kehutanan, sedangkan data
            jumlah kasus TBC diperoleh dari Kementerian Kesehatan Republik Indonesia.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:600;">
            Pendekatan Analisis
          </div>
          <div class="muted" style="line-height:1.6;">
            Analisis mencakup perhitungan rate atau prevalensi TBC per 100.000 penduduk,
            analisis asosiasi menggunakan Prevalence Ratio (PR) dan Prevalence Odds Ratio (POR)
            berdasarkan pengelompokan kepadatan penduduk, serta pemodelan lanjutan menggunakan
            regresi binomial negatif untuk data cacah dengan potensi overdispersi.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:600;">
            Pengembang
          </div>
          <div class="muted" style="line-height:1.6;">
            Dashboard ini disusun oleh <b>Ghaitsa Shafiyyah</b>,
            mahasiswa Program Studi Statistika, Universitas Padjadjaran,
            dalam rangka pemenuhan tugas mata kuliah Epidemiologi.
          </div>

          <div style="margin-top:14px; font-size:14px; font-weight:600;">
            Catatan Penggunaan
          </div>
          <div class="muted" style="line-height:1.6;">
            Seluruh hasil analisis ditujukan untuk keperluan akademik dan pembelajaran.
            Interpretasi sangat bergantung pada kualitas data sumber dan tidak dimaksudkan
            sebagai dasar pengambilan kebijakan kesehatan publik.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

