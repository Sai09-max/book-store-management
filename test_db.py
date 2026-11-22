import os
import sys

# Ensure app uses the proper config
sys.path.append(os.getcwd())
from app import app, db

# Drop all tables then create (for test only)
# Uncomment the next line to reset the DB:
# db.drop_all()

with app.app_context():
    db.create_all()
    print('✅ DB tables created')
