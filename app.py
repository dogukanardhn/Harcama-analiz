import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Aile Bütçesi", page_icon="🏡", layout="wide")

# 1. HAFIZA OLUŞTURMA (ID Sistemi eklendi)
if 'harcamalar' not in st.session_state:
    st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KİŞİ', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
if 'istekler' not in st.session_state:
    # Hangi isteğin kime ait olduğunu takip etmek için gizli bir 'ID' sütunu
    st.session_state.istekler = pd.DataFrame(columns=['ID', 'KİMDEN', 'KİME', 'İSTEK', 'DURUM'])
    st.session_state.istek_id_sayaci = 0

# 2. SOL MENÜ - KULLANICI VE GİRDİ
st.sidebar.title("Kullanıcı Paneli")
kullanici = st.sidebar.radio("👤 Kim İşlem Yapıyor?", ["Doğukan", "Eşim"])
st.sidebar.divider()

st.sidebar.header("➕ Yeni Harcama Ekle")
with st.sidebar.form("veri_giris_formu", clear_on_submit=True):
    tarih = st.date_input("İşlem Tarihi")
    kategori = st.selectbox("Kategori", ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "TEKNOLOJİ", "DİĞER"])
    aciklama = st.text_input("Açıklama", placeholder="Örn: Arabaya yakıt, pazar alışverişi...")
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
    # Kullanıcı kendisi dışındakine istek atsın diye mantık
    hedef_kisi = "Eşim" if kullanici == "Doğukan" else "Doğukan"
    st.markdown(f"**Alıcı:** {hedef_kisi}")
    istek_metni = st.text_input("Ne Lazım?", placeholder="Örn: Akşam gelirken su alır mısın?")
    istek_btn = st.form_submit_button("İsteği Gönder")

    if istek_btn and istek_metni:
        st.session_state.istek_id_sayaci += 1
        yeni_istek = pd.DataFrame([{
            'ID': st.session_state.istek_id_sayaci,
            'KİMDEN': kullanici,
            'KİME': hedef_kisi,
            'İSTEK': istek_metni,
            'DURUM': 'Bekliyor ⏳'
        }])
        st.session_state.istekler = pd.concat([st.session_state.istekler, yeni_istek], ignore_index=True)
        st.sidebar.success("İstek başarıyla iletildi!")

# 3. ANA EKRAN - BİLDİRİMLER VE SEKMELER
st.title("🏡 Aile Bütçesi ve Planlama Paneli")

# BİLDİRİM EKRANI: Aktif kullanıcıya ait "Bekleyen" istekleri bul
bekleyen_istekler = st.session_state.istekler[(st.session_state.istekler['KİME'] == kullanici) & (st.session_state.istekler['DURUM'] == 'Bekliyor ⏳')]

if not bekleyen_istekler.empty:
    st.warning(f"🔔 Sana atanmış {len(bekleyen_istekler)} adet yeni görev/istek var!")
    for index, row in bekleyen_istekler.iterrows():
        col_metin, col_buton = st.columns([4, 1])
        with col_metin:
            st.info(f"**{row['KİMDEN']}** istiyor: {row['İSTEK']}")
        with col_buton:
            # Karşıla butonuna basıldığında o ID'ye ait durumu günceller
            if st.button("✅ Karşıla", key=f"btn_{row['ID']}"):
                st.session_state.istekler.loc[st.session_state.istekler['ID'] == row['ID'], 'DURUM'] = 'Tamamlandı ✅'
                st.rerun() # Sayfayı yenileyip bildirimi kaldırır

st.markdown("---")

sekme_istek, sekme_grafik, sekme_genel = st.tabs([
    "💬 İstekler & Görevler Paneli",
    "📈 Aylık Grafikler",
    "📊 Tüm Harcama Tablosu"
])

df = st.session_state.harcamalar
df_istek = st.session_state.istekler

with sekme_istek:
    st.subheader("Görev Geçmişi")
    if not df_istek.empty:
        # ID sütununu ekranda kalabalık yapmasın diye gizleyerek gösteriyoruz
        gosterilecek_istekler = df_istek.drop(columns=['ID'])
        st.dataframe(gosterilecek_istekler, use_container_width=True)
        if st.button("Tüm İstek Geçmişini Temizle"):
            st.session_state.istekler = pd.DataFrame(columns=['ID', 'KİMDEN', 'KİME', 'İSTEK', 'DURUM'])
            st.rerun()
    else:
        st.info("Şu an bekleyen veya tamamlanmış bir istek yok.")

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
