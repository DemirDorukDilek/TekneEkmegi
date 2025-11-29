SELECT DISTINCT
    s.sparisNo,
    s.teslimAdres,
    e.name AS efendiName,
    e.surname AS efendiSurname,
    r.name AS restoranName,
    r.adres AS restoranAdres,
    r.X AS restoranX,
    r.Y AS restoranY,
    COALESCE(
        SQRT(POW(r.X - COALESCE(k.X, 0), 2) +
             POW(r.Y - COALESCE(k.Y, 0), 2)),
        999999
    ) AS mesafe
FROM sparis s
JOIN efendi e ON s.efendiID = e.ID
JOIN sparisUrunler su ON s.sparisNo = su.sparisNo
JOIN yemek y ON su.yemekID = y.ID
JOIN restoran r ON y.restoranID = r.ID
LEFT JOIN kurye k ON k.ID = %s
WHERE s.durum = 'Get' AND s.kuryeID IS NULL
ORDER BY mesafe ASC
LIMIT 10
