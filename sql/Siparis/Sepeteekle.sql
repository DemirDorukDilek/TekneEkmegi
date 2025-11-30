INSERT INTO sepetUrunler(efendiID, yemekID, adet) 
VALUES (?, ?, ?)
ON DUPLICATE KEY UPDATE adet = adet + ?