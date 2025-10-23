CREATE TABLE IF NOT EXISTS games (
     id         INTEGER,
     date       DATE     NOT NULL
                         DEFAULT (DATE('now') ),
     game       TEXT     NOT NULL,
     timestamp  DATETIME NOT NULL
                         DEFAULT (strftime('%FT%H:%M:%fZ', datetime('subsec', 'utc')))
                         CONSTRAINT explicit_utc CHECK (timestamp LIKE '%Z'),
     timezone   TEXT     NOT NULL
                         DEFAULT (DATETIME('Etc/Utc') ),
     text_data  TEXT,
     image_data BLOB,
     UNIQUE (date, game),
     PRIMARY KEY (id));
CREATE TABLE IF NOT EXISTS outimgs (
     id       INTEGER,
     gentime  DATETIME NOT NULL
                       CONSTRAINT explicit_utc CHECK (gentime LIKE '%Z'),
     timezone TEXT     NOT NULL
                       DEFAULT (DATETIME('Etc/Utc') ),
     date     DATE     NOT NULL
                       UNIQUE,
     hash     BLOB     NOT NULL,
     PRIMARY KEY (id));
CREATE UNIQUE INDEX IF NOT EXISTS games_index ON games (
    date DESC,
    game
);
CREATE UNIQUE INDEX IF NOT EXISTS outimgs_index ON outimgs (
    date DESC
);
CREATE VIEW IF NOT EXISTS games_per_day AS
    SELECT date,
           COUNT( * ) AS games_per_day
    FROM games
    GROUP BY date
    ORDER BY date DESC;
CREATE VIEW IF NOT EXISTS  play_counts AS
    SELECT game,
           COUNT( * ) AS play_count,
           MAX(date) AS last_played,
           MIN(date) AS first_played
    FROM games
    GROUP BY game
    ORDER BY game;
