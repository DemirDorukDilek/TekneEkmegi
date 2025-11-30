SELECT s.yemekID, y.name, y.price, s.adet, r.name as restoranAdi, r.ID as restoranID
FROM sepetUrunler s
JOIN yemek y ON s.yemekID = y.ID
JOIN restoran r ON y.restoranID = r.ID
WHERE s.efendiID = ?