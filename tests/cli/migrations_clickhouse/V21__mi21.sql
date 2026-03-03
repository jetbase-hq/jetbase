INSERT INTO users (name) VALUES ('mike21');

--rollback
DELETE FROM users WHERE name = 'mike21';