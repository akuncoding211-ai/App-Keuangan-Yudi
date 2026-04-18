import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Finance Tracker Pro", layout="wide")

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_google_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1Ig-coNVWo1F-1JsCTalmnp0qLcLiR28-D5yN4fxkduk")
        return sheet
    except KeyError:
        st.error("❌ Secret 'gcp_service_account' tidak ditemukan.")
        return None
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Spreadsheet tidak ditemukan.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

# Definisikan kategori
KATEGORI_MAPPING = {
    # Pemasukan
    'Gaji': 'Pemasukan',
    'Bonus': 'Pemasukan',
    'Freelance': 'Pemasukan',
    'Investasi': 'Pemasukan',
    # Pengeluaran
    'Makan': 'Pengeluaran',
    'Bensin': 'Pengeluaran',
    'Listrik': 'Pengeluaran',
    'Internet': 'Pengeluaran',
    'Transport': 'Pengeluaran',
    # Tabungan
    'Liburan': 'Tabungan',
    'Pendidikan': 'Tabungan',
    'Rumah': 'Tabungan',
    'Mobil': 'Tabungan',
    # Hutang
    'Cicilan Motor': 'Hutang',
    'Cicilan Rumah': 'Hutang',
    'Hutang Teman': 'Hutang',
    # Piutang
    'Piutang Klien': 'Piutang',
    'Bonus Tertunda': 'Piutang',
}

st.sidebar.title("Navigasi")
menu = ["📊 Dashboard", "➕ Input Transaksi", "🏦 Manajemen Tabungan", "💰 Monitoring Budget", "📋 Kewajiban", "📈 Rekap Bulanan"]
choice = st.sidebar.selectbox("Pilih Menu", menu)

st.title("💰 Aplikasi Keuangan Pribadi")

sheet = get_google_sheet()

if sheet is None:
    st.warning("⚠️ Tidak dapat terhubung ke Google Sheets.")
else:
    try:
        # 1. DASHBOARD
        if choice == "📊 Dashboard":
            st.subheader("Ringkasan Keuangan Keseluruhan")
            
            df_trans = pd.DataFrame(sheet.worksheet("Transaksi").get_all_records())
            df_tab = pd.DataFrame(sheet.worksheet("Tabungan").get_all_records())
            df_kewajiban = pd.DataFrame(sheet.worksheet("Kewajiban").get_all_records())
            
            # Hitung Total Pemasukan
            if not df_trans.empty:
                df_trans['Nominal'] = pd.to_numeric(df_trans['Nominal'], errors='coerce')
                total_pemasukan = df_trans[df_trans['Tipe_Kategori'] == 'Pemasukan']['Nominal'].sum()
                total_pengeluaran = df_trans[df_trans['Tipe_Kategori'] == 'Pengeluaran']['Nominal'].sum()
            else:
                total_pemasukan = 0
                total_pengeluaran = 0
            
            # Total Tabungan
            if not df_tab.empty:
                df_tab['Jumlah_Saat_Ini'] = pd.to_numeric(df_tab['Jumlah_Saat_Ini'], errors='coerce')
                total_tabungan = df_tab['Jumlah_Saat_Ini'].sum()
            else:
                total_tabungan = 0
            
            # Total Hutang & Piutang
            if not df_kewajiban.empty:
                df_kewajiban['Nominal'] = pd.to_numeric(df_kewajiban['Nominal'], errors='coerce')
                total_hutang = df_kewajiban[df_kewajiban['Tipe'] == 'Hutang']['Nominal'].sum()
                total_piutang = df_kewajiban[df_kewajiban['Tipe'] == 'Piutang']['Nominal'].sum()
            else:
                total_hutang = 0
                total_piutang = 0
            
            # Saldo Akhir
            saldo_akhir = total_pemasukan - total_pengeluaran - total_hutang + total_piutang
            
            st.markdown("### 💹 Ringkasan Keuangan")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Pemasukan", f"Rp {total_pemasukan:,.0f}")
            col2.metric("Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
            col3.metric("Tabungan", f"Rp {total_tabungan:,.0f}")
            col4.metric("Saldo Akhir", f"Rp {saldo_akhir:,.0f}")
            
            col1, col2 = st.columns(2)
            col1.metric("Hutang", f"Rp {total_hutang:,.0f}")
            col2.metric("Piutang", f"Rp {total_piutang:,.0f}")
            
            st.markdown("### 📊 Breakdown Transaksi")
            col1, col2, col3 = st.columns(3)
            
            # Transaksi Biasa
            if not df_trans.empty:
                trans_regular = df_trans[df_trans['Tipe_Kategori'].isin(['Pemasukan', 'Pengeluaran'])]
                with col1:
                    st.write(f"**Transaksi Reguler:** {len(trans_regular)} item")
                    st.dataframe(trans_regular[['Kategori', 'Tipe_Kategori', 'Nominal']], use_container_width=True)
            
            # Tabungan
            if not df_tab.empty:
                with col2:
                    st.write(f"**Akun Tabungan:** {len(df_tab)} akun")
                    for _, row in df_tab.iterrows():
                        target = float(row['Target_Jumlah']) if row['Target_Jumlah'] else 1
                        current = float(row['Jumlah_Saat_Ini']) if row['Jumlah_Saat_Ini'] else 0
                        progress = min(current / target, 1.0)
                        st.write(f"**{row['Nama_Akun']}**")
                        st.progress(progress)
                        st.write(f"Rp {current:,.0f} / Rp {target:,.0f}")
            
            # Hutang & Piutang
            if not df_kewajiban.empty:
                with col3:
                    st.write(f"**Kewajiban:** {len(df_kewajiban)} item")
                    for _, row in df_kewajiban.iterrows():
                        badge = "💳" if row['Tipe'] == 'Hutang' else "💰"
                        st.write(f"{badge} {row['Nama_Kewajiban']} - Rp {row['Nominal']:,.0f} ({row['Status']})")

        # 2. INPUT TRANSAKSI
        elif choice == "➕ Input Transaksi":
            st.subheader("Tambah Transaksi Baru")
            
            with st.form("form_transaksi", clear_on_submit=True):
                tgl = st.date_input("Tanggal")
                
                # Dropdown Kategori
                kategori_list = list(KATEGORI_MAPPING.keys())
                kat = st.selectbox("Kategori", kategori_list)
                
                # Auto-detect Tipe Kategori
                tipe_kategori = KATEGORI_MAPPING[kat]
                st.info(f"📌 Tipe: {tipe_kategori}")
                
                nom = st.number_input("Nominal", step=1000, min_value=0)
                ket = st.text_area("Keterangan")
                
                # Conditional input untuk Hutang & Piutang
                pemilik_hutang = None
                pihak_penghutang = None
                
                if tipe_kategori == 'Hutang':
                    pemilik_hutang = st.text_input("Nama Pemilik Hutang/Bank", value="")
                
                if tipe_kategori == 'Piutang':
                    pihak_penghutang = st.text_input("Pihak yang Menghutang", value="")
                
                if st.form_submit_button("Simpan"):
                    # Router berdasarkan Tipe Kategori
                    if tipe_kategori in ['Pemasukan', 'Pengeluaran']:
                        # Masuk sheet Transaksi
                        sheet.worksheet("Transaksi").append_row([str(tgl), kat, tipe_kategori, nom, ket, tipe_kategori])
                        st.success("✅ Transaksi tersimpan!")
                    
                    elif tipe_kategori == 'Tabungan':
                        # Masuk sheet Transaksi
                        sheet.worksheet("Transaksi").append_row([str(tgl), kat, 'Pengeluaran', nom, ket, 'Tabungan'])
                        
                        # Update sheet Tabungan
                        df_tab = pd.DataFrame(sheet.worksheet("Tabungan").get_all_records())
                        for idx, row in df_tab.iterrows():
                            if row['Nama_Akun'] == kat:
                                current_amount = float(row['Jumlah_Saat_Ini']) if row['Jumlah_Saat_Ini'] else 0
                                new_amount = current_amount + nom
                                sheet.worksheet("Tabungan").update_cell(idx + 2, 3, new_amount)
                                break
                        
                        st.success("✅ Transaksi & Akun Tabungan ter-update!")
                    
                    elif tipe_kategori == 'Hutang':
                        # Masuk sheet Kewajiban
                        sheet.worksheet("Kewajiban").append_row([pemilik_hutang or kat, nom, str(tgl), "Belum Lunas", "Hutang", pemilik_hutang or ""])
                        st.success("✅ Hutang tersimpan!")
                    
                    elif tipe_kategori == 'Piutang':
                        # Masuk sheet Kewajiban
                        sheet.worksheet("Kewajiban").append_row([kat, nom, str(tgl), "Belum Tertagih", "Piutang", pihak_penghutang or ""])
                        st.success("✅ Piutang tersimpan!")
                    
                    st.rerun()

        # 3. MANAJEMEN TABUNGAN
        elif choice == "🏦 Manajemen Tabungan":
            st.subheader("Kelola Akun Tabungan")
            
            with st.form("form_akun", clear_on_submit=True):
                nama_akun = st.text_input("Nama Akun")
                target = st.number_input("Target Jumlah", step=100000, min_value=0)
                awal = st.number_input("Jumlah Saat Ini", step=10000, min_value=0)
                
                if st.form_submit_button("Buat Akun"):
                    sheet.worksheet("Tabungan").append_row([nama_akun, target, awal, str(datetime.now().date())])
                    st.success("✅ Akun berhasil dibuat!")
                    st.rerun()
            
            st.markdown("### Daftar Akun Tabungan")
            df_tab = pd.DataFrame(sheet.worksheet("Tabungan").get_all_records())
            if not df_tab.empty:
                st.dataframe(df_tab, use_container_width=True)

        # 4. MONITORING BUDGET
        elif choice == "💰 Monitoring Budget":
            st.subheader("Monitoring Budget vs Pengeluaran")
            
            df_trans = pd.DataFrame(sheet.worksheet("Transaksi").get_all_records())
            df_budget = pd.DataFrame(sheet.worksheet("Budget").get_all_records())
            
            if not df_trans.empty and not df_budget.empty:
                df_trans['Nominal'] = pd.to_numeric(df_trans['Nominal'], errors='coerce')
                df_budget['Budget'] = pd.to_numeric(df_budget['Budget'], errors='coerce')
                
                # Hitung pengeluaran per kategori
                pengeluaran = df_trans[df_trans['Tipe_Kategori'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum().reset_index()
                pengeluaran.rename(columns={'Nominal': 'Pengeluaran'}, inplace=True)
                
                # Merge dengan budget
                budget_vs_actual = pd.merge(df_budget, pengeluaran, on='Kategori', how='left').fillna(0)
                budget_vs_actual['Selisih'] = budget_vs_actual['Budget'] - budget_vs_actual['Pengeluaran']
                budget_vs_actual['Status'] = budget_vs_actual.apply(
                    lambda row: '✅ OK' if row['Selisih'] >= 0 else '❌ MELEBIHI',
                    axis=1
                )
                
                st.dataframe(budget_vs_actual, use_container_width=True)
                
                chart_data = budget_vs_actual.set_index('Kategori')[['Budget', 'Pengeluaran']]
                st.bar_chart(chart_data)
            else:
                st.info("ℹ️ Data Budget atau Transaksi belum tersedia.")

        # 5. KEWAJIBAN
        elif choice == "📋 Kewajiban":
            st.subheader("Daftar Kewajiban (Hutang & Piutang)")
            
            df_kewajiban = pd.DataFrame(sheet.worksheet("Kewajiban").get_all_records())
            
            if not df_kewajiban.empty:
                # Pisahkan Hutang dan Piutang
                hutang = df_kewajiban[df_kewajiban['Tipe'] == 'Hutang']
                piutang = df_kewajiban[df_kewajiban['Tipe'] == 'Piutang']
                
                st.markdown("### 💳 Hutang")
                if not hutang.empty:
                    st.dataframe(hutang, use_container_width=True)
                else:
                    st.info("Tidak ada hutang")
                
                st.markdown("### 💰 Piutang")
                if not piutang.empty:
                    st.dataframe(piutang, use_container_width=True)
                else:
                    st.info("Tidak ada piutang")
            else:
                st.info("ℹ️ Belum ada data kewajiban.")

        # 6. REKAP BULANAN
        elif choice == "📈 Rekap Bulanan":
            st.subheader("📈 Rekap Keuangan Bulanan")
            
            df_rekap = pd.DataFrame(sheet.worksheet("Rekap_Bulanan").get_all_records())
            
            if not df_rekap.empty:
                df_rekap['Total_Pemasukan'] = pd.to_numeric(df_rekap['Total_Pemasukan'], errors='coerce')
                df_rekap['Total_Pengeluaran'] = pd.to_numeric(df_rekap['Total_Pengeluaran'], errors='coerce')
                df_rekap['Total_Tabungan'] = pd.to_numeric(df_rekap['Total_Tabungan'], errors='coerce')
                df_rekap['Total_Hutang'] = pd.to_numeric(df_rekap['Total_Hutang'], errors='coerce')
                df_rekap['Total_Piutang'] = pd.to_numeric(df_rekap['Total_Piutang'], errors='coerce')
                
                # Filter Bulan
                st.markdown("### 🔍 Filter Data")
                bulan_pilih = st.selectbox("Pilih Bulan", df_rekap['Bulan_Tahun'].values)
                
                data_bulan = df_rekap[df_rekap['Bulan_Tahun'] == bulan_pilih].iloc[0]
                
                # METRICS
                st.markdown("### 💹 Ringkasan Bulanan")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Pemasukan", f"Rp {data_bulan['Total_Pemasukan']:,.0f}")
                col2.metric("Pengeluaran", f"Rp {data_bulan['Total_Pengeluaran']:,.0f}")
                col3.metric("Tabungan", f"Rp {data_bulan['Total_Tabungan']:,.0f}")
                col4.metric("Saldo", f"Rp {data_bulan['Total_Pemasukan'] - data_bulan['Total_Pengeluaran']:,.0f}")
                
                col1, col2 = st.columns(2)
                col1.metric("Hutang", f"Rp {data_bulan['Total_Hutang']:,.0f}")
                col2.metric("Piutang", f"Rp {data_bulan['Total_Piutang']:,.0f}")
                
                # STATUS
                st.markdown("### 📊 Status Keuangan")
                if data_bulan['Status'] == 'Positif':
                    st.success("✅ STATUS POSITIF")
                else:
                    st.error("❌ STATUS NEGATIF")
                
                # CHARTS
                st.markdown("### 📈 Trend Bulanan")
                chart_data = df_rekap[['Bulan_Tahun', 'Total_Pemasukan', 'Total_Pengeluaran', 'Total_Tabungan']].set_index('Bulan_Tahun')
                st.line_chart(chart_data)
                
                st.markdown("### 💰 Analisis Detail")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Pengeluaran per Bulan")
                    pengeluaran_chart = df_rekap[['Bulan_Tahun', 'Total_Pengeluaran']].set_index('Bulan_Tahun')
                    st.bar_chart(pengeluaran_chart)
                
                with col2:
                    st.subheader("Komposisi Keuangan")
                    pie_data = pd.DataFrame({
                        'Kategori': ['Pemasukan', 'Pengeluaran', 'Tabungan'],
                        'Nominal': [
                            data_bulan['Total_Pemasukan'],
                            data_bulan['Total_Pengeluaran'],
                            data_bulan['Total_Tabungan']
                        ]
                    })
                    fig_pie = px.pie(pie_data, names='Kategori', values='Nominal')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # TABLE
                st.markdown("### 📋 Detail Rekap Bulanan")
                st.dataframe(df_rekap, use_container_width=True)
                
                # PDF EXPORT
                st.markdown("### 📥 Export Laporan")
                if st.button("📄 Generate Laporan Keuangan PDF", key="btn_pdf"):
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.lib.units import inch
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                    from reportlab.lib import colors
                    import io
                    
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
                    elements = []
                    styles = getSampleStyleSheet()
                    
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=24,
                        textColor=colors.HexColor('#2E86C1'),
                        spaceAfter=30,
                        alignment=1
                    )
                    
                    heading_style = ParagraphStyle(
                        'CustomHeading',
                        parent=styles['Heading2'],
                        fontSize=14,
                        textColor=colors.HexColor('#2E86C1'),
                        spaceAfter=12,
                        spaceBefore=12
                    )
                    
                    elements.append(Paragraph("📊 LAPORAN KEUANGAN BULANAN", title_style))
                    elements.append(Spacer(1, 0.2*inch))
                    elements.append(Paragraph(f"<b>Periode:</b> {bulan_pilih}", styles['Normal']))
                    elements.append(Spacer(1, 0.3*inch))
                    
                    elements.append(Paragraph("📈 RINGKASAN KEUANGAN", heading_style))
                    summary_data = [
                        ['Keterangan', 'Nominal'],
                        ['Total Pemasukan', f"Rp {data_bulan['Total_Pemasukan']:,.0f}"],
                        ['Total Pengeluaran', f"Rp {data_bulan['Total_Pengeluaran']:,.0f}"],
                        ['Total Tabungan', f"Rp {data_bulan['Total_Tabungan']:,.0f}"],
                        ['Total Hutang', f"Rp {data_bulan['Total_Hutang']:,.0f}"],
                        ['Total Piutang', f"Rp {data_bulan['Total_Piutang']:,.0f}"],
                        ['Saldo Akhir', f"Rp {data_bulan['Total_Pemasukan'] - data_bulan['Total_Pengeluaran']:,.0f}"],
                        ['Status', data_bulan['Status']]
                    ]
                    
                    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(summary_table)
                    elements.append(Spacer(1, 0.5*inch))
                    
                    footer_text = Paragraph(
                        f"<i>Laporan dibuat pada {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</i>",
                        styles['Normal']
                    )
                    elements.append(footer_text)
                    
                    doc.build(elements)
                    pdf_buffer.seek(0)
                    
                    st.download_button(
                        label="✅ Download PDF Laporan",
                        data=pdf_buffer,
                        file_name=f"Laporan_Keuangan_{bulan_pilih.replace('/', '-')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("✅ PDF berhasil dibuat!")
            else:
                st.info("ℹ️ Belum ada data rekap bulanan.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Pastikan semua sheet sudah ada dan struktur data benar.")
