-- Add new user
INSERT INTO users (name) VALUES 
    ('mike5');

-- ROLLBACK
DELETE FROM users WHERE name = 'mike5';