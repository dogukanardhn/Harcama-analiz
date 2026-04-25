import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 1. SAYFA VE TEMİZLİK AYARLARI
st.set_page_config(page_title="Aile Bütçesi", page_icon="🏡", layout="wide")

# CSS Kodu: "Manage app", Menü ve Footer'ı gizler (Uygulama tam mobil görünür)
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

# 3. SOL MENÜ - KULLANICI VE GİRDİ
st.sidebar.title("🏡 Aile Paneli")
kullanici = st.sidebar.radio("👤 Kim Kullanıyor?", ["Doğukan", "Eşim"])
st.sidebar.divider()

st.sidebar.header("➕ Yeni Harcama")
with st.sidebar.form("veri_giris_formu", clear_on_submit=True):
    tarih = st.date_input("İşlem Tarihi")
    kategori = st.selectbox("Kategori", kategoriler)
    aciklama = st.text_input("Açıklama", placeholder="Örn: Mutfak robotu, benzin...")
    tutar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
    if st.form_submit_button("Harcamayı Kaydet"):
        if aciklama:
            yeni_v = pd.DataFrame([{'TARİH': tarih.strftime("%d.%m.%Y"), 'KİŞİ': kullanici, 'KATEGORİ': kategori, 'AÇIKLAMA': aciklama.upper(), 'TUTAR': float(tutar)}])
            st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, yeni_v], ignore_index=True)
            st.sidebar.success("Kaydedildi!")

st.sidebar.header("📌 İstek Gönder")
with st.sidebar.form("istek_formu", clear_on_submit=True):
    hedef = "Eşim" if kullanici == "Doğukan" else "Doğukan"
    st.markdown(f"**Alıcı:** {hedef}")
    metin = st.text_input("Ne lazım?", placeholder="Ekmek al, depoyu doldur...")
    if st.form_submit_button("İsteği Gönder"):
        if metin:
            st.session_state.istek_id_sayaci += 1
            yeni_i = pd.DataFrame([{'ID': st.session_state.istek_id_sayaci, 'KİMDEN': kullanici, 'KİME': hedef, 'İSTEK': metin, 'DURUM': 'Bekliyor ⏳'}])
            st.session_state.istekler = pd.concat([st.session_state.istekler, yeni_i], ignore_index=True)
            st.sidebar.success("Gönderildi!")

# 4. ANA EKRAN VE BİLDİRİMLER
st.title("💳 Harcama Takibi")

bekleyen = st.session_state.istekler[(st.session_state.istekler['KİME'] == kullanici) & (st.session_state.istekler['DURUM'] == 'Bekliyor ⏳')]
if not bekleyen.empty:
    st.warning(f"🔔 Sana {len(bekleyen)} yeni görev var!")
    for idx, row in bekleyen.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.info(f"**{row['KİMDEN']}**: {row['İSTEK']}")
        if c2.button("✅ Karşıla", key=f"b_{row['ID']}"):
            gorev_tamamla_penceresi(row['ID'], row['İSTEK'], kullanici)

st.markdown("---")

sekmeler = st.tabs(["💬 Görevler", "📈 Grafikler", "📊 Tüm Liste", "👰 Çeyiz", "🛒 Market", "⛽ Yakıt", "🍔 Yemek"])
s_grv, s_grf, s_lst, s_dug, s_mrk, s_ykt, s_ymk = sekmeler

# Veri tablosu
df = st.session_state.harcamalar

with s_grv:
    if not st.session_state.istekler.empty:
        st.dataframe(st.session_state.istekler.drop(columns=['ID']), use_container_width=True)
    else: st.info("Görev yok.")

with s_grf:
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("Sektörel Dağılım")
            fig1, ax1 = plt.subplots()
            df.groupby('KATEGORİ')['TUTAR'].sum().plot(kind='pie', autopct='%1.1f%%', ax=ax1, cmap='Pastel1')
            ax1.set_ylabel(''); st.pyplot(fig1)
        with col2:
            st.write("Kişisel Harcama")
            fig2, ax2 = plt.subplots()
            df.groupby('KİŞİ')['TUTAR'].sum().plot(kind='bar', ax=ax2, color=['skyblue', 'salmon'])
            st.pyplot(fig2)
    else: st.warning("Veri yok.")

with s_lst:
    st.metric("Toplam Harcama", f"{df['TUTAR'].sum():,.2f} TL")
    st.dataframe(df, use_container_width=True)

def sekme_yap(df_input, kat, sekme, emoji):
    with sekme:
        d = df_input[df_input['KATEGORİ'] == kat]
        if not d.empty:
            st.metric(f"{emoji} Toplam", f"{d['TUTAR'].sum():,.2f} TL")
            st.dataframe(d, use_container_width=True)
        else: st.info(f"{kat} harcaması yok.")

sekme_yap(df, "DÜĞÜN & ÇEYİZ", s_dug, "👰")
sekme_yap(df, "MARKET", s_mrk, "🛒")
sekme_yap(df, "AKARYAKIT & ULAŞIM", s_ykt, "⛽")
sekme_yap(df, "YEMEK & KAFE", s_ymk, "🍔")
