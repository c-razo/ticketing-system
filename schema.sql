-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('Admin', 'Agent', 'User')) NOT NULL
);

-- Tickets Table
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT CHECK(status IN ('Open', 'In Progress', 'Resolved')) NOT NULL DEFAULT 'Open',
    priority TEXT CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')) NOT NULL,
    user_id INTEGER NOT NULL,
    agent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(agent_id) REFERENCES users(id)
);
