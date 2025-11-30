-- Kurye siparişi kabul eder
UPDATE sparis
SET kuryeID = ?, durum = 'Cook'
WHERE sparisNo = ? AND kuryeID IS NULL AND durum = 'Get'
