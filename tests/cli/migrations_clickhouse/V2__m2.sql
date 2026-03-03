INSERT INTO users (name) VALUES ('mike2');

--rollback
DELETE FROM users WHERE name = 'mike2';