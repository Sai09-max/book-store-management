import os, sys, random, hashlib
from datetime import datetime

# Make project importable
sys.path.append(os.getcwd())
from app import app, db, Book, Category, Supplier

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
NUM_BOOKS        = 500          # number of books to create
MAX_STOCK        = 30
MIN_PRICE        = 10.0
MAX_PRICE        = 150.0
PLACEHOLDER_IMG  = "https://picsum.photos/seed/{seed}/400/600"

# A richer set of categories and suppliers
CATEGORY_NAMES = [
    "Computer Science","Software Engineering","Artificial Intelligence",
    "Machine Learning","Data Science","Mathematics","Physics","Chemistry",
    "Biology","Economics","History","Philosophy","Psychology","Sociology",
    "Art & Design","Business","Law","Medicine","Engineering","Literature",
    "Environmental Studies","Geography","Political Science","Astronomy",
    "Statistics","Robotics","Graphic Design","Music Theory","Film Studies",
    "Linguistics","Education","Finance","Marketing","Operations Management",
    "Supply Chain","Human Resources","Entrepreneurship","Ethics"
]

SUPPLIER_NAMES = [
    "Pearson","Prentice Hall","Addison‑Wesley","MIT Press","O'Reilly","Springer",
    "Wiley","McGraw‑Hill","Cambridge University Press","Oxford University Press",
    "Packt","Apress","No Starch Press","Bloomsbury","Penguin Random House",
    "HarperCollins","Simon & Schuster","Elsevier","SAGE Publications","John Wiley & Sons"
]

def get_or_create(model, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
    return instance

def placeholder_image(seed: str) -> str:
    return PLACEHOLDER_IMG.format(seed=seed)

with app.app_context():
    # Ensure tables exist (useful on fresh DB)
    db.create_all()

    # Create categories & suppliers if they don't exist yet
    categories = [get_or_create(Category, name=n) for n in CATEGORY_NAMES]
    suppliers  = [get_or_create(Supplier, name=n) for n in SUPPLIER_NAMES]

    added = 0
    for i in range(1, NUM_BOOKS + 1):
        # Deterministic unique title & author based on index
        title   = f"Sample Book {i:04d}"
        author  = f"Author {i:04d}"
        price   = round(random.uniform(MIN_PRICE, MAX_PRICE), 2)
        stock   = random.randint(0, MAX_STOCK)
        rating  = round(random.uniform(3.5, 5.0), 1)
        reviews = random.randint(0, 200)
        cat = random.choice(categories)
        sup = random.choice(suppliers)

        # Defensive: skip if somehow already present (should not happen)
        if Book.query.filter_by(title=title, author=author).first():
            continue

        img_seed = hashlib.sha256(f"{title}{author}".encode()).hexdigest()[:10]
        img_url  = placeholder_image(img_seed)

        book = Book(
            title=title,
            author=author,
            price=price,
            stock=stock,
            rating=rating,
            reviews_count=reviews,
            description=f"A concise guide on {title.lower()} written by {author}.",
            image_url=img_url,
            category_id=cat.id,
            supplier_id=sup.id,
        )
        db.session.add(book)
        added += 1
        if added % 100 == 0:
            db.session.commit()
            print(f"✔️  {added} books inserted…")

    db.session.commit()
    print(f"\n✅ Finished – {added} books added (target {NUM_BOOKS}).")
