import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

st.set_page_config(page_title="Aile Bütçesi", page_icon="🏡", layout="wide")

# 1. HAFIZA OLUŞTURMA
if 'harcamalar' not in st.session_state:
    st.session_state.harcamalar = pd.DataFrame(columns=['TARİH', 'KİŞİ', 'KATEGORİ', 'AÇIKLAMA', 'TUTAR'])
if 'istekler' not in st.session_state:
    st.session_state.istekler = pd.DataFrame(columns=['ID', 'KİMDEN', 'KİME', 'İSTEK', 'DURUM'])
    st.session_state.istek_id_sayaci = 0

kategoriler = ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "TEKNOLOJİ", "EĞLENCE", "SAĞLIK", "DİĞER"]

# --- AÇILIR PENCERE (POPUP) FONKSİYONU ---
@st.dialog("Görevi Karşıla ve Harcamayı Gir")
def gorev_tamamla_penceresi(istek_id, istek_metni, aktif_kullanici):
    st.info(f"**Yerine Getirilen Görev:** {istek_metni}")
    secilen_kat = st.selectbox("Bu harcama hangi kategoriye giriyor?", kategoriler)
    girilen_tutar = st.number_input("Ne kadar harcadın? (TL)", min_value=0.0, format="%.2f")
    
    if st.button("Kaydet ve Görevi Kapat"):
        # 1. Görevi tamamlandı yap
        st.session_state.istekler.loc[st.session_state.istekler['ID'] == istek_id, 'DURUM'] = 'Tamamlandı ✅'
        
        # 2. Harcamayı listeye ekle
        bugun = datetime.datetime.now().strftime("%d.%m.%Y")
        yeni_h = pd.DataFrame([{
            'TARİH': bugun,
            'KİŞİ': aktif_kullanici,
            'KATEGORİ': secilen_kat,
            'AÇIKLAMA': f"Görev: {istek_metni}",
            'TUTAR': float(girilen_tutar)
        }])
        st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, yeni_h], ignore_index=True)
        st.rerun()

# 2. SOL MENÜ - KULLANICI VE GİRDİ
st.sidebar.title("Kullanıcı Paneli")
kullanici = st.sidebar.radio("👤 Kim İşlem Yapıyor?", ["Doğukan", "Eşim"])
st.sidebar.divider()

st.sidebar.header("➕ Yeni Harcama Ekle")
with st.sidebar.form("veri_giris_formu", clear_on_submit=True):
    tarih = st.date_input("İşlem Tarihi")
    kategori = st.selectbox("Kategori", kategoriler)
    aciklama = st.text_input("Açıklama", placeholder="Örn: Clio'ya benzin, su faturası...")
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

# 3. ANA EKRAN - BİLDİRİMLER
st.title("🏡 Aile Bütçesi ve Planlama Paneli")

# Eğer aktif kullanıcıya atanmış bekleyen bir görev varsa, uyarı ekranı çıkar
bekleyen_istekler = st.session_state.istekler[(st.session_state.istekler['KİME'] == kullanici) & (st.session_state.istekler['DURUM'] == 'Bekliyor ⏳')]

if not bekleyen_istekler.empty:
    st.warning(f"🔔 Sana atanmış {len(bekleyen_istekler)} adet yeni görev/istek var!")
    for index, row in bekleyen_istekler.iterrows():
        col_metin, col_buton = st.columns([4, 1])
        with col_metin:
            st.info(f"**{row['KİMDEN']}** istiyor: {row['İSTEK']}")
        with col_buton:
            # Butona basıldığında yukarıda yazdığımız popup penceresi açılır
            if st.button("✅ Karşıla", key=f"btn_{row['ID']}"):
                gorev_tamamla_penceresi(row['ID'], row['İSTEK'], kullanici)

st.markdown("---")

# 4. KATEGORİ SEKMELERİ
sekmeler = st.tabs([
    "💬 Görevler", 
    "📈 Grafikler", 
    "📊 Tüm Liste", 
    "🛒 Market", 
    "⛽ Akaryakıt", 
    "🍔 Yemek", 
    "📱 Teknoloji", 
    "🎭 Eğlence"
])
s_gorev, s_grafik, s_tumu, s_market, s_yakit, s_yemek, s_tekno, s_eglence = sekmeler

df = st.session_state.harcamalar
df_istek = st.session_state.istekler

with s_gorev:
    st.subheader("Görev Geçmişi")
    if not df_istek.empty:
        gosterilecek_istekler = df_istek.drop(columns=['ID'])
        st.dataframe(gosterilecek_istekler, use_container_width=True)
    else:
        st.info("Kayıtlı istek yok.")

with s_grafik:
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
        st.warning("Henüz yeterli veri yok.")

with s_tumu:
    st.subheader("Tüm Harcama Dökümü")
    if not df.empty:
        st.metric("Toplam Aile Harcaması", f"{df['TUTAR'].sum():,.2f} TL")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Kayıt yok.")

# Kategoriler için sekmeleri dolduran yardımcı bir araç
def kategori_sekmesi_doldur(kat_adi, baslik, emoji):
    st.subheader(f"{emoji} {baslik} Harcamaları")
    df_kat = df[df['KATEGORİ'] == kat_adi]
    if not df_kat.empty:
        st.metric(f"{baslik} Toplamı", f"{df_kat['TUTAR'].sum():,.2f} TL")
        st.dataframe(df_kat, use_container_width=True)
    else:
        st.warning(f"Bu ay {baslik.lower()} harcaması yapılmadı.")

with s_market:
    kategori_sekmesi_doldur("MARKET", "Market", "🛒")
with s_yakit:
    kategori_sekmesi_doldur("AKARYAKIT & ULAŞIM", "Akaryakıt & Ulaşım", "⛽")
with s_yemek:
    kategori_sekmesi_doldur("YEMEK & KAFE", "Yemek & Kafe", "🍔")
with s_tekno:
    kategori_sekmesi_doldur("TEKNOLOJİ", "Teknoloji", "📱")
with s_eglence:
    kategori_sekmesi_doldur("EĞLENCE", "Eğlence", "🎭")
