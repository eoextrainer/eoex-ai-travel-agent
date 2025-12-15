-- Reset geo schema: drop old geo tables and create regions/countries/cities
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS cities;
DROP TABLE IF EXISTS capitals;
DROP TABLE IF EXISTS countries;
DROP TABLE IF EXISTS continents;
SET FOREIGN_KEY_CHECKS=1;

CREATE TABLE IF NOT EXISTS regions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS countries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  region_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  UNIQUE KEY uniq_country (region_id, name),
  FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  country_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  is_capital TINYINT(1) DEFAULT 0,
  UNIQUE KEY uniq_city (country_id, name),
  FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE CASCADE
);