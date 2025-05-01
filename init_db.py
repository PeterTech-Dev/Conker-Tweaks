from database import Base, engine, SessionLocal
from models.users import User
from models.products import Product
from models.licenses import LicenseKey
from auth.routes import hash_password
import pyotp

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")

# Create a session
db = SessionLocal()

# Check if admin already exists
existing_admin = db.query(User).filter(User.email == "conkertweaks@gmail.com").first()
if existing_admin:
    print("⚠️ Admin user already exists. Skipping creation.")
else:
    totp = pyotp.TOTP(pyotp.random_base32())
    admin_user = User(
        username="ConkerTweaks",
        email="conkertweaks@gmail.com",
        hashed_password=hash_password("Admin12!"),
        is_admin=True,
        has_2fa=True,
        twofa_secret=totp.secret
    )
    db.add(admin_user)
    db.commit()
    print("✅ Admin user created successfully!")
    print("🔐 Admin 2FA secret (scan in Google Authenticator):", totp.secret)

db.close()
