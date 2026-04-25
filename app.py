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
            /* Sol menü genişliğini biraz artıralım */
            [data-testid="stSidebar"] { min-width: 300px; max-width: 300px; }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. HAFIZA OLUŞTURMA
if 'harcamalar' not in st.session_state:
    st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KİŞİ', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
if 'istekler' not in st.session_state:
    st.session_state.istekler = pd.DataFrame(columns=['ID', 'KİMDEN', 'KİME', 'İSTEK', 'DURUM'])
    st.session_state.istek_id_sayaci = 0

# Kategori Listesi (Genişletildi)
kategoriler = ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "DÜĞÜN & ÇEYİZ", "TEKNOLOJİ", "EĞİTİM", "SU & FATURA", "SAĞLIK", "DİĞER"]

# --- AÇILIR PENCERE (POPUP) ---
@st.dialog("Görevi Karşıla ve Harcamayı Gir")
def gorev_tamamla_penceresi(istek_id, istek_metni, aktif_kullanici):
    st.info(f"**Görev:** {istek_metni}")
    secilen_kat = st.selectbox("Kategori", kategoriler)
    girilen_tutar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
    if st.button("Kaydet"):
        st.session_state.istekler.loc[st.session_state.istekler['ID'] == istek_id, 'DURUM'] = 'Tamamlandı ✅'
        bugun = datetime.datetime.now().strftime("%d.%m.%Y")
        
        # SATIRLAR BÖLÜNDÜ (Tablet kopyalaması için güvenli)
        yeni_h = pd.DataFrame([{
            'TARİH': bugun, 
            'KİŞİ': aktif_kullanici, 
            'KATEGORİ': secilen_kat, 
            'AÇIKLAMA': f"Görev: {istek_metni}", 
            'TUTAR': float(girilen_tutar)
        }])
        
        st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, yeni_h], ignore_index=True)
        st.rerun()

# 3. SOL SÜTUN (SIDEBAR) - HER ŞEY BURADA
with st.sidebar:
    st.title("🏡 Aile Paneli")
    kullanici = st.radio("👤 Kim Kullanıyor?", ["Doğukan", "Eşim"])
    st.divider()

    # FORM 1: Yeni Harcama (Gömülü/Açılır)
    with st.expander("➕ Yeni Harcama Ekle"):
        with st.form("h_form", clear_on_submit=True):
            kat = st.selectbox("Kategori", kategoriler)
            tarih = st.date_input("Tarih")
            aciklama = st.text_input("Açıklama")
            tutar = st.number_input("Tutar", min_value=0.0)
            if st.form_submit_button("Kaydet"):
                if aciklama:
                    # SATIRLAR BÖLÜNDÜ (Tablet kopyalaması için güvenli)
                    y_v = pd.DataFrame([{
                        'TARİH': tarih.strftime("%d.%m.%Y"), 
                        'KİŞİ': kullanici, 
                        'KATEGORİ': kat, 
                        'AÇIKLAMA': aciklama.upper(), 
                        'TUTAR': float(tutar)
                    }])
                    st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, y_v], ignore_index=True)
                    st.rerun()

    # FORM 2: İstek Gönder (Gömülü/Açılır)
    with st.expander("📌 Görev/İstek Gönder"):
        with st.form("i_form", clear_on_submit=True):
            hedef = "Eşim" if kullanici == "Doğukan" else "Doğukan"
            metin = st.text_input(f"{hedef} için istek:")
            if st.form_submit_button("Gönder"):
                if metin:
                    st.session_state.istek_id_sayaci += 1
                    # SATIRLAR BÖLÜNDÜ (Tablet kopyalaması için güvenli)
                    y_i = pd.DataFrame([{
                        'ID': st.session_state.istek_id_sayaci, 
                        'KİMDEN': kullanici, 
                        'KİME': hedef, 
                        'İSTEK': metin, 
                        'DURUM': 'Bekliyor ⏳'
                    }])
                    st.session_state.istekler = pd.concat([st.session_state.istekler, y_i], ignore_index=True)
                    st.rerun()

    st.divider()
    
    # NAVİGASYON MENÜSÜ
    st.subheader("📁 Menü")
    sayfa = st.radio("Gitmek istediğiniz alan:", [
        "💬 Görevler Paneli",
        "📈 Genel Grafikler",
        "📊 Tüm Harcama Listesi",
        "👰 Düğün & Çeyiz",
        "🛒 Market",
        "⛽ Akaryakıt",
        "🍔 Yemek & Kafe",
        "📱 Teknoloji",
        "🎓 Eğitim",
        "💧 Su & Fatura"
    ])

# 4. ANA EKRAN (Sağ Taraf)
st.title(f"💳 {sayfa}")

# Bildirimler
bekleyen = st.session_state.istekler[(st.session_state.istekler['KİME'] == kullanici) & (st.session_state.istekler['DURUM'] == 'Bekliyor ⏳')]
if not bekleyen.empty:
    st.warning(f"🔔 Sana {len(bekleyen)} yeni görev var!")
    for idx, row in bekleyen.iterrows():
        c1, c2 = st.columns([5, 1])
        c1.info(f"**{row['KİMDEN']}**: {row['İSTEK']}")
        if c2.button("✅ Karşıla", key=f"b_{row['ID']}"):
            gorev_tamamla_penceresi(row['ID'], row['İSTEK'], kullanici)

st.divider()

def kategori_goster(kat_anahtar, emoji):
    d_kat = df[df['KATEGORİ'] == kat_anahtar]
    if not d_kat.empty:
        st.metric(f"{emoji} {kat_anahtar} Toplam", f"{d_kat['TUTAR'].sum():,.2f} TL")
        st.dataframe(d_kat, use_container_width=True)
    else: st.info(f"{kat_anahtar} kategorisinde henüz harcama yok.")

# SAYFA İÇERİKLERİ
df = st.session_state.harcamalar

if sayfa == "💬 Görevler Paneli":
    if not st.session_state.istekler.empty:
        st.dataframe(st.session_state.istekler.drop(columns=['ID']), use_container_width=True)
    else: st.info("Henüz bir görev kaydı yok.")

elif sayfa == "📈 Genel Grafikler":
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Sektörel Dağılım")
            fig1, ax1 = plt.subplots()
            df.groupby('KATEGORİ')['TUTAR'].sum().plot(kind='pie', autopct='%1.1f%%', ax=ax1, cmap='Pastel1')
            ax1.set_ylabel(''); st.pyplot(fig1)
        with col2:
            st.subheader("Kişisel Harcama Toplamı")
            fig2, ax2 = plt.subplots()
            df.groupby('KİŞİ')['TUTAR'].sum().plot(kind='bar', ax=ax2, color=['skyblue', 'salmon'])
            st.pyplot(fig2)
    else: st.warning("Grafik için veri girilmeli.")

elif sayfa == "📊 Tüm Harcama Listesi":
    st.metric("Toplam Harcama", f"{df['TUTAR'].sum():,.2f} TL")
    st.dataframe(df, use_container_width=True)

elif sayfa == "👰 Düğün & Çeyiz": kategori_goster("DÜĞÜN & ÇEYİZ", "👰")
elif sayfa == "🛒 Market": kategori_goster("MARKET", "🛒")
elif sayfa == "⛽ Akaryakıt": kategori_goster("AKARYAKIT & ULAŞIM", "⛽")
elif sayfa == "🍔 Yemek & Kafe": kategori_goster("YEMEK & KAFE", "🍔")
elif sayfa == "📱 Teknoloji": kategori_goster("TEKNOLOJİ", "📱")
elif sayfa == "🎓 Eğitim": kategori_goster("EĞİTİM", "🎓")
elif sayfa == "💧 Su & Fatura": kategori_goster("SU & FATURA", "💧")
