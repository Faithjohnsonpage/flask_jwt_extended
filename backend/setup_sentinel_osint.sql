-- Prepares a MySQL server for the project (development environment)
CREATE DATABASE IF NOT EXISTS sentinel_osint;
CREATE USER 'sentinel_user'@'localhost' IDENTIFIED BY 'strongpassword';
GRANT ALL PRIVILEGES ON sentinel_osint.* TO 'sentinel_user'@'localhost';

-- Prepares a MySQL server for the project (testing environment)
CREATE DATABASE IF NOT EXISTS sentinel_osint_test;
CREATE USER 'sentinel_test_user'@'localhost' IDENTIFIED BY 'testpassword';
GRANT ALL PRIVILEGES ON sentinel_osint_test.* TO 'sentinel_test_user'@'localhost';

-- Apply privileges
FLUSH PRIVILEGES;
