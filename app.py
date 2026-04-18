    # 6. Rekap Bulanan
    elif choice == "📈 Rekap Bulanan":
        st.subheader("📈 Rekap Keuangan Bulanan")
        df_rekap = pd.DataFrame(sheet.worksheet("Rekap Bulanan").get_all_records())
        
        if not df_rekap.empty:
            # Filter Bulan
            st.markdown("### 🔍 Filter Data")
            col1, col2 = st.columns([3, 1])
            with col1:
                bulan_pilih = st.selectbox("Pilih Bulan", df_rekap['Bulan_Tahun'], key='bulan_rekap')
            
            # Ambil data bulan yang dipilih
            data_bulan = df_rekap[df_rekap['Bulan_Tahun'] == bulan_pilih].iloc[0]
            
            # ===== SECTION 1: METRICS SUMMARY =====
            st.markdown("### 💹 Ringkasan Bulanan")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(
                "Total Pemasukan",
                f"Rp {data_bulan['Total_Pemasukan']:,.0f}",
                delta="✅ Masuk",
                delta_color="normal"
            )
            col2.metric(
                "Total Pengeluaran",
                f"Rp {data_bulan['Total_Pengeluaran']:,.0f}",
                delta="❌ Keluar",
                delta_color="inverse"
            )
            col3.metric(
                "Total Tabungan",
                f"Rp {data_bulan['Total_Tabungan']:,.0f}",
                delta="💰 Ditabung"
            )
            col4.metric(
                "Saldo Akhir",
                f"Rp {data_bulan['Total_Pemasukan'] - data_bulan['Total_Pengeluaran']:,.0f}",
                delta=data_bulan['Status'],
                delta_color="normal" if data_bulan['Status'] == 'Positif' else 'inverse'
            )
            
            # ===== SECTION 2: STATUS BADGE =====
            st.markdown("### 📊 Status Keuangan")
            if data_bulan['Status'] == 'Positif':
                st.success("✅ STATUS POSITIF - Pengeluaran lebih kecil dari pemasukan")
            else:
                st.error("❌ STATUS NEGATIF - Pengeluaran melebihi pemasukan")
            
            # ===== SECTION 3: TREND CHART =====
            st.markdown("### 📈 Trend Pemasukan vs Pengeluaran")
            chart_data = df_rekap[['Bulan_Tahun', 'Total_Pemasukan', 'Total_Pengeluaran']].set_index('Bulan_Tahun')
            st.line_chart(chart_data, use_container_width=True)
            
            # ===== SECTION 4: SIDE BY SIDE CHARTS =====
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
            
            # ===== SECTION 5: DETAIL TABLE =====
            st.markdown("### 📋 Detail Rekap Bulanan")
            st.dataframe(df_rekap, use_container_width=True)
            
            # ===== SECTION 6: PDF DOWNLOAD =====
            st.markdown("### 📥 Export Laporan")
            if st.button("📄 Generate Laporan Keuangan PDF", key="btn_pdf"):
                # Generate PDF
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
                from reportlab.lib import colors
                from datetime import datetime
                import io
                
                # Create PDF buffer
                pdf_buffer = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
                
                # Container untuk elements
                elements = []
                styles = getSampleStyleSheet()
                
                # Custom styles
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    textColor=colors.HexColor('#2E86C1'),
                    spaceAfter=30,
                    alignment=1  # Center
                )
                
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#2E86C1'),
                    spaceAfter=12,
                    spaceBefore=12
                )
                
                # Title
                elements.append(Paragraph("📊 LAPORAN KEUANGAN BULANAN", title_style))
                elements.append(Spacer(1, 0.2*inch))
                
                # Bulan info
                bulan_text = Paragraph(f"<b>Periode:</b> {bulan_pilih}", styles['Normal'])
                elements.append(bulan_text)
                elements.append(Spacer(1, 0.3*inch))
                
                # Summary Table
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
                
                # Detail Rekap
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
                
                # Footer
                footer_text = Paragraph(
                    f"<i>Laporan ini dibuat secara otomatis oleh Aplikasi Keuangan Pribadi pada {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</i>",
                    styles['Normal']
                )
                elements.append(footer_text)
                
                # Build PDF
                doc.build(elements)
                pdf_buffer.seek(0)
                
                # Download button
                st.download_button(
                    label="✅ Download PDF Laporan",
                    data=pdf_buffer,
                    file_name=f"Laporan_Keuangan_{bulan_pilih.replace('/', '-')}.pdf",
                    mime="application/pdf"
                )
                st.success("✅ PDF Laporan berhasil dibuat!")
        
        else:
            st.info("ℹ️ Belum ada data rekap bulanan.")
