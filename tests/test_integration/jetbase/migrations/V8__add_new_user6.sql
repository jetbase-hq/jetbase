-- Add new user
INSERT INTO users (name) VALUES 
    ('mike6');

-- ROLLBACK
DELETE FROM users WHERE name = 'mike6';