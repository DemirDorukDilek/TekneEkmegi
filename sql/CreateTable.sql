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
    CONSTRAINT postiveAdet CHECK adet>0
);


CREATE TABLE sparis(
    sparisNo    INT             NOT NULL AUTO_INCREMENT,
    efendiID    INT             NOT NULL,
    durum       VARCHAR(10)     NOT NULL    DEFAULT "Get",
    kuryeID     INT             DEFAULT NULL,
    teslimAdres VARCHAR(20)     NOT NULL,

    CONSTRAINT PK PRIMARY KEY(sparisNo),
    CONSTRAINT sparisFKefendiID FOREIGN KEY(efendiID) REFERENCES efendi(ID),
    CONSTRAINT sparisFKkuryeID FOREIGN KEY(kuryeID) REFERENCES kurye(ID),
    CONSTRAINT sparisFKteslimAdres FOREIGN KEY(efendiID,teslimAdres) REFERENCES Adres(efendiID,adresName),
    CONSTRAINT ENUMdurum CHECK (durum in ("Get","Cook","OnWay","Arrived")),
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
    odemeNo                 INT         NOT NULL AUTO_INCREMENT,
    odemeDate               DATE        NOT NULL,
    price                   FLOAT       NOT NULL CHECK (price >= 0),
    EfendiOdedi             BOOLEAN     DEFAULT false, -- Musteriden para alindi
    ParaTeslimAlindi        BOOLEAN     DEFAULT false, -- Para Sisteme Ulasti (Nakit odendi ise kuryeden aliniyor)
    KuryeUcretiOdendi       BOOLEAN     DEFAULT false, -- kuryeye parasi ondendi
    RestoranUcretiOdendi    BOOLEAN     DEFAULT false, -- restorana parasi odendi

    CONSTRAINT PK PRIMARY KEY(odemeNo),
    CONSTRAINT nakitOdemeFKsparisNo FOREIGN KEY(sparisNo) REFERENCES sparis(sparisNo),
    CONSTRAINT UNQspraisNo UNIQUE (sparisNo)
);

CREATE TABLE krediKartiOdeme(
    sparisNo                INT         NOT NULL,
    odemeNo                 INT         NOT NULL AUTO_INCREMENT,
    odemeDate               DATE        NOT NULL,
    price                   FLOAT       NOT NULL CHECK (price >= 0),
    EfendiOdedi             BOOLEAN     DEFAULT false,
    ParaTeslimAlindi        BOOLEAN     DEFAULT false,
    KuryeUcretiOdendi       BOOLEAN     DEFAULT false,
    RestoranUcretiOdendi    BOOLEAN     DEFAULT false,

    cvv                     INT(3)            NOT NULL,
    kartSahibiAdi           VARCHAR(60)       NOT NULL,
    Kartno                  INT(16)           NOT NULL,
    dueDate                 DATE              NOT NULL,

    CONSTRAINT PK PRIMARY KEY(odemeNo),
    CONSTRAINT krediKartiOdemeFKsparisNo FOREIGN KEY(sparisNo) REFERENCES sparis(sparisNo),
    CONSTRAINT UNQspraisNo UNIQUE (sparisNo)
);

