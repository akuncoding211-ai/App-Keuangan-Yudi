import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Finance Tracker Pro v6", layout="wide")

# ================= CONNECT ================= #

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

# ================= AUTO SETUP ================= #

def ensure_structure():
    # Transaksi
    try:
        ws = sheet.worksheet("Transaksi")
    except:
        ws = sheet.add_worksheet(title="Transaksi", rows="1000", cols="10")
    header = ["Tanggal","Nama_Akun","Jenis_Transaksi","Nominal","Keterangan"]
    if ws.row_values(1) != header:
        ws.clear()
        ws.append_row(header)

    # Daftar Akun
    try:
        ws2 = sheet.worksheet("Daftar_Akun")
    except:
        ws2 = sheet.add_worksheet(title="Daftar_Akun", rows="200", cols="5")
        ws2.append_row(["Nama_Akun","Kategori_Akun"])

ensure_structure()

# ================= HELPERS ================= #

def load(sheet_name):
    return pd.DataFrame(sheet.worksheet(sheet_name).get_all_records())

def rupiah(x):
    return f"Rp {x:,.0f}"

def hitung_saldo_per_akun(df_trans, df_akun):
    df_trans["Nominal"] = pd.to_numeric(df_trans["Nominal"], errors="coerce")

    saldo_list = []

    for _, akun in df_akun.iterrows():
        nama = akun["Nama_Akun"]
        kategori = akun["Kategori_Akun"]

        df_filter = df_trans[df_trans["Nama_Akun"] == nama]

        total = 0

        for _, row in df_filter.iterrows():
            jenis = row["Jenis_Transaksi"]
            nominal = row["Nominal"]

            if kategori in ["Aset"]:
                if jenis in ["Pemasukan","Terima Piutang"]:
                    total += nominal
                elif jenis in ["Pengeluaran","Bayar Hutang"]:
                    total -= nominal

            elif kategori == "Kewajiban":
                if jenis in ["Pemasukan"]:
                    total += nominal
                elif jenis in ["Bayar Hutang"]:
                    total -= nominal

            elif kategori == "Pendapatan":
                if jenis == "Pemasukan":
                    total += nominal

            elif kategori == "Beban":
                if jenis == "Pengeluaran":
                    total += nominal

        saldo_list.append([nama, kategori, total])

    return pd.DataFrame(saldo_list, columns=["Nama_Akun","Kategori","Saldo"])

# ================= SIDEBAR ================= #

menu = st.sidebar.radio("Menu",[
    "📊 Dashboard",
    "📝 Input Transaksi",
    "📚 Daftar Akun",
    "📈 Laporan"
])

st.title("💰 Finance Tracker Pro v6")

# ================= DASHBOARD ================= #

if menu == "📊 Dashboard":

    df_trans = load("Transaksi")
    df_akun = load("Daftar_Akun")

    if df_trans.empty or df_akun.empty:
        st.info("Belum ada data.")
        st.stop()

    saldo_df = hitung_saldo_per_akun(df_trans, df_akun)

    total_aset = saldo_df[saldo_df["Kategori"]=="Aset"]["Saldo"].sum()
    total_kewajiban = saldo_df[saldo_df["Kategori"]=="Kewajiban"]["Saldo"].sum()

    col1,col2,col3 = st.columns(3)
    col1.metric("Total Aset", rupiah(total_aset))
    col2.metric("Total Kewajiban", rupiah(total_kewajiban))
    col3.metric("Ekuitas", rupiah(total_aset - total_kewajiban))

    st.markdown("### Saldo Per Akun")
    st.dataframe(saldo_df, use_container_width=True)

# ================= INPUT ================= #

elif menu == "📝 Input Transaksi":

    df_akun = load("Daftar_Akun")

    if df_akun.empty:
        st.warning("Tambahkan akun dulu.")
        st.stop()

    akun_list = df_akun["Nama_Akun"].tolist()

    with st.form("form_transaksi", clear_on_submit=True):
        tanggal = st.date_input("Tanggal")
        akun = st.selectbox("Nama Akun", akun_list)
        jenis = st.selectbox("Jenis Transaksi",
            ["Pemasukan","Pengeluaran","Bayar Hutang","Terima Piutang"]
        )
        nominal = st.number_input("Nominal", min_value=0)
        ket = st.text_area("Keterangan")

        if st.form_submit_button("Simpan"):
            sheet.worksheet("Transaksi").append_row(
                [str(tanggal), akun, jenis, nominal, ket]
            )
            st.success("✅ Transaksi dicatat")
            st.rerun()

# ================= DAFTAR AKUN ================= #

elif menu == "📚 Daftar Akun":

    with st.form("form_akun", clear_on_submit=True):
        nama = st.text_input("Nama Akun")
        kategori = st.selectbox("Kategori",
            ["Aset","Kewajiban","Pendapatan","Beban","Modal"]
        )

        if st.form_submit_button("Tambah"):
            sheet.worksheet("Daftar_Akun").append_row([nama,kategori])
            st.success("✅ Akun ditambahkan")
            st.rerun()

    df = load("Daftar_Akun")
    if not df.empty:
        st.dataframe(df, use_container_width=True)

# ================= LAPORAN ================= #

elif menu == "📈 Laporan":

    df_trans = load("Transaksi")
    df_akun = load("Daftar_Akun")

    if df_trans.empty or df_akun.empty:
        st.info("Belum ada data.")
        st.stop()

    saldo_df = hitung_saldo_per_akun(df_trans, df_akun)

    # LABA RUGI
    pendapatan = saldo_df[saldo_df["Kategori"]=="Pendapatan"]["Saldo"].sum()
    beban = saldo_df[saldo_df["Kategori"]=="Beban"]["Saldo"].sum()

    st.subheader("Laporan Laba Rugi")
    col1,col2,col3 = st.columns(3)
    col1.metric("Total Pendapatan", rupiah(pendapatan))
    col2.metric("Total Beban", rupiah(beban))
    col3.metric("Laba / Rugi", rupiah(pendapatan - beban))

    # NERACA
    aset = saldo_df[saldo_df["Kategori"]=="Aset"]["Saldo"].sum()
    kewajiban = saldo_df[saldo_df["Kategori"]=="Kewajiban"]["Saldo"].sum()
    modal = aset - kewajiban

    st.subheader("Neraca Sederhana")
    col1,col2,col3 = st.columns(3)
    col1.metric("Aset", rupiah(aset))
    col2.metric("Kewajiban", rupiah(kewajiban))
    col3.metric("Modal", rupiah(modal))
