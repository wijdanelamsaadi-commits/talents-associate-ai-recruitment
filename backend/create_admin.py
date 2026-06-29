"""
Script pour créer le premier compte recruteur/admin.
A placer dans le dossier backend/ du projet, puis exécuter avec :

    python create_admin.py

(le venv doit être activé et le fichier .env déjà configuré)
"""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User

# === Modifie ces 3 valeurs avant de lancer le script ===
FULL_NAME = "Admin Talents Associate"
EMAIL = "admin@talentsassociate.ma"
PASSWORD = "ChangeMoi123!"  # minimum 8 caractères
# =========================================================

db = SessionLocal()

existing = db.query(User).filter(User.email == EMAIL.lower()).first()
if existing:
    print(f"Un compte existe déjà avec cet email : {EMAIL}")
else:
    user = User(
        full_name=FULL_NAME,
        email=EMAIL.lower(),
        password_hash=hash_password(PASSWORD),
        role="admin",
        status="active",
    )
    db.add(user)
    db.commit()
    print("Compte admin créé avec succès !")
    print(f"Email    : {EMAIL}")
    print(f"Password : {PASSWORD}")

db.close()
