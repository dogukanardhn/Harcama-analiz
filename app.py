import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="Harcama Analizi", page_icon="💳", layout="wide")

st.title("📊 Detaylı Harcama Analiz Uygulamam")
st.markdown("Ekstre PDF'ini yükle, kategori ve mekan bazlı tüm detayları gör!")

uploaded_file = st.file_uploader("Vakıfbank PDF'ini Seç", type=["pdf"])

if uploaded_file is not None:
    veriler = []
    sablon = re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+((?:\+)?[\d,]+\.\d{2})')

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    match = sablon.search(line)
                    if match:
                        tarih, aciklama, tutar_str = match.groups()
                        if '+' in tutar_str or 'ÖNCEKİ DÖNEM' in aciklama.upper() or 'SON ÖDE' in aciklama.upper():
                            continue
                        tutar = float(tutar_str.replace(',', ''))
                        if tutar > 0:
                            veriler.append([tarih, aciklama, tutar])

    if veriler:
        df = pd.DataFrame(veriler, columns=['TARİH', 'AÇIKLAMA', 'TUTAR'])
        
        # Gelişmiş Kategorizasyon Sözlüğü
        kategoriler = {
            'MARKET': ['BIM', 'A101', 'FILE', 'KIPA', 'MIGROS', 'CIGDEMCI', 'METRO', 'CARREFOUR', 'SOK', 'ŞOK', 'MARKET', 'GROSMARKET'],
            'YEMEK & KAFE': ['FAST FOOD', 'KANTİN', 'TRENDYOL YEMEK', 'YEMEKSEPETI', 'GETIRYEMEK', 'RESTAURANT', 'CAFE', 'KASAP', 'FIRIN', 'IZGARA', 'LOKANTA', 'PASTANE', 'KADAYIF', 'BÜFE', 'PİDE', 'TATLICI'],
            'AKARYAKIT & ULAŞIM': ['TOTAL', 'PEGASUS', 'AJET', 'OTOPARK', 'ESHOT', 'PETROL', 'OPET', 'SHELL', 'BP', 'AYTEMİZ', 'TCDD', 'THY'],
            'TEKNOLOJİ & E-TİCARET': ['HEPSIBURADA', 'HEPSIPAY', 'IDEFIX', 'TRENDYOL', 'AMAZON', 'N11', 'VATAN', 'MEDIAMARKT'],
            'SAĞLIK': ['ECZANE', 'HASTANE', 'SAĞLIK', 'OPTİK'],
            'KURUM / DİĞER ÖDEMELER': ['VAKFI', 'DERNEĞİ', 'KUVVETL', 'KUVVETLERİ', 'TSK', 'VERGİ', 'ÖD/'],
            'EĞLENCE': ['HIPODROM', 'SİNEMA', 'BİLETİX']
        }

        def kategori_bul(desc):
            desc = str(desc).upper()
            for kat, keywords in kategoriler.items():
                for word in keywords:
                    if word in desc: return kat
            return 'DİĞER'

        df['KATEGORİ'] = df['AÇIKLAMA'].apply(kategori_bul)

        # --- GÖRSELLEŞTİRME VE ARAYÜZ ---
        st.metric("Bu Ayki Toplam Harcama", f"{df['TUTAR'].sum():,.2f} TL")
        
        # Ekranı 2 Kolona Böl
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Kategori Dağılımı")
            kat_ozet = df.groupby('KATEGORİ')['TUTAR'].sum()
            fig1, ax1 = plt.subplots()
            
            # HATA BURADAYDI: Matplotlib yerine Pandas çizicisi kullandık
            kat_ozet.plot(kind='pie', ax=ax1, autopct='%1.1f%%', startangle=140, cmap='Set2')
            ax1.set_ylabel('') # Y eksenindeki çirkin "TUTAR" yazısını siler
            st.pyplot(fig1)

        with col2:
            st.subheader("Market Harcamaları Detayı")
            # Sadece Market kategorisini filtrele
            market_df = df[df['KATEGORİ'] == 'MARKET']
            if not market_df.empty:
                market_ozet = market_df.groupby('AÇIKLAMA')['TUTAR'].sum().sort_values(ascending=True)
                fig2, ax2 = plt.subplots()
                market_ozet.plot(kind='barh', ax=ax2, color='skyblue')
                ax2.set_xlabel("Tutar (TL)")
                ax2.set_ylabel("")
                st.pyplot(fig2)
            else:
                st.info("Bu ay market harcaması bulunamadı.")
                
        st.subheader("En Çok Para Harcanan İlk 10 Yer")
        top10 = df.groupby('AÇIKLAMA')['TUTAR'].sum().sort_values(ascending=False).head(10)
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        top10.plot(kind='bar', ax=ax3, color='coral')
        plt.xticks(rotation=45, ha='right')
        ax3.set_xlabel("")
        ax3.set_ylabel("Tutar (TL)")
        st.pyplot(fig3)

        st.subheader("Tüm İşlem Dökümü")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Excel (CSV) Olarak İndir", csv, "harcamalarim.csv", "text/csv")
    else:
        st.warning("Geçerli harcama bulunamadı.")
