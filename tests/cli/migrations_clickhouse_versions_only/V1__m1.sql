CREATE TABLE users
(
    id UUID DEFAULT generateUUIDv4(),
    name String
)
ENGINE = MergeTree
ORDER BY id;