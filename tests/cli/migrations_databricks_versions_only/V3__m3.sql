INSERT INTO users (name) VALUES ('mike3');

--rollback
DELETE FROM users WHERE name = 'mike3';