from database import Base, engine
from models import users
from models.users import User
from models.products import Product
from database import SessionLocal
from auth.routes import hash_password
from models.licenses import LicenseKey

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")

# Create a session
db = SessionLocal()

# Create an admin user
admin_user = User(
    username="Admin",
    email="admin@example.com",
    hashed_password=hash_password("AdminPassword123!"),
    is_admin=True
)

# Save to database
db.add(admin_user)
db.commit()
db.close()

print("Admin user created successfully!")
