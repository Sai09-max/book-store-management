import os, sys
sys.path.append(os.getcwd())
from app import app, db
from app import User, Book, StockRemainder, Category

# Ensure fresh DB
def reset_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

reset_db()

# Create test user, category, and out‑of‑stock book
with app.app_context():
    test_user = User(username='testuser', email='test@example.com', role='customer')
    test_user.set_password('password')
    db.session.add(test_user)
    test_category = Category(name='TestCat')
    db.session.add(test_category)
    db.session.flush()  # get IDs before commit
    test_book = Book(title='Out of Stock Book', author='Author', price=10.0, stock=0, category_id=test_category.id)
    db.session.add(test_book)
    db.session.commit()
    user_id = test_user.id
    book_id = test_book.id

# Use Flask test client to log in and request remainder
with app.test_client() as client:
    client.post('/login', data={'username': 'testuser', 'password': 'password'}, follow_redirects=True)
    resp = client.post(f'/remainder/{book_id}', follow_redirects=True)
    print('Remainder request status code:', resp.status_code)
    with app.app_context():
        r = StockRemainder.query.filter_by(user_id=user_id, book_id=book_id).first()
        print('Remainder record exists?', bool(r))

