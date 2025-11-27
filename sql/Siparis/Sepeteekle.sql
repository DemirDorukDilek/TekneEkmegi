INSERT INTO sepetUrunler(efendiID, yemekID, adet) 
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE adet = adet + %s