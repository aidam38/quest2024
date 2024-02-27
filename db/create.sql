CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    clue TEXT NOT NULL,
    code VARCHAR(6) NOT NULL,
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    UNIQUE (username)
);

CREATE TABLE IF NOT EXISTS finds (
    location_id INTEGER NOT NULL,
    mole_id INTEGER NOT NULL,
    CONSTRAINT fk_location
        FOREIGN KEY (location_id) 
        REFERENCES locations(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_mole
        FOREIGN KEY (mole_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    PRIMARY KEY (location_id, mole_id)
);

CREATE TABLE IF NOT EXISTS unlocked (
    location_id INTEGER NOT NULL,
    mole_id INTEGER NOT NULL,
    CONSTRAINT fk_location
        FOREIGN KEY (location_id) 
        REFERENCES locations(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_mole
        FOREIGN KEY (mole_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    PRIMARY KEY (location_id, mole_id)
);
