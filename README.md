# Finance Tracker App

Aplikasi keuangan pribadi terhubung ke Google Sheets.

## Deployment:
1. Pastikan Sheet sudah memiliki tab: `Transaksi` dan `Kewajiban`.
2. Berikan akses **Editor** ke email service account Anda pada Google Sheets.
3. Di **Streamlit Cloud Dashboard**, buka bagian **Secrets**.
4. Tambahkan key: `gcp_service_account`
5. Isi nilainya dengan seluruh teks **JSON** dari file kunci *service account* Anda.
6. Klik **Deploy**.
