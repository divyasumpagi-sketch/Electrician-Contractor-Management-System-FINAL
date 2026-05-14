"""
Seed Script — creates demo users for all 3 roles.
Run: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
import models
import auth

models.Base.metadata.create_all(bind=engine)

DEMO_USERS = [
    {
        "name": "Admin User",
        "email": "admin@gmail.com",
        "password": "Admin@123",
        "role": models.RoleEnum.ADMIN,
    },
    {
        "name": "Client User",
        "email": "client@gmail.com",
        "password": "Client@123",
        "role": models.RoleEnum.CLIENT,
    },
    {
        "name": "Electrician User",
        "email": "electrician@gmail.com",
        "password": "Elec@123",
        "role": models.RoleEnum.ELECTRICIAN,
    },
]

db = SessionLocal()

for u in DEMO_USERS:
    existing = db.query(models.User).filter(models.User.email == u["email"]).first()
    if existing:
        print(f"[SKIP] {u['email']} already exists.")
        continue

    new_user = models.User(
        name=u["name"],
        email=u["email"],
        hashed_password=auth.get_password_hash(u["password"]),
        role=u["role"],
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if u["role"] == models.RoleEnum.ELECTRICIAN:
        profile = models.ElectricianProfile(
            user_id=new_user.id,
            approval_status="APPROVED",
            specialization="General Electrical Works"
        )
        db.add(profile)
        db.commit()

    print(f"  [OK]   Created {u['role'].value}: {u['email']} / {u['password']}")

db.close()
print("\n✅ Seeding complete! Demo credentials above.")
