-- Drop existing tables (if any)
DROP TABLE IF EXISTS app_user CASCADE;
DROP TABLE IF EXISTS task CASCADE;
DROP TABLE IF EXISTS urgency CASCADE;
DROP TABLE IF EXISTS task_status CASCADE;
DROP TABLE IF EXISTS overdue_tasks CASCADE;

-- Create app_user table
CREATE TABLE app_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Create task_status table
CREATE TABLE task_status (
    id SERIAL PRIMARY KEY,
    status TEXT
);

-- Create urgency table
CREATE TABLE urgency (
    id SERIAL PRIMARY KEY,
    urgency TEXT,
    terminal BOOLEAN
);

-- Create task table with user_id foreign key
CREATE TABLE task (
    id SERIAL PRIMARY KEY,
    task TEXT NOT NULL,
    date_of_task DATE NOT NULL,
    day TEXT,
    points TEXT,
    urgency_id INTEGER REFERENCES urgency(id),
    status_id INTEGER REFERENCES task_status(id),
    user_id INTEGER REFERENCES app_user(id) ON DELETE CASCADE
);

-- Create overdue_tasks table with user_id foreign key
CREATE TABLE overdue_tasks (
    id SERIAL PRIMARY KEY,
    task TEXT NOT NULL,
    date_of_task DATE NOT NULL,
    day TEXT,
    points TEXT,
    urgency_id INTEGER REFERENCES urgency(id),
    status_id INTEGER REFERENCES task_status(id),
    user_id INTEGER REFERENCES app_user(id) ON DELETE CASCADE
);

-- Insert permanant data
INSERT INTO urgency (urgency, terminal) VALUES ('Very Important', FALSE);
INSERT INTO urgency (urgency, terminal) VALUES ('Important', FALSE);
INSERT INTO urgency (urgency, terminal) VALUES ('Normal', FALSE);
INSERT INTO urgency (urgency, terminal) VALUES ('Expendable', FALSE);

INSERT INTO task_status (status) VALUES ('Completed');


INSERT INTO task_status (status) VALUES ('Not Complete');


