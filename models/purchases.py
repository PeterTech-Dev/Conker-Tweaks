from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.orm import relationship

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    license_key = Column(String, nullable=True)
    amount_paid = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="purchases")
    product = relationship("Product", back_populates="purchases")

