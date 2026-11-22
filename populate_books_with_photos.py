import os, sys, random, string, hashlib
from datetime import datetime

sys.path.append(os.getcwd())
from app import app, db, Book, Category, Supplier

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
NUM_BOOKS        = 500          # you can increase this if you like
MAX_STOCK        = 20
MIN_PRICE        = 10.0
MAX_PRICE        = 120.0
PLACEHOLDER_IMG  = "https://picsum.photos/seed/{seed}/400/600"

CATEGORY_NAMES = [
    "Computer Science","Software Engineering","Artificial Intelligence",
    "Machine Learning","Data Science","Mathematics","Physics","Chemistry",
    "Biology","Economics","History","Philosophy","Psychology","Sociology",
    "Art & Design","Business","Law","Medicine","Engineering","Literature",
    "Environmental Studies","Geography","Political Science","Astronomy",
    "Statistics","Robotics","Graphic Design","Music Theory","Film Studies",
    "Linguistics"
]

SUPPLIER_NAMES = [
    "Pearson","Prentice Hall","Addison‑Wesley","MIT Press","O'Reilly","Springer",
    "Wiley","McGraw‑Hill","Cambridge University Press","Oxford University Press",
    "Packt","Apress","No Starch Press","Bloomsbury","Penguin Random House",
    "HarperCollins","Simon & Schuster"
]

def random_words(num):
    return " ".join(
        "".join(random.choices(string.ascii_letters, k=random.randint(4,9)))
        for _ in range(num)
    )

def get_or_create(model, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
    return instance

def placeholder_image(seed):
    return PLACEHOLDER_IMG.format(seed=seed)

with app.app_context():
    db.create_all()
    categories = [get_or_create(Category, name=n) for n in CATEGORY_NAMES]
    suppliers  = [get_or_create(Supplier, name=n) for n in SUPPLIER_NAMES]
    added = 0
    for _ in range(NUM_BOOKS):
        title   = random_words(random.randint(2,5)).title()
        author  = random_words(random.randint(2,3)).title()
        price   = round(random.uniform(MIN_PRICE, MAX_PRICE), 2)
        stock   = random.randint(0, MAX_STOCK)
        rating  = round(random.uniform(3.5,5.0),1)
        reviews = random.randint(0,200)
        cat = random.choice(categories)
        sup = random.choice(suppliers)
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
    print(f"\n✅ Finished – {added} new books added (target {NUM_BOOKS}).")
