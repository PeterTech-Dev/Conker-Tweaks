from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    amount_paid = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    paypal_order_id = Column(String, unique=True, index=True)

    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")