import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

# Setup Halaman
st.set_page_config(page_title="Finance Tracker Pro", layout="wide")

# Konfigurasi Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

def get_google_sheet():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1Ig-coNVWo1F-1JsCTalmnp0qLcLiR28-D5yN4fxkduk")
    return sheet

# Navigasi Sidebar
st.sidebar.title("Navigasi")
menu = ["📊 Dashboard", "➕ Input Transaksi", "🏦 Manajemen Tabungan", "💰 Monitoring Budget", "📋 Kewajiban"]
choice = st.sidebar.selectbox("Pilih Menu", menu)

st.title("💰 Aplikasi Keuangan Pribadi")

try:
    sheet = get_google_sheet()
    
    # 1. Dashboard
    if choice == "📊 Dashboard":
        st.subheader("Ringkasan Keuangan")
        df_trans = pd.DataFrame(sheet.worksheet("Transaksi").get_all_records())
        df_tab = pd.DataFrame(sheet.worksheet("Tabungan").get_all_records())
        
        if not df_trans.empty:
            total_masuk = df_trans[df_trans['Tipe'] == 'Pemasukan']['Nominal'].sum()
            total_keluar = df_trans[df_trans['Tipe'] == 'Pengeluaran']['Nominal'].sum()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Pemasukan", f"Rp {total_masuk:,}")
            col2.metric("Pengeluaran", f"Rp {total_keluar:,}")
            col3.metric("Saldo", f"Rp {total_masuk - total_keluar:,}")
            
            # Progress Tabungan
            st.markdown("### Progress Tabungan")
            for _, row in df_tab.iterrows():
                progress = min(float(row['Jumlah_Saat_Ini']) / float(row['Target_Jumlah']), 1.0)
                st.write(f"**{row['Nama_Akun']}**")
                st.progress(progress)
                st.write(f"Rp {row['Jumlah_Saat_Ini']:,} / Rp {row['Target_Jumlah']:,}")

    # 2. Input Transaksi
    elif choice == "➕ Input Transaksi":
        with st.form("form_transaksi", clear_on_submit=True):
            tgl = st.date_input("Tanggal")
            kat = st.text_input("Kategori")
            tipe = st.selectbox("Tipe", ["Pemasukan", "Pengeluaran"])
            nom = st.number_input("Nominal (Rp)", step=1000)
            ket = st.text_area("Keterangan")
            if st.form_submit_button("Simpan"):
                sheet.worksheet("Transaksi").append_row(["", str(tgl), kat, tipe, nom, ket])
                st.success("Transaksi tersimpan!")

    # 3. Manajemen Tabungan
    elif choice == "🏦 Manajemen Tabungan":
        st.subheader("Kelola Akun Tabungan")
        with st.form("form_akun", clear_on_submit=True):
            nama_akun = st.text_input("Nama Akun (misal: BCA, Dana)")
            target = st.number_input("Target Jumlah (Rp)", step=100000)
            awal = st.number_input("Saldo Awal (Rp)", step=10000)
            if st.form_submit_button("Buat Akun"):
                sheet.worksheet("Tabungan").append_row([nama_akun, target, awal, str(datetime.now().date())])
                st.success("Akun berhasil dibuat!")
        
        df_tab = pd.DataFrame(sheet.worksheet("Tabungan").get_all_records())
        st.table(df_tab)

    # 4. Monitoring Budget
    elif choice == "💰 Monitoring Budget":
        df_trans = pd.DataFrame(sheet.worksheet("Transaksi").get_all_records())
        df_budget = pd.DataFrame(sheet.worksheet("Budget").get_all_records())
        pengeluaran = df_trans[df_trans['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum().reset_index()
        budget_vs_actual = pd.merge(df_budget, pengeluaran, on='Kategori', how='left').fillna(0)
        st.dataframe(budget_vs_actual, use_container_width=True)

    # 5. Kewajiban
    elif choice == "📋 Kewajiban":
        df_kew = pd.DataFrame(sheet.worksheet("Kewajiban").get_all_records())
        st.dataframe(df_kew, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Finance Tracker Pro v2.0</p>", unsafe_allow_html=True)
