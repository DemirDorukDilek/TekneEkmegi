 DROP TABLE IF EXISTS sparisUrunler;
DROP TABLE IF EXISTS sepetUrunler;
DROP TABLE IF EXISTS nakitOdeme;
DROP TABLE IF EXISTS krediKartiOdeme;
DROP TABLE IF EXISTS sparis;
DROP TABLE IF EXISTS Adres;
DROP TABLE IF EXISTS yemek;
DROP TABLE IF EXISTS kurye;
DROP TABLE IF EXISTS restoran;
DROP TABLE IF EXISTS efendi;
DROP TABLE IF EXISTS kredikarti;


CREATE TABLE efendi(
    ID          INT             NOT NULL AUTO_INCREMENT,
    name        VARCHAR(30)     NOT NULL,
    surname     VARCHAR(30)     NOT NULL,
    telno       VARCHAR(14)     NOT NULL,
    email       VARCHAR(75),
    password    VARCHAR(255)    NOT NULL,

    CONSTRAINT PK PRIMARY KEY(ID),
    CONSTRAINT UNQtelno UNIQUE(telno),
    CONSTRAINT UNQemail UNIQUE(email)
);

CREATE TABLE restoran(
    ID                  INT             NOT NULL AUTO_INCREMENT,
    name                VARCHAR(100)    NOT NULL,
    telno               VARCHAR(14)     NOT NULL,
    adres               VARCHAR(200)    NOT NULL,
    minsepettutari      INT             DEFAULT 0 NOT NULL CHECK (minsepettutari>=0),
    password    VARCHAR(255)      NOT NULL,
    X           FLOAT             NOT NULL,
    Y           FLOAT             NOT NULL,

    CONSTRAINT PK PRIMARY KEY(ID),
    CONSTRAINT UNQtelno UNIQUE(telno)
);

CREATE TABLE kurye(
    ID          INT             NOT NULL AUTO_INCREMENT,
    name        VARCHAR(30)     NOT NULL,
    surname        VARCHAR(30)     NOT NULL,
    telno       VARCHAR(14)     NOT NULL,
    email       VARCHAR(75),
    password    VARCHAR(255)    NOT NULL,
    Y           FLOAT,
    X           FLOAT,
    isWorking   BOOLEAN         NOT NULL DEFAULT FALSE,

    CONSTRAINT PK PRIMARY KEY(ID),
    CONSTRAINT UNQtelno UNIQUE(telno),
    CONSTRAINT UNQemail UNIQUE(email)
);

CREATE TABLE yemek(
    ID                  INT             NOT NULL AUTO_INCREMENT,
    name                VARCHAR(100)    NOT NULL,
    price               FLOAT           NOT NULL CHECK (price >= 0),
    restoranID          INT             NOT NULL,
    

    CONSTRAINT PK PRIMARY KEY(ID),
    CONSTRAINT FKrestoranID FOREIGN KEY(restoranID) REFERENCES restoran(ID)
);

CREATE TABLE Adres(
    efendiID        INT             NOT NULL,
    adresName       VARCHAR(20)     NOT NULL,
    il              VARCHAR(50)     NOT NULL,
    ilce            VARCHAR(50)     NOT NULL,
    mah             VARCHAR(50)     NOT NULL,
    cd              VARCHAR(50)     NOT NULL,
    binano          VARCHAR(50)     NOT NULL,
    daireno         VARCHAR(50)     NOT NULL,

    X           FLOAT             NOT NULL,
    Y           FLOAT             NOT NULL,

    CONSTRAINT PK PRIMARY KEY(efendiID,adresName),
    CONSTRAINT AdresFKefendiID FOREIGN KEY(efendiID) REFERENCES efendi(ID)
);

CREATE TABLE sepetUrunler(
    efendiID    INT        NOT NULL,
    yemekID     INT        NOT NULL,
    adet        INT        NOT NULL,

    CONSTRAINT PK PRIMARY KEY(efendiID,yemekID),
    CONSTRAINT sepetUrunlerFKefendiID FOREIGN KEY(efendiID) REFERENCES efendi(ID),
    CONSTRAINT sepetUrunlerFKyemekID FOREIGN KEY(yemekID) REFERENCES yemek(ID),
    CONSTRAINT positiveAdet CHECK (adet > 0)
);

CREATE TABLE sparis(
    sparisNo    INT             NOT NULL AUTO_INCREMENT,
    efendiID    INT             NOT NULL,
    durum       VARCHAR(20)     NOT NULL    DEFAULT "Get",
    kuryeID     INT             DEFAULT NULL,
    teslimAdres VARCHAR(20)     NOT NULL,

    CONSTRAINT PK PRIMARY KEY(sparisNo),
    CONSTRAINT sparisFKefendiID FOREIGN KEY(efendiID) REFERENCES efendi(ID),
    CONSTRAINT sparisFKkuryeID FOREIGN KEY(kuryeID) REFERENCES kurye(ID),
    CONSTRAINT sparisFKteslimAdres FOREIGN KEY(efendiID,teslimAdres) REFERENCES Adres(efendiID,adresName),
    CONSTRAINT ENUMdurum CHECK (durum in ("Get","Cook","OnWay","Arrived","Cancelled","CancelledSeen")),
    CONSTRAINT CNSTkurye CHECK (kuryeID is NULL OR durum <> "Get")
);

CREATE TABLE sparisUrunler(
    sparisNo    INT     NOT NULL,
    yemekID     INT     NOT NULL,
    adet        INT     NOT NULL,
    CONSTRAINT PK PRIMARY KEY(sparisNo,yemekID),
    CONSTRAINT sparisFKsparisNo FOREIGN KEY(sparisNo) REFERENCES sparis(sparisNo),
    CONSTRAINT sparisFKyemekID FOREIGN KEY(yemekID) REFERENCES yemek(ID)
);

CREATE TABLE nakitOdeme(
    sparisNo                INT         NOT NULL,
    odemeDate               DATE        NOT NULL,
    price                   FLOAT       NOT NULL CHECK (price >= 0),

    CONSTRAINT PK PRIMARY KEY(sparisNo),
    CONSTRAINT nakitOdemeFKsparisNo FOREIGN KEY(sparisNo) REFERENCES sparis(sparisNo),
    CONSTRAINT UNQspraisNo UNIQUE (sparisNo)
);
create TABLE kredikarti(
    Kartno                  VARCHAR(16)           NOT NULL,
    cvv                     INT(3)            NOT NULL,
    kartSahibiAdi           VARCHAR(60)       NOT NULL,
    dueDate                 VARCHAR(4)              NOT NULL,

    CONSTRAINT PK PRIMARY KEY(Kartno)
);

CREATE TABLE krediKartiOdeme(
    sparisNo                INT         NOT NULL,
    odemeDate               DATE        NOT NULL,
    price                   FLOAT       NOT NULL CHECK (price >= 0),
    Kartno                  VARCHAR(16)           NOT NULL,

    CONSTRAINT PK PRIMARY KEY(sparisNo),
    CONSTRAINT krediKartiOdemeFKsparisNo FOREIGN KEY(sparisNo) REFERENCES sparis(sparisNo),
    CONSTRAINT krediKartiFK FOREIGN KEY(Kartno) REFERENCES kredikarti(Kartno),
    CONSTRAINT UNQspraisNo UNIQUE (sparisNo)
);

--DELIMITER//

CREATE TRIGGER check_single_restaurant_before_insert
BEFORE INSERT ON sepetUrunler
FOR EACH ROW
BEGIN
    DECLARE existing_restaurant_id INT;

    SELECT DISTINCT y.restoranID INTO existing_restaurant_id
    FROM sepetUrunler su
    JOIN yemek y ON su.yemekID = y.ID
    WHERE su.efendiID = NEW.efendiID
    LIMIT 1;

    IF existing_restaurant_id IS NOT NULL THEN
        IF existing_restaurant_id != (SELECT restoranID FROM yemek WHERE ID = NEW.yemekID) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Sepetinizde farklı bir restorandan ürün var. Lütfen önce sepetinizi boşaltın.';
        END IF;
    END IF;
END//

CREATE TRIGGER check_single_restaurant_before_update
BEFORE UPDATE ON sepetUrunler
FOR EACH ROW
BEGIN
    DECLARE existing_restaurant_id INT;

    SELECT DISTINCT y.restoranID INTO existing_restaurant_id
    FROM sepetUrunler su
    JOIN yemek y ON su.yemekID = y.ID
    WHERE su.efendiID = NEW.efendiID
      AND su.yemekID != OLD.yemekID
    LIMIT 1;

    IF existing_restaurant_id IS NOT NULL THEN
        IF existing_restaurant_id != (SELECT restoranID FROM yemek WHERE ID = NEW.yemekID) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Sepetinizde farklı bir restorandan ürün var. Lütfen önce sepetinizi boşaltın.';
        END IF;
    END IF;
END//
