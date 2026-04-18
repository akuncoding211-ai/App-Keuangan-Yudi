import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# Setup Halaman
st.set_page_config(page_title="Finance Tracker Pro", layout="wide")

# Konfigurasi Akses Google Sheets
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

# Navigasi Sidebar
st.sidebar.title("Navigasi")
menu = ["📊 Dashboard", "➕ Input Transaksi", "🏦 Manajemen Tabungan", "💰 Monitoring Budget", "📋 Kewajiban", "📈 Rekap Bulanan"]
choice = st.sidebar.selectbox("Pilih Menu", menu)

st.title("💰 Aplikasi Keuangan Pribadi")

sheet = get_google_sheet()

if sheet is None:
    st.warning("⚠️ Tidak dapat terhubung ke Google Sheets.")
else:
    try:
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
                
                st.markdown("### Progress Tabungan")
                for _, row in df_tab.iterrows():
                    target = float(row['Target_Jumlah']) if row['Target_Jumlah'] else 1
                    current = float(row['Jumlah_Saat_Ini']) if row['Jumlah_Saat_Ini'] else 0
                    progress = min(current / target, 1.0)
                    st.write(f"**{row['Nama_Akun']}**")
                    st.progress(progress)
                    st.write(f"Rp {current:,.0f} / Rp {target:,.0f}")
            else:
                st.info("ℹ️ Belum ada data transaksi.")

        # 2. Input Transaksi
        elif choice == "➕ Input Transaksi":
            with st.form("form_transaksi", clear_on_submit=True):
                tgl = st.date_input("Tanggal")
                kat = st.text_input("Kategori")
                tipe = st.selectbox("Tipe", ["Pemasukan", "Pengeluaran"])
                nom = st.number_input("Nominal", step=1000)
                ket = st.text_area("Keterangan")
                if st.form_submit_button("Simpan"):
                    sheet.worksheet("Transaksi").append_row([str(tgl), kat, tipe, nom, ket])
                    st.success("✅ Transaksi tersimpan!")
                    st.rerun()

        # 3. Manajemen Tabungan
        elif choice == "🏦 Manajemen Tabungan":
            st.subheader("Kelola Akun Tabungan")
            with st.form("form_akun", clear_on_submit=True):
                nama_akun = st.text_input("Nama Akun")
                target = st.number_input("Target Jumlah", step=100000)
                awal = st.number_input("Jumlah Saat Ini", step=10000)
                if st.form_submit_button("Buat Akun"):
                    sheet.worksheet("Tabungan").append_row([nama_akun, target, awal, str(datetime.now().date())])
                    st.success("✅ Akun berhasil dibuat!")
                    st.rerun()
            st.table(pd.DataFrame(sheet.worksheet("Tabungan").get_all_records()))

        # 4. Monitoring Budget
        elif choice == "💰 Monitoring Budget":
            st.subheader("Monitoring Budget vs Pengeluaran")
            df_trans = pd.DataFrame(sheet.worksheet("Transaksi").get_all_records())
            df_budget = pd.DataFrame(sheet.worksheet("Budget").get_all_records())
            
            pengeluaran = df_trans[df_trans['Tipe'] == 'Pengeluaran'].groupby('Kategori')['Nominal'].sum().reset_index()
            pengeluaran.rename(columns={'Nominal': 'Pengeluaran'}, inplace=True)
            
            budget_vs_actual = pd.merge(df_budget, pengeluaran, on='Kategori', how='left').fillna(0)
            budget_vs_actual['Selisih'] = budget_vs_actual['Budget'] - budget_vs_actual['Pengeluaran']
            budget_vs_actual['Status'] = budget_vs_actual.apply(
                lambda row: '✅ OK' if row['Selisih'] >= 0 else '❌ MELEBIHI', 
                axis=1
            )
            
            st.dataframe(budget_vs_actual, use_container_width=True)
            st.bar_chart(budget_vs_actual.set_index('Kategori')[['Budget', 'Pengeluaran']])

        # 5. Kewajiban
        elif choice == "📋 Kewajiban":
            st.subheader("Daftar Kewajiban")
            st.dataframe(pd.DataFrame(sheet.worksheet("Kewajiban").get_all_records()), use_container_width=True)

        # 6. Rekap Bulanan
        elif choice == "📈 Rekap Bulanan":
            st.subheader("📈 Rekap Keuangan Bulanan")
            df_rekap = pd.DataFrame(sheet.worksheet("Rekap Bulanan").get_all_records())
            
            if not df_rekap.empty:
                # Filter Bulan
                st.markdown("### 🔍 Filter Data")
                bulan_pilih = st.selectbox("Pilih Bulan", df_rekap['Bulan_Tahun'], key='bulan_rekap')
                
                # Ambil data bulan yang dipilih
                data_bulan = df_rekap[df_rekap['Bulan_Tahun'] == bulan_pilih].iloc[0]
                
                # SECTION 1: METRICS SUMMARY
                st.markdown("### 💹 Ringkasan Bulanan")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Total Pemasukan", f"Rp {data_bulan['Total_Pemasukan']:,.0f}", delta="✅ Masuk")
                col2.metric("Total Pengeluaran", f"Rp {data_bulan['Total_Pengeluaran']:,.0f}", delta="❌ Keluar")
                col3.metric("Total Tabungan", f"Rp {data_bulan['Total_Tabungan']:,.0f}", delta="💰 Ditabung")
                col4.metric("Saldo Akhir", f"Rp {data_bulan['Total_Pemasukan'] - data_bulan['Total_Pengeluaran']:,.0f}", delta=data_bulan['Status'])
                
                # SECTION 2: STATUS BADGE
                st.markdown("### 📊 Status Keuangan")
                if data_bulan['Status'] == 'Positif':
                    st.success("✅ STATUS POSITIF - Pengeluaran lebih kecil dari pemasukan")
                else:
                    st.error("❌ STATUS NEGATIF - Pengeluaran melebihi pemasukan")
                
                # SECTION 3: TREND CHART
                st.markdown("### 📈 Trend Pemasukan vs Pengeluaran")
                chart_data = df_rekap[['Bulan_Tahun', 'Total_Pemasukan', 'Total_Pengeluaran']].set_index('Bulan_Tahun')
                st.line_chart(chart_data, use_container_width=True)
                
                # SECTION 4: SIDE BY SIDE CHARTS
                st.markdown("### 💰 Analisis Detail")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Tabungan per Bulan")
                    tabungan_chart = df_rekap[['Bulan_Tahun', 'Total_Tabungan']].set_index('Bulan_Tahun')
                    st.bar_chart(tabungan_chart, use_container_width=True)
                
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
                    fig_pie = px.pie(pie_data, names='Kategori', values='Nominal', hole=0.3)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # SECTION 5: DETAIL TABLE
                st.markdown("### 📋 Detail Rekap Bulanan")
                st.dataframe(df_rekap, use_container_width=True)
                
                # SECTION 6: PDF DOWNLOAD
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
                    elements.append(Spacer(1, 0.3*inch))
                    
                    elements.append(Paragraph("📋 DETAIL REKAP BULANAN", heading_style))
                    rekap_data = [['Bulan_Tahun', 'Total_Pemasukan', 'Total_Pengeluaran', 'Total_Tabungan', 'Status']]
                    for _, row in df_rekap.iterrows():
                        rekap_data.append([
                            row['Bulan_Tahun'],
                            f"Rp {row['Total_Pemasukan']:,.0f}",
                            f"Rp {row['Total_Pengeluaran']:,.0f}",
                            f"Rp {row['Total_Tabungan']:,.0f}",
                            row['Status']
                        ])
                    
                    rekap_table = Table(rekap_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 0.8*inch])
                    rekap_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                    ]))
                    elements.append(rekap_table)
                    elements.append(Spacer(1, 0.5*inch))
                    
                    footer_text = Paragraph(
                        f"<i>Laporan ini dibuat pada {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</i>",
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
                    st.success("✅ PDF Laporan berhasil dibuat!")
            
            else:
                st.info("ℹ️ Belum ada data rekap bulanan.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("Tip: Pastikan semua sheet sudah ada di spreadsheet Anda.")
