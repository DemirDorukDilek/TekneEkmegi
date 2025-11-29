SELECT
    y.name AS yemekAdi,
    y.price AS yemekFiyat,
    su.adet,
    (y.price * su.adet) AS toplamFiyat
FROM sparisUrunler su
JOIN yemek y ON su.yemekID = y.ID
WHERE su.sparisNo = %s AND y.restoranID = %s
