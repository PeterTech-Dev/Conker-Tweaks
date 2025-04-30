from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.products import Product
from models.licenses import LicenseKey
from models.purchases import Purchase
from auth.auth_utils import get_current_user
from models.users import User

products_router = APIRouter()

@products_router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@products_router.post("/purchase")
def purchase_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check stock
    if product.stock is not None and product.stock <= 0:
        raise HTTPException(status_code=400, detail="Out of stock")

    license_key_value = None

    if product.needs_license:
        license_key = db.query(LicenseKey).filter_by(product_id=product.id, is_used=False).first()
        if not license_key:
            raise HTTPException(status_code=400, detail="No license keys available for this product")
        license_key.is_used = True
        license_key.assigned_to_email = current_user.email
        license_key_value = license_key.key

    # Create purchase record
    purchase = Purchase(
        user_id=current_user.id,
        product_id=product.id,
        license_key=license_key_value,
        amount_paid=product.price
    )

    db.add(purchase)

    # Reduce stock if limited
    if product.stock is not None:
        product.stock -= 1

    db.commit()
    return {"message": "Purchase successful", "license_key": license_key_value, "download_link": product.download_link}
