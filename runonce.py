# run_once.py
from app import app, db, User

with app.app_context():
    # Check if we already have users to avoid duplicates
    if not User.query.first():
        u1 = User(username="GrandpaJoe", email="joe@test.com")
        u1.set_password("123")
        
        u2 = User(username="ZoomerSarah", email="sarah@test.com")
        u2.set_password("123")
        
        u3 = User(username="TechMentor", email="admin@test.com")
        u3.set_password("123")

        db.session.add_all([u1, u2, u3])
        db.session.commit()
        print("Dummy users added!")
    else:
        print("Users already exist.")