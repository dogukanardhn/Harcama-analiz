import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 1. SAYFA VE TEMA AYARLARI
st.set_page_config(page_title="Aile Finans Asistanı", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

# Mobil cihazlarda sol menüyü hamburger ikonu içine otomatik saklar, ekranı ferahlatır.
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
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

# --- GÖREV KARŞILAMA PENCERESİ ---
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

# 3. SOL SÜTUN (KONTROL MERKEZİ)
with st.sidebar:
    st.title("⚙️ Kontrol Paneli")
    kullanici = st.radio("👤 Kim Kullanıyor?", ["Doğukan", "Eşim"])
    
    st.divider()
    # AKILLI BÜTÇE LİMİTİ BELİRLEME
    aylik_limit = st.number_input("🎯 Bu Ayki Bütçe Hedefimiz (TL)", min_value=1000, value=30000, step=1000)
    
    st.divider()
    with st.expander("➕ Hızlı Harcama Gir"):
        with st.form("h_form", clear_on_submit=True):
            kat = st.selectbox("Kategori", kategoriler)
            tarih = st.date_input("Tarih")
            aciklama = st.text_input("Açıklama")
            tutar = st.number_input("Tutar", min_value=0.0)
            if st.form_submit_button("Kaydet"):
                if aciklama:
                    y_v = pd.DataFrame([{
                        'TARİH': tarih.strftime("%d.%m.%Y"), 
                        'AY_YIL': tarih.strftime("%m-%Y"),
                        'KİŞİ': kullanici, 'KATEGORİ': kat, 'AÇIKLAMA': aciklama.upper(), 'TUTAR': float(tutar)
                    }])
                    st.session_state.harcamalar = pd.concat([st.session_state.harcamalar, y_v], ignore_index=True)
                    st.rerun()

    with st.expander("📌 Yeni Görev İste"):
        with st.form("i_form", clear_on_submit=True):
            hedef = "Eşim" if kullanici == "Doğukan" else "Doğukan"
            metin = st.text_input(f"{hedef} için istek:")
            if st.form_submit_button("Gönder"):
                if metin:
                    st.session_state.istek_id_sayaci += 1
                    y_i = pd.DataFrame([{'ID': st.session_state.istek_id_sayaci, 'KİMDEN': kullanici, 'KİME': hedef, 'İSTEK': metin, 'DURUM': 'Bekliyor ⏳'}])
                    st.session_state.istekler = pd.concat([st.session_state.istekler, y_i], ignore_index=True)
                    st.rerun()

    st.divider()
    # HAYAT KURTARAN GERİ AL BUTONU
    if not st.session_state.harcamalar.empty:
        if st.button("↩️ Son İşlemi Sil (Hata Düzelt)"):
            st.session_state.harcamalar.drop(index=st.session_state.harcamalar.index[-1], inplace=True)
            st.rerun()
            
    st.divider()
    st.subheader("📁 Menü")
    sayfa = st.radio("Alan Seçin:", ["📈 Özet Paneli", "💬 Görevler", "📊 Tüm Liste", "👰 Düğün & Çeyiz", "🛒 Market", "⛽ Akaryakıt", "🍔 Yemek & Kafe", "📱 Teknoloji", "🎓 Eğitim", "💧 Su & Fatura"])

# 4. ANA EKRAN (DASHBOARD)
# Gelişmiş Ay/Yıl Filtresi
mevcut_aylar = st.session_state.harcamalar['AY_YIL'].unique().tolist()
su_an = datetime.datetime.now().strftime("%m-%Y")
if su_an not in mevcut_aylar: mevcut_aylar.append(su_an)

col_baslik, col_filtre = st.columns([3, 1])
with col_baslik:
    st.title(f"💳 {sayfa}")
with col_filtre:
    secilen_donem = st.selectbox("📅 Dönem Filtresi", sorted(mevcut_aylar, reverse=True))

# Seçilen döneme göre verileri filtrele
df = st.session_state.harcamalar
df_aylik = df[df['AY_YIL'] == secilen_donem]

# Bildirimler (Hep En Üstte)
bekleyen = st.session_state.istekler[(st.session_state.istekler['KİME'] == kullanici) & (st.session_state.istekler['DURUM'] == 'Bekliyor ⏳')]
if not bekleyen.empty:
    st.error(f"🔔 Dikkat! Bekleyen {len(bekleyen)} görevin var!")
    for idx, row in bekleyen.iterrows():
        c1, c2 = st.columns([5, 1])
        c1.warning(f"**{row['KİMDEN']}**: {row['İSTEK']}")
        if c2.button("✅ Karşıla", key=f"b_{row['ID']}"):
            gorev_tamamla_penceresi(row['ID'], row['İSTEK'], kullanici)

st.divider()

# --- YARDIMCI FONKSİYON (Zincirin Dışına, Üste Alındı!) ---
def kategori_goster(kat_anahtar, emoji):
    d_kat = df_aylik[df_aylik['KATEGORİ'] == kat_anahtar]
    if not d_kat.empty:
        st.metric(f"{emoji} {kat_anahtar} Dönem Toplamı", f"{d_kat['TUTAR'].sum():,.2f} TL")
        st.dataframe(d_kat, use_container_width=True)
    else: st.info(f"Bu ay {kat_anahtar} kategorisinde harcama yok.")


# --- SAYFA İÇERİKLERİ (Kesintisiz Zincir) ---
if sayfa == "📈 Özet Paneli":
    toplam_harcama = df_aylik['TUTAR'].sum()
    
    # Akıllı Bütçe Barı Hesaplaması
    yuzde = min(toplam_harcama / aylik_limit, 1.0)
    
    st.subheader(f"Hedef Bütçe Durumu ({secilen_donem})")
    st.progress(yuzde)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Aylık Harcama", f"{toplam_harcama:,.2f} TL")
    col_b.metric("Kalan Bütçe", f"{(aylik_limit - toplam_harcama):,.2f} TL")
    
    # Düğün & Çeyiz Genel Toplamı (Filtresiz, Bugüne Kadarki Tüm Masraf)
    dugun_toplam = df[df['KATEGORİ'] == "DÜĞÜN & ÇEYİZ"]['TUTAR'].sum()
    col_c.metric("👰 Toplam Çeyiz Masrafı", f"{dugun_toplam:,.2f} TL")
    
    st.divider()
    
    if not df_aylik.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Sektörel Dağılım**")
            fig1, ax1 = plt.subplots(figsize=(4,3))
            df_aylik.groupby('KATEGORİ')['TUTAR'].sum().plot(kind='pie', autopct='%1.1f%%', ax=ax1, cmap='Set3')
            ax1.set_ylabel(''); st.pyplot(fig1)
        with c2:
            st.markdown("**Kişisel Harcama Dağılımı**")
            fig2, ax2 = plt.subplots(figsize=(4,3))
            df_aylik.groupby('KİŞİ')['TUTAR'].sum().plot(kind='bar', ax=ax2, color=['#7ac5cd', '#ff9999'])
            plt.xticks(rotation=0); st.pyplot(fig2)
    else:
        st.info("Bu döneme ait henüz bir harcama grafiği oluşmadı.")

elif sayfa == "💬 Görevler":
    if not st.session_state.istekler.empty:
        st.dataframe(st.session_state.istekler.drop(columns=['ID']), use_container_width=True)
    else: st.info("Henüz bir görev kaydı yok.")

elif sayfa == "📊 Tüm Liste":
    st.dataframe(df_aylik, use_container_width=True)

elif sayfa == "👰 Düğün & Çeyiz": kategori_goster("DÜĞÜN & ÇEYİZ", "👰")
elif sayfa == "🛒 Market": kategori_goster("MARKET", "🛒")
elif sayfa == "⛽ Akaryakıt": kategori_goster("AKARYAKIT & ULAŞIM", "⛽")
elif sayfa == "🍔 Yemek & Kafe": kategori_goster("YEMEK & KAFE", "🍔")
elif sayfa == "📱 Teknoloji": kategori_goster("TEKNOLOJİ", "📱")
elif sayfa == "🎓 Eğitim": kategori_goster("EĞİTİM", "🎓")
elif sayfa == "💧 Su & Fatura": kategori_goster("SU & FATURA", "💧")
