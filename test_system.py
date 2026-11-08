"""
Automated Test Suite for Book Store Management System


Explicitly tests all 10 Test Cases from Section 5 of the Project Specification:
- TC01: Enter valid username/password -> Login successful
- TC02: Enter invalid password -> Error message
- TC03: Add book -> Book added
- TC04: Search book by title -> Matching books displayed
- TC05: Add book to cart -> Cart updated
- TC06: Generate bill -> Correct total displayed
- TC07: Complete a sale -> Stock reduced
- TC08: Sell more than available stock -> Error message
- TC09: Generate sales report -> Report displayed
- TC10: Unauthorized user accesses page -> Access denied
"""

import unittest
from app import app, db, User, Book, Category, Order, OrderItem

class BookStoreTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            # Ensure tables exist
            db.create_all()

            # Ensure Test Users exist
            if not User.query.filter_by(username='admin_test').first():
                admin = User(username='admin_test', email='admin@test.com', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)

            if not User.query.filter_by(username='mgr_test').first():
                manager = User(username='mgr_test', email='mgr@test.com', role='manager')
                manager.set_password('manager123')
                db.session.add(manager)

            if not User.query.filter_by(username='staff_test').first():
                staff = User(username='staff_test', email='staff@test.com', role='staff')
                staff.set_password('staff123')
                db.session.add(staff)

            if not User.query.filter_by(username='cust_test').first():
                customer = User(username='cust_test', email='cust@test.com', role='customer')
                customer.set_password('cust123')
                db.session.add(customer)

            # Ensure Category exists
            cat = Category.query.filter_by(name='Engineering').first()
            if not cat:
                cat = Category(name='Engineering', description='Tech books')
                db.session.add(cat)
                db.session.flush()

            # Ensure Sample Book exists
            book = Book.query.filter_by(title="Software Engineering: A Practitioner's Approach").first()
            if not book:
                book = Book(
                    title="Software Engineering: A Practitioner's Approach",
                    author="Roger S. Pressman",
                    category_id=cat.id,
                    price=500.0,
                    stock=18,
                    min_stock_alert=10
                )
                db.session.add(book)

            db.session.commit()

    def tearDown(self):
        # Clear test cart / session
        with self.client.session_transaction() as sess:
            sess.clear()

    # -------------------------------------------------------------------------
    # TC01: Enter valid username/password -> Login successful
    # -------------------------------------------------------------------------
    def test_tc01_valid_login(self):
        response = self.client.post('/login', data={
            'username': 'admin_test',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
        print("\n[PASS] TC01: Enter valid username/password -> Login successful")

    # -------------------------------------------------------------------------
    # TC02: Enter invalid password -> Error message
    # -------------------------------------------------------------------------
    def test_tc02_invalid_login(self):
        response = self.client.post('/login', data={
            'username': 'admin_test',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)
        print("[PASS] TC02: Enter invalid password -> Error message")

    # -------------------------------------------------------------------------
    # TC03: Add book -> Book added
    # -------------------------------------------------------------------------
    def test_tc03_add_book(self):
        # Login as Admin
        self.client.post('/login', data={'username': 'admin_test', 'password': 'admin123'})
        with app.app_context():
            cat = Category.query.first()
            cat_id = cat.id

        response = self.client.post('/admin/add', data={
            'title': 'Test Driven Development Practice',
            'author': 'Kent Beck',
            'category_id': cat_id,
            'supplier_id': 0,
            'price': 420.0,
            'stock': 15,
            'min_stock_alert': 5,
            'description': 'By example'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            new_book = Book.query.filter_by(title='Test Driven Development Practice').first()
            self.assertIsNotNone(new_book)
            self.assertEqual(new_book.price, 420.0)
        print("[PASS] TC03: Add book -> Book added successfully")

    # -------------------------------------------------------------------------
    # TC04: Search book by title -> Matching books displayed
    # -------------------------------------------------------------------------
    def test_tc04_search_book(self):
        response = self.client.get('/?q=Software+Engineering')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Software Engineering', response.data)
        self.assertIn(b'Roger S. Pressman', response.data)
        print("[PASS] TC04: Search book by title -> Matching books displayed")

    # -------------------------------------------------------------------------
    # TC05: Add book to cart -> Cart updated
    # -------------------------------------------------------------------------
    def test_tc05_add_to_cart(self):
        with app.app_context():
            book = Book.query.filter_by(title="Software Engineering: A Practitioner's Approach").first()
            book_id = book.id

        response = self.client.post(f'/book/{book_id}', data={'quantity': 2}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertIn('cart', sess)
            self.assertEqual(sess['cart'].get(str(book_id)), 2)
        print("[PASS] TC05: Add book to cart -> Cart updated")

    # -------------------------------------------------------------------------
    # TC06: Generate bill -> Correct total displayed
    # Formula: Net Amount = (Price x Quantity) - Discount + Tax
    # 2 copies @ 500 = 1000. Discount (5% on >= 1000) = 50. Tax 5% of 950 = 47.5. Total = 997.50
    # -------------------------------------------------------------------------
    def test_tc06_generate_bill_calculation(self):
        with app.app_context():
            book = Book.query.filter_by(title="Software Engineering: A Practitioner's Approach").first()
            book_id = book.id

        with self.client.session_transaction() as sess:
            sess['cart'] = {str(book_id): 2}

        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'997.50', response.data)  # Net Amount calculation check
        print("[PASS] TC06: Generate bill -> Correct total calculated via formula")

    # -------------------------------------------------------------------------
    # TC07: Complete a sale -> Stock reduced
    # -------------------------------------------------------------------------
    def test_tc07_complete_sale_stock_reduced(self):
        # Login as customer
        self.client.post('/login', data={'username': 'cust_test', 'password': 'cust123'})
        with app.app_context():
            book = Book.query.filter_by(title="Software Engineering: A Practitioner's Approach").first()
            initial_stock = book.stock
            book_id = book.id

        # Add 2 copies to cart
        with self.client.session_transaction() as sess:
            sess['cart'] = {str(book_id): 2}

        # Complete sale
        response = self.client.post('/cart', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with app.app_context():
            updated_book = Book.query.get(book_id)
            self.assertEqual(updated_book.stock, initial_stock - 2)
        print("[PASS] TC07: Complete a sale -> Stock reduced and invoice saved")

    # -------------------------------------------------------------------------
    # TC08: Sell more than available stock -> Error message
    # -------------------------------------------------------------------------
    def test_tc08_sell_more_than_stock_error(self):
        with app.app_context():
            book = Book.query.filter_by(title="Software Engineering: A Practitioner's Approach").first()
            book_id = book.id
            avail = book.stock

        # Try adding avail + 50 copies
        response = self.client.post(f'/book/{book_id}', data={'quantity': avail + 50}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'copies available in stock', response.data)
        print("[PASS] TC08: Sell more than available stock -> Error message prevented oversell")

    # -------------------------------------------------------------------------
    # TC09: Generate sales report -> Report displayed
    # -------------------------------------------------------------------------
    def test_tc09_generate_sales_report(self):
        # Login as Store Manager
        self.client.post('/login', data={'username': 'mgr_test', 'password': 'manager123'})
        response = self.client.get('/manager/reports')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Net Revenue', response.data)
        self.assertIn(b'Top-Selling Books', response.data)
        print("[PASS] TC09: Generate sales report -> Report displayed")

    # -------------------------------------------------------------------------
    # TC10: Unauthorized user accesses page -> Access denied
    # Customer tries to access admin-only /admin
    # -------------------------------------------------------------------------
    def test_tc10_unauthorized_access_denied(self):
        # Login as Customer
        self.client.post('/login', data={'username': 'cust_test', 'password': 'cust123'})
        response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Access denied', response.data)
        print("[PASS] TC10: Unauthorized user accesses page -> Access denied")

if __name__ == '__main__':
    print("=" * 70)
    print("Running Book Store Management System Test Suite (Batch-12)")
    print("Test Cases TC01 through TC10 Verification")
    print("=" * 70)
    unittest.main()
