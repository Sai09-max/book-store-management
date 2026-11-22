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
    # Create categories & suppliers if they don't exist yet
    categories = [get_or_create(Category, name=n) for n in CATEGORY_NAMES]
    suppliers  = [get_or_create(Supplier, name=n) for n in SUPPLIER_NAMES]
    added = 0

    # ------------------------------------------------------------
    # Add a handful of curated books (education, story, history)
    # ------------------------------------------------------------
    curated = [
        {"title": "The World of Mathematics", "author": "John Doe", "category": "Mathematics", "supplier": "Pearson"},
        {"title": "A Tale of Two Cities", "author": "Charles Dickens", "category": "Literature", "supplier": "Penguin Random House"},
        {"title": "History of Ancient Civilizations", "author": "Emily Smith", "category": "History", "supplier": "Oxford University Press"},
        {"title": "Introduction to Biology", "author": "Dr. Jane Roe", "category": "Biology", "supplier": "Cambridge University Press"},
        {"title": "The Adventures of Sherlock Holmes", "author": "Arthur Conan Doyle", "category": "Story", "supplier": "HarperCollins"},
    ]
    for b in curated:
        cat = get_or_create(Category, name=b["category"])
        sup = get_or_create(Supplier, name=b["supplier"])
        if not Book.query.filter_by(title=b["title"], author=b["author"]).first():
            book = Book(
                title=b["title"],
                author=b["author"],
                price=round(random.uniform(MIN_PRICE, MAX_PRICE), 2),
                stock=random.randint(0, MAX_STOCK),
                rating=round(random.uniform(3.5, 5.0), 1),
                reviews_count=random.randint(0, 200),
                description=f"A concise guide on {b['title'].lower()} written by {b['author']}.",
                image_url=placeholder_image(hashlib.sha256((b['title']+b['author']).encode()).hexdigest()[:10]),
                category_id=cat.id,
                supplier_id=sup.id,
            )
            db.session.add(book)
            added += 1
            print(f"🔖 Added curated book: {b['title']}")

    # ----------------------------------------------------------------
    # Generate the remaining random books (adjective + noun scheme)
    # ----------------------------------------------------------------
    for i in range(1, NUM_BOOKS + 1):
        # Generate a more realistic title and author
        adjectives = ["Silent", "Crimson", "Hidden", "Golden", "Mysterious", "Ancient", "Radiant", "Forgotten", "Stormy", "Enchanted"]
        nouns = ["River", "Horizon", "Legacy", "Oracle", "Echo", "Dream", "Shadow", "Flame", "Voyage", "Realm"]
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        title = f"{adj} {noun} {i:04d}"
        author = f"{adj} {noun}"
        price   = round(random.uniform(MIN_PRICE, MAX_PRICE), 2)
        stock   = random.randint(0, MAX_STOCK)
        rating  = round(random.uniform(3.5, 5.0), 1)
        reviews = random.randint(0, 200)
        # Match noun to a relevant category when possible
        noun_to_category = {
            "River": "Geography",
            "Horizon": "Astronomy",
            "Legacy": "History",
            "Oracle": "Philosophy",
            "Echo": "Music Theory",
            "Dream": "Literature",
            "Shadow": "Art & Design",
            "Flame": "Science",
            "Voyage": "Engineering",
            "Realm": "Fantasy",
        }
        cat_name = noun_to_category.get(noun, None)
        if cat_name:
            cat = get_or_create(Category, name=cat_name)
        else:
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

    # Clear existing books to avoid duplicates with new naming scheme
    db.session.query(Book).delete()
    db.session.commit()

    # Create categories & suppliers if they don't exist yet
    categories = [get_or_create(Category, name=n) for n in CATEGORY_NAMES]
    suppliers  = [get_or_create(Supplier, name=n) for n in SUPPLIER_NAMES]
    added = 0

    added = 0
    for i in range(1, NUM_BOOKS + 1):
        # Deterministic unique title & author based on index
                # Generate a more realistic title and author
        adjectives = ["Silent", "Crimson", "Hidden", "Golden", "Mysterious", "Ancient", "Radiant", "Forgotten", "Stormy", "Enchanted"]
        nouns = ["River", "Horizon", "Legacy", "Oracle", "Echo", "Dream", "Shadow", "Flame", "Voyage", "Realm"]
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        title = f"{adj} {noun} {i:04d}"
        author = f"{adj} {noun}"

        price   = round(random.uniform(MIN_PRICE, MAX_PRICE), 2)
        stock   = random.randint(0, MAX_STOCK)
        rating  = round(random.uniform(3.5, 5.0), 1)
        reviews = random.randint(0, 200)
        # Match noun to a relevant category when possible
        noun_to_category = {
            "River": "Geography",
            "Horizon": "Astronomy",
            "Legacy": "History",
            "Oracle": "Philosophy",
            "Echo": "Music Theory",
            "Dream": "Literature",
            "Shadow": "Art & Design",
            "Flame": "Science",
            "Voyage": "Engineering",
            "Realm": "Fantasy",
        }
        cat_name = noun_to_category.get(noun, None)
        if cat_name:
            # Find existing category object by name, or create it
            cat = get_or_create(Category, name=cat_name)
        else:
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
