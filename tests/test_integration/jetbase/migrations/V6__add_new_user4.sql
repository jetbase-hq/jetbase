-- Add new user
INSERT INTO users (name) VALUES 
    ('mike4');

-- ROLLBACK
DELETE FROM users WHERE name = 'mike4';