import streamlit as st
import pandas as pd
import pdfplumber
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="İnteraktif Bütçe", page_icon="💳", layout="wide")

# 1. HAFIZA OLUŞTURMA (Girdiğimiz verilerin kaybolmaması için)
if 'harcamalar' not in st.session_state:
    st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])

# 2. SOL MENÜ - GİRDİ ALANI (İnteraktif Kısım)
st.sidebar.header("➕ Yeni Harcama Ekle")
with st.sidebar.form("veri_giris_formu"):
    tarih = st.date_input("İşlem Tarihi")
    kategori = st.selectbox("Kategori Seçin", ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "TEKNOLOJİ", "DİĞER"])
    aciklama = st.text_input("Açıklama / Yer", placeholder="Örn: Clio için benzin, Migros alışverişi...")
    tutar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
    ekle_btn = st.form_submit_button("Listeye Ekle")

    if ekle_btn and aciklama:
        yeni_veri = pd.DataFrame([{
            'TARİH': tarih.strftime("%d.%m.%Y"), 
            'KATEGORİ': kategori, 
            'AÇIKLAMA': aciklama.upper(), 
            'TUTAR': float(tutar)
        }])
        st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, yeni_veri], ignore_index=True)
        st.sidebar.success("Harcama başarıyla eklendi!")

# İstersen PDF'i de toptan ekleyebilmen için ufak bir buton
st.sidebar.divider()
st.sidebar.subheader("Veya PDF'ten Toptan Yükle")
uploaded_file = st.sidebar.file_uploader("Vakıfbank Ekstresi", type=["pdf"])

if uploaded_file is not None:
    # Eski PDF okuma motorumuz arka planda sessizce çalışır
    sablon = re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+((?:\+)?[\d,]+\.\d{2})')
    gecici_veriler = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    match = sablon.search(line)
                    if match:
                        t, a, tut_str = match.groups()
                        if '+' in tut_str or 'ÖNCEKİ' in a.upper() or 'SON ÖDE' in a.upper(): continue
                        tut = float(tut_str.replace(',', ''))
                        if tut > 0: gecici_veriler.append([t, "DİĞER", a, tut])
    
    if gecici_veriler:
        pdf_df = pd.DataFrame(gecici_veriler, columns=['TARİH', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
        
        kat_sozluk = {
            'MARKET': ['BIM', 'A101', 'FILE', 'MIGROS', 'METRO', 'SOK', 'MARKET'],
            'YEMEK & KAFE': ['FAST FOOD', 'KANTİN', 'TRENDYOL YEMEK', 'CAFE', 'FIRIN', 'LOKANTA'],
            'AKARYAKIT & ULAŞIM': ['TOTAL', 'PEGASUS', 'AJET', 'PETROL', 'OPET', 'SHELL', 'ESHOT'],
        }
        def k_bul(desc):
            for k, kelimeler in kat_sozluk.items():
                if any(kelime in str(desc).upper() for kelime in kelimeler): return k
            return 'DİĞER'
        
        pdf_df['KATEGORİ'] = pdf_df['AÇIKLAMA'].apply(k_bul)
        st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, pdf_df], ignore_index=True)
        st.sidebar.success("PDF verileri sisteme eklendi!")

# 3. ANA EKRAN - SEKMELER (ÇIKTI ALANI)
st.title("💳 Kategorik Harcama Paneli")

df = st.session_state.harcamalar

# Sekmeleri oluşturuyoruz
sekme_genel, sekme_market, sekme_yemek, sekme_yakit = st.tabs([
    "📊 Genel Özet", 
    "🛒 Market", 
    "🍔 Yemek & Kafe", 
    "⛽ Akaryakıt & Ulaşım"
])

# SEKMELERİN İÇERİĞİ
with sekme_genel:
    st.subheader("Tüm Harcamalar")
    if not df.empty:
        st.metric("Toplam Harcama", f"{df['TUTAR'].sum():,.2f} TL")
        st.dataframe(df, use_container_width=True)
        
        if st.button("Tüm Listeyi Temizle"):
            st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
            st.rerun()
    else:
        st.info("Sol taraftan harcama ekleyin veya PDF yükleyin.")

with sekme_market:
    st.subheader("🛒 Sadece Market Harcamaları")
    df_market = df[df['KATEGORİ'] == 'MARKET']
    if not df_market.empty:
        st.metric("Market Toplamı", f"{df_market['TUTAR'].sum():,.2f} TL")
        st.dataframe(df_market, use_container_width=True)
    else:
        st.warning("Bu kategoride henüz girdi yok.")

with sekme_yemek:
    st.subheader("🍔 Sadece Yemek & Kafe Harcamaları")
    df_yemek = df[df['KATEGORİ'] == 'YEMEK & KAFE']
    if not df_yemek.empty:
        st.metric("Yemek Toplamı", f"{df_yemek['TUTAR'].sum():,.2f} TL")
        st.dataframe(df_yemek, use_container_width=True)
    else:
        st.warning("Bu kategoride henüz girdi yok.")

with sekme_yakit:
    st.subheader("⛽ Sadece Akaryakıt & Ulaşım Harcamaları")
    df_yakit = df[df['KATEGORİ'] == 'AKARYAKIT & ULAŞIM']
    if not df_yakit.empty:
        st.metric("Akaryakıt Toplamı", f"{df_yakit['TUTAR'].sum():,.2f} TL")
        st.dataframe(df_yakit, use_container_width=True)
    else:
        st.warning("Bu kategoride henüz girdi yok.")

