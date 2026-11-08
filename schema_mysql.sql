-- =============================================================================
-- Book Store Management System - MySQL Database Schema

-- =============================================================================

CREATE DATABASE IF NOT EXISTS `bookstore_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `bookstore_db`;

-- 1. Users Table (Role-based access: admin, manager, staff, customer)
DROP TABLE IF EXISTS `book_returns`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `books`;
DROP TABLE IF EXISTS `suppliers`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(80) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('admin', 'manager', 'staff', 'customer') DEFAULT 'customer' NOT NULL,
    `phone` VARCHAR(20) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Categories Table
CREATE TABLE `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT DEFAULT NULL
) ENGINE=InnoDB;

-- 3. Suppliers Table
CREATE TABLE `suppliers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL UNIQUE,
    `contact_person` VARCHAR(100) DEFAULT NULL,
    `email` VARCHAR(120) DEFAULT NULL,
    `phone` VARCHAR(30) DEFAULT NULL,
    `address` TEXT DEFAULT NULL
) ENGINE=InnoDB;

-- 4. Books Inventory Table
CREATE TABLE `books` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `author` VARCHAR(200) NOT NULL,
    `category_id` INT NOT NULL,
    `supplier_id` INT DEFAULT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `stock` INT DEFAULT 0 NOT NULL,
    `min_stock_alert` INT DEFAULT 10 NOT NULL,
    `description` TEXT DEFAULT NULL,
    `image_url` VARCHAR(500) DEFAULT NULL,
    `rating` DECIMAL(2, 1) DEFAULT 4.8,
    `reviews_count` INT DEFAULT 42,
    CONSTRAINT `fk_books_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_books_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 5. Orders / Sales Transactions Table
-- Section 4.3 Formulation: Net Amount = (Price x Quantity) - Discount + Tax
CREATE TABLE `orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `invoice_no` VARCHAR(50) NOT NULL UNIQUE,
    `customer_id` INT DEFAULT NULL,
    `customer_name` VARCHAR(100) NOT NULL,
    `customer_phone` VARCHAR(30) DEFAULT NULL,
    `staff_id` INT DEFAULT NULL,
    `subtotal` DECIMAL(10, 2) NOT NULL,
    `discount_pct` DECIMAL(5, 2) DEFAULT 0.00,
    `discount_amount` DECIMAL(10, 2) DEFAULT 0.00,
    `tax_amount` DECIMAL(10, 2) DEFAULT 0.00,
    `net_amount` DECIMAL(10, 2) NOT NULL,
    `payment_method` VARCHAR(50) DEFAULT 'Cash',
    `status` ENUM('Completed', 'Partially Returned', 'Returned') DEFAULT 'Completed',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_orders_staff` FOREIGN KEY (`staff_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 6. Order Items Table
CREATE TABLE `order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `book_id` INT NOT NULL,
    `book_title` VARCHAR(200) NOT NULL,
    `unit_price` DECIMAL(10, 2) NOT NULL,
    `quantity` INT NOT NULL,
    `subtotal` DECIMAL(10, 2) NOT NULL,
    `returned_quantity` INT DEFAULT 0,
    CONSTRAINT `fk_items_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_items_book` FOREIGN KEY (`book_id`) REFERENCES `books` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 7. Book Returns Table (Process Returns Module)
CREATE TABLE `book_returns` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `order_item_id` INT NOT NULL,
    `book_id` INT NOT NULL,
    `quantity` INT NOT NULL,
    `refund_amount` DECIMAL(10, 2) NOT NULL,
    `reason` VARCHAR(255) NOT NULL,
    `processed_by` VARCHAR(80) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_returns_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_returns_item` FOREIGN KEY (`order_item_id`) REFERENCES `order_items` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_returns_book` FOREIGN KEY (`book_id`) REFERENCES `books` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- =============================================================================
-- Initial Sample Seed Data
-- =============================================================================

-- Seed Categories
INSERT INTO `categories` (`id`, `name`, `description`) VALUES
(1, 'Engineering', 'Software, Electrical, and Mechanical Engineering textbooks'),
(2, 'Programming', 'Coding, Clean Architecture, and software languages'),
(3, 'Computer Science', 'Artificial Intelligence, Operating Systems, and Theory'),
(4, 'Algorithms', 'Data Structures, Competitive Programming, and Complexity'),
(5, 'Database', 'Relational, NoSQL, SQL, and distributed data systems'),
(6, 'Self-Help', 'Personal productivity, habit-building, and mindfulness'),
(7, 'Finance', 'Personal finance, investment principles, and economics');

-- Seed Suppliers
INSERT INTO `suppliers` (`id`, `name`, `contact_person`, `email`, `phone`, `address`) VALUES
(1, 'Pearson Education', 'John Doe', 'contact@pearson.com', '+91-9876543210', 'Tech Park, New Delhi'),
(2, 'McGraw-Hill Education', 'Jane Smith', 'orders@mcgrawhill.com', '+91-9876543211', 'Industrial Area, Mumbai'),
(3, 'O\'Reilly Media', 'Robert Lang', 'sales@oreilly.com', '+1-800-998-9938', 'Sebastopol, CA, USA'),
(4, 'Oxford University Press', 'David Brown', 'support@oup.org', '+91-11-23456789', 'YMCA Building, New Delhi');

-- Seed Books
INSERT INTO `books` (`id`, `title`, `author`, `category_id`, `supplier_id`, `price`, `stock`, `min_stock_alert`, `description`, `image_url`) VALUES
(1, 'Software Engineering: A Practitioner\'s Approach', 'Roger S. Pressman', 1, 2, 500.00, 18, 10, 'Comprehensive guide covering agile development, software architecture, and QA.', 'https://images.unsplash.com/photo-1532012164546-f432f2e3777a?auto=format&fit=crop&w=700&q=80'),
(2, 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 2, 1, 650.00, 25, 8, 'Master formatting, refactoring, and clean software architecture.', 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=700&q=80'),
(3, 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Erich Gamma, Richard Helm', 1, 1, 720.00, 12, 5, 'Catalog of 23 timeless architectural solutions.', 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=700&q=80'),
(4, 'Artificial Intelligence: A Modern Approach', 'Stuart Russell, Peter Norvig', 3, 1, 850.00, 15, 5, 'The definitive textbook exploring intelligent agents and deep learning.', 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=700&q=80'),
(5, 'Atomic Habits: An Easy & Proven Way to Build Good Habits', 'James Clear', 6, 3, 450.00, 30, 10, 'Transform your daily routines with remarkable atomic changes.', 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=700&q=80'),
(6, 'Database System Concepts', 'Abraham Silberschatz, Henry F. Korth', 5, 2, 580.00, 6, 10, 'Fundamental concepts of database management, SQL, and storage engines.', 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=700&q=80');
