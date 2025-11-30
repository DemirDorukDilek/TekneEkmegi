SELECT
    s.sparisNo,
    s.durum,
    s.teslimAdres,
    e.name AS efendiName,
    e.surname AS efendiSurname,
    e.telno AS efendiTelno,
    a.il,
    a.ilce,
    a.mah,
    a.cd,
    a.binano,
    a.daireno,
    a.X AS teslimX,
    a.Y AS teslimY,
    r.name AS restoranName,
    r.telno AS restoranTelno,
    r.adres AS restoranAdres,
    r.X AS restoranX,
    r.Y AS restoranY
FROM sparis s
JOIN efendi e ON s.efendiID = e.ID
JOIN Adres a ON s.efendiID = a.efendiID AND s.teslimAdres = a.adresName
JOIN sparisUrunler su ON s.sparisNo = su.sparisNo
JOIN yemek y ON su.yemekID = y.ID
JOIN restoran r ON y.restoranID = r.ID
WHERE s.kuryeID = ? AND s.durum IN ('Cook', 'OnWay')
LIMIT 1
