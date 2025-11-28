INSERT INTO krediKartiOdeme(sparisNo, odemeDate, price, cvv, kartSahibiAdi, Kartno, dueDate) 
VALUES (%s, CURDATE(), %s, %s, %s, %s, %s)