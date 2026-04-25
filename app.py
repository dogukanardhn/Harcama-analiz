import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Aile Bütçesi", page_icon="🏡", layout="wide")

# 1. HAFIZA OLUŞTURMA (Geçici Veritabanı)
if 'harcamalar' not in st.session_state:
    st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KİŞİ', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
if 'istekler' not in st.session_state:
    st.session_state.istekler = pd.DataFrame(columns=['KİMDEN', 'KİME', 'İSTEK', 'DURUM'])

# 2. SOL MENÜ - KULLANICI VE GİRDİ
st.sidebar.title("Kullanıcı Paneli")
kullanici = st.sidebar.radio("👤 Kim İşlem Yapıyor?", ["Doğukan", "Eşim"])
st.sidebar.divider()

st.sidebar.header("➕ Yeni Harcama Ekle")
with st.sidebar.form("veri_giris_formu", clear_on_submit=True):
    tarih = st.date_input("İşlem Tarihi")
    kategori = st.selectbox("Kategori", ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "TEKNOLOJİ", "DİĞER"])
    aciklama = st.text_input("Açıklama", placeholder="Örn: Clio'ya benzin, Migros alışverişi...")
    tutar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
    ekle_btn = st.form_submit_button("Harcamayı Kaydet")

    if ekle_btn and aciklama:
        yeni_veri = pd.DataFrame([{
            'TARİH': tarih.strftime("%d.%m.%Y"),
            'KİŞİ': kullanici,
            'KATEGORİ': kategori,
            'AÇIKLAMA': aciklama.upper(),
            'TUTAR': float(tutar)
        }])
        st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, yeni_veri], ignore_index=True)
        st.sidebar.success("Harcama listeye eklendi!")

st.sidebar.divider()

st.sidebar.header("📌 Yeni İstek/Görev Gönder")
with st.sidebar.form("istek_formu", clear_on_submit=True):
    kime = st.selectbox("Kime İstek Atıyorsun?", ["Eşim", "Doğukan"])
    istek_metni = st.text_input("Ne Lazım?", placeholder="Örn: Akşam gelirken su alır mısın?")
    istek_btn = st.form_submit_button("İsteği Gönder")

    if istek_btn and istek_metni:
        yeni_istek = pd.DataFrame([{
            'KİMDEN': kullanici,
            'KİME': kime,
            'İSTEK': istek_metni,
            'DURUM': 'Bekliyor ⏳'
        }])
        st.session_state.istekler = pd.concat([st.session_state.istekler, yeni_istek], ignore_index=True)
        st.sidebar.success("İstek paneline düştü!")

# 3. ANA EKRAN - SEKMELER
st.title("🏡 Aile Bütçesi ve Planlama Paneli")

sekme_istek, sekme_grafik, sekme_genel, sekme_market = st.tabs([
    "💬 İstekler & Görevler",
    "📈 Grafikler ve Analiz",
    "📊 Tüm Harcamalar",
    "🛒 Market"
])

df = st.session_state.harcamalar
df_istek = st.session_state.istekler

with sekme_istek:
    st.subheader("Birbirimize İlettiğimiz Görevler")
    if not df_istek.empty:
        st.dataframe(df_istek, use_container_width=True)
        if st.button("Tüm İstekleri Temizle"):
            st.session_state.istekler = pd.DataFrame(columns=['KİMDEN', 'KİME', 'İSTEK', 'DURUM'])
            st.rerun()
    else:
        st.info("Şu an bekleyen bir istek veya alınacak malzeme yok.")

with sekme_grafik:
    st.subheader("Aylık Harcama Raporu")
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Kategoriye Göre Yüzdeler**")
            kat_ozet = df.groupby('KATEGORİ')['TUTAR'].sum()
            fig1, ax1 = plt.subplots(figsize=(6,6))
            kat_ozet.plot(kind='pie', ax=ax1, autopct='%1.1f%%', startangle=140, cmap='Set3')
            ax1.set_ylabel('')
            st.pyplot(fig1)
        with col2:
            st.markdown("**Kim Ne Kadar Harcadı?**")
            kisi_ozet = df.groupby('KİŞİ')['TUTAR'].sum()
            fig2, ax2 = plt.subplots(figsize=(6,4))
            kisi_ozet.plot(kind='bar', ax=ax2, color=['#ff9999','#66b3ff'])
            ax2.set_ylabel("Toplam Tutar (TL)")
            plt.xticks(rotation=0)
            st.pyplot(fig2)
    else:
        st.warning("Grafik oluşturmak için soldan birkaç harcama girin.")

with sekme_genel:
    st.subheader("Tüm Harcama Dökümü")
    if not df.empty:
        st.metric("Toplam Aile Harcaması", f"{df['TUTAR'].sum():,.2f} TL")
        st.dataframe(df, use_container_width=True)
        if st.button("Tüm Harcamaları Sil"):
            st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KİŞİ', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
            st.rerun()
    else:
        st.info("Henüz sisteme harcama kaydedilmedi.")

with sekme_market:
    st.subheader("Sadece Market Harcamaları")
    df_market = df[df['KATEGORİ'] == 'MARKET']
    if not df_market.empty:
        st.metric("Market Toplamı", f"{df_market['TUTAR'].sum():,.2f} TL")
        st.dataframe(df_market, use_container_width=True)
    else:
        st.warning("Henüz market kategorisinde girdi yok.")
