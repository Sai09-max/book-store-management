import os, sys
sys.path.append(r'C:\Users\naden\Desktop\Project 4')
from app import app, db, Book, Category, Supplier

with app.app_context():
    print('Books:', Book.query.count())
    print('Categories:', Category.query.count())
    print('Suppliers:', Supplier.query.count())
