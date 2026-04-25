import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 1. SAYFA VE TEMA AYARLARI
st.set_page_config(page_title="Aile Finans Asistanı", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            [data-testid="stStatusWidget"] {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. GOOGLE SHEETS BAĞLANTISI (Gerçek Veritabanı)
conn = st.connection("gsheets", type=GSheetsConnection)

# Verileri Google Sheets'ten Çek
def verileri_yukle():
    h_df = conn.read(worksheet="Harcamalar", ttl="1m")
    i_df = conn.read(worksheet="Istekler", ttl="1m")
    return h_df, i_df

df_harcamalar, df_istekler = verileri_yukle()

kategoriler = ["MARKET", "YEMEK & KAFE", "AKARYAKIT & ULAŞIM", "DÜĞÜN & ÇEYİZ", "TEKNOLOJİ", "EĞİTİM", "SU & FATURA", "SAĞLIK", "DİĞER"]

# --- GÖREV KARŞILAMA PENCERESİ ---
@st.dialog("✅ Görevi Tamamla")
def gorev_tamamla_penceresi(istek_id, istek_metni, aktif_kullanici):
    st.write(f"**Görev:** {istek_metni}")
    secilen_kat = st.selectbox("Hangi kategori?", kategoriler)
    girilen_tutar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
    if st.button("Kaydet ve Veritabanına Yaz"):
        # 1. İstek Durumunu Güncelle
        df_istekler.loc[df_istekler['ID'] == istek_id, 'DURUM'] = 'Tamamlandı ✅'
        conn.update(worksheet="Istekler", data=df_istekler)
        
        # 2. Harcamayı Ekle
        bugun = datetime.datetime.now()
        yeni_h = pd.DataFrame([{
            'TARİH': bugun.strftime("%d.%m.%Y"), 
            'AY_YIL': bugun.strftime("%m-%Y"),
            'KİŞİ': aktif_kullanici, 
            'KATEGORİ': secilen_kat, 
            'AÇIKLAMA': f"Görev: {istek_metni}", 
            'TUTAR': float(girilen_tutar)
        }])
        guncel_h = pd.concat([df_harcamalar, yeni_h], ignore_index=True)
        conn.update(worksheet="Harcamalar", data=guncel_h)
        st.success("Veritabanı güncellendi!")
        st.rerun()

# 3. SOL SÜTUN (KONTROL MERKEZİ)
with st.sidebar:
    st.title("⚙️ Kontrol Paneli")
    kullanici = st.radio("👤 Kim Kullanıyor?", ["Doğukan", "Aybüke"])
    
    st.divider()
    aylik_limit = st.number_input("🎯 Bütçe Hedefi (TL)", min_value=1000, value=30000, step=1000)
    
    st.divider()
    with st.expander("➕ Hızlı Harcama Gir"):
        with st.form("h_form", clear_on_submit=True):
            kat = st.selectbox("Kategori", kategoriler)
            tarih = st.date_input("Tarih")
            aciklama = st.text_input("Açıklama")
            tutar = st.number_input("Tutar", min_value=0.0)
            if st.form_submit_button("Buluta Kaydet"):
                if aciklama:
                    y_v = pd.DataFrame([{
                        'TARİH': tarih.strftime("%d.%m.%Y"), 
                        'AY_YIL': tarih.strftime("%m-%Y"),
                        'KİŞİ': kullanici, 'KATEGORİ': kat, 'AÇIKLAMA': aciklama.upper(), 'TUTAR': float(tutar)
                    }])
                    guncel_h = pd.concat([df_harcamalar, y_v], ignore_index=True)
                    conn.update(worksheet="Harcamalar", data=guncel_h)
                    st.rerun()

    with st.expander("📌 Yeni Görev İste"):
        with st.form("i_form", clear_on_submit=True):
            hedef = "Aybüke" if kullanici == "Doğukan" else "Doğukan"
            metin = st.text_input(f"{hedef} için istek:")
            if st.form_submit_button("Gönder"):
                if metin:
                    yeni_id = int(df_istekler['ID'].max()) + 1 if not df_istekler.empty else 1
                    y_i = pd.DataFrame([{'ID': yeni_id, 'KİMDEN': kullanici, 'KİME': hedef, 'İSTEK': metin, 'DURUM': 'Bekliyor ⏳'}])
                    guncel_i = pd.concat([df_istekler, y_i], ignore_index=True)
                    conn.update(worksheet="Istekler", data=guncel_i)
                    st.rerun()

    if not df_harcamalar.empty:
        if st.button("↩️ Son İşlemi Sil"):
            guncel_h = df_harcamalar.drop(index=df_harcamalar.index[-1])
            conn.update(worksheet="Harcamalar", data=guncel_h)
            st.rerun()
            
    st.divider()
    st.subheader("📁 Menü")
    sayfa = st.radio("Alan Seçin:", ["📈 Özet Paneli", "💬 Görevler", "📊 Tüm Liste", "👰 Düğün & Çeyiz", "🛒 Market", "⛽ Akaryakıt", "🍔 Yemek & Kafe", "📱 Teknoloji", "🎓 Eğitim", "💧 Su & Fatura"])

# 4. ANA EKRAN VE AKILLI DÖNEM SEÇİCİ
taban_aylar = [f"{str(m).zfill(2)}-2026" for m in range(4, 13)] 
mevcut_aylar = df_harcamalar['AY_YIL'].unique().tolist() if not df_harcamalar.empty else []
for ay in taban_aylar:
    if ay not in mevcut_aylar: mevcut_aylar.append(ay)

mevcut_aylar_sirali = sorted(mevcut_aylar, key=lambda d: datetime.datetime.strptime(d, "%m-%Y"), reverse=True)
su_an = datetime.datetime.now().strftime("%m-%Y")
try: varsayilan_idx = mevcut_aylar_sirali.index(su_an)
except ValueError: varsayilan_idx = 0

col_baslik, col_filtre = st.columns([3, 1])
with col_baslik: st.title(f"💳 {sayfa}")
with col_filtre: secilen_donem = st.selectbox("📅 Dönem Filtresi", mevcut_aylar_sirali, index=varsayilan_idx)

df_aylik = df_harcamalar[df_harcamalar['AY_YIL'] == secilen_donem]

# BİLDİRİMLER
bekleyen = df_istekler[(df_istekler['KİME'] == kullanici) & (df_istekler['DURUM'] == 'Bekliyor ⏳')]
if not bekleyen.empty:
    st.error(f"🔔 Dikkat! {kullanici}, bekleyen {len(bekleyen)} görevin var!")
    for idx, row in bekleyen.iterrows():
        c1, c2 = st.columns([5, 1])
        c1.warning(f"**{row['KİMDEN']}**: {row['İSTEK']}")
        if c2.button("✅ Karşıla", key=f"b_{row['ID']}"):
            gorev_tamamla_penceresi(row['ID'], row['İSTEK'], kullanici)

st.divider()

# --- SAYFALAR ---
def kategori_goster(kat_anahtar, emoji, df_input):
    d_kat = df_input[df_input['KATEGORİ'] == kat_anahtar]
    if not d_kat.empty:
        st.metric(f"{emoji} {kat_anahtar} Dönem Toplamı", f"{d_kat['TUTAR'].sum():,.2f} TL")
        st.dataframe(d_kat, use_container_width=True)
    else: st.info(f"Bu ay {kat_anahtar} kategorisinde harcama yok.")

if sayfa == "📈 Özet Paneli":
    toplam_harcama = df_aylik['TUTAR'].sum()
    yuzde = min(toplam_harcama / aylik_limit, 1.0) if aylik_limit > 0 else 0.0
    st.subheader(f"Bütçe Durumu ({secilen_donem})")
    st.progress(yuzde)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Aylık Harcama", f"{toplam_harcama:,.2f} TL")
    col_b.metric("Kalan Bütçe", f"{(aylik_limit - toplam_harcama):,.2f} TL")
    dugun_toplam = df_harcamalar[df_harcamalar['KATEGORİ'] == "DÜĞÜN & ÇEYİZ"]['TUTAR'].sum()
    col_c.metric("👰 Toplam Çeyiz Masrafı", f"{dugun_toplam:,.2f} TL")
    
    if not df_aylik.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Sektörel Dağılım**")
            fig1, ax1 = plt.subplots(figsize=(4,3))
            df_aylik.groupby('KATEGORİ')['TUTAR'].sum().plot(kind='pie', autopct='%1.1f%%', ax=ax1, cmap='Set3')
            ax1.set_ylabel(''); st.pyplot(fig1)
        with c2:
            st.markdown("**Bireysel Harcama**")
            fig2, ax2 = plt.subplots(figsize=(4,3))
            df_aylik.groupby('KİŞİ')['TUTAR'].sum().plot(kind='bar', ax=ax2, color=['#7ac5cd', '#ff9999'])
            plt.xticks(rotation=0); st.pyplot(fig2)

elif sayfa == "💬 Görevler":
    st.dataframe(df_istekler.drop(columns=['ID']), use_container_width=True)

elif sayfa == "📊 Tüm Liste":
    st.dataframe(df_aylik, use_container_width=True)

elif sayfa == "👰 Düğün & Çeyiz": kategori_goster("DÜĞÜN & ÇEYİZ", "👰", df_aylik)
elif sayfa == "🛒 Market": kategori_goster("MARKET", "🛒", df_aylik)
elif sayfa == "⛽ Akaryakıt": kategori_goster("AKARYAKIT & ULAŞIM", "⛽", df_aylik)
elif sayfa == "🍔 Yemek & Kafe": kategori_goster("YEMEK & KAFE", "🍔", df_aylik)
elif sayfa == "📱 Teknoloji": kategori_goster("TEKNOLOJİ", "📱", df_aylik)
elif sayfa == "🎓 Eğitim": kategori_goster("EĞİTİM", "🎓", df_aylik)
elif sayfa == "💧 Su & Fatura": kategori_goster("SU & FATURA", "💧", df_aylik)
