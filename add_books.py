import os
import sys

# Ensure the script can import the Flask app
sys.path.append(os.getcwd())
from app import app, db, Book, Category, Supplier

# Sample data – you can extend this list as needed
books_data = [
    {
        "title": "Introduction to Algorithms",
        "author": "Thomas H. Cormen",
        "price": 79.99,
        "stock": 5,
        "category": "Computer Science",
        "supplier": "Pearson",
        "description": "Comprehensive textbook on algorithms, widely used in university courses.",
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "price": 45.00,
        "stock": 8,
        "category": "Software Engineering",
        "supplier": "Prentice Hall",
        "description": "A handbook of agile software craftsmanship.",
    },
    {
        "title": "Design Patterns: Elements of Reusable Object-Oriented Software",
        "author": "Erich Gamma",
        "price": 55.50,
        "stock": 4,
        "category": "Software Design",
        "supplier": "Addison-Wesley",
        "description": "Classic book describing 23 design patterns.",
    },
    {
        "title": "Artificial Intelligence: A Modern Approach",
        "author": "Stuart Russell",
        "price": 90.00,
        "stock": 7,
        "category": "Artificial Intelligence",
        "supplier": "Pearson",
        "description": "Comprehensive AI textbook covering theory and practice.",
    },
    {
        "title": "Deep Learning",
        "author": "Ian Goodfellow",
        "price": 85.00,
        "stock": 6,
        "category": "Machine Learning",
        "supplier": "MIT Press",
        "description": "Foundational text on deep learning techniques.",
    },
]

def get_or_create_category(name):
    cat = Category.query.filter_by(name=name).first()
    if not cat:
        cat = Category(name=name)
        db.session.add(cat)
        db.session.commit()
    return cat

def get_or_create_supplier(name):
    sup = Supplier.query.filter_by(name=name).first()
    if not sup:
        sup = Supplier(name=name)
        db.session.add(sup)
        db.session.commit()
    return sup

with app.app_context():
    # Ensure tables exist (in case the DB is fresh)
    db.create_all()
    for b in books_data:
        # Create or fetch related Category and Supplier
        cat = get_or_create_category(b["category"])
        sup = get_or_create_supplier(b["supplier"])
        # Check if the book already exists (by title & author)
        existing = Book.query.filter_by(title=b["title"], author=b["author"]).first()
        if existing:
            print(f"Book already exists: {b['title']} – skipping")
            continue
        # Create the Book instance
        book = Book(
            title=b["title"],
            author=b["author"],
            price=b["price"],
            stock=b["stock"],
            category_id=cat.id,
            supplier_id=sup.id,
            description=b["description"],
        )
        db.session.add(book)
        print(f"Added book: {b['title']}")
    db.session.commit()
    print("All books processed.")
