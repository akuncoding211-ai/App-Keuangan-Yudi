import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Finance Tracker Pro", layout="wide")

# ==========================
# GOOGLE SHEETS CONNECTION
# ==========================

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def connect_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(creds)
    return client.open_by_key("1Ig-coNVWo1F-1JsCTalmnp0qLcLiR28-D5yN4fxkduk")

sheet = connect_sheet()

def load_data(sheet_name):
    df = pd.DataFrame(sheet.worksheet(sheet_name).get_all_records())
    if not df.empty:
        df.columns = df.columns.str.strip()
    return df

def format_rupiah(x):
    return f"Rp {x:,.0f}"

# ==========================
# SIDEBAR
# ==========================

menu = st.sidebar.radio("Menu", [
    "📊 Dashboard",
    "➕ Transaksi",
    "🏦 Tabungan",
    "💰 Budget",
    "📋 Kewajiban",
    "📈 Rekap Bulanan"
])

st.title("💰 Finance Tracker Pro")

# ==========================
# DASHBOARD
# ==========================

if menu == "📊 Dashboard":

    df = load_data("Transaksi")

    if df.empty:
        st.info("Belum ada transaksi.")
        st.stop()

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], dayfirst=True, errors="coerce")
    df["Nominal"] = pd.to_numeric(df["Nominal"], errors="coerce")

    total_pemasukan = df[df["Tipe_Kategori"]=="Pemasukan"]["Nominal"].sum()
    total_pengeluaran = df[df["Tipe_Kategori"]=="Pengeluaran"]["Nominal"].sum()
    saldo = total_pemasukan - total_pengeluaran

    col1, col2, col3 = st.columns(3)
    col1.metric("Pemasukan", format_rupiah(total_pemasukan))
    col2.metric("Pengeluaran", format_rupiah(total_pengeluaran))
    col3.metric("Saldo", format_rupiah(saldo))

    st.markdown("### Cashflow Bulanan")
    df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)
    trend = df.groupby(["Bulan","Tipe_Kategori"])["Nominal"].sum().unstack().fillna(0)
    st.line_chart(trend)

    st.markdown("### Komposisi Pengeluaran")
    pie = df[df["Tipe_Kategori"]=="Pengeluaran"] \
        .groupby("Kategori")["Nominal"].sum().reset_index()
    if not pie.empty:
        fig = px.pie(pie, names="Kategori", values="Nominal")
        st.plotly_chart(fig, use_container_width=True)

# ==========================
# TRANSAKSI
# ==========================

elif menu == "➕ Transaksi":

    with st.form("form_transaksi", clear_on_submit=True):
        tanggal = st.date_input("Tanggal")
        kategori = st.text_input("Kategori")
        tipe = st.selectbox("Tipe", ["Pemasukan","Pengeluaran","Tabungan"])
        nominal = st.number_input("Nominal", min_value=0)
        keterangan = st.text_area("Keterangan")

        if st.form_submit_button("Simpan"):
            sheet.worksheet("Transaksi").append_row(
                [str(tanggal), kategori, tipe, nominal, keterangan]
            )
            st.success("✅ Transaksi berhasil disimpan")
            st.rerun()

    st.markdown("### Data Transaksi")
    df = load_data("Transaksi")
    if not df.empty:
        st.dataframe(df, use_container_width=True)

# ==========================
# TABUNGAN
# ==========================

elif menu == "🏦 Tabungan":

    with st.form("form_tabungan", clear_on_submit=True):
        nama = st.text_input("Nama Akun")
        target = st.number_input("Target", min_value=0)
        awal = st.number_input("Saldo Awal", min_value=0)

        if st.form_submit_button("Buat Akun"):
            sheet.worksheet("Tabungan").append_row(
                [nama, target, awal, str(datetime.now().date())]
            )
            st.success("✅ Akun tabungan dibuat")
            st.rerun()

    df = load_data("Tabungan")
    if not df.empty:
        df["Target_Jumlah"] = pd.to_numeric(df["Target_Jumlah"], errors="coerce")
        df["Jumlah_Saat_Ini"] = pd.to_numeric(df["Jumlah_Saat_Ini"], errors="coerce")

        for _, row in df.iterrows():
            target = row["Target_Jumlah"] if row["Target_Jumlah"] > 0 else 1
            current = row["Jumlah_Saat_Ini"]
            progress = min(current / target, 1.0)

            st.write(f"**{row['Nama_Akun']}**")
            st.progress(progress)
            st.write(f"{format_rupiah(current)} / {format_rupiah(target)}")

# ==========================
# BUDGET
# ==========================

elif menu == "💰 Budget":

    with st.form("form_budget", clear_on_submit=True):
        kategori = st.text_input("Kategori")
        jumlah = st.number_input("Budget", min_value=0)

        if st.form_submit_button("Simpan"):
            sheet.worksheet("Budget").append_row([kategori, jumlah])
            st.success("✅ Budget disimpan")
            st.rerun()

    df_budget = load_data("Budget")
    df_trans = load_data("Transaksi")

    if not df_budget.empty and not df_trans.empty:
        df_trans["Nominal"] = pd.to_numeric(df_trans["Nominal"], errors="coerce")
        actual = df_trans[df_trans["Tipe_Kategori"]=="Pengeluaran"] \
            .groupby("Kategori")["Nominal"].sum().reset_index()

        df_budget["Budget"] = pd.to_numeric(df_budget["Budget"], errors="coerce")

        merged = pd.merge(df_budget, actual, on="Kategori", how="left").fillna(0)
        merged.rename(columns={"Nominal":"Pengeluaran"}, inplace=True)
        merged["Sisa"] = merged["Budget"] - merged["Pengeluaran"]

        st.dataframe(merged, use_container_width=True)

# ==========================
# KEWAJIBAN
# ==========================

elif menu == "📋 Kewajiban":

    with st.form("form_kewajiban", clear_on_submit=True):
        nama = st.text_input("Nama Kewajiban")
        nominal = st.number_input("Nominal", min_value=0)
        tipe = st.selectbox("Tipe", ["Hutang","Piutang"])
        pihak = st.text_input("Pihak Terkait")

        if st.form_submit_button("Simpan"):
            sheet.worksheet("Kewajiban").append_row(
                [nama, nominal, str(datetime.now().date()),
                 "Belum Lunas", tipe, pihak]
            )
            st.success("✅ Kewajiban ditambahkan")
            st.rerun()

    df = load_data("Kewajiban")
    if not df.empty:
        st.dataframe(df, use_container_width=True)

# ==========================
# REKAP BULANAN OTOMATIS
# ==========================

elif menu == "📈 Rekap Bulanan":

    df = load_data("Transaksi")

    if df.empty:
        st.info("Belum ada transaksi.")
        st.stop()

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], dayfirst=True, errors="coerce")
    df["Nominal"] = pd.to_numeric(df["Nominal"], errors="coerce")
    df = df.dropna(subset=["Tanggal"])

    df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)

    rekap = df.groupby(["Bulan","Tipe_Kategori"])["Nominal"] \
        .sum().unstack().fillna(0)

    st.subheader("Rekap Bulanan Otomatis")

    st.dataframe(rekap, use_container_width=True)
    st.line_chart(rekap)

    csv = rekap.to_csv().encode("utf-8")
    st.download_button(
        "Download Rekap CSV",
        csv,
        "rekap_bulanan.csv",
        "text/csv"
    )
