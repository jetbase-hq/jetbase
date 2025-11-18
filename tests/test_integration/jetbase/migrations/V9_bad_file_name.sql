-- Add new user
INSERT INTO users (name) VALUES 
    ('bad user');

-- ROLLBACK
DELETE FROM users WHERE name = 'bad user';