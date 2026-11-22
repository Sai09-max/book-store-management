"""
Book Store Management System - Full Implementation


Modules Implemented:
1. Communication & Stakeholder Role-based Access (Admin, Store Manager, Sales Staff, Customer)
2. Book Management (CRUD, Availability, Search by Title/Author/Category)
3. Category & Supplier Management
4. Customer Management & Order History
5. Cart & POS Billing (Net Amount = (Price x Quantity) - Discount + Tax)
6. Stock Tracking & Low-Stock Alerts
7. Book Returns Processing & Automatic Inventory Restoration
8. Comprehensive Sales Reports Generation
"""

import os
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, flash, request, session, abort
)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash

from forms import (
    RegisterForm, LoginForm, BookForm, CategoryForm, SupplierForm,
    StaffCreateForm, CartAddForm, POSCheckoutForm, ReturnForm
)

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------------------------------------------------------------------
# Role-based Access Control Helpers
# ---------------------------------------------------------------------------
def role_required(*allowed_roles):
    """Decorator to enforce role-based access control for specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles:
                flash('Access denied. You do not have permission to view that resource.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ---------------------------------------------------------------------------
# Database Models
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer', nullable=False)  # admin, manager, staff, customer
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role in ('admin', 'manager')

    @property
    def is_staff(self):
        return self.role in ('admin', 'manager', 'staff')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    books = db.relationship('Book', backref='category_rel', lazy=True, cascade='all, delete-orphan')


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    books = db.relationship('Book', backref='supplier_rel', lazy=True)


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    min_stock_alert = db.Column(db.Integer, default=10, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.Float, default=4.8)
    reviews_count = db.Column(db.Integer, default=42)

    @property
    def is_available(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.min_stock_alert


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    subtotal = db.Column(db.Float, nullable=False)
    discount_pct = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='Cash')
    status = db.Column(db.String(30), default='Completed')  # Completed, Partially Returned, Returned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('User', foreign_keys=[customer_id], backref='customer_orders')
    staff = db.relationship('User', foreign_keys=[staff_id], backref='staff_orders')
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('BookReturn', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    book_title = db.Column(db.String(200), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    returned_quantity = db.Column(db.Integer, default=0)

    book = db.relationship('Book')

    @property
    def remaining_returnable(self):
        return self.quantity - self.returned_quantity


class BookReturn(db.Model):
    __tablename__ = 'book_returns'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    refund_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    processed_by = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_item = db.relationship('OrderItem', backref='return_logs')
    book = db.relationship('Book')


# ---------------------------------------------------------------------------
# Login Manager Loader
# ---------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Database Seeding & Setup
# ---------------------------------------------------------------------------
def init_db():
    """Initializes tables and populates default categories, suppliers, books, and accounts."""
    db.create_all()

    # 1. Seed Roles & Default Accounts
    default_users = [
        ('admin', 'admin@bookstore.com', 'admin123', 'admin'),
        ('staff1', 'staff1@bookstore.com', 'staff123', 'staff'),
        ('staff2', 'staff2@bookstore.com', 'staff123', 'staff'),
        ('staff3', 'staff3@bookstore.com', 'staff123', 'staff'),
    ]
    for uname, email, pwd, role in default_users:
        user = User.query.filter_by(username=uname).first()
        if not user:
            user = User(username=uname, email=email, role=role)
            user.set_password(pwd)
            db.session.add(user)

    db.session.commit()

    # 2. Seed Categories
    category_names = [
        ("Engineering", "Software, Electrical, and Mechanical Engineering textbooks"),
        ("Programming", "Coding, Clean Architecture, and software languages"),
        ("Computer Science", "Artificial Intelligence, Operating Systems, and Theory"),
        ("Algorithms", "Data Structures, Competitive Programming, and Complexity"),
        ("Database", "Relational, NoSQL, SQL, and distributed data systems"),
        ("Self-Help", "Personal productivity, habit-building, and mindfulness"),
        ("Finance", "Personal finance, investment principles, and economics")
    ]
    for cat_name, cat_desc in category_names:
        if not Category.query.filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name, description=cat_desc))

    # 3. Seed Suppliers
    sample_suppliers = [
        ("Pearson Education", "John Doe", "contact@pearson.com", "+91-9876543210", "Tech Park, New Delhi"),
        ("McGraw-Hill Education", "Jane Smith", "orders@mcgrawhill.com", "+91-9876543211", "Industrial Area, Mumbai"),
        ("O'Reilly Media", "Robert Lang", "sales@oreilly.com", "+1-800-998-9938", "Sebastopol, CA, USA"),
        ("Oxford University Press", "David Brown", "support@oup.org", "+91-11-23456789", "YMCA Building, New Delhi")
    ]
    for s_name, s_contact, s_email, s_phone, s_addr in sample_suppliers:
        if not Supplier.query.filter_by(name=s_name).first():
            db.session.add(Supplier(
                name=s_name, contact_person=s_contact, email=s_email, phone=s_phone, address=s_addr
            ))

    db.session.commit()

    # 4. Seed Books
    c_eng = Category.query.filter_by(name="Engineering").first()
    c_prog = Category.query.filter_by(name="Programming").first()
    c_cs = Category.query.filter_by(name="Computer Science").first()
    c_algo = Category.query.filter_by(name="Algorithms").first()
    c_db = Category.query.filter_by(name="Database").first()
    c_self = Category.query.filter_by(name="Self-Help").first()
    c_fin = Category.query.filter_by(name="Finance").first()

    s_pearson = Supplier.query.filter_by(name="Pearson Education").first()
    s_mcgraw = Supplier.query.filter_by(name="McGraw-Hill Education").first()
    s_oreilly = Supplier.query.filter_by(name="O'Reilly Media").first()
    s_oxford = Supplier.query.filter_by(name="Oxford University Press").first()

    catalog_books = [
        # Original core collection
        {
            "title": "Software Engineering: A Practitioner's Approach",
            "author": "Roger S. Pressman",
            "category_id": c_eng.id if c_eng else 1,
            "supplier_id": s_mcgraw.id if s_mcgraw else None,
            "price": 500.0,
            "stock": 18,
            "min_stock_alert": 10,
            "rating": 4.9,
            "reviews_count": 128,
            "description": "Comprehensive guide covering agile development, software architecture, quality assurance, requirement gathering, and cost estimation.",
            "image_url": "https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/books/1387717052i/142783.jpg"
        },
        {
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "author": "Robert C. Martin",
            "category_id": c_prog.id if c_prog else 2,
            "supplier_id": s_pearson.id if s_pearson else None,
            "price": 650.0,
            "stock": 25,
            "min_stock_alert": 8,
            "rating": 4.8,
            "reviews_count": 94,
            "description": "Even bad code can function. But if code isn't clean, it can bring a development team to its knees. Master formatting, refactoring, and clean design.",
            "image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Design Patterns: Elements of Reusable Object-Oriented Software",
            "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
            "category_id": c_eng.id if c_eng else 1,
            "supplier_id": s_pearson.id if s_pearson else None,
            "price": 720.0,
            "stock": 12,
            "min_stock_alert": 5,
            "rating": 4.9,
            "reviews_count": 86,
            "description": "Capturing a wealth of experience about the design of object-oriented software, four top-notch designers present a catalog of timeless architectural solutions.",
            "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Artificial Intelligence: A Modern Approach",
            "author": "Stuart Russell, Peter Norvig",
            "category_id": c_cs.id if c_cs else 3,
            "supplier_id": s_pearson.id if s_pearson else None,
            "price": 850.0,
            "stock": 15,
            "min_stock_alert": 5,
            "rating": 4.9,
            "reviews_count": 110,
            "description": "The definitive textbook on AI, exploring intelligent agents, heuristic search, logic, probabilistic reasoning, and modern deep learning foundations.",
            "image_url": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Atomic Habits: An Easy & Proven Way to Build Good Habits",
            "author": "James Clear",
            "category_id": c_self.id if c_self else 6,
            "supplier_id": s_oreilly.id if s_oreilly else None,
            "price": 450.0,
            "stock": 30,
            "min_stock_alert": 10,
            "rating": 4.9,
            "reviews_count": 350,
            "description": "An easy and proven way to build good habits and break bad ones. Transform your daily routines with remarkable atomic changes.",
            "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Database System Concepts",
            "author": "Abraham Silberschatz, Henry F. Korth",
            "category_id": c_db.id if c_db else 5,
            "supplier_id": s_mcgraw.id if s_mcgraw else None,
            "price": 580.0,
            "stock": 6,
            "min_stock_alert": 10,
            "rating": 4.7,
            "reviews_count": 73,
            "description": "Fundamental concepts of database management, SQL, relational calculus, transaction processing, indexing, and storage engines.",
            "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Introduction to Algorithms (CLRS)",
            "author": "Thomas H. Cormen, Charles E. Leiserson",
            "category_id": c_algo.id if c_algo else 4,
            "supplier_id": s_pearson.id if s_pearson else None,
            "price": 950.0,
            "stock": 4,
            "min_stock_alert": 5,
            "rating": 4.9,
            "reviews_count": 215,
            "description": "Comprehensive textbook covering a broad spectrum of algorithms in depth, asymptotic analysis, dynamic programming, and greedy methods.",
            "image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "The Psychology of Money",
            "author": "Morgan Housel",
            "category_id": c_fin.id if c_fin else 7,
            "supplier_id": s_oreilly.id if s_oreilly else None,
            "price": 399.0,
            "stock": 22,
            "min_stock_alert": 8,
            "rating": 4.8,
            "reviews_count": 180,
            "description": "Timeless lessons on wealth, greed, and happiness. Doing well with money isn't necessarily about what you know, but how you behave.",
            "image_url": "https://images.unsplash.com/photo-1553729459-efe14ef6055d?auto=format&fit=crop&w=700&q=80"
        },

        # Newly added books with curated high-res covers
        {
            "title": "The Pragmatic Programmer: Your Journey to Mastery",
            "author": "David Thomas, Andrew Hunt",
            "category_id": c_prog.id if c_prog else 2,
            "supplier_id": s_pearson.id if s_pearson else None,
            "price": 680.0,
            "stock": 16,
            "min_stock_alert": 6,
            "rating": 4.9,
            "reviews_count": 142,
            "description": "One of the most significant books in computer programming. Fresh advice on career paths, software architecture, refactoring, and personal development.",
            "image_url": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Grokking Algorithms: An Illustrated Guide",
            "author": "Aditya Y. Bhargava",
            "category_id": c_algo.id if c_algo else 4,
            "supplier_id": s_oreilly.id if s_oreilly else None,
            "price": 520.0,
            "stock": 20,
            "min_stock_alert": 7,
            "rating": 4.8,
            "reviews_count": 230,
            "description": "A friendly, fully illustrated guide that teaches you how to apply common algorithms to practical programming problems with visual breakdowns.",
            "image_url": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Designing Data-Intensive Applications",
            "author": "Martin Kleppmann",
            "category_id": c_db.id if c_db else 5,
            "supplier_id": s_oreilly.id if s_oreilly else None,
            "price": 890.0,
            "stock": 14,
            "min_stock_alert": 5,
            "rating": 4.9,
            "reviews_count": 310,
            "description": "The definitive guide to distributed architectures, replication, partitioning, stream processing, consistency, and scalable cloud databases.",
            "image_url": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Computer Networking: A Top-Down Approach",
            "author": "James Kurose, Keith Ross",
            "category_id": c_cs.id if c_cs else 3,
            "supplier_id": s_pearson.id if s_pearson else None,
            "price": 790.0,
            "stock": 11,
            "min_stock_alert": 6,
            "rating": 4.7,
            "reviews_count": 88,
            "description": "Focuses on internet protocols, application layers, routing, wireless networks, network security, and modern cloud transport layers.",
            "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Deep Learning",
            "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
            "category_id": c_cs.id if c_cs else 3,
            "supplier_id": s_oxford.id if s_oxford else None,
            "price": 999.0,
            "stock": 8,
            "min_stock_alert": 4,
            "rating": 4.9,
            "reviews_count": 165,
            "description": "An essential mathematical and conceptual text covering neural networks, optimization algorithms, autoencoders, computer vision, and NLP.",
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Refactoring: Improving the Design of Existing Code",
            "author": "Martin Fowler",
            "category_id": c_prog.id if c_prog else 2,
            "supplier_id": s_pearson.id if s_pearson else None,
            "price": 740.0,
            "stock": 19,
            "min_stock_alert": 5,
            "rating": 4.8,
            "reviews_count": 78,
            "description": "Learn how to systematically refactor legacy codebases safely with unit tests, clean abstractions, and proven architectural principles.",
            "image_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Zero to One: Notes on Startups",
            "author": "Peter Thiel, Blake Masters",
            "category_id": c_fin.id if c_fin else 7,
            "supplier_id": s_mcgraw.id if s_mcgraw else None,
            "price": 420.0,
            "stock": 28,
            "min_stock_alert": 10,
            "rating": 4.7,
            "reviews_count": 195,
            "description": "How to build companies that create entirely new things. The secrets of monopolistic innovation, vertical growth, and visionary technology.",
            "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=700&q=80"
        },
        {
            "title": "Deep Work: Rules for Focused Success in a Distracted World",
            "author": "Cal Newport",
            "category_id": c_self.id if c_self else 6,
            "supplier_id": s_oxford.id if s_oxford else None,
            "price": 460.0,
            "stock": 24,
            "min_stock_alert": 8,
            "rating": 4.8,
            "reviews_count": 210,
            "description": "Master the superpower of distraction-free concentration to produce elite results, sharpen skills, and achieve genuine fulfillment.",
            "image_url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=700&q=80"
        }
    ]

    for b_item in catalog_books:
        existing = Book.query.filter_by(title=b_item["title"]).first()
        if not existing:
            db.session.add(Book(**b_item))
        else:
            # Sync cover image URL if it changed or was empty
            if existing.image_url != b_item["image_url"] and (not existing.image_url or existing.image_url.startswith('http') or existing.image_url.startswith('/static/uploads/-resized')):
                existing.image_url = b_item["image_url"]

    db.session.commit()

    # 5. Seed Initial Sample Orders for Reports if none exist
    if Order.query.count() == 0:
        customer_user = User.query.filter_by(username='customer').first()
        staff_user = User.query.filter_by(username='staff').first()
        book1 = Book.query.filter_by(title="Software Engineering: A Practitioner's Approach").first()
        book2 = Book.query.filter_by(title="Clean Code: A Handbook of Agile Software Craftsmanship").first()

        if book1 and book2:
            # Order 1 (Sample Completed Sale)
            subtot = (book1.price * 2)  # 1000
            disc = 50.0  # 5%
            tax = (subtot - disc) * 0.05  # 47.5
            net = (subtot - disc) + tax  # 997.5

            o1 = Order(
                invoice_no="INV-20261107-1001",
                customer_id=customer_user.id if customer_user else None,
                customer_name="Alice Johnson",
                customer_phone="+91-9876541122",
                staff_id=staff_user.id if staff_user else None,
                subtotal=subtot,
                discount_pct=5.0,
                discount_amount=disc,
                tax_amount=tax,
                net_amount=net,
                payment_method="Cash",
                status="Completed",
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(o1)
            db.session.flush()

            item1 = OrderItem(
                order_id=o1.id,
                book_id=book1.id,
                book_title=book1.title,
                unit_price=book1.price,
                quantity=2,
                subtotal=1000.0,
                returned_quantity=0
            )
            db.session.add(item1)

            # Order 2
            subtot2 = book2.price * 1  # 650
            disc2 = 0.0
            tax2 = subtot2 * 0.05  # 32.5
            net2 = subtot2 + tax2  # 682.5

            o2 = Order(
                invoice_no="INV-20261107-1002",
                customer_id=customer_user.id if customer_user else None,
                customer_name="Bob Smith",
                customer_phone="+91-9876543344",
                staff_id=staff_user.id if staff_user else None,
                subtotal=subtot2,
                discount_pct=0.0,
                discount_amount=disc2,
                tax_amount=tax2,
                net_amount=net2,
                payment_method="UPI",
                status="Completed",
                created_at=datetime.utcnow()
            )
            db.session.add(o2)
            db.session.flush()

            item2 = OrderItem(
                order_id=o2.id,
                book_id=book2.id,
                book_title=book2.title,
                unit_price=book2.price,
                quantity=1,
                subtotal=650.0,
                returned_quantity=0
            )
            db.session.add(item2)
            db.session.commit()


# ---------------------------------------------------------------------------
# General & Customer Routes
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    sort = request.args.get('sort', 'popular').strip()
    stock_filter = request.args.get('stock', '').strip()

    books_query = Book.query

    if query:
        books_query = books_query.filter(
            (Book.title.ilike(f'%{query}%')) |
            (Book.author.ilike(f'%{query}%'))
        )

    if category_id:
        books_query = books_query.filter(Book.category_id == category_id)

    if stock_filter == 'available':
        books_query = books_query.filter(Book.stock > 0)
    elif stock_filter == 'low':
        books_query = books_query.filter(Book.stock <= Book.min_stock_alert, Book.stock > 0)

    if sort == 'price_asc':
        books_query = books_query.order_by(Book.price.asc())
    elif sort == 'price_desc':
        books_query = books_query.order_by(Book.price.desc())
    elif sort == 'name_asc':
        books_query = books_query.order_by(Book.title.asc())
    else:
        books_query = books_query.order_by(Book.id.asc())

    books = books_query.all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'index.html',
        books=books,
        query=query,
        categories=categories,
        selected_category=category_id,
        current_sort=sort,
        stock_filter=stock_filter,
        total_count=len(books)
    )


@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    form = CartAddForm()
    if form.validate_on_submit():
        qty = form.quantity.data
        if qty <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(url_for('book_detail', book_id=book.id))
        if qty > book.stock:
            flash(f'Sorry! Only {book.stock} copies available in stock.', 'danger')
            return redirect(url_for('book_detail', book_id=book.id))
        cart = session.get('cart', {})
        current_cart_qty = cart.get(str(book.id), 0)
        if current_cart_qty + qty > book.stock:
            flash(f'Cannot add {qty} more. You already have {current_cart_qty} in cart and only {book.stock} are in stock.', 'warning')
            return redirect(url_for('book_detail', book_id=book.id))
        cart[str(book.id)] = current_cart_qty + qty
        session['cart'] = cart
        session.modified = True
        flash(f'Added {qty} copy/copies of "{book.title}" to cart.', 'success')
        return redirect(url_for('cart'))
    return render_template('book_detail.html', book=book, form=form)


# ---------------------------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=form.email.data).first():
            flash('Email is already registered. Please login.', 'warning')
            return redirect(url_for('login'))
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.username}! ({user.role.capitalize()} role active)', 'success')
            # Route by role appropriately
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'manager':
                return redirect(url_for('manager_reports'))
            elif user.role == 'staff':
                return redirect(url_for('staff_pos'))
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Cart & Customer Checkout
# ---------------------------------------------------------------------------
def get_cart():
    return session.get('cart', {})

def save_cart(cart):
    session['cart'] = cart
    session.modified = True

@app.route('/cart/quick-add/<int:book_id>', methods=['POST'])
def quick_add(book_id):
    book = Book.query.get_or_404(book_id)
    if book.stock <= 0:
        flash('Sorry, this book is currently out of stock.', 'danger')
        return redirect(request.referrer or url_for('index'))
    cart = get_cart()
    current_qty = cart.get(str(book.id), 0)
    if current_qty + 1 > book.stock:
        flash(f'Cannot add more copies. Max available stock is {book.stock}.', 'warning')
        return redirect(request.referrer or url_for('index'))
    cart[str(book.id)] = current_qty + 1
    save_cart(cart)
    flash(f'Added "{book.title}" to cart!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart/update/<int:book_id>/<action>', methods=['POST'])
def cart_update_qty(book_id, action):
    cart = get_cart()
    book = Book.query.get_or_404(book_id)
    current_qty = cart.get(str(book_id), 0)
    if action == 'increase':
        if current_qty < book.stock:
            cart[str(book_id)] = current_qty + 1
            flash(f'Increased quantity for "{book.title}".', 'success')
        else:
            flash(f'Cannot add more. Only {book.stock} copies in stock.', 'warning')
    elif action == 'decrease':
        if current_qty > 1:
            cart[str(book_id)] = current_qty - 1
            flash(f'Decreased quantity for "{book.title}".', 'info')
        else:
            del cart[str(book_id)]
            flash(f'Removed "{book.title}" from cart.', 'info')
    save_cart(cart)
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:book_id>', methods=['POST'])
def cart_remove(book_id):
    cart = get_cart()
    if str(book_id) in cart:
        del cart[str(book_id)]
        save_cart(cart)
        flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    cart_data = get_cart()
    items = []
    subtotal = 0.0

    for book_id, qty in list(cart_data.items()):
        book = Book.query.get(int(book_id))
        if book:
            item_total = book.price * qty
            items.append({'book': book, 'qty': qty, 'subtotal': item_total})
            subtotal += item_total
        else:
            del cart_data[book_id]
            save_cart(cart_data)

    # Billing Calculation Specification (Section 4.3):
    # Net Amount = (Price x Quantity) - Discount + Tax
    # Standard Campus Discount: 5% on orders >= 1000 (preserves TC06: 1000 subtotal -> 5% disc = 50 -> 5% tax = 47.5 -> 997.50)
    # Tiered Special Discount:
    # >= ₹1500 -> 10%
    # >= ₹1000 -> 5%
    if subtotal >= 1500:
        discount_pct = 10.0
        amount_needed_for_next = 0.0
        next_discount_label = "Maximum 10% Mega Discount applied!"
    elif subtotal >= 1000:
        discount_pct = 5.0
        amount_needed_for_next = 1500.0 - subtotal
        next_discount_label = f"Add ₹{amount_needed_for_next:.2f} more to unlock 10% Mega Discount!"
    else:
        discount_pct = 0.0
        amount_needed_for_next = 1000.0 - subtotal
        next_discount_label = f"Add ₹{amount_needed_for_next:.2f} more to unlock 5% Campus Discount!"

    discount_amount = (subtotal * discount_pct) / 100.0
    tax_amount = (subtotal - discount_amount) * 0.05
    total = (subtotal - discount_amount) + tax_amount

    if request.method == 'POST':
        if not items:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('index'))
        if not current_user.is_authenticated:
            flash('Please log in or register to complete your order.', 'info')
            return redirect(url_for('login'))

        # Check stock again before finalizing
        for entry in items:
            if entry['qty'] > entry['book'].stock:
                flash(f"Error: Not enough stock for '{entry['book'].title}'. Available: {entry['book'].stock}.", 'danger')
                return redirect(url_for('cart'))

        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        new_order = Order(
            invoice_no=invoice_number,
            customer_id=current_user.id,
            customer_name=current_user.username,
            customer_phone=current_user.phone or "N/A",
            subtotal=subtotal,
            discount_pct=discount_pct,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            net_amount=total,
            payment_method="Online/Counter",
            status="Completed"
        )
        db.session.add(new_order)
        db.session.flush()

        for entry in items:
            entry['book'].stock -= entry['qty']
            order_item = OrderItem(
                order_id=new_order.id,
                book_id=entry['book'].id,
                book_title=entry['book'].title,
                unit_price=entry['book'].price,
                quantity=entry['qty'],
                subtotal=entry['subtotal'],
                returned_quantity=0
            )
            db.session.add(order_item)

        db.session.commit()
        session.pop('cart', None)
        flash(f'Order completed successfully! Invoice #{invoice_number} generated.', 'success')
        return redirect(url_for('invoice_view', invoice_no=invoice_number))

    return render_template(
        'cart.html',
        items=items,
        subtotal=subtotal,
        discount_amount=discount_amount,
        discount_pct=discount_pct,
        tax_amount=tax_amount,
        total=total,
        amount_needed_for_next=amount_needed_for_next,
        next_discount_label=next_discount_label
    )


# ---------------------------------------------------------------------------
# Sales Staff Module: POS Billing Counter & Book Returns
# ---------------------------------------------------------------------------
@app.route('/staff/pos', methods=['GET', 'POST'])
@login_required
@role_required('staff', 'manager', 'admin')
def staff_pos():
    """Point of Sale billing counter designed for Sales Staff/Cashiers."""
    form = POSCheckoutForm()
    books = Book.query.order_by(Book.title.asc()).all()

    # Staff POS cart in session
    pos_cart = session.get('pos_cart', {})
    items = []
    subtotal = 0.0

    for book_id, qty in list(pos_cart.items()):
        b = Book.query.get(int(book_id))
        if b:
            line_tot = b.price * qty
            items.append({'book': b, 'qty': qty, 'subtotal': line_tot})
            subtotal += line_tot
        else:
            del pos_cart[book_id]
            session['pos_cart'] = pos_cart

    discount_pct = float(request.form.get('discount_pct', 0.0) if request.method == 'POST' else 0.0)
    tax_pct = float(request.form.get('tax_pct', 5.0) if request.method == 'POST' else 5.0)
    discount_amount = (subtotal * discount_pct) / 100.0
    tax_amount = (subtotal - discount_amount) * (tax_pct / 100.0)
    net_amount = (subtotal - discount_amount) + tax_amount

    if form.validate_on_submit():
        if not items:
            flash('Cannot generate bill: POS Cart is empty.', 'danger')
            return redirect(url_for('staff_pos'))

        # Check stock validity
        for entry in items:
            if entry['qty'] > entry['book'].stock:
                flash(f"Stock Error: Book '{entry['book'].title}' has only {entry['book'].stock} copies left.", 'danger')
                return redirect(url_for('staff_pos'))

        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        new_order = Order(
            invoice_no=invoice_number,
            customer_name=form.customer_name.data,
            customer_phone=form.customer_phone.data or "Walk-in",
            staff_id=current_user.id,
            subtotal=subtotal,
            discount_pct=discount_pct,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            net_amount=net_amount,
            payment_method=form.payment_method.data,
            status="Completed"
        )
        db.session.add(new_order)
        db.session.flush()

        for entry in items:
            entry['book'].stock -= entry['qty']
            order_item = OrderItem(
                order_id=new_order.id,
                book_id=entry['book'].id,
                book_title=entry['book'].title,
                unit_price=entry['book'].price,
                quantity=entry['qty'],
                subtotal=entry['subtotal'],
                returned_quantity=0
            )
            db.session.add(order_item)

        db.session.commit()
        session.pop('pos_cart', None)
        flash(f'Bill #{invoice_number} generated successfully and stock updated!', 'success')
        return redirect(url_for('invoice_view', invoice_no=invoice_number))

    return render_template(
        'pos.html',
        books=books,
        items=items,
        subtotal=subtotal,
        discount_pct=discount_pct,
        discount_amount=discount_amount,
        tax_pct=tax_pct,
        tax_amount=tax_amount,
        net_amount=net_amount,
        form=form
    )

@app.route('/staff/pos/add/<int:book_id>', methods=['POST'])
@login_required
@role_required('staff', 'manager', 'admin')
def staff_pos_add(book_id):
    book = Book.query.get_or_404(book_id)
    pos_cart = session.get('pos_cart', {})
    cur_qty = pos_cart.get(str(book.id), 0)
    if cur_qty + 1 > book.stock:
        flash(f'Cannot add book: Only {book.stock} copies currently in stock.', 'danger')
    else:
        pos_cart[str(book.id)] = cur_qty + 1
        session['pos_cart'] = pos_cart
        flash(f'Added "{book.title}" to POS Cart.', 'success')
    return redirect(url_for('staff_pos'))

@app.route('/staff/pos/update/<int:book_id>/<action>', methods=['POST'])
@login_required
@role_required('staff', 'manager', 'admin')
def staff_pos_update(book_id, action):
    pos_cart = session.get('pos_cart', {})
    book = Book.query.get_or_404(book_id)
    cur_qty = pos_cart.get(str(book.id), 0)
    if action == 'increase':
        if cur_qty < book.stock:
            pos_cart[str(book.id)] = cur_qty + 1
        else:
            flash(f'Cannot exceed available stock ({book.stock}).', 'warning')
    elif action == 'decrease':
        if cur_qty > 1:
            pos_cart[str(book.id)] = cur_qty - 1
        else:
            del pos_cart[str(book.id)]
    session['pos_cart'] = pos_cart
    return redirect(url_for('staff_pos'))

@app.route('/staff/pos/clear', methods=['POST'])
@login_required
@role_required('staff', 'manager', 'admin')
def staff_pos_clear():
    session.pop('pos_cart', None)
    flash('POS Cart has been reset.', 'info')
    return redirect(url_for('staff_pos'))

@app.route('/staff/returns', methods=['GET', 'POST'])
@login_required
@role_required('staff', 'manager', 'admin')
def process_return():
    """Sales Staff process book returns: restores stock and updates order balance."""
    form = ReturnForm()
    selected_order = None
    if request.method == 'GET' and request.args.get('search_invoice'):
        inv = request.args.get('search_invoice').strip()
        selected_order = Order.query.filter_by(invoice_no=inv).first()
        if not selected_order:
            flash(f'No invoice found with number "{inv}".', 'warning')
        else:
            form.invoice_no.data = selected_order.invoice_no

    if form.validate_on_submit():
        order = Order.query.filter_by(invoice_no=form.invoice_no.data.strip()).first()
        if not order:
            flash('Invalid invoice number.', 'danger')
            return redirect(url_for('process_return'))

        item_id = request.form.get('order_item_id', type=int)
        item = OrderItem.query.filter_by(id=item_id, order_id=order.id).first()
        if not item:
            flash('Please select a valid item from the order to return.', 'danger')
            return redirect(url_for('process_return', search_invoice=order.invoice_no))

        return_qty = form.quantity.data
        if return_qty <= 0 or return_qty > item.remaining_returnable:
            flash(f'Invalid return quantity. Maximum returnable for this item is {item.remaining_returnable}.', 'danger')
            return redirect(url_for('process_return', search_invoice=order.invoice_no))

        # Restock book inventory
        book = Book.query.get(item.book_id)
        if book:
            book.stock += return_qty

        item.returned_quantity += return_qty
        unit_refund = item.unit_price * return_qty
        # Adjust for proportion of original discount/tax
        refund_amount = unit_refund * (1 - (order.discount_pct / 100.0)) * 1.05

        return_log = BookReturn(
            order_id=order.id,
            order_item_id=item.id,
            book_id=item.book_id,
            quantity=return_qty,
            refund_amount=round(refund_amount, 2),
            reason=form.reason.data,
            processed_by=current_user.username
        )
        db.session.add(return_log)

        # Update order status
        all_returned = all(it.remaining_returnable == 0 for it in order.items)
        order.status = "Returned" if all_returned else "Partially Returned"

        db.session.commit()
        flash(f'Return processed successfully! {return_qty} copy/copies returned to stock. Refund: ₹{round(refund_amount, 2)}', 'success')
        return redirect(url_for('process_return', search_invoice=order.invoice_no))

    recent_returns = BookReturn.query.order_by(BookReturn.created_at.desc()).limit(10).all()
    return render_template('returns.html', form=form, selected_order=selected_order, recent_returns=recent_returns)


# ---------------------------------------------------------------------------
# Store Manager & Inventory Reports Module
# ---------------------------------------------------------------------------
@app.route('/manager/reports')
@login_required
@role_required('manager', 'admin')
def manager_reports():
    """Generate comprehensive sales and revenue reports."""
    filter_period = request.args.get('period', 'all')
    now = datetime.utcnow()

    query = Order.query
    if filter_period == 'today':
        today_start = datetime(now.year, now.month, now.day)
        query = query.filter(Order.created_at >= today_start)
    elif filter_period == 'week':
        week_ago = now - timedelta(days=7)
        query = query.filter(Order.created_at >= week_ago)
    elif filter_period == 'month':
        month_ago = now - timedelta(days=30)
        query = query.filter(Order.created_at >= month_ago)

    orders = query.order_by(Order.created_at.desc()).all()
    total_sales = len(orders)
    total_revenue = sum(o.net_amount for o in orders)
    total_discount = sum(o.discount_amount for o in orders)
    total_tax = sum(o.tax_amount for o in orders)

    # Top selling books aggregation
    top_items = db.session.query(
        OrderItem.book_title,
        db.func.sum(OrderItem.quantity).label('units_sold'),
        db.func.sum(OrderItem.subtotal).label('gross_sales')
    ).group_by(OrderItem.book_title).order_by(db.desc('units_sold')).limit(5).all()

    # Inventory Valuation
    books = Book.query.all()
    total_inventory_items = sum(b.stock for b in books)
    inventory_val = sum(b.stock * b.price for b in books)
    low_stock_count = sum(1 for b in books if b.is_low_stock)

    return render_template(
        'reports.html',
        orders=orders,
        total_sales=total_sales,
        total_revenue=total_revenue,
        total_discount=total_discount,
        total_tax=total_tax,
        top_items=top_items,
        total_inventory_items=total_inventory_items,
        inventory_val=inventory_val,
        low_stock_count=low_stock_count,
        filter_period=filter_period
    )

@app.route('/manager/stock')
@login_required
@role_required('manager', 'admin')
def manager_stock():
    """Stock tracking and low-stock alerts."""
    books = Book.query.order_by(Book.stock.asc()).all()
    low_stock_books = [b for b in books if b.is_low_stock]
    out_of_stock_books = [b for b in books if b.stock <= 0]
    return render_template(
        'stock.html',
        books=books,
        low_stock_books=low_stock_books,
        out_of_stock_books=out_of_stock_books
    )

@app.route('/manager/stock/update/<int:book_id>', methods=['POST'])
@login_required
@role_required('manager', 'admin')
def update_stock_qty(book_id):
    book = Book.query.get_or_404(book_id)
    new_stock = request.form.get('stock', type=int)
    if new_stock is not None and new_stock >= 0:
        book.stock = new_stock
        db.session.commit()
        flash(f'Stock updated for "{book.title}". New stock: {book.stock}', 'success')
    else:
        flash('Invalid stock quantity.', 'danger')
    return redirect(url_for('manager_stock'))


# ---------------------------------------------------------------------------
# Administrator Management: Books, Categories, Suppliers, Staff
# ---------------------------------------------------------------------------
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    books = Book.query.all()
    total_books = len(books)
    total_stock = sum(b.stock for b in books)
    low_stock = sum(1 for b in books if b.is_low_stock)
    inventory_val = sum(b.stock * b.price for b in books)
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.net_amount)).scalar() or 0.0
    staff_count = User.query.filter(User.role.in_(['staff', 'manager'])).count()

    return render_template(
        'admin.html',
        books=books,
        total_books=total_books,
        total_stock=total_stock,
        low_stock=low_stock,
        inventory_val=inventory_val,
        total_orders=total_orders,
        total_revenue=total_revenue,
        staff_count=staff_count
    )

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_book():
    form = BookForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name.asc()).all()]
    form.supplier_id.choices = [(0, '-- None --')] + [(s.id, s.name) for s in Supplier.query.order_by(Supplier.name.asc()).all()]

    if form.validate_on_submit():
        sup_id = form.supplier_id.data if form.supplier_id.data != 0 else None

        # Handle uploaded cover image
        saved_image_url = None
        if form.cover_image.data and form.cover_image.data.filename:
            file = form.cover_image.data
            filename = secure_filename(file.filename)
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            saved_image_url = url_for('static', filename='uploads/' + filename)

        book = Book(
            title=form.title.data,
            author=form.author.data,
            category_id=form.category_id.data,
            supplier_id=sup_id,
            price=form.price.data,
            stock=form.stock.data,
            min_stock_alert=form.min_stock_alert.data,
            description=form.description.data,
            image_url=saved_image_url,
            rating=round(random.uniform(4.5, 4.9), 1),
            reviews_count=random.randint(15, 80)
        )
        db.session.add(book)
        db.session.commit()
        flash('Book successfully added to database!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('book_form.html', form=form, action='Add')

@app.route('/admin/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name.asc()).all()]
    form.supplier_id.choices = [(0, '-- None --')] + [(s.id, s.name) for s in Supplier.query.order_by(Supplier.name.asc()).all()]

    if form.validate_on_submit():
        form.populate_obj(book)
        book.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None

        # Handle new cover image upload
        if form.cover_image.data and form.cover_image.data.filename:
            file = form.cover_image.data
            filename = secure_filename(file.filename)
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            book.image_url = url_for('static', filename='uploads/' + filename)

        db.session.commit()
        flash('Book details updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('book_form.html', form=form, action='Edit', book=book)

@app.route('/admin/delete/<int:book_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash(f'Book "{book.title}" was removed.', 'info')
    return redirect(url_for('admin_dashboard'))

# Admin: Categories
@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        if Category.query.filter_by(name=form.name.data.strip()).first():
            flash('Category already exists.', 'warning')
        else:
            cat = Category(name=form.name.data.strip(), description=form.description.data)
            db.session.add(cat)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('admin_categories'))
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('categories.html', categories=categories, form=form)

@app.route('/admin/categories/delete/<int:cat_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.books:
        flash(f'Cannot delete category "{cat.name}" because books are linked to it.', 'danger')
    else:
        db.session.delete(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" deleted.', 'info')
    return redirect(url_for('admin_categories'))

# Admin: Suppliers
@app.route('/admin/suppliers', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_suppliers():
    form = SupplierForm()
    if form.validate_on_submit():
        if Supplier.query.filter_by(name=form.name.data.strip()).first():
            flash('Supplier with this name already exists.', 'warning')
        else:
            sup = Supplier(
                name=form.name.data.strip(),
                contact_person=form.contact_person.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data
            )
            db.session.add(sup)
            db.session.commit()
            flash('Supplier registered successfully!', 'success')
            return redirect(url_for('admin_suppliers'))
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    return render_template('suppliers.html', suppliers=suppliers, form=form)

@app.route('/admin/suppliers/delete/<int:sup_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_supplier(sup_id):
    sup = Supplier.query.get_or_404(sup_id)
    db.session.delete(sup)
    db.session.commit()
    flash(f'Supplier "{sup.name}" deleted.', 'info')
    return redirect(url_for('admin_suppliers'))

# Admin: Staff Management
@app.route('/admin/staff', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_staff():
    form = StaffCreateForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username is already taken.', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash('Email is already registered.', 'danger')
        else:
            new_staff = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            new_staff.set_password(form.password.data)
            db.session.add(new_staff)
            db.session.commit()
            flash(f'Staff account for "{new_staff.username}" ({new_staff.role}) created!', 'success')
            return redirect(url_for('admin_staff'))
    staff_members = User.query.filter(User.role.in_(['staff', 'manager', 'admin'])).all()
    return render_template('staff_manage.html', staff_members=staff_members, form=form)


# ---------------------------------------------------------------------------
# Invoice & Customer Order History
# ---------------------------------------------------------------------------
@app.route('/invoice/<invoice_no>')
def invoice_view(invoice_no):
    order = Order.query.filter_by(invoice_no=invoice_no).first_or_404()
    return render_template('invoice.html', order=order)

@app.route('/customer/orders')
@login_required
def customer_orders():
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer_orders.html', orders=orders)


# ---------------------------------------------------------------------------
# Context Processors
# ---------------------------------------------------------------------------
@app.context_processor
def inject_cart_count():
    cart_data = get_cart()
    total_qty = sum(cart_data.values()) if cart_data else 0
    return dict(cart_count=total_qty)


# ---------------------------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------------------------
with app.app_context():
    os.makedirs(app.instance_path, exist_ok=True)
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
