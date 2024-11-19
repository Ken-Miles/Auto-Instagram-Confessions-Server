CREATE TABLE IF NOT EXISTS accounts (
        username VARCHAR (255) UNIQUE NOT NULL,
        password VARCHAR (255)
);

INSERT INTO accounts (username, password) VALUES ('manoj', 'manoj');

CREATE TABLE  IF NOT EXISTS entries (
        id  SERIAL PRIMARY KEY,
        entry TEXT NOT NULL
);

CREATE TABLE  IF NOT EXISTS accepted (
        id INT UNIQUE NOT NULL
);

CREATE TABLE  IF NOT EXISTS declined (
        id INT UNIQUE NOT NULL
);

CREATE TABLE  IF NOT EXISTS skipped (
        id INT UNIQUE NOT NULL
);

CREATE TABLE  IF NOT EXISTS sessions (
        session_id text PRIMARY KEY,
        username VARCHAR (255) NOT NULL,
        login_time TIMESTAMP
);

-- INSERT INTO sessions (session_id, username, login_time) VALUES ('session_id', 'manoj', current_timestamp);