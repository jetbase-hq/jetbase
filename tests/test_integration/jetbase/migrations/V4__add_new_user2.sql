-- Add new user
INSERT INTO users (name) VALUES 
    ('mike2');

-- ROLLBACK
DELETE FROM users WHERE name = 'mike2';