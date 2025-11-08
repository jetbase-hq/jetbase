-- Add new user
INSERT INTO users (name) VALUES 
    ('mike3');

-- ROLLBACK
DELETE FROM users WHERE name = 'mike3';