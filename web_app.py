import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
import config
from telegram_client import ShpBotAdapter
from storage import OutputWriter

# ==========================================
# KONFIGURASI HALAMAN & CSS KUSTOM (DASHBOARD)
# ==========================================
st.set_page_config(
    page_title="Mission Checker Dashboard",
    page_icon="🛍️",
    layout="wide"
)

# CSS untuk meniru desain gambar Anda
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Nunito', sans-serif;
    }
    
    /* Latar belakang abu-abu terang */
    .stApp {
        background-color: #F4F5F7;
    }
    
    /* Styling untuk kotak statistik atas */
    .stat-card {
        background-color: #A8A0FA; /* Warna ungu pastel */
        border: 3px solid #000000;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 4px 4px 0px #000000; /* Efek bayangan keras */
        margin-bottom: 20px;
    }
    .stat-card h4 { margin: 0; color: #000; font-size: 14px; font-weight: 700; }
    .stat-card h2 { margin: 0; color: #000; font-size: 28px; font-weight: 900; }
    
    /* Styling untuk kotak putih (panel) */
    .panel-box {
        background-color: #FFFFFF;
        border: 2px solid #E0E0E0;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Tombol kuning */
    .stButton>button {
        background-color: #FFE44D;
        color: #000000;
        border: 3px solid #000000;
        border-radius: 12px;
        font-weight: 900;
        padding: 10px;
        box-shadow: 3px 3px 0px #000000;
        transition: all 0.1s ease;
    }
    .stButton>button:active {
        transform: translate(3px, 3px);
        box-shadow: 0px 0px 0px #000000;
    }
    
    /* Kotak Terminal Hitam */
    .terminal-box {
        background-color: #000000;
        color: #00FF00; /* Teks hijau terminal */
        font-family: 'Courier New', Courier, monospace;
        padding: 15px;
        border-radius: 12px;
        height: 250px;
        overflow-y: auto;
        border: 3px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER: STATISTIK (4 Kotak Ungu)
# ==========================================
st.markdown("### 📊 Dashboard Pemantauan")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown('<div class="stat-card"><h4>⏳ Antrian Aktif</h4><h2>0 Akun</h2></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="stat-card"><h4>🎟️ Voucher Food</h4><h2>0 Akun</h2></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="stat-card"><h4>🎯 Misi 10K</h4><h2>0 Akun</h2></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="stat-card"><h4>🎁 Auto Deals</h4><h2>0 Akun</h2></div>', unsafe_allow_html=True)

st.write("---")

# ==========================================
# LAYOUT UTAMA (KIRI & KANAN)
# ==========================================
col_left, col_right = st.columns([1, 1])

with col_left:
    # Panel Sumber Akun
    st.markdown("#### 📂 SUMBER AKUN")
    with st.container():
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        targets_text = st.text_area("List Akun (Manual .txt):", height=150, placeholder="ky4zwc5ek2\numtl1zxn99")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.button("💾 Simpan", use_container_width=True)
        with col_btn2:
            st.button("🗑️ Kosongkan", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Panel Mode Bot
    st.markdown("#### ⚙️ PILIH MODE BOT")
    with st.container():
        st.markdown('<div class="panel-box">', unsafe_allow_html=True)
        mode = st.radio(
            "Pilih Mode:",
            ["Cek Voucher Shopee Food", "Cek Misi 10K", "Auto Buy Deals", "Top Up ShopeePay"],
            label_visibility="collapsed"
        )
        
        # Tombol Mulai
        if st.button("🚀 MULAI EKSEKUSI BOT", use_container_width=True):
            targets = [t.strip() for t in targets_text.split("\n") if t.strip()]
            if not targets:
                st.error("Isi daftar akun dulu ya!")
            else:
                st.session_state['run_trigger'] = True
                st.session_state['targets_to_run'] = targets
        st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # Panel Antrian Proses
    st.markdown("#### 📋 ANTRIAN PROSES")
    st.markdown('<div class="terminal-box" id="antrian-box">[] Antrian kosong...</div>', unsafe_allow_html=True)
    
    # Panel Real-Time Terminal
    st.markdown("#### 🖥️ REAL-TIME TERMINAL")
    terminal_placeholder = st.empty()
    terminal_placeholder.markdown('<div class="terminal-box">[!] Menunggu perintah...</div>', unsafe_allow_html=True)


# ==========================================
# LOGIKA EKSEKUSI (DIJALANKAN SAAT TOMBOL DITEKAN)
# ==========================================
if st.session_state.get('run_trigger', False):
    targets = st.session_state['targets_to_run']
    st.session_state['run_trigger'] = False # Reset trigger
    
    # Siapkan teks log untuk terminal
    log_text = "[*] Memulai Bot...\n"
    terminal_placeholder.markdown(f'<div class="terminal-box">{log_text}</div>', unsafe_allow_html=True)
    
    async def run_bulk():
        global log_text
        adapter = ShpBotAdapter(str(config.SESSIONS_DIR / "shp_checker"))
        writer = OutputWriter(config.OUTPUT_DIR)
        
        log_text += "[*] Menghubungkan ke Telegram...\n"
        terminal_placeholder.markdown(f'<div class="terminal-box">{log_text}</div>', unsafe_allow_html=True)
        
        await adapter.connect()
        
        for i, target in enumerate(targets, 1):
            log_text += f"[{i}/{len(targets)}] Memproses: {target}...\n"
            terminal_placeholder.markdown(f'<div class="terminal-box">{log_text}</div>', unsafe_allow_html=True)
            
            res = await adapter.check_target(target)
            await writer.write_result(res)
            
            if res.category == "coin":
                log_text += f"   [+] BERHASIL! Misi ditemukan.\n"
            else:
                log_text += f"   [-] Gagal / Format salah.\n"
                
            terminal_placeholder.markdown(f'<div class="terminal-box">{log_text}</div>', unsafe_allow_html=True)
        
        await adapter.disconnect()
        log_text += "\n[!] SEMUA PROSES SELESAI.\n"
        terminal_placeholder.markdown(f'<div class="terminal-box">{log_text}</div>', unsafe_allow_html=True)

    # Jalankan Proses
    asyncio.run(run_bulk())
    st.success("✅ Eksekusi Selesai! Silakan cek file coin.txt.")