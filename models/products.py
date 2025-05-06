from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=True)
    needs_license = Column(Boolean, default=False)
    download_link = Column(String, nullable=True)

    purchases = relationship("Purchase", back_populates="product")

