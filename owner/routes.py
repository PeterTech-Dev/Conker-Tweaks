from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.products import Product
from schemas.products import ProductCreate, LicenseKeyCreate, ProductUpdate
from models.licenses import LicenseKey
from auth.routes import get_current_user
from models.users import User
from models.products import Product
from models.purchases import Purchase
from models.order_items import OrderItem
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload

owner_router = APIRouter()

def is_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return True

@owner_router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin or not current_user.has_2fa:
        raise HTTPException(status_code=403, detail="Admins only with 2FA")

    total_users = db.query(User).count()
    total_products = db.query(Product).count()

    # Sum of all purchased quantities across all orders
    total_purchases = db.query(OrderItem).with_entities(OrderItem.quantity).all()
    total_purchases_count = sum(q[0] for q in total_purchases)

    return {
        "users": total_users,
        "products": total_products,
        "purchases": total_purchases_count
    }

# Create a new product
@owner_router.post("/create-product")
def create_product(name: str, has_keys: bool, download_link: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)

    product = Product(name=name, has_keys=has_keys, download_link=download_link)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"message": "Product created", "product_id": product.id}

@owner_router.post("/add_license_key")
def add_license_key(license: LicenseKeyCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    keys = license.key.splitlines()
    for key in keys:
        new_key = LicenseKey(key=key.strip(), product_id=product.id)
        db.add(new_key)
    product.stock += len(keys)
    db.commit()
    return {"message": f"{len(keys)} license keys added"}

@owner_router.delete("/delete-product/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

# List all products
@owner_router.get("/list-products")
def list_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)

    products = db.query(Product).all()
    return products

# List keys for a product
@owner_router.get("/list-keys/{product_id}")
def list_keys(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)

    keys = db.query(LicenseKey).filter(LicenseKey.product_id == product_id).all()
    return keys

@owner_router.get("/admin/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@owner_router.get("/admin/products")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@owner_router.get("/admin/purchases")
def get_all_purchases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)

    purchases = (
        db.query(Purchase)
        .options(
            joinedload(Purchase.user),     # Assuming Purchase.user = relationship("User")
            joinedload(Purchase.product)   # Assuming Purchase.product = relationship("Product")
        )
        .all()
    )

    response = []
    for p in purchases:
        response.append({
            "purchase_id": p.id,
            "user_email": p.user.email if p.user else "N/A",
            "product_name": p.product.name if p.product else "N/A",
            "license_key": p.license_key,
            "amount_paid": p.amount_paid,
            "timestamp": p.timestamp.isoformat()
        })

    return JSONResponse(content=response)


@owner_router.post("/add_product")
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

@owner_router.patch("/set-stock/{product_id}")
def set_infinite_stock(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    is_admin(current_user)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.stock = -1
    db.commit()
    return {"message": "Stock set to infinite"}

@owner_router.patch("/update-product/{product_id}")
def update_product(
    product_id: int,
    updated_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    is_admin(current_user)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = updated_data.name
    product.description = updated_data.description
    product.price = updated_data.price
    product.stock = updated_data.stock
    product.needs_license = updated_data.needs_license
    product.download_link = updated_data.download_link

    db.commit()
    db.refresh(product)

    return {"message": "Product updated successfully", "product": product}