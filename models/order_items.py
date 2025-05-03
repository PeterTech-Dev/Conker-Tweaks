from sqlalchemy import Column, Integer, ForeignKey, Float, String
from sqlalchemy.orm import relationship
from database import Base

class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # per unit

order = relationship("Order", back_populates="order_items")
