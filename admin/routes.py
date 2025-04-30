from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.products import Product
from schemas.products import ProductCreate, LicenseKeyCreate
from models.licenses import LicenseKey
from auth.routes import get_current_user
from models.users import User
from models.products import Product
from models.purchases import Purchase
from typing import List

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

def is_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return True

# Create a new product
@admin_router.post("/create-product")
def create_product(name: str, has_keys: bool, download_link: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)

    product = Product(name=name, has_keys=has_keys, download_link=download_link)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"message": "Product created", "product_id": product.id}

@admin_router.post("/add_license_key")
def add_license_key(license: LicenseKeyCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_key = LicenseKey(
        key=license.key,
        product_id=license.product_id
    )
    db.add(new_key)
    db.commit()
    return {"message": "License key added"}


# List all products
@admin_router.get("/list-products")
def list_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)

    products = db.query(Product).all()
    return products

# List keys for a product
@admin_router.get("/list-keys/{product_id}")
def list_keys(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)

    keys = db.query(LicenseKey).filter(LicenseKey.product_id == product_id).all()
    return keys

def save_payment(db, email: str, product_name: str, amount: float, payment_method: str):
    new_payment = Payment(
        email=email,
        product_name=product_name,
        amount=amount,
        payment_method=payment_method
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@admin_router.get("/admin/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@admin_router.get("/admin/products")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@admin_router.get("/admin/purchases")
def get_all_purchases(db: Session = Depends(get_db)):
    purchases = db.query(Purchase).all()
    return purchases

@admin_router.post("/add_product")
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.name == product.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already exists")

    new_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        needs_license=product.needs_license,
        download_link=product.download_link
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Product added", "product_id": new_product.id}
