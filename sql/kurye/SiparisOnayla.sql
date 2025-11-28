UPDATE sparis
SET kuryeID = %s, durum = 'Cook'
WHERE sparisNo = %s AND kuryeID IS NULL
