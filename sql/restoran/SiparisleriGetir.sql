SELECT DISTINCT
    s.sparisNo,
    s.durum,
    s.teslimAdres,
    e.name AS efendiName,
    e.surname AS efendiSurname,
    e.telno AS efendiTelno,
    k.name AS kuryeName,
    k.surname AS kuryeSurname,
    k.telno AS kuryeTelno,
    a.il,
    a.ilce,
    a.mah,
    a.cd,
    a.binano,
    a.daireno
FROM sparis s
JOIN efendi e ON s.efendiID = e.ID
JOIN Adres a ON s.efendiID = a.efendiID AND s.teslimAdres = a.adresName
JOIN sparisUrunler su ON s.sparisNo = su.sparisNo
JOIN yemek y ON su.yemekID = y.ID
LEFT JOIN kurye k ON s.kuryeID = k.ID
WHERE y.restoranID = %s AND s.durum != 'Arrived'
ORDER BY s.sparisNo DESC
