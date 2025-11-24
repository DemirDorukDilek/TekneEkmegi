SELECT 
    r.ID AS restoranID,
    k.ID AS kuryeID,
    ((r.X - k.X)*(r.X - k.X) + (r.Y - k.Y)*(r.Y - k.Y)) AS uzaklikKaresi
FROM restoran r
CROSS JOIN kurye k
ORDER BY uzaklikKaresi ASC
LIMIT 1;