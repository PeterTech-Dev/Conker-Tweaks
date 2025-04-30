from pydantic import BaseModel
from typing import List

class CartItem(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    cart: List[CartItem]
    user_email: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str

class PaymentRequest(BaseModel):
    amount: float