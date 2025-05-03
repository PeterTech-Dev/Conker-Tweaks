from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int | None = None
    needs_license: bool
    download_link: str | None = None

class LicenseKeyCreate(BaseModel):
    product_id: int
    key: str
    
class ProductUpdate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    needs_license: bool
    download_link: str

