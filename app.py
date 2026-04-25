import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 1. SAYFA VE TEMA AYARLARI
st.set_page_config(
    page_title="Aile Finans Asistanı", 
    page_icon="💎", 
    layout="wide", 
    initial_sidebar_state="expanded" # Menünün açık gelmesi için zorla
)

# GÜNCELLENEN TEMİZLİK KODU: Header'ı tamamen gizlemiyoruz, sadece butonları temizliyoruz.
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            /* Manage App ve diğer kalabalıkları gizle ama menü tuşunu bırak */
            [data-testid="stStatusWidget"] {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. VERİTABANI HAFIZASI
if 'harcamalar' not in st.session_state:
    st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'AY_YIL', 'KİŞİ', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
if 'istekler' not in st.session_state:
    st.session_state.istekler = pd.DataFrame(columns=['ID', 'KİMDEN', 'KİME', 'İSTEK', 'DURUM'])
    st.session_state.istek_id_sayaci = 0

kategoriler = ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "DÜĞÜN & ÇEYİZ", "TEKNOLOJİ", "EĞİTİM", "SU & FATURA", "SAĞLIK", "DİĞER"]

# --- FONKSİYONLAR ---
@st.dialog("✅ Görevi Tamamla")
def gorev_tamamla_penceresi(istek_id, istek_metni, aktif_kullanici):
    st.write(f"**Görev:** {istek_metni}")
    secilen_kat = st.selectbox("Hangi kategori?", kategoriler)
    girilen_tutar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
    if st.button("Kaydet ve Kapat"):
        st.session_state.istekler.loc[st.session_state.istekler['ID'] == istek_id, 'DURUM'] = 'Tamamlandı ✅'
        bugun = datetime.datetime.now()
        yeni_h = pd.DataFrame([{
            'TARİH': bugun.strftime("%d.%m.%Y"), 
            'AY_YIL': bugun.strftime("%m-%Y"),
            'KİŞİ': aktif_kullanici, 
            'KATEGORİ': secilen_kat, 
            'AÇIKLAMA': f"Görev: {istek_metni}", 
            'TUTAR': float(girilen_tutar)
        }])
        st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, yeni_h], ignore_index=True)
        st.rerun()

def kategori_goster(kat_anahtar, emoji, df_input):
    d_kat = df_input[df_input['KATEGORİ'] == kat_anahtar]
    if not d_kat.empty:
        st.metric(f"{emoji} {kat_anahtar} Dönem Toplamı", f"{d_kat['TUTAR'].sum():,.2f} TL")
        st.dataframe(d_kat, use_container_width=True)
    else: st.info(f"Bu ay {kat_anahtar} kategorisinde harcama yok.")

# 3. SOL SÜTUN (KONTROL MERKEZİ)
with st.sidebar:
    st.title("⚙️ Kontrol Paneli")
    kullanici = st.radio("👤 Kim Kullanıyor?", ["Doğukan", "Eşim"])
    
    st.divider()
    aylik_limit = st.number_input("🎯
