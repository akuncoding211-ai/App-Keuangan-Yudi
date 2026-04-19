import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Finance Tracker Pro v5", layout="wide")

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

def ensure_sheet_structure():
    try:
        ws = sheet.worksheet("Transaksi")
    except:
        ws = sheet.add_worksheet(title="Transaksi", rows="1000", cols="10")
    
    headers = ws.row_values(1)
    new_headers = ["Tanggal","Nama_Akun","Jenis_Transaksi","Nominal","Keterangan"]

    if headers != new_headers:
        ws.clear()
        ws.append_row(new_headers)

    # Daftar Akun
    try:
        ws2 = sheet.worksheet("Daftar_Akun")
    except:
        ws2 = sheet.add_worksheet(title="Daftar_Akun", rows="100", cols="5")
        ws2.append_row(["Nama_Akun","Kategori_Akun"])

ensure_sheet_structure()

# ================= HELPERS ================= #

def load(sheet_name):
    df = pd.DataFrame(sheet.worksheet(sheet_name).get_all_records())
    return df

def rupiah(x):
    return f"Rp {x:,.0f}"

# ================= SIDEBAR ================= #

menu = st.sidebar.radio("Menu",[
    "📊 Dashboard",
    "📝 Input Transaksi",
    "📚 Daftar Akun",
    "📈 Rekap"
])

st.title("💰 Finance Tracker Pro v5")

# ================= DASHBOARD ================= #

if menu == "📊 Dashboard":

    df = load("Transaksi")

    if df.empty:
        st.info("Belum ada transaksi.")
        st.stop()

    df["Nominal"] = pd.to_numeric(df["Nominal"], errors="coerce")

    pemasukan = df[df["Jenis_Transaksi"]=="Pemasukan"]["Nominal"].sum()
    pengeluaran = df[df["Jenis_Transaksi"]=="Pengeluaran"]["Nominal"].sum()

    saldo = pemasukan - pengeluaran

    col1,col2,col3 = st.columns(3)
    col1.metric("Total Pemasukan", rupiah(pemasukan))
    col2.metric("Total Pengeluaran", rupiah(pengeluaran))
    col3.metric("Saldo", rupiah(saldo))

    st.markdown("### Semua Transaksi")
    st.dataframe(df, use_container_width=True)

# ================= INPUT TRANSAKSI ================= #

elif menu == "📝 Input Transaksi":

    df_akun = load("Daftar_Akun")

    if df_akun.empty:
        st.warning("Belum ada akun. Tambahkan dulu di menu Daftar Akun.")
        st.stop()

    akun_list = df_akun["Nama_Akun"].tolist()

    with st.form("form_transaksi", clear_on_submit=True):
        tanggal = st.date_input("Tanggal")
        akun = st.selectbox("Nama Akun", akun_list)
        jenis = st.selectbox("Jenis Transaksi",
            ["Pemasukan","Pengeluaran","Bayar Hutang","Terima Piutang","Tabungan","Budget"]
        )
        nominal = st.number_input("Nominal", min_value=0)
        ket = st.text_area("Keterangan")

        if st.form_submit_button("Simpan"):
            sheet.worksheet("Transaksi").append_row(
                [str(tanggal), akun, jenis, nominal, ket]
            )
            st.success("✅ Transaksi berhasil dicatat")
            st.rerun()

# ================= DAFTAR AKUN ================= #

elif menu == "📚 Daftar Akun":

    with st.form("form_akun", clear_on_submit=True):
        nama = st.text_input("Nama Akun")
        kategori = st.selectbox("Kategori Akun",
            ["Aset","Kewajiban","Pendapatan","Beban","Tabungan","Budget"]
        )

        if st.form_submit_button("Tambah Akun"):
            sheet.worksheet("Daftar_Akun").append_row([nama,kategori])
            st.success("✅ Akun ditambahkan")
            st.rerun()

    df = load("Daftar_Akun")
    if not df.empty:
        st.dataframe(df, use_container_width=True)

# ================= REKAP ================= #

elif menu == "📈 Rekap":

    df = load("Transaksi")

    if df.empty:
        st.info("Belum ada transaksi.")
        st.stop()

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df["Nominal"] = pd.to_numeric(df["Nominal"], errors="coerce")
    df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)

    rekap = df.groupby(["Bulan","Jenis_Transaksi"])["Nominal"] \
        .sum().unstack().fillna(0)

    st.dataframe(rekap, use_container_width=True)
    st.line_chart(rekap)
