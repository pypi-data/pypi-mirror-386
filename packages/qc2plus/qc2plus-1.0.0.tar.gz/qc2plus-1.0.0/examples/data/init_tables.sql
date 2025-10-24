
-- Basic demo schema and tables
CREATE SCHEMA IF NOT EXISTS demo;

-- Customers table
CREATE TABLE demo.customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE demo.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS demo.user_sessions (
    session_id SERIAL PRIMARY KEY,
    session_date DATE NOT NULL,
    user_id INTEGER NOT NULL,
    page_views INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Normal customers
INSERT INTO demo.customers (email, first_name, last_name, age, status, country, created_at) VALUES
('john.doe@email.com', 'John', 'Doe', 35, 'active', 'USA', CURRENT_DATE - INTERVAL '27 days'),
('xjohn.doe@email.com', 'XJohn', 'XDoe', 25, 'active', 'USA', CURRENT_DATE - INTERVAL '20 days'),
('yjohn.doe@email.com', 'YJohn', 'YDoe', 19, 'active', 'USA', CURRENT_DATE - INTERVAL '15 days'),
('zjohn.doe@email.com', 'ZJohn', 'ZDoe', 45, 'active', 'USA', CURRENT_DATE - INTERVAL '3 days'),
('jane.smith@email.com', 'Jane', 'Smith', 28, 'active', 'UK', CURRENT_DATE - INTERVAL '30 days'),
('xjane.smith@email.com', 'XJane', 'XSmith', 27, 'active', 'UK', CURRENT_DATE - INTERVAL '20 days'),
('yjane.smith@email.com', 'YJane', 'YSmith', 18, 'active', 'UK', CURRENT_DATE - INTERVAL '15 days'),
('zjane.smith@email.com', 'ZJane', 'ZSmith', 38, 'active', 'UK', CURRENT_DATE - INTERVAL '1 days'),
('bob.johnson@email.com', 'Bob', 'Johnson', 42, 'active', 'Canada', CURRENT_DATE - INTERVAL '29 days'),
('xbob.johnson@email.com', 'XBob', 'XJohnson', 41, 'active', 'Canada', CURRENT_DATE - INTERVAL '20 days'),
('ybob.johnson@email.com', 'YBob', 'YJohnson', 43, 'active', 'Canada', CURRENT_DATE - INTERVAL '12 days'),
('zbob.johnson@email.com', 'ZBob', 'ZJohnson', 82, 'active', 'Canada', CURRENT_DATE - INTERVAL '5 days'),
('alice.brown@email.com', 'Alice', 'Brown', 31, 'inactive', 'USA', CURRENT_DATE - INTERVAL '30 days'),
('xalice.brown@email.com', 'XAlice', 'XBrown', 43, 'active', 'USA', CURRENT_DATE - INTERVAL '18 days'),
('yalice.brown@email.com', 'YAlice', 'YBrown', 39, 'active', 'USA', CURRENT_DATE - INTERVAL '3 days'),
('zalice.brown@email.com', 'ZAlice', 'ZBrown', 21, 'active', 'USA', CURRENT_DATE - INTERVAL '2 days'),
('charlie.wilson@email.com', 'Charlie', 'Wilson', 29, 'active', 'UK', CURRENT_DATE - INTERVAL '27 days'),
('xcharlie.wilson@email.com', 'XCharlie', 'XWilson', 29, 'active', 'UK', CURRENT_DATE - INTERVAL '17 days'),
('ycharlie.wilson@email.com', 'yCharlie', 'yWilson', 49, 'active', 'UK', CURRENT_DATE - INTERVAL '8 days'),
('zcharlie.wilson@email.com', 'ZCharlie', 'ZWilson', 38, 'active', 'UK', CURRENT_DATE - INTERVAL '2 days');

-- Problematic customers data for testing for postgres
INSERT INTO demo.customers (email, first_name, last_name, age, status, country, created_at) VALUES
('invalid-email', 'Test', 'User1', 25, 'active', 'USA', CURRENT_DATE - INTERVAL '17 days'),  -- Invalid email
('test2@email.com', 'Test', 'User2', 150, 'active', 'USA', CURRENT_DATE - INTERVAL '25 days'); -- Invalid age

-- Orders with normal pattern (baseline)
INSERT INTO demo.orders (customer_id, order_date, total_amount, status) VALUES
(1, CURRENT_DATE - INTERVAL '30 days', 150.00, 'completed'),
(20, CURRENT_DATE - INTERVAL '30 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '30 days', 200.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '30 days', 95.00, 'completed'),
(9, CURRENT_DATE - INTERVAL '30 days', 220.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '30 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '30 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '29 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '29 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '29 days', 200.00, 'completed'),
(10, CURRENT_DATE - INTERVAL '29 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '29 days', 195.00, 'completed'),
(13, CURRENT_DATE - INTERVAL '29 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '29 days', 250.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '28 days', 50.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '28 days', 75.50, 'completed'),
(13, CURRENT_DATE - INTERVAL '28 days', 200.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '28 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '28 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '28 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '28 days', 85.00, 'completed'),

(2, CURRENT_DATE - INTERVAL '27 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '27 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '27 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '27 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '27 days', 120.00, 'completed'),
(14, CURRENT_DATE - INTERVAL '27 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '27 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '26 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '26 days', 75.50, 'completed'),
(1, CURRENT_DATE - INTERVAL '26 days', 180.00, 'completed'),
(12, CURRENT_DATE - INTERVAL '26 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '26 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '26 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '26 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '25 days', 150.00, 'completed'),
(11, CURRENT_DATE - INTERVAL '25 days', 175.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '25 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '25 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '25 days', 95.00, 'completed'),
(18, CURRENT_DATE - INTERVAL '25 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '25 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '24 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '24 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '24 days', 200.00, 'completed'),
(6, CURRENT_DATE - INTERVAL '24 days', 180.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '24 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '24 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '24 days', 85.00, 'completed'),

(2, CURRENT_DATE - INTERVAL '23 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '23 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '23 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '23 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '23 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '23 days', 250.00, 'completed'),
(13, CURRENT_DATE - INTERVAL '23 days', 185.00, 'completed'),

(15, CURRENT_DATE - INTERVAL '22 days', 150.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '22 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '22 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '22 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '22 days', 120.00, 'completed'),
(6, CURRENT_DATE - INTERVAL '22 days', 50.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '22 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '21 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '21 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '21 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '21 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '21 days', 295.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '21 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '21 days', 250.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '20 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '20 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '20 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '20 days', 380.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '20 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '20 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '20 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '19 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '19 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '19 days', 100.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '19 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '19 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '19 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '19 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '18 days', 150.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '18 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '18 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '18 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '18 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '18 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '18 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '17 days', 250.00, 'completed'),
(19, CURRENT_DATE - INTERVAL '17 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '17 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '17 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '17 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '17 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '17 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '16 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '16 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '16 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '16 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '16 days', 95.00, 'completed'),
(8, CURRENT_DATE - INTERVAL '16 days', 120.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '16 days', 185.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '15 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '15 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '15 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '15 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '15 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '15 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '15 days', 50.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '14 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '14 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '14 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '14 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '14 days', 95.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '14 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '14 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '13 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '13 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '13 days', 200.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '13 days', 395.00, 'completed'),
(20, CURRENT_DATE - INTERVAL '13 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '13 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '13 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '12 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '12 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '12 days', 200.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '12 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '12 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '12 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '12 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '11 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '11 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '11 days', 100.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '11 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '11 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '11 days', 120.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '11 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '10 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '10 days', 375.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '10 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '10 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '10 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '10 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '10 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '10 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '9 days', 250.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '9 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '9 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '9 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '9 days', 95.00, 'completed'),
(7, CURRENT_DATE - INTERVAL '9 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '9 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '9 days', 85.00, 'completed'),

(16, CURRENT_DATE - INTERVAL '8 days', 50.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '8 days', 75.50, 'completed'),
(1, CURRENT_DATE - INTERVAL '8 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '8 days', 95.00, 'completed'),
(16, CURRENT_DATE - INTERVAL '8 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '8 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '8 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '7 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '7 days', 175.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '7 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '7 days', 180.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '7 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '7 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '7 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '6 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '6 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '6 days', 300.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '6 days', 180.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '6 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '6 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '6 days', 85.00, 'completed'),

(2, CURRENT_DATE - INTERVAL '5 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '5 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '5 days', 80.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '5 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '5 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '5 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '5 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '4 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '4 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '4 days', 200.00, 'completed'),
(8, CURRENT_DATE - INTERVAL '4 days', 395.00, 'completed'),
(20, CURRENT_DATE - INTERVAL '4 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '4 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '4 days', 85.00, 'completed'),

(1, CURRENT_DATE - INTERVAL '3 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '3 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '3 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '3 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '3 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '3 days', 20.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '3 days', 250.00, 'completed'),

(17, CURRENT_DATE - INTERVAL '2 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '2 days', 75.50, 'completed'),
(1, CURRENT_DATE - INTERVAL '2 days', 180.00, 'completed'),
(20, CURRENT_DATE - INTERVAL '2 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '2 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '2 days', 150.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '2 days', 85.00, 'completed'),

-- Invalid order for testing
(999, CURRENT_DATE - INTERVAL '2 days', 100.00, 'completed'), -- Invalid customer_id

-- Orders with pick pattern (marketing campaign Day-1) 
(1, CURRENT_DATE - INTERVAL '1 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '1 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '1 days', 200.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '1 days', 180.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '1 days', 95.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '1 days', 220.00, 'completed'), 
(19, CURRENT_DATE - INTERVAL '1 days', 130.00, 'completed'),  
(3, CURRENT_DATE - INTERVAL '1 days', 165.00, 'completed'),
(15, CURRENT_DATE - INTERVAL '1 days', 145.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '1 days', 190.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '1 days', 220.00, 'completed'), 
(20, CURRENT_DATE - INTERVAL '1 days', 130.00, 'completed'),  
(3, CURRENT_DATE - INTERVAL '1 days', 165.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '1 days', 145.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '1 days', 190.00, 'completed'),
(18, CURRENT_DATE - INTERVAL '1 days', 220.00, 'completed'), 
(2, CURRENT_DATE - INTERVAL '1 days', 130.00, 'completed'),  
(3, CURRENT_DATE - INTERVAL '1 days', 165.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '1 days', 145.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '1 days', 190.00, 'completed'),
(7, CURRENT_DATE - INTERVAL '1 days', 220.00, 'completed'), 
(2, CURRENT_DATE - INTERVAL '1 days', 130.00, 'completed'),  
(3, CURRENT_DATE - INTERVAL '1 days', 165.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '1 days', 145.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '1 days', 190.00, 'completed');




-- Normal session data (baseline)
INSERT INTO demo.user_sessions (session_date, user_id, page_views) VALUES


-- Jour -8 (normal)
(CURRENT_DATE - INTERVAL '8 days', 1, 5),
(CURRENT_DATE - INTERVAL '8 days', 2, 3),
(CURRENT_DATE - INTERVAL '8 days', 3, 7),
(CURRENT_DATE - INTERVAL '8 days', 4, 2),


(CURRENT_DATE - INTERVAL '7 days', 1, 7),
(CURRENT_DATE - INTERVAL '7 days', 10, 8),
(CURRENT_DATE - INTERVAL '7 days', 1, 1),
(CURRENT_DATE - INTERVAL '7 days', 7, 4),

(CURRENT_DATE - INTERVAL '6 days', 8, 2),
(CURRENT_DATE - INTERVAL '6 days', 1, 1),
(CURRENT_DATE - INTERVAL '6 days', 1, 2),
(CURRENT_DATE - INTERVAL '6 days', 7, 9),
(CURRENT_DATE - INTERVAL '6 days', 6, 2),
(CURRENT_DATE - INTERVAL '6 days', 8, 1),

(CURRENT_DATE - INTERVAL '5 days', 5, 2),
(CURRENT_DATE - INTERVAL '5 days', 5, 8),
(CURRENT_DATE - INTERVAL '5 days', 3, 3),

(CURRENT_DATE - INTERVAL '4 days', 3, 2),
(CURRENT_DATE - INTERVAL '4 days', 6, 5),
(CURRENT_DATE - INTERVAL '4 days', 1, 1),
(CURRENT_DATE - INTERVAL '4 days', 6, 2),
(CURRENT_DATE - INTERVAL '4 days', 2, 1),

(CURRENT_DATE - INTERVAL '3 days', 1, 2),
(CURRENT_DATE - INTERVAL '3 days', 5, 5),
(CURRENT_DATE - INTERVAL '3 days', 8, 2),
(CURRENT_DATE - INTERVAL '3 days', 8, 8),

(CURRENT_DATE - INTERVAL '2 days', 1, 1),
(CURRENT_DATE - INTERVAL '2 days', 4, 2),
(CURRENT_DATE - INTERVAL '2 days', 1, 1),
(CURRENT_DATE - INTERVAL '2 days', 9, 12),
(CURRENT_DATE - INTERVAL '2 days', 4, 4),

(CURRENT_DATE - INTERVAL '1 days', 3, 3),
(CURRENT_DATE - INTERVAL '1 days', 1, 12),
(CURRENT_DATE - INTERVAL '1 days', 5, 5),
(CURRENT_DATE - INTERVAL '1 days', 2, 1),
(CURRENT_DATE - INTERVAL '1 days', 1, 2),

-- Anormal session data (O pages view in session)
(CURRENT_DATE - INTERVAL '1 days', 2, 100);


CREATE TABLE demo.customer_datamart AS 
    WITH mart AS (
        SELECT
            cus.customer_id
            , cus.country
            , SUM(total_amount) AS lifetime_value
            , COUNT(DISTINCT order_id) AS order_frequency
        FROM demo.customers cus 
        LEFT JOIN demo.orders ord
        ON cus.customer_id=ord.customer_id
        WHERE ord.order_date >= CURRENT_DATE - INTERVAL '90 days' 
        GROUP BY 1, 2
    )

    SELECT
        customer_id
        , country
        , lifetime_value
        , order_frequency
        , CASE 
            WHEN order_frequency = 1 THEN 'Mono-buyer'
            WHEN order_frequency < 20 THEN 'Regular-buyer'
            WHEN order_frequency >= 20 THEN 'VIP-buyer'
            ELSE 'Not-segmented'
        END AS customer_segment
    FROM mart
;