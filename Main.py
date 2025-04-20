import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# Konfigurasi API ThingSpeak
READ_API_KEY = "HN1IL39E5FEC1BQE"
CHANNEL_ID = "2925424"
URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=50"

# Fungsi ambil data
def get_data():
    response = requests.get(URL)
    data = response.json()
    feeds = data["feeds"]
    df = pd.DataFrame(feeds)
    df["field1"] = pd.to_numeric(df["field1"], errors="coerce").fillna(0)  # Suhu
    df["field2"] = pd.to_numeric(df["field2"], errors="coerce").fillna(0)  # Vibrasi
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df

st.title("\U0001F4C8 Monitor Suhu & Vibrasi Mesin")
st.markdown("Pantau kondisi mesin melalui suhu dan vibrasi secara real-time.")

# Ambil data
data = get_data()

# Unduh data
st.download_button("📥 Unduh Data Mentah", data.to_csv(index=False).encode("utf-8"), "data_mentah.csv", "text/csv")

# Ambil data terbaru
latest_suhu = data["field1"].iloc[-1]
latest_vibrasi = data["field2"].iloc[-1]

# Statistik suhu
mean_suhu = np.mean(data["field1"])
std_suhu = np.std(data["field1"])
min_suhu = np.min(data["field1"])
max_suhu = np.max(data["field1"])

# Statistik vibrasi
vibrasi_count = data["field2"].value_counts()

# Notifikasi
st.info(f"Suhu saat ini: {latest_suhu:.2f}°C")
if latest_vibrasi == 1:
    st.warning("\U0001F4CC Mesin sedang bergetar (vibrasi = 1)")
else:
    st.success("\u2705 Mesin dalam keadaan tenang (vibrasi = 0)")

# Statistik
st.subheader("\U0001F4C8 Analisis Suhu & Vibrasi")
col1, col2 = st.columns(2)
with col1:
    if len(data) >= 2:
        delta_suhu = data["field1"].iloc[-1] - data["field1"].iloc[-2]
        delta_waktu = (data["created_at"].iloc[-1] - data["created_at"].iloc[-2]).total_seconds()
        rate_of_change = np.round(delta_suhu / delta_waktu if delta_waktu != 0 else 0, 3)
        st.metric(label="🧮 Pengukuran Suhu", value=f"{mean_suhu:.2f} ± {std_suhu:.2f}°C", delta=f"{rate_of_change}°C/s")
    else:
        st.warning("❗ Data kurang dari 2, tidak bisa hitung rate of change.")
    
    cola, colb = st.columns(2)
    cola.metric("🥶 Min Suhu", f"{min_suhu:.2f}°C")
    colb.metric("🥵 Max Suhu", f"{max_suhu:.2f}°C")

    suhu_bergetar = data[data["field2"] == 1]["field1"]
    suhu_tidak_bergetar = data[data["field2"] == 0]["field1"]
    st.metric("✂️ Selisih Suhu (tidak bergetar vs bergetar)", f"{np.round(suhu_tidak_bergetar.mean() - suhu_bergetar.mean(), 3)} °C")

with col2:
    show_piechart = st.toggle("tunjukkan grafik pie chart")
    if show_piechart:
        total = len(data)
        prop_bergetar = (data["field2"] == 1).sum() / total * 100
        prop_tidak_bergetar = 100 - prop_bergetar

        fig_pie = px.pie(names=["Tidak Bergetar", "Bergetar"], values=[prop_tidak_bergetar, prop_bergetar],
                        title="Proporsi Waktu Mesin Bergetar", color_discrete_sequence=["green", "purple"])
        fig_pie.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.write(f"\U0001F4CC Selama periode ini: {prop_bergetar:.2f}% waktu mesin bergetar.")
    else:
        vib_dist = vibrasi_count.rename(index={0: "Tidak Bergetar", 1: "Bergetar"}).reset_index()
        vib_dist.columns = ["Kondisi", "Jumlah"]
        fig_bar = px.bar(vib_dist, x="Kondisi", y="Jumlah", color="Kondisi", title="Distribusi Vibrasi", color_discrete_map={"Bergetar": "purple", "Tidak Bergetar": "green"})
        st.plotly_chart(fig_bar, use_container_width=True)

# Visualisasi
st.subheader("\U0001F4CA Visualisasi Distribusi dan Waktu")

# Grafik suhu terhadap waktu
fig_line = px.line(data, x="created_at", y="field1", title="Grafik Suhu terhadap Waktu", markers=True)
fig_line.update_layout(yaxis_title="Suhu (°C)", xaxis_title="Waktu")
st.plotly_chart(fig_line, use_container_width=True)

# Histogram distribusi tanpa Gaussian fit
fig_hist = px.histogram(data, x="field1", nbins=20, marginal="rug", title="Distribusi Suhu")
fig_hist.add_vline(x=mean_suhu, line_dash="dash", line_color="blue", annotation_text="Mean")
fig_hist.update_layout(xaxis_title="Suhu (°C)")
st.plotly_chart(fig_hist, use_container_width=True)

# Auto update
st.markdown("\U0001F501 Data akan diperbarui otomatis setiap 30 detik.")
time.sleep(30)
st.rerun()
