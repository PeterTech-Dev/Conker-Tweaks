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

# Add default products
default_products = [
    Product(
        name="Premium",
        description="Delivers a Noticeable FPS Boost\nOptimizes Latency for a More Responsive Feel\nPuts You in Control of Your System’s Performance",
        price=20.00,
        stock=0,
        needs_license=True,
        download_link="https://example.com/premium-download"
    ),
    Product(
        name="Manual",
        description="Precision-Tuned System Optimization\nUltra-Low Latency Configuration\nExpert-Level Custom Tweaks",
        price=30.00,
        stock=0,
        needs_license=True,
        download_link="https://example.com/manual-download"
    ),
    Product(
        name="Overclock",
        description="Full-System Overclocking (CPU, GPU & RAM)\nProfessionally Tuned & Stability Tested\nCustomized for Your Workflow or Playstyle",
        price=40.00,
        stock=0,
        needs_license=True,
        download_link="https://example.com/overclock-download"
    ),
]

for product in default_products:
    existing = db.query(Product).filter_by(name=product.name).first()
    if not existing:
        db.add(product)
        print(f"✅ Added product: {product.name}")
    else:
        print(f"⚠️ Product already exists: {product.name}")

db.commit()
db.close()
