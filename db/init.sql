-- =====================================================
-- CMPE341 Project - Group 7: Product Management System
-- PostgreSQL schema + sample data
-- Runs automatically on first start of the db container
-- =====================================================

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS supplier;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS users;

-- 1. USERS (login + roles)
CREATE TABLE users (
    user_id        SERIAL PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    role           VARCHAR(20)  NOT NULL CHECK (role IN ('admin', 'staff'))
);

-- 2. CATEGORY
CREATE TABLE category (
    category_id  SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL UNIQUE,
    description  VARCHAR(255)
);

-- 3. SUPPLIER
CREATE TABLE supplier (
    supplier_id  SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    phone        VARCHAR(20),
    email        VARCHAR(100) UNIQUE
);

-- 4. PRODUCT
CREATE TABLE product (
    product_id   SERIAL PRIMARY KEY,
    name         VARCHAR(100)  NOT NULL,
    price        DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock        INT           NOT NULL DEFAULT 0 CHECK (stock >= 0),
    category_id  INT NOT NULL REFERENCES category(category_id) ON DELETE RESTRICT,
    supplier_id  INT NOT NULL REFERENCES supplier(supplier_id) ON DELETE RESTRICT
);

-- 5. ORDERS
CREATE TABLE orders (
    order_id       SERIAL PRIMARY KEY,
    product_id     INT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    user_id        INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    customer_name  VARCHAR(100) NOT NULL,
    quantity       INT  NOT NULL CHECK (quantity > 0),
    order_date     DATE NOT NULL DEFAULT CURRENT_DATE
);

-- ===================== SAMPLE DATA =====================
-- Scenario: NetPoint, a small IT & network equipment shop in Ankara
-- Test passwords: admin/admin123, elif.sales/staff123, kerem.depot/staff456 (stored hashed)
INSERT INTO users (username, password_hash, role) VALUES
('admin',       'pbkdf2:sha256:1000000$9rpL7kit71izkRy8$cc4efb76414f146e16ae4fd646459949d9f4285d3c4af29ac19ebe5d1294a1be', 'admin'),
('elif.sales',  'pbkdf2:sha256:1000000$Y7uhe8GJJ1E1xo98$17de73c785ddaff9c71fd93ca7cc6bb8c6892318b9119ba19dea18fb1fc69c1c', 'staff'),
('kerem.depot', 'pbkdf2:sha256:1000000$fjjc1uXF3GTUFdqG$2894bff28f72927a703e9afdf3f86d2a6861269f4a93d3f745ee91cc2fc653dc', 'staff');

INSERT INTO category (name, description) VALUES
('Switching',      'Managed and unmanaged Ethernet switches'),
('Wireless',       'Access points and Wi-Fi routers'),
('Security',       'Firewalls and IP cameras'),
('Cabling',        'Patch cables, keystones and patch panels'),
('Rack & Power',   'Cabinets and UPS units');

INSERT INTO supplier (name, phone, email) VALUES
('Baskent Bilisim Dagitim',  '+90 312 418 22 40', 'siparis@baskentbilisim.example'),
('Ostim Kablo Sanayi',       '+90 312 385 61 17', 'satis@ostimkablo.example'),
('Ege Network Tedarik',      '+90 232 462 90 05', 'info@egenetwork.example');

INSERT INTO product (name, price, stock, category_id, supplier_id) VALUES
('Cisco Catalyst 1000-24T Switch',   38500.00,   6, 1, 1),
('TP-Link TL-SG108 8-Port Switch',     1450.00,  40, 1, 3),
('MikroTik CRS326-24G Switch',        12900.00,   9, 1, 3),
('Ubiquiti UniFi U6 Lite AP',          5200.00,  18, 2, 3),
('TP-Link Archer AX55 Router',         3650.00,  25, 2, 1),
('Fortinet FortiGate 40F Firewall',   27800.00,   4, 3, 1),
('Hikvision 4MP Dome IP Camera',       2950.00,  30, 3, 3),
('Cat6 UTP Patch Cable 2m',              85.00, 500, 4, 2),
('24-Port Cat6 Patch Panel',           1750.00,  22, 4, 2),
('APC Back-UPS 1500VA',                9400.00,   0, 5, 1);

INSERT INTO orders (product_id, user_id, customer_name, quantity, order_date) VALUES
(2, 2, 'Cankaya Dis Klinigi',         2,  '2026-11-03'),
(8, 2, 'Cankaya Dis Klinigi',        40,  '2026-11-03'),
(4, 3, 'Bahcelievler Kafe Kahve',     3,  '2026-11-06'),
(7, 3, 'Ulus Eczanesi',               4,  '2026-11-09'),
(1, 1, 'Etimesgut Lojistik A.S.',     1,  '2026-11-12'),
(6, 1, 'Etimesgut Lojistik A.S.',     1,  '2026-11-12'),
(9, 2, 'Kizilay Mimarlik Ofisi',      1,  '2026-11-15'),
(8, 3, 'Kizilay Mimarlik Ofisi',     24,  '2026-11-15');
