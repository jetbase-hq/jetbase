-- Add new user
INSERT INTO users (name) VALUES 
    ('jake');

-- ROLLBACK
DELETE FROM users WHERE name = 'jake';