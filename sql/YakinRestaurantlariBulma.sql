SELECT 
    r.ID AS restoranID,
    E.ID AS EfendiID,
    ((r.X - E.X)*(r.X - E.X) + (r.Y - E.Y)*(r.Y - E.Y)) AS uzaklikKaresi
FROM restoran r
CROSS JOIN Efendi E
where uzaklikKaresi <10000;