import streamlit as st
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="Harcama Analizi", page_icon="💳")

st.title("📊 Harcama Analiz Uygulamam")
st.markdown("Ekstre PDF'ini yükle, gerisini uygulamaya bırak!")

# Dosya Yükleme Butonu
uploaded_file = st.file_uploader("Vakıfbank PDF'ini Seç", type=["pdf"])

if uploaded_file is not None:
    veriler = []
    # Regex Şablonu: Tarih + Açıklama + Tutar
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
        
        # Kategorizasyon Sözlüğü
        kategoriler = {
            'MARKET': ['BIM', 'A101', 'FILE', 'KIPA', 'MIGROS', 'CIGDEMCI'],
            'YEMEK': ['FAST FOOD', 'KANTİN', 'TRENDYOL YEMEK', 'RESTAURANT', 'CAFE', 'KASAP', 'FIRIN', 'IZGARA'],
            'ULAŞIM': ['TOTAL', 'PEGASUS', 'AJET', 'OTOPARK', 'ESHOT'],
            'TEKNOLOJİ': ['HEPSIBURADA', 'HEPSIPAY', 'IDEFIX', 'TRENDYOL'],
            'EĞLENCE': ['HIPODROM'],
            'DİĞER': []
        }

        def kategori_bul(desc):
            desc = str(desc).upper()
            for kat, keywords in kategoriler.items():
                for word in keywords:
                    if word in desc: return kat
            return 'DİĞER'

        df['KATEGORİ'] = df['AÇIKLAMA'].apply(kategori_bul)

        # Görselleştirme
        st.metric("Toplam Harcama", f"{df['TUTAR'].sum():,.2f} TL")
        
        kat_ozet = df.groupby('KATEGORİ')['TUTAR'].sum()
        fig, ax = plt.subplots()
        ax.pie(kat_ozet, labels=kat_ozet.index, autopct='%1.1f%%', startangle=140)
        st.pyplot(fig)

        st.dataframe(df, use_container_width=True)
        
        # Excel İndirme Butonu
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Excel (CSV) Olarak İndir", csv, "harcamalarim.csv", "text/csv")
    else:
        st.warning("Geçerli harcama bulunamadı.")
