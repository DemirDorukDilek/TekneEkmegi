DROP TABLE IF EXISTS sparisUrunler;
DROP TABLE IF EXISTS sepetUrunler;
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
    password    VARCHAR(20)     NOT NULL,

    CONSTRAINT PK PRIMARY KEY(ID),
    CONSTRAINT UNQtelno UNIQUE(telno),
    CONSTRAINT UNQemail UNIQUE(email)
);

CREATE TABLE restoran(
    ID                  INT             NOT NULL AUTO_INCREMENT,
    name                VARCHAR(100)    NOT NULL,
    telno               VARCHAR(14)     NOT NULL,
    adres               VARCHAR(200)    NOT NULL,
    minsepettutari      INT             CHECK (minsepettutari>=0) DEFAULT 0 NOT NULL,

    CONSTRAINT PK PRIMARY KEY(ID),
    CONSTRAINT UNQtelno UNIQUE(telno)
);

CREATE TABLE kurye(
    ID          INT             NOT NULL AUTO_INCREMENT,
    name        VARCHAR(30)     NOT NULL,
    telno       VARCHAR(14)     NOT NULL,
    email       VARCHAR(75),
    password    VARCHAR(20)     NOT NULL,

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

    CONSTRAINT PK PRIMARY KEY(efendiID,adresName),
    CONSTRAINT AdresFKefendiID FOREIGN KEY(efendiID) REFERENCES efendi(ID)
);

CREATE TABLE sepetUrunler(
    efendiID    INT        NOT NULL,
    yemekID     INT        NOT NULL,

    CONSTRAINT PK PRIMARY KEY(efendiID,yemekID),
    CONSTRAINT sepetUrunlerFKefendiID FOREIGN KEY(efendiID) REFERENCES efendi(ID),
    CONSTRAINT sepetUrunlerFKyemekID FOREIGN KEY(yemekID) REFERENCES yemek(ID)
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

    CONSTRAINT PK PRIMARY KEY(sparisNo,yemekID),
    CONSTRAINT sparisFKsparisNo FOREIGN KEY(sparisNo) REFERENCES sparis(sparisNo),
    CONSTRAINT sparisFKyemekID FOREIGN KEY(yemekID) REFERENCES yemek(ID)
);