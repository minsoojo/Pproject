CREATE TABLE member (
    name VARCHAR(50) NOT NULL,
    uid  VARCHAR(50) NOT NULL PRIMARY KEY,
    pass VARCHAR(50) NOT NULL
);

INSERT INTO member (name, uid, pass)
VALUES ('조민수', '1', '1234');

INSERT INTO member (name, uid, pass)
VALUES ('박소영', '2', '1234');

INSERT INTO member (name, uid, pass)
VALUES ('신채은', '3', '1234');

INSERT INTO member (name, uid, pass)
VALUES ('이유진', '4', '1234');

INSERT INTO member (name, uid, pass)
VALUES ('유준하', '5', '1234');