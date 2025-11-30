SELECT 
    restoran.ID AS restoranID,
    efendi.ID AS EfendiID,
    ((restoran.X - Adres.X)*(restoran.X - Adres.X) + (restoran.Y - Adres.Y)*(restoran.Y - Adres.Y)) AS distSqr,
    restoran.name
FROM
    Adres
    JOIN efendi on efendi.ID=Adres.efendiID
    CROSS JOIN restoran
WHERE efendi.ID = ? AND restoran.name LIKE ?
ORDER BY distSqr ASC
