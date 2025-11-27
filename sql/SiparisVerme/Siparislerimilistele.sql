SELECT 
    s.sparisNo,
    s.durum,
    s.teslimAdres,
    GROUP_CONCAT(CONCAT(y.name, ' (', su.adet, 'x)') SEPARATOR ', ') AS urunler,
    SUM(y.price * su.adet) AS toplamFiyat,
    r.name AS restoranAdi,
    CONCAT(k.name, ' ', k.surname) AS kuryeAdi
FROM sparis s
JOIN sparisUrunler su ON s.sparisNo = su.sparisNo
JOIN yemek y ON su.yemekID = y.ID
JOIN restoran r ON y.restoranID = r.ID
LEFT JOIN kurye k ON s.kuryeID = k.ID
WHERE s.efendiID = %s
GROUP BY s.sparisNo, s.durum, s.teslimAdres, r.name, k.name, k.surname
ORDER BY s.sparisNo DESC