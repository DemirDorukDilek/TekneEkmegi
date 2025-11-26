SELECT ID, name, price 
FROM yemek 
WHERE restoranID = %s
ORDER BY name ASC