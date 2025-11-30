SELECT 
    k.ID AS kuryeID,
    ((r.X - k.X)*(r.X - k.X) + (r.Y - k.Y)*(r.Y - k.Y)) AS uzaklikKaresi
FROM kurye k
CROSS JOIN restoran r
WHERE r.ID = ? 
  AND k.isWorking = TRUE
  AND k.ID NOT IN (
      SELECT kuryeID FROM sparis 
      WHERE kuryeID IS NOT NULL 
        AND durum IN ('Get', 'Cook', 'OnWay')
  )
ORDER BY uzaklikKaresi ASC
LIMIT 1