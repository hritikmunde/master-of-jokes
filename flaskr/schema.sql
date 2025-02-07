DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS joke;
DROP TABLE IF EXISTS joke_taken;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    nickname TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'User',
    joke_balance INTEGER DEFAULT 0
);

CREATE TABLE joke (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rating REAL DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE joke_taken (
    user_id INTEGER NOT NULL,
    joke_id INTEGER NOT NULL,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rating INTEGER,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (joke_id) REFERENCES joke (id),
    PRIMARY KEY (user_id, joke_id)
);
