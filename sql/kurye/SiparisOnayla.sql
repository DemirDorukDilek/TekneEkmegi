UPDATE sparis
SET durum = 'OnWay'
WHERE kuryeID=? AND sparisNo = ? AND durum='Cook'
