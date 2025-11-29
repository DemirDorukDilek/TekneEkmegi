-- PRIMARY INDEXLER MYSQL OTOMATIK PRIMARY KEY E GORE OLUSTURULUR BU YUZDEN BURDAKI INDEXLER SECONDARY INDEX

CREATE INDEX idx_krediKartiOdeme_Kartno ON krediKartiOdeme(Kartno);

CREATE INDEX idx_yemek_restoranID ON yemek(restoranID);

CREATE INDEX idx_sepetUrunler_yemekID ON sepetUrunler(yemekID);

CREATE INDEX idx_sparisUrunler_yemekID ON sparisUrunler(yemekID);



CREATE INDEX idx_sparis_efendiID ON sparis(efendiID);

CREATE INDEX idx_sparis_durum ON sparis(durum);

CREATE INDEX idx_sparis_kurye_durum ON sparis(kuryeID, durum);



-- odeme takibi icin indexler
CREATE INDEX idx_nakitOdeme_EfendiOdedi ON nakitOdeme(EfendiOdedi);
CREATE INDEX idx_nakitOdeme_ParaTeslimAlindi ON nakitOdeme(ParaTeslimAlindi);

CREATE INDEX idx_krediKartiOdeme_EfendiOdedi ON krediKartiOdeme(EfendiOdedi);
CREATE INDEX idx_krediKartiOdeme_ParaTeslimAlindi ON krediKartiOdeme(ParaTeslimAlindi);

-- Kurye calisma durumu kontrolu icin
CREATE INDEX idx_kurye_isWorking ON kurye(isWorking);

-- Konum bazl1 sorgular icin (restoran ve kurye konumlar1)
CREATE INDEX idx_restoran_location ON restoran(X, Y);
CREATE INDEX idx_kurye_location ON kurye(X, Y);
CREATE INDEX idx_Adres_location ON Adres(X, Y);
