from datetime import datetime
import os
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Sistem Absensi & Honorarium MTs Miftahul Ulum Bettet",
    page_icon="🏫",
    layout="wide",
)

FILE_EXCEL = "JADWAL 2026-2027 GANJIL.xlsx"
FILE_ABSEN = "rekap_absensi.xlsx"

# Tarif Honorarium
TARIF_HARIAN = 10000  # Rp 10.000 per hari hadir/dinas luar
TARIF_JTM = 6000  # Rp 6.000 per Jam Tatap Muka


# Fungsi untuk otomatis membaca data master jadwal
@st.cache_data
def load_data(file_path):
  if not os.path.exists(file_path):
    return None
  try:
    df_raw = pd.read_excel(file_path, header=None)
    header_row = 0
    for idx, row in df_raw.iterrows():
      row_str = row.astype(str).str.upper().values
      if any("HARI" in str(val) for val in row_str) and any(
          "JAM" in str(val) for val in row_str
      ):
        header_row = idx
        break
    df = pd.read_excel(file_path, header=header_row)
    return df
  except Exception as e:
    st.error(f"Gagal membaca file Excel: {e}")
    return None


# Fungsi untuk memuat atau membuat file database absensi
def load_absensi():
  if os.path.exists(FILE_ABSEN):
    return pd.read_excel(FILE_ABSEN)
  else:
    return pd.DataFrame(
        columns=["Tanggal", "Nama Guru", "Status", "Jumlah JTM", "Total Honor"]
    )


# Fungsi untuk menyimpan data absensi
def save_absensi(df_absen):
  df_absen.to_excel(FILE_ABSEN, index=False)


# Sidebar Navigasi & Login Role
st.sidebar.title("🏫 Portal Madrasah")
st.sidebar.subheader("MTs Miftahul Ulum Bettet")

role = st.sidebar.radio(
    "Pilih Hak Akses:", ["Portal Guru (Lihat Jadwal)", "Login Admin / Kurikulum"]
)

df_jadwal = load_data(FILE_EXCEL)

if df_jadwal is None:
  st.error(
      f"File Excel '{FILE_EXCEL}' tidak ditemukan di dalam folder kerja Anda!"
  )
  st.stop()

# Deteksi kolom nama guru (indeks 39 atau kolom NAMA)
col_guru = None
for col in df_jadwal.columns:
  if "NAMA" in str(col).upper():
    col_guru = col
    break
if not col_guru and len(df_jadwal.columns) > 39:
  col_guru = df_jadwal.columns[39]

# Ambil daftar nama guru yang bersih
daftar_guru = []
if col_guru is not None:
  raw_list = df_jadwal[col_guru].dropna().unique().tolist()
  daftar_guru = sorted(
      [
          str(x).strip()
          for x in raw_list
          if str(x).strip() != ""
          and str(x).lower() != "nan"
          and not str(x).replace(".", "", 1).isdigit()
      ]
  )

# --- PORTAL GURU ---
if role == "Portal Guru (Lihat Jadwal)":
  st.title("👨‍🏫 Portal Guru - Jadwal & Riwayat Kehadiran")
  st.write(
      "Silakan pilih nama Anda untuk melihat jadwal mengajar dan rekap"
      " kehadiran."
  )

  if daftar_guru:
    guru_pilihan = st.selectbox("Pilih Nama Guru:", daftar_guru)

    if guru_pilihan:
      st.markdown(f"### 📋 Jadwal Mengajar: **{guru_pilihan}**")
      jadwal_guru = df_jadwal[
          df_jadwal[col_guru].astype(str).str.strip() == guru_pilihan
      ]
      st.dataframe(jadwal_guru, use_container_width=True)

      st.markdown("---")
      st.markdown("### 📊 Riwayat Kehadiran & Honorarium Anda")
      df_absen = load_absensi()
      riwayat_guru = df_absen[df_absen["Nama Guru"] == guru_pilihan]
      if not riwayat_guru.empty:
        st.dataframe(riwayat_guru, use_container_width=True)
        total_didapat = riwayat_guru["Total Honor"].sum()
        st.success(f"**Total Akumulasi Honorarium: Rp {total_didapat:,.0f}**")
      else:
        st.info("Belum ada data kehadiran yang tercatat untuk nama Anda.")
  else:
    st.error("Daftar nama guru tidak ditemukan.")

# --- PORTAL ADMIN / KURIKULUM ---
elif role == "Login Admin / Kurikulum":
  st.title("🔐 Portal Admin & Kurikulum")
  password = st.text_input("Masukkan Password Admin:", type="password")

  if password == "admin123":
    st.success("Login Berhasil! Selamat datang di Panel Kurikulum.")

    menu_admin = st.selectbox(
        "Pilih Menu Admin:",
        [
            "1. Lihat Master Jadwal",
            "2. Input Kehadiran & Status Harian",
            "3. Kalkulasi & Rekap Honorarium Guru",
        ],
    )

    if menu_admin == "1. Lihat Master Jadwal":
      st.subheader("📁 Data Master Jadwal Keseluruhan")
      st.dataframe(df_jadwal, use_container_width=True)

    elif menu_admin == "2. Input Kehadiran & Status Harian":
      st.subheader("📝 Input Kehadiran Guru Harian")

      with st.form("form_absensi", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
          tanggal_absen = st.date_input(
              "Pilih Tanggal Absensi:", datetime.today()
          )
          nama_guru_absen = st.selectbox("Pilih Nama Guru:", daftar_guru)
        with col2:
          status_absen = st.selectbox(
              "Status Kehadiran:",
              [
                  "Hadir Mengajar",
                  "Dinas Luar / Tugas OSIS",
                  "Izin / Sakit",
                  "Tanpa Keterangan",
              ],
          )
          jumlah_jtm = st.number_input(
              "Jumlah Jam Tatap Muka (JTM) Hari Ini:",
              min_value=0,
              max_value=12,
              value=2,
          )

        submit_btn = st.form_submit_button("💾 Simpan Data Kehadiran")

        if submit_btn:
          if status_absen in ["Hadir Mengajar", "Dinas Luar / Tugas OSIS"]:
            honor_hari = TARIF_HARIAN + (jumlah_jtm * TARIF_JTM)
          else:
            honor_hari = 0

          df_absen = load_absensi()
          data_baru = pd.DataFrame([{
              "Tanggal": tanggal_absen.strftime("%Y-%m-%d"),
              "Nama Guru": nama_guru_absen,
              "Status": status_absen,
              "Jumlah JTM": jumlah_jtm if honor_hari > 0 else 0,
              "Total Honor": honor_hari,
          }])

          df_absen = pd.concat([df_absen, data_baru], ignore_index=True)
          save_absensi(df_absen)
          st.success(
              f"Berhasil mencatat kehadiran **{nama_guru_absen}**! Honor"
              f" tercatat: **Rp {honor_hari:,.0f}**"
          )

      st.markdown("---")
      st.subheader("🗑️ Kelola / Hapus Data Absensi")
      df_absen_current = load_absensi()

      if not df_absen_current.empty:
        # Tampilkan tabel lengkap dengan nomor indeksnya
        df_display = df_absen_current.copy()
        df_display.index.name = "ID Data"
        df_display = df_display.reset_index()

        st.dataframe(df_display, use_container_width=True)

        # Pilihan nomor ID data yang ingin dihapus
        id_to_delete = st.number_input(
            "Masukkan Nomor ID Data yang ingin dihapus:",
            min_value=0,
            max_value=len(df_absen_current) - 1,
            step=1,
        )

        if st.button("❌ Hapus Data Terpilih"):
          df_absen_current = df_absen_current.drop(id_to_delete).reset_index(
              drop=True
          )
          save_absensi(df_absen_current)
          st.success(f"Data dengan ID {id_to_delete} berhasil dihapus!")
          st.rerun()
      else:
        st.info("Belum ada data absensi yang tersimpan.")

    elif menu_admin == "3. Kalkulasi & Rekap Honorarium Guru":
      st.subheader("💰 Rekapitulasi & Perhitungan Honor Guru")
      df_absen = load_absensi()

      if df_absen.empty:
        st.info(
            "Belum ada data absensi. Silakan input kehadiran guru di Menu 2"
            " terlebih dahulu."
        )
      else:
        rekap = (
            df_absen.groupby("Nama Guru")
            .agg(
                Total_Hadir=(
                    "Status",
                    lambda x: (
                        x.isin(["Hadir Mengajar", "Dinas Luar / Tugas OSIS"])
                    ).sum(),
                ),
                Total_JTM=("Jumlah JTM", "sum"),
                Total_Honor=("Total Honor", "sum"),
            )
            .reset_index()
        )

        rekap_tampil = rekap.copy()
        rekap_tampil["Total_Honor"] = rekap_tampil["Total_Honor"].apply(
            lambda x: f"Rp {x:,.0f}"
        )
        rekap_tampil.columns = [
            "Nama Guru",
            "Total Hari Hadir/Tugas",
            "Total JTM",
            "Total Honorarium",
        ]

        total_anggaran = rekap["Total_Honor"].sum()
        st.metric(
            label="Total Keseluruhan Anggaran Honorarium",
            value=f"Rp {total_anggaran:,.0f}",
        )

        st.dataframe(rekap_tampil, use_container_width=True)

        st.download_button(
            label="📥 Download Laporan Rekapitulasi (Excel)",
            data=open(FILE_ABSEN, "rb").read(),
            file_name=f"Rekap_Honor_MTs_MUB_{datetime.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

  elif password != "":
    st.error("Password salah! Silakan coba lagi (Default: admin123).")