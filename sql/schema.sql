CREATE DATABASE IF NOT EXISTS gym_inventory;
USE gym_inventory;

CREATE TABLE IF NOT EXISTS inventory_raw (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    quantity INT
);

CREATE TABLE IF NOT EXISTS inventory_cleaned (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    quantity INT
);
