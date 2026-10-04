import streamlit as st
import pandas as pd
import os
import re

FILE_DATABASE_LOKAL = "input_manual_unwinder.csv"

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Pencocokan Sparepart Unwinder",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS RESPONSISTIF UNTUK LAYAR KECIL ---
st.markdown("""
    <style>
        /* Mengurangi padding atas & samping agar area kerja lebih luas */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            max-width: 100% !important;
        }
        /* Menyesuaikan ukuran font & padding input form di layar kecil */
        .stTextInput > div > div > input, .stSelectbox > div > div {
            font-size: 14px !important;
        }
        /* Mengatur agar tabel bisa di-scroll secara horizontal jika terlalu lebar */
        .stDataFrame {
            width: 100% !important;
            overflow-x: auto !important;
        }
        /* Menyesuaikan jarak tombol */
        .stButton button {
            width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI HELPER & CLEANSING DATA ---
def bersihkan_teks(teks):
    if pd.isna(teks):
        return ""
    s = str(teks).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return re.sub(r'\s+', ' ', s).upper()

def ekstrak_karakter_saja(teks):
    return re.sub(r'[^A-Z0-9]', '', bersihkan_teks(teks))

def muat_data_lokal():
    kolom_wajib = ["kode", "nama", "kategori"]
    if os.path.exists(FILE_DATABASE_LOKAL):
        try:
            df = pd.read_csv(FILE_DATABASE_LOKAL, dtype=str)
            for col in kolom_wajib:
                if col not in df.columns:
                    df[col] = "-"
            df['kode'] = df['kode'].apply(bersihkan_teks)
            df['nama'] = df['nama'].apply(bersihkan_teks)
            return df[kolom_wajib]
        except Exception:
            return pd.DataFrame(columns=kolom_wajib)
    else:
        return pd.DataFrame(columns=kolom_wajib)

def simpan_data_lokal(df):
    df.to_csv(FILE_DATABASE_LOKAL, index=False)

def beri_warna_status(val):
    if "ADA" in str(val) or "MATCH" in str(val):
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    elif "TIDAK ADA" in str(val):
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
    return ""

df_lokal = muat_data_lokal()

# --- HEADER APLIKASI ---
st.title("⚙️ Verifikasi & Pendataan Sparepart Unwinder")
st.caption("Aplikasi untuk pendataan harian sparepart Unwinder dan pencocokan ke Master Database Excel")
st.markdown("---")

# --- SIDEBAR: UPLOAD MASTER EXCEL ---
st.sidebar.header("📁 Master Database Excel")

file_excel_master = st.sidebar.file_uploader(
    "Upload File Database Master (.xlsx / .xls / .xlsm):", 
    type=["xlsx", "xls", "xlsm"], 
    key="master_excel"
)

master_lookup = {}
df_master_raw = None

if file_excel_master is not None:
    try:
        df_master_raw = pd.read_excel(file_excel_master, dtype=str)
        st.sidebar.success(f"✅ Excel Master Dimuat! Total: **{len(df_master_raw)}** baris data.")
        
        kolom_list = df_master_raw.columns.tolist()
        col_nama = st.sidebar.selectbox("Pilih Kolom Deskripsi / Nama Part Master:", kolom_list, index=min(1, len(kolom_list)-1))
        
        for _, row in df_master_raw.iterrows():
            nama_part = bersihkan_teks(row[col_nama])
            if not nama_part:
                continue
                
            for col_val in row.values:
                val_clean = bersihkan_teks(col_val)
                val_strict = ekstrak_karakter_saja(col_val)
                
                if val_clean and len(val_clean) >= 3:
                    master_lookup[val_clean] = nama_part
                if val_strict and len(val_strict) >= 3:
                    master_lookup[val_strict] = nama_part
                    
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file Excel: {e}")
else:
    st.sidebar.info("💡 Unggah file Master Excel di atas untuk mulai memverifikasi data inputan.")

# --- SIDEBAR MENU NAVIGATION ---
st.sidebar.markdown("---")
st.sidebar.header("📌 Navigasi")
menu = st.sidebar.radio(
    "Pilih Fitur:",
    [
        "1. Input & Cocokkan Data Unwinder",
        "2. Lihat & Edit Data Tersimpan",
        "3. Download Laporan Hasil Verifikasi"
    ]
)

def cermati_pencocokan(kode_input, nama_input):
    if not master_lookup:
        return "MASTER BELUM DIUPLOAD", "-"
    
    k_clean = bersihkan_teks(kode_input)
    k_strict = ekstrak_karakter_saja(kode_input)
    n_clean = bersihkan_teks(nama_input)
    
    if k_clean and k_clean in master_lookup:
        return "ADA (MATCH KODE)", master_lookup[k_clean]
    if k_strict and k_strict in master_lookup:
        return "ADA (MATCH KODE)", master_lookup[k_strict]
        
    if n_clean and n_clean in master_lookup:
        return "ADA (MATCH NAMA)", master_lookup[n_clean]
        
    return "TIDAK ADA", "-"

# --- MENU 1: INPUT & COCOKKAN DATA ---
if menu == "1. Input & Cocokkan Data Unwinder":
    st.subheader("➕ Input Manual Sparepart Unwinder Harian")
    
    with st.form("form_input", clear_on_submit=True):
        # Menggunakan rasio kolom yang lebih adaptif untuk layar laptop kecil
        col1, col2 = st.columns([1, 1])
        with col1:
            kode_raw = st.text_input("Kode / Material Code Sparepart *", placeholder="Contoh: 4008671 / 7004428200030")
            nama_raw = st.text_input("Nama Sparepart *", placeholder="Contoh: RELAY WEIDMULLER 1122880000 6MM 24VDC+RELAY")
        with col2:
            kategori = st.selectbox(
                "Kategori Sparepart",
                [
                    "Elektrikal & Panel Control (Kontaktor, Relay, MCB, Power Supply)",
                    "Sensor & Detektor",
                    "Aktuator & Motor / Drive",
                    "Pneumatik & Hidrolik",
                    "Mekanikal",
                    "Lain-lain"
                ]
            )
            
        tombol_simpan = st.form_submit_button("💾 Simpan & Verifikasi")
        
        if tombol_simpan:
            kode = bersihkan_teks(kode_raw)
            nama = bersihkan_teks(nama_raw)
            
            if not nama and not kode:
                st.error("⚠️ Kode Part atau Nama Sparepart wajib diisi!")
            else:
                baru = pd.DataFrame([{
                    "kode": kode,
                    "nama": nama,
                    "kategori": kategori
                }])
                df_lokal = pd.concat([df_lokal, baru], ignore_index=True)
                simpan_data_lokal(df_lokal)
                st.success(f"✅ Data berhasil disimpan: **{nama}** (`{kode}`)")
                st.rerun()

    st.markdown("---")
    st.subheader("📊 Hasil Pencocokan Data Unwinder Saat Ini")
    
    if df_lokal.empty:
        st.info("Belum ada data sparepart Unwinder yang diinputkan hari ini.")
    else:
        df_hasil = df_lokal.copy()
        
        status_list = []
        ket_master_list = []
        
        for _, row in df_hasil.iterrows():
            st_res, ket_res = cermati_pencocokan(row['kode'], row['nama'])
            status_list.append(st_res)
            ket_master_list.append(ket_res)
                
        df_hasil['Status di Master Excel'] = status_list
        df_hasil['Nama di Master Excel'] = ket_master_list
        
        if master_lookup:
            match_count = sum(1 for s in status_list if "ADA" in s)
            unmatch_count = status_list.count("TIDAK ADA")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Input Unwinder", len(df_hasil))
            c2.metric("Ada di Master Excel (Match)", match_count)
            c3.metric("Tidak Ada di Master Excel", unmatch_count)
        
        st.dataframe(
            df_hasil.style.map(beri_warna_status, subset=['Status di Master Excel']), 
            use_container_width=True
        )

# --- MENU 2: LIHAT & EDIT DATA TERSIMPAN ---
elif menu == "2. Lihat & Edit Data Tersimpan":
    st.subheader("📋 Kelola Data Inputan Unwinder")
    st.caption("Kamu bisa mengedit langsung teks pada tabel, atau menghapus per item di bagian bawah.")
    
    if df_lokal.empty:
        st.info("Belum ada data yang tersimpan.")
    else:
        df_edited = st.data_editor(
            df_lokal[["kode", "nama", "kategori"]],
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "kode": st.column_config.TextColumn("Kode / Material Code", required=True),
                "nama": st.column_config.TextColumn("Nama Sparepart", required=True),
                "kategori": st.column_config.SelectboxColumn("Kategori", options=[
                    "Elektrikal & Panel Control (Kontaktor, Relay, MCB, Power Supply)",
                    "Sensor & Detektor", 
                    "Aktuator & Motor / Drive", 
                    "Pneumatik & Hidrolik", 
                    "Mekanikal", 
                    "Lain-lain"
                ])
            }
        )
        
        if st.button("💾 Simpan Perubahan Edit Tabel", type="primary"):
            df_edited['kode'] = df_edited['kode'].apply(bersihkan_teks)
            df_edited['nama'] = df_edited['nama'].apply(bersihkan_teks)
            simpan_data_lokal(df_edited)
            st.success("✅ Perubahan tabel berhasil disimpan!")
            st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Opsi Penghapusan Data")
        
        col_hapus1, col_hapus2 = st.columns([2, 1])
        
        with col_hapus1:
            df_lokal['label_pilihan'] = df_lokal['kode'] + " - " + df_lokal['nama']
            part_dihapus = st.selectbox("Pilih Item Sparepart yang Ingin Dihapus:", df_lokal['label_pilihan'])
            
        with col_hapus2:
            st.write(" ")
            st.write(" ")
            if st.button("🗑️ Hapus Item Ini"):
                kode_target = part_dihapus.split(" - ")[0]
                df_lokal = df_lokal[df_lokal['kode'] != kode_target].drop(columns=['label_pilihan'], errors='ignore')
                simpan_data_lokal(df_lokal)
                st.success(f"✅ Item `{kode_target}` berhasil dihapus!")
                st.rerun()

        with st.expander("⚠️ Area Bahaya: Reset Hapus Semua Data"):
            st.warning("Tindakan ini akan menghapus SELURUH data inputan yang tersimpan!")
            if st.button("🚨 Hapus Semua Data Inputan", type="primary"):
                df_kosong = pd.DataFrame(columns=["kode", "nama", "kategori"])
                simpan_data_lokal(df_kosong)
                st.success("✅ Seluruh data berhasil dibersihkan.")
                st.rerun()

# --- MENU 3: DOWNLOAD LAPORAN HASIL VERIFIKASI ---
elif menu == "3. Download Laporan Hasil Verifikasi":
    st.subheader("📥 Export Laporan Hasil Pencocokan Unwinder")
    
    if df_lokal.empty:
        st.warning("⚠️ Data inputan masih kosong.")
    else:
        df_export = df_lokal.copy()
        
        status_list = []
        ket_master_list = []
        
        for _, row in df_export.iterrows():
            st_res, ket_res = cermati_pencocokan(row['kode'], row['nama'])
            status_list.append(st_res)
            ket_master_list.append(ket_res)
                
        df_export['Status di Master Excel'] = status_list
        df_export['Nama di Master Excel'] = ket_master_list
        
        st.dataframe(
            df_export.style.map(beri_warna_status, subset=['Status di Master Excel']), 
            use_container_width=True
        )
        
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan LENGKAP (.csv)",
            data=csv_data,
            file_name="Laporan_Verifikasi_Unwinder.csv",
            mime="text/csv"
        )
