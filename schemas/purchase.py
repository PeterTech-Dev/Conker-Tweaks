from pydantic import BaseModel
from datetime import datetime

class PurchaseOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    license_key: str | None
    amount_paid: float
    timestamp: datetime

    class Config:
        orm_mode = True
