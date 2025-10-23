CREATE TABLE IF NOT EXISTS dat (
     id         INTEGER,
     date       DATE     NOT NULL
                         DEFAULT (DATE('now') ),
     game       TEXT     NOT NULL,
     timestamp  DATETIME NOT NULL
                         DEFAULT (DATETIME('now') ),
     timezone   TEXT     NOT NULL
                         DEFAULT (DATETIME('Etc/Utc') ),
     text_data  TEXT,
     image_data BLOB,
     UNIQUE (date, game),
     PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS outimgs (
     id      INTEGER,
     gentime DATETIME NOT NULL,
     date    DATE     NOT NULL
                      UNIQUE,
     hash    BLOB     NOT NULL,
     PRIMARY KEY (id));
CREATE UNIQUE INDEX IF NOT EXISTS games_index ON dat (
    date DESC,
    game
);
CREATE UNIQUE INDEX IF NOT EXISTS outimgs_index ON outimgs (
    date DESC
);
