CREATE DATABASE airport_project;

USE airport_project;

CREATE TABLE food_orders (

    id INT AUTO_INCREMENT PRIMARY KEY,

    restaurant VARCHAR(100),

    food_name VARCHAR(100),

    quantity INT,

    price INT,

    total_price INT
);

CREATE TABLE ticket_bookings (

    id INT AUTO_INCREMENT PRIMARY KEY,

    passenger_name VARCHAR(100),

    source VARCHAR(100),

    destination VARCHAR(100),

    flight_number VARCHAR(50),

    travel_date DATE,

    seat_type VARCHAR(50)
);

CREATE TABLE flights (

    id INT AUTO_INCREMENT PRIMARY KEY,

    flight_no VARCHAR(20),

    destination VARCHAR(100),

    time TIME,

    status VARCHAR(50),

    gate INT
);

CREATE TABLE IF NOT EXISTS ticket_bookings (

    id INT AUTO_INCREMENT PRIMARY KEY,

    passenger_name VARCHAR(100),

    source VARCHAR(100),

    destination VARCHAR(100),

    flight_number VARCHAR(50),

    travel_date DATE,

    seat_type VARCHAR(50)
);


