import streamlit as st
import pandas as pd
import os

FILE_DATABASE_LOKAL = "input_manual_unwinder.csv"

# Konfigurasi Tampilan Halaman Web
st.set_page_config(
    page_title="Sparepart Unwinder Inspector",
    page_icon="⚙️",
    layout="wide"
)

# --- FUNGSI DATABASE ---
def muat_data_lokal():
    if os.path.exists(FILE_DATABASE_LOKAL):
        df = pd.read_csv(FILE_DATABASE_LOKAL)
        # Memastikan kolom selalu bertipe string
        df['kode'] = df['kode'].astype(str)
        return df
    else:
        return pd.DataFrame(columns=["kode", "nama", "kategori"])

def simpan_data_lokal(df):
    df.to_csv(FILE_DATABASE_LOKAL, index=False)

# Memuat data
df_lokal = muat_data_lokal()

# --- HEADER APLIKASI ---
st.title("⚙️ Sistem Inspeksi Sparepart Unwinder")
st.caption("Aplikasi manajemen dan verifikasi sparepart mesin Unwinder M.Torres THT90-TTW")
st.markdown("---")

# --- SIDEBAR MENU ---
st.sidebar.header("📌 Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih Fitur:",
    ["1. Input Part Manual", "2. Lihat & Kelola Data Inputan", "3. Cek / Bandingkan CSV Master"]
)

# --- MENU 1: INPUT PART MANUAL ---
if menu == "1. Input Part Manual":
    st.subheader("➕ Tambah Sparepart Manual")
    
    with st.form("form_input", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Sparepart", placeholder="Contoh: Sensor Ultrasonik")
        with col2:
            kode = st.text_input("Kode / Part Number", placeholder="Contoh: UC2000-30GM").strip().upper()
            
        kategori = st.selectbox(
            "Pilih Kategori Sparepart",
            [
                "Sensor & Detektor (Ultrasonic, Encoder, Laser, Photoelectric)",
                "Aktuator & Motor (Servo, Drive, Inverter, Brakes)",
                "Pneumatik & Hidrolik (Solenoid Valve, Bellows, Cylinders)",
                "Mekanikal (Chucks, Rollers, Bearings, Belts)",
                "Lain-lain"
            ]
        )
        
        tombol_simpan = st.form_submit_button("Simpan Sparepart")
        
        if tombol_simpan:
            if not nama or not kode:
                st.error("⚠️ Nama Sparepart dan Kode Part tidak boleh kosong!")
            else:
                baru = pd.DataFrame([{"kode": kode, "nama": nama, "kategori": kategori}])
                df_lokal = pd.concat([df_lokal, baru], ignore_index=True)
                simpan_data_lokal(df_lokal)
                st.success(f"✅ Berhasil menyimpan: **{nama}** (`{kode}`)")
                st.rerun()

# --- MENU 2: LIHAT & KELOLA DATA INPUTAN (FITUR HAPUS) ---
elif menu == "2. Lihat & Kelola Data Inputan":
    st.subheader("📋 Daftar Sparepart Inputan Manual")
    
    if df_lokal.empty:
        st.info("Belum ada data sparepart yang diinputkan.")
    else:
        st.metric("Total Sparepart Tersimpan", len(df_lokal))
        st.dataframe(df_lokal, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🗑️ Hapus Data Sparepart")
        
        # Opsi 1: Hapus berdasarkan item tertentu
        col_hapus1, col_hapus2 = st.columns([3, 1])
        with col_hapus1:
            # Membuat label gabungan Kode + Nama untuk dropdown
            df_lokal['label_pilihan'] = df_lokal['kode'] + " - " + df_lokal['nama']
            part_dihapus = st.selectbox("Pilih Sparepart yang Ingin Dihapus:", df_lokal['label_pilihan'])
            
        with col_hapus2:
            st.write(" ") # Spasi vertikal
            st.write(" ") 
            if st.button("🗑️ Hapus Item Ini", type="primary"):
                # Mengambil kode part dari pilihan
                kode_target = part_dihapus.split(" - ")[0]
                df_lokal = df_lokal[df_lokal['kode'] != kode_target].drop(columns=['label_pilihan'], errors='ignore')
                simpan_data_lokal(df_lokal)
                st.success(f"✅ Sparepart `{kode_target}` berhasil dihapus!")
                st.rerun()

        # Opsi 2: Hapus Semua Data (Reset)
        with st.expander("⚠️ Area Bahaya: Reset Semua Data"):
            st.warning("Tindakan ini akan menghapus SELURUH data inputan manual!")
            if st.button("🚨 Hapus Semua Data Manual"):
                df_kosong = pd.DataFrame(columns=["kode", "nama", "kategori"])
                simpan_data_lokal(df_kosong)
                st.success("✅ Seluruh data manual berhasil dibersihkan.")
                st.rerun()

# --- MENU 3: CEK / BANDINGKAN CSV MASTER ---
elif menu == "3. Cek / Bandingkan CSV Master":
    st.subheader("🔍 Pembandingan dengan CSV Master")
    
    if df_lokal.empty:
        st.warning("⚠️ Masukkan data sparepart secara manual terlebih dahulu di Menu 1!")
    else:
        file_master = st.file_uploader("Upload File CSV Master (contoh: master_parts.csv)", type=["csv"])
        
        if file_master is not None:
            try:
                df_master = pd.read_csv(file_master, header=None)
                df_master[0] = df_master[0].astype(str).str.strip().str.upper()
                master_dict = dict(zip(df_master[0], df_master[1] if len(df_master.columns) > 1 else ["Terdaftar di Master"] * len(df_master)))
                
                status_list = []
                ket_list = []
                
                for k in df_lokal['kode']:
                    if k in master_dict:
                        status_list.append("ADA (MATCH)")
                        ket_list.append(master_dict[k])
                    else:
                        status_list.append("TIDAK ADA")
                        ket_list.append("-")
                
                df_hasil = df_lokal.copy()
                if 'label_pilihan' in df_hasil.columns:
                    df_hasil = df_hasil.drop(columns=['label_pilihan'])
                    
                df_hasil['Status di CSV Master'] = status_list
                df_hasil['Keterangan Master'] = ket_list
                
                col1, col2 = st.columns(2)
                col1.metric("Part Ditemukan (Match)", status_list.count("ADA (MATCH)"))
                col2.metric("Part Tidak Ditemukan", status_list.count("TIDAK ADA"))
                
                st.markdown("### Hasil Analisis:")
                st.dataframe(df_hasil, use_container_width=True)
                
            except Exception as e:
                st.error(f"Gagal membaca file CSV Master: {e}")