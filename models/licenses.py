from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

class LicenseKey(Base):
    __tablename__ = "license_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    is_used = Column(Boolean, default=False)
    assigned_to_email = Column(String, nullable=True)
