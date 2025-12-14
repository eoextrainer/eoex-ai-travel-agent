CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  surname VARCHAR(100) NOT NULL,
  date_of_birth DATE,
  current_location VARCHAR(255),
  current_budget DECIMAL(12,2),
  travel_preferences ENUM('business','personal') DEFAULT 'personal',
  travel_companions ENUM('none','1','2','3','4') DEFAULT 'none',
  special_travel_needs TEXT,
  username VARCHAR(100) UNIQUE,
  role ENUM('user','admin') DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS journeys (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  destination_country VARCHAR(100),
  destination_city VARCHAR(100),
  budget DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS flights (
  id INT AUTO_INCREMENT PRIMARY KEY,
  journey_id INT NOT NULL,
  airline VARCHAR(100),
  origin_city VARCHAR(100),
  destination_city VARCHAR(100),
  departure_date DATE,
  arrival_date DATE,
  price DECIMAL(12,2),
  FOREIGN KEY (journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS accommodations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  journey_id INT NOT NULL,
  name VARCHAR(255),
  address VARCHAR(255),
  city VARCHAR(100),
  price_per_night DECIMAL(12,2),
  FOREIGN KEY (journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS transportation (
  id INT AUTO_INCREMENT PRIMARY KEY,
  journey_id INT NOT NULL,
  type VARCHAR(100),
  provider VARCHAR(100),
  price DECIMAL(12,2),
  FOREIGN KEY (journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS food_choices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  journey_id INT NOT NULL,
  restaurant VARCHAR(255),
  cuisine VARCHAR(100),
  price_range VARCHAR(50),
  FOREIGN KEY (journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS shopping_choices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  journey_id INT NOT NULL,
  shop_name VARCHAR(255),
  category VARCHAR(100),
  price_range VARCHAR(50),
  FOREIGN KEY (journey_id) REFERENCES journeys(id)
);

CREATE TABLE IF NOT EXISTS places_to_visit (
  id INT AUTO_INCREMENT PRIMARY KEY,
  journey_id INT NOT NULL,
  place_name VARCHAR(255),
  category VARCHAR(100),
  description TEXT,
  FOREIGN KEY (journey_id) REFERENCES journeys(id)
);

-- Geography seed tables
CREATE TABLE IF NOT EXISTS continents (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS countries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  continent_id INT NOT NULL,
  name VARCHAR(128) NOT NULL,
  UNIQUE KEY uniq_country (continent_id, name),
  FOREIGN KEY (continent_id) REFERENCES continents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS capitals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  country_id INT NOT NULL,
  name VARCHAR(128) NOT NULL,
  UNIQUE KEY uniq_capital (country_id, name),
  FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE CASCADE
);

INSERT INTO users (first_name, surname, date_of_birth, current_location, current_budget, travel_preferences, travel_companions, special_travel_needs, username, role)
VALUES ('Default', 'Traveler', '1990-01-01', 'Madrid', 2000.00, 'personal', 'none', NULL, 'traveler-1', 'user')
ON DUPLICATE KEY UPDATE username=VALUES(username);

INSERT INTO users (first_name, surname, date_of_birth, current_location, current_budget, travel_preferences, travel_companions, special_travel_needs, username, role)
VALUES ('Admin', 'User', '1985-05-05', 'Global', 999999.99, 'business', 'none', NULL, 'admin', 'admin')
ON DUPLICATE KEY UPDATE username=VALUES(username);
