import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 1. SAYFA VE TEMİZLİK AYARLARI
st.set_page_config(page_title="Aile Bütçesi", page_icon="🏡", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            [data-testid="stStatusWidget"] {visibility: hidden;}
            #manage-app-button {display: none !important;}
            button[title="View source on GitHub"] {display: none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. HAFIZA OLUŞTURMA
if 'harcamalar' not in st.session_state:
    st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KİŞİ', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
if 'istekler' not in st.session_state:
    st.session_state.istekler = pd.DataFrame(columns=['ID', 'KİMDEN', 'KİME', 'İSTEK', 'DURUM'])
    st.session_state.istek_id_sayaci = 0

kategoriler = ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "DÜĞÜN & ÇEYİZ", "TEKNOLOJİ", "EĞLENCE", "SAĞLIK", "DİĞER"]

# --- AÇILIR PENCERE (POPUP) FONKSİYONU ---
@st.dialog("Görevi Karşıla ve Harcamayı Gir")
def gorev_tamamla_penceresi(istek_id, istek_metni, aktif_kullanici):
    st.info(f"**Yerine Getirilen Görev:** {istek_metni}")
    secilen_kat = st.selectbox("Bu harcama hangi kategoriye giriyor?", kategoriler)
    girilen_tutar = st.number_input("Ne kadar harcadın? (TL)", min_value=0.0, format="%.2f")
    
    if st.button("Kaydet ve Görevi Kapat"):
        st.session_state.istekler.loc[st.session_state.istekler['ID'] == istek_id, 'DURUM'] = 'Tamamlandı ✅'
        bugun = datetime.datetime.now().strftime("%d.%m.%Y")
        yeni_h = pd.DataFrame([{
            'TARİH': bugun, 'KİŞİ': aktif_kullanici, 'KATEGORİ': secilen_kat, 
            'AÇIKLAMA': f"Görev: {istek_metni}", 'TUTAR': float(girilen_tutar)
        }])
        st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, yeni_h], ignore_index=True)
        st.rerun()

# 3. YAN MENÜ (SOL SÜTUN) - Tümü Aile Paneliyle Aynı Hizada!
st.sidebar.title("🏡 Aile Paneli")
kullanici = st.sidebar.radio("👤 Kim Kullanıyor?", ["Doğukan", "Eşim"])
st.sidebar.divider()

st.sidebar.header("➕ Yeni Harcama")
with st.
