INSERT INTO users (name) VALUES ('mike4');

--rollback
DELETE FROM users WHERE name = 'mike4';