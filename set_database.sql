CREATE DATABASE ndlawyers_data;
CREATE USER 'nd_lawyers'@'localhost' IDENTIFIED BY 'admin';
GRANT ALL PRIVILEGES ON ndlawyers_data.* TO 'nd_lawyers'@'localhost';
FLUSH PRIVILEGES;