-- Prepares a MySQL server for the project (development environment)
CREATE DATABASE IF NOT EXISTS proforce_db;
CREATE USER 'proforce_user'@'localhost' IDENTIFIED BY 'proforce12345';
GRANT ALL PRIVILEGES ON proforce_db.* TO 'proforce_user'@'localhost';

-- Prepares a MySQL server for the project (testing environment)
CREATE DATABASE IF NOT EXISTS proforce_db_test;
CREATE USER 'proforce_user_test'@'localhost' IDENTIFIED BY 'proforce12345#';
GRANT ALL PRIVILEGES ON proforce_db_test.* TO 'proforce_user_test'@'localhost';

-- Apply privileges
FLUSH PRIVILEGES;
